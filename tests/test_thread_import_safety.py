"""The client must never execute an ``import`` on a background thread.

``run.py`` reaches the client through ``import aoslib.run`` and the frozen
launcher reaches ``run.py`` through ``import run``.  CPython 2 holds a single
global import lock until the *outermost* import returns, so a game loop running
inside one of those imports blocks every worker thread that imports anything --
which is exactly how Create Match and Start Game stopped responding: the social
HTTPS worker parked forever on ``from urllib import quote`` and never delivered
a single lobby callback.

These tests pin both halves of the fix: the loop runs outside every import, and
the modules that execute on worker threads resolve their names up front.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Every public entry point of these modules is reached from a worker thread:
# the social HTTPS pump, the relay allocation worker, and the relay tunnel.
WORKER_THREAD_MODULES = (
    "revival_api.py",
    "revival_crypto.py",
    "revival_http.py",
    "revival_social.py",
    "revival_store.py",
    "relay_host.py",
)

# Helpers in ``local_host`` that the readiness worker calls directly.
LOCAL_HOST_WORKER_FUNCTIONS = (
    "_probe_a2s",
    "_probe_owned_a2s",
    "_parse_netstat_udp_owner_pids",
    "_bounded_hidden_command_output",
    "_udp_port_owner_pids",
    "_append_local_host_log",
)


def parse(relative_path):
    path = PROJECT_ROOT / relative_path
    return path, ast.parse(path.read_text(encoding="utf-8"))


def nested_imports(node):
    """Return every import statement below a function definition."""
    found = []
    for child in ast.walk(node):
        if isinstance(child, (ast.Import, ast.ImportFrom)):
            found.append("line %d" % child.lineno)
    return found


@pytest.mark.parametrize("module_name", WORKER_THREAD_MODULES)
def test_worker_thread_modules_import_only_at_module_scope(module_name):
    path, tree = parse(module_name)
    offenders = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            offenders.extend(
                "%s.%s %s" % (module_name, node.name, location)
                for location in nested_imports(node)
            )
    assert not offenders, (
        "%s runs on a worker thread; these imports would deadlock on CPython "
        "2's import lock: %s" % (path.name, ", ".join(offenders))
    )


def test_local_host_readiness_helpers_import_only_at_module_scope():
    module_name = "local_host.py"
    _, tree = parse(module_name)
    offenders = []
    for node in tree.body:
        if (
            isinstance(node, ast.FunctionDef)
            and node.name in LOCAL_HOST_WORKER_FUNCTIONS
        ):
            offenders.extend(
                "%s %s" % (node.name, location) for location in nested_imports(node)
            )
    assert not offenders, (
        "the readiness worker calls these helpers off the main thread: %s"
        % ", ".join(offenders)
    )


def source_lines(relative_path):
    """Read a Python 2 module as text; CPython 3's ``ast`` cannot parse it."""
    return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8").splitlines()


def test_aoslib_run_does_not_enter_the_game_loop_during_its_own_import():
    lines = source_lines(Path("aoslib") / "run.py")
    assert "BootClass()" not in [line.strip() for line in lines if line[:1] != " "], (
        "aoslib/run.py must not construct BootClass at module scope; the game "
        "loop would then run inside 'import aoslib.run' and hold the import "
        "lock for the whole session"
    )
    assert "def boot():" in [line.strip() for line in lines], (
        "aoslib/run.py must expose boot() for callers to invoke after importing"
    )


def test_run_module_boots_only_when_executed_as_a_script():
    lines = [line.rstrip() for line in source_lines("run.py")]
    assert "def boot():" in lines, (
        "run.py must expose boot() so the launcher can start the loop itself"
    )
    guard = next(
        (index for index, line in enumerate(lines) if "__main__" in line and
         line.startswith("if ")),
        None,
    )
    assert guard is not None, (
        "run.py must only self-boot under if __name__ == '__main__'"
    )
    assert any(
        line.strip() == "boot()" for line in lines[guard + 1:guard + 4]
    ), "the __main__ guard in run.py must call boot()"


def test_launcher_boots_the_client_after_the_import_completes():
    _, tree = parse("launcher.py")
    game_start = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "game_start"
    )
    calls = [
        "%s.%s" % (node.func.value.id, node.func.attr)
        for node in ast.walk(game_start)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
    ]
    assert "run.boot" in calls, (
        "launcher.game_start must call run.boot() instead of relying on "
        "'import run' to start the game loop"
    )
