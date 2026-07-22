import hashlib
import importlib.util
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "build_legacy_release.py"
SPEC = importlib.util.spec_from_file_location("build_legacy_release", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def test_release_spec_does_not_rewrite_executable_resources():
    assert builder.SPEC_TEMPLATE.count("icon=None") == 2
    assert "icon={" not in builder.SPEC_TEMPLATE


def test_restore_clean_bootloader_requires_and_copies_pinned_bytes(
    monkeypatch, tmp_path
):
    payload = b"pristine PyInstaller windowed bootloader"
    source = tmp_path / "runw.exe"
    source.write_bytes(payload)
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    (runtime / "aos.exe").write_bytes(b"resource-mutated executable")

    monkeypatch.setattr(builder, "CLEAN_WINDOWED_BOOTLOADER", source)
    monkeypatch.setattr(builder, "CLEAN_WINDOWED_BOOTLOADER_SHA256", digest(payload))
    builder.restore_clean_windowed_bootloader(runtime)

    assert (runtime / "aos.exe").read_bytes() == payload


def test_restore_clean_bootloader_rejects_unpinned_bytes(monkeypatch, tmp_path):
    source = tmp_path / "runw.exe"
    source.write_bytes(b"unexpected bootloader")
    runtime = tmp_path / "runtime"
    runtime.mkdir()

    monkeypatch.setattr(builder, "CLEAN_WINDOWED_BOOTLOADER", source)
    monkeypatch.setattr(builder, "CLEAN_WINDOWED_BOOTLOADER_SHA256", "0" * 64)
    with pytest.raises(RuntimeError, match="pinned SHA-256"):
        builder.restore_clean_windowed_bootloader(runtime)


def test_version_argument_must_match_source_marker(monkeypatch, tmp_path):
    marker = tmp_path / "VERSION"
    marker.write_text("0.1.3\n", encoding="ascii")
    monkeypatch.setattr(builder, "SOURCE_VERSION_FILE", marker)

    builder.validate_release_version("0.1.3")
    with pytest.raises(RuntimeError, match="does not match"):
        builder.validate_release_version("0.1.2")


def test_checksum_manifest_covers_each_artifact(monkeypatch, tmp_path):
    first = tmp_path / "client.zip"
    second = tmp_path / "client.7z"
    first.write_bytes(b"zip")
    second.write_bytes(b"seven zip")
    monkeypatch.setattr(builder, "ARTIFACTS_ROOT", tmp_path)

    checksum_path = builder.write_artifact_checksums("0.1.3", [first, second])
    lines = checksum_path.read_text(encoding="ascii").splitlines()

    assert lines == [
        "%s  client.7z" % digest(b"seven zip"),
        "%s  client.zip" % digest(b"zip"),
    ]
