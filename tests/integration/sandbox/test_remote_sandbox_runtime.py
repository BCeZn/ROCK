import logging

import gem
from fastapi.testclient import TestClient
from gem.envs.game_env.sokoban import SokobanEnv

logger = logging.getLogger(__name__)


def test_gem(rocklet_test_client: TestClient):
    env_id = "game:Sokoban-v0-easy"
    sandbox_id = "test_gem"
    gem_env: SokobanEnv = gem.make(env_id)
    make_response = rocklet_test_client.post("/env/make", json={"env_id": env_id, "sandbox_id": sandbox_id})
    assert make_response.status_code == 200
    sandbox_id = make_response.json()["sandbox_id"]

    reset_response = rocklet_test_client.post("/env/reset", json={"sandbox_id": sandbox_id, "seed": 42})
    assert reset_response.status_code == 200
    reset_data = reset_response.json()
    observation = reset_data["observation"]
    info = reset_data["info"]
    logger.info(f"Reset: observation is {observation}, info is {info}")

    for _ in range(10):
        action = gem_env.sample_random_action()
        step_response = rocklet_test_client.post(
            "/env/step",
            json={"sandbox_id": sandbox_id, "action": action},
        )
        assert step_response.status_code == 200
        step_data = step_response.json()
        next_observation = step_data["observation"]
        reward = step_data["reward"]
        terminated = step_data["terminated"]
        truncated = step_data["truncated"]
        info = step_data["info"]
        logger.info(
            f"Step: next_observation is {next_observation}, reward is {reward}, terminated is {terminated}, truncated is {truncated}, info is {info}"
        )
        if terminated or truncated:
            break

    close_response = rocklet_test_client.post(
        "/env/close",
        json={"sandbox_id": sandbox_id},
    )
    assert close_response.status_code == 200
