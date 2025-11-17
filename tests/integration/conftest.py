import socket
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field

import pytest
import uvicorn
from fastapi.testclient import TestClient

from rock import env_vars
from rock.utils import find_free_port, run_until_complete
from rock.utils.concurrent_helper import run_until_complete
from rock.utils.docker import DockerUtil
from rock.utils.system import find_free_port

TEST_API_KEY = "testkey"


SKIP_IF_NO_DOCKER = pytest.mark.skipif(
    not (DockerUtil.is_docker_available() and DockerUtil.is_image_available(env_vars.ROCK_ENVHUB_DEFAULT_DOCKER_IMAGE)),
    reason=f"Requires Docker and image {env_vars.ROCK_ENVHUB_DEFAULT_DOCKER_IMAGE}",
)


@dataclass
class RemoteServer:
    port: int
    headers: dict[str, str] = field(default_factory=lambda: {"X-API-Key": TEST_API_KEY})


@pytest.fixture
def test_api_key():
    return TEST_API_KEY


## Rocklet Client & Remote Server


@pytest.fixture(scope="session")
def rocklet_test_client():
    from rock.rocklet.server import app

    client = TestClient(app)
    yield client


@pytest.fixture(scope="session")
def rocklet_remote_server() -> RemoteServer:
    port = run_until_complete(find_free_port())
    from rock.rocklet.server import app

    def run_server():
        uvicorn.run(app, host="127.0.0.1", port=port, log_level="error")

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


## Admin Client & Remote Server


@pytest.fixture(name="admin_client", scope="session")
def admin_client_fixture():
    """Create test client using TestClient"""
    # Save original sys.argv
    original_argv = sys.argv.copy()
    # Modify sys.argv
    sys.argv = ["main.py", "--env", "local", "--role", "admin"]
    try:
        from rock.admin.main import app, gem_router

        # Register env router
        app.include_router(gem_router, prefix="/apis/v1/envs/gem", tags=["gem"])
        with TestClient(app) as client:
            yield client
    finally:
        # Restore original sys.argv
        sys.argv = original_argv


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
