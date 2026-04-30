"""
Tests for Repository Pattern - Clock In/Out functionality

Tests the repositories that handle time tracking:
- TimeRepository: clock_in, clock_out, get_active_timelog
- UserRepository: user operations
"""

import asyncio
import logging
from datetime import datetime, date, time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_import_repositories():
    """Test that all repositories can be imported"""
    print("\n=== Testing Repository Imports ===")
    
    try:
        from backend.crud.repositories import (
            user_repo, time_repo, company_repo, 
            settings_repo, vehicle_repo, payroll_repo
        )
        print("✅ All repositories imported successfully")
        
        # Test that they are instances
        assert user_repo is not None
        assert time_repo is not None
        print("✅ Repository instances available")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        raise


async def test_time_repository_clock_in():
    """Test clock in via TimeRepository"""
    print("\n=== Testing Clock In ===")
    
    from backend.database.database import AsyncSessionLocal
    from backend.crud.repositories import time_repo
    
    async with AsyncSessionLocal() as db:
        try:
            # Check for active timelog first
            active_log = await time_repo.get_active_timelog(db, user_id=1)
            
            if active_log:
                print(f"ℹ️ User already has active timelog: {active_log.id}")
                print("✅ TimeRepository get_active_timelog working")
                return True
            
            # Clock in
            log = await time_repo.start_time_log(db, user_id=1)
            
            assert log is not None
            assert log.user_id == 1
            assert log.start_time is not None
            assert log.end_time is None
            
            await db.commit()
            
            print(f"✅ Clock in SUCCESS: id={log.id}, start_time={log.start_time}")
            return log.id
        except Exception as e:
            print(f"❌ Clock in failed: {e}")
            await db.rollback()
            raise


async def test_time_repository_clock_out(timelog_id: int = None):
    """Test clock out via TimeRepository"""
    print("\n=== Testing Clock Out ===")
    
    from backend.database.database import AsyncSessionLocal
    from backend.crud.repositories import time_repo
    
    async with AsyncSessionLocal() as db:
        try:
            # Get active timelog
            if timelog_id is None:
                active_log = await time_repo.get_active_timelog(db, user_id=1)
                if not active_log:
                    print("ℹ️ No active timelog to clock out")
                    return None
                timelog_id = active_log.id
            
            # Clock out
            log = await time_repo.end_time_log(db, user_id=1, notes="Test clock out")
            
            assert log is not None
            assert log.end_time is not None
            
            await db.commit()
            
            print(f"✅ Clock out SUCCESS: id={log.id}, end_time={log.end_time}")
            return log.id
        except Exception as e:
            print(f"❌ Clock out failed: {e}")
            await db.rollback()
            raise


async def test_time_repository_get_active():
    """Test get_active_timelog"""
    print("\n=== Testing Get Active Timelog ===")
    
    from backend.database.database import AsyncSessionLocal
    from backend.crud.repositories import time_repo
    
    async with AsyncSessionLocal() as db:
        try:
            active_log = await time_repo.get_active_timelog(db, user_id=1)
            
            if active_log:
                print(f"✅ Active timelog found: id={active_log.id}, start_time={active_log.start_time}")
            else:
                print("ℹ️ No active timelog (user may have clocked out)")
            
            return active_log
        except Exception as e:
            print(f"❌ Get active timelog failed: {e}")
            raise


async def test_time_repository_manual_timelog():
    """Test create_manual_time_log"""
    print("\n=== Testing Manual Timelog ===")
    
    from backend.database.database import AsyncSessionLocal
    from backend.crud.repositories import time_repo
    
    async with AsyncSessionLocal() as db:
        try:
            start = datetime(2026, 4, 23, 9, 0, 0)
            end = datetime(2026, 4, 23, 17, 0, 0)
            
            log = await time_repo.create_manual_time_log(
                db, 
                user_id=1,
                start_time=start,
                end_time=end,
                break_duration_minutes=30,
                notes="Test manual entry"
            )
            
            assert log is not None
            assert log.user_id == 1
            assert log.is_manual == True
            
            await db.commit()
            
            print(f"✅ Manual timelog SUCCESS: id={log.id}")
            return log.id
        except Exception as e:
            print(f"❌ Manual timelog failed: {e}")
            await db.rollback()
            raise


async def test_time_repository_shifts():
    """Test shift operations"""
    print("\n=== Testing Shifts ===")
    
    from backend.database.database import AsyncSessionLocal
    from backend.crud.repositories import time_repo
    
    async with AsyncSessionLocal() as db:
        try:
            # Get all shifts
            shifts = await time_repo.get_all_shifts(db)
            print(f"✅ Found {len(shifts)} shifts")
            
            # Get shift by ID if exists
            if shifts:
                shift = await time_repo.get_shift_by_id(db, shifts[0].id)
                assert shift is not None
                print(f"✅ Get shift by ID: {shift.name}")
            
            return True
        except Exception as e:
            print(f"❌ Shifts test failed: {e}")
            raise


async def test_time_repository_schedule():
    """Test schedule operations"""
    print("\n=== Testing Schedules ===")
    
    from backend.database.database import AsyncSessionLocal
    from backend.crud.repositories import time_repo
    
    async with AsyncSessionLocal() as db:
        try:
            # Get schedules by period
            from datetime import date
            start = date(2026, 4, 1)
            end = date(2026, 4, 30)
            
            schedules = await time_repo.get_schedules_by_period(db, start, end)
            print(f"✅ Found {len(schedules)} schedules for period")
            
            return True
        except Exception as e:
            print(f"❌ Schedules test failed: {e}")
            raise


async def test_user_repository():
    """Test user repository operations"""
    print("\n=== Testing User Repository ===")
    
    from backend.database.database import AsyncSessionLocal
    from backend.crud.repositories import user_repo
    
    async with AsyncSessionLocal() as db:
        try:
            # Get users
            users = await user_repo.get_users(db, limit=5)
            print(f"✅ Found {len(users)} users")
            
            if users:
                user = await user_repo.get_by_id(db, users[0].id)
                assert user is not None
                print(f"✅ Get user by ID: {user.email}")
            
            return True
        except Exception as e:
            print(f"❌ User repository test failed: {e}")
            raise


async def test_settings_repository():
    """Test settings repository operations"""
    print("\n=== Testing Settings Repository ===")
    
    from backend.database.database import AsyncSessionLocal
    from backend.crud.repositories import settings_repo
    
    async with AsyncSessionLocal() as db:
        try:
            # Get and set setting
            smtp_server = await settings_repo.get_setting(db, "smtp_server")
            print(f"✅ SMTP server setting: {smtp_server or 'not set'}")
            
            # Check SMTP configured
            is_configured = await settings_repo.is_smtp_configured(db)
            print(f"✅ SMTP configured: {is_configured}")
            
            return True
        except Exception as e:
            print(f"❌ Settings repository test failed: {e}")
            raise


async def run_repository_tests():
    """Run all repository tests"""
    print("=" * 60)
    print("🚀 Starting Repository Tests (Clock In/Out)")
    print("=" * 60)
    
    tests = [
        ("Import Repositories", test_import_repositories),
        ("Get Active Timelog", test_time_repository_get_active),
        ("Clock In", test_time_repository_clock_in),
        ("Clock Out", test_time_repository_clock_out),
        ("Manual Timelog", test_time_repository_manual_timelog),
        ("Shifts", test_time_repository_shifts),
        ("Schedules", test_time_repository_schedule),
        ("User Repository", test_user_repository),
        ("Settings Repository", test_settings_repository),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            if name == "Clock Out":
                result = await test_func(results[1] if len(results) > 1 else None)
            else:
                result = await test_func()
            results.append(result)
            print(f"✅ {name}: PASSED")
        except Exception as e:
            print(f"❌ {name}: FAILED - {e}")
            results.append(None)
    
    print("\n" + "=" * 60)
    print("📊 Results Summary")
    print("=" * 60)
    
    passed = sum(1 for r in results if r is not None)
    print(f"Passed: {passed}/{len(tests)}")
    
    if passed == len(tests):
        print("🎉 All repository tests passed!")
    else:
        print(f"❌ {len(tests) - passed} test(s) failed")
    
    return passed == len(tests)


if __name__ == "__main__":
    success = asyncio.run(run_repository_tests())
    exit(0 if success else 1)
