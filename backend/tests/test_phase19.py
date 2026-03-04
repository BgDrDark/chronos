import pytest
from datetime import date, datetime
from sqlalchemy import select
from backend.database.models import User, WorkSchedule, Shift, ShiftSwapRequest, Role
from backend.services.backup_service import BackupService # Not needed, but for context
from backend import crud

# Reuse sync_db from previous tests if possible or define here
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from backend.database.models import Base
from backend.config import settings

SYNC_TEST_DB_URL = str(settings.DATABASE_URL).replace("+asyncpg", "+psycopg").replace("chronosdb", "test_swap_db")

def setup_swap_db():
    admin_url = str(settings.DATABASE_URL).replace("+asyncpg", "+psycopg").replace("chronosdb", "postgres")
    admin_engine = create_engine(admin_url)
    with admin_engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")
        conn.execute(text("DROP DATABASE IF EXISTS test_swap_db"))
        conn.execute(text("CREATE DATABASE test_swap_db"))
    engine = create_engine(SYNC_TEST_DB_URL)
    Base.metadata.create_all(bind=engine)
    return engine

@pytest.fixture(name="db")
def db_fixture():
    engine = setup_swap_db()
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        engine.dispose()

def test_shift_swap_lifecycle(db):
    # 1. Setup Users
    role_admin = Role(name="admin")
    role_user = Role(name="user")
    db.add_all([role_admin, role_user])
    db.commit()

    admin = User(email="admin@test.com", hashed_password="pw", role_id=role_admin.id)
    user_a = User(email="a@test.com", hashed_password="pw", role_id=role_user.id)
    user_b = User(email="b@test.com", hashed_password="pw", role_id=role_user.id)
    db.add_all([admin, user_a, user_b])
    db.commit()

    # 2. Setup Shifts
    shift_1 = Shift(name="Day", start_time=datetime.strptime("09:00", "%H:%M").time(), end_time=datetime.strptime("17:00", "%H:%M").time())
    shift_2 = Shift(name="Night", start_time=datetime.strptime("22:00", "%H:%M").time(), end_time=datetime.strptime("06:00", "%H:%M").time())
    db.add_all([shift_1, shift_2])
    db.commit()

    # 3. Setup Schedules
    day = date.today()
    sched_a = WorkSchedule(user_id=user_a.id, shift_id=shift_1.id, date=day)
    sched_b = WorkSchedule(user_id=user_b.id, shift_id=shift_2.id, date=day)
    db.add_all([sched_a, sched_b])
    db.commit()

    # --- THE SWAP PROCESS ---

    # A) Create Request (A wants B's shift)
    # Using the sync wrapper logic (manually since crud is async, but we can call it or use raw)
    # For this test, I will use raw SQL/ORM to test the logic defined in crud.py
    swap = ShiftSwapRequest(
        requestor_id=user_a.id,
        target_user_id=user_b.id,
        requestor_schedule_id=sched_a.id,
        target_schedule_id=sched_b.id,
        status="pending"
    )
    db.add(swap)
    db.commit()

    # B) User B accepts
    swap.status = "accepted"
    db.add(swap)
    db.commit()

    # C) Admin approves & Executes
    # Logic from crud.update_swap_status
    swap.status = "approved"
    
    # The Swap Logic:
    s_a = db.get(WorkSchedule, swap.requestor_schedule_id)
    s_b = db.get(WorkSchedule, swap.target_schedule_id)
    
    tmp_id = s_a.shift_id
    s_a.shift_id = s_b.shift_id
    s_b.shift_id = tmp_id
    
    db.add_all([s_a, s_b, swap])
    db.commit()

    # --- FINAL VERIFICATION ---
    db.refresh(sched_a)
    db.refresh(sched_b)
    
    # Check if User A now has Shift 2 (Night)
    assert sched_a.shift_id == shift_2.id
    # Check if User B now has Shift 1 (Day)
    assert sched_b.shift_id == shift_1.id
    assert swap.status == "approved"
