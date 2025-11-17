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
