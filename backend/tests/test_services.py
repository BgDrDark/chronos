"""
Tests for Shift Swap Service, Leave Service, Time Tracking Service, Notification Service, Contract Service,
Payroll Service, Settings Service, and Auth Service

Tests the services we created for business logic separation:
- shift_swap_service.py
- leave_service.py
- time_tracking_service.py
- notification_service.py
- contract_service.py
- payroll_service.py (NEW)
- settings_service.py (NEW)
- auth_service.py (NEW)
"""

import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_import_services():
    """Test that all services can be imported"""
    print("\n=== Testing Service Imports ===")
    
    try:
        from backend.services.shift_swap_service import shift_swap_service, ShiftSwapService
        from backend.services.leave_service import leave_service, LeaveService
        from backend.services.time_tracking_service import time_tracking_service, TimeTrackingService
        from backend.services.notification_service import notification_service, NotificationService
        from backend.services.contract_service import contract_service, ContractService
        from backend.services.payroll_service import payroll_service, PayrollService
        from backend.services.settings_service import settings_service, SettingsService
        from backend.services.auth_service import auth_service, AuthService
        print("✅ shift_swap_service imported successfully")
        print("✅ leave_service imported successfully")
        print("✅ time_tracking_service imported successfully")
        print("✅ notification_service imported successfully")
        print("✅ contract_service imported successfully")
        print("✅ payroll_service imported successfully")
        print("✅ settings_service imported successfully")
        print("✅ auth_service imported successfully")
        
        assert ShiftSwapService is not None
        assert LeaveService is not None
        assert TimeTrackingService is not None
        assert NotificationService is not None
        assert ContractService is not None
        assert PayrollService is not None
        assert SettingsService is not None
        assert AuthService is not None
        print("✅ Service classes available")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        raise


async def test_service_initialization():
    """Test that services can be initialized"""
    print("\n=== Testing Service Initialization ===")
    
    from unittest.mock import MagicMock
    
    mock_db = MagicMock()
    
    try:
        from backend.services.shift_swap_service import ShiftSwapService
        from backend.services.leave_service import LeaveService
        from backend.services.time_tracking_service import TimeTrackingService
        from backend.services.notification_service import NotificationService
        from backend.services.contract_service import ContractService
        from backend.services.payroll_service import PayrollService
        from backend.services.settings_service import SettingsService
        from backend.services.auth_service import AuthService
        
        swap_service = ShiftSwapService(mock_db)
        assert swap_service is not None
        assert swap_service.db == mock_db
        print("✅ ShiftSwapService initialized")
        
        leave_service = LeaveService(mock_db)
        assert leave_service is not None
        assert leave_service.db == mock_db
        print("✅ LeaveService initialized")
        
        time_service = TimeTrackingService(mock_db)
        assert time_service is not None
        assert time_service.db == mock_db
        print("✅ TimeTrackingService initialized")
        
        notif_service = NotificationService(mock_db)
        assert notif_service is not None
        assert notif_service.db == mock_db
        print("✅ NotificationService initialized")
        
        contract_svc = ContractService(mock_db)
        assert contract_svc is not None
        assert contract_svc.db == mock_db
        print("✅ ContractService initialized")
        
        payroll_svc = PayrollService(mock_db)
        assert payroll_svc is not None
        assert payroll_svc.db == mock_db
        print("✅ PayrollService initialized")
        
        settings_svc = SettingsService(mock_db)
        assert settings_svc is not None
        assert settings_svc.db == mock_db
        print("✅ SettingsService initialized")
        
        auth_svc = AuthService(mock_db)
        assert auth_svc is not None
        assert auth_svc.db == mock_db
        print("✅ AuthService initialized")
        
        return True
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        raise


async def test_shift_swap_service_methods():
    """Test that ShiftSwapService has required methods"""
    print("\n=== Testing ShiftSwapService Methods ===")
    
    from unittest.mock import MagicMock
    mock_db = MagicMock()
    
    from backend.services.shift_swap_service import ShiftSwapService
    service = ShiftSwapService(mock_db)
    
    required_methods = [
        'create_request',
        'get_request',
        'get_user_requests',
        'get_pending_requests',
        'update_status',
        'delete_request',
    ]
    
    for method in required_methods:
        assert hasattr(service, method), f"Missing method: {method}"
        assert callable(getattr(service, method)), f"Not callable: {method}"
        print(f"✅ Method exists: {method}")
    
    return True


async def test_leave_service_methods():
    """Test that LeaveService has required methods"""
    print("\n=== Testing LeaveService Methods ===")
    
    from unittest.mock import MagicMock
    mock_db = MagicMock()
    
    from backend.services.leave_service import LeaveService
    service = LeaveService(mock_db)
    
    required_methods = [
        'get_balance',
        'calculate_working_days',
        'approve_request',
        'reject_request',
        'cancel_request',
        'get_my_requests',
        'get_pending_requests',
    ]
    
    for method in required_methods:
        assert hasattr(service, method), f"Missing method: {method}"
        assert callable(getattr(service, method)), f"Not callable: {method}"
        print(f"✅ Method exists: {method}")
    
    return True


async def test_time_tracking_service_methods():
    """Test that TimeTrackingService has required methods"""
    print("\n=== Testing TimeTrackingService Methods ===")
    
    from unittest.mock import MagicMock
    mock_db = MagicMock()
    
    from backend.services.time_tracking_service import TimeTrackingService
    service = TimeTrackingService(mock_db)
    
    required_methods = [
        'validate_geofence_entry',
        'validate_geofence_exit',
        'calculate_working_hours',
        'get_schedule_for_date',
        'get_matching_shift',
        'snap_time_to_shift',
        'check_time_overlap',
        'get_active_timelog',
        'get_user_timelogs',
        'clock_in',
        'clock_out',
    ]
    
    for method in required_methods:
        assert hasattr(service, method), f"Missing method: {method}"
        assert callable(getattr(service, method)), f"Not callable: {method}"
        print(f"✅ Method exists: {method}")
    
    return True


async def test_notification_service_methods():
    """Test that NotificationService has required methods"""
    print("\n=== Testing NotificationService Methods ===")
    
    from unittest.mock import MagicMock
    mock_db = MagicMock()
    
    from backend.services.notification_service import NotificationService
    service = NotificationService(mock_db)
    
    required_methods = [
        'subscribe',
        'unsubscribe',
        'send',
        'send_multiple',
        'broadcast',
        'get_subscriptions',
    ]
    
    for method in required_methods:
        assert hasattr(service, method), f"Missing method: {method}"
        assert callable(getattr(service, method)), f"Not callable: {method}"
        print(f"✅ Method exists: {method}")
    
    return True


async def test_contract_service_methods():
    """Test that ContractService has required methods"""
    print("\n=== Testing ContractService Methods ===")
    
    from unittest.mock import MagicMock
    mock_db = MagicMock()
    
    from backend.services.contract_service import ContractService
    service = ContractService(mock_db)
    
    required_methods = [
        'create',
        'get_by_id',
        'get_active_for_user',
        'get_all_for_user',
        'get_expiring_soon',
        'extend',
        'terminate',
        'deactivate_expired',
        'get_contracts_by_company',
    ]
    
    for method in required_methods:
        assert hasattr(service, method), f"Missing method: {method}"
        assert callable(getattr(service, method)), f"Not callable: {method}"
        print(f"✅ Method exists: {method}")
    
    return True


async def test_payroll_service_methods():
    """Test that PayrollService has required methods"""
    print("\n=== Testing PayrollService Methods ===")
    
    from unittest.mock import MagicMock
    mock_db = MagicMock()
    
    from backend.services.payroll_service import PayrollService
    service = PayrollService(mock_db)
    
    required_methods = [
        'get_global_config',
        'update_global_config',
        'calculate_payroll',
        'create_payslip',
        'mark_payslip_as_paid',
        'set_monthly_work_days',
    ]
    
    for method in required_methods:
        assert hasattr(service, method), f"Missing method: {method}"
        assert callable(getattr(service, method)), f"Not callable: {method}"
        print(f"✅ Method exists: {method}")
    
    return True


async def test_settings_service_methods():
    """Test that SettingsService has required methods"""
    print("\n=== Testing SettingsService Methods ===")
    
    from unittest.mock import MagicMock
    mock_db = MagicMock()
    
    from backend.services.settings_service import SettingsService
    service = SettingsService(mock_db)
    
    required_methods = [
        'get_setting',
        'set_setting',
        'delete_setting',
        'get_all_settings',
        'get_settings_by_category',
        'set_multiple_settings',
    ]
    
    for method in required_methods:
        assert hasattr(service, method), f"Missing method: {method}"
        assert callable(getattr(service, method)), f"Not callable: {method}"
        print(f"✅ Method exists: {method}")
    
    return True


async def test_auth_service_methods():
    """Test that AuthService has required methods"""
    print("\n=== Testing AuthService Methods ===")
    
    from unittest.mock import MagicMock
    mock_db = MagicMock()
    
    from backend.services.auth_service import AuthService
    service = AuthService(mock_db)
    
    required_methods = [
        'verify_password',
        'verify_totp',
        'create_session',
        'invalidate_session',
        'verify_session',
        'refresh_session',
    ]
    
    for method in required_methods:
        assert hasattr(service, method), f"Missing method: {method}"
        assert callable(getattr(service, method)), f"Not callable: {method}"
        print(f"✅ Method exists: {method}")
    
    return True


async def test_mutations_import_services():
    """Test that mutations can import all services"""
    print("\n=== Testing Mutations Import ===")
    
    try:
        from backend.graphql import mutations
        print("✅ Mutations module imported")
        
        import inspect
        source = inspect.getsource(mutations)
        
        assert 'shift_swap_service' in source, "shift_swap_service not found in mutations"
        assert 'leave_service' in source, "leave_service not found in mutations"
        assert 'time_tracking_service' in source, "time_tracking_service not found in mutations"
        assert 'notification_service' in source, "notification_service not found in mutations"
        assert 'auth_service' in source, "auth_service not found in mutations"
        assert 'payroll_service' in source, "payroll_service not found in mutations"
        assert 'settings_service' in source, "settings_service not found in mutations"
        print("✅ All services referenced in mutations")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        raise


async def run_service_tests():
    """Run all service tests"""
    print("\n" + "="*50)
    print("RUNNING SERVICE TESTS")
    print("="*50)
    
    tests = [
        test_import_services(),
        test_service_initialization(),
        test_shift_swap_service_methods(),
        test_leave_service_methods(),
        test_time_tracking_service_methods(),
        test_notification_service_methods(),
        test_contract_service_methods(),
        test_payroll_service_methods(),
        test_settings_service_methods(),
        test_auth_service_methods(),
        test_mutations_import_services(),
    ]
    
    results = []
    for test in tests:
        try:
            result = await test
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed: {e}")
            results.append(False)
    
    print("\n" + "="*50)
    if all(results):
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("="*50)
    
    return all(results)


if __name__ == "__main__":
    asyncio.run(run_service_tests())