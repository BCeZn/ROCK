import asyncio
import logging
import socket
import sys
import threading
import time
from collections.abc import Generator
from dataclasses import dataclass, field
from pathlib import Path

import pytest
import uvicorn
from fastapi.testclient import TestClient

import rock
import rock.rocklet.server
from rock import env_vars
from rock.config import RockConfig
from rock.sandbox.remote_sandbox import RemoteSandboxRuntime
from rock.utils import find_free_port, run_until_complete
from rock.utils.providers import RedisProvider

TEST_API_KEY = "testkey"


@dataclass
class RemoteServer:
    port: int
    headers: dict[str, str] = field(default_factory=lambda: {"X-API-Key": TEST_API_KEY})


@pytest.fixture(scope="session", autouse=True)
def set_rock_python_env():
    """automatically set rock.ROCK_PYTHON_ENV_PATH  sys.base_prefix"""
    original_value = env_vars.ROCK_PYTHON_ENV_PATH
    env_vars.ROCK_PYTHON_ENV_PATH = sys.base_prefix

    yield

    # 恢复原值
    if original_value is not None:
        env_vars.ROCK_PYTHON_ENV_PATH = original_value
    else:
        delattr(env_vars, "ROCK_PYTHON_ENV_PATH")


@pytest.fixture(autouse=True)
def event_loop():
    # Make Sure each test has its own event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def rock_config():
    return RockConfig.from_env()


@pytest.fixture(autouse=True)
def configure_logging():
    """Automatically configure logging for all tests"""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(filename)s:%(lineno)d -- %(message)s",
        force=True,  # Force reconfiguration
    )
    log_dir = env_vars.ROCK_LOGGING_PATH
    if not Path(log_dir).is_absolute():
        # Relative to project root directory
        project_root = Path(__file__).parent.parent  # Project root directory
        log_dir = str(project_root / log_dir)
        env_vars.ROCK_LOGGING_PATH = log_dir


@pytest.fixture
async def redis_provider(rock_config: RockConfig):
    redis_provider = RedisProvider(
        host=rock_config.redis.host,
        port=rock_config.redis.port,
        password=rock_config.redis.password,
    )
    await redis_provider.init_pool()
    return redis_provider


@pytest.fixture(scope="session")
def remote_server() -> RemoteServer:
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


@pytest.fixture
def remote_runtime(remote_server: RemoteServer) -> Generator[RemoteSandboxRuntime, None]:
    r = RemoteSandboxRuntime(port=remote_server.port)
    yield r
    asyncio.run(r.close())


@pytest.fixture(scope="session")
def rocklet_test_client():
    return TestClient(rock.rocklet.server.app)
