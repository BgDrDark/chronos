import pytest
from datetime import datetime, timedelta, date
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from backend.database.models import Base, User, TimeLog, Role
from backend.services.backup_service import BackupService
from backend.config import settings
from backend.main import app
import json
import io

# --- Sync Setup for Service Tests ---
SYNC_TEST_DB_URL = str(settings.DATABASE_URL).replace("+asyncpg", "+psycopg").replace("chronosdb", "test_backup_db")

def setup_sync_db():
    admin_url = str(settings.DATABASE_URL).replace("+asyncpg", "+psycopg").replace("chronosdb", "postgres")
    admin_engine = create_engine(admin_url)
    
    with admin_engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")
        conn.execute(text("""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = 'test_backup_db'
              AND pid <> pg_backend_pid();
        """))
        conn.execute(text("DROP DATABASE IF EXISTS test_backup_db"))
        conn.execute(text("CREATE DATABASE test_backup_db"))
    
    engine = create_engine(SYNC_TEST_DB_URL)
    Base.metadata.create_all(bind=engine)
    return engine

@pytest.fixture(name="sync_db")
def sync_db_fixture():
    engine = setup_sync_db()
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        engine.dispose()

# --- Unit Tests for BackupService ---

def test_create_backup_logic(sync_db):
    role = Role(name="role_backup_test", description="Test Role")
    sync_db.add(role)
    sync_db.commit()
    
    user = User(email="test_backup@example.com", hashed_password="pw", role_id=role.id)
    sync_db.add(user)
    sync_db.commit()
    
    backup = BackupService.create_backup(sync_db)
    assert "metadata" in backup
    assert "data" in backup
    users_in_backup = [u for u in backup["data"]["users"] if u["email"] == "test_backup@example.com"]
    assert len(users_in_backup) == 1

def test_restore_backup_logic(sync_db):
    backup_data = {
        "metadata": {"timestamp": "now"},
        "data": {
            "roles": [{"id": 101, "name": "role_restore_test", "description": "Desc"}],
            "users": [{"id": 101, "email": "restored_user@test.com", "hashed_password": "pw", "role_id": 101, "is_active": True}]
        }
    }
    BackupService.restore_backup(sync_db, backup_data)
    restored_user = sync_db.query(User).filter_by(email="restored_user@test.com").first()
    assert restored_user is not None
    assert restored_user.id == 101

def test_archive_old_data_logic(sync_db):
    role = Role(name="role_archive_test", description="User")
    sync_db.add(role)
    sync_db.commit()
    
    user = User(email="archive_worker@test.com", hashed_password="pw", role_id=role.id)
    sync_db.add(user)
    sync_db.commit()
    
    old_date = datetime(2023, 1, 1, 10, 0)
    new_date = datetime.now()
    
    log_old = TimeLog(user_id=user.id, start_time=old_date, end_time=old_date + timedelta(hours=8))
    log_new = TimeLog(user_id=user.id, start_time=new_date, end_time=new_date + timedelta(hours=8))
    
    sync_db.add_all([log_old, log_new])
    sync_db.commit()
    
    cutoff = date.today()
    archive = BackupService.archive_old_data(sync_db, cutoff)
    
    assert len(archive["data"]["timelogs"]) >= 1
    remaining_logs = sync_db.query(TimeLog).all()
    assert all(l.start_time >= datetime.combine(cutoff, datetime.min.time()) for l in remaining_logs)

# --- API Integration Tests (Async) ---

@pytest.mark.anyio
async def test_api_backup_permissions(client, regular_user):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/auth/token",
            data={"username": "user@example.com", "password": "userpassword"}
        )
        token = response.json()["access_token"]
        
        response = await ac.get(
            "/system/backup",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403

@pytest.mark.anyio
async def test_api_backup_download_admin(create_admin_and_login):
    admin, token = await create_admin_and_login
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(
            "/system/backup",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "metadata" in data

@pytest.mark.anyio
async def test_api_restore_admin(create_admin_and_login):
    admin, token = await create_admin_and_login
    backup_content = {
        "metadata": {"version": "1.0"},
        "data": {
            "roles": [{"id": 999, "name": "role_api_restore", "description": "temp"}],
            "users": []
        }
    }
    file_content = json.dumps(backup_content).encode('utf-8')
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/system/restore",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("backup.json", file_content, "application/json")}
        )
        assert response.status_code == 200

@pytest.mark.anyio
async def test_api_archive_admin(create_admin_and_login):
    admin, token = await create_admin_and_login
    cutoff = (date.today() - timedelta(days=1)).isoformat()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            f"/system/archive?cutoff_date={cutoff}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
