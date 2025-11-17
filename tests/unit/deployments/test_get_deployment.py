from rock.deployments import get_deployment
from rock.deployments.config import (
    DockerDeploymentConfig,
    LocalDeploymentConfig,
    RemoteDeploymentConfig,
)
from rock.deployments.docker import DockerDeployment
from rock.deployments.local import LocalDeployment
from rock.deployments.manager import DeploymentManager
from rock.deployments.ray import RayDeployment
from rock.deployments.remote import RemoteDeployment


def test_get_local_deployment():
    deployment = get_deployment(LocalDeploymentConfig())
    assert isinstance(deployment, LocalDeployment)


def test_get_docker_deployment():
    deployment = get_deployment(DockerDeploymentConfig(image="test"))
    assert isinstance(deployment, DockerDeployment)


def test_get_remote_deployment():
    deployment = get_deployment(RemoteDeploymentConfig())
    assert isinstance(deployment, RemoteDeployment)


async def test_deployment_manager(rock_config):
    manager = DeploymentManager(rock_config)
    config = DockerDeploymentConfig()
    docker_deployment_config = await manager.init_config(config)
    deployment = manager.get_deployment(docker_deployment_config)
    assert isinstance(deployment, RayDeployment)
