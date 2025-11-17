import pytest

from rock.sdk.envhub.client import EnvHubClient, EnvHubError
from rock.sdk.envhub.schema import EnvHubClientConfig


@pytest.mark.asyncio
async def test_register_env(envhub_server):
    """Test environment registration."""
    client = EnvHubClient(EnvHubClientConfig(base_url=envhub_server))

    # Use unique prefix for environment name
    prefix = "register_test_"

    # Test full field registration
    env_info = await client.register(
        env_name=f"{prefix}env",
        image="python:3.9",
        owner="test-user",
        description="Test environment",
        tags=["test", "dev"],
        extra_spec={"gpu": True},
    )

    assert env_info.env_name == f"{prefix}env"
    assert env_info.image == "python:3.9"
    assert env_info.owner == "test-user"
    assert env_info.description == "Test environment"
    assert "test" in env_info.tags
    assert env_info.extra_spec == {"gpu": True}


@pytest.mark.asyncio
async def test_get_env(envhub_server):
    """Test getting environment."""
    client = EnvHubClient(EnvHubClientConfig(base_url=envhub_server))

    # Use unique prefix for environment name
    prefix = "get_test_"

    # Register an environment first
    await client.register(env_name=f"{prefix}env", image="python:3.9", owner="test-user")

    # Get environment
    env_info = await client.get_env(f"{prefix}env")

    assert env_info.env_name == f"{prefix}env"
    assert env_info.image == "python:3.9"
    assert env_info.owner == "test-user"


@pytest.mark.asyncio
async def test_get_nonexistent_env(envhub_server):
    """Test getting non-existent environment."""
    client = EnvHubClient(EnvHubClientConfig(base_url=envhub_server))

    # Try to get a non-existent environment, should raise an exception
    with pytest.raises(EnvHubError):
        await client.get_env("nonexistent-env")


@pytest.mark.asyncio
async def test_list_envs(envhub_server):
    """Test listing environments."""
    client = EnvHubClient(EnvHubClientConfig(base_url=envhub_server))

    # Use unique prefix for environment name
    prefix = "list_test_"
    await client.register(f"{prefix}env1", "img1", "user1")
    await client.register(f"{prefix}env2", "img2", "user2")
    await client.register(f"{prefix}env3", "img3", "user1")

    # List all environments with prefix
    all_envs = await client.list_envs()

    # Filter out environments we created
    envs = [env for env in all_envs if env.env_name.startswith(prefix)]

    assert len(envs) == 3
    env_names = {env.env_name for env in envs}
    assert env_names == {f"{prefix}env1", f"{prefix}env2", f"{prefix}env3"}


@pytest.mark.asyncio
async def test_list_envs_filter_by_owner(envhub_server):
    """Test filtering environments by owner."""
    client = EnvHubClient(EnvHubClientConfig(base_url=envhub_server))

    # Use unique prefix for environment name
    prefix = "owner_test_"

    # Register multiple environments
    await client.register(f"{prefix}alice-env-1", "img1", "alice")
    await client.register(f"{prefix}bob-env", "img2", "bob")
    await client.register(f"{prefix}alice-env-2", "img3", "alice")

    # Filter by owner
    all_envs = await client.list_envs()

    # Filter out environments we created
    envs = [env for env in all_envs if env.env_name.startswith(prefix)]
    alice_envs = [env for env in envs if env.owner == "alice"]

    assert len(alice_envs) == 2
    assert all(env.owner == "alice" for env in alice_envs)


@pytest.mark.asyncio
async def test_list_envs_filter_by_tags(envhub_server):
    """Test filtering environments by tags."""
    client = EnvHubClient(EnvHubClientConfig(base_url=envhub_server))

    # Use unique prefix for environment name
    prefix = "tags_test_"

    # Register multiple environments
    await client.register(f"{prefix}ml-env", "img1", tags=["ml", "gpu"])
    await client.register(f"{prefix}web-env", "img2", tags=["web", "nodejs"])
    await client.register(f"{prefix}data-env", "img3", tags=["ml", "data"])

    # Filter by tags
    all_envs = await client.list_envs()

    # Filter out environments we created
    envs = [env for env in all_envs if env.env_name.startswith(prefix)]
    ml_envs = [env for env in envs if "ml" in env.tags]

    assert len(ml_envs) == 2
    env_names = {env.env_name for env in ml_envs}
    assert env_names == {f"{prefix}ml-env", f"{prefix}data-env"}


@pytest.mark.asyncio
async def test_update_env(envhub_server):
    """Test updating environment."""
    client = EnvHubClient(EnvHubClientConfig(base_url=envhub_server))

    # Use unique prefix for environment name
    prefix = "update_test_"

    # Register environment
    await client.register(f"{prefix}env", "python:3.9", "alice")

    # Update environment
    updated_env = await client.register(
        env_name=f"{prefix}env", image="python:3.10", owner="bob", description="Updated environment"
    )

    assert updated_env.image == "python:3.10"
    assert updated_env.owner == "bob"
    assert updated_env.description == "Updated environment"


@pytest.mark.asyncio
async def test_delete_env(envhub_server):
    """Test deleting environment."""
    client = EnvHubClient(EnvHubClientConfig(base_url=envhub_server))

    # Use unique prefix for environment name
    prefix = "delete_test_"

    # Register environment
    await client.register(f"{prefix}env", "python:3.9")

    # Delete environment
    result = await client.delete_env(f"{prefix}env")

    assert result is True

    # Verify environment is deleted
    with pytest.raises(EnvHubError):
        await client.get_env(f"{prefix}env")


@pytest.mark.asyncio
async def test_delete_nonexistent_env(envhub_server):
    """Test deleting non-existent environment."""
    client = EnvHubClient(EnvHubClientConfig(base_url=envhub_server))

    # Delete non-existent environment, should return False
    result = await client.delete_env("nonexistent-env")

    assert result is False


@pytest.mark.asyncio
async def test_health_check(envhub_server):
    """Test health check."""
    client = EnvHubClient(EnvHubClientConfig(base_url=envhub_server))

    # Health check
    status = await client.health_check()

    assert status == {"status": "ok"}
