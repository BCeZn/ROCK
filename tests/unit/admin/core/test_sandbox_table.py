import pytest

from rock.admin.core.db_provider import DatabaseProvider
from rock.admin.core.sandbox_table import SandboxTable
from rock.admin.core.schema import DBModelBase as Base
from rock.admin.core.schema import SandboxRecord
from rock.config import DatabaseConfig


class DatabaseProviderUtil:
    @staticmethod
    async def reset(provider: DatabaseProvider):
        async with provider.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)


@pytest.mark.asyncio
async def _create_sandbox_table():
    db_provider = DatabaseProvider(DatabaseConfig(url="sqlite+aiosqlite:///:memory:"))
    await db_provider.init()
    await DatabaseProviderUtil.reset(db_provider)
    return SandboxTable(db_provider.engine)


@pytest.mark.asyncio
async def test_sandbox_table():
    table = await _create_sandbox_table()
    await table.create(SandboxRecord(id="1", experiment_id="1", image="1"))
    sandbox_record = await table.get("1")
    assert "1" == sandbox_record.id
    assert "1" == sandbox_record.image


@pytest.mark.asyncio
async def test_list():
    table = await _create_sandbox_table()
    await table.create(SandboxRecord(id="1", experiment_id="1", image="1"))
    await table.create(SandboxRecord(id="2", experiment_id="1", image="2"))
    await table.create(SandboxRecord(id="3", experiment_id="2", image="3"))

    sandbox_records = await table.list(experiment_id="1")
    assert 2 == len(sandbox_records)
    sandbox_records = await table.list(experiment_id="2")
    assert 1 == len(sandbox_records)
    sandbox_records = await table.list()
    assert 3 == len(sandbox_records)
