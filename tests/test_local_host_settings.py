from __future__ import annotations

import sys
import tomllib
from types import SimpleNamespace

import pytest

import local_host


def test_normalized_host_settings_keep_unicode_name_and_private_admin_password():
    settings = local_host.normalize_lobby_settings(
        {
            "Name": "Ignored lobby title",
            "SERVER_NAME": "Сървър 日本語",
            "ADMIN_PASSWORD": "private-admin-123",
            "MAX_PLAYERS": "12",
            "SERVER_PORT": "27015",
        }
    )

    assert settings["name"] == "Сървър 日本語"
    assert settings["admin_password"] == "private-admin-123"


def test_generated_session_toml_contains_essential_server_settings():
    payload = local_host.build_session_toml(
        {
            "name": "Two Client Test",
            "admin_password": "private-admin-123",
            "port": 28015,
            "max_players": 16,
            "match_length": 20,
            "mode": "ctf",
            "maps": ["London"],
            "bot_count": 4,
            "bot_difficulty": "hard",
            "rules": {},
        }
    )
    parsed = tomllib.loads(payload)

    assert parsed["server"] == {
        "name": "Two Client Test",
        "port": 28015,
        "max_players": 16,
        "tick_rate": 60,
    }
    assert parsed["admin"]["password"] == "private-admin-123"
    assert parsed["admin"]["log_commands"] is True
    assert parsed["game"]["default_mode"] == "ctf"
    assert parsed["lobby"]["map_rotation"] == ["London"]
    assert parsed["bots"]["fill_target"] == 4


def test_admin_password_is_process_local_and_never_requires_lobby_storage():
    local_host._LOCAL_ADMIN_PASSWORDS.clear()
    first = local_host.get_local_admin_password(77)

    assert first == local_host.get_local_admin_password(77)
    assert first != local_host.get_local_admin_password(78)
    assert len(first) >= local_host.MIN_ADMIN_PASSWORD_CHARACTERS


@pytest.mark.parametrize(
    "value",
    ["short", "has spaces", "line\nbreak"],
)
def test_admin_password_rejects_values_that_admin_command_cannot_parse(value):
    with pytest.raises(local_host.LocalHostError):
        local_host.normalize_admin_password(value)


def test_social_start_timeout_restores_button_and_shows_exact_error(monkeypatch):
    scheduled = []

    class FakeClock:
        @staticmethod
        def schedule_once(callback, delay):
            scheduled.append((callback, delay))

        @staticmethod
        def unschedule(callback):
            scheduled[:] = [entry for entry in scheduled if entry[0] is not callback]

    failures = []
    fake_steam = SimpleNamespace(
        SteamStartSocialLobby=lambda success, error: True,
        SteamSocialLobbyStartFailed=failures.append,
        SteamGetCurrentLobby=lambda: 77,
        SteamGetLobbyData=lambda lobby_id, key: {
            "Name": "Timeout Test",
            "PLAYLIST": "tdm",
            "MAP_ROTATION_FILENAME": "London",
            "MAX_PLAYERS": "12",
            "BOT_COUNT": "6",
            "BOT_DIFFICULTY": "normal",
            "SERVER_PORT": "27015",
        }.get(key, ""),
    )
    monkeypatch.setitem(sys.modules, "pyglet", SimpleNamespace(clock=FakeClock))
    monkeypatch.setitem(sys.modules, "shared.steam", fake_steam)
    monkeypatch.setattr(local_host, "_lobby_values", lambda ugc: {})

    manager = SimpleNamespace(
        hosted_ugc_map_filename="",
        big_text=SimpleNamespace(text=""),
        big_text_timer=0.0,
        set_big_text_message=lambda *args, **kwargs: None,
    )
    menu = SimpleNamespace(
        starting_game=False,
        ugc_mode=False,
        manager=manager,
        update_buttons_enabled_state=lambda: None,
    )

    assert local_host.start_lobby(menu) is True
    assert menu.starting_game is True
    assert len(scheduled) == 1

    timeout_callback, delay = scheduled[0]
    assert delay == local_host.SOCIAL_LOBBY_START_TIMEOUT_SECONDS
    timeout_callback(delay)

    assert menu.starting_game is False
    assert failures and "did not acknowledge Start" in failures[0]
    assert "did not acknowledge Start" in manager.big_text.text
    assert manager.big_text_timer == 8.0


def test_preflight_failure_restores_button_and_shows_exact_error(monkeypatch):
    monkeypatch.setattr(
        local_host,
        "_lobby_values",
        lambda ugc: (_ for _ in ()).throw(local_host.LocalHostError("bad port")),
    )
    manager = SimpleNamespace(
        hosted_ugc_map_filename="",
        big_text=SimpleNamespace(text=""),
        big_text_timer=0.0,
        set_big_text_message=lambda *args, **kwargs: None,
    )
    states = []
    menu = SimpleNamespace(
        starting_game=False,
        ugc_mode=False,
        manager=manager,
        update_buttons_enabled_state=lambda: states.append(menu.starting_game),
    )

    assert local_host.start_lobby(menu) is True
    assert states[0] is True
    assert menu.starting_game is False
    assert "bad port" in manager.big_text.text
    assert manager.big_text_timer == 8.0


# ---------------------------------------------------------------------------
# A finished, kicked or crashed match leaves the authoritative lobby in
# ``starting`` / ``in_game`` with a ``server_id`` for a server nobody runs.
# ``start`` is accepted in that state and changes nothing, so the host's next
# Start allocated a rate-limited relay the lobby never adopted and appeared to
# do nothing at all.  ``start_failed`` is the only transition back to
# ``forming``, and the only thing that clears the dead endpoint.
# ---------------------------------------------------------------------------


def make_start_environment(monkeypatch, state, scheduled):
    class FakeClock:
        @staticmethod
        def schedule_once(callback, delay):
            scheduled.append((callback, delay))

        @staticmethod
        def unschedule(callback):
            scheduled[:] = [entry for entry in scheduled if entry[0] is not callback]

        @staticmethod
        def schedule_interval(callback, interval):
            scheduled.append((callback, interval))

    calls = []

    def start_social(success, error):
        calls.append("start")
        return True

    def start_failed(message, success=None, error=None):
        calls.append("start_failed")
        if callable(success):
            success({"ok": True})
        return True

    fake_steam = SimpleNamespace(
        SteamStartSocialLobby=start_social,
        SteamSocialLobbyStartFailed=start_failed,
        SteamGetSocialLobbyState=lambda: state,
        SteamGetCurrentLobby=lambda: 77,
        SteamGetLobbyData=lambda lobby_id, key: "",
    )
    monkeypatch.setitem(sys.modules, "pyglet", SimpleNamespace(clock=FakeClock))
    monkeypatch.setitem(sys.modules, "shared.steam", fake_steam)
    monkeypatch.setattr(local_host, "_lobby_values", lambda ugc: {})

    manager = SimpleNamespace(
        hosted_ugc_map_filename="",
        big_text=SimpleNamespace(text=""),
        big_text_timer=0.0,
        set_big_text_message=lambda *args, **kwargs: None,
    )
    menu = SimpleNamespace(
        starting_game=False,
        ugc_mode=False,
        manager=manager,
        update_buttons_enabled_state=lambda: None,
    )
    return menu, calls


@pytest.mark.parametrize("state", ["in_game", "ready", "starting"])
def test_a_stuck_lobby_is_reclaimed_before_starting(monkeypatch, state):
    scheduled = []
    menu, calls = make_start_environment(monkeypatch, state, scheduled)

    local_host.start_lobby(menu)

    assert calls == ["start_failed", "start"], (
        "starting a %s lobby is accepted but does nothing, so it must be "
        "reclaimed first" % state
    )


def test_a_fresh_lobby_is_started_without_an_extra_round_trip(monkeypatch):
    scheduled = []
    menu, calls = make_start_environment(monkeypatch, "forming", scheduled)

    local_host.start_lobby(menu)

    assert calls == ["start"]


def test_an_unreadable_state_still_starts(monkeypatch):
    scheduled = []
    menu, calls = make_start_environment(monkeypatch, "", scheduled)

    local_host.start_lobby(menu)

    assert calls == ["start"]


def test_state_lookup_degrades_when_the_abi_lacks_the_accessor(monkeypatch):
    monkeypatch.setitem(
        sys.modules, "shared.steam", SimpleNamespace(SteamGetCurrentLobby=lambda: 0)
    )

    assert local_host.social_lobby_state() == ""


def test_reclaiming_reports_a_service_failure_as_handled(monkeypatch):
    def refuse(message, success=None, error=None):
        raise RuntimeError("service down")

    monkeypatch.setitem(
        sys.modules, "shared.steam",
        SimpleNamespace(SteamSocialLobbyStartFailed=refuse),
    )

    assert local_host.reclaim_social_lobby() is False
