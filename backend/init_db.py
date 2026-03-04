import asyncio
import logging
from datetime import time, datetime
from sqlalchemy import select
from backend.database.database import engine, AsyncSessionLocal
from backend.database.models import (
    Base, Role, User, Shift, ShiftType, Permission, RolePermission,
    AdvancePayment, ServiceLoan, EmploymentContract, PayrollDeduction, LeaveRequest,
    Company, Workstation
)
from backend import crud, schemas
from backend.auth.rbac_service import DEFAULT_PERMISSIONS, DEFAULT_ROLES

# Настройка на логването
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_db():
    logger.info("Стартиране на пълна инициализация на базата данни...")
    
    # 1. Създаване на таблиците (ако не съществуват)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
        # Ръчно добавяне на колони ако липсват (за съществуващи инсталации)
        from sqlalchemy import text
        try:
            # Смени и Логове
            await conn.execute(text("ALTER TABLE shifts ADD COLUMN IF NOT EXISTS pay_multiplier NUMERIC(4, 2) DEFAULT 1.0"))
            await conn.execute(text("ALTER TABLE timelogs ADD COLUMN IF NOT EXISTS break_duration_minutes INTEGER DEFAULT 0"))
            
            # Потребители (Security & QR)
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS qr_secret VARCHAR(64)"))
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS failed_login_attempts INTEGER DEFAULT 0"))
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS locked_until TIMESTAMP WITHOUT TIME ZONE"))
            
            # Договори
            await conn.execute(text("ALTER TABLE employment_contracts ADD COLUMN IF NOT EXISTS salary_calculation_type VARCHAR(20) DEFAULT 'gross'"))
            await conn.execute(text("ALTER TABLE employment_contracts ADD COLUMN IF NOT EXISTS tax_resident BOOLEAN DEFAULT TRUE"))
            await conn.execute(text("ALTER TABLE employment_contracts ADD COLUMN IF NOT EXISTS insurance_contributor BOOLEAN DEFAULT TRUE"))
            await conn.execute(text("ALTER TABLE employment_contracts ADD COLUMN IF NOT EXISTS has_income_tax BOOLEAN DEFAULT TRUE"))
            await conn.execute(text("ALTER TABLE employment_contracts ADD COLUMN IF NOT EXISTS salary_installments_count INTEGER DEFAULT 1"))
            await conn.execute(text("ALTER TABLE employment_contracts ADD COLUMN IF NOT EXISTS monthly_advance_amount NUMERIC(10, 2) DEFAULT 0"))
            await conn.execute(text("ALTER TABLE payroll_deductions ADD COLUMN IF NOT EXISTS comment VARCHAR(255)"))
            await conn.execute(text("ALTER TABLE payroll_deductions ADD COLUMN IF NOT EXISTS priority INTEGER DEFAULT 0"))
            await conn.execute(text("ALTER TABLE leave_requests ADD COLUMN IF NOT EXISTS employer_top_up BOOLEAN DEFAULT FALSE"))
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS phone_number VARCHAR(20)"))
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS address VARCHAR(255)"))
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS egn VARCHAR(10)"))
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS birth_date DATE"))
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS iban VARCHAR(34)"))
            
            # Modules Table Check
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS modules (
                    id SERIAL PRIMARY KEY,
                    code VARCHAR(50) UNIQUE NOT NULL,
                    is_enabled BOOLEAN DEFAULT FALSE,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
                )
            """))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_modules_code ON modules (code)"))
            
            # Production Control Tablet - Срок за производство
            await conn.execute(text("ALTER TABLE recipes ADD COLUMN IF NOT EXISTS production_deadline_days INTEGER"))
            await conn.execute(text("ALTER TABLE production_orders ADD COLUMN IF NOT EXISTS production_deadline TIMESTAMP WITHOUT TIME ZONE"))
            
            logger.info("Проверка/Добавяне на липсващи колони (Full Schema Update) завърши.")
        except Exception as e:
            logger.warning(f"Грешка при опит за добавяне на колони: {e}")

    # Инициализация на модули и нови глобални настройки
    async with AsyncSessionLocal() as session:
        from backend.database.models import Module
        # 0. Инициализация на модули (Enabled by default)
        MODULES_TO_SEED = [
            {'code': 'shifts', 'name': 'Смени и работно време', 'desc': 'Управление на работно време, смени и присъствие'},
            {'code': 'salaries', 'name': 'Заплати', 'desc': 'Изчисляване на заплати, ТРЗ и договори'},
            {'code': 'kiosk', 'name': 'Kiosk терминал', 'desc': 'Управление на физически терминали и QR чекиране'},
            {'code': 'integrations', 'name': 'Интеграции', 'desc': 'Google Calendar, Webhooks и външни услуги'},
            {'code': 'confectionery', 'name': 'Сладкарско производство и Склад', 'desc': 'Управление на склад (FEFO), Рецептурник и Производствени станции'},
            {'code': 'accounting', 'name': 'Счетоводство и Фактуриране', 'desc': 'Управление на фактури, доставчици и разплащания'},
            {'code': 'notifications', 'name': 'Уведомления и Кореспонденция', 'desc': 'SMTP настройки, имейл справки и автоматични известия за наличности'},
        ]
        
        for m_data in MODULES_TO_SEED:
            res = await session.execute(select(Module).where(Module.code == m_data['code']))
            if not res.scalar_one_or_none():
                new_mod = Module(
                    code=m_data['code'],
                    name=m_data['name'],
                    description=m_data['desc'],
                    is_enabled=True # ВСИЧКИ ВКЛЮЧЕНИ ПО ПОДРАЗБИРАНЕ
                )
                session.add(new_mod)
                logger.info(f"Инициализиран модул (активен): {m_data['name']}")
            else:
                # Ensure they are enabled if they are in the default enabled list
                result = await session.execute(select(Module).where(Module.code == m_data['code']))
                existing_mod = result.scalar_one()
                if m_data['code'] in ['shifts', 'accounting', 'confectionery', 'notifications']:
                    existing_mod.is_enabled = True
                    session.add(existing_mod)

        from backend import crud
        # Болнични правила
        await crud.set_global_setting(session, "payroll_noi_compensation_percent", "80.0")
        await crud.set_global_setting(session, "payroll_employer_paid_sick_days", "3")
        await crud.set_global_setting(session, "payroll_default_tax_resident", "true")
        
        # Настройки за Аванси (Сигурност)
        await crud.set_global_setting(session, "qr_token_regen_minutes", "15")
        
        # Настройки за пароли
        await crud.set_global_setting(session, "pwd_min_length", "8")
        await crud.set_global_setting(session, "pwd_max_length", "32")
        await crud.set_global_setting(session, "pwd_require_upper", "false")
        await crud.set_global_setting(session, "pwd_require_lower", "false")
        await crud.set_global_setting(session, "pwd_require_digit", "false")
        await crud.set_global_setting(session, "pwd_require_special", "false")
        await crud.set_global_setting(session, "password_settings_version", "1") # Initial version
        
        await session.commit()
            
    logger.info("Структурата на таблиците е проверена/създадена.")

    async with AsyncSessionLocal() as session:
        # 2. Seeding Permissions
        logger.info("Проверка на правата (permissions)...")
        for perm_name, perm_data in DEFAULT_PERMISSIONS.items():
            result = await session.execute(select(Permission).where(Permission.name == perm_name))
            existing = result.scalar_one_or_none()
            
            if not existing:
                permission = Permission(
                    name=perm_name,
                    resource=perm_data['resource'],
                    action=perm_data['action'],
                    description=perm_data['description'],
                    created_at=datetime.now()
                )
                session.add(permission)
                logger.info(f"Създадено право: {perm_name}")
        await session.commit() # Commit permissions first

        # 3. Seeding Roles
        logger.info("Проверка на ролите...")
        for role_name, role_data in DEFAULT_ROLES.items():
            result = await session.execute(select(Role).where(Role.name == role_name))
            existing_role = result.scalar_one_or_none()
            
            if not existing_role:
                role = Role(
                    name=role_name,
                    description=role_data['description'],
                    priority=role_data.get('priority', 0),
                    is_system_role=role_data.get('is_system_role', False),
                    created_at=datetime.now()
                )
                session.add(role)
                await session.flush() # Get ID
                logger.info(f"Създадена роля: {role_name}")
                
                # Assign permissions
                for perm_name in role_data.get('permissions', []):
                    perm_result = await session.execute(select(Permission).where(Permission.name == perm_name))
                    permission = perm_result.scalar_one_or_none()
                    if permission:
                        role_perm = RolePermission(
                            role_id=role.id,
                            permission_id=permission.id,
                            granted_at=datetime.now()
                        )
                        session.add(role_perm)
            else:
                # Optional: Update existing role permissions if needed (skipping for now to be safe)
                pass
        
        await session.commit()

        # 3.5 Проверка и създаване на основна фирма
        logger.info("Проверка на фирмите...")
        res = await session.execute(select(Company))
        default_company = res.scalars().first()
        if not default_company:
            default_company = Company(
                name="Основна Фирма",
                eik="000000000",
                address="гр. София, ул. Централна 1"
            )
            session.add(default_company)
            await session.flush()
            logger.info(f"Създадена основна фирма: {default_company.name} (ID: {default_company.id})")
        else:
            logger.info(f"Намерена съществуваща фирма: {default_company.name}")

        # 3.6 Създаване на работни станции (за сладкарско производство)
        logger.info("Проверка на работни станции...")
        
        DEFAULT_WORKSTATIONS = [
            {"name": "Пекарна", "description": "Изпичане на блатове и основи"},
            {"name": "Кремове", "description": "Приготвяне на кремове и пълнежи"},
            {"name": "Декорация", "description": "Украса на готовите изделия"},
        ]
        
        for ws_data in DEFAULT_WORKSTATIONS:
            result = await session.execute(
                select(Workstation).filter(
                    Workstation.name == ws_data["name"],
                    Workstation.company_id == default_company.id
                )
            )
            existing_ws = result.scalars().first()
            
            if not existing_ws:
                workstation = Workstation(
                    name=ws_data["name"],
                    description=ws_data["description"],
                    company_id=default_company.id
                )
                session.add(workstation)
                logger.info(f"Създадена работна станция: {ws_data['name']} за фирма {default_company.name}")
            else:
                logger.info(f"Работна станция вече съществува: {ws_data['name']} за фирма {default_company.name}")

        # 4. Създаване на администраторски акаунт
        admin_email = "admin@example.com"
        logger.info(f"Проверка на администратор ({admin_email})...")
        db_admin = await crud.get_user_by_email(session, admin_email)
        
        # Determine admin role name (prefer super_admin, fallback to admin)
        admin_role_name = "super_admin"
        role_check = await session.execute(select(Role).where(Role.name == admin_role_name))
        if not role_check.scalar_one_or_none():
             admin_role_name = "admin" # Fallback if super_admin wasn't in DEFAULT_ROLES for some reason

        if not db_admin:
            admin_in = schemas.UserCreate(
                email=admin_email,
                password="admin1234",
                first_name="Системен",
                last_name="Администратор",
                company_id=default_company.id
            )
            # Use crud.create_user which handles password hashing and role assignment
            await crud.create_user(session, admin_in, role_name=admin_role_name)
            logger.info(f"Администратор е създаден: {admin_email} / admin1234 (Role: {admin_role_name}, Company: {default_company.name})")
        else:
            if not db_admin.company_id:
                db_admin.company_id = default_company.id
                session.add(db_admin)
                logger.info(f"Администраторът е зачислен към фирма: {default_company.name}")
            logger.info("Администраторът вече съществува.")

        # 5. Създаване на системни типове смени
        logger.info("Проверка на системните смени...")
        
        async def ensure_shift(name, shift_type, start=time(0,0), end=time(0,0), tolerance=0, break_duration=0, pay_multiplier=1.0):
            existing = await crud.get_shift_by_name(session, name)
            if not existing:
                s = Shift(
                    name=name,
                    start_time=start,
                    end_time=end,
                    shift_type=shift_type,
                    tolerance_minutes=tolerance,
                    break_duration_minutes=break_duration,
                    pay_multiplier=pay_multiplier
                )
                session.add(s)
                logger.info(f"Създадена системна смяна: {name}")
            else:
                # Обновяваме параметрите, ако са различни
                updated = False
                if existing.start_time != start:
                    existing.start_time = start
                    updated = True
                if existing.end_time != end:
                    existing.end_time = end
                    updated = True
                if existing.tolerance_minutes != tolerance:
                    existing.tolerance_minutes = tolerance
                    updated = True
                if existing.break_duration_minutes != break_duration:
                    existing.break_duration_minutes = break_duration
                    updated = True
                if float(existing.pay_multiplier or 1.0) != float(pay_multiplier):
                    existing.pay_multiplier = pay_multiplier
                    updated = True
                
                if updated:
                    logger.info(f"Обновени параметри за системна смяна: {name} ({start}-{end}, T:{tolerance}, B:{break_duration}, M:{pay_multiplier})")

        # Стандартна работна смяна
        await ensure_shift("Стандартна смяна", ShiftType.REGULAR.value, time(7, 30), time(16, 30), tolerance=5, break_duration=60)
        
        # Специални типове за отпуски
        await ensure_shift("Болничен", ShiftType.SICK_LEAVE.value)
        await ensure_shift("Платен Отпуск", ShiftType.PAID_LEAVE.value)
        await ensure_shift("Неплатен Отпуск", ShiftType.UNPAID_LEAVE.value)
        await ensure_shift("Почивен Ден", ShiftType.DAY_OFF.value)

        await session.commit()

    logger.info("Базата данни е напълно готова и попълнена с начални данни.")


async def ensure_workstations_for_company(company_id: int, session=None):
    """
    Създава работни станции за дадена фирма ако не съществуват.
    Може да се извика при създаване на нова фирма.
    
    Args:
        company_id: ID на фирмата
        session: AsyncSession (ако не е подаден, създава нова връзка)
    """
    from sqlalchemy.ext.asyncio import AsyncSession
    
    DEFAULT_WORKSTATIONS = [
        {"name": "Пекарна", "description": "Изпичане на блатове и основи"},
        {"name": "Кремове", "description": "Приготвяне на кремове и пълнежи"},
        {"name": "Декорация", "description": "Украса на готовите изделия"},
    ]
    
    close_session = False
    if session is None:
        session = AsyncSessionLocal()
        close_session = True
    
    try:
        for ws_data in DEFAULT_WORKSTATIONS:
            result = await session.execute(
                select(Workstation).filter(
                    Workstation.name == ws_data["name"],
                    Workstation.company_id == company_id
                )
            )
            existing_ws = result.scalars().first()
            
            if not existing_ws:
                workstation = Workstation(
                    name=ws_data["name"],
                    description=ws_data["description"],
                    company_id=company_id
                )
                session.add(workstation)
                logger.info(f"Създадена работна станция: {ws_data['name']} за фирма ID {company_id}")
            else:
                logger.info(f"Работна станция вече съществува: {ws_data['name']} за фирма ID {company_id}")
        
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error(f"Грешка при създаване на работни станции: {e}")
    finally:
        if close_session:
            await session.close()


if __name__ == "__main__":
    try:
        asyncio.run(init_db())
    except Exception as e:
        logger.error(f"Критична грешка при инициализация: {e}")
