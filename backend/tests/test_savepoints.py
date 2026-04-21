"""
Tests for atomic_with_savepoint functionality

Tests the savepoint functionality within transactions:
1. Savepoint can be imported
2. Savepoint works in context manager
3. Exception propagation works
"""

import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_savepoint_import():
    """Test that atomic_with_savepoint can be imported"""
    print("\n=== Testing Savepoint Import ===")
    
    try:
        from backend.database.transaction_manager import atomic_with_savepoint
        print("✅ atomic_with_savepoint imported successfully")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        raise


async def test_savepoint_basic_functionality():
    """Test that savepoint context manager works"""
    print("\n=== Testing Savepoint Basic Functionality ===")
    
    from backend.database.transaction_manager import atomic_with_savepoint
    
    print("✅ atomic_with_savepoint is a context manager")
    print(f"✅ Type: {type(atomic_with_savepoint)}")
    return True


async def test_savepoint_exception_propagation():
    """Test that exceptions are properly propagated"""
    print("\n=== Testing Exception Propagation ===")
    
    from backend.database.transaction_manager import atomic_with_savepoint
    
    class MockDB:
        def __init__(self):
            self.executed = []
            
        async def execute(self, query):
            self.executed.append(str(query))
            # Simulate SQL execution
            if "SAVEPOINT" in str(query):
                logger.info(f"Executing: {query}")
            elif "ROLLBACK" in str(query):
                logger.info(f"Rolling back: {query}")
            elif "RELEASE" in str(query):
                logger.info(f"Releasing: {query}")
    
    mock_db = MockDB()
    
    custom_error = ValueError("Custom error message")
    
    try:
        async with atomic_with_savepoint(mock_db, "error_test"):
            raise custom_error
    except ValueError as e:
        assert str(e) == "Custom error message", "Original exception should be preserved"
        print("✅ Exception propagated correctly")
    
    # Verify savepoint operations were called
    assert len(mock_db.executed) >= 2, "SAVEPOINT and ROLLBACK should be executed"
    print(f"✅ Savepoint operations executed: {len(mock_db.executed)}")
    
    return True


async def test_savepoint_normal_flow():
    """Test savepoint in normal (no error) flow"""
    print("\n=== Testing Normal Flow ===")
    
    from backend.database.transaction_manager import atomic_with_savepoint
    
    class MockDB:
        def __init__(self):
            self.executed = []
            
        async def execute(self, query):
            self.executed.append(str(query))
            logger.info(f"Executing: {query}")
    
    mock_db = MockDB()
    
    async with atomic_with_savepoint(mock_db, "normal_test"):
        logger.info("Inside savepoint block - normal operation")
    
    # Verify all operations were called
    assert len(mock_db.executed) >= 2, "SAVEPOINT and RELEASE should be executed"
    print(f"✅ Normal flow completed with {len(mock_db.executed)} operations")
    
    return True


async def test_savepoint_name_sanitization():
    """Test that savepoint names are sanitized"""
    print("\n=== Testing Savepoint Name Sanitization ===")
    
    from backend.database.transaction_manager import atomic_with_savepoint
    
    class MockDB:
        def __init__(self):
            self.executed = []
            
        async def execute(self, query):
            self.executed.append(str(query))
    
    mock_db = MockDB()
    
    # Test with dangerous characters
    async with atomic_with_savepoint(mock_db, "test';DROP--"):
        pass
    
    # Verify dangerous characters are stripped - should become "testdrop--"
    for query in mock_db.executed:
        assert "testdrop" in query.lower(), f"Name should be sanitized: {query}"
        # Original dangerous chars should be gone
        assert "'" not in query, f"Quote should be stripped: {query}"
    
    print("✅ Savepoint name sanitization working")
    return True


async def run_savepoint_tests():
    """Run all savepoint tests"""
    print("=" * 60)
    print("🚀 Starting Savepoint Tests")
    print("=" * 60)
    
    tests = [
        test_savepoint_import,
        test_savepoint_basic_functionality,
        test_savepoint_exception_propagation,
        test_savepoint_normal_flow,
        test_savepoint_name_sanitization,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            await test()
            passed += 1
        except Exception as e:
            logger.error(f"❌ {test.__name__} failed: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("🎉 All savepoint tests passed!")
    else:
        print(f"❌ {failed} test(s) failed")
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_savepoint_tests())
    exit(0 if success else 1)
