import asyncio
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import psycopg
import uuid

from backend.main import app
from backend.database.database import get_db
from backend.database.models import Base
from backend.config import settings
from backend import crud
from backend.schemas import RoleCreate, UserCreate

# Global test DB name for the session
TEST_DB_NAME = f"test_db_{uuid.uuid4().hex[:8]}"

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="session")
async def setup_test_database():
    """Create a test database and drop it after tests."""
    default_db_url_sync = str(settings.DATABASE_URL).replace("postgresql+asyncpg", "postgresql").replace("chronosdb", "postgres")
    conn = None
    try:
        conn = psycopg.connect(default_db_url_sync)
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE {TEST_DB_NAME}")
        print(f"Created database: {TEST_DB_NAME}")
    except Exception as e:
        print(f"Error during test database setup: {e}")
    finally:
        if conn:
            conn.close()
    
    # Create tables via Alembic head
    from alembic.config import Config
    from alembic import command
    import os
    
    # Alembic needs a sync URL
    test_db_url_sync = str(settings.DATABASE_URL).replace("postgresql+asyncpg", "postgresql").replace("chronosdb", TEST_DB_NAME)
    
    # Path to alembic.ini
    alembic_ini_path = os.path.join(os.path.dirname(__file__), "..", "alembic.ini")
    alembic_cfg = Config(alembic_ini_path)
    
    # Ensure script_location is correct
    alembic_cfg.set_main_option("script_location", os.path.join(os.path.dirname(__file__), "..", "alembic"))
    alembic_cfg.set_main_option("sqlalchemy.url", test_db_url_sync)
    
    # Run migrations
    command.upgrade(alembic_cfg, "head")
    print(f"Migrated database {TEST_DB_NAME} to head")

    yield
    
    conn = None
    try:
        conn = psycopg.connect(default_db_url_sync)
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{TEST_DB_NAME}'
              AND pid <> pg_backend_pid();
        """)
        cursor.execute(f"DROP DATABASE IF EXISTS {TEST_DB_NAME} WITH (FORCE)")
        print(f"Dropped database: {TEST_DB_NAME}")
    except Exception as e:
        print(f"Error during test database teardown: {e}")
    finally:
        if conn:
            conn.close()

@pytest.fixture(name="test_db")
async def test_db_fixture(setup_test_database):
    """Provides an AsyncSession for each test."""
    test_db_url = str(settings.DATABASE_URL).replace("chronosdb", TEST_DB_NAME)
    engine = create_async_engine(test_db_url, future=True)
    
    TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()
    
    await engine.dispose()

@pytest.fixture(name="client")
def client_fixture(test_db: AsyncSession):
    app.dependency_overrides[get_db] = lambda: test_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()

@pytest.fixture(name="async_client")
async def async_client_fixture(test_db: AsyncSession):
    app.dependency_overrides[get_db] = lambda: test_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()

@pytest.fixture
async def admin_user_data():
    return {
        "email": "admin@example.com",
        "password": "adminpassword"
    }

@pytest.fixture
async def create_admin_and_login(client: TestClient, admin_user_data: dict, test_db: AsyncSession):
    db_session = test_db
    
    admin_role = await crud.get_role_by_name(db_session, "admin")
    if not admin_role:
            admin_role = await crud.create_role(db_session, RoleCreate(name="admin", description="Administrator"))
    
    admin_user = await crud.get_user_by_email(db_session, admin_user_data["email"])
    if not admin_user:
            user_in = UserCreate(**admin_user_data)
            admin_user = await crud.create_user(db_session, user_in, role_name="admin")

    response = client.post(
        "/auth/token",
        data={"username": admin_user_data["email"], "password": admin_user_data["password"]}
    )
    token = response.json()["access_token"]
    client.headers = {"Authorization": f"Bearer {token}"}
    return client, admin_user