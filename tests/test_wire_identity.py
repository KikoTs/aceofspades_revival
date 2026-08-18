"""The join code has to reach the wire, not just the client config.

An identity-required match (every relay-hosted match) refuses any player whose
``NewPlayerConnection`` name is not a one-use join code, and the retail client
renders that refusal as "to connect to a ranked server, use the Ranked Match
option".  The game takes that name from ``SteamGetPersonaName``, so overriding
only ``config.name`` left the real nickname on the wire and every host was
thrown out of its own match at class selection.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STEAM_SOURCE = (PROJECT_ROOT / "shared" / "steam.py").read_text(encoding="utf-8")

CODE = "~AAAAAAAAAAAAAA"


@pytest.fixture
def wire_identity(monkeypatch):
    """Load the module against a stub ABI so the override can be observed."""
    calls = []
    stub = SimpleNamespace(
        SteamSetWireNameOverride=lambda value: calls.append(value) or True
    )
    monkeypatch.setitem(sys.modules, "shared.steam", stub)

    spec = importlib.util.spec_from_file_location(
        "revival_wire_identity_under_test",
        PROJECT_ROOT / "revival_wire_identity.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, calls


def make_manager():
    return SimpleNamespace(config=SimpleNamespace(name="KikoTs"))


def test_activating_a_code_puts_it_on_the_wire(wire_identity):
    module, calls = wire_identity
    manager = make_manager()

    assert module.activate(manager, CODE) is True

    assert calls == [CODE], (
        "the game sends SteamGetPersonaName in NewPlayerConnection, so the "
        "code must override that and not only config.name"
    )
    assert manager.config.name == CODE


def test_restoring_clears_the_wire_override(wire_identity):
    module, calls = wire_identity
    manager = make_manager()
    module.activate(manager, CODE)
    calls[:] = []

    assert module.restore(manager) is True

    assert calls == [""], "the real nickname must go back on the wire"
    assert manager.config.name == "KikoTs"


def test_a_malformed_code_is_never_put_on_the_wire(wire_identity):
    module, calls = wire_identity
    manager = make_manager()

    assert module.activate(manager, "KikoTs") is False
    assert module.activate(manager, "~tooshort") is False

    assert calls == []
    assert manager.config.name == "KikoTs"


def test_restore_is_idempotent(wire_identity):
    module, _ = wire_identity
    manager = make_manager()
    module.activate(manager, CODE)

    assert module.restore(manager) is True
    assert module.restore(manager) is False


def test_a_missing_override_in_the_abi_does_not_break_activation(monkeypatch):
    monkeypatch.setitem(sys.modules, "shared.steam", SimpleNamespace())
    spec = importlib.util.spec_from_file_location(
        "revival_wire_identity_no_abi",
        PROJECT_ROOT / "revival_wire_identity.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module.activate(make_manager(), CODE) is True


def test_the_abi_resolves_the_override_before_the_persona_name():
    body = STEAM_SOURCE[STEAM_SOURCE.index("def SteamGetPersonaName():"):]
    body = body[:body.index("\ndef ", 1)]
    assert "wire_name_override" in body, (
        "SteamGetPersonaName supplies the wire name; it must honour the "
        "one-use join code while a join is in flight"
    )
    assert body.index("wire_name_override") < body.index("persona_name"), (
        "the override has to win over the stored nickname"
    )


def test_the_override_is_part_of_the_client_state():
    assert '"wire_name_override": u""' in STEAM_SOURCE


def test_the_abi_exposes_a_setter():
    assert "def SteamSetWireNameOverride(value):" in STEAM_SOURCE
