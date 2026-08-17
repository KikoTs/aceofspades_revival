# -*- coding: utf-8 -*-
"""Single-worker HTTPS synchronizer for Revival social state.

The worker never calls game or launcher callbacks.  ``update`` must be called
from the owning UI thread and is the only place completed work is delivered.
Compatible with the game's CPython 2.7 frozen runtime and Python 3 tests.
"""
from __future__ import absolute_import

import threading
import time
import uuid

from revival_api import RevivalApiError, RevivalClient, service_unavailable


class RevivalSocialClient(object):
    POLL_ACTIVE_LOBBY = 1.0
    POLL_GAME_MENU = 3.0
    POLL_LAUNCHER = 5.0
    MAX_BACKOFF = 30.0

    def __init__(self, api=None, on_sync=None, on_error=None, poll_interval=None):
        self.api = api or RevivalClient()
        self.on_sync = on_sync
        self.on_error = on_error
        self.client_instance_id = str(uuid.uuid4())
        self.cursor = "0"
        self.snapshot = {
            "friends": [],
            "blocks": [],
            "invitations": [],
            "lobby": None,
            "events": [],
        }
        self._lock = threading.RLock()
        self._pending = []
        self._completed = []
        self._running = False
        self._closed = False
        self._next_poll = 0.0
        self._base_interval = float(poll_interval or self.POLL_GAME_MENU)
        self._backoff = self._base_interval
        self._presence_status = "online"
        self._presence_metadata = {}
        self.available = bool(self.api.access_token and not (self.api.account or {}).get("offline"))
        self.last_error = None

    def set_poll_interval(self, interval):
        self._base_interval = max(0.5, float(interval))
        self._backoff = self._base_interval
        self._next_poll = min(self._next_poll, time.time() + self._base_interval)

    def set_presence(self, status, metadata=None):
        self._presence_status = status or "online"
        self._presence_metadata = dict(metadata or {})

    def sync_now(self, success=None, error=None):
        """Queue one authoritative refresh ahead of the next timed poll."""
        return self.enqueue(
            "social_sync",
            (
                self.cursor,
                self.client_instance_id,
                self._presence_status,
                self._presence_metadata,
            ),
            success=success,
            error=error,
            coalesce_key="social-sync",
        )

    def enqueue(self, method_name, args=None, kwargs=None,
                success=None, error=None, coalesce_key=None):
        if self._closed:
            return False
        job = {
            "method": method_name,
            "args": tuple(args or ()),
            "kwargs": dict(kwargs or {}),
            "success": success,
            "error": error,
            "coalesce": coalesce_key,
            "sync": method_name == "social_sync",
        }
        with self._lock:
            if coalesce_key is not None:
                self._pending = [
                    pending for pending in self._pending
                    if pending.get("coalesce") != coalesce_key
                ]
            if job.get("sync"):
                self._pending.append(job)
            else:
                # Periodic reads must never hold an explicit player action
                # behind a poll which has not started yet.  Preserve FIFO
                # ordering between mutations while moving them ahead of the
                # first queued synchronization request.
                insert_at = len(self._pending)
                for index, pending in enumerate(self._pending):
                    if pending.get("sync"):
                        insert_at = index
                        break
                self._pending.insert(insert_at, job)
        return True

    def friend_action(self, action, target, success=None, error=None):
        return self.enqueue(
            "social_friend_action",
            (action, target),
            success=success,
            error=error,
        )

    def create_lobby(self, metadata, success=None, error=None):
        return self.enqueue(
            "social_create_lobby",
            (metadata,),
            success=success,
            error=error,
        )

    def lobby_action(self, lobby_id, action, success=None, error=None,
                     coalesce_key=None, **values):
        return self.enqueue(
            "social_lobby_action",
            (lobby_id, action),
            values,
            success,
            error,
            coalesce_key,
        )

    def request_lobbies(self, success=None, error=None):
        return self.enqueue(
            "social_lobbies",
            success=success,
            error=error,
            coalesce_key="lobby-list",
        )

    def request_friends(self, query=None, success=None, error=None):
        return self.enqueue(
            "social_friends",
            (query,),
            success=success,
            error=error,
            coalesce_key=("friend-lookup" if query else "friend-list"),
        )

    def _queue_poll(self):
        if not self.available or self._closed:
            return
        with self._lock:
            # A running request is already the sole network operation.  Do
            # not build a permanent one-poll backlog while it is in flight;
            # that backlog used to delay Start Game indefinitely at the
            # one-second active-lobby polling interval.
            if self._running or any(job.get("sync") for job in self._pending):
                return
            self._pending.append({
                "method": "social_sync",
                "args": (
                    self.cursor,
                    self.client_instance_id,
                    self._presence_status,
                    self._presence_metadata,
                ),
                "kwargs": {},
                "success": None,
                "error": None,
                "coalesce": "social-sync",
                "sync": True,
            })

    def _start_next(self):
        with self._lock:
            if self._running or not self._pending:
                return
            job = self._pending.pop(0)
            self._running = True

        def worker():
            result = None
            failure = None
            try:
                method = getattr(self.api, job["method"])
                result = method(*job["args"], **job["kwargs"])
            except Exception as exc:
                failure = exc
            with self._lock:
                self._completed.append((job, result, failure))
                self._running = False
            if self._closed:
                self._start_next()

        thread = threading.Thread(target=worker, name="RevivalSocialHttp")
        thread.daemon = True
        thread.start()

    def _deliver(self, job, result, failure):
        if failure is not None:
            self.last_error = failure
            if job.get("sync"):
                if isinstance(failure, RevivalApiError) and failure.code == "authentication_required":
                    self.available = False
                delay = self._backoff
                self._backoff = min(self.MAX_BACKOFF, max(self._base_interval, delay * 2.0))
                self._next_poll = time.time() + delay
            callback = job.get("error")
            if callable(callback):
                callback(failure)
            if callable(self.on_error) and (job.get("sync") or service_unavailable(failure)):
                self.on_error(failure)
            return

        self.last_error = None
        self.available = bool(self.api.access_token)
        if job.get("sync"):
            if not isinstance(result, dict):
                return
            self.cursor = str(result.get("cursor") or self.cursor)
            self.snapshot = result
            lobby = result.get("lobby")
            self._base_interval = (
                self.POLL_ACTIVE_LOBBY if isinstance(lobby, dict)
                else max(self.POLL_GAME_MENU, self._base_interval)
            )
            self._backoff = self._base_interval
            self._next_poll = time.time() + self._base_interval
            if callable(self.on_sync):
                self.on_sync(result)
        callback = job.get("success")
        if callable(callback):
            callback(result)

    def update(self):
        """Drain worker results and callbacks on the caller's main thread."""
        with self._lock:
            completed = list(self._completed)
            self._completed[:] = []
        for job, result, failure in completed:
            self._deliver(job, result, failure)
        if self.available and time.time() >= self._next_poll:
            self._queue_poll()
        self._start_next()

    def shutdown(self):
        if self._closed:
            return
        self.enqueue(
            "social_presence_offline",
            (self.client_instance_id,),
            coalesce_key="presence-offline",
        )
        # Give the normal update loop a chance to start the final request.  It
        # remains daemonized so shutdown can never hang on a network outage.
        self._start_next()
        self._closed = True


__all__ = ["RevivalSocialClient"]
