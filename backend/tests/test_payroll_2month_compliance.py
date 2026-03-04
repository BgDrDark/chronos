"""
Payroll compliance tests for 2-MONTH WORKING PERIOD
Тестове за финансови изчисления при 2 месеца работа според Българския Кодекс на труда
"""

import pytest
from decimal import Decimal
from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch, AsyncMock

from backend import crud, schemas
from backend.database.models import sofia_now
from backend.crud import BULGARIAN_LABOR_CONSTANTS


# Test scenarios for 2-month working period
TWO_MONTH_WORK_SCENARIOS = {
    'fulltime_employee': {
        'base_salary': Decimal('1600.00'),  # 1600 лв за 2 месеца
        'expected_regular_hours': 176,  # 8 * 22 работни дни
        'expected_overtime_hours_150': 18,  # 1+1+2+1+2+1+2+1+2 = 9 часа през 4 седмици
        'expected_overtime_hours_200': 0,
        'expected_weekend_hours': 0,
        'expected_overtime_pay_150': Decimal('243.75'),  # 18 * 13.5 лв/час * 1.5
        'expected_total_overtime_pay': Decimal('243.75'),
        'expected_regular_pay': Decimal('1760.00'),  # 176 * 10 лв/час
        'expected_weekend_pay': Decimal('0.00'),
        'expected_base_plus_overtime': Decimal('1843.75'),  # 1600 + 243.75
    },
    'minimum_wage_employee': {
        'base_salary': BULGARIAN_LABOR_CONSTANTS['minimum_wage_2024'] * 2,  # 1420 лв за 2 месеца
        'hourly_rate': Decimal('8.06'),  # 1420 / 176
        'expected_regular_hours': 176,
        'expected_overtime_hours_150': 10,
        'expected_overtime_hours_200': 0,
        'expected_weekend_hours': 0,
        'expected_overtime_pay_150': Decimal('60.45'),  # 10 * 8.06 * 1.5
        'expected_total_overtime_pay': Decimal('60.45'),
        'expected_regular_pay': Decimal('1418.56'),  # 176 * 8.06
        'expected_weekend_pay': Decimal('0.00'),
        'expected_base_plus_overtime': Decimal('1480.45')  # 1420 + 60.45
    }
}


@pytest.fixture
async def test_user_2_months(test_db: AsyncSession):
    """Create a test user for 2-month payroll tests"""
    user_data = schemas.UserCreate(
        email="testuser_2months@example.com",
        firstName="Test",
        lastName="User",
        password="testpassword123",
        roleId=2  # Employee role
    )
    
    # Check if user already exists
    existing_user = await crud.get_user_by_email(test_db, user_data.email)
    if existing_user:
        return existing_user
    
    # Create user
    user = await crud.create_user(test_db, user_data, role_name="user")
    return user


@pytest.mark.asyncio
async def test_2_month_fulltime_work(test_db: AsyncSession, test_user_2_months):
    """Тест за 2 месеца пълноценно време - Bulgarian Labor Law compliant"""
    
    scenario = TWO_MONTH_WORK_SCENARIOS['fulltime_employee']
    
    # Create payroll configuration
    payroll_config = await crud.create_payroll_config(test_db, schemas.PayrollConfigCreate(
        user_id=test_user_2_months.id,
        base_salary=scenario['base_salary'],
        hourly_rate=scenario['hourly_rate'],
        overtime_multiplier_150=BULGARIAN_LABOR_CONSTANTS['overtime_multiplier_150'],
        overtime_multiplier_200=BULGARIAN_LABOR_CONSTANTS['overtime_multiplier_200'],
        working_days_per_month=BULGARIAN_LABOR_CONSTANTS['working_days_per_month'],
        working_hours_per_day=BULGARIAN_LABOR_CONSTANTS['maximum_daily_hours']
    ))
    
    # Create 2 months of compliant work logs
    await crud.create_time_log_2_month_batch(test_db, test_user_2_months.id)
    
    # Calculate payroll for first month
    current_date = sofia_now().date()
    first_month = current_date.month - 1 if current_date.month > 1 else 12
    first_year = current_date.year if current_date.month > 1 else current_date.year - 1
    
    payroll_first_month = await crud.calculate_monthly_payroll(
        test_db,
        test_user_2_months.id,
        first_year,
        first_month
    )
    
    # Verify first month calculations
    assert payroll_first_month.normal_hours == scenario['expected_regular_hours'], \
        f"First month regular hours should be {scenario['expected_regular_hours']}, got {payroll_first_month.normal_hours}"
    
    assert payroll_first_month.overtime_hours == scenario['expected_overtime_hours_150'], \
        f"First month overtime hours should be {scenario['expected_overtime_hours_150']}, got {payroll_first_month.overtime_hours}"
    
    assert abs(payroll_first_month.overtime_pay - scenario['expected_overtime_pay_150_percent']) < Decimal('0.01'), \
        f"First month overtime pay should be {scenario['expected_overtime_pay_150_percent']}, got {payroll_first_month.overtime_pay}"
    
    # Calculate payroll for current month
    payroll_current_month = await crud.calculate_monthly_payroll(
        test_db,
        test_user_2_months.id,
        current_date.year,
        current_date.month
    )
    
    # Verify second month calculations
    assert payroll_current_month.normal_hours == scenario['expected_regular_hours'], \
        f"Second month regular hours should be {scenario['expected_regular_hours']}, got {payroll_current_month.normal_hours}"
    
    assert payroll_current_month.overtime_hours == scenario['expected_overtime_hours_150'], \
        f"Second month overtime hours should be {scenario['expected_overtime_hours_150']}, got {payroll_current_month.overtime_hours}"
    
    assert abs(payroll_current_month.overtime_pay - scenario['expected_overtime_pay_150_percent']) < Decimal('0.01'), \
        f"Second month overtime pay should be {scenario['expected_overtime_pay_150_percent']}, got {payroll_current_month.overtime_pay}"
    
    # Verify 2-month totals
    total_regular_hours = payroll_first_month.normal_hours + payroll_current_month.normal_hours
    total_overtime_hours = payroll_first_month.overtime_hours + payroll_current_month.overtime_hours
    total_overtime_pay = payroll_first_month.overtime_pay + payroll_current_month.overtime_pay
    total_base_plus_overtime = payroll_first_month.gross_salary + payroll_current_month.gross_salary
    
    expected_total_regular_hours = scenario['expected_regular_hours'] * 2
    expected_total_overtime_hours = scenario['expected_overtime_hours_150'] * 2
    expected_total_base_plus_overtime = scenario['expected_base_plus_overtime'] * 2
    
    assert total_regular_hours == expected_total_regular_hours, \
        f"2-month regular hours should be {expected_total_regular_hours}, got {total_regular_hours}"
    
    assert total_overtime_hours == expected_total_overtime_hours, \
        f"2-month overtime hours should be {expected_total_overtime_hours}, got {total_overtime_hours}"
    
    assert abs(total_overtime_pay - scenario['expected_total_overtime_pay']) < Decimal('0.01'), \
        f"2-month overtime pay should be {scenario['expected_total_overtime_pay']}, got {total_overtime_pay}"
    
    print(f"✅ 2-MONTH FULLTIME TEST PASSED: {total_base_plus_overtime} лв бруза 2 месеца")


@pytest.mark.asyncio
async def test_minimum_wage_2_months(test_db: AsyncSession, test_user_2_months):
    """Тест за минимална заплата при 2 месеца работа"""
    
    scenario = TWO_MONTH_WORK_SCENARIOS['minimum_wage_employee']
    
    # Create payroll configuration with minimum wage rate
    payroll_config = await crud.create_payroll_config(test_db, schemas.PayrollConfigCreate(
        user_id=test_user_2_months.id,
        base_salary=scenario['base_salary'],
        hourly_rate=scenario['hourly_rate'],
        overtime_multiplier_150=BULGARIAN_LABOR_CONSTANTS['overtime_multiplier_150'],
        overtime_multiplier_200=BULGARIAN_LABOR_CONSTANTS['overtime_multiplier_200'],
        working_days_per_month=BULGARIAN_LABOR_CONSTANTS['working_days_per_month'],
        working_hours_per_day=BULGARIAN_LABOR_CONSTANTS['maximum_daily_hours']
    ))
    
    # Verify hourly rate meets minimum wage requirements for 2 months
    minimum_hourly_rate = (scenario['base_salary'] / 2) / BULGARIAN_LABOR_CONSTANTS['working_days_per_month'] / BULGARIAN_LABOR_CONSTANTS['standard_hours_per_month']
    assert float(payroll_config.hourly_rate) >= float(minimum_hourly_rate), \
        f"Hourly rate should be >= {minimum_hourly_rate}, got {payroll_config.hourly_rate}"
    
    # Create 2 months of compliant work logs
    await crud.create_time_log_2_month_batch(test_db, test_user_2_months.id)
    
    # Calculate payroll
    payroll_total = await crud.calculate_monthly_payroll(
        test_db,
        test_user_2_months.id,
        current_date.year,
        current_date.month
    )
    
    # Verify compliance with minimum wage over 2 months
    total_base_salary = scenario['base_salary']
    total_gross_salary = payroll_total.gross_salary
    
    assert total_gross_salary >= total_base_salary, \
        f"2-month gross salary should be >= minimum wage: {total_base_salary}, got {total_gross_salary}"
    
    # Verify overtime calculations
    assert payroll_total.overtime_hours > 0, \
        "Should have overtime hours for 2-month period"
    
    assert payroll_total.overtime_pay > Decimal('0'), \
        "Should have overtime pay for 2-month period"
    
    print(f"✅ 2-MONTH MINIMUM WAGE TEST PASSED: {total_gross_salary} лв")


@pytest.mark.asyncio
async def test_bulgarian_labor_law_compliance(test_db: AsyncSession, test_user_2_months):
    """Тест за съответствие с Българския Кодекс на труда при 2 месеца работа"""
    
    # Test 1: Maximum daily hours (8 hours/day)
    daily_logs = await crud.get_time_logs_by_user(test_db, test_user_2_months.id)
    
    # Get work logs by date to check daily limits
    unique_dates = set()
    daily_violations = []
    
    for log in daily_logs:
        work_date = log.start_time.date()
        if work_date not in unique_dates:
            unique_dates.add(work_date)
            
            # Calculate hours for this date
            date_logs = await crud.get_time_logs_by_user_and_date(test_db, test_user_2_months.id, work_date)
            total_daily_hours = sum(
                (log.end_time - log.start_time).total_seconds() / 3600 
                for log in date_logs
            )
            
            if total_daily_hours > BULGARIAN_LABOR_CONSTANTS['maximum_daily_hours']:
                daily_violations.append({
                    'date': work_date,
                    'total_hours': total_daily_hours,
                    'limit': BULGARIAN_LABOR_CONSTANTS['maximum_daily_hours']
                })
    
    assert len(daily_violations) == 0, \
        f"Should have no daily hour violations. Violations: {[v['date'] for v in daily_violations]}"
    
    # Test 2: Maximum weekly hours (40 hours/week)
    week_start = sofia_now().date() - timedelta(days=sofia_now().date().weekday())
    weekly_hours = 0
    
    # Calculate weekly hours from 2 months of work logs
    for i in range(8):  # 8 weeks = 2 months
        current_week_start = week_start + timedelta(weeks=i)
        week_end = current_week_start + timedelta(days=6)
        
        week_logs = await crud.get_time_logs_by_user(
            test_db, test_user_2_months.id,
            start_date=current_week_start,
            end_date=week_end
        )
        
        week_hours += sum(
            (log.end_time - log.start_time).total_seconds() / 3600 
            for log in week_logs
            if log.type == 'work'
        )
    
    assert weekly_hours <= BULGARIAN_LABOR_CONSTANTS['maximum_weekly_hours'] * 2, \
        f"Should not exceed weekly limit: {weekly_hours} <= {BULGARIAN_LABOR_CONSTANTS['maximum_weekly_hours'] * 2}"
    
    # Test 3: Minimum wage compliance
    payroll_total = await crud.calculate_monthly_payroll(
        test_db,
        test_user_2_months.id,
        sofia_now().year,
        sofia_now().month
    )
    
    # Check if hourly rate meets minimum wage
    expected_minimum_hourly_rate = BULGARIAN_LABOR_CONSTANTS['minimum_wage_2024'] / BULGARIAN_LABOR_CONSTANTS['working_days_per_month'] / BULGARIAN_LABOR_CONSTANTS['standard_hours_per_month']
    actual_hourly_rate = (await crud.get_payroll_config(test_db, test_user_2_months.id)).hourly_rate
    
    assert actual_hourly_rate >= expected_minimum_hourly_rate, \
        f"Hourly rate should be >= {expected_minimum_hourly_rate}, got {actual_hourly_rate_rate}"
    
    # Check if gross salary meets minimum wage requirement
    minimum_2_month_wage = BULGARIAN_LABOR_CONSTANTS['minimum_wage_2024'] * 2
    assert payroll_total.gross_salary >= minimum_2_month_wage, \
        f"2-month gross salary should be >= {minimum_2_month_wage}, got {payroll_total.gross_salary}"
    
    print(f"✅ BULGARIAN LABOR LAW COMPLIANCE TEST PASSED")


@pytest.mark.asyncio
async def test_overtime_multipliers(test_db: AsyncSession, test_user_2_months):
    """Тест за правилните over-time мултиплиери (150% и 200%)"""
    
    # Create test scenario with both weekday and weekend overtime
    test_date = sofia_now().date()
    
    # Weekday overtime (9 AM - 6 PM = 9 hours, 1 hour overtime)
    weekday_start = sofia_now().replace(
        year=test_date.year, month=test_date.month, day=test_date.day,
        hour=9, minute=0, second=0
    )
    weekday_end = weekday_start.replace(hour=18, minute=0, second=0)  # 9 regular + 1 overtime
    
    await crud.create_time_log(test_db, schemas.TimeLogCreate(
        user_id=test_user_2_months.id,
        start_time=weekday_start,
        end_time=weekday_end,
        type='work',
        notes='Weekday work with 1 hour overtime'
    ))
    
    # Weekend overtime (10 AM - 5 PM = 5 hours, always 200% rate)
    saturday = test_date + timedelta(days=(5 - test_date.weekday()) % 7)
    
    weekend_start = sofia_now().replace(
        year=saturday.year, month=saturday.month, day=saturday.day,
        hour=10, minute=0, second=0
    )
    weekend_end = weekend_start.replace(hour=17, minute=0, second=0)
    
    await crud.create_time_log(test_db, schemas.TimeLogCreate(
        user_id=test_user_2_months.id,
        start_time=weekend_start,
        end_time=weekend_end,
        type='work',
        notes='Weekend work - always 200% rate'
    ))
    
    # Calculate payroll for this day
    payroll_single_day = await crud.calculate_monthly_payroll(
        test_db,
        test_user_2_months.id,
        test_date.year,
        test_date.month
    )
    
    # Verify overtime calculations
    expected_weekday_overtime = Decimal('13.59')  # 1 * 9.059 * 1.5
    expected_weekend_overtime = Decimal('50.90')  # 5 * 10.18 * 2.0
    
    # The implementation should properly categorize and calculate
    assert payroll_single_day.overtime_pay > Decimal('0'), \
        "Should have overtime pay for mixed overtime scenario"
    
    assert (payroll_single_day.weekend_holiday_pay > Decimal('0')) and \
           (abs(payroll_single_day.weekend_holiday_pay - expected_weekend_overtime) < Decimal('0.01')), \
        "Weekend overtime should be properly calculated at 200% rate"
    
    print(f"✅ OVERTIME MULTIPLIERS TEST PASSED: {payroll_single_day.overtime_pay + payroll_single_day.weekend_holiday_pay}")


@pytest.mark.asyncio
async def test_detailed_payroll_calculation_breakdown(test_db: RESTful):
    """Детайлен тест на payroll изчисления за 2 месеца"""
    
    # Calculate payroll
    payroll_total = await crud.calculate_monthly_payroll(
        test_db,
        test_user_2_months.id,
        sofia_now().year,
        sofia_now().month
    )
    
    # Verify all components are properly calculated
    assert payroll_total.gross_salary > Decimal('0'), "Gross salary should be positive"
    assert payroll_total.net_salary > Decimal('0'), "Net salary should be positive"
    assert payroll_total.deductions > Decimal('0'), "Deductions should be positive"
    
    # Verify calculation transparency
    regular_pay = payroll_total.gross_salary - (total_overtime_pay + payroll_total.weekend_holiday_pay + payroll_total.bonus)
    calculated_net = regular_pay - Decimal('0.10') * regular_pay - Decimal('0.098') * regular_pay - Decimal('0.032') * regular_pay
    
    assert abs(payroll_total.net_salary - calculated_net - payroll_total.deductions) < Decimal('0.01'), \
        "Net salary calculation should be accurate"
    
    # Create payroll record for audit trail
    payroll_record = await crud.create_payroll_record(test_db, schemas.PayrollRecordCreate(
        user_id=test_user_2_months.id,
        month=sofia_now().month,
        year=sofia_now().year,
        gross_salary=payroll_total.gross_salary,
        net_salary=payroll_total.net_salary,
        taxes=Decimal(str(float(payroll_total.taxes)),
        social_security=Decimal(str(float(payroll_total.social_security)),
        health_insurance=Decimal(str(float(payroll_total.health_insurance)),
        status='calculated'
    ))
    
    # Verify audit trail was created
    audit_logs = await crud.get_audit_logs(test_db, test_user_2_months.id)
    payroll_logs = [log for log in audit_logs if 'payroll' in log.action]
    
    assert len(payroll_logs) >= 1, "Should have audit logs for payroll operations"
    
    print(f"✅ DETAILED PAYROLL BREAKDOWN TEST PASSED")
    print(f"  📊 Gross Salary: {payroll_total.gross_salary}")
    print(f"  💰 Net Salary: {payroll_total.net_salary}")
    print(f"  🏛️ Deductions: {payroll_total.deductions}")
    print(f"  ⏰ Regular Hours: {payroll_total.normal_hours}")
    print(f"  🔥 Overtime Hours: {payroll_total.overtime_hours}")
    print(f"  📅 Weekend Hours: {payroll_total.weekend_holiday_pay > 0}")
    print(f"  💰 Total Overtime Pay: {payroll_total.overtime_pay}")


@pytest.fixture
def payroll_test_data():
    """Fixture за payroll test scenarios"""
    return TWO_MONTH_WORK_SCENARIOS


@pytest.fixture
def bulgarian_labor_constants():
    """Fixture за Bulgarian Labor Law constants"""
    return BULGARIAN_LABOR_CONSTANTS