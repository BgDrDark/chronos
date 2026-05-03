import asyncio
import logging
from datetime import time, datetime
from sqlalchemy import select
from backend.database.database import engine, AsyncSessionLocal
from backend.database.models import (
    Base, Role, User, Shift, ShiftType, Permission, RolePermission,
    AdvancePayment, ServiceLoan, EmploymentContract, PayrollDeduction, LeaveRequest,
    Company, Workstation, ContractTemplate, ContractTemplateVersion, ContractTemplateSection,
    AnnexTemplate, AnnexTemplateVersion, AnnexTemplateSection, ClauseTemplate, ThrottleLog
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
            
            # Company Accounting Settings - Счетоводни настройки за фирмата
            await conn.execute(text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS default_sales_account_id INTEGER"))
            await conn.execute(text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS default_expense_account_id INTEGER"))
            await conn.execute(text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS default_vat_account_id INTEGER"))
            await conn.execute(text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS default_customer_account_id INTEGER"))
            await conn.execute(text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS default_supplier_account_id INTEGER"))
            await conn.execute(text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS default_cash_account_id INTEGER"))
            await conn.execute(text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS default_bank_account_id INTEGER"))
            
            # Recipe Pricing Fields - Цени за рецепти
            await conn.execute(text("ALTER TABLE recipes ADD COLUMN IF NOT EXISTS category VARCHAR(100)"))
            await conn.execute(text("ALTER TABLE recipes ADD COLUMN IF NOT EXISTS selling_price NUMERIC(10, 2)"))
            await conn.execute(text("ALTER TABLE recipes ADD COLUMN IF NOT EXISTS cost_price NUMERIC(10, 2)"))
            await conn.execute(text("ALTER TABLE recipes ADD COLUMN IF NOT EXISTS markup_percentage NUMERIC(5, 2) DEFAULT 0"))
            await conn.execute(text("ALTER TABLE recipes ADD COLUMN IF NOT EXISTS premium_amount NUMERIC(10, 2) DEFAULT 0"))
            await conn.execute(text("ALTER TABLE recipes ADD COLUMN IF NOT EXISTS portions INTEGER DEFAULT 1"))
            await conn.execute(text("ALTER TABLE recipes ADD COLUMN IF NOT EXISTS last_price_update TIMESTAMP"))
            await conn.execute(text("ALTER TABLE recipes ADD COLUMN IF NOT EXISTS price_calculated_at TIMESTAMP"))
            
            # Price History Table - История на цените
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS price_history (
                    id SERIAL PRIMARY KEY,
                    recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
                    old_price NUMERIC(10, 2),
                    new_price NUMERIC(10, 2),
                    old_cost NUMERIC(10, 2),
                    new_cost NUMERIC(10, 2),
                    old_markup NUMERIC(5, 2),
                    new_markup NUMERIC(5, 2),
                    old_premium NUMERIC(10, 2),
                    new_premium NUMERIC(10, 2),
                    changed_by INTEGER NOT NULL REFERENCES users(id),
                    changed_at TIMESTAMP DEFAULT NOW(),
                    reason VARCHAR(255)
                )
            """))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_price_history_recipe ON price_history(recipe_id)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_price_history_date ON price_history(changed_at)"))
            
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
            {'code': 'fleet', 'name': 'Автопарк', 'desc': 'Управление на автомобили, горива, ремонти, винетки и пътни карти'},
            {'code': 'cost_centers', 'name': 'Разходни центрове', 'desc': 'Управление на разходни центрове за финансово проследяване'},
            {'code': 'inventory', 'name': 'Инвентаризация', 'desc': 'Инвентаризационни сесии и баркод сканиране'},
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
                if m_data['code'] in ['shifts']:
                    existing_mod.is_enabled = True
                    session.add(existing_mod)

        from backend import crud
        # Болнични правила
        await crud.set_global_setting(session, "payroll_noi_compensation_percent", "80.0")
        await crud.set_global_setting(session, "payroll_employer_paid_sick_days", "2")
        await crud.set_global_setting(session, "payroll_default_tax_resident", "true")
        await crud.set_global_setting(session, "trz_compliance_strict_mode", "false")
        
        # Осигуровки (Фаза 1) - начални ставки 2026
        # ДОО - Пенсия (за родени след 1959)
        await crud.set_global_setting(session, "payroll_doo_employee_rate", "14.3")
        await crud.set_global_setting(session, "payroll_doo_employer_rate", "14.3")
        # ДОО - Пенсия (за родени преди 1960)
        await crud.set_global_setting(session, "payroll_doo_older_employee_rate", "19.3")
        await crud.set_global_setting(session, "payroll_doo_older_employer_rate", "19.3")
        # ЗО - Здравно
        await crud.set_global_setting(session, "payroll_zo_employee_rate", "3.2")
        await crud.set_global_setting(session, "payroll_zo_employer_rate", "4.8")
        # ДЗПО - Допълнително пенсионно
        await crud.set_global_setting(session, "payroll_dzpo_employee_rate", "2.2")
        await crud.set_global_setting(session, "payroll_dzpo_employer_rate", "2.8")
        # ТЗПБ - Трудова злополука
        await crud.set_global_setting(session, "payroll_tzpb_rate", "0.4")
        
        # Данъци (Фаза 2)
        await crud.set_global_setting(session, "payroll_income_tax_rate", "10")
        await crud.set_global_setting(session, "payroll_standard_deduction", "500")
        
        # Максимална осигурителна база и минимална заплата
        await crud.set_global_setting(session, "payroll_max_insurable_base", "4100")
        await crud.set_global_setting(session, "payroll_min_wage", "1213")
        
        # Автоматизация (Фаза 3)
        await crud.set_global_setting(session, "payroll_auto_night_work", "false")
        await crud.set_global_setting(session, "payroll_auto_overtime", "false")
        await crud.set_global_setting(session, "payroll_auto_holiday", "false")
        await crud.set_global_setting(session, "payroll_night_hourly_supplement", "0.15")
        await crud.set_global_setting(session, "payroll_overtime_rate", "50")
        await crud.set_global_setting(session, "payroll_holiday_rate", "100")
        
        # Отпуски и болнични (Фаза 5)
        await crud.set_global_setting(session, "payroll_annual_leave_days", "20")  # Годишен отпуск
        await crud.set_global_setting(session, "payroll_sick_day_1_rate", "70")  # Първи ден болничен 70%
        await crud.set_global_setting(session, "payroll_sick_days_covered_by_employer", "2")  # 2 дни от работодател
        await crud.set_global_setting(session, "payroll_maternity_days", "410")  # Майчинство 410 дни
        await crud.set_global_setting(session, "payroll_paternity_days", "15")  # Бащинство 15 дни
        
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
        
        # Seed TRZ Templates (Шаблони за договори и анекси)
        # Винаги обновяваме шаблоните с актуално съдържание
        result = await session.execute(select(ContractTemplate).limit(1))
        existing_templates = result.scalars().first()
        
        # Ако има съществуващи шаблони, ги изтриваме и създаваме наново
        if existing_templates:
            logger.info("Обновяване на TRZ шаблони...")
            await session.execute(text("DELETE FROM contract_template_sections"))
            await session.execute(text("DELETE FROM contract_template_versions"))
            await session.execute(text("DELETE FROM contract_templates"))
            await session.flush()
            logger.info("Изтрити съществуващи TRZ шаблони.")
        
        # Вземаме или създаваме default company за шаблоните
        company_result = await session.execute(select(Company).limit(1))
        default_company = company_result.scalar_one_or_none()
        
        if not default_company:
            # Създаваме default company ако не съществува
            default_company = Company(
                name="Demo Company",
                eik="1234567890",
                bulstat="BG123456789",
                mol_name="System Admin"
            )
            session.add(default_company)
            await session.flush()
            logger.info(f"Създадена default компания: {default_company.id}")
        
        # Винаги създаваме шаблоните (или пресъздаваме)
        logger.info("Създаване на TRZ шаблони...")
        
        # 1. Contract Templates (Шаблони за договори)
        contract_templates_data = [
                {
                    "name": "Трудов договор - пълно работно време",
                    "description": "Стандартен трудов договор с пълно работно време",
                    "contract_type": "full_time",
                    "work_hours_per_week": 40,
                    "probation_months": 6,
                    "salary_calculation_type": "gross",
                    "payment_day": 25,
                    "night_work_rate": 0.5,
                    "overtime_rate": 1.5,
                    "holiday_rate": 2.0,
                },
                {
                    "name": "Трудов договор - непълно работно време",
                    "description": "Трудов договор с намалено работно време",
                    "contract_type": "part_time",
                    "work_hours_per_week": 20,
                    "probation_months": 6,
                    "salary_calculation_type": "gross",
                    "payment_day": 25,
                    "night_work_rate": 0.5,
                    "overtime_rate": 1.5,
                    "holiday_rate": 2.0,
                },
                {
                    "name": "Граждански договор",
                    "description": "Договор за извършване на услуга",
                    "contract_type": "contractor",
                    "work_hours_per_week": 0,
                    "probation_months": 0,
                    "salary_calculation_type": "net",
                    "payment_day": 25,
                    "night_work_rate": 0,
                    "overtime_rate": 1.0,
                    "holiday_rate": 1.0,
                },
            ]
        for template_data in contract_templates_data:
            template = ContractTemplate(
                company_id=default_company.id,
                name=template_data["name"],
                description=template_data["description"],
                contract_type=template_data["contract_type"],
                work_hours_per_week=template_data["work_hours_per_week"],
                probation_months=template_data["probation_months"],
                salary_calculation_type=template_data["salary_calculation_type"],
                payment_day=template_data["payment_day"],
                night_work_rate=template_data["night_work_rate"],
                overtime_rate=template_data["overtime_rate"],
                holiday_rate=template_data["holiday_rate"],
                is_active=True,
            )
            session.add(template)
            await session.flush()
            
            version = ContractTemplateVersion(
                template_id=template.id,
                version=1,
                contract_type=template_data["contract_type"],
                work_hours_per_week=template_data["work_hours_per_week"],
                probation_months=template_data["probation_months"],
                salary_calculation_type=template_data["salary_calculation_type"],
                payment_day=template_data["payment_day"],
                night_work_rate=template_data["night_work_rate"],
                overtime_rate=template_data["overtime_rate"],
                holiday_rate=template_data["holiday_rate"],
                is_current=True,
                created_by="system",
                change_note="Първоначална версия",
            )
            session.add(version)
            await session.flush()
            
            if template_data["contract_type"] == "full_time":
                sections = [
                    {"title": "Предмет на договора", "content": "Настоящият трудов договор се сключва съгласно Кодекса на труда между Работодателя и Работника за изпълнение на работа по определена длъжност - [ДЛЪЖНОСТ], отдел [ОТДЕЛ]. Работникът изпълнява работата лично.", "order_index": 0, "is_required": True},
                    {"title": "Работно време и почивка", "content": "Работникът изпълнява работата си в рамките на 40 часа седмично, при 8-часов работен ден от понеделник до петък. Работодателят осигурява почивка между работните дни съгласно чл. 151 КТ.", "order_index": 1, "is_required": True},
                    {"title": "Заплащане", "content": "За извършената работа Работодателят заплаща на Работника основно трудово възнаграждение в размер на [СУМА] лева, начислявано на брутна / нето основа. Възнаграждението се изплаща до [ДЕН] число на текущия месец.", "order_index": 2, "is_required": True},
                    {"title": "Права и задължения на работодателя", "content": "Работодателят е длъжен да: 1) осигури на Работника работата, за която е сключен договорът; 2) заплаща своевременно трудовото възнаграждение; 3) осигури здравословни и безопасни условия на труд; 4) предостави необходимите материално-технически средства.", "order_index": 3, "is_required": True},
                    {"title": "Права и задължения на работника", "content": "Работникът е длъжен да: 1) изпълнява работата лично и добросъвестно; 2) спазва установения ред в предприятието; 3) изпълнява указанията на работодателя; 4) пази търговската тайна на работодателя; 5) спазва правилата за безопасност и здраве при работа.", "order_index": 4, "is_required": True},
                    {"title": "Клаузи", "content": "1) Изпитателен срок: до 6 месеца съгласно чл. 67 КТ. \n2) Нощен труд: заплаща се с увеличение 0.5% за всеки час съгласно чл. 8 КТ. \n3) Извънреден труд: заплаща се с увеличение 50% съгласно чл. 9 КТ. \n4) Труд по празници: заплаща се с увеличение 100% съгласно чл. 10 КТ.", "order_index": 5, "is_required": True},
                    {"title": "Заключителни разпоредби", "content": "Настоящият договор влиза в сила от [ДАТА НА СКЛЮЧВАНЕ] и е валиден за неопределено време. Всички изменения и допълнения са валидни само в писмена форма. За неуредените въпроси се прилагат разпоредбите на Кодекса на труда и Закona за трудовата миграция и трудовата мобилност.", "order_index": 6, "is_required": True},
                ]
            elif template_data["contract_type"] == "part_time":
                sections = [
                    {"title": "Предмет на договора", "content": "Настоящият трудов договор за непълно работно време се сключва съгласно чл. 138 КТ между Работодателя и Работника за изпълнение на работа по определена длъжност - [ДЛЪЖНОСТ], отдел [ОТДЕЛ]. Работникът изпълнява работата лично.", "order_index": 0, "is_required": True},
                    {"title": "Работно време и почивка", "content": "Работникът изпълнява работата си в рамките на 20 часа седмично, при намален работен ден съгласно чл. 138, ал. 1 КТ. Работното време се разпределя равномерно през работните дни на седмицата.", "order_index": 1, "is_required": True},
                    {"title": "Заплащане", "content": "За извършената работа Работодателят заплаща на Работника основно трудово възнаграждение в размер на [СУМА] лева, съответстващо на 4 часа дневно. Възнаграждението се изплаща пропорционално на отработеното време до [ДЕН] число на текущия месец.", "order_index": 2, "is_required": True},
                    {"title": "Права и задължения на работодателя", "content": "Работодателят е длъжен да: 1) осигури на Работника работата за уговореното работно време; 2) заплаща своевременно трудовото възнаграждение пропорционално на отработеното време; 3) осигури здравословни и безопасни условия на труд; 4) не допуска дискриминация поради непълно работно време.", "order_index": 3, "is_required": True},
                    {"title": "Права и задължения на работника", "content": "Работникът е длъжен да: 1) изпълнява работата лично и добросъвестно; 2) спазва установения ред в предприятието; 3) изпълнява указанията на работодателя в рамките на уговореното работно време; 4) пази търговската тайна на работодателя.", "order_index": 4, "is_required": True},
                    {"title": "Клаузи", "content": "1) Изпитателен срок: до 6 месеца съгласно чл. 67 КТ. \n2) Работникът има право на всички права по КТ, включително платен годишен отпуск, пропорционален на отработеното време (чл. 155 КТ). \n3) Нощен труд: заплаща се с увеличение 0.5% за всеки час. \n4) Извънреден труд: допустим само при условията на чл. 144 КТ.", "order_index": 5, "is_required": True},
                    {"title": "Заключителни разпоредби", "content": "Настоящият договор влиза в сила от [ДАТА НА СКЛЮЧВАНЕ]. Работникът има равни права с работниците на пълно работно време съгласно чл. 138, ал. 3 КТ. За неуредените въпроси се прилагат разпоредбите на Кодекса на труда.", "order_index": 6, "is_required": True},
                ]
            else:
                sections = [
                    {"title": "Предмет на договора", "content": "Настоящият граждански договор (договор за услуга) се сключва по чл. 280 от Закона за задълженията и договорите (ЗЗД) между ВЪЗЛОЖИТЕЛЯ и ИЗПЪЛНИТЕЛЯ за извършване на услугата: [ОПИСАНИЕ НА УСЛУГАТА].", "order_index": 0, "is_required": True},
                    {"title": "Работно време и почивка", "content": "Изпълнителят извършва услугата самостоятелно, без да е обвързан с определено работно време. ВЪЗЛОЖИТЕЛЯТ определя конкретните задачи и срокове за изпълнение. Изпълнителят няма право на почивки по смисъла на КТ.", "order_index": 1, "is_required": True},
                    {"title": "Заплащане", "content": "За извършената услуга ВЪЗЛОЖИТЕЛЯТ заплаща на Изпълнителя възнаграждение в размер на [СУМА] лева, платимо в срок до [ДЕН] дни след приемане на услугата. Възнаграждението е окончателно и не подлежи на осигуровки.", "order_index": 2, "is_required": True},
                    {"title": "Права и задължения на ВЪЗЛОЖИТЕЛЯ", "content": "ВЪЗЛОЖИТЕЛЯТ е длъжен да: 1) предостави на Изпълнителя необходимата информация за изпълнение на услугата; 2) приеме извършената услуга, ако е качествено изпълнена; 3) заплати уговореното възнаграждение в срок.", "order_index": 3, "is_required": True},
                    {"title": "Права и задължения на Изпълнителя", "content": "Изпълнителят е длъжен да: 1) извърши услугата лично и качествено; 2) предаде резултата в уговорения срок; 3) информира ВЪЗЛОЖИТЕЛЯ за хода на работата; 4) пази конфиденциалността на информацията.", "order_index": 4, "is_required": True},
                    {"title": "Клаузи", "content": "1) Срок за изпълнение: [СРОК] от сключване на договора. \n2) Гражданският договор не установява трудови правоотношения и не подлежи на КТ. \n3) При забава от страна на Изпълнителя, ВЪЗЛОЖИТЕЛЯТ може да прекрати договора. \n4) При неизпълнение, страните носят отговорност съгласно ЗЗД.", "order_index": 5, "is_required": True},
                    {"title": "Заключителни разпоредби", "content": "Настоящият договор влиза в сила от датата на подписването му. Всички изменения са валидни само в писмена форма. За неуредените въпроси се прилагат разпоредбите на ЗЗД. Договорът се прекратява с изпълнението на услугата или по взаимно съгласие.", "order_index": 6, "is_required": True},
                ]
            
            for section_data in sections:
                section = ContractTemplateSection(
                    template_id=template.id,
                    version_id=version.id,
                    title=section_data["title"],
                    content=section_data["content"],
                    order_index=section_data["order_index"],
                    is_required=section_data["is_required"],
                )
                session.add(section)

        logger.info("TRZ шаблоните са създадени успешно.")

        # 2. Annex Templates (Шаблони за анекси)
        annex_templates_data = [
            {"name": "Повишение на заплатата", "description": "Повишение на основното трудово възнаграждение", "change_type": "salary"},
            {"name": "Промяна на длъжността", "description": "Промяна на длъжността по трудовия договор", "change_type": "position"},
            {"name": "Промяна на работното време", "description": "Промяна на режима на работа", "change_type": "hours"},
            {"name": "Промяна на надбавки", "description": "Промяна на процентите за нощен труд, извънреден труд и труд по празници", "change_type": "rate"},
        ]
        
        for template_data in annex_templates_data:
            template = AnnexTemplate(
                company_id=default_company.id,
                name=template_data["name"],
                description=template_data["description"],
                change_type=template_data["change_type"],
                is_active=True,
            )
            session.add(template)
            await session.flush()
            
            version = AnnexTemplateVersion(
                template_id=template.id,
                version=1,
                change_type=template_data["change_type"],
                is_current=True,
                created_by="system",
                change_note="Първоначална версия",
            )
            session.add(version)
            await session.flush()
            
            default_sections = [
                {"title": "Описание на промените", "content": "С настоящото споразумение се променят следните условия от трудовия договор:", "order_index": 0, "is_required": True},
                {"title": "Основание", "content": "Настоящото споразумение се сключва на основание чл. 119, ал. 1 от Кодекса на труда.", "order_index": 1, "is_required": False},
            ]
            
            for section_data in default_sections:
                section = AnnexTemplateSection(
                    template_id=template.id,
                    version_id=version.id,
                    title=section_data["title"],
                    content=section_data["content"],
                    order_index=section_data["order_index"],
                    is_required=section_data["is_required"],
                )
                session.add(section)

        # 3. Clause Templates (Библиотека от клаузи)
        clause_templates_data = [
            {"title": "Конфиденциалност", "category": "confidentiality", "content": "Работникът се задължава да не разкрива на трети лица информация, станала му известна при или по повод изпълнението на работата, включително след прекратяване на договора."},
            {"title": "Забрана за конкуренция", "category": "other", "content": "Работникът се задължава да не извършва дейност, конкурентна на работодателя, за срока на договора и 6 месеца след неговото прекратяване."},
            {"title": "Право на обучение", "category": "rights_employee", "content": "Работникът има право на професионално обучение и квалификация, съгласно Закона за професионалното образование и обучение."},
            {"title": "Допълнителен платен отпуск", "category": "rights_employee", "content": "Работникът има право на допълнителен платен отпуск при смърт на брачен партньор или роднина - 2 дни."},
            {"title": "Задължения на работодателя - осигуряване", "category": "rights_employer", "content": "Работодателят е длъжен да осигури на Работника всички необходими лични предпазни средства съгласно изискванията на ЗЗБУТ."},
        ]
        
        for clause_data in clause_templates_data:
            clause = ClauseTemplate(
                company_id=default_company.id,
                title=clause_data["title"],
                content=clause_data["content"],
                category=clause_data["category"],
                is_active=True,
            )
            session.add(clause)
        
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
