import pytest
import ray

from rock.deployments.config import LocalDeploymentConfig
from rock.sandbox.sandbox_actor import SandboxActor


@pytest.mark.asyncio
async def test_execute_with_additional_pkgs():
    sandbox_config = LocalDeploymentConfig()
    actor_name = "sandbox-test"
    sandbox_actor = SandboxActor.options(name=actor_name).remote(sandbox_config, "test", "dev")
    actor_obj = ray.get_actor(actor_name)
    assert actor_obj
    ray.kill(sandbox_actor)
