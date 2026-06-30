import asyncio
import logging
from datetime import datetime, time

from sqlalchemy import select

from backend import schemas, crud
from backend.auth.rbac_service import DEFAULT_PERMISSIONS, DEFAULT_ROLES
from backend.config import SeedSettings
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.database import AsyncSessionLocal, engine
from backend.seed_documentation import seed_documentation
from backend.database.models import (
    AnnexTemplate,
    AnnexTemplateSection,
    AnnexTemplateVersion,
    Base,
    ClauseTemplate,
    Company,
    CompanyRoleAssignment,
    ContractTemplate,
    ContractTemplateSection,
    ContractTemplateVersion,
    GlobalSetting,
    Module,
    Permission,
    Role,
    RolePermission,
    Shift,
    ShiftType,
    Workstation,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

seed_cfg = SeedSettings()


async def init_db():
    logger.info("Стартиране на пълна инициализация на базата данни...")

    # 1. Създаване на таблиците (ако не съществуват)
    import backend.modules.behavioral_analysis.models  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Структурата на таблиците е проверена/създадена.")

    async with AsyncSessionLocal() as session:
        existing_version = await crud.get_global_setting(session, "seed_version")
        if existing_version and int(existing_version) >= seed_cfg.SEED_VERSION:
            logger.info(f"Seed версия {seed_cfg.SEED_VERSION} вече е приложена, пропускане.")
            await session.close()
            await seed_documentation()
            logger.info("Документацията е попълнена успешно.")
            return

        # 1. Модули
        for m_data in seed_cfg.MODULES:
            res = await session.execute(select(Module).where(Module.code == m_data["code"]))
            existing = res.scalar_one_or_none()
            if not existing:
                session.add(Module(code=m_data["code"], name=m_data["name"], description=m_data["desc"], is_enabled=True))
                logger.info(f"Инициализиран модул: {m_data['name']}")
            elif m_data["code"] in ("shifts",):
                existing.is_enabled = True

        # 2. Глобални настройки (inline upsert — crud.set_global_setting вика commit)
        for key, value in seed_cfg.GLOBAL_SETTINGS.items():
            result = await session.execute(select(GlobalSetting).where(GlobalSetting.key == key))
            setting = result.scalar_one_or_none()
            if setting:
                setting.value = value
            else:
                session.add(GlobalSetting(key=key, value=value))

        # 3. Default company
        company_result = await session.execute(select(Company).limit(1))
        default_company = company_result.scalar_one_or_none()
        if not default_company:
            default_company = Company(name="Demo Company", eik="1234567890", bulstat="BG123456789", mol_name="System Admin")
            session.add(default_company)
            await session.flush()

        # 4. Contract Templates upsert
        _VERSION_FIELDS = {"contract_type", "work_hours_per_week", "probation_months", "salary_calculation_type", "payment_day", "night_work_rate", "overtime_rate", "holiday_rate"}
        for tpl in seed_cfg.CONTRACT_TEMPLATES:
            existing = await session.execute(select(ContractTemplate).where(ContractTemplate.name == tpl["name"], ContractTemplate.company_id == default_company.id))
            if not existing.scalar_one_or_none():
                template = ContractTemplate(company_id=default_company.id, is_active=True, **tpl)
                session.add(template)
                await session.flush()
                version = ContractTemplateVersion(template_id=template.id, version=1, is_current=True, created_by="system", change_note="Първоначална версия", **{k: v for k, v in tpl.items() if k in _VERSION_FIELDS})
                session.add(version)
                await session.flush()
                for sd in seed_cfg.CONTRACT_SECTIONS.get(tpl["contract_type"], []):
                    session.add(ContractTemplateSection(template_id=template.id, version_id=version.id, **sd))

        # 5. Annex Templates upsert
        for tpl in seed_cfg.ANNEX_TEMPLATES:
            existing = await session.execute(select(AnnexTemplate).where(AnnexTemplate.name == tpl["name"], AnnexTemplate.company_id == default_company.id))
            if not existing.scalar_one_or_none():
                template = AnnexTemplate(company_id=default_company.id, is_active=True, **tpl)
                session.add(template)
                await session.flush()
                version = AnnexTemplateVersion(template_id=template.id, version=1, is_current=True, created_by="system", change_note="Първоначална версия", change_type=tpl["change_type"])
                session.add(version)
                await session.flush()
                for sd in seed_cfg.ANNEX_SECTIONS:
                    session.add(AnnexTemplateSection(template_id=template.id, version_id=version.id, **sd))

        # 6. Clause Templates upsert
        for cl in seed_cfg.CLAUSE_TEMPLATES:
            existing = await session.execute(select(ClauseTemplate).where(ClauseTemplate.title == cl["title"], ClauseTemplate.company_id == default_company.id))
            if not existing.scalar_one_or_none():
                session.add(ClauseTemplate(company_id=default_company.id, is_active=True, **cl))

        # 7. Permissions
        for perm_name, perm_data in DEFAULT_PERMISSIONS.items():
            existing = await session.execute(select(Permission).where(Permission.name == perm_name))
            if not existing.scalar_one_or_none():
                session.add(Permission(name=perm_name, resource=perm_data["resource"], action=perm_data["action"], description=perm_data["description"], created_at=datetime.now()))

        # 8. Roles
        for role_name, role_data in DEFAULT_ROLES.items():
            existing = await session.execute(select(Role).where(Role.name == role_name))
            existing_role = existing.scalar_one_or_none()
            if not existing_role:
                role = Role(name=role_name, description=role_data["description"], priority=role_data.get("priority", 0), is_system_role=role_data.get("is_system_role", False), created_at=datetime.now())
                session.add(role)
                await session.flush()
                for perm_name in role_data.get("permissions", []):
                    perm = await session.execute(select(Permission).where(Permission.name == perm_name))
                    perm = perm.scalar_one_or_none()
                    if perm:
                        session.add(RolePermission(role_id=role.id, permission_id=perm.id, granted_at=datetime.now()))

        # 9. Main company
        res = await session.execute(select(Company))
        default_company = res.scalars().first()
        if not default_company:
            default_company = Company(name="Основна Фирма", eik="000000000", address="гр. София, ул. Централна 1")
            session.add(default_company)
            await session.flush()

        # 10. Workstations
        for ws_data in seed_cfg.WORKSTATIONS:
            existing = await session.execute(select(Workstation).filter(Workstation.name == ws_data["name"], Workstation.company_id == default_company.id))
            if not existing.scalars().first():
                session.add(Workstation(name=ws_data["name"], description=ws_data["description"], company_id=default_company.id))

        # 11. Admin user
        admin_email = "admin@example.com"
        admin_role_name = "super_admin"
        role_result = await session.execute(select(Role).where(Role.name == admin_role_name))
        if not role_result.scalar_one_or_none():
            admin_role_name = "admin"
        db_admin = await crud.get_user_by_email(session, admin_email)
        if not db_admin:
            db_admin = await crud.create_user(session, schemas.UserCreate(email=admin_email, username="admin", password="admin1234", first_name="Системен", last_name="Администратор", company_id=default_company.id), role_name=admin_role_name)
            await crud.user_repo.set_pin_code(session, db_admin.id, "00000000")
        else:
            if not db_admin.company_id:
                db_admin.company_id = default_company.id
            if not db_admin.username:
                db_admin.username = "admin"
            if not db_admin.pin_code:
                await crud.user_repo.set_pin_code(session, db_admin.id, "00000000")

        # CompanyRoleAssignment
        admin_role = await session.execute(select(Role).where(Role.name == admin_role_name))
        admin_role = admin_role.scalar_one_or_none()
        db_admin = await crud.get_user_by_email(session, admin_email)
        if db_admin and admin_role:
            existing = await session.execute(select(CompanyRoleAssignment).where(CompanyRoleAssignment.user_id == db_admin.id, CompanyRoleAssignment.company_id == default_company.id, CompanyRoleAssignment.is_active))
            if not existing.scalar_one_or_none():
                session.add(CompanyRoleAssignment(user_id=db_admin.id, company_id=default_company.id, role_id=admin_role.id, assigned_at=datetime.now(), assigned_by=db_admin.id, is_active=True))

        # 12. Shifts
        async def ensure_shift(name, shift_type, start=time(0, 0), end=time(0, 0), tolerance=0, break_duration=0, pay_multiplier=1.0):
            existing = await crud.get_shift_by_name(session, name)
            if not existing:
                session.add(Shift(name=name, start_time=start, end_time=end, shift_type=shift_type, tolerance_minutes=tolerance, break_duration_minutes=break_duration, pay_multiplier=pay_multiplier))
            else:
                updated = False
                if existing.start_time != start: existing.start_time = start; updated = True
                if existing.end_time != end: existing.end_time = end; updated = True
                if existing.tolerance_minutes != tolerance: existing.tolerance_minutes = tolerance; updated = True
                if existing.break_duration_minutes != break_duration: existing.break_duration_minutes = break_duration; updated = True
                if float(existing.pay_multiplier or 1.0) != float(pay_multiplier): existing.pay_multiplier = pay_multiplier; updated = True
                if updated: logger.info(f"Обновени параметри за системна смяна: {name}")

        await ensure_shift("Стандартна смяна", ShiftType.REGULAR.value, time(7, 30), time(16, 30), tolerance=5, break_duration=60)
        await ensure_shift("Болничен", ShiftType.SICK_LEAVE.value)
        await ensure_shift("Платен Отпуск", ShiftType.PAID_LEAVE.value)
        await ensure_shift("Неплатен Отпуск", ShiftType.UNPAID_LEAVE.value)
        await ensure_shift("Почивен Ден", ShiftType.DAY_OFF.value)

        await session.flush()

        # Mark seed version
        result = await session.execute(select(GlobalSetting).where(GlobalSetting.key == "seed_version"))
        setting = result.scalar_one_or_none()
        if setting:
            setting.value = str(seed_cfg.SEED_VERSION)
        else:
            session.add(GlobalSetting(key="seed_version", value=str(seed_cfg.SEED_VERSION)))
        await session.commit()
        logger.info(f"Seed версия {seed_cfg.SEED_VERSION} приложена.")

    # 13. Documentation
    await seed_documentation()
    logger.info("Документацията е попълнена успешно.")


async def ensure_workstations_for_company(company_id: int, session: AsyncSession | None = None):
    """Създава работни станции за дадена фирма ако не съществуват."""
    async with session or AsyncSessionLocal() as s:
        for ws_data in seed_cfg.WORKSTATIONS:
            result = await s.execute(
                select(Workstation).filter(
                    Workstation.name == ws_data["name"],
                    Workstation.company_id == company_id,
                ),
            )
            if not result.scalars().first():
                s.add(Workstation(name=ws_data["name"], description=ws_data["description"], company_id=company_id))
                logger.info(f"Създадена работна станция: {ws_data['name']} за фирма ID {company_id}")
        await s.commit()


if __name__ == "__main__":
    try:
        asyncio.run(init_db())
    except Exception as e:
        logger.error(f"Критична грешка при инициализация: {e}")
