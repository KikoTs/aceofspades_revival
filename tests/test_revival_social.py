from __future__ import annotations

import threading
import time
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import revival_wire_identity
from revival_api import RevivalApiError
from revival_social import RevivalSocialClient

FACADE_PATH = (
    Path(__file__).resolve().parents[1] / "shared" / "revival_lobby_facade.py"
)
FACADE_SPEC = importlib.util.spec_from_file_location(
    "revival_lobby_facade_under_test", FACADE_PATH
)
assert FACADE_SPEC is not None and FACADE_SPEC.loader is not None
facade_module = importlib.util.module_from_spec(FACADE_SPEC)
FACADE_SPEC.loader.exec_module(facade_module)
RevivalLobbyFacade = facade_module.RevivalLobbyFacade


class FakeApi:
    access_token = "token"
    account = {"legacy_id": "123", "nickname": "Tester"}

    def __init__(self):
        self.active = 0
        self.max_active = 0
        self.calls = []
        self.gate = threading.Event()

    def social_sync(self, cursor, instance_id, status, metadata):
        self.calls.append(("sync", cursor, status))
        return {
            "cursor": "1",
            "account": self.account,
            "friends": [],
            "blocks": [],
            "invitations": [],
            "lobby": None,
            "events": [],
        }

    def guarded(self, value):
        self.active += 1
        self.max_active = max(self.max_active, self.active)
        self.gate.wait(1.0)
        self.active -= 1
        self.calls.append(("guarded", value))
        return value

    def social_presence_offline(self, instance_id):
        self.calls.append(("offline", instance_id))
        return {"offline": True}


def drain_until(client, predicate, timeout=2.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        client.update()
        if predicate():
            return
        time.sleep(0.005)
    raise AssertionError("social worker did not finish in time")


def make_facade():
    state = {
        "steam_id": 123,
        "persona_name": "Tester",
        "social_available": True,
        "social_error": "",
        "social_invitations": [],
        "friends": [],
        "friend_records": {},
        "friend_lobbies": {},
        "lobbies": {},
        "current_lobby": 0,
        "callbacks": {},
    }

    def ensure_lobby(lobby_id):
        lobby_id = int(lobby_id)
        return state["lobbies"].setdefault(
            lobby_id,
            {
                "id": lobby_id,
                "owner": 0,
                "members": [],
                "data": {},
                "member_data": {},
                "max_players": 24,
                "accessibility": 0,
                "revision": "1",
                "game_server": None,
                "server_id": "",
            },
        )

    queued = []

    def queue_callback(callback, *args):
        if callable(callback):
            queued.append((callback, args))
            callback(*args)

    return RevivalLobbyFacade(state, ensure_lobby, queue_callback), state, queued


def test_http_worker_delivers_callbacks_only_from_update_thread():
    api = FakeApi()
    callback_threads = []
    client = RevivalSocialClient(api=api, poll_interval=60)
    client._next_poll = time.time() + 60
    client.enqueue(
        "guarded",
        ("done",),
        success=lambda value: callback_threads.append(threading.current_thread().ident),
    )
    client.update()
    api.gate.set()
    main_thread = threading.current_thread().ident
    drain_until(client, lambda: bool(callback_threads))

    assert callback_threads == [main_thread]
    assert api.calls[-1] == ("guarded", "done")


def test_social_client_never_runs_two_http_requests_at_once():
    api = FakeApi()
    results = []
    client = RevivalSocialClient(api=api, poll_interval=60)
    client._next_poll = time.time() + 60
    client.enqueue("guarded", (1,), success=results.append)
    client.enqueue("guarded", (2,), success=results.append)
    client.update()
    api.gate.set()
    drain_until(client, lambda: len(results) == 2)

    assert results == [1, 2]
    assert api.max_active == 1


def test_player_action_overtakes_a_queued_sync_request():
    api = FakeApi()
    client = RevivalSocialClient(api=api, poll_interval=60)
    client.sync_now()
    client.enqueue("guarded", ("start",))

    assert [job["method"] for job in client._pending] == [
        "guarded", "social_sync",
    ]


def test_periodic_poll_does_not_backlog_while_http_request_is_running():
    class BlockingSyncApi(FakeApi):
        def __init__(self):
            FakeApi.__init__(self)
            self.sync_started = threading.Event()
            self.sync_release = threading.Event()

        def social_sync(self, cursor, instance_id, status, metadata):
            self.calls.append(("sync-start", cursor, status))
            self.sync_started.set()
            self.sync_release.wait(1.0)
            self.calls.append(("sync-finish", cursor, status))
            return {
                "cursor": "1",
                "account": self.account,
                "friends": [],
                "blocks": [],
                "invitations": [],
                "lobby": None,
                "events": [],
            }

    api = BlockingSyncApi()
    client = RevivalSocialClient(api=api, poll_interval=60)
    client._next_poll = 0.0
    client.update()
    assert api.sync_started.wait(1.0)

    client.update()
    assert client._pending == []

    results = []
    client.enqueue("guarded", ("start",), success=results.append)
    api.gate.set()
    api.sync_release.set()
    drain_until(client, lambda: results == ["start"])

    assert [call[0] for call in api.calls] == [
        "sync-start", "sync-finish", "guarded",
    ]


def test_worker_chains_queued_action_without_another_ui_update():
    """A menu transition must not strand Start behind an in-flight poll."""

    class BlockingSyncApi(FakeApi):
        def __init__(self):
            FakeApi.__init__(self)
            self.sync_started = threading.Event()
            self.sync_release = threading.Event()

        def social_sync(self, cursor, instance_id, status, metadata):
            self.calls.append(("sync-start", cursor, status))
            self.sync_started.set()
            self.sync_release.wait(1.0)
            self.calls.append(("sync-finish", cursor, status))
            return {
                "cursor": "1",
                "account": self.account,
                "friends": [],
                "blocks": [],
                "invitations": [],
                "lobby": None,
                "events": [],
            }

    api = BlockingSyncApi()
    client = RevivalSocialClient(api=api, poll_interval=60)
    client._next_poll = 0.0
    client.update()
    assert api.sync_started.wait(1.0)

    client.enqueue("guarded", ("start",))
    api.gate.set()
    api.sync_release.set()

    deadline = time.time() + 1.0
    while time.time() < deadline and ("guarded", "start") not in api.calls:
        time.sleep(0.005)

    assert ("guarded", "start") in api.calls


def test_sync_failures_back_off_exponentially_and_cap():
    client = RevivalSocialClient(api=FakeApi(), poll_interval=3.0)
    job = {"sync": True, "error": None}
    client._deliver(job, None, RevivalApiError("offline", "service_unavailable"))
    assert client._backoff == 6.0
    client._deliver(job, None, RevivalApiError("offline", "service_unavailable"))
    assert client._backoff == 12.0
    for _ in range(8):
        client._deliver(job, None, RevivalApiError("offline", "service_unavailable"))
    assert client._backoff == client.MAX_BACKOFF


def test_duplicate_authoritative_events_fire_legacy_callback_once():
    facade, state, queued = make_facade()
    chats = []
    state["callbacks"]["lobby_chat"] = lambda actor, message: chats.append(
        (actor, message)
    )
    snapshot = {
        "events": [{
            "id": "77",
            "type": "lobby.chat",
            "lobby_id": "2000000001",
            "actor_id": "456",
            "payload": {"message": "hello"},
        }]
    }
    facade._dispatch_events(snapshot, 2000000001)
    facade._dispatch_events(snapshot, 2000000001)

    assert chats == [(456, "hello")]


def test_friend_lobby_enumeration_uses_exactly_one_callback_argument():
    facade, state, queued = make_facade()
    state["friends"] = [456]

    class FakeSocialClient:
        available = True

        def request_lobbies(self, success, error):
            success({
                "lobbies": [{
                    "id": "2000000001",
                    "owner_id": "456",
                    "name": "Friend Lobby",
                    "max_members": 24,
                    "privacy": "friends",
                    "revision": "1",
                    "settings": {},
                    "members": [],
                }]
            })
            return True

    facade.client = FakeSocialClient()
    received = []
    facade.enumerate_lobbies(lambda *args: received.append(args), friends_only=True)

    assert received == [(2000000001,)]


def test_pending_owner_settings_survive_an_older_sync_snapshot():
    facade, state, queued = make_facade()
    facade._pending_settings["Name"] = "Newest"
    facade._on_sync({
        "account": {"legacy_id": "123", "nickname": "Tester"},
        "friends": [],
        "invitations": [],
        "events": [],
        "lobby": {
            "id": "2000000001",
            "owner_id": "123",
            "name": "Old",
            "max_members": 24,
            "privacy": "invite",
            "revision": "1",
            "settings": {"Name": "Old"},
            "members": [{"legacy_id": "123", "member_data": {}}],
        },
    })

    assert state["lobbies"][2000000001]["data"]["Name"] == "Newest"


def test_wire_ticket_restores_unicode_visible_nickname_idempotently():
    manager = SimpleNamespace(config=SimpleNamespace(name="Ð˜Ð³Ñ€Ð°Ñ‡ æ—¥æœ¬èªž"))

    assert revival_wire_identity.activate(manager, "~ABCDEFGHIJKLMN") is True
    assert manager.config.name == "~ABCDEFGHIJKLMN"
    assert revival_wire_identity.restore(manager) is True
    assert manager.config.name == "Ð˜Ð³Ñ€Ð°Ñ‡ æ—¥æœ¬èªž"
    assert revival_wire_identity.restore(manager) is False


def test_invalid_wire_ticket_never_changes_visible_name():
    manager = SimpleNamespace(config=SimpleNamespace(name="Player"))

    assert revival_wire_identity.activate(manager, "not-a-ticket") is False
    assert manager.config.name == "Player"
