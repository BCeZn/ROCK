from typing import Annotated, Literal

from pydantic import BaseModel, Field

from rock.actions import UploadRequest
from rock.admin.proto.request import (
    SandboxBashAction,
    SandboxCloseBashSessionRequest,
    SandboxCommand,
    SandboxCreateBashSessionRequest,
    SandboxReadFileRequest,
    SandboxWriteFileRequest,
)


class InitDockerEnvRequest(BaseModel):
    image: str = ""
    """Docker image name to use for the container."""

    python_standalone_dir: str | None = None
    """Directory path for the Python standalone installation."""

    auto_clear_time: int = 60 * 6
    """Automatic container cleanup time in minutes."""

    pull: Literal["never", "always", "missing"] = "missing"
    """Docker image pull policy: 'never', 'always', or 'missing'."""

    memory: str = "8g"
    """Memory allocation for the container (e.g., '8g', '4096m')."""

    cpus: float = 2
    """Number of CPU cores to allocate for the container."""

    container_name: str | None = None
    """Custom name for the container. If None, a random name will be generated."""


class InternalCommand(SandboxCommand):
    container_name: str | None = None


class InternalCreateBashSessionRequest(SandboxCreateBashSessionRequest):
    container_name: str | None = None


InternalCreateSessionRequest = Annotated[InternalCreateBashSessionRequest, Field(discriminator="session_type")]


class InternalBashAction(SandboxBashAction):
    container_name: str | None = None


InternalAction = InternalBashAction


class InternalCloseBashSessionRequest(SandboxCloseBashSessionRequest):
    container_name: str | None = None


InternalCloseSessionRequest = Annotated[InternalCloseBashSessionRequest, Field(discriminator="session_type")]


class InternalReadFileRequest(SandboxReadFileRequest):
    container_name: str | None = None


class InternalWriteFileRequest(SandboxWriteFileRequest):
    container_name: str | None = None


InternalUploadRequest = UploadRequest


class BashInterruptAction(BaseModel):
    command: str = "interrupt"

    session: str = "default"

    timeout: float = 0.2
    """The timeout for the command. None means no timeout."""

    n_retry: int = 3
    """How many times to retry quitting."""

    expect: list[str] = []
    """Outputs to expect in addition to the PS1"""

    action_type: Literal["bash_interrupt"] = "bash_interrupt"
