from __future__ import annotations

import base64
import socket
import threading
import time

import local_host
import relay_host


ALLOCATION_ID = "00112233-4455-4677-8899-aabbccddeeff"
KEY = bytes(range(32))
HOST_KEY = base64.urlsafe_b64encode(KEY).rstrip(b"=").decode("ascii")
GOLDEN_FRAME_HEX = (
    "414f5352010400112233445546778899aabbccddeeff0000000000000009"
    "0000002a0004656e6574a53701111744f4a1012c1f7e3967bd8b4c9817"
    "267423716cdd4e233c922eb0ad"
)


def test_relay_protocol_matches_cross_runtime_golden_vector() -> None:
    frame = relay_host.encode_frame(
        relay_host.CLIENT_TO_HOST,
        ALLOCATION_ID,
        9,
        42,
        b"enet",
        KEY,
    )
    assert frame.hex() == GOLDEN_FRAME_HEX
    decoded = relay_host.decode_frame(frame, KEY, ALLOCATION_ID)
    assert decoded == {
        "type": relay_host.CLIENT_TO_HOST,
        "allocation_id": ALLOCATION_ID,
        "sequence": 9,
        "client_id": 42,
        "payload": b"enet",
    }
    tampered = bytearray(frame)
    tampered[40] ^= 1
    assert relay_host.decode_frame(bytes(tampered), KEY, ALLOCATION_ID) is None


def test_host_tunnel_preserves_distinct_slot_and_raw_udp_payload() -> None:
    local_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    local_server.bind(("127.0.0.1", 0))
    local_port = local_server.getsockname()[1]
    relay = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    relay.bind(("127.0.0.1", 0))
    relay_port = relay.getsockname()[1]
    relay.settimeout(2.0)
    local_server.settimeout(2.0)
    stopped = threading.Event()

    def echo_server() -> None:
        try:
            payload, remote = local_server.recvfrom(65535)
            local_server.sendto(payload.upper(), remote)
        finally:
            stopped.set()

    echo = threading.Thread(target=echo_server)
    echo.daemon = True
    echo.start()

    tunnel = relay_host.RelayHostTunnel(
        ALLOCATION_ID,
        HOST_KEY,
        "127.0.0.1",
        relay_port,
        local_port,
        keepalive_seconds=60,
    )
    starter_result: list[object] = []

    def start_tunnel() -> None:
        try:
            starter_result.append(tunnel.start(timeout=2.0))
        except Exception as error:  # pragma: no cover - failure diagnostics
            starter_result.append(error)

    starter = threading.Thread(target=start_tunnel)
    starter.start()
    hello_bytes, host_address = relay.recvfrom(65535)
    hello = relay_host.decode_frame(hello_bytes, KEY, ALLOCATION_ID)
    assert hello is not None and hello["type"] == relay_host.HELLO
    relay.sendto(
        relay_host.encode_frame(
            relay_host.ACK,
            ALLOCATION_ID,
            1,
            0,
            b"",
            KEY,
        ),
        host_address,
    )
    starter.join(2.0)
    assert starter_result == [True]

    relay.sendto(
        relay_host.encode_frame(
            relay_host.CLIENT_TO_HOST,
            ALLOCATION_ID,
            2,
            17,
            b"enet-payload",
            KEY,
        ),
        host_address,
    )

    reply = None
    deadline = time.time() + 2.0
    while time.time() < deadline:
        packet, _ = relay.recvfrom(65535)
        candidate = relay_host.decode_frame(packet, KEY, ALLOCATION_ID)
        if candidate and candidate["type"] == relay_host.HOST_TO_CLIENT:
            reply = candidate
            break
    tunnel.stop()
    echo.join(2.0)
    relay.close()
    local_server.close()
    assert stopped.is_set()
    assert reply is not None
    assert reply["client_id"] == 17
    assert reply["payload"] == b"ENET-PAYLOAD"


def test_public_lobby_config_enables_scoped_master_without_serializing_secret() -> None:
    settings = {
        "name": "Relay Match",
        "admin_password": "local-admin-secret",
        "port": 27015,
        "max_players": 12,
        "match_length": 10,
        "mode": "tdm",
        "maps": ["London"],
        "bot_count": 0,
        "bot_difficulty": "mixed",
        "rules": {},
        "public_lobby": {
            "master_url": "https://www.aosplay.net",
            "server_id": "relay.example:40001",
            "server_token": "aos_lobby_" + "x" * 43,
            "public_host": "relay.example",
            "public_port": 40001,
        },
    }
    payload = local_host.build_session_toml(settings)
    assert "[revival]" in payload
    assert "enabled = true" in payload
    assert 'public_host = "relay.example"' in payload
    assert 'server_id = "relay.example:40001"' in payload
    assert "aos_lobby_" not in payload
    assert "[admin]" in payload
    assert 'password = "local-admin-secret"' in payload


def test_public_lobby_environment_keeps_secret_out_of_server_config() -> None:
    class Api:
        api_base = "https://www.aosplay.net"

        def close_lobby(self, lobby_id: str, token: str) -> dict[str, bool]:
            return {"closed": True}

    response = {
        "lobby_id": "11111111-2222-4333-8444-555555555555",
        "server_id": "relay.example:40002",
        "server_token": "aos_lobby_" + "a" * 43,
        "tunnel": {
            "allocation_id": ALLOCATION_ID,
            "host": "relay.example",
            "port": 40002,
            "host_key": HOST_KEY,
            "keepalive_seconds": 15,
        },
    }
    session = relay_host.PublicLobbySession(Api(), response)
    environment = session.environment({"PATH": "test"})
    assert environment["AOS_MASTER_WRITE_TOKEN"] == response["server_token"]
    assert environment["AOS_SERVER_ID"] == response["server_id"]
    assert environment["AOS_PUBLIC_PORT"] == "40002"
    assert environment["PATH"] == "test"
