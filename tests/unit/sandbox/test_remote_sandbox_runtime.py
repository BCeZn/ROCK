import gem
from fastapi.testclient import TestClient
from gem.envs.game_env.sokoban import SokobanEnv

from tests.unit.conftest import TEST_API_KEY


def test_gem(rocklet_test_client: TestClient):
    env_id = "game:Sokoban-v0-easy"
    sandbox_id = "test_gem"
    gem_env: SokobanEnv = gem.make(env_id)
    make_response = rocklet_test_client.post(
        "/env/make", json={"env_id": env_id, "sandbox_id": sandbox_id}, headers={"X-API-Key": TEST_API_KEY}
    )
    assert make_response.status_code == 200
    sandbox_id = make_response.json()["sandbox_id"]

    reset_response = rocklet_test_client.post(
        "/env/reset", json={"sandbox_id": sandbox_id, "seed": 42}, headers={"X-API-Key": TEST_API_KEY}
    )
    assert reset_response.status_code == 200
    observation, info = reset_response.json()

    for _ in range(10):
        action = gem_env.sample_random_action()
        step_response = rocklet_test_client.post(
            "/env/step",
            json={"sandbox_id": sandbox_id, "action": action},
            headers={"X-API-Key": TEST_API_KEY},
        )
        assert step_response.status_code == 200
        next_observation, reward, terminated, truncated, info = step_response.json()
        if terminated or truncated:
            break

    close_response = rocklet_test_client.post(
        "/env/close", json={"sandbox_id": sandbox_id}, headers={"X-API-Key": TEST_API_KEY}
    )
    assert close_response.status_code == 200
