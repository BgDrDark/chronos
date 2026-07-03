import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool

from backend.database.models import Terminal

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def db_session():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    from backend.database.models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = AsyncSession(engine)
    yield async_session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


async def test_terminal_config_default(db_session: AsyncSession):
    t = Terminal(hardware_uuid="test-uuid-1", device_type="tablet", mode="access")
    db_session.add(t)
    await db_session.flush()
    assert t.config is None


async def test_terminal_config_set(db_session: AsyncSession):
    cfg = {"colors": {"primary": "#ff0000"}, "timeouts": {"inactivity": 120}}
    t = Terminal(hardware_uuid="test-uuid-2", device_type="tablet", mode="access", config=cfg)
    db_session.add(t)
    await db_session.flush()
    assert t.config == cfg
