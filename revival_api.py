# -*- coding: utf-8 -*-
"""Synchronous HTTP client used from launcher worker threads."""
from __future__ import print_function

import json
import os

# Every social method below runs on the client's HTTPS worker thread.  The game
# boots inside ``import aoslib.run``, so its main thread owns CPython 2's global
# import lock for the whole session; an ``import`` statement executed on any
# other thread would block forever.  Resolve these names at module import time.
try:
    from urllib import quote as url_quote
except ImportError:  # pragma: no cover - Python 3 test runs
    from urllib.parse import quote as url_quote

from revival_crypto import b64url_encode, new_seed, public_key, sign
from revival_http import HttpTransportError, request as http_request
from revival_store import (
    clear_session,
    get_secret,
    load_state,
    save_state,
    set_secret,
)


DEFAULT_API_BASE = "https://www.aosplay.net"
USER_AGENT = "AoS-Revival-Launcher/1.0 (protocol 168)"


class RevivalApiError(Exception):
    def __init__(self, message, code="api_error", status=None):
        Exception.__init__(self, message)
        self.message = message
        self.code = code
        self.status = status

    def __str__(self):
        try:
            text_type = unicode
        except NameError:
            return str(self.message)
        if isinstance(self.message, text_type):
            return self.message.encode("utf-8")
        return str(self.message)

    def __unicode__(self):
        try:
            text_type = unicode
        except NameError:
            return str(self.message)
        if isinstance(self.message, text_type):
            return self.message
        return str(self.message).decode("utf-8", "replace")


def service_unavailable(error):
    """Return whether an API failure should activate local offline behavior."""
    if not isinstance(error, RevivalApiError):
        return False
    return (
        error.code in ("network_error", "invalid_response", "invalid_server_list")
        or error.status is not None and error.status >= 500
    )


def player_facing_message(error):
    """Describe an API failure without blaming the player's session.

    A 5xx means the service could not do its job right now.  Repeating the
    raw wording ("Authentication is temporarily unavailable") reads as "you
    are signed out", which sends players off to re-login over an outage they
    cannot do anything about.
    """

    status = getattr(error, "status", None)
    code = getattr(error, "code", "")
    if code == "network_error":
        return (u"Could not reach the Revival service. Check your"
                u" connection and try again.")
    if status is not None and status >= 500:
        return (u"The Revival service is temporarily unavailable."
                u" Your sign-in is still fine - please try again shortly.")
    if code == "authentication_required":
        return u"Sign in again to use this feature."
    message = getattr(error, "message", None) or _text(error)
    return message or u"The Revival service could not complete this action."


def _text(value):
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return value


def _bounded_guest_name(value, fingerprint):
    """Return a human-readable name that fits Protocol 168's 15-byte field."""
    value = _text(value or u"")
    try:
        text_type = unicode
    except NameError:
        text_type = str
    if not isinstance(value, text_type):
        value = text_type(value)
    value = u" ".join(value.split()).strip()
    if not value or value.startswith(u"~"):
        value = u"Guest-" + _text(fingerprint)
    encoded = value.encode("utf-8")[:15]
    while encoded:
        try:
            return encoded.decode("utf-8")
        except UnicodeDecodeError:
            encoded = encoded[:-1]
    return u"Guest"


class RevivalClient(object):
    def __init__(self, api_base=None):
        self.state = load_state()
        configured = api_base or os.environ.get("AOS_API_BASE")
        self.api_base = (configured or self.state.get("api_base") or DEFAULT_API_BASE).rstrip("/")
        self.service_available = None
        self.last_service_error = None

    @property
    def account(self):
        value = self.state.get("account")
        return value if isinstance(value, dict) else None

    @property
    def access_token(self):
        value = get_secret(self.state, "access_token")
        return _text(value) if value else None

    def _request(self, path, method="GET", payload=None, token=None, timeout=10):
        url = self.api_base + path
        body = None
        headers = {
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        }
        if payload is not None:
            body = json.dumps(payload, separators=(",", ":"))
            if not isinstance(body, bytes):
                body = body.encode("utf-8")
            headers["Content-Type"] = "application/json"
        if token:
            headers["Authorization"] = "Bearer " + token
        try:
            status, raw = http_request(
                url,
                method=method,
                headers=headers,
                body=body,
                timeout=timeout,
            )
        except HttpTransportError as error:
            api_error = RevivalApiError(
                "Could not reach the Revival service: %s" % error,
                "network_error",
            )
            self.service_available = False
            self.last_service_error = api_error
            raise api_error

        self.service_available = status < 500

        if status < 200 or status >= 300:
            try:
                detail = json.loads(_text(raw))
            except (ValueError, TypeError):
                detail = {}
            api_error = RevivalApiError(
                detail.get("message") or detail.get("detail") or "The Revival service rejected this request.",
                detail.get("error") or "http_error",
                status,
            )
            self.last_service_error = api_error
            raise api_error

        try:
            result = json.loads(_text(raw))
        except (ValueError, TypeError):
            api_error = RevivalApiError(
                "The Revival service returned invalid data.",
                "invalid_response",
                status,
            )
            self.service_available = False
            self.last_service_error = api_error
            raise api_error
        self.service_available = True
        self.last_service_error = None
        return result

    def _accept_session(self, response):
        token = response.get("access_token")
        account = response.get("account")
        if not token or not isinstance(account, dict):
            raise RevivalApiError("The sign-in response did not contain a launcher session.", "invalid_session")
        self.state["account"] = account
        self.state["session_expires_at"] = (response.get("session") or {}).get("expires_at")
        self.state["api_base"] = self.api_base
        set_secret(self.state, "access_token", token)
        save_state(self.state)
        return response

    def register(self, username, password):
        response = self._request(
            "/api/auth/register",
            "POST",
            {"username": username, "password": password, "client": "launcher"},
        )
        return self._accept_session(response)

    def login(self, username, password):
        response = self._request(
            "/api/auth/login",
            "POST",
            {"username": username, "password": password, "client": "launcher"},
        )
        return self._accept_session(response)

    def recover(self, username, recovery_code, new_password):
        response = self._request(
            "/api/auth/recover",
            "POST",
            {
                "username": username,
                "recovery_code": recovery_code,
                "new_password": new_password,
                "client": "launcher",
            },
        )
        return self._accept_session(response)

    def _offline_guest_session(self, seed, preferred_name=None, reason=None):
        """Persist an unranked local guest that never impersonates an account."""
        fingerprint = b64url_encode(public_key(seed))[:8]
        account = {
            "nickname": _bounded_guest_name(preferred_name, fingerprint),
            "legacy_id": "LOCAL-" + fingerprint.upper(),
            "ranked_eligible": False,
            "account_type": "guest",
            "identity_type": "guest_offline",
            "offline": True,
            "guest_fingerprint": fingerprint,
        }
        clear_session(self.state)
        self.state["account"] = account
        self.state["api_base"] = self.api_base
        save_state(self.state)
        return {
            "account": account,
            "offline": True,
            "offline_reason": (
                _text(getattr(reason, "message", reason)) if reason else None
            ),
        }

    def guest_login(self, preferred_name=None, force_online=False):
        """Authenticate a guest online, or preserve it locally when offline."""
        seed = get_secret(self.state, "guest_seed")
        if not seed or len(seed) != 32:
            seed = new_seed()
            set_secret(self.state, "guest_seed", seed)
            save_state(self.state)
        if self.service_available is False and not force_online:
            return self._offline_guest_session(
                seed,
                preferred_name,
                self.last_service_error,
            )
        public = public_key(seed)
        try:
            challenge = self._request(
                "/api/auth/guest/challenge",
                "POST",
                {"public_key": b64url_encode(public)},
                timeout=4,
            )
            message = challenge.get("message")
            nonce = challenge.get("nonce")
            challenge_id = challenge.get("challenge_id")
            if not message or not nonce or not challenge_id:
                raise RevivalApiError(
                    "Guest challenge was incomplete.",
                    "invalid_guest_challenge",
                )
            signature = sign(seed, message.encode("utf-8"))
            response = self._request(
                "/api/auth/guest/complete",
                "POST",
                {
                    "challenge_id": challenge_id,
                    "nonce": nonce,
                    "signature": b64url_encode(signature),
                    "client": "launcher",
                },
                timeout=4,
            )
        except RevivalApiError as error:
            if service_unavailable(error):
                return self._offline_guest_session(seed, preferred_name, error)
            raise
        return self._accept_session(response)

    def refresh_identity(self):
        token = self.access_token
        if not token:
            return None
        response = self._request("/api/auth/me", token=token)
        if not response.get("authenticated"):
            self.forget_session()
            return None
        self.state["account"] = response.get("account")
        save_state(self.state)
        return self.account

    def forget_session(self):
        clear_session(self.state)
        save_state(self.state)

    def logout(self):
        token = self.access_token
        if token:
            try:
                self._request("/api/auth/logout", "POST", {}, token=token)
            except RevivalApiError:
                pass
        self.forget_session()

    def servers(self):
        result = self._request("/api/serverlist", timeout=8)
        if not isinstance(result, list):
            error = RevivalApiError(
                "Server list has an invalid shape.",
                "invalid_server_list",
            )
            self.service_available = False
            self.last_service_error = error
            raise error
        return result

    def game_ticket(self, server_id):
        token = self.access_token
        if not token:
            raise RevivalApiError("Choose Sign in or Play as guest first.", "authentication_required")
        result = self._request(
            "/api/auth/game-ticket",
            "POST",
            {"server_id": server_id},
            token=token,
        )
        ticket = result.get("join_code") or result.get("ticket")
        if not ticket or len(ticket.encode("ascii")) != 15 or not ticket.startswith("~"):
            raise RevivalApiError("Master service returned an incompatible join code.", "invalid_join_code")
        return ticket

    def create_lobby(self, metadata):
        """Allocate one scoped, relay-backed public Match Lobby."""

        token = self.access_token
        if not token:
            raise RevivalApiError(
                "Sign in or create an online guest before hosting publicly.",
                "authentication_required",
            )
        result = self._request(
            "/api/lobbies",
            "POST",
            metadata,
            token=token,
            timeout=8,
        )
        if not isinstance(result, dict) or not result.get("created"):
            raise RevivalApiError(
                "Master service returned an invalid lobby allocation.",
                "invalid_lobby_allocation",
            )
        return result

    def close_lobby(self, lobby_id, server_token):
        """Release one public listing with its ephemeral lobby credential."""

        return self._request(
            "/api/lobbies/%s" % lobby_id,
            "DELETE",
            token=server_token,
            timeout=4,
        )

    # Social methods deliberately remain synchronous.  The game and launcher
    # each own a single-worker scheduler which serializes these calls and
    # delivers every result on their UI/main thread.
    def social_sync(self, cursor, client_instance_id, status="online", metadata=None):
        token = self.access_token
        if not token:
            raise RevivalApiError(
                "Social features require an online Revival account.",
                "authentication_required",
            )
        query = [
            "cursor=" + url_quote(str(cursor or "0")),
            "client_instance_id=" + url_quote(str(client_instance_id)),
            "status=" + url_quote(str(status or "online")),
        ]
        if metadata:
            encoded = json.dumps(metadata, separators=(",", ":"))
            if not isinstance(encoded, bytes):
                encoded = encoded.encode("utf-8")
            query.append("metadata=" + url_quote(encoded))
        return self._request(
            "/api/social/sync?" + "&".join(query),
            token=token,
            timeout=6,
        )

    def social_presence_offline(self, client_instance_id):
        token = self.access_token
        if not token:
            return {"offline": True}
        return self._request(
            "/api/social/sync",
            "DELETE",
            {"client_instance_id": client_instance_id},
            token=token,
            timeout=4,
        )

    def social_friends(self, query=None):
        token = self.access_token
        if not token:
            raise RevivalApiError("Sign in to use Friends.", "authentication_required")
        path = "/api/social/friends"
        if query:
            value = query.encode("utf-8") if not isinstance(query, bytes) else query
            path += "?query=" + url_quote(value)
        return self._request(path, token=token, timeout=6)

    def social_friend_action(self, action, target):
        token = self.access_token
        if not token:
            raise RevivalApiError("Sign in to use Friends.", "authentication_required")
        return self._request(
            "/api/social/friends",
            "POST",
            {"action": action, "target": str(target)},
            token=token,
            timeout=6,
        )

    def social_lobbies(self):
        token = self.access_token
        if not token:
            raise RevivalApiError("Sign in to browse social lobbies.", "authentication_required")
        return self._request("/api/social/lobbies", token=token, timeout=6)

    def social_create_lobby(self, metadata):
        token = self.access_token
        if not token:
            raise RevivalApiError("Sign in to create a social lobby.", "authentication_required")
        payload = dict(metadata or {})
        payload["action"] = "create"
        return self._request(
            "/api/social/lobbies",
            "POST",
            payload,
            token=token,
            timeout=6,
        )

    def social_lobby_action(self, lobby_id, action, **values):
        token = self.access_token
        if not token:
            raise RevivalApiError("Sign in to use social lobbies.", "authentication_required")
        payload = dict(values)
        payload["action"] = action
        return self._request(
            "/api/social/lobbies/%s" % lobby_id,
            "POST",
            payload,
            token=token,
            timeout=8,
        )
