"""Lobby settings must survive the round trip to the social service.

Hosting reads the match configuration straight back out of the lobby snapshot
(``local_host._lobby_values``), so a sync response that lands while a write is
still in flight used to blank the playlist, map rotation, and port a fraction of
a second before Start Game read them.  A revision conflict then retried the same
stale revision forever, so the host's edits were never stored at all.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from revival_api import RevivalApiError


FACADE_PATH = (
    Path(__file__).resolve().parents[1] / "shared" / "revival_lobby_facade.py"
)
FACADE_SPEC = importlib.util.spec_from_file_location(
    "revival_lobby_facade_settings_sync", FACADE_PATH
)
assert FACADE_SPEC is not None and FACADE_SPEC.loader is not None
facade_module = importlib.util.module_from_spec(FACADE_SPEC)
FACADE_SPEC.loader.exec_module(facade_module)
RevivalLobbyFacade = facade_module.RevivalLobbyFacade

USER_ID = 123
LOBBY_ID = 1


class FakeSocialClient:
    available = True

    def __init__(self):
        self.actions = []
        self.sync_requests = 0

    def lobby_action(self, lobby_id, action, success=None, error=None,
                     coalesce_key=None, priority=False, **values):
        recorded = dict(values)
        recorded["priority"] = priority
        self.actions.append(
            {
                "lobby_id": lobby_id,
                "action": action,
                "success": success,
                "error": error,
                "values": recorded,
            }
        )
        return True

    def sync_now(self, success=None, error=None):
        self.sync_requests += 1
        return True

    def set_presence(self, status, metadata=None):
        pass

    def update(self):
        pass


def make_facade():
    state = {
        "steam_id": USER_ID,
        "persona_name": "Tester",
        "social_available": True,
        "social_error": "",
        "social_invitations": [],
        "friends": [],
        "friend_records": {},
        "friend_lobbies": {},
        "lobbies": {},
        "current_lobby": LOBBY_ID,
        "callbacks": {},
    }

    def ensure_lobby(lobby_id):
        lobby_id = int(lobby_id)
        return state["lobbies"].setdefault(
            lobby_id,
            {
                "id": lobby_id,
                "owner": USER_ID,
                "members": [USER_ID],
                "data": {},
                "member_data": {},
                "max_players": 24,
                "accessibility": 0,
                "revision": "1",
                "game_server": None,
                "server_id": "",
            },
        )

    def queue_callback(callback, *args):
        if callable(callback):
            callback(*args)

    facade = RevivalLobbyFacade(state, ensure_lobby, queue_callback)
    facade.client = FakeSocialClient()
    ensure_lobby(LOBBY_ID)
    return facade, state


def server_snapshot(settings, revision="1"):
    return {
        "cursor": "2",
        "account": {"legacy_id": str(USER_ID), "nickname": "Tester"},
        "friends": [],
        "invitations": [],
        "events": [],
        "lobby": {
            "id": str(LOBBY_ID),
            "owner_id": str(USER_ID),
            "name": "Tester's Lobby",
            "max_members": 24,
            "privacy": "invite",
            "revision": revision,
            "state": "idle",
            "server_id": None,
            "settings": dict(settings),
            "members": [{"legacy_id": str(USER_ID), "member_data": {}}],
        },
    }


def start_flush(facade):
    facade._flush_at = 0.0
    facade._flush_settings()
    assert facade.client.actions, "the settings write was never sent"
    return facade.client.actions[-1]


def test_sync_during_an_inflight_write_keeps_the_local_settings():
    facade, state = make_facade()
    facade.set_lobby_data("PLAYLIST", "ctf")
    facade.set_lobby_data("SERVER_PORT", "27015")
    request = start_flush(facade)
    assert request["values"]["settings"]["PLAYLIST"] == "ctf"

    # The service answers an older poll that predates the write.
    facade._on_sync(server_snapshot({"MAX_PLAYERS": "24"}))

    data = state["lobbies"][LOBBY_ID]["data"]
    assert data["PLAYLIST"] == "ctf"
    assert data["SERVER_PORT"] == "27015"
    assert data["MAX_PLAYERS"] == "24"


def test_acknowledged_settings_stop_being_replayed():
    facade, state = make_facade()
    facade.set_lobby_data("PLAYLIST", "ctf")
    request = start_flush(facade)
    request["success"]({"lobby": server_snapshot({"PLAYLIST": "ctf"})["lobby"]})

    assert facade._inflight_settings == {}
    facade._on_sync(server_snapshot({"PLAYLIST": "tdm", "MAX_PLAYERS": "24"}))
    assert state["lobbies"][LOBBY_ID]["data"]["PLAYLIST"] == "tdm"


def test_revision_conflict_refreshes_before_retrying():
    facade, _ = make_facade()
    facade.set_lobby_data("PLAYLIST", "ctf")
    request = start_flush(facade)

    request["error"](
        RevivalApiError(
            "Lobby settings changed; refresh before retrying.",
            "lobby_revision_conflict",
            409,
        )
    )

    assert facade.client.sync_requests == 1, (
        "a stale revision must be refreshed, otherwise the retry repeats the "
        "same 409 forever and the host's edits are never stored"
    )
    assert facade._pending_settings["PLAYLIST"] == "ctf"
    assert facade._inflight_settings == {}


def test_other_failures_do_not_request_an_extra_refresh():
    facade, _ = make_facade()
    facade.set_lobby_data("PLAYLIST", "ctf")
    request = start_flush(facade)

    request["error"](RevivalApiError("Service is busy.", "http_error", 503))

    assert facade.client.sync_requests == 0
    assert facade._pending_settings["PLAYLIST"] == "ctf"


def test_failed_write_never_overwrites_a_newer_edit():
    facade, _ = make_facade()
    facade.set_lobby_data("PLAYLIST", "ctf")
    request = start_flush(facade)
    facade.set_lobby_data("PLAYLIST", "tdm")

    request["error"](RevivalApiError("Service is busy.", "http_error", 503))

    assert facade._pending_settings["PLAYLIST"] == "tdm"


@pytest.mark.parametrize(
    "setter, reader",
    (
        ("set_lobby_data", "_pending_settings"),
        ("set_member_data", "_pending_member_data"),
    ),
)
def test_rewriting_an_unchanged_value_queues_nothing(setter, reader):
    facade, _ = make_facade()
    getattr(facade, setter)("team_id", "1")
    getattr(facade, reader).clear()

    # The retail lobby rewrites its whole settings block on every refresh tick.
    getattr(facade, setter)("team_id", "1")

    assert getattr(facade, reader) == {}


# ---------------------------------------------------------------------------
# Hosting waits on the master four times.  Anything the player is blocked on
# belongs in the priority lane so it cannot queue behind a background poll.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "call, action",
    (
        (lambda f: f.start(), "start"),
        (lambda f: f.publish("relay", "1.2.3.4:40000"), "publish"),
        (lambda f: f.mark_in_game(), "in_game"),
        (lambda f: f.start_failed("nope"), "start_failed"),
        (lambda f: f.leave_lobby(), "leave"),
        (lambda f: f.send_chat("hi"), "chat"),
    ),
)
def test_player_actions_use_the_priority_lane(call, action):
    facade, _ = make_facade()

    call(facade)

    request = facade.client.actions[-1]
    assert request["action"] == action
    assert request["values"].get("priority") is True, (
        "%s blocks the player, so it must not queue behind a poll" % action
    )


def test_background_settings_writes_stay_serialized():
    facade, _ = make_facade()
    facade.set_lobby_data("PLAYLIST", "ctf")
    start_flush(facade)

    request = facade.client.actions[-1]
    assert request["action"] == "update"
    assert request["values"].get("priority") is not True, (
        "lobby settings are revisioned; they must keep their serialized order"
    )
