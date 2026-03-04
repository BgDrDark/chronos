"""
Time tracking compliance tests for Bulgarian Labor Law
Тестове за отчитане на работно време и съответствие с Кодекса на труда
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta, date
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch, AsyncMock

from backend import crud, schemas
from backend.database.models import sofia_now, ShiftType


# Bulgarian Labor Law working time regulations
BULGARIAN_WORK_TIME_REGULATIONS = {
    'maximum_daily_hours': 8,
    'maximum_weekly_hours': 40,
    'minimum_break_minutes': 30,  # след 6 часа работа
    'minimum_rest_between_shifts_hours': 11,
    'night_hours_start': 22,  # 22:00
    'night_hours_end': 6,    # 06:00
    'workable_days_per_week': 5,
    'maximum_overtime_per_year': 150,  # часове
    'night_shift_minimum_rest': 7,  # часове
}

# Test scenarios for time tracking
TIME_TRACKING_SCENARIOS = {
    'regular_schedule': {
        'start_hour': 9,
        'end_hour': 17,
        'total_hours': 8,
        'break_required': False,
        'compliant': True
    },
    'extended_schedule': {
        'start_hour': 8,
        'end_hour': 18,
        'total_hours': 10,
        'break_required': True,
        'compliant': False,  # Exceeds 8 hours
    },
    'night_shift': {
        'start_hour': 22,
        'end_hour': 6,
        'total_hours': 8,
        'break_required': False,
        'compliant': True,
        'is_night_shift': True
    },
    'overtime_schedule': {
        'start_hour': 9,
        'end_hour': 20,
        'total_hours': 11,
        'break_required': True,
        'compliant': False,  # Exceeds maximum
        'overtime_hours': 3
    }
}


@pytest.mark.asyncio
async def test_maximum_daily_hours_enforcement(db: AsyncSession, test_user):
    """Тест за спазване на максимум 8 часа работа на ден"""
    
    # Create time log exceeding 8 hours
    start_time = sofia_now().replace(hour=8, minute=0, second=0)
    end_time = sofia_now().replace(hour=18, minute=0, second=0)  # 10 hours
    
    time_log = await crud.create_time_log(db, schemas.TimeLogCreate(
        user_id=test_user.id,
        start_time=start_time,
        end_time=end_time,
        type='work',
        notes='Extended work day - should be flagged'
    ))
    
    # Calculate total hours
    total_hours = (time_log.end_time - time_log.start_time).total_seconds() / 3600
    
    # Check if violation is detected
    assert total_hours > BULGARIAN_WORK_TIME_REGULATIONS['maximum_daily_hours'], \
        "Тестът трябва да симулира нарушаване на максималните дневни часове"
    
    # Check if system flags the violation
    time_logs = await crud.get_time_logs_by_user_and_date(db, test_user.id, start_time.date())
    assert len(time_logs) > 0, "Трябва да има time log за деня"
    
    # System should have a way to flag violations
    # This could be through a separate compliance check function
    violations = await crud.check_daily_hours_violations(db, test_user.id, start_time.date())
    assert len(violations) > 0, "Системата трябва да засече нарушението"


@pytest.mark.asyncio
async def test_weekly_hours_limit_enforcement(db: AsyncSession, test_user):
    """Тест за спазване на максимум 40 часа работа седмично"""
    
    # Create time logs for the entire week
    current_date = sofia_now().date()
    start_of_week = current_date - timedelta(days=current_date.weekday())
    
    total_hours = 0
    
    # Create 5 days of 9 hours each (45 hours total)
    for i in range(5):
        work_date = start_of_week + timedelta(days=i)
        start_time = sofia_now().replace(
            year=work_date.year,
            month=work_date.month,
            day=work_date.day,
            hour=8,
            minute=0,
            second=0
        )
        end_time = start_time + timedelta(hours=9)
        
        await crud.create_time_log(db, schemas.TimeLogCreate(
            user_id=test_user.id,
            start_time=start_time,
            end_time=end_time,
            type='work',
            notes=f'Day {i+1} - 9 hours'
        ))
        
        total_hours += 9
    
    # Check weekly compliance
    weekly_total = await crud.get_weekly_work_hours(db, test_user.id, start_of_week)
    
    assert weekly_total > BULGARIAN_WORK_TIME_REGULATIONS['maximum_weekly_hours'], \
        "Тестът трябва да симулира надвишаване на седмичните часове"
    
    # System should flag weekly violations
    violations = await crud.check_weekly_hours_violations(db, test_user.id, start_of_week)
    assert len(violations) > 0, "Системата трябва да засече седмичното нарушение"


@pytest.mark.asyncio
async def test_break_time_enforcement(db: AsyncSession, test_user):
    """Тест за задължителна 30 минутна почивка след 6 часа работа"""
    
    # Create 7-hour work day without break (should be flagged)
    start_time = sofia_now().replace(hour=9, minute=0, second=0)
    end_time = sofia_now().replace(hour=16, minute=0, second=0)
    
    await crud.create_time_log(db, schemas.TimeLogCreate(
        user_id=test_user.id,
        start_time=start_time,
        end_time=end_time,
        type='work',
        notes='7 hours without break - should be flagged'
    ))
    
    # Check break requirements
    daily_summary = await crud.get_daily_work_summary(db, test_user.id, start_time.date())
    total_work_time = daily_summary.total_hours
    
    if total_work_time > 6:
        # Should require break
        break_violations = await crud.check_break_violations(db, test_user.id, start_time.date())
        assert len(break_violations) > 0, \
            "Системата трябва да изисква почивка след 6 часа работа"


@pytest.mark.asyncio
async def test_minimum_rest_between_shifts(db: AsyncSession, test_user):
    """Тест за минимум 11 часа почивка между смени"""
    
    # Create late shift ending at 23:00
    day1 = sofia_now().replace(hour=15, minute=0, second=0)
    end_day1 = day1.replace(hour=23, minute=0, second=0)
    
    await crud.create_time_log(db, schemas.TimeLogCreate(
        user_id=test_user.id,
        start_time=day1,
        end_time=end_day1,
        type='work',
        notes='Late shift'
    ))
    
    # Create early next shift starting at 06:00 (only 7 hours rest)
    day2_start = end_day1.replace(hour=6, minute=0, second=0) + timedelta(days=1)
    day2_end = day2_start + timedelta(hours=8)
    
    await crud.create_time_log(db, schemas.TimeLogCreate(
        user_id=test_user.id,
        start_time=day2_start,
        end_time=day2_end,
        type='work',
        notes='Early shift - insufficient rest'
    ))
    
    # Check rest period violation
    rest_violations = await crud.check_rest_period_violations(
        db, test_user.id, day1.date(), day2_start.date()
    )
    assert len(rest_violations) > 0, \
        "Системата трябва да засече недостатъчната почивка между смени"


@pytest.mark.asyncio
async def test_night_shift_regulations(db: AsyncSession, test_user):
    """Тест за регулации на нощен труд"""
    
    # Create night shift (22:00 - 06:00)
    start_time = sofia_now().replace(hour=22, minute=0, second=0)
    end_time = start_time + timedelta(hours=8)
    
    night_log = await crud.create_time_log(db, schemas.TimeLogCreate(
        user_id=test_user.id,
        start_time=start_time,
        end_time=end_time,
        type='work',
        notes='Night shift'
    ))
    
    # Check if shift is correctly identified as night work
    is_night_shift = await crud.is_night_shift(db, night_log.id)
    assert is_night_shift, "Смената трябва да бъде идентифицирана като нощна"
    
    # Check night shift compliance
    night_violations = await crud.check_night_shift_compliance(db, test_user.id, start_time.date())
    # Night shifts have different regulations - this test verifies proper detection


@pytest.mark.asyncio
async def test_overtime_calculation_rules(db: AsyncSession, test_user):
    """Тест за правилно изчисляване на извънреден труд"""
    
    # Create regular work day (8 hours)
    regular_start = sofia_now().replace(hour=9, minute=0, second=0)
    regular_end = regular_start + timedelta(hours=8)
    
    await crud.create_time_log(db, schemas.TimeLogCreate(
        user_id=test_user.id,
        start_time=regular_start,
        end_time=regular_end,
        type='work',
        notes='Regular hours'
    ))
    
    # Create overtime work (2 hours)
    overtime_start = regular_end
    overtime_end = overtime_start + timedelta(hours=2)
    
    await crud.create_time_log(db, schemas.TimeLogCreate(
        user_id=test_user.id,
        start_time=overtime_start,
        end_time=overtime_end,
        type='work',
        notes='Overtime work'
    ))
    
    # Calculate daily summary
    daily_summary = await crud.get_daily_work_summary(db, test_user.id, regular_start.date())
    
    assert daily_summary.regular_hours == 8, "Регулярните часове трябва да са 8"
    assert daily_summary.overtime_hours == 2, "Извънредните часове трябва да са 2"
    assert daily_summary.total_hours == 10, "Общите часове трябва да са 10"


@pytest.mark.asyncio
async def test_weekend_overtime_rules(db: AsyncSession, test_user):
    """Тест за надници през уикенди/празници"""
    
    # Find Saturday
    current_date = sofia_now().date()
    saturday = current_date + timedelta(days=(5 - current_date.weekday()) % 7)
    
    # Create work on Saturday (should be 200% rate)
    saturday_start = sofia_now().replace(
        year=saturday.year,
        month=saturday.month,
        day=saturday.day,
        hour=10,
        minute=0,
        second=0
    )
    saturday_end = saturday_start + timedelta(hours=4)
    
    await crud.create_time_log(db, schemas.TimeLogCreate(
        user_id=test_user.id,
        start_time=saturday_start,
        end_time=saturday_end,
        type='work',
        notes='Weekend work - 200% rate'
    ))
    
    # Check overtime classification
    daily_summary = await crud.get_daily_work_summary(db, test_user.id, saturday)
    
    assert daily_summary.weekend_hours == 4, "Уикенд часовете трябва да са 4"
    assert daily_summary.is_weekend_work, "Работата трябва да бъде маркирана като уикенд"


@pytest.mark.asyncio
async def test_time_rounding_policies(db: AsyncSession, test_user):
    """Тест за правилно закръгляне на работно време"""
    
    # Create time log with irregular times (should be rounded)
    start_time = sofia_now().replace(hour=8, minute=47, second=23)  # 8:47:23
    end_time = sofia_now().replace(hour=17, minute=12, second=45)   # 17:12:45
    
    await crud.create_time_log(db, schemas.TimeLogCreate(
        user_id=test_user.id,
        start_time=start_time,
        end_time=end_time,
        type='work',
        notes='Irregular times for rounding test'
    ))
    
    # Get rounded calculation
    rounded_summary = await crud.get_rounded_daily_summary(db, test_user.id, start_time.date())
    
    # Verify rounding policy (e.g., round to nearest 15 minutes)
    expected_start_rounded = start_time.replace(minute=45, second=0)  # 8:45
    expected_end_rounded = end_time.replace(minute=15, second=0)    # 17:15
    
    assert rounded_summary.start_time == expected_start_rounded, \
        "Началният час трябва да бъде закръглен до 8:45"
    assert rounded_summary.end_time == expected_end_rounded, \
        "Крайният час трябва да бъде закръглен до 17:15"


@pytest.mark.asyncio
async def test_geolocation_boundary_enforcement(db: AsyncSession, test_user, test_company):
    """Тест за геолокационни ограничения за маркране на присъствие"""
    
    # Create workplace location
    workplace_location = await crud.create_workplace_location(db, schemas.WorkplaceLocationCreate(
        company_id=test_company.id,
        name="Main Office",
        address="Sofia, Bulgaria",
        latitude=42.6977,
        longitude=23.3219,
        radius_meters=100  # 100 meters radius
    ))
    
    # Test within allowed radius (should be approved)
    valid_location = schemas.GeolocationCheck(
        latitude=42.6977,
        longitude=23.3219,
        accuracy=10.0
    )
    
    is_within_radius = await crud.check_geolocation_compliance(
        db, workplace_location.id, valid_location
    )
    assert is_within_radius, "Локацията в радиуса трябва да бъде одобрена"
    
    # Test outside allowed radius (should be rejected)
    invalid_location = schemas.GeolocationCheck(
        latitude=42.7000,  # ~250 meters away
        longitude=23.3200,
        accuracy=10.0
    )
    
    is_outside_radius = await crud.check_geolocation_compliance(
        db, workplace_location.id, invalid_location
    )
    assert not is_outside_radius, "Локацията извън радиуса трябва да бъде отхвърлена"


@pytest.mark.asyncio
async def test_shift_overlap_prevention(db: AsyncSession, test_user):
    """Тест за предотвратяване на застъпващи се смени"""
    
    # Create first shift
    shift1_start = sofia_now().replace(hour=9, minute=0, second=0)
    shift1_end = shift1_start + timedelta(hours=8)
    
    await crud.create_time_log(db, schemas.TimeLogCreate(
        user_id=test_user.id,
        start_time=shift1_start,
        end_time=shift1_end,
        type='work',
        notes='First shift'
    ))
    
    # Try to create overlapping shift (should be prevented)
    overlap_start = shift1_start + timedelta(hours=6)  # Overlaps with first shift
    overlap_end = overlap_start + timedelta(hours=4)
    
    # This should raise an exception or be rejected
    with pytest.raises(Exception) as exc_info:
        await crud.create_time_log(db, schemas.TimeLogCreate(
            user_id=test_user.id,
            start_time=overlap_start,
            end_time=overlap_end,
            type='work',
            notes='Overlapping shift'
        ))
    
    assert "overlap" in str(exc_info.value).lower() or "conflict" in str(exc_info.value).lower(), \
        "Застъпващите се смени трябва да бъдат предотвратени"


@pytest.mark.asyncio
async def test_annual_overtime_limit(db: AsyncSession, test_user):
    """Тест за годишен лимит на извънреден труд (150 часа)"""
    
    # Simulate overtime throughout the year
    current_year = sofia_now().year
    
    # Create overtime throughout different months (exceeding annual limit)
    overtime_per_month = 15  # 15 hours per month × 12 months = 180 hours (exceeds 150)
    
    for month in range(1, 13):
        # Create regular hours
        regular_date = sofia_now().replace(year=current_year, month=month, day=15, hour=9, minute=0)
        await crud.create_time_log(db, schemas.TimeLogCreate(
            user_id=test_user.id,
            start_time=regular_date,
            end_time=regular_date + timedelta(hours=8),
            type='work',
            notes='Regular work'
        ))
        
        # Create overtime
        overtime_start = regular_date + timedelta(hours=8)
        overtime_end = overtime_start + timedelta(hours=overtime_per_month)
        
        await crud.create_time_log(db, schemas.TimeLogCreate(
            user_id=test_user.id,
            start_time=overtime_start,
            end_time=overtime_end,
            type='work',
            notes=f'Overtime - Month {month}'
        ))
    
    # Check annual overtime compliance
    annual_overtime = await crud.get_annual_overtime_hours(db, test_user.id, current_year)
    
    assert annual_overtime > BULGARIAN_WORK_TIME_REGULATIONS['maximum_overtime_per_year'], \
        "Тестът трябва да симулира надвишаване на годишния лимит"
    
    # System should flag annual limit violation
    annual_violations = await crud.check_annual_overtime_violations(db, test_user.id, current_year)
    assert len(annual_violations) > 0, \
        "Системата трябва да засече надвишаването на годишния лимит"


@pytest.fixture
def work_time_regulations():
    """Fixture за Bulgarian work time regulations"""
    return BULGARIAN_WORK_TIME_REGULATIONS


@pytest.fixture
def time_tracking_scenarios():
    """Fixture за time tracking test scenarios"""
    return TIME_TRACKING_SCENARIOS