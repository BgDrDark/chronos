"""
Data integrity and audit trail tests for financial compliance
Тестове за цялостност на данни и audit trail за финансови регулации
"""

import pytest
from decimal import Decimal
from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch, AsyncMock
import json

from backend import crud, schemas
from backend.database.models import sofia_now


# Audit trail requirements for financial systems
AUDIT_TRAIL_REQUIREMENTS = {
    'immutable_records': True,  # Одобрените финансови записи не могат да се променят
    'complete_traceability': True,  # Всеки CRUD операция трябва да се логва
    'user_identification': True,  # Всеки лог трябва да съдържа user_id
    'timestamp_precision': 'second',  # Точност на timestamp
    'ip_address_logging': True,  # IP адрес на клиента
    'user_agent_logging': True,  # User Agent на клиента
    'data_before_after': True,  # Запазване на данни преди и след промяна
}

# Data integrity validation rules
DATA_INTEGRITY_RULES = {
    'financial_summaries': {
        'gross_minus_deductions_equals_net': True,
        'no_negative_values': True,
        'decimal_precision': 2,  # 2 decimals for money
        'audit_trail_complete': True
    },
    'time_logs': {
        'end_time_after_start_time': True,
        'no_future_dates': True,
        'reasonable_hours_range': [0, 24],  # Max 24 hours per day
        'geolocation_valid': True
    }
}


@pytest.mark.asyncio
async def test_financial_audit_trail_completeness(db: AsyncSession, test_user):
    """Тест за completeness на audit trail за финансови операции"""
    
    # Create payroll record
    payroll_data = schemas.PayrollRecordCreate(
        user_id=test_user.id,
        month=sofia_now().month,
        year=sofia_now().year,
        gross_salary=Decimal('1500.00'),
        net_salary=Decimal('1200.00'),
        taxes=Decimal('180.00'),
        social_security=Decimal('147.00'),
        health_insurance=Decimal('48.00'),
        other_deductions=Decimal('25.00'),
        status='calculated'
    )
    
    created_payroll = await crud.create_payroll_record(db, payroll_data)
    
    # Check that audit log is created
    audit_logs = await crud.get_audit_logs(db, user_id=test_user.id)
    
    # Filter for payroll creation logs
    payroll_logs = [log for log in audit_logs if log.action == 'payroll_record_created']
    
    assert len(payroll_logs) > 0, "Трябва да има audit лог за създаване на payroll запис"
    
    # Verify audit log contains required fields
    latest_log = payroll_logs[0]
    assert latest_log.user_id == test_user.id, "Audit логът трябва да съдържа user_id"
    assert latest_log.action == 'payroll_record_created', "Действието трябва да е правилно"
    assert latest_log.timestamp is not None, "Трябва да има timestamp"
    assert latest_log.ip_address is not None, "Трябва да има IP адрес"
    assert latest_log.user_agent is not None, "Трябва да има user agent"
    
    # Verify data preservation
    assert 'record_id' in latest_log.details or 'payroll_id' in latest_log.details, \
        "Audit логът трябва да съдържа ID на записа"
    
    log_details = json.loads(latest_log.details) if isinstance(latest_log.details, str) else latest_log.details
    assert 'gross_salary' in log_details, "Трябва да се запази съществената информация"


@pytest.mark.asyncio
async def test_payroll_data_consistency_validation(db: AsyncSession, test_user):
    """Тест за консистентност на payroll данните"""
    
    # Create consistent payroll data
    gross_salary = Decimal('2000.00')
    taxes = Decimal('200.00')  # 10%
    social_security = Decimal('196.00')  # 9.8%
    health_insurance = Decimal('64.00')  # 3.2%
    other_deductions = Decimal('40.00')
    
    total_deductions = taxes + social_security + health_insurance + other_deductions
    expected_net = gross_salary - total_deductions
    
    # Create payroll record
    payroll = await crud.create_payroll_record(db, schemas.PayrollRecordCreate(
        user_id=test_user.id,
        month=sofia_now().month,
        year=sofia_now().year,
        gross_salary=gross_salary,
        net_salary=expected_net,
        taxes=taxes,
        social_security=social_security,
        health_insurance=health_insurance,
        other_deductions=other_deductions,
        status='calculated'
    ))
    
    # Validate data consistency
    validation_result = await crud.validate_payroll_consistency(db, payroll.id)
    
    assert validation_result.is_valid, "Payroll данните трябва да са консистентни"
    assert validation_result.gross_minus_deductions_equals_net, \
        "Брутната заплата минус удръжките трябва да е равна на нетната"
    assert validation_result.no_negative_values, "Не трябва да има отрицателни стойности"
    assert validation_result.decimal_precision_correct, \
        "Десетичната точност трябва да е правилна"


@pytest.mark.asyncio
async def test_financial_record_immutability_after_approval(db: AsyncSession, test_user):
    """Тест за неизменност на финансови записи след одобрение"""
    
    # Create and approve payroll record
    payroll = await crud.create_payroll_record(db, schemas.PayrollRecordCreate(
        user_id=test_user.id,
        month=sofia_now().month,
        year=sofia_now().year,
        gross_salary=Decimal('1500.00'),
        net_salary=Decimal('1200.00'),
        status='pending'
    ))
    
    # Approve the record
    approved_payroll = await crud.update_payroll_status(db, payroll.id, 'approved')
    assert approved_payroll.status == 'approved', "Записът трябва да е одобрен"
    
    # Try to modify approved record (should fail)
    with pytest.raises(Exception) as exc_info:
        await crud.update_payroll_record(db, payroll.id, schemas.PayrollRecordUpdate(
            gross_salary=Decimal('2000.00')
        ))
    
    assert "approved" in str(exc_info.value).lower() or "immutable" in str(exc_info.value).lower(), \
        "Одобрените финансови записи трябва да са неизменни"
    
    # Try to delete approved record (should fail)
    with pytest.raises(Exception) as exc_info:
        await crud.delete_payroll_record(db, payroll.id)
    
    assert "approved" in str(exc_info.value).lower() or "immutable" in str(exc_info.value).lower(), \
        "Одобрените финансови записи не могат да се изтриват"


@pytest.mark.asyncio
async def test_backup_restore_integrity(db: AsyncSession, test_user):
    """Тест за цялостност на backup/restore операциите"""
    
    # Create comprehensive test data
    # 1. Payroll records
    payroll_records = []
    for month in range(1, 4):
        payroll = await crud.create_payroll_record(db, schemas.PayrollRecordCreate(
            user_id=test_user.id,
            month=month,
            year=2024,
            gross_salary=Decimal(f'{1500 + month * 100}.00'),
            net_salary=Decimal(f'{1200 + month * 80}.00'),
            status='approved' if month < 3 else 'calculated'
        ))
        payroll_records.append(payroll)
    
    # 2. Time logs
    time_logs = []
    for day in range(1, 29):  # One month
        work_date = sofia_now().replace(day=day, hour=9, minute=0, second=0)
        if work_date.month == sofia_now().month:
            time_log = await crud.create_time_log(db, schemas.TimeLogCreate(
                user_id=test_user.id,
                start_time=work_date,
                end_time=work_date.replace(hour=17),
                type='work',
                notes=f'Day {day}'
            ))
            time_logs.append(time_log)
    
    # Create backup
    backup_data = await crud.create_system_backup(db, schemas.BackupCreate(
        description='Test backup before integrity check',
        include_payroll=True,
        include_time_logs=True,
        include_users=True
    ))
    
    # Verify backup creation
    assert backup_data.id is not None, "Backup трябва да бъде създаден"
    assert backup_data.status == 'completed', "Backup трябва да бъде завършен"
    assert backup_data.file_size > 0, "Backup файлът трябва да има размер"
    
    # Verify backup integrity
    backup_integrity = await crud.verify_backup_integrity(db, backup_data.id)
    assert backup_integrity.is_valid, "Backup трябва да е валиден"
    assert backup_integrity.record_counts['payroll_records'] == len(payroll_records), \
        "Брой payroll записи трябва да съвпада"
    assert backup_integrity.record_counts['time_logs'] == len(time_logs), \
        "Брой time logs трябва да съвпада"
    
    # Test restore process (simulation)
    restore_result = await crud.simulate_restore_from_backup(db, backup_data.id)
    assert restore_result.can_restore, "Трябва да е възможно restore"
    assert restore_result.expected_records['payroll_records'] == len(payroll_records), \
        "Restore трябва да възстанови правилния брой записи"


@pytest.mark.asyncio
async def test_audit_log_data_preservation(db: AsyncSession, test_user):
    """Тест за запазване на пълни данни в audit логовете"""
    
    # Create multiple operations to test audit logging
    operations = []
    
    # 1. Create user (if possible)
    # 2. Create payroll record
    payroll = await crud.create_payroll_record(db, schemas.PayrollRecordCreate(
        user_id=test_user.id,
        month=sofia_now().month,
        year=sofia_now().year,
        gross_salary=Decimal('1800.00'),
        net_salary=Decimal('1440.00'),
        taxes=Decimal('180.00'),
        social_security=Decimal('176.40'),
        health_insurance=Decimal('57.60'),
        other_deductions=Decimal('0.00'),
        status='calculated'
    ))
    operations.append(('create', 'payroll', payroll.id))
    
    # 3. Update payroll record
    updated_payroll = await crud.update_payroll_record(db, payroll.id, schemas.PayrollRecordUpdate(
        gross_salary=Decimal('1900.00')
    ))
    operations.append(('update', 'payroll', payroll.id))
    
    # 4. Change status
    status_updated = await crud.update_payroll_status(db, payroll.id, 'pending_approval')
    operations.append(('status_change', 'payroll', payroll.id))
    
    # Verify audit logs for all operations
    audit_logs = await crud.get_audit_logs(db, user_id=test_user.id)
    
    for operation_type, entity_type, entity_id in operations:
        matching_logs = [
            log for log in audit_logs 
            if entity_type in log.action and 
               log.details and 
               (str(entity_id) in str(log.details) or 
                (isinstance(log.details, dict) and log.details.get('record_id') == entity_id))
        ]
        
        assert len(matching_logs) > 0, f"Трябва да има audit лог за {operation_type} на {entity_type}"
        
        # Check log completeness
        log = matching_logs[0]
        assert log.user_id == test_user.id, "User ID трябва да е запазено"
        assert log.action is not None, "Действието трябва да е запазено"
        assert log.timestamp is not None, "Timestamp трябва да е запазен"
        assert log.details is not None, "Детайлите трябва да са запазени"
        
        # Verify data preservation in details
        if isinstance(log.details, str):
            try:
                details_dict = json.loads(log.details)
            except json.JSONDecodeError:
                details_dict = {}
        else:
            details_dict = log.details
        
        assert len(details_dict) > 0, "Детайлите трябва да съдържат информация"
        assert 'before' in details_dict or 'after' in details_dict or 'data' in details_dict, \
            "Трябва да има данни за преди/след или текущите данни"


@pytest.mark.asyncio
async def test_concurrent_financial_operations_integrity(db: AsyncSession, test_user):
    """Тест за интегритет при едновременни финансови операции"""
    
    import asyncio
    
    # Create concurrent payroll calculations for the same user/period
    async def calculate_payroll_concurrently(user_id: int, month: int, year: int):
        """Simulate concurrent payroll calculation"""
        try:
            # Simulate complex calculation
            await asyncio.sleep(0.1)  # Simulate processing time
            
            return await crud.calculate_monthly_payroll(db, user_id, year, month)
        except Exception as e:
            return {'error': str(e)}
    
    # Start multiple concurrent calculations
    tasks = [
        calculate_payroll_concurrently(test_user.id, sofia_now().month, sofia_now().year)
        for _ in range(5)
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Verify consistency - should either all succeed or all fail gracefully
    successful_results = [r for r in results if not isinstance(r, Exception) and 'error' not in r]
    failed_results = [r for r in results if isinstance(r, Exception) or 'error' in r]
    
    # Should not have mixed success/failure for same operation
    assert len(successful_results) == 0 or len(failed_results) == 0, \
        "Еднакви операции не трябва да имат смесени резултати при concurrency"
    
    # If successful, all should be consistent
    if successful_results:
        first_result = successful_results[0]
        for result in successful_results[1:]:
            assert result.gross_salary == first_result.gross_salary, \
                "Резултатите трябва да са консистентни"
            assert result.net_salary == first_result.net_salary, \
                "Резултатите трябва да са консистентни"


@pytest.mark.asyncio
async def test_financial_data_cascade_operations_integrity(db: AsyncSession, test_user):
    """Тест за интегритет при cascade операции на финансови данни"""
    
    # Create payroll with associated records
    payroll = await crud.create_payroll_record(db, schemas.PayrollRecordCreate(
        user_id=test_user.id,
        month=sofia_now().month,
        year=sofia_now().year,
        gross_salary=Decimal('1500.00'),
        net_salary=Decimal('1200.00'),
        status='calculated'
    ))
    
    # Create associated payroll details
    details = await crud.create_payroll_details(db, schemas.PayrollDetailsCreate(
        payroll_id=payroll.id,
        normal_hours=160,
        overtime_hours=8,
        bonus=Decimal('100.00'),
        deductions_breakdown={
            'tax': Decimal('150.00'),
            'social_security': Decimal('147.00'),
            'health_insurance': Decimal('48.00'),
            'other': Decimal('55.00')
        }
    ))
    
    # Verify cascade delete doesn't break integrity (if delete is allowed)
    # This test depends on business rules - some systems allow cascade delete,
    # others use soft delete for financial records
    
    # For now, test that related operations are properly tracked
    related_operations = await crud.get_related_financial_operations(db, payroll.id)
    assert len(related_operations) >= 1, "Трябва да има свързани финансови операции"
    
    # Verify audit trail includes cascade operations
    audit_logs = await crud.get_audit_logs(db, user_id=test_user.id)
    payroll_related_logs = [
        log for log in audit_logs 
        if 'payroll' in log.action.lower()
    ]
    
    assert len(payroll_related_logs) >= 2, \
        "Трябва да има audit логове за payroll и свързаните с него операции"


@pytest.mark.asyncio
async def test_data_migration_integrity(db: AsyncSession, test_user):
    """Тест за интегритет при data migration операции"""
    
    # Create test data for migration
    original_data = {
        'user_id': test_user.id,
        'payroll_records': [],
        'time_logs': []
    }
    
    # Create payroll records
    for month in range(1, 4):
        payroll = await crud.create_payroll_record(db, schemas.PayrollRecordCreate(
            user_id=test_user.id,
            month=month,
            year=2024,
            gross_salary=Decimal(f'{1400 + month * 50}.00'),
            net_salary=Decimal(f'{1100 + month * 40}.00'),
            status='approved'
        ))
        original_data['payroll_records'].append(payroll)
    
    # Simulate migration process
    migration_result = await crud.simulate_data_migration(
        db, 
        user_id=test_user.id,
        target_version='2.0',
        dry_run=True  # Only simulate
    )
    
    assert migration_result.is_successful, "Migration симулацията трябва да е успешна"
    assert migration_result.records_to_migrate > 0, "Трябва да има записи за миграция"
    assert migration_result.data_integrity_check_passed, \
        "Data integrity check трябва да премине"
    
    # Verify that original data is unchanged after simulation
    current_payroll_records = await crud.get_user_payroll_records(db, test_user.id, 2024)
    assert len(current_payroll_records) == len(original_data['payroll_records']), \
        "Оригиналните данни не трябва да се променят при dry run"


@pytest.fixture
def audit_trail_requirements():
    """Fixture за audit trail изисквания"""
    return AUDIT_TRAIL_REQUIREMENTS


@pytest.fixture
def data_integrity_rules():
    """Fixture за data integrity правила"""
    return DATA_INTEGRITY_RULES