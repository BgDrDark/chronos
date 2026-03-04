import pytest
from datetime import date, timedelta, datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models import (
    User, EmploymentContract, AdvancePayment, ServiceLoan, 
    LeaveRequest, TimeLog, GlobalSetting, Company
)
from backend.services.enhanced_payroll_calculator import EnhancedPayrollCalculator
from backend import crud

@pytest.fixture
async def test_company(test_db: AsyncSession):
    company = Company(name="Test Corp")
    test_db.add(company)
    await test_db.commit()
    await test_db.refresh(company)
    return company

@pytest.mark.asyncio
async def test_payroll_advance_deduction(test_db: AsyncSession, regular_user, test_company):
    """Тества дали еднократен аванс се приспада правилно от нетото за плащане."""
    # 1. Setup: Добавяне на договор
    contract = EmploymentContract(
        user_id=regular_user.id,
        company_id=test_company.id,
        contract_type='labor',
        start_date=date(2026, 1, 1),
        base_salary=2000.0,
        salary_calculation_type='gross',
        is_active=True
    )
    test_db.add(contract)
    
    # 2. Setup: Добавяне на аванс за Февруари
    advance = AdvancePayment(
        user_id=regular_user.id,
        amount=500.0,
        payment_date=date(2026, 2, 10),
        is_processed=False
    )
    test_db.add(advance)
    await test_db.commit()

    # 3. Calculate Payroll for February
    period = {"start_date": date(2026, 2, 1), "end_date": date(2026, 2, 28)}
    calc = EnhancedPayrollCalculator(test_db, test_company.id, regular_user.id, period)
    result = await calc.calculate_enhanced_payroll()

    # 4. Verify
    assert result['advances'] == 500.0
    assert result['net_payable'] == result['net_amount'] - 500.0

@pytest.mark.asyncio
async def test_payroll_loan_installment(test_db: AsyncSession, regular_user, test_company):
    """Тества дали вноска по заем се удържа правилно."""
    # 1. Setup: Добавяне на заем (3000 на 6 вноски = 500/месец)
    loan = ServiceLoan(
        user_id=regular_user.id,
        total_amount=3000.0,
        installment_amount=500.0,
        remaining_amount=3000.0,
        installments_count=6,
        installments_paid=0,
        start_date=date(2026, 2, 1),
        is_active=True
    )
    test_db.add(loan)
    
    contract = EmploymentContract(
        user_id=regular_user.id,
        company_id=test_company.id,
        contract_type='labor',
        start_date=date(2026, 1, 1),
        base_salary=2000.0,
        is_active=True
    )
    test_db.add(contract)
    await test_db.commit()

    # 2. Calculate
    period = {"start_date": date(2026, 2, 1), "end_date": date(2026, 2, 28)}
    calc = EnhancedPayrollCalculator(test_db, test_company.id, regular_user.id, period)
    result = await calc.calculate_enhanced_payroll()

    # 3. Verify
    assert result['loan_deductions'] == 500.0
    assert result['net_payable'] == result['net_amount'] - 500.0

@pytest.mark.asyncio
async def test_salary_split_installments(test_db: AsyncSession, regular_user, test_company):
    """Тества дали нетото се разделя правилно на вноски."""
    contract = EmploymentContract(
        user_id=regular_user.id,
        company_id=test_company.id,
        contract_type='labor',
        start_date=date(2026, 1, 1),
        base_salary=2000.0,
        salary_installments_count=2, # Разделена на 2 плащания
        is_active=True
    )
    test_db.add(contract)
    await test_db.commit()

    period = {"start_date": date(2026, 2, 1), "end_date": date(2026, 2, 28)}
    calc = EnhancedPayrollCalculator(test_db, test_company.id, regular_user.id, period)
    result = await calc.calculate_enhanced_payroll()

    # Verify
    assert result['installments']['count'] == 2
    assert result['installments']['amount_per_installment'] == result['net_payable'] / 2

@pytest.mark.asyncio
async def test_sick_leave_employer_topup(test_db: AsyncSession, regular_user, test_company):
    """Тества изчислението на болничен с доплащане от работодателя."""
    contract = EmploymentContract(
        user_id=regular_user.id,
        company_id=test_company.id,
        contract_type='labor',
        start_date=date(2026, 1, 1),
        base_salary=2000.0,
        is_active=True
    )
    test_db.add(contract)
    
    # Одобрен болничен с Top-up
    sick_leave = LeaveRequest(
        user_id=regular_user.id,
        leave_type='sick_leave',
        start_date=date(2026, 2, 2), # Понеделник
        end_date=date(2026, 2, 6),   # Петък (5 работни дни)
        status='approved',
        employer_top_up=True
    )
    test_db.add(sick_leave)
    
    # TimeLogs за останалите 15 дни (пропускаме болничните)
    for d in range(9, 28):
        dt = date(2026, 2, d)
        if dt.weekday() < 5: # Само делници
            log = TimeLog(
                user_id=regular_user.id,
                start_time=datetime.combine(dt, datetime.min.time()).replace(hour=9),
                end_time=datetime.combine(dt, datetime.min.time()).replace(hour=17)
            )
            test_db.add(log)
            
    await test_db.commit()

    # 2. Calculate
    period = {"start_date": date(2026, 2, 1), "end_date": date(2026, 2, 28)}
    calc = EnhancedPayrollCalculator(test_db, test_company.id, regular_user.id, period)
    result = await calc.calculate_enhanced_payroll()

    # 3. Verify
    # При 100% Top-up, служителят трябва да получи ПЪЛНАТА си брутна заплата (2000)
    assert result['gross_amount'] >= 2000.0