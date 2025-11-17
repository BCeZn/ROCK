import pytest

from rock.config import RockConfig


@pytest.mark.asyncio
async def test_rock_config():
    rock_config: RockConfig = RockConfig.from_env()
    assert rock_config
