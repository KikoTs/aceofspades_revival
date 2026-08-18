# -*- coding: utf-8 -*-
"""Revival-backed implementation behind the recovered ``shared.steam`` ABI."""
from __future__ import absolute_import

import socket
import threading
import time

from revival_api import RevivalApiError
from revival_social import RevivalSocialClient

try:
    text_type = unicode
except NameError:
    text_type = str


def _text(value):
    if value is None:
        return u""
    if isinstance(value, text_type):
        return value
    try:
        return text_type(value)
    except Exception:
        return u""


def _integer(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return default


def _join_error(error):
    code = getattr(error, "code", "")
    if code == "lobby_not_found":
        return 1
    if code in ("lobby_invitation_required", "lobby_blocked"):
        return 2
    if code == "lobby_full":
        return 3
    return 4


class RevivalLobbyFacade(object):
    """Maps authoritative social snapshots onto the recovered lobby layout."""

    def __init__(self, state, ensure_lobby, queue_callback, debug=None):
        self.state = state
        self.ensure_lobby = ensure_lobby
        self.queue_callback = queue_callback
        self.debug = debug or (lambda message: None)
        self.client = None
        self._last_member_ids = set()
        self._last_lobby_id = 0
        self._pending_settings = {}
        self._pending_member_data = {}
        # A batch leaves ``_pending_*`` the moment its request starts, so it is
        # retained here until the service acknowledges it.  Without that, a sync
        # response issued before the write lands hydrates the older server
        # snapshot over the lobby and blanks the Match Settings panel.
        self._inflight_settings = {}
        self._inflight_member_data = {}
        self._pending_privacy = None
        self._pending_max_members = None
        self._flush_at = 0.0
        self._settings_request_active = False
        self._member_request_active = False
        self._seen_event_ids = set()
        self._seen_event_order = []
        self._lock = threading.RLock()

    def initialize(self):
        if self.client is not None:
            return True
        self.client = RevivalSocialClient(
            on_sync=self._on_sync,
            on_error=self._on_error,
            poll_interval=RevivalSocialClient.POLL_GAME_MENU,
        )
        account = self.client.api.account or {}
        legacy_id = _integer(account.get("legacy_id"), 0)
        if legacy_id:
            self.state["steam_id"] = legacy_id
        nickname = _text(account.get("nickname")).strip()
        if nickname:
            self.state["persona_name"] = nickname
        self.state["social_available"] = bool(self.client.available)
        return True

    def shutdown(self):
        if self.client is not None:
            self.client.shutdown()
        self.client = None

    def available(self):
        return bool(self.client is not None and self.client.available)

    def _on_error(self, error):
        self.state["social_available"] = self.available()
        self.state["social_error"] = _text(error)
        self.debug("Revival social request failed: %r" % (error,))

    def _member_payload(self, lobby):
        members = lobby.get("members") or []
        result = []
        for member in members:
            if not isinstance(member, dict):
                continue
            member_id = _integer(member.get("legacy_id"), 0)
            if not member_id:
                continue
            result.append(member_id)
            self.state["friend_records"][member_id] = dict(member)
        return result

    def _hydrate_lobby(self, payload):
        if not isinstance(payload, dict):
            return None
        lobby_id = _integer(payload.get("id"), 0)
        if not lobby_id:
            return None
        lobby = self.ensure_lobby(lobby_id)
        settings = payload.get("settings")
        if not isinstance(settings, dict):
            settings = {}
        lobby["data"] = dict((_text(key), _text(value)) for key, value in settings.items())
        lobby["data"]["Name"] = _text(payload.get("name"))
        lobby["data"]["MAX_PLAYERS"] = _text(payload.get("max_members"))
        lobby["data"]["NumMembers"] = _text(len(payload.get("members") or []))
        lobby["owner"] = _integer(payload.get("owner_id"), 0)
        lobby["members"] = self._member_payload(payload)
        lobby["member_data"] = {}
        for member in payload.get("members") or []:
            if not isinstance(member, dict):
                continue
            member_id = _integer(member.get("legacy_id"), 0)
            data = member.get("member_data")
            if member_id and isinstance(data, dict):
                lobby["member_data"][member_id] = dict(
                    (_text(key), _text(value)) for key, value in data.items()
                )
        lobby["max_players"] = _integer(payload.get("max_members"), 24)
        lobby["accessibility"] = {
            "invite": 0,
            "friends": 1,
            "open": 2,
        }.get(payload.get("privacy"), 0)
        lobby["revision"] = _text(payload.get("revision")) or u"1"
        lobby["social_state"] = _text(payload.get("state"))
        lobby["server_id"] = _text(payload.get("server_id"))
        if lobby["server_id"]:
            lobby["game_server"] = self._game_server_tuple(lobby["server_id"])
        else:
            lobby["game_server"] = None
        self._apply_local_overlay(lobby)
        return lobby

    def _apply_local_overlay(self, lobby):
        """Keep unacknowledged local edits visible over an older snapshot.

        Every hydration path replaces ``data``/``member_data`` wholesale with
        what the service last stored.  Queued and in-flight writes are replayed
        on top so a sync that crosses a local edit cannot momentarily erase the
        playlist, map rotation, or port the host is about to start with.
        """
        user_id = self.user_id()
        with self._lock:
            if _integer(lobby.get("owner"), 0) == user_id:
                lobby["data"].update(self._inflight_settings)
                lobby["data"].update(self._pending_settings)
            if user_id and user_id in (lobby.get("members") or ()):
                own_data = lobby["member_data"].setdefault(user_id, {})
                own_data.update(self._inflight_member_data)
                own_data.update(self._pending_member_data)

    def _game_server_tuple(self, identifier):
        try:
            host, port = identifier.rsplit(":", 1)
            host = socket.gethostbyname(host)
            blocks = [int(value) for value in host.split(".")]
            encoded = ((blocks[0] << 24) | (blocks[1] << 16) |
                       (blocks[2] << 8) | blocks[3])
            return encoded, int(port)
        except Exception:
            self.debug("invalid social server identifier: %r" % identifier)
            return None

    def _apply_friends(self, snapshot):
        friend_ids = []
        friend_lobbies = {}
        for friend in snapshot.get("friends") or []:
            if not isinstance(friend, dict) or friend.get("friendship_status") != "accepted":
                continue
            friend_id = _integer(friend.get("legacy_id"), 0)
            if not friend_id:
                continue
            friend_ids.append(friend_id)
            self.state["friend_records"][friend_id] = dict(friend)
            lobby_id = _integer(friend.get("current_lobby_id"), 0)
            if lobby_id:
                friend_lobbies[friend_id] = lobby_id
        self.state["friends"] = friend_ids
        self.state["friend_lobbies"] = friend_lobbies
        self.state["social_invitations"] = list(snapshot.get("invitations") or [])

    def _dispatch_events(self, snapshot, lobby_id):
        callbacks = self.state["callbacks"]
        for event in snapshot.get("events") or []:
            if not isinstance(event, dict):
                continue
            event_id = _text(event.get("id"))
            if event_id and event_id in self._seen_event_ids:
                continue
            if event_id:
                self._seen_event_ids.add(event_id)
                self._seen_event_order.append(event_id)
                if len(self._seen_event_order) > 1024:
                    expired = self._seen_event_order.pop(0)
                    self._seen_event_ids.discard(expired)
            event_type = event.get("type")
            actor_id = _integer(event.get("actor_id"), 0)
            payload = event.get("payload") or {}
            event_lobby = _integer(event.get("lobby_id"), lobby_id)
            if event_type == "lobby.chat":
                self.queue_callback(
                    callbacks.get("lobby_chat"),
                    actor_id,
                    _text(payload.get("message")),
                )
            elif event_type in (
                    "lobby.data_changed", "lobby.member_data_changed",
                    "lobby.owner_changed", "lobby.server_ready",
                    "lobby.starting", "lobby.in_game", "lobby.start_failed"):
                self.queue_callback(callbacks.get("lobby_data_changed"), event_lobby, True)
            elif event_type == "lobby.invited":
                self.queue_callback(
                    callbacks.get("lobby_join_request"),
                    _integer(payload.get("lobby_id"), event_lobby),
                )
            elif event_type == "lobby.kicked":
                self.queue_callback(callbacks.get("lobby_user_kicked"), self.user_id())

    def _on_sync(self, snapshot):
        self.state["social_available"] = True
        self.state["social_error"] = u""
        account = snapshot.get("account") or {}
        account_id = _integer(account.get("legacy_id"), 0)
        if account_id:
            self.state["steam_id"] = account_id
        nickname = _text(account.get("nickname")).strip()
        if nickname:
            self.state["persona_name"] = nickname
        self._apply_friends(snapshot)
        lobby_payload = snapshot.get("lobby")
        lobby = self._hydrate_lobby(lobby_payload)
        lobby_id = _integer(lobby_payload.get("id"), 0) if isinstance(lobby_payload, dict) else 0
        member_ids = set(lobby["members"] if lobby is not None else [])
        callbacks = self.state["callbacks"]
        if lobby_id and lobby_id == self._last_lobby_id:
            for joined in sorted(member_ids - self._last_member_ids):
                if joined != self.user_id():
                    self.queue_callback(callbacks.get("lobby_user_joined"), joined)
            for left in sorted(self._last_member_ids - member_ids):
                self.queue_callback(callbacks.get("lobby_user_left"), left)
        self.state["current_lobby"] = lobby_id
        self._dispatch_events(snapshot, lobby_id)
        self._last_lobby_id = lobby_id
        self._last_member_ids = member_ids
        if lobby_id:
            self.queue_callback(callbacks.get("lobby_data_changed"), lobby_id, True)

    def user_id(self):
        return _integer(self.state.get("steam_id"), 0)

    def update(self):
        if self.client is None:
            return
        lobby_id = _integer(self.state.get("current_lobby"), 0)
        lobby = self.state.get("lobbies", {}).get(lobby_id) if lobby_id else None
        own_data = (lobby or {}).get("member_data", {}).get(self.user_id(), {})
        in_game = _text(own_data.get("in-game")) == u"1"
        self.client.set_presence(
            "in_game" if in_game else ("in_lobby" if lobby_id else "online"),
            {"client": "game", "game_version": 168},
        )
        self.client.update()
        self.state["social_available"] = self.available()
        now = time.time()
        if now >= self._flush_at:
            self._flush_settings()
            self._flush_member_data()

    def _flush_settings(self):
        with self._lock:
            if self._settings_request_active or not self._pending_settings:
                return
            lobby_id = _integer(self.state.get("current_lobby"), 0)
            lobby = self.state["lobbies"].get(lobby_id)
            if not lobby or lobby.get("owner") != self.user_id() or not self.available():
                return
            pending = dict(self._pending_settings)
            privacy = self._pending_privacy
            max_members = self._pending_max_members
            revision = _text(lobby.get("revision")) or u"1"
            settings = dict(lobby.get("data") or {})
            self._pending_settings.clear()
            self._inflight_settings = pending
            self._pending_privacy = None
            self._pending_max_members = None
            self._settings_request_active = True

        values = {"settings": settings, "revision": revision}
        if privacy is not None:
            values["privacy"] = privacy
        if max_members is not None:
            values["max_members"] = max_members
        if settings.get("Name"):
            values["name"] = settings["Name"]

        def succeeded(result):
            self._settings_request_active = False
            with self._lock:
                self._inflight_settings = {}
            payload = (result or {}).get("lobby")
            hydrated = self._hydrate_lobby(payload)
            if hydrated is not None:
                self.queue_callback(
                    self.state["callbacks"].get("lobby_data_changed"),
                    hydrated["id"], True,
                )
            if self._pending_settings:
                self._flush_at = time.time() + 0.05

        def failed(error):
            self._settings_request_active = False
            with self._lock:
                # Newer queued edits win over the batch being restored.
                restored = dict(self._inflight_settings)
                restored.update(self._pending_settings)
                self._pending_settings = restored
                self._inflight_settings = {}
                if privacy is not None:
                    self._pending_privacy = privacy
                if max_members is not None:
                    self._pending_max_members = max_members
            self.queue_callback(
                self.state["callbacks"].get("lobby_data_changed"),
                lobby_id, False,
            )
            if getattr(error, "code", "") == "lobby_revision_conflict":
                # Our cached revision is behind the service (Start and Publish
                # both bump it).  Retrying with the same one only repeats the
                # 409 forever and the host's edits are never stored, so refresh
                # the authoritative snapshot before the next attempt.
                self.client.sync_now()
                self._flush_at = time.time() + 0.25
                return
            self._flush_at = time.time() + 1.0

        self.client.lobby_action(
            lobby_id, "update", succeeded, failed,
            coalesce_key="lobby-settings", **values
        )

    def _flush_member_data(self):
        with self._lock:
            if self._member_request_active or not self._pending_member_data:
                return
            lobby_id = _integer(self.state.get("current_lobby"), 0)
            if not lobby_id or not self.available():
                return
            pending = dict(self._pending_member_data)
            lobby = self.ensure_lobby(lobby_id)
            data = dict(lobby["member_data"].get(self.user_id(), {}))
            self._pending_member_data.clear()
            self._inflight_member_data = pending
            self._member_request_active = True

        def succeeded(result):
            self._member_request_active = False
            with self._lock:
                self._inflight_member_data = {}
            if self._pending_member_data:
                self._flush_at = time.time() + 0.05

        def failed(error):
            self._member_request_active = False
            with self._lock:
                restored = dict(self._inflight_member_data)
                restored.update(self._pending_member_data)
                self._pending_member_data = restored
                self._inflight_member_data = {}
            self._flush_at = time.time() + 1.0

        self.client.lobby_action(
            lobby_id, "member_update", succeeded, failed,
            coalesce_key="lobby-member-data", member_data=data,
        )

    def set_lobby_data(self, key, value):
        lobby_id = _integer(self.state.get("current_lobby"), 0)
        if not lobby_id:
            return False
        lobby = self.ensure_lobby(lobby_id)
        key = _text(key)
        value = _text(value)
        # The retail lobby rewrites its whole settings block on every refresh
        # tick.  ``data`` already carries queued and in-flight local edits, so
        # an identical value is either stored or on its way and must not queue
        # another revisioned write.
        if lobby["data"].get(key) == value:
            return True
        lobby["data"][key] = value
        with self._lock:
            self._pending_settings[key] = value
            self._flush_at = time.time() + 0.25
        return True

    def set_member_data(self, key, value):
        lobby_id = _integer(self.state.get("current_lobby"), 0)
        if not lobby_id:
            return False
        lobby = self.ensure_lobby(lobby_id)
        data = lobby["member_data"].setdefault(self.user_id(), {})
        key = _text(key)
        value = _text(value)
        if data.get(key) == value:
            return True
        data[key] = value
        with self._lock:
            self._pending_member_data[key] = value
            self._flush_at = time.time() + 0.25
        return True

    def set_privacy(self, accessibility):
        value = {0: "invite", 1: "friends", 2: "open"}.get(_integer(accessibility), "invite")
        lobby = self.ensure_lobby(self.state.get("current_lobby"))
        lobby["accessibility"] = _integer(accessibility)
        with self._lock:
            self._pending_privacy = value
            self._pending_settings["PRIVACY"] = _text(accessibility)
            lobby["data"]["PRIVACY"] = _text(accessibility)
            self._flush_at = time.time() + 0.25
        return True

    def set_max_members(self, maximum):
        lobby = self.ensure_lobby(self.state.get("current_lobby"))
        maximum = max(2, min(24, _integer(maximum, 24)))
        lobby["max_players"] = maximum
        lobby["data"]["MAX_PLAYERS"] = _text(maximum)
        with self._lock:
            self._pending_max_members = maximum
            self._pending_settings["MAX_PLAYERS"] = _text(maximum)
            self._flush_at = time.time() + 0.25
        return True

    def _resume_owned_lobby(self, created_callback):
        lobby_id = _integer(self.state.get("current_lobby"), 0)
        lobby = self.state.get("lobbies", {}).get(lobby_id)
        user_id = self.user_id()
        if (
                not lobby_id or not isinstance(lobby, dict) or
                _integer(lobby.get("owner"), 0) != user_id or
                user_id not in lobby.get("members", ())):
            return False
        self._last_lobby_id = lobby_id
        self._last_member_ids = set(lobby.get("members") or ())
        self.queue_callback(created_callback, lobby_id)
        return True

    def create_lobby(self, created_callback, error_callback):
        if not self.available():
            self.queue_callback(error_callback, 4)
            return False
        if self._resume_owned_lobby(created_callback):
            return True
        metadata = {
            "name": self.state.get("persona_name") or u"Revival Lobby",
            "privacy": "invite",
            "max_members": 24,
            "lobby_type": "normal",
            "settings": {},
        }

        def succeeded(result):
            lobby = self._hydrate_lobby((result or {}).get("lobby"))
            if lobby is None:
                self.queue_callback(error_callback, 4)
                return
            self.state["current_lobby"] = lobby["id"]
            self._last_lobby_id = lobby["id"]
            self._last_member_ids = set(lobby["members"])
            self.queue_callback(created_callback, lobby["id"])

        def failed(error):
            if getattr(error, "code", "") == "active_lobby_exists":
                def refreshed(snapshot):
                    if not self._resume_owned_lobby(created_callback):
                        self.queue_callback(error_callback, _join_error(error))

                def refresh_failed(refresh_error):
                    self.queue_callback(error_callback, _join_error(refresh_error))

                if self.client.sync_now(refreshed, refresh_failed):
                    return
            self.queue_callback(error_callback, _join_error(error))

        self.client.create_lobby(metadata, succeeded, failed)
        return True

    def join_lobby(self, lobby_id, joined_callback, error_callback,
                   invitation_id=None, blocking=False):
        lobby_id = _integer(lobby_id, 0)
        if not lobby_id or not self.available():
            self.queue_callback(error_callback, 4)
            return False

        def apply_result(result):
            lobby = self._hydrate_lobby((result or {}).get("lobby"))
            if lobby is None:
                raise RevivalApiError("Lobby join returned no lobby.", "invalid_response")
            self.state["current_lobby"] = lobby["id"]
            self._last_lobby_id = lobby["id"]
            self._last_member_ids = set(lobby["members"])
            return lobby

        if blocking:
            try:
                values = {}
                if invitation_id:
                    values["invitation_id"] = invitation_id
                result = self.client.api.social_lobby_action(lobby_id, "join", **values)
                lobby = apply_result(result)
                callback = self.state["callbacks"].get("lobby_join_request")
                if callable(callback):
                    callback(lobby["id"])
                return True
            except Exception as error:
                self.debug("blocking lobby join failed: %r" % (error,))
                return False

        def succeeded(result):
            try:
                lobby = apply_result(result)
            except Exception as error:
                self.queue_callback(error_callback, _join_error(error))
                return
            self.queue_callback(joined_callback, lobby["id"])

        def failed(error):
            self.queue_callback(error_callback, _join_error(error))

        values = {}
        if invitation_id:
            values["invitation_id"] = invitation_id
        self.client.lobby_action(
            lobby_id, "join", succeeded, failed, priority=True, **values
        )
        return True

    def leave_lobby(self, success=None, error=None):
        lobby_id = _integer(self.state.get("current_lobby"), 0)
        if not lobby_id:
            if callable(success):
                self.queue_callback(success, {"left": True, "idempotent": True})
            return

        def finished(result):
            self.state["current_lobby"] = 0
            self._last_lobby_id = 0
            self._last_member_ids = set()
            if callable(success):
                self.queue_callback(success, result or {"left": True})

        def failed(reason):
            if callable(error):
                self.queue_callback(error, reason)

        if self.available():
            self.client.lobby_action(
                lobby_id, "leave", finished, failed, priority=True
            )
        else:
            finished(None)

    def send_chat(self, message):
        lobby_id = _integer(self.state.get("current_lobby"), 0)
        if not lobby_id or not self.available():
            return False
        return self.client.lobby_action(
            lobby_id, "chat", priority=True, message=_text(message)
        )

    def enumerate_lobbies(self, callback, friends_only=False):
        if not self.available():
            return False

        def succeeded(result):
            accepted_friends = set(self.state.get("friends") or [])
            seen = set()
            for payload in (result or {}).get("lobbies") or []:
                if not isinstance(payload, dict):
                    continue
                owner_id = _integer(payload.get("owner_id"), 0)
                if friends_only and owner_id not in accepted_friends:
                    continue
                lobby = self._hydrate_lobby(payload)
                if lobby is not None and lobby["id"] not in seen:
                    seen.add(lobby["id"])
                    # Recovered ABI: exactly one positional lobby id.
                    self.queue_callback(callback, lobby["id"])

        self.client.request_lobbies(succeeded, lambda error: None)
        return True

    def invite(self, friend_id, success=None, error=None):
        lobby_id = _integer(self.state.get("current_lobby"), 0)
        if not lobby_id or not self.available():
            return False
        return self.client.lobby_action(
            lobby_id, "invite", success, error, priority=True,
            target=_text(friend_id)
        )

    def find_player(self, query, success=None, error=None):
        if not self.available():
            if callable(error):
                self.queue_callback(error, RevivalApiError(
                    "Social service is offline.", "social_unavailable"
                ))
            return False
        return self.client.request_friends(query, success, error)

    def friend_action(self, action, target, success=None, error=None):
        if not self.available():
            if callable(error):
                self.queue_callback(error, RevivalApiError(
                    "Social service is offline.", "social_unavailable"
                ))
            return False
        return self.client.friend_action(action, target, success, error)

    def start(self, success=None, error=None):
        lobby_id = _integer(self.state.get("current_lobby"), 0)
        if not lobby_id or not self.available():
            return False
        return self.client.lobby_action(
            lobby_id, "start", success, error, priority=True
        )

    def publish(self, relay_lobby_id, server_id, success=None, error=None):
        lobby_id = _integer(self.state.get("current_lobby"), 0)
        if not lobby_id or not self.available():
            return False
        return self.client.lobby_action(
            lobby_id, "publish", success, error, priority=True,
            relay_lobby_id=relay_lobby_id, server_id=server_id,
        )

    def start_failed(self, message, success=None, error=None):
        lobby_id = _integer(self.state.get("current_lobby"), 0)
        if not lobby_id or not self.available():
            return False
        return self.client.lobby_action(
            lobby_id, "start_failed", success, error, priority=True,
            message=_text(message)
        )

    def mark_in_game(self, success=None, error=None):
        lobby_id = _integer(self.state.get("current_lobby"), 0)
        if not lobby_id or not self.available():
            return False
        return self.client.lobby_action(
            lobby_id, "in_game", success, error, priority=True
        )

    def game_ticket(self, server_id, success=None, error=None):
        if not self.available():
            return False
        return self.client.enqueue(
            "game_ticket", (_text(server_id),),
            success=success, error=error, priority=True,
        )


__all__ = ["RevivalLobbyFacade"]
