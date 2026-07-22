# -*- coding: utf-8 -*-
"""Verified full-release updater for the frozen AoS Revival launcher.

The updater deliberately accepts only the canonical full ZIP published by the
project's GitHub repository.  It verifies both GitHub's asset digest and the
per-file build manifest before an apply script is allowed to touch the install.
"""
from __future__ import print_function, unicode_literals

import ctypes
from ctypes import wintypes
import hashlib
import json
import ntpath
import os
import posixpath
import re
import shutil
import subprocess
import sys
import zipfile

try:
    from urlparse import urlsplit
except ImportError:  # pragma: no cover - Python 3 source tooling
    from urllib.parse import urlsplit

from revival_http import request


REPOSITORY = "KikoTs/aceofspades_revival"
LATEST_RELEASE_URL = "https://api.github.com/repos/%s/releases/latest" % REPOSITORY
USER_AGENT = "AoS-Revival-Updater/1.0"
MAX_ARCHIVE_BYTES = 2 * 1024 * 1024 * 1024
MAX_EXTRACTED_BYTES = 8 * 1024 * 1024 * 1024
REQUIRED_RELEASE_FILES = {
    "aos.exe",
    "aos.pkg",
    "build_manifest.json",
    "server/battlespades.exe",
    "version.txt",
}
PRESERVED_FILES = (
    "config.txt",
    "config_user.json",
    "steam_emu.ini",
    "server_favorites.json",
    "server/config.toml",
    "server/admin.toml",
    "server/bans.json",
)
KNOWN_STALE_FILES = (
    "GameOverlayRenderer.dll",
    "codex.dll",
    "steam_api.dll",
    "steamclient.dll",
)
KNOWN_STALE_DIRECTORIES = (
    "server/_internal/numpy",
    "server/_internal/numpy.libs",
    "server/_internal/numpy-2.3.0.dist-info",
)
_VERSION_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)(?:[-+][0-9A-Za-z.-]+)?$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_CMD_UNSAFE_RE = re.compile(r"[\r\n\"%%!&|<>^]")

try:
    TEXT_TYPE = unicode
except NameError:  # pragma: no cover - Python 3 source tooling
    TEXT_TYPE = str


class UpdateError(Exception):
    """Raised when an update cannot be authenticated or safely prepared."""


def _text(value):
    if isinstance(value, TEXT_TYPE):
        return value
    if isinstance(value, bytes):
        return value.decode("utf-8", "strict")
    return TEXT_TYPE(value)


def _application_directory():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def current_version(app_dir=None):
    """Read the installed release version without trusting command-line input."""

    app_dir = os.path.abspath(app_dir or _application_directory())
    candidates = (
        os.path.join(app_dir, "version.txt"),
        os.path.join(app_dir, "VERSION"),
    )
    for path in candidates:
        try:
            with open(path, "rb") as stream:
                value = _text(stream.read()).strip()
        except (IOError, OSError, UnicodeError):
            continue
        if _VERSION_RE.match(value):
            return value.lstrip("v")
    raise UpdateError("This installation has no valid version marker.")


def parse_version(value):
    """Return a comparable three-part release tuple."""

    match = _VERSION_RE.match(_text(value).strip())
    if not match:
        raise UpdateError("Invalid release version: %s" % _text(value))
    return tuple(int(part) for part in match.groups())


def _asset_name(version):
    return "AoSRevival-%s-win32-full.zip" % version


def _decode_json(payload, label):
    try:
        return json.loads(_text(payload))
    except (TypeError, ValueError, UnicodeError) as error:
        raise UpdateError("%s returned invalid JSON: %s" % (label, error))


def _validated_asset(release):
    tag = _text(release.get("tag_name") or "").strip().lstrip("v")
    parse_version(tag)
    expected_name = _asset_name(tag)
    matches = [
        asset for asset in release.get("assets") or []
        if _text(asset.get("name") or "") == expected_name
    ]
    if len(matches) != 1:
        raise UpdateError("Release %s does not contain one canonical full ZIP." % tag)

    asset = matches[0]
    digest_value = _text(asset.get("digest") or "").lower()
    if not digest_value.startswith("sha256:"):
        raise UpdateError("GitHub did not publish a SHA-256 digest for %s." % expected_name)
    digest = digest_value.split(":", 1)[1]
    if not _SHA256_RE.match(digest):
        raise UpdateError("GitHub published an invalid asset digest.")

    try:
        size = int(asset.get("size"))
    except (TypeError, ValueError):
        raise UpdateError("GitHub published an invalid asset size.")
    if size <= 0 or size > MAX_ARCHIVE_BYTES:
        raise UpdateError("The release ZIP size is outside the updater safety limit.")

    url = _text(asset.get("browser_download_url") or "")
    parsed = urlsplit(url)
    hostname = (parsed.hostname or "").lower()
    if parsed.scheme.lower() != "https" or hostname not in (
        "github.com",
        "objects.githubusercontent.com",
        "release-assets.githubusercontent.com",
    ):
        raise UpdateError("The release asset URL is not an approved GitHub HTTPS URL.")

    return {
        "version": tag,
        "name": expected_name,
        "url": url,
        "size": size,
        "sha256": digest,
        "release_url": _text(release.get("html_url") or ""),
    }


def find_update(installed_version=None):
    """Return authenticated release metadata when a newer stable build exists."""

    installed_version = installed_version or current_version()
    status, payload = request(
        LATEST_RELEASE_URL,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": USER_AGENT,
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=15,
    )
    if status != 200:
        raise UpdateError("GitHub release check failed with HTTP %s." % status)
    release = _decode_json(payload, "GitHub")
    if release.get("draft") or release.get("prerelease"):
        return None
    release_version = _text(release.get("tag_name") or "").strip().lstrip("v")
    if parse_version(release_version) <= parse_version(installed_version):
        return None
    asset = _validated_asset(release)
    return asset


def _configure_winhttp(winhttp):
    handle_type = wintypes.HANDLE
    winhttp.WinHttpOpen.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD, wintypes.LPCWSTR,
        wintypes.LPCWSTR, wintypes.DWORD,
    ]
    winhttp.WinHttpOpen.restype = handle_type
    winhttp.WinHttpSetTimeouts.argtypes = [
        handle_type, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    ]
    winhttp.WinHttpConnect.argtypes = [
        handle_type, wintypes.LPCWSTR, wintypes.WORD, wintypes.DWORD,
    ]
    winhttp.WinHttpConnect.restype = handle_type
    winhttp.WinHttpOpenRequest.argtypes = [
        handle_type, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.LPCWSTR,
        wintypes.LPCWSTR, ctypes.POINTER(wintypes.LPCWSTR), wintypes.DWORD,
    ]
    winhttp.WinHttpOpenRequest.restype = handle_type
    winhttp.WinHttpSendRequest.argtypes = [
        handle_type, wintypes.LPCWSTR, wintypes.DWORD, wintypes.LPVOID,
        wintypes.DWORD, wintypes.DWORD, ctypes.c_size_t,
    ]
    winhttp.WinHttpSendRequest.restype = wintypes.BOOL
    winhttp.WinHttpReceiveResponse.argtypes = [handle_type, wintypes.LPVOID]
    winhttp.WinHttpReceiveResponse.restype = wintypes.BOOL
    winhttp.WinHttpQueryHeaders.argtypes = [
        handle_type, wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPVOID,
        ctypes.POINTER(wintypes.DWORD), ctypes.POINTER(wintypes.DWORD),
    ]
    winhttp.WinHttpQueryHeaders.restype = wintypes.BOOL
    winhttp.WinHttpQueryDataAvailable.argtypes = [
        handle_type, ctypes.POINTER(wintypes.DWORD),
    ]
    winhttp.WinHttpQueryDataAvailable.restype = wintypes.BOOL
    winhttp.WinHttpReadData.argtypes = [
        handle_type, wintypes.LPVOID, wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
    ]
    winhttp.WinHttpReadData.restype = wintypes.BOOL
    winhttp.WinHttpCloseHandle.argtypes = [handle_type]
    winhttp.WinHttpCloseHandle.restype = wintypes.BOOL


def _download_windows(url, destination, expected_size, progress):
    parsed = urlsplit(url)
    hostname = _text(parsed.hostname)
    path = _text(parsed.path or "/")
    if parsed.query:
        path += "?" + _text(parsed.query)

    winhttp = ctypes.windll.winhttp
    _configure_winhttp(winhttp)
    session = connection = request_handle = None
    try:
        session = winhttp.WinHttpOpen(USER_AGENT, 0, None, None, 0)
        if not session:
            raise ctypes.WinError()
        timeout_ms = 30000
        if not winhttp.WinHttpSetTimeouts(
            session, timeout_ms, timeout_ms, timeout_ms, timeout_ms
        ):
            raise ctypes.WinError()
        connection = winhttp.WinHttpConnect(session, hostname, parsed.port or 443, 0)
        if not connection:
            raise ctypes.WinError()
        request_handle = winhttp.WinHttpOpenRequest(
            connection, u"GET", path, None, None, None, 0x00800000
        )
        if not request_handle:
            raise ctypes.WinError()
        headers = u"User-Agent: %s\r\nAccept: application/octet-stream" % USER_AGENT
        if not winhttp.WinHttpSendRequest(
            request_handle, headers, len(headers), None, 0, 0, 0
        ):
            raise ctypes.WinError()
        if not winhttp.WinHttpReceiveResponse(request_handle, None):
            raise ctypes.WinError()

        status = wintypes.DWORD()
        status_size = wintypes.DWORD(ctypes.sizeof(status))
        if not winhttp.WinHttpQueryHeaders(
            request_handle,
            19 | 0x20000000,
            None,
            ctypes.byref(status),
            ctypes.byref(status_size),
            None,
        ):
            raise ctypes.WinError()
        if int(status.value) != 200:
            raise UpdateError("Release download failed with HTTP %s." % status.value)

        digest = hashlib.sha256()
        received = 0
        with open(destination, "wb") as output:
            while True:
                available = wintypes.DWORD()
                if not winhttp.WinHttpQueryDataAvailable(
                    request_handle, ctypes.byref(available)
                ):
                    raise ctypes.WinError()
                if available.value == 0:
                    break
                buffer_value = ctypes.create_string_buffer(available.value)
                read = wintypes.DWORD()
                if not winhttp.WinHttpReadData(
                    request_handle,
                    buffer_value,
                    available.value,
                    ctypes.byref(read),
                ):
                    raise ctypes.WinError()
                chunk = buffer_value.raw[:read.value]
                output.write(chunk)
                digest.update(chunk)
                received += len(chunk)
                if received > expected_size:
                    raise UpdateError("The release download exceeded its declared size.")
                if progress:
                    progress(received, expected_size)
        return received, digest.hexdigest()
    finally:
        for handle in (request_handle, connection, session):
            if handle:
                winhttp.WinHttpCloseHandle(handle)


def _download_portable(url, destination, expected_size, progress):
    try:
        import urllib.request as urllib_request
    except ImportError:  # pragma: no cover - Python 2 non-Windows source tooling
        import urllib2 as urllib_request
    request_value = urllib_request.Request(url, headers={"User-Agent": USER_AGENT})
    digest = hashlib.sha256()
    received = 0
    response = urllib_request.urlopen(request_value, timeout=30)
    try:
        with open(destination, "wb") as output:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                output.write(chunk)
                digest.update(chunk)
                received += len(chunk)
                if received > expected_size:
                    raise UpdateError("The release download exceeded its declared size.")
                if progress:
                    progress(received, expected_size)
    finally:
        response.close()
    return received, digest.hexdigest()


def download_release(asset, destination, progress=None):
    """Stream one release ZIP and verify its declared size and SHA-256."""

    destination = os.path.abspath(destination)
    partial = destination + ".part"
    parent = os.path.dirname(destination)
    if not os.path.isdir(parent):
        os.makedirs(parent)
    for path in (partial, destination):
        if os.path.isfile(path):
            os.remove(path)
    try:
        if sys.platform == "win32" and hasattr(ctypes, "windll"):
            received, digest = _download_windows(
                asset["url"], partial, asset["size"], progress
            )
        else:
            received, digest = _download_portable(
                asset["url"], partial, asset["size"], progress
            )
        if received != asset["size"]:
            raise UpdateError(
                "Release download size mismatch (%s != %s)."
                % (received, asset["size"])
            )
        if digest.lower() != asset["sha256"].lower():
            raise UpdateError("Release download failed SHA-256 verification.")
        os.rename(partial, destination)
        return destination
    finally:
        if os.path.isfile(partial):
            os.remove(partial)


def safe_relative_path(value):
    """Normalize one archive/manifest path and reject Windows escape tricks."""

    value = _text(value).replace("\\", "/")
    if not value or "\x00" in value or value.startswith("/"):
        raise UpdateError("Release contains an unsafe path.")
    if ntpath.splitdrive(value)[0]:
        raise UpdateError("Release contains a drive-qualified path.")
    normalized = posixpath.normpath(value)
    parts = normalized.split("/")
    if normalized in (".", "..") or any(part in ("", ".", "..") for part in parts):
        raise UpdateError("Release contains a path traversal entry.")

    reserved = {
        "con", "prn", "aux", "nul", "clock$",
        "com1", "com2", "com3", "com4", "com5", "com6", "com7", "com8", "com9",
        "lpt1", "lpt2", "lpt3", "lpt4", "lpt5", "lpt6", "lpt7", "lpt8", "lpt9",
    }
    for part in parts:
        if part.endswith((" ", ".")) or ":" in part:
            raise UpdateError("Release contains an unsafe Windows filename.")
        if any(ord(character) < 32 for character in part):
            raise UpdateError("Release contains a control character in a filename.")
        if part.split(".", 1)[0].lower() in reserved:
            raise UpdateError("Release contains a reserved Windows filename.")
    return normalized


def _target_path(root, relative):
    relative = safe_relative_path(relative)
    root = os.path.abspath(root)
    target = os.path.abspath(os.path.join(root, *relative.split("/")))
    root_prefix = os.path.normcase(root.rstrip(os.sep) + os.sep)
    if not os.path.normcase(target).startswith(root_prefix):
        raise UpdateError("Release path escaped the extraction directory.")
    return target


def extract_release(archive_path, destination):
    """Extract a ZIP without Zip Slip, duplicate names, or a zip bomb."""

    destination = os.path.abspath(destination)
    if os.path.isdir(destination):
        shutil.rmtree(destination)
    os.makedirs(destination)
    seen = set()
    total = 0
    try:
        with zipfile.ZipFile(archive_path, "r") as archive:
            for info in archive.infolist():
                raw_name = _text(info.filename).replace("\\", "/")
                is_directory = raw_name.endswith("/")
                name = raw_name.rstrip("/")
                if not name:
                    continue
                relative = safe_relative_path(name)
                key = relative.lower()
                if key in seen:
                    raise UpdateError("Release contains duplicate paths.")
                seen.add(key)
                total += int(info.file_size)
                if total > MAX_EXTRACTED_BYTES:
                    raise UpdateError("Release exceeds the extraction safety limit.")
                target = _target_path(destination, relative)
                if is_directory:
                    if not os.path.isdir(target):
                        os.makedirs(target)
                    continue
                parent = os.path.dirname(target)
                if not os.path.isdir(parent):
                    os.makedirs(parent)
                with archive.open(info, "r") as source, open(target, "wb") as output:
                    shutil.copyfileobj(source, output, 1024 * 1024)
        return destination
    except Exception:
        if os.path.isdir(destination):
            shutil.rmtree(destination)
        raise


def _sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        while True:
            chunk = stream.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _load_manifest(path):
    try:
        with open(path, "rb") as stream:
            return _decode_json(stream.read(), "Build manifest")
    except (IOError, OSError) as error:
        raise UpdateError("Build manifest could not be read: %s" % error)


def verify_release_tree(root, version):
    """Verify every staged file against the build manifest."""

    manifest_path = os.path.join(root, "build_manifest.json")
    manifest = _load_manifest(manifest_path)
    manifest_version = _text(manifest.get("version") or "").strip().lstrip("v")
    if manifest_version != version:
        raise UpdateError("Build manifest version does not match the GitHub release.")

    expected = {}
    for entry in manifest.get("files") or []:
        relative = safe_relative_path(entry.get("path") or "")
        key = relative.lower()
        if key in expected:
            raise UpdateError("Build manifest contains duplicate paths.")
        try:
            size = int(entry.get("size"))
        except (TypeError, ValueError):
            raise UpdateError("Build manifest contains an invalid file size.")
        digest = _text(entry.get("sha256") or "").lower()
        if size < 0 or not _SHA256_RE.match(digest):
            raise UpdateError("Build manifest contains invalid integrity data.")
        expected[key] = (relative, size, digest)

    actual = set()
    for current_root, directories, files in os.walk(root):
        directories.sort()
        files.sort()
        for filename in files:
            full_path = os.path.join(current_root, filename)
            relative = os.path.relpath(full_path, root).replace("\\", "/")
            actual.add(safe_relative_path(relative).lower())
    allowed_unlisted = {"build_manifest.json", "pkg_manifest.json"}
    if actual != set(expected).union(allowed_unlisted.intersection(actual)):
        raise UpdateError("Release tree contains missing or unlisted files.")

    for relative, size, digest in expected.values():
        path = _target_path(root, relative)
        if not os.path.isfile(path) or os.path.getsize(path) != size:
            raise UpdateError("Release file size check failed: %s" % relative)
        if _sha256_file(path).lower() != digest:
            raise UpdateError("Release file hash check failed: %s" % relative)

    if not REQUIRED_RELEASE_FILES.issubset(actual):
        raise UpdateError("Release is missing a required client or server file.")
    with open(os.path.join(root, "version.txt"), "rb") as stream:
        marker = _text(stream.read()).strip().lstrip("v")
    if marker != version:
        raise UpdateError("Release version marker does not match its manifest.")
    return manifest


def _copy_preserved_files(app_dir, preserve_dir):
    for relative in PRESERVED_FILES:
        source = _target_path(app_dir, relative)
        if not os.path.isfile(source):
            continue
        destination = _target_path(preserve_dir, relative)
        parent = os.path.dirname(destination)
        if not os.path.isdir(parent):
            os.makedirs(parent)
        shutil.copy2(source, destination)


def _managed_paths(manifest):
    result = set()
    if not manifest:
        return result
    for entry in manifest.get("files") or []:
        try:
            result.add(safe_relative_path(entry.get("path") or "").lower())
        except UpdateError:
            continue
    return result


def _stale_paths(app_dir, new_manifest):
    old_path = os.path.join(app_dir, "build_manifest.json")
    try:
        old_manifest = _load_manifest(old_path)
    except UpdateError:
        old_manifest = None
    preserved = set(path.lower() for path in PRESERVED_FILES)
    stale = _managed_paths(old_manifest) - _managed_paths(new_manifest) - preserved
    stale.update(path.lower() for path in KNOWN_STALE_FILES)
    return sorted(path for path in stale if not _CMD_UNSAFE_RE.search(path))


def _validate_batch_path(path):
    path = os.path.abspath(path)
    if _CMD_UNSAFE_RE.search(path):
        raise UpdateError("The install path contains characters unsafe for self-update.")
    return path


def _write_apply_script(
    update_root,
    app_dir,
    payload_dir,
    preserve_dir,
    stale_paths,
    archive_path=None,
):
    update_root = _validate_batch_path(update_root)
    app_dir = _validate_batch_path(app_dir)
    payload_dir = _validate_batch_path(payload_dir)
    preserve_dir = _validate_batch_path(preserve_dir)
    archive_path = _validate_batch_path(
        archive_path or os.path.join(update_root, "release.zip")
    )
    script_path = os.path.join(update_root, "apply-update.cmd")
    stale_path = os.path.join(update_root, "stale-files.txt")
    log_path = os.path.join(update_root, "apply-update.log")
    with open(stale_path, "wb") as stream:
        stream.write(("\r\n".join(path.replace("/", "\\") for path in stale_paths) + "\r\n").encode("utf-8"))

    lines = [
        "@echo off",
        "setlocal DisableDelayedExpansion",
        'set "INSTALL=%s"' % app_dir,
        'set "PAYLOAD=%s"' % payload_dir,
        'set "PRESERVE=%s"' % preserve_dir,
        'set "ARCHIVE=%s"' % archive_path,
        'set "STALE=%s"' % stale_path,
        'set "LOG=%s"' % log_path,
        ":wait_for_launcher",
        '"%%SystemRoot%%\\System32\\tasklist.exe" /FI "PID eq %s" /NH | "%%SystemRoot%%\\System32\\find.exe" "%s" >nul 2>&1' % (os.getpid(), os.getpid()),
        "if not errorlevel 1 (",
        '  "%SystemRoot%\\System32\\timeout.exe" /t 1 /nobreak >nul 2>&1',
        "  goto wait_for_launcher",
        ")",
        '"%SystemRoot%\\System32\\robocopy.exe" "%PAYLOAD%" "%INSTALL%" /E /COPY:DAT /DCOPY:DAT /R:3 /W:1 /NP /NFL /NDL >>"%LOG%" 2>&1',
        'set "COPY_RC=%ERRORLEVEL%"',
        "if %COPY_RC% GEQ 8 goto update_failed",
        '"%SystemRoot%\\System32\\robocopy.exe" "%PRESERVE%" "%INSTALL%" /E /COPY:DAT /DCOPY:DAT /R:3 /W:1 /NP /NFL /NDL >>"%LOG%" 2>&1',
        'set "PRESERVE_RC=%ERRORLEVEL%"',
        "if %PRESERVE_RC% GEQ 8 goto update_failed",
        'for /f "usebackq delims=" %%F in ("%STALE%") do del /f /q "%INSTALL%\\%%F" >>"%LOG%" 2>&1',
    ]
    for relative in KNOWN_STALE_DIRECTORIES:
        lines.append('rmdir /s /q "%%INSTALL%%\\%s" >>"%%LOG%%" 2>&1' % relative.replace("/", "\\"))
    lines.extend([
        'start "" "%INSTALL%\\aos.exe"',
        'rmdir /s /q "%PAYLOAD%" >>"%LOG%" 2>&1',
        'rmdir /s /q "%PRESERVE%" >>"%LOG%" 2>&1',
        'del /q "%ARCHIVE%" >>"%LOG%" 2>&1',
        'del /q "%STALE%" >>"%LOG%" 2>&1',
        'del /q "%~f0"',
        "exit /b 0",
        ":update_failed",
        '"%SystemRoot%\\System32\\robocopy.exe" "%PRESERVE%" "%INSTALL%" /E /COPY:DAT /DCOPY:DAT /R:1 /W:1 /NP /NFL /NDL >>"%LOG%" 2>&1',
        'start "" "%INSTALL%\\aos.exe"',
        "exit /b 1",
        "",
    ])
    script_encoding = "mbcs" if os.name == "nt" else "utf-8"
    with open(script_path, "wb") as stream:
        stream.write("\r\n".join(lines).encode(script_encoding))
    return script_path


def prepare_update(asset, app_dir=None, data_dir=None, progress=None):
    """Download, authenticate, extract, and prepare a deferred update apply."""

    version = _text(asset["version"]).strip().lstrip("v")
    parse_version(version)
    app_dir = os.path.abspath(app_dir or _application_directory())
    data_dir = os.path.abspath(
        data_dir or os.path.join(os.environ.get("LOCALAPPDATA") or app_dir, "AoS Revival")
    )
    updates_dir = os.path.join(data_dir, "updates")
    if not os.path.isdir(updates_dir):
        os.makedirs(updates_dir)
    update_root = os.path.abspath(os.path.join(updates_dir, version))
    if os.path.normcase(update_root).startswith(os.path.normcase(app_dir.rstrip(os.sep) + os.sep)):
        raise UpdateError("Update staging must be outside the game installation.")
    if os.path.isdir(update_root):
        shutil.rmtree(update_root)
    os.makedirs(update_root)

    archive_path = os.path.join(update_root, asset["name"])
    payload_dir = os.path.join(update_root, "payload")
    preserve_dir = os.path.join(update_root, "preserved")
    os.makedirs(preserve_dir)
    download_release(asset, archive_path, progress=progress)
    extract_release(archive_path, payload_dir)
    manifest = verify_release_tree(payload_dir, version)
    _copy_preserved_files(app_dir, preserve_dir)
    script_path = _write_apply_script(
        update_root,
        app_dir,
        payload_dir,
        preserve_dir,
        _stale_paths(app_dir, manifest),
        archive_path=archive_path,
    )
    return {
        "version": version,
        "script": script_path,
        "update_root": update_root,
    }


def launch_prepared_update(prepared):
    """Start the deferred installer; it waits for this launcher to exit."""

    if os.name != "nt":
        raise UpdateError("Automatic apply is available only on Windows.")
    script_path = _validate_batch_path(prepared["script"])
    if not os.path.isfile(script_path):
        raise UpdateError("The prepared update script is missing.")
    command = [os.environ.get("COMSPEC") or "cmd.exe", "/d", "/c", script_path]
    creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
    subprocess.Popen(command, close_fds=True, creationflags=creation_flags)
