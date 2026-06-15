import asyncio
import logging
from datetime import datetime, time

from sqlalchemy import select

from backend import schemas, crud
from backend.auth.rbac_service import DEFAULT_PERMISSIONS, DEFAULT_ROLES
from backend.config import SeedSettings
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.database import AsyncSessionLocal, engine
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
        # 0. Seed version tracking
        existing_version = await crud.get_global_setting(session, "seed_version")
        if existing_version and int(existing_version) >= seed_cfg.SEED_VERSION:
            logger.info(f"Seed версия {seed_cfg.SEED_VERSION} вече е приложена, пропускане.")
            return

        # 1. Модули
        for m_data in seed_cfg.MODULES:
            res = await session.execute(select(Module).where(Module.code == m_data["code"]))
            existing = res.scalar_one_or_none()
            if not existing:
                new_mod = Module(
                    code=m_data["code"],
                    name=m_data["name"],
                    description=m_data["desc"],
                    is_enabled=True,
                )
                session.add(new_mod)
                logger.info(f"Инициализиран модул: {m_data['name']}")
            else:
                # Ensure core modules stay enabled
                if m_data["code"] in ("shifts",):
                    existing.is_enabled = True

        # 2. Глобални настройки
        for key, value in seed_cfg.GLOBAL_SETTINGS.items():
            await crud.set_global_setting(session, key, value)

        # 3. Contract Templates (идемпотентно — upsert по име + company)
        company_result = await session.execute(select(Company).limit(1))
        default_company = company_result.scalar_one_or_none()
        if not default_company:
            default_company = Company(
                name="Demo Company", eik="1234567890",
                bulstat="BG123456789", mol_name="System Admin",
            )
            session.add(default_company)
            await session.flush()
            logger.info(f"Създадена default компания: {default_company.id}")

        CONT_SECTION_MAP = {
            "full_time": [
                {"title": "Предмет на договора", "content": "Настоящият трудов договор се сключва съгласно Кодекса на труда между Работодателя и Работника за изпълнение на работа по определена длъжност - [ДЛЪЖНОСТ], отдел [ОТДЕЛ]. Работникът изпълнява работата лично.", "order_index": 0, "is_required": True},
                {"title": "Работно време и почивка", "content": "Работникът изпълнява работата си в рамките на 40 часа седмично, при 8-часов работен ден от понеделник до петък. Работодателят осигурява почивка между работните дни съгласно чл. 151 КТ.", "order_index": 1, "is_required": True},
                {"title": "Заплащане", "content": "За извършената работа Работодателят заплаща на Работника основно трудово възнаграждение в размер на [СУМА] лева, начислявано на брутна / нето основа. Възнаграждението се изплаща до [ДЕН] число на текущия месец.", "order_index": 2, "is_required": True},
                {"title": "Права и задължения на работодателя", "content": "Работодателят е длъжен да: 1) осигури на Работника работата, за която е сключен договорът; 2) заплаща своевременно трудовото възнаграждение; 3) осигури здравословни и безопасни условия на труд; 4) предостави необходимите материално-технически средства.", "order_index": 3, "is_required": True},
                {"title": "Права и задължения на работника", "content": "Работникът е длъжен да: 1) изпълнява работата лично и добросъвестно; 2) спазва установения ред в предприятието; 3) изпълнява указанията на работодателя; 4) пази търговската тайна на работодателя; 5) спазва правилата за безопасност и здраве при работа.", "order_index": 4, "is_required": True},
                {"title": "Клаузи", "content": "1) Изпитателен срок: до 6 месеца съгласно чл. 67 КТ. \n2) Нощен труд: заплаща се с увеличение 0.5% за всеки час съгласно чл. 8 КТ. \n3) Извънреден труд: заплаща се с увеличение 50% съгласно чл. 9 КТ. \n4) Труд по празници: заплаща се с увеличение 100% съгласно чл. 10 КТ.", "order_index": 5, "is_required": True},
                {"title": "Заключителни разпоредби", "content": "Настоящият договор влиза в сила от [ДАТА НА СКЛЮЧВАНЕ] и е валиден за неопределено време. Всички изменения и допълнения са валидни само в писмена форма. За неуредените въпроси се прилагат разпоредбите на Кодекса на труда и Закона за трудовата миграция и трудовата мобилност.", "order_index": 6, "is_required": True},
            ],
            "part_time": [
                {"title": "Предмет на договора", "content": "Настоящият трудов договор за непълно работно време се сключва съгласно чл. 138 КТ между Работодателя и Работника за изпълнение на работа по определена длъжност - [ДЛЪЖНОСТ], отдел [ОТДЕЛ]. Работникът изпълнява работата лично.", "order_index": 0, "is_required": True},
                {"title": "Работно време и почивка", "content": "Работникът изпълнява работата си в рамките на 20 часа седмично, при намален работен ден съгласно чл. 138, ал. 1 КТ. Работното време се разпределя равномерно през работните дни на седмицата.", "order_index": 1, "is_required": True},
                {"title": "Заплащане", "content": "За извършената работа Работодателят заплаща на Работника основно трудово възнаграждение в размер на [СУМА] лева, съответстващо на 4 часа дневно. Възнаграждението се изплаща пропорционално на отработеното време до [ДЕН] число на текущия месец.", "order_index": 2, "is_required": True},
                {"title": "Права и задължения на работодателя", "content": "Работодателят е длъжен да: 1) осигури на Работника работата за уговореното работно време; 2) заплаща своевременно трудовото възнаграждение пропорционално на отработеното време; 3) осигури здравословни и безопасни условия на труд; 4) не допуска дискриминация поради непълно работно време.", "order_index": 3, "is_required": True},
                {"title": "Права и задължения на работника", "content": "Работникът е длъжен да: 1) изпълнява работата лично и добросъвестно; 2) спазва установения ред в предприятието; 3) изпълнява указанията на работодателя в рамките на уговореното работно време; 4) пази търговската тайна на работодателя.", "order_index": 4, "is_required": True},
                {"title": "Клаузи", "content": "1) Изпитателен срок: до 6 месеца съгласно чл. 67 КТ. \n2) Работникът има право на всички права по КТ, включително платен годишен отпуск, пропорционален на отработеното време (чл. 155 КТ). \n3) Нощен труд: заплаща се с увеличение 0.5% за всеки час. \n4) Извънреден труд: допустим само при условията на чл. 144 КТ.", "order_index": 5, "is_required": True},
                {"title": "Заключителни разпоредби", "content": "Настоящият договор влиза в сила от [ДАТА НА СКЛЮЧВАНЕ]. Работникът има равни права с работниците на пълно работно време съгласно чл. 138, ал. 3 КТ. За неуредените въпроси се прилагат разпоредбите на Кодекса на труда.", "order_index": 6, "is_required": True},
            ],
            "contractor": [
                {"title": "Предмет на договора", "content": "Настоящият граждански договор (договор за услуга) се сключва по чл. 280 от Закона за задълженията и договорите (ЗЗД) между ВЪЗЛОЖИТЕЛЯ и ИЗПЪЛНИТЕЛЯ за извършване на услугата: [ОПИСАНИЕ НА УСЛУГАТА].", "order_index": 0, "is_required": True},
                {"title": "Работно време и почивка", "content": "Изпълнителят извършва услугата самостоятелно, без да е обвързан с определено работно време. ВЪЗЛОЖИТЕЛЯТ определя конкретните задачи и срокове за изпълнение. Изпълнителят няма право на почивки по смисъла на КТ.", "order_index": 1, "is_required": True},
                {"title": "Заплащане", "content": "За извършената услуга ВЪЗЛОЖИТЕЛЯТ заплаща на Изпълнителя възнаграждение в размер на [СУМА] лева, платимо в срок до [ДЕН] дни след приемане на услугата. Възнаграждението е окончателно и не подлежи на осигуровки.", "order_index": 2, "is_required": True},
                {"title": "Права и задължения на ВЪЗЛОЖИТЕЛЯ", "content": "ВЪЗЛОЖИТЕЛЯТ е длъжен да: 1) предостави на Изпълнителя необходимата информация за изпълнение на услугата; 2) приеме извършената услуга, ако е качествено изпълнена; 3) заплати уговореното възнаграждение в срок.", "order_index": 3, "is_required": True},
                {"title": "Права и задължения на Изпълнителя", "content": "Изпълнителят е длъжен да: 1) извърши услугата лично и качествено; 2) предаде резултата в уговорения срок; 3) информира ВЪЗЛОЖИТЕЛЯ за хода на работата; 4) пази конфиденциалността на информацията.", "order_index": 4, "is_required": True},
                {"title": "Клаузи", "content": "1) Срок за изпълнение: [СРОК] от сключване на договора. \n2) Гражданският договор не установява трудови правоотношения и не подлежи на КТ. \n3) При забава от страна на Изпълнителя, ВЪЗЛОЖИТЕЛЯТ може да прекрати договора. \n4) При неизпълнение, страните носят отговорност съгласно ЗЗД.", "order_index": 5, "is_required": True},
                {"title": "Заключителни разпоредби", "content": "Настоящият договор влиза в сила от датата на подписването му. Всички изменения са валидни само в писмена форма. За неуредените въпроси се прилагат разпоредбите на ЗЗД. Договорът се прекратява с изпълнението на услугата или по взаимно съгласие.", "order_index": 6, "is_required": True},
            ],
        }

        # Contract Templates upsert
        for tpl in seed_cfg.CONTRACT_TEMPLATES:
            existing = await session.execute(
                select(ContractTemplate).where(
                    ContractTemplate.name == tpl["name"],
                    ContractTemplate.company_id == default_company.id,
                ),
            )
            existing = existing.scalar_one_or_none()
            exists = existing is not None
            if not exists:
                template = ContractTemplate(company_id=default_company.id, is_active=True, **tpl)
                session.add(template)
                await session.flush()
                version = ContractTemplateVersion(
                    template_id=template.id, version=1, is_current=True,
                    created_by="system", change_note="Първоначална версия", **tpl,
                )
                session.add(version)
                await session.flush()
                for sd in CONT_SECTION_MAP.get(tpl["contract_type"], []):
                    session.add(ContractTemplateSection(
                        template_id=template.id, version_id=version.id, **sd,
                    ))
                logger.info(f"Създаден шаблон: {tpl['name']}")

        # Annex Templates upsert
        for tpl in seed_cfg.ANNEX_TEMPLATES:
            existing = await session.execute(
                select(AnnexTemplate).where(
                    AnnexTemplate.name == tpl["name"],
                    AnnexTemplate.company_id == default_company.id,
                ),
            )
            if not existing.scalar_one_or_none():
                template = AnnexTemplate(company_id=default_company.id, is_active=True, **tpl)
                session.add(template)
                await session.flush()
                version = AnnexTemplateVersion(
                    template_id=template.id, version=1, is_current=True,
                    created_by="system", change_note="Първоначална версия",
                    change_type=tpl["change_type"],
                )
                session.add(version)
                await session.flush()
                for sd in [
                    {"title": "Описание на промените", "content": "С настоящото споразумение се променят следните условия от трудовия договор:", "order_index": 0, "is_required": True},
                    {"title": "Основание", "content": "Настоящото споразумение се сключва на основание чл. 119, ал. 1 от Кодекса на труда.", "order_index": 1, "is_required": False},
                ]:
                    session.add(AnnexTemplateSection(
                        template_id=template.id, version_id=version.id, **sd,
                    ))
                logger.info(f"Създаден анекс шаблон: {tpl['name']}")

        # Clause Templates upsert
        for cl in seed_cfg.CLAUSE_TEMPLATES:
            existing = await session.execute(
                select(ClauseTemplate).where(
                    ClauseTemplate.title == cl["title"],
                    ClauseTemplate.company_id == default_company.id,
                ),
            )
            if not existing.scalar_one_or_none():
                session.add(ClauseTemplate(company_id=default_company.id, is_active=True, **cl))
                logger.info(f"Създадена клауза: {cl['title']}")

        # 4. Mark seed version
        await crud.set_global_setting(session, "seed_version", str(seed_cfg.SEED_VERSION))
        await session.commit()
        logger.info(f"Seed версия {seed_cfg.SEED_VERSION} приложена.")

    async with AsyncSessionLocal() as session:
        # 2. Seeding Permissions
        logger.info("Проверка на правата (permissions)...")
        for perm_name, perm_data in DEFAULT_PERMISSIONS.items():
            result = await session.execute(select(Permission).where(Permission.name == perm_name))
            existing = result.scalar_one_or_none()

            if not existing:
                permission = Permission(
                    name=perm_name,
                    resource=perm_data["resource"],
                    action=perm_data["action"],
                    description=perm_data["description"],
                    created_at=datetime.now(),
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
                    description=role_data["description"],
                    priority=role_data.get("priority", 0),
                    is_system_role=role_data.get("is_system_role", False),
                    created_at=datetime.now(),
                )
                session.add(role)
                await session.flush() # Get ID
                logger.info(f"Създадена роля: {role_name}")

                # Assign permissions
                for perm_name in role_data.get("permissions", []):
                    perm_result = await session.execute(select(Permission).where(Permission.name == perm_name))
                    permission = perm_result.scalar_one_or_none()
                    if permission:
                        role_perm = RolePermission(
                            role_id=role.id,
                            permission_id=permission.id,
                            granted_at=datetime.now(),
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
                address="гр. София, ул. Централна 1",
            )
            session.add(default_company)
            await session.flush()
            logger.info(f"Създадена основна фирма: {default_company.name} (ID: {default_company.id})")
        else:
            logger.info(f"Намерена съществуваща фирма: {default_company.name}")

        # 3.6 Създаване на работни станции (за сладкарско производство)
        logger.info("Проверка на работни станции...")

        for ws_data in seed_cfg.WORKSTATIONS:
            result = await session.execute(
                select(Workstation).filter(
                    Workstation.name == ws_data["name"],
                    Workstation.company_id == default_company.id,
                ),
            )
            existing_ws = result.scalars().first()

            if not existing_ws:
                workstation = Workstation(
                    name=ws_data["name"],
                    description=ws_data["description"],
                    company_id=default_company.id,
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
                company_id=default_company.id,
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

        # Ensure CompanyRoleAssignment exists for the admin (new RBAC system)
        admin_role = await session.execute(select(Role).where(Role.name == admin_role_name))
        admin_role = admin_role.scalar_one_or_none()
        db_admin = await crud.get_user_by_email(session, admin_email)
        if db_admin and admin_role:
            existing_assignment = await session.execute(
                select(CompanyRoleAssignment).where(
                    CompanyRoleAssignment.user_id == db_admin.id,
                    CompanyRoleAssignment.company_id == default_company.id,
                    CompanyRoleAssignment.is_active,
                ),
            )
            if not existing_assignment.scalar_one_or_none():
                assignment = CompanyRoleAssignment(
                    user_id=db_admin.id,
                    company_id=default_company.id,
                    role_id=admin_role.id,
                    assigned_at=datetime.now(),
                    assigned_by=db_admin.id,
                    is_active=True,
                )
                session.add(assignment)
                logger.info(f"Създадена CompanyRoleAssignment за admin (user_id={db_admin.id}, role_id={admin_role.id})")

        await session.commit()

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
                    pay_multiplier=pay_multiplier,
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
