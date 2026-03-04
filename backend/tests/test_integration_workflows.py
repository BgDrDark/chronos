"""
Integration tests for complete workflows
End-to-end тестове за пълни работни процеси
"""

import pytest
from decimal import Decimal
from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch, AsyncMock

from backend import crud, schemas
from backend.database.models import sofia_now


# Integration workflow scenarios
INTEGRATION_SCENARIOS = {
    'complete_payroll_cycle': {
        'steps': [
            'create_user',
            'set_payroll_config', 
            'log_regular_hours',
            'log_overtime',
            'calculate_payroll',
            'approve_payroll',
            'generate_payslip'
        ]
    },
    'leave_request_workflow': {
        'steps': [
            'create_user',
            'set_payroll_config',
            'log_regular_hours',
            'request_leave',
            'approve_leave',
            'calculate_adjusted_payroll'
        ]
    },
    'shift_swap_workflow': {
        'steps': [
            'create_user',
            'create_schedule',
            'request_shift_swap',
            'approve_swap',
            'log_hours_after_swap',
            'calculate_payroll_with_swap'
        ]
    }
}


@pytest.mark.asyncio
async def test_complete_payroll_cycle(db: AsyncSession, test_user):
    """End-to-end тест: Time tracking → Payroll calculation → Payslip generation"""
    
    # Step 1: Create payroll configuration
    payroll_config = await crud.create_payroll_config(db, schemas.PayrollConfigCreate(
        user_id=test_user.id,
        base_salary=Decimal('1500.00'),
        hourly_rate=Decimal('9.30'),
        overtime_multiplier_150=Decimal('1.5'),
        overtime_multiplier_200=Decimal('2.0'),
        working_days_per_month=22,
        working_hours_per_day=8
    ))
    
    assert payroll_config.id is not None, "Payroll config трябва да бъде създаден"
    
    # Step 2: Log regular working hours for a month
    current_date = sofia_now().date()
    first_day_of_month = current_date.replace(day=1)
    
    regular_hours_logged = 0
    for day in range(1, 29):  # Simulate one month
        work_date = first_day_of_month.replace(day=day)
        if work_date.weekday() < 5:  # Monday to Friday
            start_time = sofia_now().replace(
                year=work_date.year,
                month=work_date.month,
                day=work_date.day,
                hour=9,
                minute=0,
                second=0
            )
            end_time = start_time.replace(hour=17)
            
            await crud.create_time_log(db, schemas.TimeLogCreate(
                user_id=test_user.id,
                start_time=start_time,
                end_time=end_time,
                type='work',
                notes=f'Regular work day {day}'
            ))
            regular_hours_logged += 8
    
    # Step 3: Log overtime hours
    overtime_day = first_day_of_month.replace(day=15)
    overtime_start = sofia_now().replace(
        year=overtime_day.year,
        month=overtime_day.month,
        day=overtime_day.day,
        hour=17,
        minute=0,
        second=0
    )
    overtime_end = overtime_start + timedelta(hours=3)  # 3 hours overtime
    
    await crud.create_time_log(db, schemas.TimeLogCreate(
        user_id=test_user.id,
        start_time=overtime_start,
        end_time=overtime_end,
        type='work',
        notes='Overtime work'
    ))
    
    # Step 4: Calculate monthly payroll
    payroll_calculation = await crud.calculate_monthly_payroll(
        db, test_user.id, current_date.year, current_date.month
    )
    
    assert payroll_calculation.user_id == test_user.id, "Payroll трябва да е за правилния потребител"
    assert payroll_calculation.normal_hours == regular_hours_logged, "Регулярните часове трябва да съвпадат"
    assert payroll_calculation.overtime_hours == 3, "Извънредните часове трябва да са 3"
    
    expected_overtime_pay = Decimal('9.30') * Decimal('1.5') * Decimal('3')
    assert abs(payroll_calculation.overtime_pay - expected_overtime_pay) < Decimal('0.01'), \
        "Надничният плат трябва да е правилно изчислен"
    
    # Step 5: Create payroll record
    payroll_record = await crud.create_payroll_record(db, schemas.PayrollRecordCreate(
        user_id=test_user.id,
        month=current_date.month,
        year=current_date.year,
        gross_salary=payroll_calculation.gross_salary,
        net_salary=payroll_calculation.net_salary,
        taxes=payroll_calculation.taxes,
        social_security=payroll_calculation.social_security,
        health_insurance=payroll_calculation.health_insurance,
        normal_hours=payroll_calculation.normal_hours,
        overtime_hours=payroll_calculation.overtime_hours,
        overtime_pay=payroll_calculation.overtime_pay,
        status='calculated'
    ))
    
    assert payroll_record.id is not None, "Payroll запис трябва да бъде създаден"
    assert payroll_record.status == 'calculated', "Статусът трябва да е 'calculated'"
    
    # Step 6: Approve payroll
    approved_payroll = await crud.update_payroll_status(db, payroll_record.id, 'approved')
    assert approved_payroll.status == 'approved', "Payroll трябва да бъде одобрен"
    
    # Step 7: Generate payslip
    payslip = await crud.generate_payslip(db, schemas.PayslipCreate(
        payroll_id=payroll_record.id,
        template_type='standard',
        include_details=True
    ))
    
    assert payslip.id is not None, "Payslip трябва да бъде генериран"
    assert payslip.payroll_id == payroll_record.id, "Payslip трябва да е свързан с payroll"
    
    # Verify audit trail for complete workflow
    audit_logs = await crud.get_audit_logs(db, user_id=test_user.id)
    workflow_actions = [
        'payroll_config_created',
        'time_log_created',
        'payroll_calculated',
        'payroll_record_created',
        'payroll_status_updated',
        'payslip_generated'
    ]
    
    for action in workflow_actions:
        matching_logs = [log for log in audit_logs if action in log.action]
        assert len(matching_logs) > 0, f"Трябва да има audit лог за {action}"


@pytest.mark.asyncio
async def test_leave_request_financial_impact(db: AsyncSession, test_user):
    """Тест за влияние на отпуски върху заплати"""
    
    # Step 1: Setup payroll configuration
    payroll_config = await crud.create_payroll_config(db, schemas.PayrollConfigCreate(
        user_id=test_user.id,
        base_salary=Decimal('1500.00'),
        hourly_rate=Decimal('9.30'),
        working_days_per_month=22,
        working_hours_per_day=8
    ))
    
    # Step 2: Log regular hours for part of month (before leave)
    current_date = sofia_now().date()
    first_day = current_date.replace(day=1)
    
    # Log 10 working days before leave
    for day in range(1, 15):
        work_date = first_day.replace(day=day)
        if work_date.weekday() < 5:  # Monday to Friday
            start_time = sofia_now().replace(
                year=work_date.year,
                month=work_date.month,
                day=work_date.day,
                hour=9,
                minute=0
            )
            end_time = start_time.replace(hour=17)
            
            await crud.create_time_log(db, schemas.TimeLogCreate(
                user_id=test_user.id,
                start_time=start_time,
                end_time=end_time,
                type='work',
                notes=f'Work day {day}'
            ))
    
    # Step 3: Request and approve paid leave
    leave_start = first_day.replace(day=15)
    leave_end = first_day.replace(day=19)  # 5 days leave
    
    leave_request = await crud.create_leave_request(db, schemas.LeaveRequestCreate(
        user_id=test_user.id,
        type='paid_leave',
        start_date=leave_start,
        end_date=leave_end,
        reason='Annual vacation',
        status='pending'
    ))
    
    # Approve the leave
    approved_leave = await crud.update_leave_status(db, leave_request.id, 'approved')
    assert approved_leave.status == 'approved', "Отпускът трябва да бъде одобрен"
    
    # Step 4: Calculate payroll with leave
    payroll_calculation = await crud.calculate_monthly_payroll(
        db, test_user.id, current_date.year, current_date.month
    )
    
    # Step 5: Verify financial impact
    expected_working_days = 22 - 5  # 22 total - 5 leave days = 17 working days
    expected_regular_hours = expected_working_days * 8  # 136 hours
    
    assert payroll_calculation.normal_hours == expected_regular_hours, \
        f"Регулярните часове трябва да са {expected_regular_hours} (с отнета отпуска)"
    
    # Paid leave should not reduce base salary but should be reflected correctly
    assert payroll_calculation.base_salary == Decimal('1500.00'), \
        "Базовата заплата не трябва да се променя при платен отпуск"
    
    # Verify leave days are tracked
    leave_days = await crud.get_approved_leave_days(db, test_user.id, current_date.year, current_date.month)
    assert leave_days == 5, "Трябва да има 5 дни отпуск"
    
    # Step 6: Generate payroll record
    payroll_with_leave = await crud.create_payroll_record(db, schemas.PayrollRecordCreate(
        user_id=test_user.id,
        month=current_date.month,
        year=current_date.year,
        gross_salary=payroll_calculation.gross_salary,
        net_salary=payroll_calculation.net_salary,
        normal_hours=payroll_calculation.normal_hours,
        leave_days=5,
        status='calculated'
    ))
    
    assert payroll_with_leave.leave_days == 5, "Payroll записът трябва да отразява отпуск дните"


@pytest.mark.asyncio
async def test_shift_swap_financial_impact(db: AsyncSession, test_user):
    """Тест за финансови последици от смяна на смени"""
    
    # Step 1: Create work schedule
    current_date = sofia_now().date()
    week_start = current_date - timedelta(days=current_date.weekday())
    
    # Original schedule: Monday-Friday 9-17
    for day in range(5):
        schedule_date = week_start + timedelta(days=day)
        await crud.create_work_schedule(db, schemas.WorkScheduleCreate(
            user_id=test_user.id,
            date=schedule_date,
            start_time=sofia_now().replace(
                year=schedule_date.year,
                month=schedule_date.month,
                day=schedule_date.day,
                hour=9,
                minute=0
            ),
            end_time=sofia_now().replace(
                year=schedule_date.year,
                month=schedule_date.month,
                day=schedule_date.day,
                hour=17,
                minute=0
            ),
            shift_type='regular'
        ))
    
    # Step 2: Request shift swap for Wednesday
    wednesday = week_start + timedelta(days=2)
    swap_request = await crud.create_shift_swap_request(db, schemas.ShiftSwapRequestCreate(
        user_id=test_user.id,
        original_date=wednesday,
        original_start=sofia_now().replace(
            year=wednesday.year,
            month=wednesday.month,
            day=wednesday.day,
            hour=9,
            minute=0
        ),
        original_end=sofia_now().replace(
            year=wednesday.year,
            month=wednesday.month,
            day=wednesday.day,
            hour=17,
            minute=0
        ),
        requested_date=wednesday,
        requested_start=sofia_now().replace(
            year=wednesday.year,
            month=wednesday.month,
            day=wednesday.day,
            hour=14,
            minute=0
        ),
        requested_end=sofia_now().replace(
            year=wednesday.year,
            month=wednesday.month,
            day=wednesday.day,
            hour=22,
            minute=0
        ),
        reason='Personal appointment'
    ))
    
    assert swap_request.id is not None, "Swap заявката трябва да бъде създадена"
    assert swap_request.status == 'pending', "Статусът трябва да е 'pending'"
    
    # Step 3: Approve shift swap
    approved_swap = await crud.update_shift_swap_status(db, swap_request.id, 'approved')
    assert approved_swap.status == 'approved', "Swap заявката трябва да бъде одобрена"
    
    # Step 4: Log time according to swapped schedule
    swapped_start = sofia_now().replace(
        year=wednesday.year,
        month=wednesday.month,
        day=wednesday.day,
        hour=14,
        minute=0
    )
    swapped_end = swapped_start.replace(hour=22)
    
    await crud.create_time_log(db, schemas.TimeLogCreate(
        user_id=test_user.id,
        start_time=swapped_start,
        end_time=swapped_end,
        type='work',
        notes='Swapped shift - 14:00-22:00'
    ))
    
    # Log regular hours for other days
    for day in range(5):
        if day != 2:  # Skip Wednesday (swapped day)
            work_date = week_start + timedelta(days=day)
            if work_date <= sofia_now().date():  # Only log past/present days
                start_time = sofia_now().replace(
                    year=work_date.year,
                    month=work_date.month,
                    day=work_date.day,
                    hour=9,
                    minute=0
                )
                end_time = start_time.replace(hour=17)
                
                await crud.create_time_log(db, schemas.TimeLogCreate(
                    user_id=test_user.id,
                    start_time=start_time,
                    end_time=end_time,
                    type='work',
                    notes=f'Regular work day'
                ))
    
    # Step 5: Calculate payroll with swap
    payroll_calculation = await crud.calculate_monthly_payroll(
        db, test_user.id, current_date.year, current_date.month
    )
    
    # Step 6: Verify financial calculations
    # Swapped shift: 8 hours total (4 regular hours + 4 evening hours)
    # Evening hours might have different rate based on company policy
    assert payroll_calculation.normal_hours == 40, "Общите часове трябва да са 40 за седмицата"
    
    # Check if swap is properly recorded
    swap_logs = await crud.get_shift_swap_logs(db, test_user.id, wednesday, wednesday)
    assert len(swap_logs) > 0, "Трябва да има логове за swap"
    
    # Step 7: Create payroll record
    payroll_with_swap = await crud.create_payroll_record(db, schemas.PayrollRecordCreate(
        user_id=test_user.id,
        month=current_date.month,
        year=current_date.year,
        gross_salary=payroll_calculation.gross_salary,
        net_salary=payroll_calculation.net_salary,
        normal_hours=payroll_calculation.normal_hours,
        status='calculated',
        notes='Includes approved shift swap'
    ))
    
    # Verify audit trail includes swap workflow
    audit_logs = await crud.get_audit_logs(db, user_id=test_user.id)
    swap_actions = [log for log in audit_logs if 'shift_swap' in log.action]
    assert len(swap_actions) >= 2, "Трябва да има audit логове за swap създаване и одобрение"


@pytest.mark.asyncio
async def test_concurrent_user_workflow_isolation(db: AsyncSession):
    """Тест за изолация на workflows при едновременно използване"""
    
    import asyncio
    
    # Create two test users
    user1_data = schemas.UserCreate(
        email="user1@test.com",
        firstName="User1",
        lastName="Test",
        password="password123",
        roleId=2  # Employee role
    )
    
    user2_data = schemas.UserCreate(
        email="user2@test.com", 
        firstName="User2",
        lastName="Test",
        password="password123",
        roleId=2  # Employee role
    )
    
    user1 = await crud.create_user(db, user1_data)
    user2 = await crud.create_user(db, user2_data)
    
    # Define concurrent workflow for each user
    async def user_workflow(user: schemas.User, delay: float = 0.1):
        """Complete payroll workflow for a user"""
        await asyncio.sleep(delay)  # Simulate processing time
        
        # Create payroll config
        config = await crud.create_payroll_config(db, schemas.PayrollConfigCreate(
            user_id=user.id,
            base_salary=Decimal('1500.00'),
            hourly_rate=Decimal('9.30'),
            working_days_per_month=22,
            working_hours_per_day=8
        ))
        
        # Log some hours
        work_date = sofia_now().replace(hour=9, minute=0)
        await crud.create_time_log(db, schemas.TimeLogCreate(
            user_id=user.id,
            start_time=work_date,
            end_time=work_date.replace(hour=17),
            type='work'
        ))
        
        # Calculate payroll
        calculation = await crud.calculate_monthly_payroll(
            db, user.id, sofia_now().year, sofia_now().month
        )
        
        return {
            'user_id': user.id,
            'config_id': config.id,
            'normal_hours': calculation.normal_hours,
            'gross_salary': calculation.gross_salary
        }
    
    # Run concurrent workflows
    tasks = [
        user_workflow(user1, 0.1),
        user_workflow(user2, 0.15)
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Verify both workflows completed successfully
    assert len(results) == 2, "Два workflows трябва да завършат"
    
    user1_result = results[0]
    user2_result = results[1]
    
    assert not isinstance(user1_result, Exception), "User1 workflow трябва да успее"
    assert not isinstance(user2_result, Exception), "User2 workflow трябва да успее"
    
    assert user1_result['user_id'] == user1.id, "User1 резултатът трябва да е за user1"
    assert user2_result['user_id'] == user2.id, "User2 резултатът трябва да е за user2"
    
    # Verify data isolation - users shouldn't interfere
    user1_logs = await crud.get_time_logs_by_user(db, user1.id)
    user2_logs = await crud.get_time_logs_by_user(db, user2.id)
    
    assert len(user1_logs) > 0, "User1 трябва да има time logs"
    assert len(user2_logs) > 0, "User2 трябва да има time logs"
    assert len(user1_logs) != len(user2_logs) or user1_logs[0].user_id != user2_logs[0].user_id, \
        "Time logs трябва да са изолирани между потребителите"


@pytest.mark.asyncio
async def test_error_recovery_and_rollback(db: AsyncSession, test_user):
    """Тест за възстановяване от грешки и rollback на операции"""
    
    # Step 1: Create initial payroll config
    config = await crud.create_payroll_config(db, schemas.PayrollConfigCreate(
        user_id=test_user.id,
        base_salary=Decimal('1500.00'),
        hourly_rate=Decimal('9.30'),
        working_days_per_month=22,
        working_hours_per_day=8
    ))
    
    # Step 2: Log some work hours
    work_date = sofia_now().replace(hour=9, minute=0)
    await crud.create_time_log(db, schemas.TimeLogCreate(
        user_id=test_user.id,
        start_time=work_date,
        end_time=work_date.replace(hour=17),
        type='work'
    ))
    
    # Step 3: Calculate initial payroll
    initial_calculation = await crud.calculate_monthly_payroll(
        db, test_user.id, sofia_now().year, sofia_now().month
    )
    
    initial_gross = initial_calculation.gross_salary
    
    # Step 4: Create payroll record
    payroll_record = await crud.create_payroll_record(db, schemas.PayrollRecordCreate(
        user_id=test_user.id,
        month=sofia_now().month,
        year=sofia_now().year,
        gross_salary=initial_gross,
        net_salary=initial_calculation.net_salary,
        status='calculated'
    ))
    
    # Step 5: Simulate error during approval process
    # Try to modify an already calculated field (should fail)
    with pytest.raises(Exception) as exc_info:
        await crud.update_payroll_record(db, payroll_record.id, schemas.PayrollRecordUpdate(
            gross_salary=Decimal('99999.99')  # Invalid large amount
        ))
    
    # Step 6: Verify system recovered correctly
    # The original record should be unchanged
    unchanged_record = await crud.get_payroll_record(db, payroll_record.id)
    assert unchanged_record.gross_salary == initial_gross, \
        "Original payroll record should be unchanged after failed update"
    
    # Step 7: Continue with normal workflow (approve and generate payslip)
    approved_record = await crud.update_payroll_status(db, payroll_record.id, 'approved')
    assert approved_record.status == 'approved', "Payroll should still be approvable after error"
    
    # Step 8: Generate payslip
    payslip = await crud.generate_payslip(db, schemas.PayslipCreate(
        payroll_id=payroll_record.id
    ))
    
    assert payslip.id is not None, "Payslip should be generated successfully"
    
    # Step 9: Verify audit trail includes both successful and failed operations
    audit_logs = await crud.get_audit_logs(db, user_id=test_user.id)
    
    successful_actions = [log for log in audit_logs if not log.details or 'error' not in log.details.lower()]
    error_actions = [log for log in audit_logs if log.details and 'error' in log.details.lower()]
    
    assert len(successful_actions) > 0, "Should have successful operations"
    assert len(error_actions) > 0, "Should have error operations logged"
    
    # Verify system consistency after error recovery
    final_record = await crud.get_payroll_record(db, payroll_record.id)
    assert final_record.status == 'approved', "Final state should be consistent"


@pytest.fixture
def integration_scenarios():
    """Fixture за integration workflow сценарии"""
    return INTEGRATION_SCENARIOS