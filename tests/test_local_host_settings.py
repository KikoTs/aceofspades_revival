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
