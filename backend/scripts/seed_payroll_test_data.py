"""
Seed тестови данни за заплати - Май 2026

Създава 5 потребителя с:
- Пълни TRZ досиета (ЕГН, адрес, банкова сметка)
- Трудови договори на пълен работен ден
- Смени за пълен месец Май 2026
- Overtime часове
- Leave (отпуск) за 2-3 потребител
- Бонус/Авансови плащания

Usage:
    python -m backend.scripts.seed_payroll_test_data
"""

import asyncio
import sys
import os
import random
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional
import hashlib

# Проста функция за hashing (заобикаля circular import)
def hash_password_simple(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import select, func

from backend.database.database import AsyncSessionLocal
from backend.database.models import (
    Company, User, Role, Department, Position,
    EmploymentContract, Shift, TimeLog, LeaveRequest,
    AdvancePayment, Bonus, Payroll, PayrollDeduction,
    WorkSchedule
)


# Конфигурация за тестовите потребители
USERS_DATA = [
    {
        "username": "pesho_petkov",
        "email": "pesho@test.com",
        "first_name": "Петко",
        "last_name": "Петков",
        "position": "Пекар",
        "salary": 1800.00,
        "hourly_rate": 10.00,
        "egn": "7501010010",
        "address": "гр. София, ул. Княз Борис I №45",
        "phone": "+359888123456",
        "bank_account": "BG81KNCB97901001000100",
        "start_date": date(2024, 1, 15),
        "overtime_hours": 20,
        "leave_days": 3,
        "bonus_amount": 250.00,  # ~14% от заплатата
        "advance_amount": 0,
    },
    {
        "username": "maria_ivanova",
        "email": "maria@test.com",
        "first_name": "Мария",
        "last_name": "Иванова",
        "position": "Декоратор",
        "salary": 1900.00,
        "hourly_rate": 10.56,
        "egn": "7552010011",
        "address": "гр. Пловдив, ул. Гладстон №12",
        "phone": "+359888234567",
        "bank_account": "BG82KNCB97901001000200",
        "start_date": date(2024, 3, 1),
        "overtime_hours": 10,
        "leave_days": 2,
        "bonus_amount": 0,
        "advance_amount": 300.00,
    },
    {
        "username": "georgi_dimitrov",
        "email": "georgi@test.com",
        "first_name": "Георги",
        "last_name": "Димитров",
        "position": "Шофьор",
        "salary": 2000.00,
        "hourly_rate": 11.11,
        "egn": "8032056032",
        "address": "гр. Варна, ул. Кан Гаврил №8",
        "phone": "+359888345678",
        "bank_account": "BG83KNCB97901001000300",
        "start_date": date(2023, 6, 15),
        "overtime_hours": 15,
        "leave_days": 0,
        "bonus_amount": 400.00,  # 20% от заплатата
        "advance_amount": 500.00,
    },
    {
        "username": "elena_petrova",
        "email": "elena@test.com",
        "first_name": "Елена",
        "last_name": "Петрова",
        "position": "Мениджър",
        "salary": 3000.00,
        "hourly_rate": 16.67,
        "egn": "8212106033",
        "address": "гр. София, бул. Витоша №100",
        "phone": "+359888456789",
        "bank_account": "BG84KNCB97901001000400",
        "start_date": date(2023, 1, 1),
        "overtime_hours": 5,
        "leave_days": 5,
        "bonus_amount": 1000.00,  # ~33% от заплатата
        "advance_amount": 0,
    },
    {
        "username": "stefan_kostadinov",
        "email": "stefan@test.com",
        "first_name": "Стефан",
        "last_name": "Костадинов",
        "position": "Складов работник",
        "salary": 1500.00,
        "hourly_rate": 8.33,
        "egn": "8032056034",
        "address": "гр. Пловдив, ул. Самарна №3",
        "phone": "+359888567890",
        "bank_account": "BG85KNCB97901001000500",
        "start_date": date(2024, 2, 10),
        "overtime_hours": 18,
        "leave_days": 2,
        "bonus_amount": 150.00,
        "advance_amount": 200.00,
    },
]

# Май 2026 - пълен месец
MONTH = 5
YEAR = 2026


def get_working_days(year: int, month: int) -> list:
    """Връща списък с работни дни за дадения месец"""
    from calendar import monthrange
    
    working_days = []
    days_in_month = monthrange(year, month)[1]
    
    for day in range(1, days_in_month + 1):
        d = date(year, month, day)
        # Понеделник - Петък са работни дни
        if d.weekday() < 5:  # 0=Понеделник, 4=Петък
            working_days.append(d)
    
    return working_days


async def get_or_create_user(db, user_data: dict, company_id: int, role_id: int, position_id: int) -> User:
    """Създава или връща съществуващ потребител"""
    
    # Провери дали потребителят съществува
    result = await db.execute(
        select(User).where(User.email == user_data["email"])
    )
    user = result.scalar_one_or_none()
    
    if user:
        print(f"  → Потребител {user_data['username']} вече съществува (id={user.id})")
        return user
    
    # Създай нов потребител
    user = User(
        username=user_data["username"],
        email=user_data["email"],
        first_name=user_data["first_name"],
        last_name=user_data["last_name"],
        hashed_password=hash_password_simple("Password123!"),
        role_id=role_id,
        company_id=company_id,
        position_id=position_id,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    
    print(f"  ✓ Създаден потребител: {user.username} (id={user.id})")
    return user


async def create_contract(db, user: User, user_data: dict, company_id: int) -> EmploymentContract:
    """Създава трудов договор"""
    
    contract = EmploymentContract(
        user_id=user.id,
        company_id=company_id,
        contract_type="full_time",  # Пълен работен ден
        start_date=user_data["start_date"],
        end_date=None,  # Безсрочен
        base_salary=user_data["salary"],
        work_hours_per_week=40,
        salary_calculation_type="gross",
        tax_resident=True,
        insurance_contributor=True,
        has_income_tax=True,
        status='signed',  # Подписан
        signed_at=datetime.now(),
        employee_egn=user_data["egn"],
        employee_name=user_data["first_name"] + " " + user_data["last_name"],
    )
    db.add(contract)
    await db.flush()
    
    print(f"  ✓ Трудов договор: {contract.contract_type}, status={contract.status}")
    return contract


async def create_shifts_for_month(db, user: User, company_id: int, user_data: dict):
    """Създава смени за целия месец Май 2026"""
    
    from datetime import time as dt_time
    
    # Създай или намери Shift шаблони
    from backend.database.models import ShiftType
    
    morning_shift = await db.execute(
        select(Shift).where(Shift.shift_type == ShiftType.REGULAR.value)
    )
    morning_shift = morning_shift.scalar_one_or_none()
    
    if not morning_shift:
        morning_shift = Shift(
            name="Сутрешна",
            start_time=dt_time(8, 0),
            end_time=dt_time(16, 0),
            pay_multiplier=Decimal("1.0"),
            shift_type=ShiftType.REGULAR.value,
            break_duration_minutes=30,
        )
        db.add(morning_shift)
        await db.flush()
    
    overtime_shift = await db.execute(
        select(Shift).where(Shift.shift_type == "overtime")
    )
    overtime_shift = overtime_shift.scalar_one_or_none()
    
    if not overtime_shift:
        overtime_shift = Shift(
            name="Overtime",
            start_time=dt_time(16, 0),
            end_time=dt_time(18, 0),
            pay_multiplier=Decimal("1.5"),
            shift_type="overtime",
        )
        db.add(overtime_shift)
        await db.flush()
    
    working_days = get_working_days(YEAR, MONTH)
    
    rest_days = random.sample(working_days, min(len(working_days) - 18, 3))
    
    shifts_created = 0
    overtime_used = 0
    target_overtime = user_data.get("overtime_hours", 0)
    
    for work_date in working_days:
        if work_date in rest_days:
            continue
        
        schedule = WorkSchedule(
            date=work_date,
            user_id=user.id,
            shift_id=morning_shift.id,
        )
        db.add(schedule)
        shifts_created += 1
        
        clock_in = datetime.combine(work_date, datetime.min.time()).replace(hour=8)
        clock_out = datetime.combine(work_date, datetime.min.time()).replace(hour=16)
        
        time_log = TimeLog(
            user_id=user.id,
            start_time=clock_in,
            end_time=clock_out,
            break_duration_minutes=30,
            type="work",
        )
        db.add(time_log)
        
        if overtime_used < target_overtime and random.random() < 0.3:
            ot_schedule = WorkSchedule(
                date=work_date,
                user_id=user.id,
                shift_id=overtime_shift.id,
            )
            db.add(ot_schedule)
            
            ot_clock_in = datetime.combine(work_date, datetime.min.time()).replace(hour=16)
            ot_clock_out = datetime.combine(work_date, datetime.min.time()).replace(hour=18)
            
            ot_log = TimeLog(
                user_id=user.id,
                start_time=ot_clock_in,
                end_time=ot_clock_out,
                type="overtime",
            )
            db.add(ot_log)
            overtime_used += 2
    
    await db.flush()
    print(f"  ✓ Смени: {shifts_created} нормални + {overtime_used} overtime часа")


async def create_leave(db, user: User, days: int, company_id: int):
    """Създава leave заявка"""
    
    if days <= 0:
        return
    
    working_days = get_working_days(YEAR, MONTH)
    
    leave_days_dates = random.sample(working_days, min(len(working_days), days))
    
    for leave_date in leave_days_dates:
        leave = LeaveRequest(
            user_id=user.id,
            leave_type="annual_paid",
            start_date=leave_date,
            end_date=leave_date,
            status="approved",
        )
        db.add(leave)
    
    await db.flush()
    print(f"  ✓ Leave: {days} дни отпу")


async def create_bonus_or_advance(db, user: User, bonus_amount: Decimal, advance_amount: Decimal, company_id: int):
    """Създава бонус или авансово плащане"""
    
    if bonus_amount > 0:
        bonus = Bonus(
            user_id=user.id,
            amount=bonus_amount,
            date=datetime(YEAR, MONTH, 1).date(),
            description="Performance бонус",
        )
        db.add(bonus)
        await db.flush()
        print(f"  ✓ Бонус: {bonus_amount} лв.")
    
    if advance_amount > 0:
        advance = AdvancePayment(
            user_id=user.id,
            amount=advance_amount,
            payment_date=datetime(YEAR, MONTH, 15).date(),
            description="Персонален аванс",
            is_processed=True,
        )
        db.add(advance)
        await db.flush()
        print(f"  ✓ Аванс: {advance_amount} лв.")


async def seed_payroll_test_data():
    """Основна функция за seed"""
    
    print("=" * 60)
    print("SEED ТЕСТОВИ ДАННИ ЗА ЗАПЛАТИ - МАЙ 2026")
    print("=" * 60)
    
    async with AsyncSessionLocal() as db:
        # Вземи компания
        result = await db.execute(select(Company).limit(1))
        company = result.scalar_one_or_none()
        
        if not company:
            print("ГРЕШКА: Няма компания в базата")
            return
        
        company_id = company.id
        print(f"\nКомпания: {company.name} (id={company_id})")
        
        # Вземи роля
        result = await db.execute(select(Role).where(Role.name == "employee"))
        role = result.scalar_one_or_none()
        
        if not role:
            role = Role(name="employee")
            db.add(role)
            await db.flush()
        
        role_id = role.id
        print(f"Роля: {role.name} (id={role_id})")
        
        for i, user_data in enumerate(USERS_DATA, 1):
            print(f"\n[{i}/5] Създавам {user_data['username']}...")
            
            result = await db.execute(
                select(Position).where(Position.title == user_data["position"])
            )
            position = result.scalar_one_or_none()
            
            if not position:
                position = Position(title=user_data["position"])
                db.add(position)
                await db.flush()
            
            position_id = position.id
            
            user = await get_or_create_user(db, user_data, company_id, role_id, position_id)
            
            contract = await create_contract(db, user, user_data, company_id)
            
            await create_shifts_for_month(db, user, company_id, user_data)
            
            leave_days = user_data.get("leave_days", 0)
            if leave_days > 0:
                await create_leave(db, user, leave_days, company_id)
            
            bonus = Decimal(str(user_data.get("bonus_amount", 0)))
            advance = Decimal(str(user_data.get("advance_amount", 0)))
            if bonus > 0 or advance > 0:
                await create_bonus_or_advance(db, user, bonus, advance, company_id)
        
        await db.commit()
        
        print("\n" + "=" * 60)
        print("ГОТОВО!")
        print("=" * 60)


def main():
    asyncio.run(seed_payroll_test_data())


if __name__ == "__main__":
    main()