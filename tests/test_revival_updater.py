import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import zipfile

import pytest


MODULE_PATH = Path(__file__).resolve().parents[1] / "revival_updater.py"
SPEC = importlib.util.spec_from_file_location("revival_updater", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
updater = importlib.util.module_from_spec(SPEC)
sys.path.insert(0, str(MODULE_PATH.parent))
try:
    SPEC.loader.exec_module(updater)
finally:
    sys.path.pop(0)


def sha256(payload):
    return hashlib.sha256(payload).hexdigest()


def write_verified_tree(root, version="0.1.3"):
    files = {
        "aos.exe": b"clean bootloader",
        "aos.pkg": b"client package",
        "server/BattleSpades.exe": b"server binary",
        "version.txt": version.encode("ascii"),
    }
    entries = []
    for relative, payload in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        entries.append(
            {"path": relative, "size": len(payload), "sha256": sha256(payload)}
        )
    manifest = {
        "product_name": "AoS Revival",
        "version": version,
        "files": entries,
    }
    (root / "build_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return manifest


def test_parse_version_accepts_release_tags_and_orders_versions():
    assert updater.parse_version("v0.1.3") == (0, 1, 3)
    assert updater.parse_version("0.2.0") > updater.parse_version("0.1.99")
    with pytest.raises(updater.UpdateError):
        updater.parse_version("latest")


def test_asset_policy_requires_exact_name_https_and_github_digest():
    release = {
        "tag_name": "0.1.3",
        "html_url": "https://github.com/KikoTs/aceofspades_revival/releases/tag/0.1.3",
        "assets": [
            {
                "name": "AoSRevival-0.1.3-win32-full.zip",
                "size": 123,
                "digest": "sha256:" + ("a" * 64),
                "browser_download_url": (
                    "https://github.com/KikoTs/aceofspades_revival/releases/download/"
                    "0.1.3/AoSRevival-0.1.3-win32-full.zip"
                ),
            }
        ],
    }
    asset = updater._validated_asset(release)
    assert asset["version"] == "0.1.3"
    assert asset["sha256"] == "a" * 64

    release["assets"][0]["browser_download_url"] = "http://example.com/update.zip"
    with pytest.raises(updater.UpdateError):
        updater._validated_asset(release)


@pytest.mark.parametrize(
    "path",
    [
        "../aos.exe",
        "/absolute/aos.exe",
        "C:/Windows/aos.exe",
        "server/../../aos.exe",
        "server/file.txt:payload",
        "server/CON.txt",
        "server/trailing. ",
    ],
)
def test_safe_relative_path_rejects_windows_escape_paths(path):
    with pytest.raises(updater.UpdateError):
        updater.safe_relative_path(path)


def test_extract_release_rejects_zip_slip(tmp_path):
    archive_path = tmp_path / "bad.zip"
    with zipfile.ZipFile(str(archive_path), "w") as archive:
        archive.writestr("../escaped.txt", b"bad")
    with pytest.raises(updater.UpdateError):
        updater.extract_release(str(archive_path), str(tmp_path / "payload"))
    assert not (tmp_path / "escaped.txt").exists()


def test_extract_release_rejects_case_collisions(tmp_path):
    archive_path = tmp_path / "duplicate.zip"
    with zipfile.ZipFile(str(archive_path), "w") as archive:
        archive.writestr("Maps/Test.vxl", b"first")
        archive.writestr("maps/test.vxl", b"second")
    with pytest.raises(updater.UpdateError):
        updater.extract_release(str(archive_path), str(tmp_path / "payload"))


def test_verify_release_tree_checks_every_file(tmp_path):
    write_verified_tree(tmp_path)
    manifest = updater.verify_release_tree(str(tmp_path), "0.1.3")
    assert manifest["version"] == "0.1.3"

    (tmp_path / "aos.pkg").write_bytes(b"tampered")
    with pytest.raises(updater.UpdateError, match="size check failed|hash check failed"):
        updater.verify_release_tree(str(tmp_path), "0.1.3")


def test_verify_release_tree_rejects_unlisted_payload(tmp_path):
    write_verified_tree(tmp_path)
    (tmp_path / "surprise.dll").write_bytes(b"not listed")
    with pytest.raises(updater.UpdateError, match="unlisted"):
        updater.verify_release_tree(str(tmp_path), "0.1.3")


def test_apply_script_preserves_configs_and_uses_scoped_paths(tmp_path):
    app_dir = tmp_path / "game"
    update_root = tmp_path / "updates" / "0.1.3"
    payload = update_root / "payload"
    preserved = update_root / "preserved"
    for directory in (app_dir, payload, preserved):
        directory.mkdir(parents=True, exist_ok=True)

    script = updater._write_apply_script(
        str(update_root),
        str(app_dir),
        str(payload),
        str(preserved),
        ["obsolete.dll"],
    )
    text = open(script, "rb").read().decode("utf-8")
    assert "robocopy.exe" in text
    assert str(app_dir) in text
    assert 'del /q "%ARCHIVE%"' in text
    assert "rmdir /s /q \"%INSTALL%\\server\\_internal\\numpy\"" in text
    assert (update_root / "stale-files.txt").read_text().strip() == "obsolete.dll"


def test_stale_paths_never_trusts_manifest_traversal(tmp_path):
    app_dir = tmp_path / "game"
    app_dir.mkdir()
    old_manifest = {
        "files": [
            {"path": "../outside.dll"},
            {"path": "old-runtime.dll"},
            {"path": "config.txt"},
        ]
    }
    (app_dir / "build_manifest.json").write_text(
        json.dumps(old_manifest), encoding="utf-8"
    )
    stale = updater._stale_paths(str(app_dir), {"files": []})
    assert "../outside.dll" not in stale
    assert "config.txt" not in stale
    assert "old-runtime.dll" in stale


def test_download_release_rejects_digest_mismatch(monkeypatch, tmp_path):
    destination = tmp_path / "release.zip"

    def fake_download(url, partial, expected_size, progress):
        with open(partial, "wb") as stream:
            stream.write(b"abc")
        return 3, sha256(b"abc")

    monkeypatch.setattr(updater, "_download_portable", fake_download)
    monkeypatch.setattr(updater.sys, "platform", "linux")
    asset = {
        "url": "https://github.com/example.zip",
        "size": 3,
        "sha256": "0" * 64,
    }
    with pytest.raises(updater.UpdateError, match="SHA-256"):
        updater.download_release(asset, str(destination))
    assert not destination.exists()
    assert not (tmp_path / "release.zip.part").exists()
