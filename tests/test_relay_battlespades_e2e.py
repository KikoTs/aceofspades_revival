from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

import pytest

import relay_host


_A2S_INFO_REQUEST = b"\xff\xff\xff\xffTSource Engine Query\x00"


def _unused_port(socket_type: int) -> int:
    with socket.socket(socket.AF_INET, socket_type) as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def _request_json(
    url: str,
    *,
    method: str = "GET",
    token: str = "",
    payload: dict[str, Any] | None = None,
    timeout: float = 1.0,
) -> tuple[int, dict[str, Any]]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"accept": "application/json"}
    if body is not None:
        headers["content-type"] = "application/json"
    if token:
        headers["authorization"] = "Bearer " + token
    request = Request(url, data=body, headers=headers, method=method)
    with urlopen(request, timeout=timeout) as response:
        return response.status, json.load(response)


def _wait_for_relay(control_url: str, process: subprocess.Popen[str]) -> None:
    deadline = time.monotonic() + 8.0
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        if process.poll() is not None:
            output = process.stdout.read() if process.stdout is not None else ""
            raise AssertionError(
                "relay worker exited before becoming ready: " + output[-4000:]
            )
        try:
            status, payload = _request_json(control_url + "/health")
            if status == 200 and payload.get("ready") is True:
                return
        except (OSError, URLError, ValueError) as error:
            last_error = error
        time.sleep(0.05)
    raise AssertionError("relay worker did not become ready: %s" % last_error)


def _query_a2s(host: str, port: int, timeout: float = 1.0) -> bytes:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as query:
        query.settimeout(timeout)
        query.sendto(_A2S_INFO_REQUEST, (host, port))
        response, _ = query.recvfrom(4096)
        if response[:5] == b"\xff\xff\xff\xffA":
            assert len(response) >= 9, "A2S challenge was truncated"
            query.sendto(_A2S_INFO_REQUEST + response[5:9], (host, port))
            response, _ = query.recvfrom(4096)
        return response


def _wait_for_battlespades(port: int, process: subprocess.Popen[bytes]) -> bytes:
    deadline = time.monotonic() + 30.0
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        if process.poll() is not None:
            output = process.stdout.read() if process.stdout is not None else b""
            raise AssertionError(
                "BattleSpades exited before A2S became ready: "
                + output[-4000:].decode("utf-8", "replace")
            )
        try:
            response = _query_a2s("127.0.0.1", port, timeout=0.25)
            if response[:5] == b"\xff\xff\xff\xffI":
                return response
        except (OSError, socket.timeout) as error:
            last_error = error
        time.sleep(0.05)
    raise AssertionError("BattleSpades A2S endpoint did not become ready: %s" % last_error)


def _stop_process(process: subprocess.Popen[Any]) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5.0)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5.0)


def _connect_enet_clients(
    host: str, port: int, module_root: Path, client_count: int = 2
) -> None:
    """Keep multiple real ENet clients connected at the same time."""

    assert module_root.is_dir(), "BattleSpades ENet module root is missing"
    script = r"""
import enet
import sys
import time

host = enet.Host(None, peerCount=1, channelLimit=1,
                 incomingBandwidth=0, outgoingBandwidth=0)
host.compress_with_range_coder()
peer = host.connect(enet.Address(sys.argv[1].encode("ascii"), int(sys.argv[2])),
                    1, 168)
deadline = time.time() + 8.0
while time.time() < deadline:
    event = host.service(100)
    if event is None or event.type == enet.EVENT_TYPE_NONE:
        continue
    if event.type == enet.EVENT_TYPE_CONNECT:
        print("enet_connected")
        sys.stdout.flush()
        hold_until = time.time() + 2.0
        while time.time() < hold_until:
            host.service(50)
        peer.disconnect()
        raise SystemExit(0)
    if event.type == enet.EVENT_TYPE_DISCONNECT:
        raise SystemExit("ENet disconnected before connecting")
raise SystemExit("ENet connection timed out")
"""
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(module_root)
    processes = [
        subprocess.Popen(
            [sys.executable, "-c", script, host, str(port)],
            cwd=str(module_root),
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        for _ in range(client_count)
    ]
    outputs = []
    try:
        for process in processes:
            output, _ = process.communicate(timeout=12.0)
            outputs.append(output)
            assert process.returncode == 0, output[-4000:]
            assert "enet_connected" in output
    finally:
        for process in processes:
            _stop_process(process)


@pytest.mark.skipif(
    not os.environ.get("AOS_RELAY_E2E_SERVER_EXE")
    or not os.environ.get("AOS_RELAY_E2E_WORKER_ROOT")
    or not os.environ.get("AOS_RELAY_E2E_ENET_ROOT"),
    reason=(
        "set AOS_RELAY_E2E_SERVER_EXE, AOS_RELAY_E2E_WORKER_ROOT, and "
        "AOS_RELAY_E2E_ENET_ROOT to run the packaged BattleSpades relay proof"
    ),
)
def test_packaged_battlespades_a2s_traverses_real_relay() -> None:
    """Prove native UDP survives Node relay and Python host-tunnel framing."""

    server_exe = Path(os.environ["AOS_RELAY_E2E_SERVER_EXE"]).resolve()
    worker_root = Path(os.environ["AOS_RELAY_E2E_WORKER_ROOT"]).resolve()
    enet_root = Path(os.environ["AOS_RELAY_E2E_ENET_ROOT"]).resolve()
    node = shutil.which("node")
    assert node is not None, "Node.js is required for the relay worker"
    assert server_exe.is_file(), "packaged BattleSpades executable is missing"
    server_config = server_exe.with_name("config.toml")
    worker_cli = worker_root / "relay" / "cli.mjs"
    assert server_config.is_file(), "packaged BattleSpades config is missing"
    assert worker_cli.is_file(), "relay worker CLI is missing"

    control_port = _unused_port(socket.SOCK_STREAM)
    relay_port = _unused_port(socket.SOCK_DGRAM)
    game_port = _unused_port(socket.SOCK_DGRAM)
    control_token = "relay-e2e-control-" + "x" * 32
    control_url = "http://127.0.0.1:%d" % control_port
    relay_environment = os.environ.copy()
    relay_environment.update(
        {
            "AOS_RELAY_CONTROL_HOST": "127.0.0.1",
            "AOS_RELAY_CONTROL_PORT": str(control_port),
            "AOS_RELAY_CONTROL_TOKEN": control_token,
            "AOS_RELAY_PUBLIC_HOST": "127.0.0.1",
            "AOS_RELAY_UDP_BIND_HOST": "127.0.0.1",
            "AOS_RELAY_PORT_MIN": str(relay_port),
            "AOS_RELAY_PORT_MAX": str(relay_port),
        }
    )
    no_window = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    relay_process = subprocess.Popen(
        [node, str(worker_cli)],
        cwd=str(worker_root),
        env=relay_environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        creationflags=no_window,
    )
    server_process: subprocess.Popen[bytes] | None = None
    tunnel: relay_host.RelayHostTunnel | None = None
    allocation_id = ""
    run_dir = ""

    try:
        _wait_for_relay(control_url, relay_process)
        status, allocation = _request_json(
            control_url + "/v1/allocations",
            method="POST",
            token=control_token,
            payload={"max_clients": 4},
        )
        assert status == 201
        allocation_id = str(allocation["allocation_id"])

        server_environment = os.environ.copy()
        server_environment.update(
            {
                "AOS_MASTER_URL": "http://127.0.0.1:9",
                "AOS_MASTER_WRITE_TOKEN": "relay-e2e-lobby-" + "y" * 32,
                "AOS_PUBLIC_HOST": "127.0.0.1",
                "AOS_PUBLIC_PORT": str(allocation["public_port"]),
                "AOS_PUBLIC_QUERY_PORT": str(allocation["public_port"]),
                "AOS_SERVER_ID": "127.0.0.1:%s" % allocation["public_port"],
            }
        )
        run_dir = tempfile.mkdtemp(prefix="aos-relay-e2e-")
        server_process = subprocess.Popen(
            [
                str(server_exe),
                "--config",
                str(server_config),
                "--port",
                str(game_port),
            ],
            cwd=run_dir,
            env=server_environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            creationflags=no_window,
        )
        direct = _wait_for_battlespades(game_port, server_process)
        assert b"BattleSpades" in direct

        tunnel = relay_host.RelayHostTunnel(
            allocation_id,
            allocation["host_key"],
            allocation["public_host"],
            int(allocation["public_port"]),
            game_port,
            keepalive_seconds=5,
        )
        assert tunnel.start(timeout=3.0) is True
        relayed = _query_a2s(
            str(allocation["public_host"]),
            int(allocation["public_port"]),
            timeout=3.0,
        )
        assert relayed[:5] == b"\xff\xff\xff\xffI"
        assert b"BattleSpades" in relayed
        assert relayed == direct
        _connect_enet_clients(
            str(allocation["public_host"]),
            int(allocation["public_port"]),
            enet_root,
        )
    finally:
        if tunnel is not None:
            tunnel.stop()
        if allocation_id:
            try:
                _request_json(
                    control_url + "/v1/allocations/" + allocation_id,
                    method="DELETE",
                    token=control_token,
                )
            except (OSError, URLError, ValueError):
                pass
        if server_process is not None:
            _stop_process(server_process)
        _stop_process(relay_process)
        if run_dir:
            shutil.rmtree(run_dir, ignore_errors=True)
