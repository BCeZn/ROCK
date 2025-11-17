import pytest

from rock.utils import ListUtil


@pytest.mark.asyncio
async def test_get_unique():
    input_list = ["a", "b", "a"]
    output_list = await ListUtil.get_unique_list(input_list)
    assert output_list == ["a", "b"]
