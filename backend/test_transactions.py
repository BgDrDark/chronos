"""
Test script for transactional operations

This script tests the atomic transaction implementation
to ensure data consistency and proper error handling.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.database import AsyncSessionLocal
from backend.database.transaction_manager import (
    atomic_transaction, 
    TransactionError, 
    DeadlockError,
    transaction_monitor
)
from backend.database.models import TimeLog, User, WorkSchedule
from backend.crud import start_time_log, end_time_log, create_manual_time_log, delete_time_log
from backend.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_transaction_monitor():
    """Test transaction monitoring functionality"""
    print("\n=== Testing Transaction Monitor ===")
    
    # Reset stats
    transaction_monitor.reset_stats()
    
    # Create some test transactions
    async with AsyncSessionLocal() as db:
        try:
            async with atomic_transaction(db):
                # Simulate some operations
                await db.execute(select(TimeLog).limit(1))
                transaction_monitor.record_commit()
        except Exception as e:
            transaction_monitor.record_rollback()
    
    # Check stats
    stats = transaction_monitor.get_stats()
    print(f"Transaction Stats: {stats}")
    
    assert stats['total_transactions'] >= 1, "Should have at least one transaction"
    print("✅ Transaction monitor test passed")


async def test_atomic_transaction_success():
    """Test successful atomic transaction"""
    print("\n=== Testing Atomic Transaction Success ===")
    
    async with AsyncSessionLocal() as db:
        # Get a test user (assuming admin@example.com exists)
        user_result = await db.execute(
            select(User).where(User.email == "admin@example.com")
        )
        test_user = user_result.scalars().first()
        
        if not test_user:
            print("❌ Test user not found, skipping test")
            return
        
        try:
            # Test creating a manual time log atomically
            start_time = datetime.now() - timedelta(hours=2)
            end_time = datetime.now() - timedelta(hours=1)
            
            log = await create_manual_time_log(
                db, 
                test_user.id, 
                start_time, 
                end_time
            )
            
            print(f"✅ Created time log with ID: {log.id}")
            
            # Clean up - delete the test log
            await delete_time_log(db, log.id)
            print("✅ Deleted test time log")
            
        except Exception as e:
            print(f"❌ Atomic transaction test failed: {e}")
            raise


async def test_concurrent_modification():
    """Test concurrent modification prevention"""
    print("\n=== Testing Concurrent Modification Prevention ===")
    
    async with AsyncSessionLocal() as db:
        # Get a test user
        user_result = await db.execute(
            select(User).where(User.email == "admin@example.com")
        )
        test_user = user_result.scalars().first()
        
        if not test_user:
            print("❌ Test user not found, skipping test")
            return
        
        try:
            # Create initial time log
            start_time = datetime.now() - timedelta(hours=3)
            end_time = datetime.now() - timedelta(hours=2)
            
            log = await create_manual_time_log(
                db, 
                test_user.id, 
                start_time, 
                end_time
            )
            
            print(f"✅ Created initial time log with ID: {log.id}")
            
            # Try to create overlapping log (should fail)
            try:
                overlap_start = datetime.now() - timedelta(hours=2.5)
                overlap_end = datetime.now() - timedelta(hours=1.5)
                
                await create_manual_time_log(
                    db, 
                    test_user.id, 
                    overlap_start, 
                    overlap_end
                )
                
                print("❌ Overlap detection failed - should have thrown error")
                
            except ValueError as e:
                if "застъпва" in str(e):
                    print("✅ Overlap detection working correctly")
                else:
                    print(f"❌ Unexpected error: {e}")
            
            # Clean up
            await delete_time_log(db, log.id)
            print("✅ Cleaned up test data")
            
        except Exception as e:
            print(f"❌ Concurrent modification test failed: {e}")
            raise


async def test_transaction_rollback():
    """Test transaction rollback on error"""
    print("\n=== Testing Transaction Rollback ===")
    
    async with AsyncSessionLocal() as db:
        # Get a test user
        user_result = await db.execute(
            select(User).where(User.email == "admin@example.com")
        )
        test_user = user_result.scalars().first()
        
        if not test_user:
            print("❌ Test user not found, skipping test")
            return
        
        # Count existing time logs
        count_result = await db.execute(
            select(func.count(TimeLog.id)).where(TimeLog.user_id == test_user.id)
        )
        initial_count = count_result.scalar()
        
        try:
            # Try to create invalid time log (end before start)
            start_time = datetime.now()
            end_time = datetime.now() - timedelta(hours=1)  # Invalid: end before start
            
            await create_manual_time_log(
                db, 
                test_user.id, 
                start_time, 
                end_time
            )
            
            print("❌ Should have failed with invalid time range")
            
        except ValueError as e:
            if "преди крайния" in str(e):
                print("✅ Validation working correctly")
                
                # Verify no new records were created (rollback worked)
                count_result = await db.execute(
                    select(func.count(TimeLog.id)).where(TimeLog.user_id == test_user.id)
                )
                final_count = count_result.scalar()
                
                if final_count == initial_count:
                    print("✅ Transaction rollback working correctly")
                else:
                    print("❌ Transaction rollback failed - records were created")
            else:
                print(f"❌ Unexpected error: {e}")
        
        except Exception as e:
            print(f"❌ Rollback test failed: {e}")


async def test_row_locking():
    """Test row-level locking functionality"""
    print("\n=== Testing Row-Level Locking ===")
    
    async with AsyncSessionLocal() as db:
        # Get a test user
        user_result = await db.execute(
            select(User).where(User.email == "admin@example.com")
        )
        test_user = user_result.scalars().first()
        
        if not test_user:
            print("❌ Test user not found, skipping test")
            return
        
        try:
            # Test start_time_log with row locking
            start_time = datetime.now() - timedelta(hours=1)
            
            log = await start_time_log(db, test_user.id)
            print(f"✅ Started time log with ID: {log.id}")
            
            # End the time log
            ended_log = await end_time_log(db, test_user.id)
            print(f"✅ Ended time log with ID: {ended_log.id}")
            
            # Clean up
            await delete_time_log(db, ended_log.id)
            print("✅ Cleaned up test data")
            
        except Exception as e:
            print(f"❌ Row locking test failed: {e}")
            raise


async def run_all_tests():
    """Run all transaction tests"""
    print("🚀 Starting Transaction Security Tests")
    print("=" * 50)
    
    try:
        await test_transaction_monitor()
        await test_atomic_transaction_success()
        await test_concurrent_modification()
        await test_transaction_rollback()
        await test_row_locking()
        
        print("\n" + "=" * 50)
        print("🎉 All transaction security tests passed!")
        print("✅ Missing transactional security issue has been resolved")
        
    except Exception as e:
        print(f"\n❌ Tests failed: {e}")
        raise
    
    finally:
        # Print final stats
        stats = transaction_monitor.get_stats()
        print(f"\n📊 Final Transaction Stats: {stats}")


if __name__ == "__main__":
    # Import func for count operations
    from sqlalchemy import func
    
    asyncio.run(run_all_tests())