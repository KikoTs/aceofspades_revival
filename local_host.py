# -*- coding: utf-8 -*-
"""Launch the bundled BattleSpades server for retail front-end actions.

This module deliberately keeps its configuration helpers independent from the
compiled game modules so they can be tested with modern Python.  Runtime-only
imports live in the small menu adapter functions at the bottom of the file.
The generated TOML is per-session and is never written over the bundle's base
``config.toml``.
"""
from __future__ import print_function

import atexit
import ast
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import unicodedata
import uuid

try:
    WindowsError
except NameError:  # pragma: no cover - Python 3 compatibility
    WindowsError = OSError


BOT_COUNT_PRESETS = ("0", "2", "4", "6", "8", "10", "12", "16", "20", "24")
BOT_DIFFICULTIES = ("casual", "normal", "hard", "mixed")
DEFAULT_SERVER_PORT = 27015
TUTORIAL_MODE = "tut"
TUTORIAL_MAP_FILENAME = "Training.vxl"
TUTORIAL_MAP_STEM = os.path.splitext(TUTORIAL_MAP_FILENAME)[0]
MAX_UGC_TITLE_CHARACTERS = 80
LOCAL_UGC_TITLE_COMMAND = "/__local_ugc_title "
SERVER_READY_TIMEOUT_SECONDS = 20.0
GRACEFUL_SHUTDOWN_TIMEOUT_SECONDS = 5.0
UGC_GRACEFUL_SHUTDOWN_TIMEOUT_SECONDS = 15.0
WINDOWS_OWNER_QUERY_TIMEOUT_SECONDS = 0.75
WINDOWS_OWNER_QUERY_POLL_SECONDS = 0.01
WINDOWS_OWNER_QUERY_MAX_BYTES = 4 * 1024 * 1024
_A2S_INFO_QUERY = b"\xff\xff\xff\xffTSource Engine Query\x00"

_ACTIVE_SESSION = None
_SESSION_LOCK = threading.RLock()
_DIAGNOSTIC_LOCK = threading.RLock()
_LOCAL_HOST_LOG_MAX_BYTES = 2 * 1024 * 1024


class LocalHostError(Exception):
    """Raised when a local session cannot be configured or launched."""


def _local_host_log_path():
    """Return the per-user log used by both readiness and UI callbacks."""

    base = os.environ.get("LOCALAPPDATA") or tempfile.gettempdir()
    directory = os.path.join(base, "AoS Revival", "logs")
    if not os.path.isdir(directory):
        try:
            os.makedirs(directory)
        except OSError:
            if not os.path.isdir(directory):
                return os.path.join(tempfile.gettempdir(), "aos-local-host.log")
    return os.path.join(directory, "local-host.log")


def _append_local_host_log(event, session=None, exc_info=None):
    """Write a bounded diagnostic record without affecting gameplay.

    Startup crosses three execution contexts: the retail menu/reactor thread,
    an A2S readiness worker, and a hidden server process.  Errors raised by a
    ``callFromThread`` callback were previously swallowed by the reactor and
    left the UI at "Waiting For Host" with no evidence.  This log records only
    state transitions and exceptions; it is not a packet or frame trace.
    """

    try:
        path = _local_host_log_path()
        with _DIAGNOSTIC_LOCK:
            try:
                if os.path.isfile(path) and os.path.getsize(path) > _LOCAL_HOST_LOG_MAX_BYTES:
                    archive = path + ".old"
                    try:
                        if os.path.isfile(archive):
                            os.remove(archive)
                        os.rename(path, archive)
                    except OSError:
                        pass
            except OSError:
                pass

            fields = [
                time.strftime("%Y-%m-%d %H:%M:%S"),
                threading.current_thread().name,
            ]
            if session is not None:
                fields.extend([
                    "kind=%s" % _text(getattr(session, "kind", "unknown")),
                    "port=%s" % _text(getattr(session, "port", "unknown")),
                    "pid=%s" % _text(getattr(getattr(session, "process", None), "pid", "unknown")),
                ])
            line = "[%s] %s\n" % (" | ".join(fields), _text(event))
            if exc_info:
                line += "".join(traceback.format_exception(*exc_info))
            with open(path, "ab") as stream:
                if not isinstance(line, bytes):
                    line = line.encode("utf-8", "replace")
                stream.write(line)
    except Exception:
        # Diagnostics are deliberately fail-open; local hosting must not depend
        # on a writable profile directory.
        pass


def _text(value):
    """Return one value as Unicode on Python 2 and Python 3."""

    if value is None:
        return u""
    try:
        unicode_type = unicode
    except NameError:  # pragma: no cover - Python 3 branch
        unicode_type = str
    if isinstance(value, unicode_type):
        return value
    if isinstance(value, bytes):
        return value.decode("utf-8", "replace")
    return unicode_type(value)


def _toml_string(value):
    """Encode a string using JSON's TOML-compatible double-quote escapes."""

    return json.dumps(_text(value), ensure_ascii=True)


def normalize_port(value):
    """Validate one menu-supplied UDP port."""

    try:
        port = int(_text(value).strip())
    except (TypeError, ValueError):
        raise LocalHostError("Server port must be a number between 1 and 65535.")
    if not 1 <= port <= 65535:
        raise LocalHostError("Server port must be between 1 and 65535.")
    return port


def normalize_ugc_title(value):
    """Validate one editor title before it enters the chat command channel."""

    title = _text(value).strip()
    if not title:
        raise LocalHostError("Map title cannot be empty.")
    if len(title) > MAX_UGC_TITLE_CHARACTERS:
        raise LocalHostError(
            "Map title cannot exceed %d characters." % MAX_UGC_TITLE_CHARACTERS
        )
    if any(unicodedata.category(character) == "Cc" for character in title):
        raise LocalHostError("Map title cannot contain control characters.")
    return title


def _safe_first(value, fallback):
    """Read a scalar, comma list, or retail repr-list without executing code."""

    text = _text(value).strip()
    if not text:
        return fallback
    if len(text) <= 1024 and text[:1] in ("[", "("):
        try:
            parsed = ast.literal_eval(text)
        except (SyntaxError, ValueError):
            parsed = None
        if isinstance(parsed, (list, tuple)) and parsed:
            text = _text(parsed[0]).strip()
    if "," in text:
        text = text.split(",", 1)[0].strip()
    return text or fallback


def normalize_map_rotation(value, fallback="MayanJungle"):
    """Return unique safe map stems from one retail lobby value."""

    raw = _text(value).strip()
    values = []
    if raw[:1] in ("[", "(") and len(raw) <= 8192:
        try:
            parsed = ast.literal_eval(raw)
        except (SyntaxError, ValueError):
            parsed = None
        if isinstance(parsed, (list, tuple)):
            values = list(parsed)
    if not values:
        values = raw.split(",") if raw else [fallback]

    result = []
    seen = set()
    for value in values:
        name = os.path.splitext(os.path.basename(_text(value).strip()))[0]
        if not name or name in (".", ".."):
            continue
        folded = name.lower()
        if folded not in seen:
            result.append(name)
            seen.add(folded)
    return result or [fallback]


def normalize_lobby_settings(values, rule_names=(), ugc=False):
    """Normalize untrusted Steam-lobby strings into one local host snapshot."""

    getter = values.get
    mode_key = "UGC_MODES" if ugc else "PLAYLIST"
    mode = _safe_first(getter(mode_key), "tdm")
    if mode == "ugc":
        mode = _safe_first(getter("UGC_MODES"), "tdm")
    maps = normalize_map_rotation(getter("MAP_ROTATION_FILENAME"))
    try:
        max_players = int(getter("MAX_PLAYERS") or 12)
    except (TypeError, ValueError):
        max_players = 12
    max_players = min(24, max(2, max_players))

    try:
        match_length = int(getter("MATCH_LENGTH") or 10)
    except (TypeError, ValueError):
        match_length = 10
    if match_length not in (0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 90):
        match_length = 10

    try:
        bot_count = int(getter("BOT_COUNT") or 0)
    except (TypeError, ValueError):
        bot_count = 0
    bot_count = min(max_players - 1, max(0, bot_count))
    difficulty = _text(getter("BOT_DIFFICULTY") or "mixed").strip().lower()
    if difficulty not in BOT_DIFFICULTIES:
        difficulty = "mixed"

    rules = {}
    for name in rule_names:
        key = _text(name).strip().upper()
        if not key.startswith("RULE_"):
            continue
        value = _text(getter(key)).strip()
        if value:
            rules[key] = value

    return {
        "name": _text(getter("Name") or "Local BattleSpades Match").strip(),
        "port": normalize_port(getter("SERVER_PORT") or DEFAULT_SERVER_PORT),
        "max_players": max_players,
        "match_length": match_length,
        "mode": mode,
        "maps": maps,
        "bot_count": bot_count,
        "bot_difficulty": difficulty,
        "rules": rules,
        "ugc": bool(ugc),
        "ugc_title": _text(getter("MAP_ROTATION_NEW_TITLE") or maps[0]).strip(),
        "ugc_project": _text(getter("UGC_PROJECT") or "").strip(),
    }


def tutorial_session_settings(port=DEFAULT_SERVER_PORT):
    """Return an isolated retail-tutorial configuration snapshot.

    Tutorial is not a variant of the last Match Lobby.  Keeping its complete
    snapshot in one helper prevents a previously selected mode, rotation,
    game rule, or bot population from leaking into the dedicated training
    process.
    """

    return {
        "name": "BattleSpades Tutorial",
        "port": normalize_port(port),
        "max_players": 12,
        "match_length": 0,
        "mode": TUTORIAL_MODE,
        "maps": [TUTORIAL_MAP_STEM],
        "bot_count": 0,
        "bot_difficulty": "mixed",
        "rules": {},
    }


def build_session_toml(settings, kind="match"):
    """Serialize a normalized local session using BattleSpades' public schema.

    ``kind`` is an authorization boundary, not presentation metadata.  A
    tutorial launch is rebuilt from the fixed tutorial contract here so even
    a bad caller cannot serialize ordinary lobby state into its private TOML.
    """

    if kind not in ("match", "tutorial", "ugc"):
        raise LocalHostError("Unknown local server kind: %s" % kind)
    if kind == "tutorial":
        settings = tutorial_session_settings(
            settings.get("port", DEFAULT_SERVER_PORT)
        )

    port = normalize_port(settings.get("port", DEFAULT_SERVER_PORT))
    max_players = min(24, max(2, int(settings.get("max_players", 12))))
    bot_count = min(max_players - 1, max(0, int(settings.get("bot_count", 0))))
    difficulty = _text(settings.get("bot_difficulty", "mixed")).lower()
    if difficulty not in BOT_DIFFICULTIES:
        difficulty = "mixed"
    maps = normalize_map_rotation(settings.get("maps", []))
    mode = _text(settings.get("mode", "tdm")).strip().lower() or "tdm"

    lines = [
        "# Generated by the AoS Revival client for one local session.",
        "# Deleting this file is safe; the bundled base config is never modified.",
        "",
        "[server]",
        "name = %s" % _toml_string(settings.get("name", "Local BattleSpades Match")),
        "port = %d" % port,
        "max_players = %d" % max_players,
        "tick_rate = 60",
        "",
        "[network]",
        "max_connections = %d" % max_players,
        "",
        "[game]",
        "default_mode = %s" % _toml_string(mode),
        "default_map = %s" % _toml_string(maps[0]),
        "bot_count = %d" % bot_count,
        "movement_authority = \"server\"",
        "map_sync_mode = \"full\"",
        "",
        "[lobby]",
        "map_rotation = [%s]" % ", ".join(_toml_string(item) for item in maps),
        "end_screen_seconds = 12.0",
    ]
    match_length = int(settings.get("match_length", 10) or 0)
    if match_length:
        lines.append("match_length_minutes = %d" % match_length)

    lines.extend([
        "",
        "[bots]",
        "enabled = %s" % ("true" if bot_count else "false"),
        "population_mode = \"fixed\"",
        "fill_target = %d" % bot_count,
        "max_bots = %d" % bot_count,
        "reserve_human_slots = 1",
        "difficulty = %s" % _toml_string(difficulty),
        "worker = \"process\"",
        # Pin the local-host performance contract instead of inheriting
        # whichever bot defaults happen to ship in a bundled server build.
        # The retail client and authoritative server share one machine, so a
        # predictable 5 Hz strategy cadence is important for frame pacing.
        "perception_hz = 10.0",
        "decision_hz = 5.0",
        "path_requests_per_second = 24",
        "main_thread_budget_ms = 0.75",
        "",
        "[steam]",
        "enabled = false",
        "public = false",
        "require_registration = false",
        "",
        "[revival]",
        "enabled = false",
        "require_identity = false",
        "",
        "[plugins]",
        "enabled = false",
        "",
        "[logging]",
        "level = \"INFO\"",
        "console = false",
        "packet_trace = false",
    ])

    rules = settings.get("rules", {}) or {}
    if rules:
        lines.extend(("", "[game_rules]"))
        for key in sorted(rules):
            if _text(key).startswith("RULE_"):
                lines.append("%s = %s" % (key, _toml_string(rules[key])))
    lines.append("")
    return "\n".join(lines)


def application_root():
    """Return the client asset root for source and cx_Freeze launches."""

    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def resolve_server_bundle(root=None):
    """Find the bundled server directory without consulting the CWD."""

    root = os.path.abspath(root or application_root())
    candidates = []
    configured = os.environ.get("AOS_BATTLESPADES_SERVER")
    if configured:
        candidates.append(configured)
    candidates.extend([
        os.path.join(root, "server"),
        os.path.join(os.path.dirname(root), "server"),
        os.path.abspath(os.path.join(root, "..", "..", "BattleSpades", "dist", "BattleSpades")),
    ])
    for candidate in candidates:
        executable = os.path.join(os.path.abspath(candidate), "BattleSpades.exe")
        if os.path.isfile(executable):
            return os.path.dirname(executable)
    raise LocalHostError(
        "The bundled BattleSpades server is missing. Reinstall the complete client package."
    )


def build_server_command(kind, bundle, config_path, port, project=None, client_root=None,
                         terrain=None, target_mode=None, title=None, author=None):
    """Build one frozen-server command using the per-session config contract."""

    names = {
        "match": "BattleSpades.exe",
        "tutorial": "BattleSpadesTutorial.exe",
        "ugc": "BattleSpadesMapCreator.exe",
    }
    if kind not in names:
        raise LocalHostError("Unknown local server kind: %s" % kind)
    executable = os.path.join(os.path.abspath(bundle), names[kind])
    if not os.path.isfile(executable):
        raise LocalHostError("Missing local server executable: %s" % executable)
    # Every bundled launcher exposes the same stdin control contract.  It is
    # the only way a windowless child can run its normal async shutdown path
    # (most importantly UGCMode.deactivate(), which writes the final VXL).
    command = [
        executable,
        "--config", os.path.abspath(config_path),
        "--control-stdin",
    ]
    if kind in ("tutorial", "ugc"):
        command.extend(["--port", str(normalize_port(port))])
    if kind == "ugc":
        client_root = os.path.abspath(client_root or application_root())
        publish_root = os.path.join(client_root, "hosted_ugc")
        output_dir = os.path.join(publish_root, "maps")
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)
        command.extend([
            "--project", project or "Custommap_1",
            "--publish-root", publish_root,
            "--retail-root", client_root,
        ])
        if terrain:
            command.extend(["--terrain", terrain])
        if target_mode:
            command.extend(["--target-mode", target_mode])
        if title:
            command.extend(["--title", title])
        if author:
            command.extend(["--author", author])
    return command


def create_session_config(settings, parent=None, kind="match"):
    """Atomically create one private temporary config and return its directory."""

    if parent is None:
        local = os.environ.get("LOCALAPPDATA") or tempfile.gettempdir()
        parent = os.path.join(local, "AoSRevival", "local-servers")
    if not os.path.isdir(parent):
        os.makedirs(parent)
    session_dir = os.path.join(parent, "session-%s" % uuid.uuid4().hex)
    os.makedirs(session_dir)
    config_path = os.path.join(session_dir, "config.toml")
    temporary = config_path + ".tmp"
    payload = build_session_toml(settings, kind=kind).encode("utf-8")
    with open(temporary, "wb") as stream:
        stream.write(payload)
        stream.flush()
        try:
            os.fsync(stream.fileno())
        except OSError:
            pass
    os.rename(temporary, config_path)
    return session_dir, config_path


def _udp_port_is_available(port):
    """Return whether ENet can bind the requested IPv4 wildcard endpoint.

    BattleSpades listens on ``0.0.0.0``.  Probing only ``127.0.0.1`` is not
    equivalent on Windows: it can succeed while another process already owns
    the wildcard endpoint.  That false positive used to launch a doomed child
    and let the subsequent A2S probe connect the client to the old server.
    """

    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        if os.name == "nt" and hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            probe.setsockopt(
                socket.SOL_SOCKET,
                socket.SO_EXCLUSIVEADDRUSE,
                1,
            )
        probe.bind(("0.0.0.0", int(port)))
        return True
    except socket.error:
        return False
    finally:
        probe.close()


def _allocate_private_udp_port(requested_port, kind):
    """Resolve the first free UDP endpoint at/after the preferred port.

    The menu setting is a preference, not a demand that an unrelated process
    be displaced.  Search upward deterministically and wrap after 65535.  The
    resolved value is written into the disposable TOML and used by the client,
    so Match, Tutorial, and Map Creator share one collision-safe rule.
    """

    requested_port = normalize_port(requested_port)
    try:
        offsets = xrange(65535)
    except NameError:  # pragma: no cover - Python 3 compatibility
        offsets = range(65535)
    for offset in offsets:
        candidate = ((requested_port - 1 + offset) % 65535) + 1
        if _udp_port_is_available(candidate):
            return candidate
    raise LocalHostError(
        "No local UDP port is available for %s starting at %d."
        % (kind, requested_port)
    )


def _probe_a2s(port):
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.settimeout(0.2)
        probe.sendto(_A2S_INFO_QUERY, ("127.0.0.1", int(port)))
        payload, _address = probe.recvfrom(4096)
        return payload.startswith(b"\xff\xff\xff\xff")
    except socket.error:
        return False
    finally:
        probe.close()


def _parse_netstat_udp_owner_pids(payload, port):
    """Extract IPv4 UDP owner PIDs from Windows ``netstat -ano`` output.

    Netstat's headings are localized, but protocol tokens and endpoint fields
    are stable.  Lines that are malformed, IPv6-only, or lack a numeric PID are
    ignored so ambiguous output always fails closed at the caller.
    """

    requested_port = int(port)
    owners = set()
    for raw_line in (payload or b"").splitlines():
        fields = raw_line.strip().split()
        if len(fields) < 4 or fields[0].upper() != b"UDP":
            continue
        endpoint = fields[1]
        if endpoint.startswith(b"[") or b":" not in endpoint:
            continue
        try:
            local_port = int(endpoint.rsplit(b":", 1)[1])
            process_id = int(fields[-1])
        except (TypeError, ValueError):
            continue
        if local_port == requested_port and process_id >= 0:
            owners.add(process_id)
    return owners


def _bounded_hidden_command_output(command, timeout):
    """Run one Windows helper with a hard deadline and bounded output.

    ``GetExtendedUdpTable`` occasionally blocks inside ``iphlpapi`` on affected
    Windows installations.  Calling it in the client process can therefore
    strand the readiness worker forever.  A disposable OS helper gives us a
    process boundary that can be terminated without touching the retail game
    or its server child.  Output uses a temporary file rather than ``PIPE`` so
    a large endpoint table cannot deadlock the helper on a full pipe.

    Returns ``None`` on launch failure, timeout, non-zero exit, or I/O failure.
    This function is called only by the readiness worker, never by the UI.
    """

    output_stream = None
    null_stream = None
    process = None
    try:
        output_stream = tempfile.TemporaryFile()
        null_stream = open(os.devnull, "r+b", 0)
        startupinfo = None
        creationflags = 0
        if os.name == "nt":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= getattr(
                subprocess,
                "STARTF_USESHOWWINDOW",
                1,
            )
            startupinfo.wShowWindow = 0
            creationflags |= getattr(
                subprocess,
                "CREATE_NO_WINDOW",
                0x08000000,
            )
        process = subprocess.Popen(
            command,
            stdin=null_stream,
            stdout=output_stream,
            stderr=null_stream,
            startupinfo=startupinfo,
            creationflags=creationflags,
        )
        deadline = time.time() + max(0.0, float(timeout))
        while process.poll() is None and time.time() < deadline:
            remaining = max(0.0, deadline - time.time())
            time.sleep(min(WINDOWS_OWNER_QUERY_POLL_SECONDS, remaining))
        if process.poll() is None:
            try:
                process.kill()
            except (AttributeError, OSError, WindowsError):
                pass
            # Do not call wait()/communicate() here: the bounded contract is
            # more important than reaping a Windows handle synchronously.
            return None
        if process.returncode != 0:
            return None
        output_stream.seek(0)
        return output_stream.read(WINDOWS_OWNER_QUERY_MAX_BYTES)
    except (AttributeError, IOError, OSError, TypeError, ValueError):
        return None
    finally:
        if process is not None:
            for stream_name in ("stdout", "stderr", "stdin"):
                stream = getattr(process, stream_name, None)
                if stream is not None and stream not in (
                    output_stream,
                    null_stream,
                ):
                    try:
                        stream.close()
                    except (IOError, OSError):
                        pass
        if output_stream is not None:
            try:
                output_stream.close()
            except (IOError, OSError):
                pass
        if null_stream is not None:
            try:
                null_stream.close()
            except (IOError, OSError):
                pass


def _udp_port_owner_pids(port):
    """Return PIDs owning one Windows IPv4 UDP port within a hard deadline.

    ``None`` means the platform has no supported ownership query.  Windows
    failures and timeouts return an empty set so readiness cannot connect to an
    unrelated A2S responder.  The helper is invoked only after A2S has answered,
    making the normal startup cost one bounded process rather than every poll.
    """

    if os.name != "nt":
        return None
    system_root = os.environ.get("SystemRoot") or os.environ.get("WINDIR")
    if not system_root:
        return set()
    executable = os.path.join(system_root, "System32", "netstat.exe")
    if not os.path.isfile(executable):
        return set()
    payload = _bounded_hidden_command_output(
        [executable, "-ano", "-p", "udp"],
        WINDOWS_OWNER_QUERY_TIMEOUT_SECONDS,
    )
    if payload is None:
        return set()
    return _parse_netstat_udp_owner_pids(payload, port)


def _probe_owned_a2s(session):
    """Accept A2S readiness only from the server process we launched."""

    if not _probe_a2s(session.port):
        return False
    owners = _udp_port_owner_pids(session.port)
    if owners is None:
        # Wildcard preflight is the portable ownership boundary.  Windows has
        # the stronger PID check above because that is where split binds occur.
        return True
    try:
        process_id = int(session.process.pid)
    except (AttributeError, TypeError, ValueError):
        return False
    # Any second owner makes the responder ambiguous.  Membership alone would
    # still permit a shared/racing socket to answer before our child.
    return owners == set([process_id])


class LocalServerSession(object):
    """Own one hidden child process and its disposable client-side files.

    ``owner_manager`` scopes local-only UI privileges to the exact client
    runtime that created this process.  It is deliberately unrelated to the
    UGC role advertised on packet 114; the dedicated server must continue to
    advertise CLIENT so retail map loading never enters the Steam-lobby host
    branch.
    """

    def __init__(self, process, session_dir, log_stream, stdin_stream, port,
                 kind="match", owner_manager=None, control_stdin=False):
        self.process = process
        self.session_dir = session_dir
        self.log_stream = log_stream
        self.stdin_stream = stdin_stream
        self.port = int(port)
        self.kind = kind
        self.owner_manager = owner_manager
        self.control_stdin = bool(control_stdin)
        self.session_id = uuid.uuid4().hex
        self._stop_lock = threading.RLock()

    def is_running(self):
        """Return whether the owned child has not exited yet."""

        return self.process is not None and self.process.poll() is None

    def _request_graceful_shutdown(self):
        """Ask the hidden launcher to stop through its opt-in stdin channel."""

        if not self.control_stdin or self.stdin_stream is None:
            return False
        try:
            self.stdin_stream.write(b"shutdown\n")
            self.stdin_stream.flush()
            return True
        except (IOError, OSError, ValueError):
            return False

    def stop(self):
        """Stop once, preferring lifecycle cleanup over forced termination."""

        with self._stop_lock:
            process = self.process
            if process is not None and process.poll() is None:
                graceful = self._request_graceful_shutdown()
                timeout = (
                    UGC_GRACEFUL_SHUTDOWN_TIMEOUT_SECONDS
                    if self.kind == "ugc"
                    else GRACEFUL_SHUTDOWN_TIMEOUT_SECONDS
                )
                deadline = time.time() + (timeout if graceful else 0.0)
                while process.poll() is None and time.time() < deadline:
                    time.sleep(0.05)
            if process is not None and process.poll() is None:
                try:
                    process.terminate()
                except (OSError, WindowsError):
                    pass
                deadline = time.time() + 2.0
                while process.poll() is None and time.time() < deadline:
                    time.sleep(0.05)
            if process is not None and process.poll() is None:
                try:
                    process.kill()
                    process.wait()
                except (AttributeError, OSError, WindowsError):
                    pass
            self.process = None
            if self.log_stream is not None:
                try:
                    self.log_stream.close()
                except IOError:
                    pass
                self.log_stream = None
            if self.stdin_stream is not None:
                try:
                    self.stdin_stream.close()
                except IOError:
                    pass
                self.stdin_stream = None
            self.owner_manager = None
            try:
                shutil.rmtree(self.session_dir)
            except OSError:
                pass


def spawn_hidden(command, cwd, session_dir, port, kind="match",
                 owner_manager=None, control_stdin=False):
    """Spawn one server without a visible console window."""

    log_path = os.path.join(session_dir, "server-bootstrap.log")
    log_stream = open(log_path, "ab", 0)
    stdin_stream = None
    child_stdin = subprocess.PIPE if control_stdin else open(os.devnull, "rb")
    startupinfo = None
    creationflags = 0
    if os.name == "nt":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= getattr(subprocess, "STARTF_USESHOWWINDOW", 1)
        startupinfo.wShowWindow = 0
        creationflags |= getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
        creationflags |= getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)
    try:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            stdin=child_stdin,
            stdout=log_stream,
            stderr=subprocess.STDOUT,
            startupinfo=startupinfo,
            creationflags=creationflags,
        )
    except Exception:
        log_stream.close()
        if not control_stdin:
            child_stdin.close()
        raise
    stdin_stream = process.stdin if control_stdin else child_stdin
    return LocalServerSession(
        process,
        session_dir,
        log_stream,
        stdin_stream,
        port,
        kind=kind,
        owner_manager=owner_manager,
        control_stdin=control_stdin,
    )


def has_active_local_session(manager=None, kind=None):
    """Return whether a matching client-owned child is currently alive."""

    with _SESSION_LOCK:
        session = _ACTIVE_SESSION
        if session is None or not session.is_running():
            return False
        if manager is not None and session.owner_manager is not manager:
            return False
        if kind is not None and session.kind != kind:
            return False
        return True


def is_local_ugc_host(manager):
    """Grant retail UGC host UI only to this active local session owner.

    This is a client-side menu capability, not a network role.  In particular,
    it must never be used to change ``InitialInfo.map_is_ugc``/packet 114.
    """

    return manager is not None and has_active_local_session(manager, "ugc")


def send_local_ugc_title(manager, value):
    """Send an edited title to the authoritative local UGC server.

    The stock UI only writes Steam lobby metadata.  A dedicated editor owns
    the persisted sidecar, so it receives the title through a private,
    host-only ChatMessage command intercepted before normal slash commands.
    """

    if not is_local_ugc_host(manager):
        return False
    try:
        title = normalize_ugc_title(value)
        from shared.packet import ChatMessage

        client = manager.client
        scene = manager.game_scene
    except (AttributeError, ImportError, LocalHostError):
        return False

    player_id = 0
    player = getattr(scene, "player", None)
    try:
        candidate = int(getattr(player, "id", 0))
    except (TypeError, ValueError):
        candidate = 0
    if 0 <= candidate <= 255:
        player_id = candidate

    command = LOCAL_UGC_TITLE_COMMAND + title
    if sys.version_info[0] < 3:
        command = command.encode("utf-8")
    try:
        packet = ChatMessage()
        packet.player_id = player_id
        packet.chat_type = 0
        packet.value = command
        client.send_packet(packet)
    except (AttributeError, OverflowError, RuntimeError, TypeError, ValueError):
        return False
    return True


def _fail_session_if_current(menu, session, error):
    """Report one readiness failure only if its session is still current.

    This executes on the reactor thread.  The identity comparison must happen
    here, immediately before touching the menu: an old readiness worker can
    otherwise overwrite a rapidly launched replacement session's UI.
    """

    global _ACTIVE_SESSION
    _append_local_host_log("readiness/transition failure: %s" % _text(error), session)
    with _SESSION_LOCK:
        if _ACTIVE_SESSION is not session:
            return False
        _ACTIVE_SESSION = None
    _show_local_error(menu, error)
    cleanup = threading.Thread(
        target=session.stop,
        name="aos-local-server-failure-cleanup",
    )
    cleanup.daemon = True
    cleanup.start()
    return True


def stop_active_session(manager=None):
    """Gracefully stop the active local child owned by ``manager``.

    The operation is idempotent.  Supplying a manager prevents one stale menu
    from stopping a newer session owned by another client runtime.
    """

    global _ACTIVE_SESSION
    with _SESSION_LOCK:
        session = _ACTIVE_SESSION
        if session is None:
            return False
        if manager is not None and session.owner_manager is not manager:
            return False
        _ACTIVE_SESSION = None
    session.stop()
    return True


# Compatibility for the first local-host integration and older call sites.
_stop_active_session = stop_active_session


atexit.register(stop_active_session)


def _terrain_from_map(map_name):
    key = _text(map_name).replace("_", "").replace(" ", "").lower()
    mapping = {
        "desertbaseplate": "desert",
        "lunarbaseplate": "lunar",
        "mountainbaseplate": "mountain",
        "grasslandbaseplate": "grassland",
        "templebaseplate": "temple",
        "urbanbaseplate": "urban",
        "marshbaseplate": "marsh",
        "snowybaseplate": "snowy",
        "waterbaseplate": "water",
    }
    return mapping.get(key)


def _show_local_error(menu, message):
    print("Local server launch failed: %s" % _text(message))
    menu.starting_game = False
    try:
        menu.update_buttons_enabled_state()
    except Exception:
        pass
    try:
        from shared.constants import A968
        menu.manager.set_big_text_message(A968, False, 6.0)
    except Exception:
        pass


def _connect_when_ready(menu, session, server_mode, name):
    """Poll readiness off-thread and consume it on pyglet's frame clock.

    The recovered pyglet reactor does not reliably wake for Twisted's
    ``callFromThread`` or drain its ``callLater`` queue on every frozen Windows
    build.  Both variants could prove the server ready in a worker and then
    leave the UI on "Waiting For Host" forever.  Pyglet's clock is the retail
    render/menu scheduler itself, so a tiny interval callback attached from the
    button handler is the reliable main-thread boundary.  Socket work remains
    in the worker and never blocks a frame.
    """

    from pyglet import clock

    result = {"finished": False, "error": None}
    result_lock = threading.RLock()
    poll_started = [False]

    def finish(error=None):
        with result_lock:
            result["error"] = error
            result["finished"] = True

    def connect():
        _append_local_host_log("reactor connect callback entered", session)
        try:
            with _SESSION_LOCK:
                if _ACTIVE_SESSION is not session or not session.is_running():
                    _append_local_host_log(
                        "reactor connect callback ignored stale/stopped session",
                        session,
                    )
                    return
            from aoslib.scenes.ingame_menus.loadingMenu import LoadingMenu

            parent = getattr(menu, "parent", None)
            if parent is None or not hasattr(parent, "set_menu"):
                raise LocalHostError(
                    "The active retail menu has no transition parent."
                )
            parent.set_menu(
                LoadingMenu,
                identifier="127.0.0.1:%d" % session.port,
                server_mode=server_mode,
                name=name,
                from_server_menu=True,
                previous_menu=type(menu),
            )
            _append_local_host_log("LoadingMenu transition completed", session)
        except Exception as error:
            _append_local_host_log(
                "LoadingMenu transition raised: %s" % _text(error),
                session,
                sys.exc_info(),
            )
            _fail_session_if_current(
                menu,
                session,
                "The game could not open the local loading screen: %s"
                % _text(error),
            )

    def poll_result(_dt):
        if not poll_started[0]:
            poll_started[0] = True
            _append_local_host_log("pyglet readiness poll entered", session)
        with result_lock:
            finished = result["finished"]
            error = result["error"]
        if not finished:
            with _SESSION_LOCK:
                current = _ACTIVE_SESSION is session
            if not current:
                clock.unschedule(poll_result)
            return
        clock.unschedule(poll_result)
        if error is not None:
            _fail_session_if_current(menu, session, error)
            return
        connect()

    def worker():
        _append_local_host_log("readiness worker started", session)
        try:
            deadline = time.time() + SERVER_READY_TIMEOUT_SECONDS
            error = None
            while time.time() < deadline:
                return_code = session.process.poll()
                if return_code is not None:
                    error = "The local server exited with code %s." % return_code
                    break
                if _probe_owned_a2s(session):
                    _append_local_host_log("owned A2S endpoint is ready", session)
                    break
                time.sleep(0.1)
            else:
                error = "The local server did not become ready within %s seconds." % int(SERVER_READY_TIMEOUT_SECONDS)

            if error is not None:
                _append_local_host_log(error, session)
                finish(error)
                return
            finish()
        except Exception as error:
            _append_local_host_log(
                "readiness worker raised: %s" % _text(error),
                session,
                sys.exc_info(),
            )
            finish("The local server readiness check failed: %s" % _text(error))

    thread = threading.Thread(target=worker, name="aos-local-server-ready")
    thread.daemon = True
    thread.start()
    _append_local_host_log("armed pyglet readiness poll", session)
    clock.schedule_interval(poll_result, 0.05)


def _launch_runtime(menu, kind, settings, project=None):
    """Create, spawn, and asynchronously connect one menu-owned local host."""

    global _ACTIVE_SESSION
    requested_port = normalize_port(
        settings.get("port", DEFAULT_SERVER_PORT)
    )
    # One client owns one local server. Stop our previous child before probing
    # the requested port so restarting with the same setting is deterministic.
    stop_active_session()
    port = _allocate_private_udp_port(requested_port, kind)
    if port != requested_port:
        # Never mutate the normalized lobby snapshot retained by the UI.  Only
        # this disposable process and its client connection use the fallback.
        settings = dict(settings)
        settings["port"] = port
    bundle = resolve_server_bundle()
    session_dir, config_path = create_session_config(settings, kind=kind)
    client_root = application_root()
    command = build_server_command(
        kind,
        bundle,
        config_path,
        port,
        project=project,
        client_root=client_root,
        terrain=_terrain_from_map(settings["maps"][0]) if kind == "ugc" else None,
        target_mode=settings.get("mode") if kind == "ugc" else None,
        title=settings.get("ugc_title") if kind == "ugc" else None,
        author=getattr(getattr(menu, "config", None), "name", None),
    )
    try:
        session = spawn_hidden(
            command,
            bundle,
            session_dir,
            port,
            kind=kind,
            owner_manager=getattr(menu, "manager", None),
            control_stdin=True,
        )
    except Exception:
        shutil.rmtree(session_dir, ignore_errors=True)
        raise
    with _SESSION_LOCK:
        _ACTIVE_SESSION = session
    _append_local_host_log("hidden server process spawned", session)

    menu.starting_game = True
    try:
        menu.update_buttons_enabled_state()
    except Exception:
        pass
    from shared.constants import A2389, A2387
    server_mode = A2389 if kind == "tutorial" else A2387
    title = "Tutorial" if kind == "tutorial" else ("Map Creator" if kind == "ugc" else "Local Match")
    _connect_when_ready(menu, session, server_mode, title)
    return session


def _lobby_values(ugc):
    from shared.constants_matchmaking import A2688
    from shared.steam import SteamGetCurrentLobby, SteamGetLobbyData

    lobby_id = SteamGetCurrentLobby()
    keys = [
        "Name", "PLAYLIST", "UGC_MODES", "MAP_ROTATION_FILENAME",
        "MAP_ROTATION_NEW_TITLE", "MAX_PLAYERS", "MATCH_LENGTH",
        "BOT_COUNT", "BOT_DIFFICULTY", "SERVER_PORT",
    ]
    rule_names = list(A2688.keys())
    values = dict((key, SteamGetLobbyData(lobby_id, key)) for key in keys + rule_names)
    return normalize_lobby_settings(values, rule_names, ugc=ugc)


def start_lobby(menu):
    """Replace the retail server-finder action with a bundled local host."""

    # Retail buttons can deliver a second activation before their disabled
    # state is rendered.  Re-entering would stop the healthy child that the
    # first click just created and can loop forever under rapid mouse input.
    if getattr(menu, "starting_game", False):
        return True
    try:
        settings = _lobby_values(bool(getattr(menu, "ugc_mode", False)))
        project = None
        if getattr(menu, "ugc_mode", False):
            project = getattr(menu.manager, "hosted_ugc_map_filename", "") or "Custommap_1"
        _launch_runtime(menu, "ugc" if getattr(menu, "ugc_mode", False) else "match", settings, project)
    except Exception as error:
        _show_local_error(menu, error)
    return True


def start_tutorial(menu):
    """Start the isolated tutorial executable and connect the same client."""

    if getattr(menu, "starting_game", False):
        return True
    settings = tutorial_session_settings()
    try:
        _launch_runtime(menu, "tutorial", settings)
    except Exception as error:
        _show_local_error(menu, error)
    return True


def create_server_port_row(manager, lobby_id, callback=None):
    """Create the retail-styled validated port editor only inside Python 2 UI."""

    from aoslib.scenes.gui.editBoxControl import EditBoxControl
    from aoslib.scenes.main.matchSettingsListItem import MatchSettingsListItem
    from shared.steam import SteamGetLobbyData, SteamSetLobbyData

    class ServerPortListItem(MatchSettingsListItem):
        def initialize(self):
            MatchSettingsListItem.initialize(self, "Server Port", "SERVER_PORT", lobby_id)
            value = SteamGetLobbyData(lobby_id, "SERVER_PORT") or str(DEFAULT_SERVER_PORT)
            SteamSetLobbyData("SERVER_PORT", value)
            self.original_text = value
            self.control = EditBoxControl(value, self.x1, self.y1, self.width, self.height,
                                          center=False, max_characters=5)
            self.control.on_return_callback = self.on_edit_text
            self.control.add_handler(self.on_edit_text)
            self.control.allow_over_typing = True
            self.elements.append(self.control)

        def update_position(self, x, y, width, height, highlight_width):
            MatchSettingsListItem.update_position(self, x, y, width, height, highlight_width)
            self.control.initialise_text(self.original_text)

        def on_edit_text(self):
            try:
                value = str(normalize_port(self.control.text))
            except LocalHostError:
                self.control.set(self.original_text)
                self.control.initialise_caret_index()
                return
            self.original_text = value
            self.control.set(value)
            SteamSetLobbyData("SERVER_PORT", value)
            if callback is not None:
                callback(value)

        def reset(self):
            self.original_text = str(DEFAULT_SERVER_PORT)
            self.control.set(self.original_text)
            SteamSetLobbyData("SERVER_PORT", self.original_text)

    return ServerPortListItem()
