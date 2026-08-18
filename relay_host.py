# -*- coding: utf-8 -*-
"""Authenticated host-side tunnel for the AoS Revival UDP lobby relay.

The native retail client and bundled BattleSpades server continue to exchange
ordinary ENet/A2S datagrams.  This module frames only the public relay hop and
uses one loopback UDP socket per remote client slot so ENet still observes
distinct peers.
"""
from __future__ import print_function

import base64
import hashlib
import hmac
import os
import select
import socket
import struct
import threading
import time
import uuid

# Resolved here, not inside the allocation helper below: the game boots inside
# ``import aoslib.run`` and therefore holds CPython 2's global import lock for
# the whole session, so an ``import`` on the allocation worker thread would
# block forever instead of returning a relay.
from revival_api import RevivalClient


MAGIC = b"AOSR"
VERSION = 1
HEADER_BYTES = 36
MAC_BYTES = 32
MAX_PAYLOAD_BYTES = 32 * 1024

HELLO = 1
ACK = 2
HOST_TO_CLIENT = 3
CLIENT_TO_HOST = 4
KEEPALIVE = 5
CLOSE = 6
VALID_TYPES = set((HELLO, ACK, HOST_TO_CLIENT, CLIENT_TO_HOST, KEEPALIVE, CLOSE))


class RelayTunnelError(Exception):
    """Raised when a relay allocation or tunnel handshake is invalid."""


def _bytes(value):
    if isinstance(value, bytes):
        return value
    return value.encode("utf-8")


def decode_host_key(value):
    """Decode one canonical 32-byte base64url host key."""

    raw = _bytes(value)
    if len(raw) != 43:
        raise RelayTunnelError("Relay host key has an invalid length.")
    try:
        decoded = base64.urlsafe_b64decode(raw + b"=")
    except (TypeError, ValueError):
        raise RelayTunnelError("Relay host key is not valid base64url.")
    canonical = base64.urlsafe_b64encode(decoded).rstrip(b"=")
    if len(decoded) != 32 or canonical != raw:
        raise RelayTunnelError("Relay host key is not canonical.")
    return decoded


def _constant_equals(left, right):
    compare = getattr(hmac, "compare_digest", None)
    if compare is not None:
        return compare(left, right)
    if len(left) != len(right):
        return False
    result = 0
    for first, second in zip(bytearray(left), bytearray(right)):
        result |= first ^ second
    return result == 0


def encode_frame(frame_type, allocation_id, sequence, client_id, payload, key):
    """Encode one v1 frame exactly as documented by the master service."""

    if frame_type not in VALID_TYPES:
        raise RelayTunnelError("Unknown relay frame type.")
    payload = _bytes(payload or b"")
    if len(payload) > MAX_PAYLOAD_BYTES:
        raise RelayTunnelError("Relay payload is too large.")
    try:
        allocation = uuid.UUID(str(allocation_id)).bytes
    except (AttributeError, TypeError, ValueError):
        raise RelayTunnelError("Relay allocation id is invalid.")
    sequence = int(sequence)
    client_id = int(client_id)
    if sequence < 0 or sequence > 0xffffffffffffffff:
        raise RelayTunnelError("Relay sequence is out of range.")
    if client_id < 0 or client_id > 0xffffffff:
        raise RelayTunnelError("Relay client slot is out of range.")
    header = struct.pack(
        "!4sBB16sQIH",
        MAGIC,
        VERSION,
        frame_type,
        allocation,
        sequence,
        client_id,
        len(payload),
    )
    unsigned = header + payload
    return unsigned + hmac.new(key, unsigned, hashlib.sha256).digest()


def decode_frame(message, key, expected_allocation_id=None):
    """Authenticate and decode one relay frame, returning ``None`` on drop."""

    if not isinstance(message, bytes):
        message = bytes(message)
    if len(message) < HEADER_BYTES + MAC_BYTES:
        return None
    if len(message) > HEADER_BYTES + MAX_PAYLOAD_BYTES + MAC_BYTES:
        return None
    try:
        magic, version, frame_type, allocation, sequence, client_id, length = (
            struct.unpack("!4sBB16sQIH", message[:HEADER_BYTES])
        )
    except struct.error:
        return None
    if magic != MAGIC or version != VERSION or frame_type not in VALID_TYPES:
        return None
    if len(message) != HEADER_BYTES + length + MAC_BYTES:
        return None
    unsigned = message[:-MAC_BYTES]
    supplied = message[-MAC_BYTES:]
    expected = hmac.new(key, unsigned, hashlib.sha256).digest()
    if not _constant_equals(supplied, expected):
        return None
    allocation_id = str(uuid.UUID(bytes=allocation))
    if (
        expected_allocation_id is not None
        and allocation_id.lower() != str(expected_allocation_id).lower()
    ):
        return None
    return {
        "type": frame_type,
        "allocation_id": allocation_id,
        "sequence": sequence,
        "client_id": client_id,
        "payload": message[HEADER_BYTES:HEADER_BYTES + length],
    }


class RelayHostTunnel(object):
    """Own one outbound relay socket and per-remote loopback proxy sockets."""

    def __init__(self, allocation_id, host_key, relay_host, relay_port,
                 local_port, keepalive_seconds=15, logger=None):
        self.allocation_id = str(uuid.UUID(str(allocation_id)))
        self.key = decode_host_key(host_key)
        self.relay_host = str(relay_host)
        self.relay_port = int(relay_port)
        self.local_port = int(local_port)
        self.keepalive_seconds = min(60.0, max(5.0, float(keepalive_seconds)))
        if not 1 <= self.relay_port <= 65535 or not 1 <= self.local_port <= 65535:
            raise RelayTunnelError("Relay or local UDP port is invalid.")
        self.logger = logger or (lambda event: None)
        self.socket = None
        self.thread = None
        self._running = threading.Event()
        self._connected = threading.Event()
        self._stopped = threading.Event()
        self._lock = threading.RLock()
        self._host_sequence = 0
        self._relay_sequence = -1
        self._client_sockets = {}
        self._socket_clients = {}
        self._client_last_seen = {}
        self.failure = None

    def _log(self, event):
        try:
            self.logger(event)
        except Exception:
            pass

    def _next_sequence(self):
        with self._lock:
            self._host_sequence += 1
            return self._host_sequence

    def _send_frame(self, frame_type, client_id=0, payload=b""):
        sock = self.socket
        if sock is None:
            return False
        frame = encode_frame(
            frame_type,
            self.allocation_id,
            self._next_sequence(),
            client_id,
            payload,
            self.key,
        )
        try:
            sock.send(frame)
            return True
        except (IOError, OSError, socket.error):
            return False

    def start(self, timeout=3.0):
        """Start the worker and prove the relay accepted its authenticated HELLO."""

        with self._lock:
            if self.thread is not None:
                return self._connected.is_set()
            try:
                address = socket.gethostbyname(self.relay_host)
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.connect((address, self.relay_port))
                sock.setblocking(False)
            except (IOError, OSError, socket.error) as error:
                raise RelayTunnelError("Could not open the relay tunnel: %s" % error)
            self.socket = sock
            self._running.set()
            self.thread = threading.Thread(
                target=self._run,
                name="aos-relay-host-tunnel",
            )
            self.thread.daemon = True
            self.thread.start()
        if not self._connected.wait(max(0.1, float(timeout))):
            failure = self.failure or "Relay did not acknowledge the host tunnel."
            self.stop()
            raise RelayTunnelError(failure)
        return True

    def _client_socket(self, client_id):
        sock = self._client_sockets.get(client_id)
        if sock is not None:
            return sock
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("127.0.0.1", self.local_port))
        sock.setblocking(False)
        self._client_sockets[client_id] = sock
        self._socket_clients[sock] = client_id
        return sock

    def _drop_client(self, client_id):
        sock = self._client_sockets.pop(client_id, None)
        self._client_last_seen.pop(client_id, None)
        if sock is not None:
            self._socket_clients.pop(sock, None)
            try:
                sock.close()
            except (IOError, OSError, socket.error):
                pass

    def _handle_relay_frame(self, message):
        frame = decode_frame(message, self.key, self.allocation_id)
        if frame is None or frame["sequence"] <= self._relay_sequence:
            return
        self._relay_sequence = frame["sequence"]
        frame_type = frame["type"]
        if frame_type == ACK:
            self._connected.set()
            return
        if frame_type == CLOSE:
            self._running.clear()
            return
        if frame_type != CLIENT_TO_HOST or not frame["payload"]:
            return
        client_id = frame["client_id"]
        if client_id <= 0:
            return
        try:
            self._client_socket(client_id).send(frame["payload"])
            self._client_last_seen[client_id] = time.time()
        except (IOError, OSError, socket.error):
            self._drop_client(client_id)

    def _prune_clients(self, now):
        for client_id, last_seen in list(self._client_last_seen.items()):
            if now - last_seen > 120.0:
                self._drop_client(client_id)

    def _run(self):
        last_keepalive = 0.0
        try:
            self._send_frame(HELLO)
            while self._running.is_set():
                now = time.time()
                if now - last_keepalive >= self.keepalive_seconds:
                    self._send_frame(KEEPALIVE)
                    last_keepalive = now
                sockets = []
                if self.socket is not None:
                    sockets.append(self.socket)
                sockets.extend(self._client_sockets.values())
                if not sockets:
                    time.sleep(0.05)
                    continue
                try:
                    readable, _, _ = select.select(sockets, [], [], 0.1)
                except (IOError, OSError, select.error):
                    continue
                for readable_socket in readable:
                    try:
                        message = readable_socket.recv(MAX_PAYLOAD_BYTES + 96)
                    except (IOError, OSError, socket.error):
                        continue
                    if readable_socket is self.socket:
                        self._handle_relay_frame(message)
                        continue
                    client_id = self._socket_clients.get(readable_socket)
                    if client_id is not None and message:
                        self._client_last_seen[client_id] = now
                        self._send_frame(HOST_TO_CLIENT, client_id, message)
                self._prune_clients(now)
        except Exception as error:
            self.failure = "Relay tunnel stopped: %s" % error
            self._log(self.failure)
        finally:
            self._running.clear()
            self._close_sockets()
            self._stopped.set()

    def _close_sockets(self):
        for client_id in list(self._client_sockets):
            self._drop_client(client_id)
        sock = self.socket
        self.socket = None
        if sock is not None:
            try:
                sock.close()
            except (IOError, OSError, socket.error):
                pass

    def stop(self):
        """Close the allocation channel and reap all proxy sockets once."""

        with self._lock:
            if not self._running.is_set() and self.thread is None:
                return
            if self.socket is not None:
                self._send_frame(CLOSE)
            self._running.clear()
            thread = self.thread
            self.thread = None
        if thread is not None and thread is not threading.current_thread():
            thread.join(1.5)
        self._close_sockets()
        self._stopped.set()


class PublicLobbySession(object):
    """Bind one master allocation, scoped server token, and UDP tunnel."""

    def __init__(self, api, response, logger=None):
        if not isinstance(response, dict):
            raise RelayTunnelError("Master lobby response is invalid.")
        tunnel = response.get("tunnel")
        if not isinstance(tunnel, dict):
            raise RelayTunnelError("Master lobby response omitted tunnel data.")
        self.api = api
        self.lobby_id = str(uuid.UUID(str(response.get("lobby_id"))))
        self.server_id = str(response.get("server_id") or "")
        self.server_token = str(response.get("server_token") or "")
        if (
            not self.server_id
            or not self.server_token.startswith("aos_lobby_")
            or len(self.server_token) != 53
        ):
            raise RelayTunnelError("Master lobby response omitted its scoped credential.")
        self.master_url = str(getattr(api, "api_base", "")).rstrip("/")
        self.allocation_id = str(uuid.UUID(str(tunnel.get("allocation_id"))))
        self.relay_host = str(tunnel.get("host") or "")
        self.relay_port = int(tunnel.get("port") or 0)
        self.host_key = tunnel.get("host_key")
        self.keepalive_seconds = int(tunnel.get("keepalive_seconds") or 15)
        decode_host_key(self.host_key)
        if not self.master_url or not self.relay_host or not 1 <= self.relay_port <= 65535:
            raise RelayTunnelError("Master lobby endpoint is invalid.")
        self.tunnel = None
        self.logger = logger
        self._closed = False

    def start(self, local_port):
        tunnel = RelayHostTunnel(
            self.allocation_id,
            self.host_key,
            self.relay_host,
            self.relay_port,
            local_port,
            keepalive_seconds=self.keepalive_seconds,
            logger=self.logger,
        )
        tunnel.start()
        self.tunnel = tunnel
        return True

    def settings(self):
        return {
            "master_url": self.master_url,
            "server_id": self.server_id,
            "server_token": self.server_token,
            "public_host": self.relay_host,
            "public_port": self.relay_port,
        }

    def environment(self, base=None):
        environment = dict(base or os.environ)
        environment.update({
            "AOS_MASTER_URL": self.master_url,
            "AOS_MASTER_WRITE_TOKEN": self.server_token,
            "AOS_PUBLIC_HOST": self.relay_host,
            "AOS_PUBLIC_PORT": str(self.relay_port),
            "AOS_PUBLIC_QUERY_PORT": str(self.relay_port),
            "AOS_SERVER_ID": self.server_id,
        })
        return environment

    def stop(self):
        if self._closed:
            return
        self._closed = True
        if self.tunnel is not None:
            self.tunnel.stop()
            self.tunnel = None

        def close_listing():
            try:
                self.api.close_lobby(self.lobby_id, self.server_token)
            except Exception as error:
                if self.logger is not None:
                    try:
                        self.logger("Could not close public lobby: %s" % error)
                    except Exception:
                        pass

        cleanup = threading.Thread(
            target=close_listing,
            name="aos-relay-lobby-close",
        )
        cleanup.daemon = True
        cleanup.start()


def create_public_lobby(settings, logger=None):
    """Allocate a public relay lobby for an online launcher identity.

    Offline/unsigned users retain the existing private local-host behavior.
    Network or service errors are raised so the caller can log the downgrade
    explicitly instead of advertising an unreachable endpoint.
    """

    api = RevivalClient()
    account = api.account or {}
    if not api.access_token or account.get("offline"):
        return None
    maps = settings.get("maps") or ["MayanJungle"]
    mode = str(settings.get("mode") or "tdm").lower()
    response = api.create_lobby({
        "name": settings.get("name") or "Player Match",
        "map": maps[0],
        "game_mode": mode.upper(),
        "mode_tla": mode,
        "max_players": int(settings.get("max_players") or 12),
        "version": "1.0.0.0",
        "region": "europe",
        "playlist_id": int(settings.get("playlist_id") or 0),
        "classic": bool(settings.get("classic", False)),
        "texture_skin": settings.get("skin") or None,
    })
    return PublicLobbySession(api, response, logger=logger)
