from rock import env_vars


def test_default_envs():
    log_dir = "/data/log"
    env_vars.ROCK_LOGGING_PATH = log_dir
    assert log_dir == env_vars.ROCK_LOGGING_PATH


def test_envs_project_root():
    project_root = env_vars.ROCK_PROJECT_ROOT
    assert project_root is not None
