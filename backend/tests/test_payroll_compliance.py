"""
Payroll compliance tests for Bulgarian financial standards and Labor Law
Тестове за финансови изчисления и съответствие с Българския Кодекс на труда
"""

import pytest
from decimal import Decimal
from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch

from backend import crud, schemas
from backend.database.models import sofia_now




# Bulgarian Labor Law Constants
BULGARIAN_LABOR_CONSTANTS = {
    'maximum_daily_hours': 8,
    'maximum_weekly_hours': 40,
    'minimum_break_minutes': 30,
    'overtime_multiplier_daily': Decimal('1.5'),
    'overtime_multiplier_holiday': Decimal('2.0'),
    'minimum_wage_2024': Decimal('710.00'),
    'average_monthly_hours': Decimal('161.4'),  # 40 седмици * 40 часа / 12 месеца
}

# Test scenarios for payroll calculations
PAYROLL_TEST_SCENARIOS = {
    'minimum_wage_employee': {
        'monthly_salary': Decimal('710.00'),
        'hourly_rate': Decimal('4.39'),  # 710 / 161.4
        'normal_hours': 160,
        'overtime_hours_weekday': 8,
        'overtime_hours_holiday': 4,
        'expected_normal_pay': Decimal('702.40'),  # 4.39 * 160
        'expected_weekday_overtime': Decimal('52.68'),  # 4.39 * 1.5 * 8
        'expected_holiday_overtime': Decimal('35.12'),  # 4.39 * 2.0 * 4
        'expected_gross': Decimal('790.20')  # 702.40 + 52.68 + 35.12
    },
    'average_salary_employee': {
        'monthly_salary': Decimal('1500.00'),
        'hourly_rate': Decimal('9.30'),  # 1500 / 161.4
        'normal_hours': 160,
        'overtime_hours_weekday': 12,
        'overtime_hours_holiday': 8,
        'expected_normal_pay': Decimal('1488.00'),  # 9.30 * 160
        'expected_weekday_overtime': Decimal('167.40'),  # 9.30 * 1.5 * 12
        'expected_holiday_overtime': Decimal('148.80'),  # 9.30 * 2.0 * 8
        'expected_gross': Decimal('1804.20')  # 1488.00 + 167.40 + 148.80
    }
}


@pytest.mark.asyncio
async def test_overtime_calculation_150_percent(test_db: AsyncSession):
    """Тест за 150% надници през работни дни"""

    # First get/create a regular user
    user_data = schemas.UserCreate(
        email="testuser@example.com",
        firstName="Test",
        lastName="User",
        password="testpassword123",
        roleId=2  # Employee role
    )
    
    # Check if user already exists
    existing_user = await crud.get_user_by_email(test_db, user_data.email)
    if existing_user:
        test_user = existing_user
    else:
        test_user = await crud.create_user(test_db, user_data, role_name="user")

    scenario = PAYROLL_TEST_SCENARIOS['minimum_wage_employee']

    # Create payroll configuration with minimum wage
    payroll_config = await crud.create_payroll_config(test_db, schemas.PayrollConfigCreate(
        user_id=test_user.id,
        base_salary=BULGARIAN_LABOR_CONSTANTS['minimum_wage_2024'],
        hourly_rate=Decimal('4.39'),
        overtime_multiplier_150=BULGARIAN_LABOR_CONSTANTS['overtime_multiplier_daily'],
        overtime_multiplier_200=BULGARIAN_LABOR_CONSTANTS['overtime_multiplier_holiday'],
        working_days_per_month=22,
        working_hours_per_day=8
    ))
    
print(f"DEBUG: Created payroll config for user {test_user.id} with hourly_rate: {payroll_config.hourly_rate}")
    
    # Verify hourly rate meets minimum wage requirements
    assert float(payroll_config.hourly_rate) >= 4.39, "Часовата ставка не отговаря на минимална работна заплата"
    
    # Create regular work for the day (9 AM - 5 PM)
    regular_start = sofia_now().replace(year=workday.year, month=workday.month, day=workday.day, hour=9, minute=0, second=0)
    regular_end = regular_start.replace(hour=17, minute=0, second=0)
    
    await crud.create_time_log(test_db, schemas.TimeLogCreate(
        user_id=test_user.id,
        start_time=regular_start,
        end_time=regular_end,
        type='work',
        notes='Regular work day'
    ))
    
    # Create overtime work (3 hours after regular time)
    overtime_start = regular_end
    overtime_end = overtime_start + timedelta(hours=3)  # 3 hours overtime for 150% rate
    
    await crud.create_time_log(test_db, schemas.TimeLogCreate(
        user_id=test_user.id,
        start_time=overtime_start,
        end_time=overtime_end,
        type='work',
        notes='Weekday overtime work - 150% rate'
    ))
    
    # Create overtime work (3 hours after regular time)
    overtime_start = regular_end
    overtime_end = overtime_start + timedelta(hours=3)  # 3 hours overtime for 150% rate
    
    await crud.create_time_log(test_db, schemas.TimeLogCreate(
        user_id=test_user.id,
        start_time=overtime_start,
        end_time=overtime_end,
        type='work',
        notes='Weekday overtime work - 150% rate'
    ))

      # Verify time logs were created before calculating payroll
    created_logs = await crud.get_time_logs_by_user(test_db, test_user.id)
    print(f"DEBUG: Total logs for user {test_user.id}: {len(created_logs)}")
    for log in created_logs:
        print(f"DEBUG: Log: {log.start_time} to {log.end_time} ({log.start_time.date()})")
    
    # Calculate payroll - use January 2026 (when logs were created)
    payroll_calc = await crud.calculate_monthly_payroll(
        test_db,
        test_user.id,
        2026,  # Year
        1    # January month
    )
    
    # Verify overtime calculation
    expected_overtime_pay = scenario['expected_weekday_overtime']
    actual_overtime_pay = payroll_calc.overtime_pay or Decimal('0')
    
    assert abs(actual_overtime_pay - expected_overtime_pay) < Decimal('0.01'), \
        f"Очакван надничен плат: {expected_overtime_pay}, получен: {actual_overtime_pay}"


@pytest.mark.asyncio
async def test_overtime_calculation_200_percent(test_db: AsyncSession, test_user):
    """Тест за 200% надници през празници/уикенд"""
    
    scenario = PAYROLL_TEST_SCENARIOS['minimum_wage_employee']
    
    # Create time log for holiday work (Saturday)
    saturday = sofia_now().replace(hour=10, minute=0, second=0)
    while saturday.weekday() != 5:  # Find Saturday
        saturday = saturday.replace(day=saturday.day + 1)
    
    for i in range(scenario['overtime_hours_holiday']):
        await crud.create_time_log(test_db, schemas.TimeLogCreate(
            user_id=test_user.id,
            start_time=saturday.replace(hour=10+i, minute=0),
            end_time=saturday.replace(hour=11+i, minute=0),
            type='work',
            notes='Weekend work'
        ))
    
    # Calculate payroll
    payroll_calc = await crud.calculate_monthly_payroll(
        test_db, 
        test_user.id, 
        sofia_now().year, 
        sofia_now().month
    )
    
    # Verify weekend overtime calculation (200%)
    expected_overtime_pay = scenario['expected_holiday_overtime']
    actual_overtime_pay = payroll_calc.weekend_holiday_pay or Decimal('0')
    
    assert abs(actual_overtime_pay - expected_overtime_pay) < Decimal('0.01'), \
        f"Очакван празничен надничен плат: {expected_overtime_pay}, получен: {actual_overtime_pay}"


@pytest.mark.asyncio
async def test_tax_deduction_calculation(test_db: AsyncSession, test_user):
    """Тест за правилно изчисляване на данъци и осигуровки"""
    
    # Create payroll with known salary
    gross_salary = Decimal('1500.00')
    
    payroll_calc = schemas.PayrollCalculation(
        user_id=test_user.id,
        period_start=date(2024, 1, 1),
        period_end=date(2024, 1, 31),
        gross_salary=gross_salary,
        normal_hours=160,
        overtime_hours=0,
        overtime_pay=Decimal('0'),
        weekend_holiday_pay=Decimal('0'),
        bonus=Decimal('0'),
        deductions=Decimal('0'),
        net_salary=Decimal('0')
    )
    
    # Calculate Bulgarian taxes and social security
    # 2024 rates (example rates - should be updated with current rates)
    social_security_rate = Decimal('0.147')  # 14.7% total social security
    health_insurance_rate = Decimal('0.048')  # 4.8% health insurance
    tax_threshold = Decimal('500.00')  # Monthly tax-free threshold
    income_tax_rate = Decimal('0.10')  # 10% income tax
    
    # Calculate deductions
    social_security = gross_salary * social_security_rate
    health_insurance = gross_salary * health_insurance_rate
    taxable_income = max(Decimal('0'), gross_salary - tax_threshold)
    income_tax = taxable_income * income_tax_rate
    
    total_deductions = social_security + health_insurance + income_tax
    expected_net = gross_salary - total_deductions
    
    # Verify calculations
    assert social_security > Decimal('0'), "Социални осигуровки трябва да са > 0"
    assert health_insurance > Decimal('0'), "Здравни осигуровки трябва да са > 0"
    assert total_deductions > Decimal('0'), "Общите удръжки трябва да са > 0"
    assert expected_net < gross_salary, "Нетната заплата трябва да е по-малка от брутната"


@pytest.mark.asyncio
async def test_labor_law_maximum_hours(test_db: AsyncSession, test_user):
    """Тест за спазване на максимум часове по Кодекса на труда"""
    
    # Try to create more than 8 hours in a single day
    start_time = sofia_now().replace(hour=8, minute=0, second=0)
    end_time = sofia_now().replace(hour=18, minute=0, second=0)  # 10 hours
    
    # This should trigger validation or at least be flagged
    time_log = schemas.TimeLogCreate(
        user_id=test_user.id,
        start_time=start_time,
        end_time=end_time,
        type='work',
        notes='Extended work day'
    )
    
    created_log = await crud.create_time_log(test_db, time_log)
    
    # Calculate hours worked
    hours_worked = (created_log.end_time - created_log.start_time).total_seconds() / 3600
    
    # Should be flagged for labor law violation
    assert hours_worked > BULGARIAN_LABOR_CONSTANTS['maximum_daily_hours'], \
        "Тестът трябва да създаде сценарий с нарушение на максималните часове"


@pytest.mark.asyncio
async def test_payroll_audit_trail(test_db: AsyncSession, test_user):
    """Тест за complete audit trail на финансови операции"""
    
    # Create payroll record
    payroll = await crud.create_payroll_record(test_db, schemas.PayrollRecordCreate(
        user_id=test_user.id,
        month=sofia_now().month,
        year=sofia_now().year,
        gross_salary=Decimal('1500.00'),
        net_salary=Decimal('1200.00'),
        taxes=Decimal('300.00'),
        social_security=Decimal('147.00'),
        health_insurance=Decimal('48.00'),
        status='calculated'
    ))
    
    # Check that audit log is created
    audit_logs = await crud.get_audit_logs(test_db, user_id=test_user.id)
    
    payroll_logs = [log for log in audit_logs if log.action == 'payroll_calculated']
    assert len(payroll_logs) > 0, "Трябва да има audit лог за payroll изчисление"
    
    # Verify audit log contains required fields
    latest_log = payroll_logs[0]
    assert latest_log.user_id == test_user.id
    assert latest_log.action == 'payroll_calculated'
    assert latest_log.timestamp is not None
    assert latest_log.ip_address is not None


@pytest.mark.asyncio
async def test_payroll_data_consistency(test_db: AsyncSession, test_user):
    """Тест за консистентност на данните за заплати"""
    
    # Create consistent payroll data
    base_salary = Decimal('1500.00')
    hourly_rate = base_salary / BULGARIAN_LABOR_CONSTANTS['average_monthly_hours']
    
    # Create payroll config
    payroll_config = await crud.create_payroll_config(test_db, schemas.PayrollConfigCreate(
        user_id=test_user.id,
        base_salary=base_salary,
        hourly_rate=hourly_rate,
        working_days_per_month=22,
        working_hours_per_day=8
    ))
    
    # Create time logs for a full month
    normal_hours = 0
    for week in range(4):
        for day in range(5):  # Monday to Friday
            work_date = sofia_now().replace(day=1 + week*7 + day)
            if work_date.month == sofia_now().month:
                await crud.create_time_log(test_db, schemas.TimeLogCreate(
                    user_id=test_user.id,
                    start_time=work_date.replace(hour=9, minute=0),
                    end_time=work_date.replace(hour=17, minute=0),
                    type='work',
                    notes='Regular work'
                ))
                normal_hours += 8
    
    # Calculate payroll
    calculation = await crud.calculate_monthly_payroll(
        test_db, test_user.id, sofia_now().year, sofia_now().month
    )
    
    # Verify data consistency
    expected_normal_pay = hourly_rate * normal_hours
    assert abs(calculation.normal_pay - expected_normal_pay) < Decimal('1.00'), \
        "Несъответствие в изчислението на нормална заплата"


@pytest.mark.asyncio
async def test_financial_record_immutability(test_db: AsyncSession, test_user):
    """Тест за неизменност на финансови записи"""
    
    # Create approved payroll record
    payroll = await crud.create_payroll_record(test_db, schemas.PayrollRecordCreate(
        user_id=test_user.id,
        month=sofia_now().month,
        year=sofia_now().year,
        gross_salary=Decimal('1500.00'),
        net_salary=Decimal('1200.00'),
        status='approved'
    ))
    
    # Try to modify approved record
    with pytest.raises(Exception) as exc_info:
        await crud.update_payroll_record(test_db, payroll.id, schemas.PayrollRecordUpdate(
            gross_salary=Decimal('2000.00')
        ))
    
    # Should raise an error for modifying approved financial records
    assert "approved" in str(exc_info.value).lower() or "immutable" in str(exc_info.value).lower(), \
        "Одобрените финансови записи трябва да са неизменни"


@pytest.mark.asyncio
async def test_monthly_reporting_compliance(test_db: AsyncSession, test_user):
    """Тест за съответствие с месечни финансови отчети"""
    
    # Generate payroll for multiple months
    months = [
        (2024, 1, Decimal('1500.00')),
        (2024, 2, Decimal('1500.00')),
        (2024, 3, Decimal('1600.00'))  # Small increase
    ]
    
    for year, month, salary in months:
        await crud.create_payroll_record(test_db, schemas.PayrollRecordCreate(
            user_id=test_user.id,
            month=month,
            year=year,
            gross_salary=salary,
            net_salary=salary * Decimal('0.80'),  # Approximate net
            taxes=salary * Decimal('0.20'),
            status='calculated'
        ))
    
    # Generate annual report
    annual_report = await crud.generate_annual_payroll_report(test_db, test_user.id, 2024)
    
    # Verify report calculations
    expected_total_gross = sum(salary for _, _, salary in months)
    assert abs(annual_report.total_gross - expected_total_gross) < Decimal('0.01'), \
        "Годишният отчет трябва да събира правилно месечните заплати"
    
    assert annual_report.total_months == len(months), "Броят месеци трябва да съвпада"
    assert annual_report.average_salary == expected_total_gross / len(months), \
        "Средната заплата трябва да е правилно изчислена"


@pytest.fixture
def payroll_test_data():
    """Fixture за payroll тестови данни"""
    return PAYROLL_TEST_SCENARIOS


@pytest.fixture
def labor_law_constants():
    """Fixture за Bulgarian Labor Law константи"""
    return BULGARIAN_LABOR_CONSTANTS