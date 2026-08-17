from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


def _unexpected_steamworks_call(*args, **kwargs):
    raise AssertionError("the compatibility facade attempted to use Steamworks")


def _load_steam_facade(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    package = ModuleType("shared")
    package.__path__ = [str(root / "shared")]
    monkeypatch.setitem(sys.modules, "shared", package)

    facade_spec = importlib.util.spec_from_file_location(
        "shared.revival_lobby_facade",
        root / "shared" / "revival_lobby_facade.py",
    )
    facade = importlib.util.module_from_spec(facade_spec)
    monkeypatch.setitem(sys.modules, "shared.revival_lobby_facade", facade)
    facade_spec.loader.exec_module(facade)

    steam_spec = importlib.util.spec_from_file_location(
        "steamless_facade_under_test",
        root / "shared" / "steam.py",
    )
    steam = importlib.util.module_from_spec(steam_spec)
    steam_spec.loader.exec_module(steam)
    return steam


def test_legacy_auth_and_dlc_calls_never_touch_steamworks(monkeypatch):
    steam = _load_steam_facade(monkeypatch)
    monkeypatch.setattr(steam._backend, "initialize", _unexpected_steamworks_call)
    monkeypatch.setattr(
        steam._backend,
        "create_session_ticket",
        _unexpected_steamworks_call,
    )
    monkeypatch.setattr(
        steam._backend,
        "cancel_session_ticket",
        _unexpected_steamworks_call,
    )
    monkeypatch.setattr(
        steam._backend,
        "is_dlc_installed",
        _unexpected_steamworks_call,
    )
    monkeypatch.setattr(steam._backend, "update", _unexpected_steamworks_call)

    assert steam.SteamGetSessionTicket() == ""
    assert steam.SteamIsDLCInstalled(420650) is True
    steam.SteamCancelSessionTicket()
    steam.SteamUpdateServer()
