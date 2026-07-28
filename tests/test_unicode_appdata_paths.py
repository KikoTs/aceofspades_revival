import os
from pathlib import Path
import subprocess
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import launcher
import local_host
import revival_paths
import revival_store
import revival_updater


@pytest.mark.skipif(os.name != "nt", reason="requires Windows wide-path APIs")
def test_local_appdata_preserves_non_ascii_environment(monkeypatch, tmp_path):
    expected = str(tmp_path / "Кико-日本語")
    monkeypatch.setenv("LOCALAPPDATA", expected)

    actual = revival_paths.local_appdata_directory()

    assert isinstance(actual, str)
    assert actual == os.path.normpath(expected)
    assert "?" not in actual


def test_python2_writes_unicode_localappdata_when_runtime_is_available(tmp_path):
    python2 = os.environ.get("AOS_PY2_PYTHON")
    if not python2 or not Path(python2).is_file():
        pytest.skip("AOS_PY2_PYTHON does not point to the legacy runtime")
    expected_root = tmp_path / "Кико-日本語"
    environment = os.environ.copy()
    environment["LOCALAPPDATA"] = str(expected_root)
    source = (
        "import os, shutil, subprocess, sys; "
        "sys.path.insert(0, %r); "
        "import revival_paths, revival_store, revival_updater, time; "
        "root = revival_paths.local_appdata_directory(); "
        "assert isinstance(root, unicode); "
        "assert u'\\u041a\\u0438\\u043a\\u043e-"
        "\\u65e5\\u672c\\u8a9e' in root; "
        "revival_store.save_state({'version': 1}); "
        "assert os.path.isfile(revival_store.state_path()); "
        "update_root = os.path.join("
        "root, u'AoS Revival', u'updates', "
        "u'\\u043f\\u0440\\u043e\\u0432\\u0435\\u0440\\u043a\\u0430-"
        "\\u65e5\\u672c\\u8a9e'); "
        "os.path.isdir(update_root) or os.makedirs(update_root); "
        "script_path = os.path.join(update_root, u'apply-update.cmd'); "
        "open(script_path, 'wb').write("
        "'@echo off\\r\\n>launch-ok.txt echo ok\\r\\nexit /b 0\\r\\n'); "
        "revival_updater.launch_prepared_update({'script': script_path}); "
        "time.sleep(2); "
        "assert os.path.isfile(os.path.join(update_root, u'launch-ok.txt')); "
        "child_exe = os.path.join(update_root, u'child.exe'); "
        "shutil.copy2(os.path.join("
        "os.environ['SystemRoot'], 'System32', 'cmd.exe'), child_exe); "
        "null_stream = open(os.devnull, 'ab', 0); "
        "child = revival_paths.unicode_popen("
        "[child_exe, '/d', '/c', '>wide-launch-ok.txt echo ok'], "
        "cwd=update_root, stdout=null_stream, stderr=subprocess.STDOUT); "
        "assert child.wait() == 0; "
        "pipe_child = revival_paths.unicode_popen("
        "[child_exe, '/d', '/c', 'more > pipe-launch-ok.txt'], "
        "cwd=update_root, stdin=subprocess.PIPE, "
        "stdout=null_stream, stderr=subprocess.STDOUT); "
        "pipe_child.stdin.write('hello\\r\\n'); "
        "pipe_child.stdin.close(); "
        "assert pipe_child.wait() == 0; "
        "long_child = revival_paths.unicode_popen("
        "[child_exe, '/d', '/c', "
        "'ping -n 20 127.0.0.1 >nul'], cwd=update_root, "
        "stdout=null_stream, stderr=subprocess.STDOUT); "
        "assert long_child.poll() is None; "
        "long_child.terminate(); "
        "assert long_child.wait() == 1; "
        "null_stream.close(); "
        "assert os.path.isfile("
        "os.path.join(update_root, u'wide-launch-ok.txt')); "
        "assert 'hello' in open("
        "os.path.join(update_root, u'pipe-launch-ok.txt'), 'rb').read()"
    ) % str(PROJECT_ROOT)

    completed = subprocess.run(
        [python2, "-c", source],
        cwd=str(tmp_path),
        env=environment,
        capture_output=True,
    )

    assert completed.returncode == 0, (
        completed.stdout + completed.stderr
    ).decode("utf-8", "replace")
    assert (
        expected_root / "AoS Revival" / "launcher_state.json"
    ).is_file()


def test_launcher_state_round_trips_under_unicode_path(monkeypatch, tmp_path):
    root = str(tmp_path / "Кико-日本語")
    monkeypatch.setattr(
        revival_store,
        "local_appdata_directory",
        lambda fallback=None: root,
    )

    revival_store.save_state(
        {
            "version": revival_store.STATE_VERSION,
            "account": {"display_name": "Играч"},
        }
    )

    assert Path(revival_store.state_path()).is_file()
    assert revival_store.load_state()["account"]["display_name"] == "Играч"


def test_local_server_config_uses_unicode_appdata(monkeypatch, tmp_path):
    root = str(tmp_path / "ユーザー")
    monkeypatch.setattr(
        local_host,
        "local_appdata_directory",
        lambda fallback=None: root,
    )

    session_dir, config_path = local_host.create_session_config({})

    assert Path(session_dir).parent == Path(root) / "AoSRevival" / "local-servers"
    assert Path(config_path).is_file()
    assert b"[server]" in Path(config_path).read_bytes()


def test_updater_default_data_root_uses_unicode_appdata(monkeypatch, tmp_path):
    root = str(tmp_path / "玩家")
    monkeypatch.setattr(
        revival_updater,
        "local_appdata_directory",
        lambda fallback=None: root,
    )
    captured = {}

    def stop_before_download(asset, destination, progress=None):
        captured["destination"] = destination
        raise RuntimeError("stop after path creation")

    monkeypatch.setattr(revival_updater, "download_release", stop_before_download)
    asset = {
        "version": "0.1.5",
        "name": "AoSRevival-0.1.5-win32-full.zip",
    }

    with pytest.raises(RuntimeError, match="stop after path creation"):
        revival_updater.prepare_update(
            asset,
            app_dir=str(tmp_path / "game"),
        )

    destination = Path(captured["destination"])
    assert destination.parent == Path(root) / "AoS Revival" / "updates" / "0.1.5"


def test_frozen_updater_uses_wide_executable_path(monkeypatch):
    executable = "C:\\Игри\\日本語\\aos.exe"
    monkeypatch.setattr(revival_updater.sys, "frozen", True, raising=False)
    monkeypatch.setattr(
        revival_updater,
        "current_executable_path",
        lambda fallback=None: executable,
    )

    assert revival_updater._application_directory() == "C:\\Игри\\日本語"


def test_frozen_launcher_uses_wide_executable_path(monkeypatch):
    executable = "C:\\Игри\\日本語\\aos.exe"
    monkeypatch.setattr(launcher.sys, "frozen", True, raising=False)
    monkeypatch.setattr(
        launcher,
        "current_executable_path",
        lambda fallback=None: executable,
    )

    assert launcher.app_directory() == "C:\\Игри\\日本語"
    assert launcher.launcher_executable_path() == executable
    assert launcher.check_launcher_path() == executable
    assert launcher.game_command(["+s"])[0] == executable


def test_frozen_launcher_reports_missing_openal_runtime(monkeypatch, tmp_path):
    (tmp_path / "config.txt").write_bytes(b"")
    (tmp_path / "ALURE32.dll").write_bytes(b"")
    (tmp_path / "aos.pkg").write_bytes(b"")
    for directory in ("png", "sounds", "maps"):
        (tmp_path / directory).mkdir()

    monkeypatch.setattr(launcher, "APP_DIR", str(tmp_path))
    monkeypatch.setattr(launcher.sys, "frozen", True, raising=False)

    missing = launcher.missing_game_files()

    assert missing == [str(tmp_path / "OpenAL32.dll")]


def test_native_path_encoding_uses_utf8():
    assert revival_paths.native_utf8_path("C:\\Игри\\日本語") == (
        "C:\\Игри\\日本語".encode("utf-8")
    )


def test_game_child_inherits_native_unicode_environment(monkeypatch, tmp_path):
    app_dir = str(tmp_path / "Игри-日本語")
    captured = {}

    class FakeProcess:
        pass

    def fake_popen(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        captured["encoding"] = os.environ.get("PYTHONIOENCODING")
        return FakeProcess()

    monkeypatch.setattr(launcher, "APP_DIR", app_dir)
    monkeypatch.setattr(launcher.subprocess, "Popen", fake_popen)
    monkeypatch.delenv("PYTHONIOENCODING", raising=False)

    process = launcher.spawn_isolated_game(["C:\\Игри\\aos.exe", "+s"])

    assert isinstance(process, FakeProcess)
    assert captured["kwargs"]["cwd"] == app_dir
    assert "env" not in captured["kwargs"]
    assert captured["encoding"] == "utf-8"
    assert "PYTHONIOENCODING" not in os.environ
