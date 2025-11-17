import time

import pytest

from rock.utils import timeout


@pytest.mark.asyncio
async def test_timeout():
    start_time = time.time()
    try:
        with timeout(1):
            time.sleep(3)
    except TimeoutError:
        assert time.time() - start_time < 3
