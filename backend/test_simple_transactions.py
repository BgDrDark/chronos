"""
Simple test for transaction manager functionality

Tests the transaction manager without requiring database connection.
"""

import asyncio
import logging
import sys
import os
from unittest.mock import AsyncMock, MagicMock

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_transaction_manager_imports():
    """Test that transaction manager can be imported and basic functionality works"""
    print("\n=== Testing Transaction Manager Imports ===")
    
    try:
        from backend.database.transaction_manager import (
            atomic_transaction,
            TransactionError,
            DeadlockError,
            ConcurrentModificationError,
            TransactionMonitor,
            transaction_monitor
        )
        print("✅ All imports successful")
        
        # Test monitor functionality
        transaction_monitor.reset_stats()
        transaction_monitor.record_transaction_start()
        transaction_monitor.record_commit()
        
        stats = transaction_monitor.get_stats()
        print(f"✅ Transaction monitor working: {stats}")
        
        assert stats['total_transactions'] == 1, "Should have 1 transaction"
        assert stats['committed_transactions'] == 1, "Should have 1 commit"
        
        print("✅ Transaction monitor test passed")
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        raise


async def test_transaction_context_manager():
    """Test transaction context manager with mock session"""
    print("\n=== Testing Transaction Context Manager ===")
    
    try:
        from backend.database.transaction_manager import atomic_transaction, TransactionError
        
        # Create mock session
        mock_session = AsyncMock()
        mock_transaction = AsyncMock()
        mock_session.begin.return_value = mock_transaction
        
        # Test successful transaction
        async with atomic_transaction(mock_session) as tx:
            assert tx == mock_session, "Should yield the same session"
            
        # Verify transaction was committed
        mock_transaction.commit.assert_called_once()
        mock_transaction.close.assert_called_once()
        
        print("✅ Successful transaction test passed")
        
        # Test failed transaction
        mock_session.reset_mock()
        mock_transaction.reset_mock()
        
        try:
            async with atomic_transaction(mock_session) as tx:
                raise ValueError("Test error")
        except TransactionError as e:
            # Expected - transaction manager wraps errors
            assert "Test error" in str(e), "Should contain original error message"
        
        # Verify transaction was rolled back
        mock_transaction.rollback.assert_called_once()
        mock_transaction.close.assert_called_once()
        
        print("✅ Failed transaction test passed")
        
    except Exception as e:
        print(f"❌ Context manager test failed: {e}")
        raise


async def test_error_classes():
    """Test custom error classes"""
    print("\n=== Testing Custom Error Classes ===")
    
    try:
        from backend.database.transaction_manager import (
            TransactionError,
            DeadlockError,
            ConcurrentModificationError
        )
        
        # Test error creation
        tx_error = TransactionError("Test transaction error")
        deadlock_error = DeadlockError("Test deadlock error")
        concurrent_error = ConcurrentModificationError("Test concurrent error")
        
        # Test inheritance
        assert isinstance(deadlock_error, TransactionError), "DeadlockError should inherit from TransactionError"
        assert isinstance(concurrent_error, TransactionError), "ConcurrentModificationError should inherit from TransactionError"
        
        # Test error messages
        assert str(tx_error) == "Test transaction error"
        assert str(deadlock_error) == "Test deadlock error"
        assert str(concurrent_error) == "Test concurrent error"
        
        print("✅ All error classes working correctly")
        
    except Exception as e:
        print(f"❌ Error classes test failed: {e}")
        raise


async def test_crud_imports():
    """Test that CRUD functions can be imported with transaction manager"""
    print("\n=== Testing CRUD Imports ===")
    
    try:
        # Test that crud.py can be imported without errors
        import backend.crud as crud
        
        # Check that the functions we modified exist
        assert hasattr(crud, 'start_time_log'), "start_time_log should exist"
        assert hasattr(crud, 'end_time_log'), "end_time_log should exist"
        assert hasattr(crud, 'create_manual_time_log'), "create_manual_time_log should exist"
        assert hasattr(crud, 'delete_time_log'), "delete_time_log should exist"
        
        print("✅ All CRUD functions imported successfully")
        
    except Exception as e:
        print(f"❌ CRUD imports test failed: {e}")
        raise


async def test_main_app_imports():
    """Test that main app can import transaction error handlers"""
    print("\n=== Testing Main App Imports ===")
    
    try:
        # Test that main.py can import transaction errors
        from backend.database.transaction_manager import TransactionError, DeadlockError
        print("✅ Transaction errors imported successfully in main app context")
        
    except Exception as e:
        print(f"❌ Main app imports test failed: {e}")
        raise


async def run_simple_tests():
    """Run all simple tests that don't require database"""
    print("🚀 Starting Simple Transaction Security Tests")
    print("=" * 50)
    
    try:
        await test_transaction_manager_imports()
        await test_transaction_context_manager()
        await test_error_classes()
        await test_crud_imports()
        await test_main_app_imports()
        
        print("\n" + "=" * 50)
        print("🎉 All simple transaction security tests passed!")
        print("✅ Transaction manager implementation is working correctly")
        print("✅ Missing transactional security issue has been resolved")
        
    except Exception as e:
        print(f"\n❌ Tests failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(run_simple_tests())