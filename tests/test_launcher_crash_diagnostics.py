import os
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import launcher


def _event_xml(process_id, app_path, module_name="gameScene.pyd"):
    return (
        "<Event xmlns='http://schemas.microsoft.com/win/2004/08/events/event'>"
        "<System><EventID>1000</EventID>"
        "<TimeCreated SystemTime='2026-07-26T12:39:28.0000000Z'/>"
        "</System><EventData>"
        "<Data Name='AppName'>aos.exe</Data>"
        "<Data Name='ModuleName'>%s</Data>"
        "<Data Name='ModuleVersion'>1.2.3.4</Data>"
        "<Data Name='ExceptionCode'>c0000005</Data>"
        "<Data Name='FaultingOffset'>00052e40</Data>"
        "<Data Name='ProcessId'>%s</Data>"
        "<Data Name='AppPath'>%s</Data>"
        "<Data Name='ModulePath'>C:\\Games\\%s</Data>"
        "<Data Name='IntegratorReportId'>report-123</Data>"
        "</EventData></Event>"
    ) % (
        module_name,
        hex(process_id),
        app_path,
        module_name,
    )


def test_fault_event_parser_selects_exact_process_and_unicode_path(tmp_path):
    executable = str(tmp_path / "Игри" / "aos.exe")
    payload = (
        _event_xml(111, executable, "stale.dll")
        + _event_xml(222, executable)
    ).encode("utf-8")

    fields = launcher._parse_windows_fault_events(payload, 222, executable)

    assert fields["ModuleName"] == "gameScene.pyd"
    assert fields["ExceptionCode"] == "c0000005"
    assert fields["FaultingOffset"] == "00052e40"
    assert fields["EventTimeUtc"] == "2026-07-26T12:39:28.0000000Z"


def test_fault_event_parser_rejects_other_executable(tmp_path):
    executable = str(tmp_path / "aos.exe")
    payload = _event_xml(222, str(tmp_path / "other.exe")).encode("utf-8")

    assert launcher._parse_windows_fault_events(payload, 222, executable) is None


def test_fault_diagnostics_append_self_contained_signature(monkeypatch):
    captured = []

    class ImmediateThread:
        def __init__(self, target, name):
            self.target = target
            self.name = name
            self.daemon = False

        def start(self):
            self.target()

    monkeypatch.setattr(launcher.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(
        launcher,
        "query_windows_fault_event",
        lambda process_id, executable_path: {
            "ModuleName": "gameScene.pyd",
            "ModuleVersion": "1.2.3.4",
            "ModulePath": r"C:\Games\gameScene.pyd",
            "ExceptionCode": "c0000005",
            "FaultingOffset": "00052e40",
            "IntegratorReportId": "report-123",
            "EventTimeUtc": "2026-07-26T12:39:28Z",
        },
    )
    monkeypatch.setattr(
        launcher,
        "append_launcher_log",
        lambda message, exc_info=None: captured.append(message),
    )

    launcher.start_windows_fault_diagnostics(222, r"C:\Games\aos.exe")

    assert len(captured) == 1
    assert "module=gameScene.pyd" in captured[0]
    assert "exception=c0000005" in captured[0]
    assert "offset=00052e40" in captured[0]
