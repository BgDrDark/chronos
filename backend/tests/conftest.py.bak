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
from backend.database.models import Company, Role

# Global test DB name for the session
TEST_DB_NAME = f"test_db_{uuid.uuid4().hex[:8]}"

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="session")
async def setup_test_database():
    """Create a test database and drop it after tests."""
    db_url = str(settings.DATABASE_URL)
    default_db_url_sync = db_url.replace("postgresql+asyncpg", "postgresql")
    # Extract database name and replace with 'postgres'
    if "/" in default_db_url_sync:
        base_url = default_db_url_sync.rsplit("/", 1)[0]
        default_db_url_sync = f"{base_url}/postgres"
    
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
    
    # Create tables using SQLAlchemy create_all (bypasses broken migrations)
    from sqlalchemy import create_engine
    from backend.database.models import Base
    
    test_db_url_sync = db_url.replace("postgresql+asyncpg", "postgresql").rsplit("/", 1)[0] + f"/{TEST_DB_NAME}"
    sync_engine = create_engine(test_db_url_sync)
    
    # Create all tables from models
    Base.metadata.create_all(bind=sync_engine)
    sync_engine.dispose()
    print(f"Created tables in database {TEST_DB_NAME}")

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
    db_url = str(settings.DATABASE_URL)
    test_db_url = db_url.rsplit("/", 1)[0] + f"/{TEST_DB_NAME}"
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

@pytest.fixture(name="db")
async def db_fixture(test_db: AsyncSession):
    """Alias for test_db fixture for backward compatibility."""
    return test_db

@pytest.fixture
async def test_company(test_db: AsyncSession) -> Company:
    """Create a test company with unique EIK."""
    unique_suffix = uuid.uuid4().hex[:6]
    company = Company(
        name=f"Test Company {unique_suffix}",
        eik=f"123456{unique_suffix}",
        bulstat=f"BG{unique_suffix}56789"
    )
    test_db.add(company)
    await test_db.commit()
    await test_db.refresh(company)
    return company

@pytest.fixture
async def test_role(test_db: AsyncSession):
    """Create admin role."""
    role = await crud.get_role_by_name(test_db, "admin")
    if not role:
        role = await crud.create_role(test_db, RoleCreate(name="admin", description="Admin"))
    return role

@pytest.fixture
async def test_user(test_db: AsyncSession, test_company: Company, test_role: Role):
    """Create a test user."""
    from backend.database.models import Role
    unique_id = uuid.uuid4().hex[:6]
    user = await crud.create_user(
        test_db,
        UserCreate(
            email=f"employee_{unique_id}@test.com",
            password="testpassword123",
            first_name="Иван",
            last_name="Иванов",
            egn="1234567890"
        ),
        role_name="employee"
    )
    user.company_id = test_company.id
    await test_db.commit()
    await test_db.refresh(user)
    return user

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