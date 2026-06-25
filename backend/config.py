import json
import os
import secrets
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet
from pydantic import computed_field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Get the directory where config.py is located
BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / ".env"


def _ensure_env_key(key_name: str, value: str | None = None, generate: bool = True, key_type: str = "hex") -> str | None:
    """Ensures a key exists in .env file.
    If value is None and generate=True, generates and saves a new key.
    
    Args:
        key_name: Name of the environment variable
        value: Optional existing value
        generate: Whether to generate if not found
        key_type: "hex" for regular secrets, "fernet" for Fernet keys
    Returns:
        The key value

    """
    if value:
        return value

    # Try to read from .env file directly
    if env_path.exists():
        with open(env_path) as f:
            content = f.read()
            for line in content.split("\n"):
                if line.startswith(f"{key_name}=") and not line.strip().startswith("#"):
                    return line.split("=", 1)[1].strip()

    # Generate new key if not found
    if generate:
        if key_type == "fernet":
            new_value = Fernet.generate_key().decode()
        else:
            new_value = secrets.token_hex(32)

        # Append to .env file
        with open(env_path, "a") as f:
            f.write(f"\n# Auto-generated {key_name}\n{key_name}={new_value}\n")
        print(f"Auto-generated {key_name} and saved to .env")
        return new_value

    return None

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=env_path, env_file_encoding="utf-8", extra="ignore")
    DEBUG: bool = False
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "chronosdb"
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432
    # Chronos-specific overrides for backward compatibility
    CHRONOS_DB_USER: str | None = None
    CHRONOS_DB_PASSWORD: str | None = None
    CHRONOS_DB_NAME: str | None = None
    CHRONOS_DB_HOST: str | None = None
    CHRONOS_DB_PORT: int | None = None

    # Secrets - will be loaded from environment if set, otherwise from .env file
    JWT_SECRET_KEY: str | None = None
    ENCRYPTION_KEY: str | None = None
    CSRF_SECRET_KEY: str | None = None
    DEPLOY_API_KEY: str | None = None

    # Application Version
    VERSION: str = "unknown"

    @computed_field
    @property
    def database_url_computed(self) -> str:
        user = self.CHRONOS_DB_USER or self.POSTGRES_USER
        password = self.CHRONOS_DB_PASSWORD or self.POSTGRES_PASSWORD
        db = self.CHRONOS_DB_NAME or self.POSTGRES_DB
        host = self.CHRONOS_DB_HOST or self.POSTGRES_HOST
        port = self.CHRONOS_DB_PORT or self.POSTGRES_PORT
        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"

    # Legacy alias for DATABASE_URL
    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return self.database_url_computed

    @model_validator(mode="after")
    def ensure_secrets(self) -> "Settings":
        """Ensure all secrets are present, generating them if necessary."""
        if not self.JWT_SECRET_KEY:
            self.JWT_SECRET_KEY = _ensure_env_key("JWT_SECRET_KEY")
        if not self.ENCRYPTION_KEY:
            self.ENCRYPTION_KEY = _ensure_env_key("ENCRYPTION_KEY", key_type="fernet")
        if not self.CSRF_SECRET_KEY:
            self.CSRF_SECRET_KEY = _ensure_env_key("CSRF_SECRET_KEY")
        if not self.KIOSK_DEVICE_SECRET:
            self.KIOSK_DEVICE_SECRET = _ensure_env_key("KIOSK_DEVICE_SECRET")
        return self

    def get_deploy_key(self) -> str:
        """Get deploy/update API key with file fallback and auto-rotation support."""
        # 1. Env var (highest priority)
        key = os.environ.get("DEPLOY_API_KEY")
        if key:
            return key.strip()

        # 2. Shared file (production - path from env var)
        key_file = os.environ.get("UPDATE_KEY_FILE", "/project/scripts/update.key")
        if os.path.exists(key_file):
            with open(key_file) as f:
                return f.read().strip()

        # 3. Fallback: generate temporary key
        new_key = secrets.token_hex(32)
        import logging
        logging.getLogger(__name__).warning(
            f"DEPLOY_API_KEY not configured and no update.key found at {key_file}. "
            f"Generated temporary key: {new_key[:8]}...",
        )
        return new_key

    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    COOKIE_SECURE: bool = True  # Set to False for HTTP development
    AUTH_KEY_ROTATION_DAYS: int = 30
    AUTH_KEY_RETENTION_DAYS: int = 90
    BACKEND_CORS_ORIGINS: list[str] | str = []
    TIMEZONE: str = "Europe/Sofia"

    # SMTP Fallback Settings (used only if DB GlobalSettings are missing)
    MAIL_SERVER: str | None = None
    MAIL_PORT: int = 587
    MAIL_USERNAME: str | None = None
    MAIL_PASSWORD: str | None = None
    MAIL_FROM: str | None = None
    MAIL_FROM_NAME: str = "Chronos ERP System"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    USE_CREDENTIALS: bool = True
    FRONTEND_URL: str = "http://localhost:5173"
    API_URL: str = "http://localhost:8000"
    # QR Code Settings
    QR_TOKEN_REGEN_MINUTES: int = 15

    KIOSK_DEVICE_SECRET: str | None = None

    # Session Settings
    SESSION_MAX_AGE_HOURS: int = 12

    # Google Calendar Integration
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    GOOGLE_REDIRECT_URI: str | None = None
    GOOGLE_CALENDAR_WEBHOOK_SECRET: str | None = None
    GOOGLE_SYNC_ENABLED: bool = True
    GOOGLE_SYNC_BATCH_SIZE: int = 50
    GOOGLE_SYNC_RETRY_ATTEMPTS: int = 3
    GOOGLE_SYNC_TIMEOUT_SECONDS: int = 30

    @model_validator(mode="after")
    def set_derived_urls(self) -> "Settings":
        if not self.GOOGLE_REDIRECT_URI:
            self.GOOGLE_REDIRECT_URI = f"{self.FRONTEND_URL}/auth/google/callback"
        return self

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        if isinstance(v, str) and v.startswith("["):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                # Fallback for Python-style lists with single quotes
                return [i.strip().strip("'\"") for i in v.strip("[]").split(",")]
        elif isinstance(v, list):
            return v
        raise ValueError(v)


from pydantic_settings import BaseSettings, SettingsConfigDict


class SeedSettings:
    SEED_VERSION: int = 2
    MODULES: list[dict] = [
        {"code": "shifts", "name": "Смени и работно време", "desc": "Управление на работно време, смени и присъствие"},
        {"code": "salaries", "name": "Заплати", "desc": "Изчисляване на заплати, ТРЗ и договори"},
        {"code": "kiosk", "name": "Kiosk терминал", "desc": "Управление на физически терминали и QR чекиране"},
        {"code": "integrations", "name": "Интеграции", "desc": "Google Calendar, Webhooks и външни услуги"},
        {"code": "confectionery", "name": "Сладкарско производство и Склад", "desc": "Управление на склад (FEFO), Рецептурник и Производствени станции"},
        {"code": "accounting", "name": "Счетоводство и Фактуриране", "desc": "Управление на фактури, доставчици и разплащания"},
        {"code": "notifications", "name": "Уведомления и Кореспонденция", "desc": "SMTP настройки, имейл справки и автоматични известия"},
        {"code": "fleet", "name": "Автопарк", "desc": "Управление на автомобили, горива, ремонти, винетки и пътни карти"},
        {"code": "cost_centers", "name": "Разходни центрове", "desc": "Управление на разходни центрове за финансово проследяване"},
        {"code": "inventory", "name": "Инвентаризация", "desc": "Инвентаризационни сесии и баркод сканиране"},
        {"code": "behavioral_analysis", "name": "Поведенчески анализ", "desc": "4-слоен поведенчески анализ с динамични правила, XAI и bias detection"},
    ]
    CONTRACT_TEMPLATES: list[dict] = [
        {"name": "Трудов договор - пълно работно време", "description": "Стандартен трудов договор с пълно работно време", "contract_type": "full_time", "work_hours_per_week": 40, "probation_months": 6, "salary_calculation_type": "gross", "payment_day": 25, "night_work_rate": 0.5, "overtime_rate": 1.5, "holiday_rate": 2.0},
        {"name": "Трудов договор - непълно работно време", "description": "Трудов договор с намалено работно време", "contract_type": "part_time", "work_hours_per_week": 20, "probation_months": 6, "salary_calculation_type": "gross", "payment_day": 25, "night_work_rate": 0.5, "overtime_rate": 1.5, "holiday_rate": 2.0},
        {"name": "Граждански договор", "description": "Договор за извършване на услуга", "contract_type": "contractor", "work_hours_per_week": 0, "probation_months": 0, "salary_calculation_type": "net", "payment_day": 25, "night_work_rate": 0, "overtime_rate": 1.0, "holiday_rate": 1.0},
    ]
    ANNEX_TEMPLATES: list[dict] = [
        {"name": "Повишение на заплатата", "description": "Повишение на основното трудово възнаграждение", "change_type": "salary"},
        {"name": "Промяна на длъжността", "description": "Промяна на длъжността по трудовия договор", "change_type": "position"},
        {"name": "Промяна на работното време", "description": "Промяна на режима на работа", "change_type": "hours"},
        {"name": "Промяна на надбавки", "description": "Промяна на процентите за нощен труд, извънреден труд и труд по празници", "change_type": "rate"},
    ]
    CLAUSE_TEMPLATES: list[dict] = [
        {"title": "Конфиденциалност", "category": "confidentiality", "content": "Работникът се задължава да не разкрива на трети лица информация, станала му известна при или по повод изпълнението на работата, включително след прекратяване на договора."},
        {"title": "Забрана за конкуренция", "category": "other", "content": "Работникът се задължава да не извършва дейност, конкурентна на работодателя, за срока на договора и 6 месеца след неговото прекратяване."},
        {"title": "Право на обучение", "category": "rights_employee", "content": "Работникът има право на професионално обучение и квалификация, съгласно Закона за професионалното образование и обучение."},
        {"title": "Допълнителен платен отпуск", "category": "rights_employee", "content": "Работникът има право на допълнителен платен отпуск при смърт на брачен партньор или роднина - 2 дни."},
        {"title": "Задължения на работодателя - осигуряване", "category": "rights_employer", "content": "Работодателят е длъжен да осигури на Работника всички необходими лични предпазни средства съгласно изискванията на ЗЗБУТ."},
    ]
    GLOBAL_SETTINGS: dict[str, str] = {
        "payroll_noi_compensation_percent": "80.0",
        "payroll_employer_paid_sick_days": "2",
        "payroll_default_tax_resident": "true",
        "trz_compliance_strict_mode": "false",
        "payroll_doo_employee_rate": "14.3",
        "payroll_doo_employer_rate": "14.3",
        "payroll_doo_older_employee_rate": "19.3",
        "payroll_doo_older_employer_rate": "19.3",
        "payroll_zo_employee_rate": "3.2",
        "payroll_zo_employer_rate": "4.8",
        "payroll_dzpo_employee_rate": "2.2",
        "payroll_dzpo_employer_rate": "2.8",
        "payroll_tzpb_rate": "0.4",
        "payroll_income_tax_rate": "10",
        "payroll_standard_deduction": "500",
        "payroll_max_insurable_base": "4100",
        "payroll_min_wage": "1213",
        "payroll_auto_night_work": "false",
        "payroll_auto_overtime": "false",
        "payroll_auto_holiday": "false",
        "payroll_night_hourly_supplement": "0.15",
        "payroll_overtime_rate": "50",
        "payroll_holiday_rate": "100",
        "payroll_annual_leave_days": "20",
        "payroll_sick_day_1_rate": "70",
        "payroll_sick_days_covered_by_employer": "2",
        "payroll_maternity_days": "410",
        "payroll_paternity_days": "15",
        "qr_token_regen_minutes": "15",
        "pwd_min_length": "8",
        "pwd_max_length": "32",
        "pwd_require_upper": "false",
        "pwd_require_lower": "false",
        "pwd_require_digit": "false",
        "pwd_require_special": "false",
        "password_settings_version": "1",
        "kiosk_validate_code_rate_limit": "5/minute",
    }
    WORKSTATIONS: list[dict] = [
        {"name": "Пекарна", "description": "Изпичане на блатове и основи"},
        {"name": "Кремове", "description": "Приготвяне на кремове и пълнежи"},
        {"name": "Декорация", "description": "Украса на готовите изделия"},
    ]
    CONTRACT_SECTIONS: dict[str, list[dict]] = {
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
    ANNEX_SECTIONS: list[dict] = [
        {"title": "Описание на промените", "content": "С настоящото споразумение се променят следните условия от трудовия договор:", "order_index": 0, "is_required": True},
        {"title": "Основание", "content": "Настоящото споразумение се сключва на основание чл. 119, ал. 1 от Кодекса на труда.", "order_index": 1, "is_required": False},
    ]


settings = Settings()
