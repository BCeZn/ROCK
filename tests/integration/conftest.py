import socket
import subprocess
import threading
import time
from dataclasses import dataclass, field

import pytest
import uvicorn
from fastapi.testclient import TestClient

import rock
import rock.rocklet.server
from rock.utils import find_free_port, run_until_complete
from rock.utils.concurrent_helper import run_until_complete
from rock.utils.system import find_free_port

TEST_API_KEY = "testkey"


@dataclass
class RemoteServer:
    port: int
    headers: dict[str, str] = field(default_factory=lambda: {"X-API-Key": TEST_API_KEY})


@pytest.fixture
def test_api_key():
    return TEST_API_KEY


@pytest.fixture(scope="session")
def rocklet_remote_server() -> RemoteServer:
    port = run_until_complete(find_free_port())
    print(f"Using port {port} for the remote server")

    def run_server():
        uvicorn.run(rock.rocklet.server.app, host="127.0.0.1", port=port, log_level="error")

    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()

    # Wait for the server to start
    max_retries = 10
    retry_delay = 0.1
    for _ in range(max_retries):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                break
        except (TimeoutError, ConnectionRefusedError):
            time.sleep(retry_delay)
    else:
        pytest.fail("Server did not start within the expected time")

    return RemoteServer(port)


@pytest.fixture(scope="session")
def rocklet_test_client():
    client = TestClient(rock.rocklet.server.app)
    yield client


@pytest.fixture(scope="session")
def admin_remote_server():
    port = run_until_complete(find_free_port())

    process = subprocess.Popen(
        [
            "admin",
            "--env",
            "local",
            "--role",
            "admin",
            "--port",
            str(port),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for the server to start
    max_retries = 10
    retry_delay = 3
    for _ in range(max_retries):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                break
        except (TimeoutError, ConnectionRefusedError):
            time.sleep(retry_delay)
    else:
        process.kill()
        pytest.fail("Server did not start within the expected time")

    yield RemoteServer(port)

    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
