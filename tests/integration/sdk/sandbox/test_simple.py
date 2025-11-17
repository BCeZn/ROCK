import pytest

from rock import env_vars
from rock.actions import CreateBashSessionRequest
from rock.sdk.sandbox.client import Sandbox
from rock.sdk.sandbox.config import SandboxConfig
from rock.utils.docker import DockerUtil


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.skipif(
    not (DockerUtil.is_docker_available() and DockerUtil.is_image_available(env_vars.ROCK_ENVHUB_DEFAULT_DOCKER_IMAGE)),
    reason=f"Requires Docker and image {env_vars.ROCK_ENVHUB_DEFAULT_DOCKER_IMAGE}",
)
@pytest.mark.asyncio
async def test_sandbox(admin_remote_server):
    """Test sandbox with admin server.

    This test requires the admin server to be running for proper execution.
    The admin_remote_server fixture provides the running server instance.
    """
    # Configure to use the admin server from fixture
    # Create sandbox configuration
    config = SandboxConfig(
        image="python:3.11", memory="8g", cpus=2.0, base_url=f"http://127.0.0.1:{admin_remote_server.port}"
    )

    # Create sandbox instance
    sandbox = Sandbox(config)

    try:
        # Start sandbox (connects to admin server)
        await sandbox.start()

        # Create session in sandbox for command execution
        await sandbox.create_session(CreateBashSessionRequest(session="bash-1"))

        # Execute command in sandbox session
        result = await sandbox.arun(cmd="echo Hello ROCK", session="bash-1")

        # Assertions
        assert result.output is not None
        assert "Hello ROCK" in result.output

        print("\n" + "*" * 50 + "\n" + result.output + "\n" + "*" * 50 + "\n")

    finally:
        # Stop and clean up sandbox resources
        await sandbox.stop()
