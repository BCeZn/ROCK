import os
import tempfile

import pytest
from fastapi.testclient import TestClient

from rock.envhub.server import app, initialize_env_hub


@pytest.fixture(scope="function")
def envhub_client():
    """Create test client with temporary database"""
    # Create temporary database file
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
        db_path = tmp_file.name

    db_url = f"sqlite:///{db_path}"

    # Initialize EnvHub
    initialize_env_hub(db_url=db_url)

    # Create test client
    with TestClient(app) as test_client:
        yield test_client

    # Clean up temporary database file
    if os.path.exists(db_path):
        os.unlink(db_path)


def test_health_check(envhub_client):
    """Test health check endpoint"""
    response = envhub_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_register_env(envhub_client):
    """Test environment registration"""
    payload = {
        "env_name": "test-env",
        "image": "python:3.9",
        "owner": "test-user",
        "description": "Test environment",
        "tags": ["test", "dev"],
        "extra_spec": {"gpu": True},
    }

    response = envhub_client.post("/env/register", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["env_name"] == "test-env"
    assert data["image"] == "python:3.9"
    assert data["owner"] == "test-user"
    assert data["description"] == "Test environment"
    assert "test" in data["tags"]
    assert data["extra_spec"] == {"gpu": True}


def test_register_env_minimal_fields(envhub_client):
    """Test environment registration with minimal fields"""
    payload = {"env_name": "minimal-env", "image": "alpine:latest"}

    response = envhub_client.post("/env/register", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["env_name"] == "minimal-env"
    assert data["image"] == "alpine:latest"
    assert data["owner"] == ""
    assert data["description"] == ""
    assert data["tags"] == []
    assert data["extra_spec"] is None


def test_get_env(envhub_client):
    """Test getting environment"""
    # First register an environment
    register_payload = {"env_name": "get-test-env", "image": "python:3.9", "owner": "test-user"}
    envhub_client.post("/env/register", json=register_payload)

    # Get environment
    get_payload = {"env_name": "get-test-env"}
    response = envhub_client.post("/env/get", json=get_payload)
    assert response.status_code == 200

    data = response.json()
    assert data["env_name"] == "get-test-env"
    assert data["image"] == "python:3.9"
    assert data["owner"] == "test-user"


def test_get_nonexistent_env(envhub_client):
    """Test getting non-existent environment"""
    payload = {"env_name": "nonexistent-env"}
    response = envhub_client.post("/env/get", json=payload)
    assert response.status_code == 404


def test_list_envs_empty(envhub_client):
    """Test listing environments (empty list)"""
    payload = {}
    response = envhub_client.post("/env/list", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "envs" in data
    assert isinstance(data["envs"], list)
    assert len(data["envs"]) == 1  # because of the default env


def test_list_envs_multiple(envhub_client):
    """Test listing multiple environments"""
    # Register multiple environments
    envs = [
        {"env_name": "env1", "image": "img1", "owner": "user1"},
        {"env_name": "env2", "image": "img2", "owner": "user2"},
        {"env_name": "env3", "image": "img3", "owner": "user1"},
    ]

    for env in envs:
        envhub_client.post("/env/register", json=env)

    # List all environments
    payload = {}
    response = envhub_client.post("/env/list", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert len(data["envs"]) == 4


def test_list_envs_filter_by_owner(envhub_client):
    """Test filtering environments by owner"""
    # Register multiple environments
    envs = [
        {"env_name": "alice-env-1", "image": "img1", "owner": "alice"},
        {"env_name": "bob-env", "image": "img2", "owner": "bob"},
        {"env_name": "alice-env-2", "image": "img3", "owner": "alice"},
    ]

    for env in envs:
        envhub_client.post("/env/register", json=env)

    # Filter by owner
    payload = {"owner": "alice"}
    response = envhub_client.post("/env/list", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert len(data["envs"]) == 2
    assert all(env["owner"] == "alice" for env in data["envs"])


def test_list_envs_filter_by_tags(envhub_client):
    """Test filtering environments by tags"""
    # Register multiple environments
    envs = [
        {"env_name": "ml-env", "image": "img1", "tags": ["ml", "gpu"]},
        {"env_name": "web-env", "image": "img2", "tags": ["web", "nodejs"]},
        {"env_name": "data-env", "image": "img3", "tags": ["ml", "data"]},
    ]

    for env in envs:
        envhub_client.post("/env/register", json=env)

    # Filter by tags
    payload = {"tags": ["ml"]}
    response = envhub_client.post("/env/list", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert len(data["envs"]) == 2

    env_names = {env["env_name"] for env in data["envs"]}
    assert env_names == {"ml-env", "data-env"}


def test_list_envs_combined_filters(envhub_client):
    """Test combined filtering conditions"""
    # Register multiple environments
    envs = [
        {"env_name": "alice-ml", "image": "img1", "owner": "alice", "tags": ["ml"]},
        {"env_name": "alice-web", "image": "img2", "owner": "alice", "tags": ["web"]},
        {"env_name": "bob-ml", "image": "img3", "owner": "bob", "tags": ["ml"]},
    ]

    for env in envs:
        envhub_client.post("/env/register", json=env)

    # Combined filter: alice's ml environment
    payload = {"owner": "alice", "tags": ["ml"]}
    response = envhub_client.post("/env/list", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert len(data["envs"]) == 1
    assert data["envs"][0]["env_name"] == "alice-ml"


def test_update_env(envhub_client):
    """Test updating environment"""
    # Register environment
    initial_payload = {"env_name": "update-test", "image": "python:3.9", "owner": "alice"}
    envhub_client.post("/env/register", json=initial_payload)

    # Update environment
    update_payload = {"env_name": "update-test", "image": "python:3.10", "owner": "bob", "description": "Updated"}
    response = envhub_client.post("/env/register", json=update_payload)
    assert response.status_code == 200

    data = response.json()
    assert data["image"] == "python:3.10"
    assert data["owner"] == "bob"
    assert data["description"] == "Updated"


def test_delete_env(envhub_client):
    """Test deleting environment"""
    # Register environment
    register_payload = {"env_name": "delete-test", "image": "python:3.9"}
    envhub_client.post("/env/register", json=register_payload)

    # Delete environment
    delete_payload = {"env_name": "delete-test"}
    response = envhub_client.post("/env/delete", json=delete_payload)
    assert response.status_code == 200
    assert response.json() is True

    # Verify environment is deleted
    get_payload = {"env_name": "delete-test"}
    response = envhub_client.post("/env/get", json=get_payload)
    assert response.status_code == 404


def test_delete_nonexistent_env(envhub_client):
    """Test deleting non-existent environment"""
    payload = {"env_name": "nonexistent-env"}
    response = envhub_client.post("/env/delete", json=payload)
    assert response.status_code == 404
