Общ Преглед на Системата
Технологичен Стек
- Backend: FastAPI, PostgreSQL, SQLAlchemy, GraphQL (Strawberry)
- Frontend: React 19.2, TypeScript, Material-UI, Apollo Client
- Инфраструктура: Docker, Nginx, JWT Authentication
Съществуващи Функционалности
- JWT-based автентикация с role система (admin/user)
- 3-етажна организационна структура (Company/Department/Position)
- Sophisticated payroll calculator (556 реда код)
- Shift management с swap system
- Time tracking с geofencing
- FullCalendar интеграция
- Audit logging система
---
Фаза 1: RBAC Система с Фирмени Администратори (2-3 седмици)
Основна Концепция
Трансформация от двоична admin/user система към пълна Role-Based Access Control с company-scoped достъп.
Нови Модели в Базата Данни
-- Основни RBAC таблици
CREATE TABLE permissions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,  -- "users:read", "payroll:create"
    resource VARCHAR(50) NOT NULL,       -- "users", "payroll", "schedules"
    action VARCHAR(50) NOT NULL,         -- "read", "create", "update", "delete"
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(resource, action)
);
CREATE TABLE role_permissions (
    id SERIAL PRIMARY KEY,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id INTEGER NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    granted_at TIMESTAMP DEFAULT NOW(),
    granted_by INTEGER REFERENCES users(id),
    UNIQUE(role_id, permission_id)
);
-- Company scoping за роли
CREATE TABLE company_role_assignments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT NOW(),
    assigned_by INTEGER REFERENCES users(id),
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(user_id, company_id, role_id)
);
-- Permission cache за performance
CREATE TABLE user_permission_cache (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    permission_name VARCHAR(100) NOT NULL,
    granted_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    INDEX(user_id, company_id, permission_name),
    INDEX(expires_at)
);
-- Audit trail за permission decisions
CREATE TABLE permission_audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50),
    resource_id INTEGER,
    permission VARCHAR(100),
    decision VARCHAR(20) NOT NULL, -- 'GRANTED' or 'DENIED'
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
Пълен Списък с Права (45+ права)
PERMISSIONS = {
    # User Management
    "users:read": {"resource": "users", "action": "read", "description": "Преглед на потребителска информация"},
    "users:read_own": {"resource": "users", "action": "read_own", "description": "Преглед на собствена информация"},
    "users:create": {"resource": "users", "action": "create", "description": "Създаване на нови потребители"},
    "users:update": {"resource": "users", "action": "update", "description": "Редактиране на потребители"},
    "users:update_own": {"resource": "users", "action": "update_own", "description": "Редактиране на собствен профил"},
    "users:delete": {"resource": "users", "action": "delete", "description": "Изтриване на потребители"},
    "users:manage_roles": {"resource": "users", "action": "manage_roles", "description": "Възлагане на роли"},
    
    # Time Management
    "timelogs:read": {"resource": "timelogs", "action": "read", "description": "Преглед на time logs"},
    "timelogs:read_own": {"resource": "timelogs", "action": "read_own", "description": "Преглед на собствени time logs"},
    "timelogs:create": {"resource": "timelogs", "action": "create", "description": "Създаване на time logs"},
    "timelogs:create_own": {"resource": "timelogs", "action": "create_own", "description": "Clock in/out за себе си"},
    "timelogs:update": {"resource": "timelogs", "action": "update", "description": "Модифициране на time logs"},
    "timelogs:delete": {"resource": "timelogs", "action": "delete", "description": "Изтриване на time logs"},
    "timelogs:admin_create": {"resource": "timelogs", "action": "admin_create", "description": "Създаване на time logs за други"},
    
    # Schedule Management
    "schedules:read": {"resource": "schedules", "action": "read", "description": "Преглед на графици"},
    "schedules:read_own": {"resource": "schedules", "action": "read_own", "description": "Преглед на собствен график"},
    "schedules:create": {"resource": "schedules", "action": "create", "description": "Създаване на графици"},
    "schedules:update": {"resource": "schedules", "action": "update", "description": "Редактиране на графици"},
    "schedules:delete": {"resource": "schedules", "action": "delete", "description": "Изтриване на графици"},
    "schedules:approve_swaps": {"resource": "schedules", "action": "approve_swaps", "description": "Одобряване на смяна на смени"},
    
    # Payroll Management
    "payroll:read": {"resource": "payroll", "action": "read", "description": "Преглед на възнаграждения"},
    "payroll:read_own": {"resource": "payroll", "action": "read_own", "description": "Преглед на собствени възнаграждения"},
    "payroll:create": {"resource": "payroll", "action": "create", "description": "Създаване на възнаграждения"},
    "payroll:update": {"resource": "payroll", "action": "update", "description": "Редактиране на възнаграждения"},
    "payroll:delete": {"resource": "payroll", "action": "delete", "description": "Изтриване на възнаграждения"},
    "payroll:export": {"resource": "payroll", "action": "export", "description": "Експорт на данни за възнаграждения"},
    
    # Leave Management
    "leaves:read": {"resource": "leaves", "action": "read", "description": "Преглед на молби за отпуск"},
    "leaves:read_own": {"resource": "leaves", "action": "read_own", "description": "Преглед на собствени молби за отпуск"},
    "leaves:create": {"resource": "leaves", "action": "create", "description": "Създаване на молби за отпуск"},
    "leaves:create_own": {"resource": "leaves", "action": "create_own", "description": "Създаване на собствени молби за отпуск"},
    "leaves:approve": {"resource": "leaves", "action": "approve", "description": "Одобряване/отказване на молби за отпуск"},
    "leaves:update": {"resource": "leaves", "action": "update", "description": "Редактиране на молби за отпуск"},
    "leaves:delete": {"resource": "leaves", "action": "delete", "description": "Изтриване на молби за отпуск"},
    
    # Company Management
    "companies:read": {"resource": "companies", "action": "read", "description": "Преглед на информация за фирми"},
    "companies:create": {"resource": "companies", "action": "create", "description": "Създаване на фирми"},
    "companies:update": {"resource": "companies", "action": "update", "description": "Редактиране на фирми"},
    "companies:delete": {"resource": "companies", "action": "delete", "description": "Изтриване на фирми"},
    "companies:manage_users": {"resource": "companies", "action": "manage_users", "description": "Управление на потребители във фирма"},
    
    # System Administration
    "system:backup": {"resource": "system", "action": "backup", "description": "Създаване на системни бекъпи"},
    "system:restore": {"resource": "system", "action": "restore", "description": "Възстановяване от бекъп"},
    "system:read_audit": {"resource": "system", "action": "read_audit", "description": "Преглед на audit логове"},
    "system:manage_settings": {"resource": "system", "action": "manage_settings", "description": "Управление на системни настройки"},
    "system:manage_roles": {"resource": "system", "action": "manage_roles", "description": "Управление на роли и права"},
    
    # Reports & Analytics
    "reports:read": {"resource": "reports", "action": "read", "description": "Преглед на справки"},
    "reports:create": {"resource": "reports", "action": "create", "description": "Генериране на справки"},
    "reports:export": {"resource": "reports", "action": "export", "description": "Експорт на справки"},
    "analytics:read": {"resource": "analytics", "action": "read", "description": "Преглед на анализи"},
    
    # Calendar Integration
    "calendar:connect": {"resource": "calendar", "action": "connect", "description": "Свързване на календар"},
    "calendar:sync": {"resource": "calendar", "action": "sync", "description": "Синхронизация на календар"},
    "calendar:manage_settings": {"resource": "calendar", "action": "manage_settings", "description": "Управление на настройки на календар"},
    "calendar:admin": {"resource": "calendar", "action": "admin", "description": "Администрация на календар"},
}
Роля Йерархия
DEFAULT_ROLES = {
    "super_admin": {
        "description": "Супер Администратор с пълен системен достъп",
        "priority": 100,
        "is_system_role": True,
        "permissions": list(PERMISSIONS.keys())  # Всички права
    },
    "company_admin": {
        "description": "Фирмен Администратор с company-scoped достъп",
        "priority": 80,
        "permissions": [
            "users:read", "users:create", "users:update", "users:delete", "users:manage_roles",
            "timelogs:read", "timelogs:admin_create", "timelogs:update", "timelogs:delete",
            "schedules:read", "schedules:create", "schedules:update", "schedules:delete", "schedules:approve_swaps",
            "payroll:read", "payroll:create", "payroll:update", "payroll:export",
            "leaves:read", "leaves:approve", "leaves:update", "leaves:delete",
            "companies:read", "companies:update", "companies:manage_users",
            "reports:read", "reports:create", "reports:export", "analytics:read",
            "calendar:admin"
        ]
    },
    "hr_manager": {
        "description": "HR Мениджър с права за управление на персонал",
        "priority": 60,
        "permissions": [
            "users:read", "users:create", "users:update", "users:manage_roles",
            "timelogs:read", "timelogs:admin_create",
            "schedules:read", "schedules:create", "schedules:update", "schedules:approve_swaps",
            "payroll:read", "payroll:create", "payroll:update",
            "leaves:read", "leaves:approve", "leaves:update",
            "reports:read", "reports:create", "analytics:read",
        ]
    },
    "manager": {
        "description": "Мениджър с права за oversite на екип",
        "priority": 50,
        "permissions": [
            "users:read",  # Само за екипа
            "timelogs:read", "timelogs:admin_create",  # За екипа
            "schedules:read", "schedules:create", "schedules:update", "schedules:approve_swaps",
            "payroll:read",
            "leaves:read", "leaves:approve",
            "reports:read", "analytics:read",
        ]
    },
    "employee": {
        "description": "Стандартен служител със self-service права",
        "priority": 20,
        "permissions": [
            "users:read_own", "users:update_own",
            "timelogs:read_own", "timelogs:create_own",
            "schedules:read_own",
            "payroll:read_own",
            "leaves:read_own", "leaves:create_own",
            "calendar:connect", "calendar:sync", "calendar:manage_settings"
        ]
    },
    "viewer": {
        "description": "Read-only достъп за аудитори и контрактори",
        "priority": 10,
        "permissions": [
            "timelogs:read_own",
            "schedules:read_own",
            "payroll:read_own",
            "leaves:read_own",
        ]
    }
}
JWT Token Structure Промени
# Нов Enhanced JWT Payload
access_payload = {
    "iss": "chronos-api",
    "sub": email,
    "iat": int(now.timestamp()),
    "exp": int((now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()),
    "jti": access_jti,
    "type": "access",
    "uid": user_id,
    
    # RBAC данни
    "permissions": [
        "users:read_own",
        "timelogs:create_own",
        "schedules:read_own",
        "payroll:read_own",
        "leaves:create_own"
    ],
    "companies": [
        {
            "id": 1,
            "name": "Company A",
            "role": "employee",
            "permissions": ["users:read_own", "timelogs:create_own"]
        }
    ],
    "primary_role": "employee",
    "role_hierarchy": ["employee", "viewer"],
    "company_id": 1,  # Primary компания
    "permission_version": 1,  # За cache invalidation
}
Критични Файлове за Промяна
1. /backend/auth/jwt_utils.py
- Добавяне на permissions към JWT payload
- Integration с PermissionService за кеширане
2. /backend/auth/rbac_middleware.py (нов файл)
- PermissionService клас с multi-level caching
- require_permission decorator за лесна употреба
- Company-scoped permission checks
- Audit logging за всички permission decisions
3. /backend/graphql/queries.py
- Замяна на 100+ admin checks с permission-based checks
- Integration с RBAC middleware
4. Frontend компоненти
- usePermissions hook за React
- PermissionGuard компонент за conditional rendering
- Permission-aware menu и navigation
---
Фаза 2: Google Calendar Интеграция (1-2 седмици)
Основна Концепция
Two-way синхронизация между вътрешния scheduling system и Google Calendar с гранулиран контрол.
Нови Модели
-- Google Calendar Integration
CREATE TABLE google_calendar_accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    google_user_id VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    access_token TEXT,
    refresh_token TEXT NOT NULL,
    token_expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT sofia_now(),
    updated_at TIMESTAMP DEFAULT sofia_now(),
    UNIQUE(user_id, google_user_id)
);
CREATE TABLE google_calendar_sync_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    calendar_id VARCHAR(255) NOT NULL DEFAULT 'primary',
    sync_work_schedules BOOLEAN DEFAULT TRUE,
    sync_time_logs BOOLEAN DEFAULT FALSE,
    sync_leave_requests BOOLEAN DEFAULT TRUE,
    sync_public_holidays BOOLEAN DEFAULT TRUE,
    sync_direction VARCHAR(20) DEFAULT 'to_google', -- 'to_google', 'from_google', 'bidirectional'
    sync_frequency_minutes INTEGER DEFAULT 15,
    privacy_level VARCHAR(20) DEFAULT 'title_only', -- 'full', 'title_only', 'busy_only'
    default_event_visibility VARCHAR(20) DEFAULT 'default', -- 'default', 'public', 'private'
    timezone VARCHAR(50) DEFAULT 'Europe/Sofia',
    created_at TIMESTAMP DEFAULT sofia_now(),
    updated_at TIMESTAMP DEFAULT sofia_now(),
    UNIQUE(user_id)
);
CREATE TABLE google_calendar_events (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    google_event_id VARCHAR(255) NOT NULL,
    google_calendar_id VARCHAR(255) NOT NULL,
    source_type VARCHAR(50) NOT NULL, -- 'work_schedule', 'time_log', 'leave_request', 'holiday'
    source_id INTEGER NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    is_all_day BOOLEAN DEFAULT FALSE,
    google_updated_at TIMESTAMP,
    last_sync_at TIMESTAMP DEFAULT sofia_now(),
    sync_status VARCHAR(20) DEFAULT 'synced', -- 'synced', 'pending', 'error', 'deleted'
    sync_error TEXT,
    created_at TIMESTAMP DEFAULT sofia_now(),
    UNIQUE(user_id, google_event_id)
);
CREATE TABLE google_sync_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    sync_type VARCHAR(50) NOT NULL, -- 'full_sync', 'incremental', 'error_retry'
    events_processed INTEGER DEFAULT 0,
    events_created INTEGER DEFAULT 0,
    events_updated INTEGER DEFAULT 0,
    events_deleted INTEGER DEFAULT 0,
    errors_count INTEGER DEFAULT 0,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'running', -- 'running', 'completed', 'failed'
    error_details TEXT,
    created_at TIMESTAMP DEFAULT sofia_now()
);
Service Architecture
GoogleCalendarService Клас
- OAuth 2.0 flow implementation с refresh tokens
- Event formatting за всеки тип (WorkSchedule, TimeLog, LeaveRequest)
- Batch processing за API rate limiting
- Automatic token refresh
- Multi-timezone support
Background Sync Job
- Process всички потребители с Google integration
- Incremental sync (последните 30 дни + следващите 90 дни)
- Error handling и exponential backoff retry logic
- Performance optimized с batch queries
Privacy Levels
# Примери за privacy formatting
def format_work_schedule_event(self, schedule, user, privacy_level='title_only'):
    title = f"Work: {schedule.shift.name}"
    description = f"Shift: {schedule.shift.name}\nTime: {schedule.shift.start_time} - {schedule.shift.end_time}"
    
    if privacy_level == 'busy_only':
        title = "Busy"
        description = ""
    elif privacy_level == 'title_only':
        description = f"Shift: {schedule.shift.name}"
    
    return {
        'summary': title,
        'description': description,
        'start': {'dateTime': start_datetime.isoformat()},
        'end': {'dateTime': end_datetime.isoformat()},
        'extendedProperties': {
            'private': {
                'source': 'chronos_worktime',
                'source_type': 'work_schedule',
                'source_id': str(schedule.id)
            }
        }
    }
Frontend Components
GoogleCalendarSettings.tsx
- OAuth flow UI
- Sync settings configuration
- Privacy level controls
- Sync status monitoring
- Manual sync triggers
Security Measures
- Encrypted storage на refresh tokens
- Automatic token rotation
- Audit logging на всички sync операции
- Rate limiting и error handling
- User consent management
---
Фаза 3: Нова Система за Възнаграждения (3-4 седмици) - Разширена
Основна Концепция
Пълна реорганизация на системата за възнаграждения с поддръжка на трудови договори, граждански договори и всички законови изисквания.
Нови Модели
-- Договори
CREATE TABLE employment_contracts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    contract_type VARCHAR(50) NOT NULL, -- 'full_time', 'part_time', 'contractor', 'internship'
    contract_number VARCHAR(100),
    start_date DATE NOT NULL,
    end_date DATE, -- NULL за безсрочни договори
    base_salary NUMERIC(12, 2), -- Бруто основна заплата
    work_hours_per_week INTEGER DEFAULT 40,
    work_days_per_week INTEGER DEFAULT 5,
    probation_months INTEGER DEFAULT 0,
    position_id INTEGER REFERENCES positions(id),
    department_id INTEGER REFERENCES departments(id),
    tax_regime VARCHAR(50) DEFAULT 'standard', -- 'standard', 'minimum_wage', 'pensioner', 'disabled'
    insurance_regime VARCHAR(50) DEFAULT 'full', -- 'full', 'reduced', 'exempt'
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT sofia_now(),
    updated_at TIMESTAMP DEFAULT sofia_now(),
    created_by INTEGER REFERENCES users(id)
);
-- Периоди на обработка на заплати
CREATE TABLE payroll_periods (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    payment_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'draft', -- 'draft', 'processing', 'approved', 'paid', 'closed'
    total_gross_amount NUMERIC(15, 2) DEFAULT 0,
    total_net_amount NUMERIC(15, 2) DEFAULT 0,
    total_tax_amount NUMERIC(15, 2) DEFAULT 0,
    total_insurance_amount NUMERIC(15, 2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT sofia_now(),
    updated_at TIMESTAMP DEFAULT sofia_now(),
    processed_by INTEGER REFERENCES users(id),
    approved_by INTEGER REFERENCES users(id),
    UNIQUE(company_id, start_date, end_date)
);
-- Разширени payslip записи
CREATE TABLE payslip_details (
    id SERIAL PRIMARY KEY,
    payslip_id INTEGER REFERENCES payslips(id) ON DELETE CASCADE,
    contract_id INTEGER REFERENCES employment_contracts(id),
    
    -- Базови данни
    base_salary NUMERIC(12, 2),
    worked_days INTEGER,
    overtime_hours NUMERIC(8, 2),
    overtime_rate NUMERIC(5, 2),
    
    -- Добавки
    bonus_amount NUMERIC(10, 2) DEFAULT 0,
    seniority_bonus NUMERIC(10, 2) DEFAULT 0,
    performance_bonus NUMERIC(10, 2) DEFAULT 0,
    night_shift_bonus NUMERIC(10, 2) DEFAULT 0,
    holiday_bonus NUMERIC(10, 2) DEFAULT 0,
    other_additions NUMERIC(10, 2) DEFAULT 0,
    
    -- Дедукции
    advance_payments NUMERIC(10, 2) DEFAULT 0,
    penalty_amount NUMERIC(10, 2) DEFAULT 0,
    other_deductions NUMERIC(10, 2) DEFAULT 0,
    
    -- Осигуровки
    health_insurance NUMERIC(10, 2) DEFAULT 0, -- 8.33% (служител)
    pension_insurance NUMERIC(10, 2) DEFAULT 0, -- 7.71% (служител)
    unemployment_insurance NUMERIC(10, 2) DEFAULT 0, -- 1.2% (служител)
    additional_insurance NUMERIC(10, 2) DEFAULT 0, -- Допълнителни осигуровки
    
    -- Данъци
    income_tax NUMERIC(10, 2) DEFAULT 0, -- 10% данък общ доход
    
    -- Болнични данни
    sick_days_used INTEGER DEFAULT 0,
    sick_days_paid_by_nss INTEGER DEFAULT 0,
    sick_days_paid_by_employer INTEGER DEFAULT 0,
    sick_pay_percentage NUMERIC(5, 2) DEFAULT 70.0, -- Процент за първите 3 дни
    
    -- Финални суми
    gross_amount NUMERIC(12, 2),
    taxable_amount NUMERIC(12, 2),
    tax_amount NUMERIC(10, 2),
    insurance_amount NUMERIC(10, 2),
    net_amount NUMERIC(12, 2),
    
    created_at TIMESTAMP DEFAULT sofia_now(),
    updated_at TIMESTAMP DEFAULT sofia_now()
);
-- Допълнителни одръжки
CREATE TABLE additional_allowances (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    allowance_type VARCHAR(50) NOT NULL, -- 'transport', 'meal', 'phone', 'representation', 'housing', 'other'
    amount NUMERIC(10, 2) NOT NULL,
    is_taxable BOOLEAN DEFAULT TRUE,
    is_insurable BOOLEAN DEFAULT FALSE,
    frequency VARCHAR(20) DEFAULT 'monthly', -- 'monthly', 'once', 'custom'
    start_date DATE NOT NULL,
    end_date DATE,
    description TEXT,
    created_at TIMESTAMP DEFAULT sofia_now(),
    created_by INTEGER REFERENCES users(id),
    is_active BOOLEAN DEFAULT TRUE
);
-- Данни за болнични
CREATE TABLE sick_leave_records (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    total_days INTEGER NOT NULL,
    sick_leave_type VARCHAR(20) NOT NULL, -- 'general', 'work_injury', 'maternity', 'child_care'
    is_nss_covered BOOLEAN DEFAULT TRUE,
    employer_covered_days INTEGER DEFAULT 3, -- Първите 3 дни за сметка на работодателя
    employer_payment_percentage NUMERIC(5, 2) DEFAULT 75.0, -- Процент за първите дни
    nss_payment_percentage NUMERIC(5, 2) DEFAULT 80.0, -- Процент от НОЙ
    doctor_note_number VARCHAR(100),
    doctor_name VARCHAR(200),
    hospital_name VARCHAR(200),
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'approved', 'rejected', 'processed'
    created_at TIMESTAMP DEFAULT sofia_now(),
    approved_by INTEGER REFERENCES users(id),
    processed_in_payroll_id INTEGER REFERENCES payroll_periods(id)
);
-- Авансови плащания
CREATE TABLE advance_payments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    amount NUMERIC(10, 2) NOT NULL,
    payment_date DATE NOT NULL,
    reason VARCHAR(500),
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'approved', 'paid', 'deducted'
    deduct_from_payroll_id INTEGER REFERENCES payroll_periods(id),
    approved_by INTEGER REFERENCES users(id),
    paid_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT sofia_now()
);
-- Плащания
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    payslip_id INTEGER REFERENCES payslips(id) ON DELETE CASCADE,
    payroll_period_id INTEGER REFERENCES payroll_periods(id),
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    amount NUMERIC(12, 2) NOT NULL,
    payment_date DATE,
    payment_method VARCHAR(20) DEFAULT 'bank_transfer', -- 'bank_transfer', 'cash', 'check'
    payment_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    bank_account VARCHAR(50),
    reference_number VARCHAR(100),
    transaction_id VARCHAR(200),
    notes TEXT,
    created_at TIMESTAMP DEFAULT sofia_now(),
    updated_at TIMESTAMP DEFAULT sofia_now()
);
Два Типа Договори
1. Трудов Договор (Standard Labor Contract)
class LaborContractConfig:
    # Законови изисквания по Кодекса на труда
    MINIMUM_WAGE = 933.00  # Минимална работна заплата за 2026 г.
    STANDARD_WORK_HOURS_WEEKLY = 40
    MAXIMUM_OVERTIME_HOURS_YEARLY = 150
    
    # Осигуровки (служител)
    HEALTH_INSURANCE_RATE = 8.33  # 13.78% общо, 8.33% служител
    PENSION_INSURANCE_RATE = 7.71  # 7.71% служител
    UNEMPLOYMENT_INSURANCE_RATE = 1.2  # 1.2% служител
    
    # Осигуровки (работодател)
    EMPLOYER_HEALTH_INSURANCE_RATE = 5.45  # 13.78% общо, 5.45% работодател
    EMPLOYER_PENSION_INSURANCE_RATE = 10.92  # 18.63% общо, 10.92% работодател
    EMPLOYER_UNEMPLOYMENT_INSURANCE_RATE = 0.7  # 1.9% общо, 0.7% работодател
    ACCIDENT_INSURANCE_RATE = 0.4  # 0.4% - 1.8% според категория
    
    # Данъци
    INCOME_TAX_RATE = 0.10  # 10% данък общ доход
    MINIMUM_TAXABLE_BASE = 933.00  # Минимална осигурителна основа
    
    # Болнични
    EMPLOYER_SICK_DAYS = 3  # Първите 3 дни
    EMPLOYER_SICK_PAY_RATE = 0.75  # 75% за първите дни
    NSS_SICK_PAY_RATE = 0.80  # 80% от 4-тия ден нататък
    
    # Отпуски
    MINIMUM_PAID_LEAVE_DAYS = 20  # Минимум 20 дни платен отпуск
    MAXIMUM_UNPAID_LEAVE_DAYS = 30  # Максимум 30 дни неплатен отпуск
2. Граждански Договор (Civil Contract)
class CivilContractConfig:
    # Осигуровки - по избор на договарящите страни
    OPTIONAL_HEALTH_INSURANCE = 3.55  # По избор
    OPTIONAL_PENSION_INSURANCE = 5.0  # По избор
    
    # Данъци
    INCOME_TAX_RATE = 0.10  # 10% данък
    MONTHLY_TAX_THRESHOLD = 3000.00  # Праг за месечно облагане
    
    # Гъвкави параметри
    FLEXIBLE_WORKING_HOURS = True
    NO_MAXIMUM_WORK_HOURS = True
    NO_OVERTIME_RESTRICTIONS = True
    
    # Допълнителни одръжки
    ALLOW_ALL_ALLOWANCES = True  # Всички видове одръжки са допустими
    NO_INSURANCE_REQUIREMENTS = True  # Без задължителни осигуровки
Болничен Система по Българско Законодателство
class BulgarianSickLeaveSystem:
    """
    Реална имплементация на болнични според Кодекса за социално осигуряване
    """
    
    def __init__(self):
        # Конфигурация според закона
        self.EMPLOYER_COVERED_DAYS = 3  # Първите 3 дни
        self.EMPLOYER_PAYMENT_RATE = 0.75  # 75% от среднодневното възнаграждение
        self.NSS_PAYMENT_RATE = 0.80  # 80% от среднодневното възнаграждение от 4-тия ден
        
        # Специални случаи
        self.WORK_INJURY_RATE = 0.90  # 90% за трудова злополука
        self.MATERNITY_RATE = 0.90  # 90% за майчинство
        self.MINIMUM_SICK_PAY = 14.70  # Минимален размер на дневно парично обезщетение
    
    def calculate_sick_pay(self, contract, sick_days):
        """Изчисляване на болнично обезщетение"""
        
        # Среднодневно възнаграждение
        daily_average = self.calculate_daily_average(contract)
        
        # Минимално обезщетение според закона
        daily_minimum = max(self.MINIMUM_SICK_PAY, daily_average)
        
        # Изчисляване на плащания
        total_employer_days = min(sick_days.total_days, self.EMPLOYER_COVERED_DAYS)
        total_nss_days = max(0, sick_days.total_days - self.EMPLOYER_COVERED_DAYS)
        
        # Плащане от работодател (първи 3 дни)
        employer_amount = 0
        if sick_days.employer_payment_percentage == 75:
            employer_amount = total_employer_days * daily_minimum * 0.75
        elif sick_days.employer_payment_percentage == 100:
            employer_amount = total_employer_days * daily_minimum
        
        # Плащане от НОЙ (от 4-тия ден)
        nss_amount = total_nss_days * daily_minimum * 0.80
        
        return {
            'employer_days': total_employer_days,
            'employer_amount': employer_amount,
            'nss_days': total_nss_days,
            'nss_amount': nss_amount,
            'total_amount': employer_amount + nss_amount,
            'daily_average': daily_average,
            'daily_minimum': daily_minimum
        }
    
    def calculate_daily_average(self, contract):
        """Изчисляване на среднодневно възнаграждение за болнични"""
        
        # Вземане на възнагражденията от последните 12 месеца
        last_12_months_payslips = self.get_last_12_months_payslips(contract.user_id)
        
        if not last_12_months_payslips:
            return self.MINIMUM_SICK_PAY
        
        # Изключване на непериодичните плащания (аванси, премии и др.)
        total_amount = sum(p.gross_amount for p in last_12_months_payslips 
                          if not p.is_bonus and not p.is_advance)
        
        # Средномесечно възнаграждение
        monthly_average = total_amount / len(last_12_months_payslips)
        
        # Среднодневно възнаграждение
        daily_average = monthly_average / 30  # Според закона се дели на 30
        
        return max(daily_average, self.MINIMUM_SICK_PAY)
Enhanced Payroll Calculator
class AdvancedPayrollCalculator(PayrollCalculator):
    """
    Разширен калкулатор за заплати с пълна поддръжка на българското законодателство
    """
    
    def __init__(self, db: AsyncSession):
        super().__init__()
        self.db = db
        self.labor_config = LaborContractConfig()
        self.civil_config = CivilContractConfig()
        self.sick_calculator = BulgarianSickLeaveSystem()
    
    async def calculate_payroll_for_period(self, user_id: int, payroll_period_id: int):
        """Основен метод за изчисляване на заплата за период"""
        
        # Вземане на данни
        contract = await self.get_active_contract(user_id)
        payroll_period = await self.get_payroll_period(payroll_period_id)
        timelogs = await self.get_timelogs_for_period(user_id, payroll_period)
        sick_records = await self.get_sick_records_for_period(user_id, payroll_period)
        allowances = await self.get_active_allowances(user_id)
        advances = await self.get_outstanding_advances(user_id)
        
        if contract.contract_type == 'full_time':
            return await self.calculate_labor_contract(contract, payroll_period, timelogs, sick_records, allowances, advances)
        elif contract.contract_type == 'contractor':
            return await self.calculate_civil_contract(contract, payroll_period, timelogs, allowances, advances)
        else:
            return await self.calculate_part_time_contract(contract, payroll_period, timelogs, sick_records, allowances, advances)
    
    async def calculate_labor_contract(self, contract, payroll_period, timelogs, sick_records, allowances, advances):
        """Изчисляване на заплата по трудов договор"""
        
        # 1. Брутна основна заплата
        base_salary = contract.base_salary
        
        # 2. Изработени дни и часове
        worked_days = self.calculate_worked_days(timelogs, payroll_period)
        overtime_hours = self.calculate_overtime_hours(timelogs)
        
        # 3. Пропорционална заплата
        monthly_working_days = self.get_monthly_working_days(payroll_period.start_date.month)
        proportional_salary = (base_salary / monthly_working_days) * worked_days
        
        # 4. Изчисляване на болнични
        sick_pay = 0
        for sick_record in sick_records:
            if sick_record.status == 'approved':
                sick_calc = self.sick_calculator.calculate_sick_pay(contract, sick_record)
                sick_pay += sick_calc['total_amount']
        
        # 5. Добавки и бонуси
        bonus_amount = await self.calculate_bonuses(contract.user_id, payroll_period)
        overtime_amount = overtime_hours * (base_salary / 176) * 1.5  # 176 часа средно месечно
        
        # 6. Допълнителни одръжки
        allowance_amount = sum(a.amount for a in allowances if self.is_payroll_date_in_range(a, payroll_period))
        
        # 7. Брутна сума
        gross_amount = proportional_salary + sick_pay + bonus_amount + overtime_amount + allowance_amount
        
        # 8. Осигуровки (служител)
        insurance_amount = self.calculate_employee_insurance(gross_amount, contract)
        
        # 9. Облагаем доход
        taxable_income = max(0, gross_amount - insurance_amount)
        
        # 10. Данък общ доход
        tax_amount = self.calculate_income_tax(taxable_income, contract)
        
        # 11. Авансови плащания
        advance_deductions = sum(a.amount for a in advances if a.status == 'approved')
        
        # 12. Нетна сума
        net_amount = gross_amount - insurance_amount - tax_amount - advance_deductions
        
        return {
            'base_salary': base_salary,
            'worked_days': worked_days,
            'sick_pay': sick_pay,
            'bonus_amount': bonus_amount,
            'overtime_amount': overtime_amount,
            'allowance_amount': allowance_amount,
            'gross_amount': gross_amount,
            'insurance_amount': insurance_amount,
            'taxable_income': taxable_income,
            'tax_amount': tax_amount,
            'advance_deductions': advance_deductions,
            'net_amount': net_amount,
            'breakdown': {
                'health_insurance': gross_amount * self.labor_config.HEALTH_INSURANCE_RATE / 100,
                'pension_insurance': gross_amount * self.labor_config.PENSION_INSURANCE_RATE / 100,
                'unemployment_insurance': gross_amount * self.labor_config.UNEMPLOYMENT_INSURANCE_RATE / 100
            }
        }
    
    async def calculate_civil_contract(self, contract, payroll_period, timelogs, allowances, advances):
        """Изчисляване на заплата по граждански договор"""
        
        # 1. Договорена сума
        contract_amount = await self.get_contract_amount_for_period(contract, payroll_period)
        
        # 2. Добавки
        allowance_amount = sum(a.amount for a in allowances if self.is_payroll_date_in_range(a, payroll_period))
        
        # 3. Брутна сума
        gross_amount = contract_amount + allowance_amount
        
        # 4. Осигуровки (по избор)
        insurance_amount = self.calculate_civil_insurance(gross_amount, contract)
        
        # 5. Облагаем доход
        taxable_income = max(0, gross_amount - insurance_amount)
        
        # 6. Данък 10%
        tax_amount = taxable_income * 0.10
        
        # 7. Авансови плащания
        advance_deductions = sum(a.amount for a in advances if a.status == 'approved')
        
        # 8. Нетна сума
        net_amount = gross_amount - insurance_amount - tax_amount - advance_deductions
        
        return {
            'contract_amount': contract_amount,
            'allowance_amount': allowance_amount,
            'gross_amount': gross_amount,
            'insurance_amount': insurance_amount,
            'taxable_income': taxable_income,
            'tax_amount': tax_amount,
            'advance_deductions': advance_deductions,
            'net_amount': net_amount
        }
    
    def calculate_employee_insurance(self, gross_amount, contract):
        """Изчисляване на осигуровки за служител"""
        
        if contract.insurance_regime == 'full':
            health = gross_amount * self.labor_config.HEALTH_INSURANCE_RATE / 100
            pension = gross_amount * self.labor_config.PENSION_INSURANCE_RATE / 100
            unemployment = gross_amount * self.labor_config.UNEMPLOYMENT_INSURANCE_RATE / 100
            return health + pension + unemployment
        elif contract.insurance_regime == 'reduced':
            # Режим за пенсионери - само здравни осигуровки
            return gross_amount * self.labor_config.HEALTH_INSURANCE_RATE / 100
        else:  # exempt
            return 0
    
    def calculate_employer_insurance(self, gross_amount, contract):
        """Изчисляване на осигуровки за работодател (за справки)"""
        
        if contract.insurance_regime == 'full':
            health = gross_amount * self.labor_config.EMPLOYER_HEALTH_INSURANCE_RATE / 100
            pension = gross_amount * self.labor_config.EMPLOYER_PENSION_INSURANCE_RATE / 100
            unemployment = gross_amount * self.labor_config.EMPLOYER_UNEMPLOYMENT_INSURANCE_RATE / 100
            accident = gross_amount * self.labor_config.ACCIDENT_INSURANCE_RATE / 100
            return health + pension + unemployment + accident
        else:
            return 0
    
    def calculate_income_tax(self, taxable_income, contract):
        """Изчисляване на данък общ доход"""
        
        if contract.tax_regime == 'minimum_wage':
            # Облагане върху минимална основа
            minimum_base = self.labor_config.MINIMUM_TAXABLE_BASE
            tax_base = max(taxable_income, minimum_base)
            return tax_base * self.labor_config.INCOME_TAX_RATE
        elif contract.tax_regime == 'pensioner':
            # Освобождаване от данък за пенсионери
            return 0
        elif contract.tax_regime == 'disabled':
            # Освобождаване за лица с увреждания
            return 0
        else:  # standard
            return taxable_income * self.labor_config.INCOME_TAX_RATE
Frontend Компоненти за Фаза 3
// Contract Management Component
interface ContractForm {
  contractType: 'full_time' | 'part_time' | 'contractor' | 'internship';
  contractNumber: string;
  startDate: Date;
  endDate?: Date;
  baseSalary: number;
  workHoursPerWeek: number;
  workDaysPerWeek: number;
  position: string;
  department: string;
  taxRegime: 'standard' | 'minimum_wage' | 'pensioner' | 'disabled';
  insuranceRegime: 'full' | 'reduced' | 'exempt';
}
// Payroll Period Management
interface PayrollPeriod {
  id: number;
  name: string;
  startDate: Date;
  endDate: Date;
  paymentDate: Date;
  status: 'draft' | 'processing' | 'approved' | 'paid' | 'closed';
  totalGrossAmount: number;
  totalNetAmount: number;
  employeeCount: number;
}
// Additional Allowances
interface Allowance {
  id: number;
  name: string;
  type: 'transport' | 'meal' | 'phone' | 'representation' | 'housing' | 'other';
  amount: number;
  isTaxable: boolean;
  isInsurable: boolean;
  frequency: 'monthly' | 'once' | 'custom';
  startDate: Date;
  endDate?: Date;
}
// Sick Leave Management
interface SickLeaveRecord {
  id: number;
  startDate: Date;
  endDate: Date;
  totalDays: number;
  type: 'general' | 'work_injury' | 'maternity' | 'child_care';
  employerCoveredDays: number;
  employerPaymentPercentage: number;
  isNSSCovered: boolean;
  doctorNoteNumber: string;
  status: 'pending' | 'approved' | 'rejected' | 'processed';
}
GraphQL Schema за Фаза 3
# Contract Mutations
mutation CreateEmploymentContract($input: EmploymentContractInput!) {
  createEmploymentContract(input: $input) {
    id
    contractType
    baseSalary
    workHoursPerWeek
    status
  }
}
mutation UpdateEmploymentContract($id: ID!, $input: EmploymentContractInput!) {
  updateEmploymentContract(id: $id, input: $input) {
    id
    # ... contract fields
  }
}
# Payroll Period Mutations
mutation CreatePayrollPeriod($input: PayrollPeriodInput!) {
  createPayrollPeriod(input: $input) {
    id
    name
    startDate
    endDate
    paymentDate
    status
  }
}
mutation ProcessPayrollPeriod($id: ID!) {
  processPayrollPeriod(id: $id) {
    id
    status
    totalGrossAmount
    totalNetAmount
    employeeCount
  }
}
# Allowance Mutations
mutation CreateAllowance($input: AllowanceInput!) {
  createAllowance(input: $input) {
    id
    name
    type
    amount
    isTaxable
    isInsurable
  }
}
# Sick Leave Mutations
mutation CreateSickLeaveRecord($input: SickLeaveRecordInput!) {
  createSickLeaveRecord(input: $input) {
    id
    startDate
    endDate
    totalDays
    status
  }
}
mutation ApproveSickLeaveRecord($id: ID!, $employerPaymentPercentage: Float!) {
  approveSickLeaveRecord(id: $id, employerPaymentPercentage: $employerPaymentPercentage) {
    id
    status
    employerPaymentPercentage
    processedInPayrollId
  }
}
# Queries
query GetContracts($userId: ID!, $companyId: ID!) {
  contracts(userId: $userId, companyId: $companyId) {
    id
    contractType
    baseSalary
    startDate
    endDate
    isActive
    position {
      id
      name
    }
    department {
      id
      name
    }
  }
}
query GetPayrollPeriods($companyId: ID!, $year: Int) {
  payrollPeriods(companyId: $companyId, year: $year) {
    id
    name
    startDate
    endDate
    paymentDate
    status
    totalGrossAmount
    totalNetAmount
    employeeCount
  }
}
query GetPayrollDetails($payrollPeriodId: ID!, $userId: ID!) {
  payrollDetails(payrollPeriodId: $payrollPeriodId, userId: $userId) {
    id
    baseSalary
    workedDays
    overtimeHours
    sickPay
    bonusAmount
    allowanceAmount
    grossAmount
    insuranceAmount
    taxAmount
    netAmount
    breakdown {
      healthInsurance
      pensionInsurance
      unemploymentInsurance
    }
  }
}
---
Фаза 4: Конфигурационен Фреймуърк (2 седмици)
Основна Концепция
Динамична система за настройки, която позволява пълна конфигурация на всички бизнес правила на фирма ниво.
Нови Модели
-- Категории на настройки
CREATE TABLE configuration_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    is_system BOOLEAN DEFAULT FALSE,  -- System vs user-defined
    company_id INTEGER REFERENCES companies(id),
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT sofia_now()
);
-- Дефиниции на полета
CREATE TABLE configuration_fields (
    id SERIAL PRIMARY KEY,
    category_id INTEGER REFERENCES configuration_categories(id),
    key VARCHAR(100) NOT NULL,
    label VARCHAR(200) NOT NULL,
    field_type VARCHAR(50) NOT NULL,  -- "text", "number", "select", "checkbox", "date", "textarea"
    validation_rules JSONB,  -- {"required": true, "min": 0, "max": 100, "pattern": "..."}
    default_value TEXT,
    display_order INTEGER DEFAULT 0,
    is_company_overridable BOOLEAN DEFAULT TRUE,
    is_required BOOLEAN DEFAULT FALSE,
    description TEXT,
    created_at TIMESTAMP DEFAULT sofia_now()
);
-- Company-specific стойности
CREATE TABLE company_configurations (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    field_id INTEGER REFERENCES configuration_fields(id),
    value TEXT,
    updated_by INTEGER REFERENCES users(id),
    updated_at TIMESTAMP DEFAULT sofia_now(),
    UNIQUE(company_id, field_id)
);
-- Версионинг на конфигурации
CREATE TABLE configuration_versions (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    configuration_snapshot JSONB NOT NULL,
    version_number INTEGER NOT NULL,
    created_by INTEGER REFERENCES users(id),
    change_description TEXT,
    created_at TIMESTAMP DEFAULT sofia_now()
);
Configuration Service
class ConfigurationService:
    """Service за управление на динамични конфигурации"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_config_schema(self, company_id: int) -> Dict:
        """Получаване на пълната конфигурационна схема за фирма"""
        
        categories = await self.db.execute(
            select(ConfigurationCategory).where(
                or_(
                    ConfigurationCategory.company_id == company_id,
                    ConfigurationCategory.is_system == True,
                    ConfigurationCategory.company_id.is_(None)
                )
            ).order_by(ConfigurationCategory.display_order)
        )
        
        schema = {}
        for category in categories.scalars():
            fields = await self.db.execute(
                select(ConfigurationField).where(
                    ConfigurationField.category_id == category.id
                ).order_by(ConfigurationField.display_order)
            )
            
            schema[category.name] = {
                'id': category.id,
                'description': category.description,
                'fields': []
            }
            
            for field in fields.scalars():
                # Взимане на company-specific стойност или default
                company_config = await self.db.execute(
                    select(CompanyConfiguration).where(
                        CompanyConfiguration.company_id == company_id,
                        CompanyConfiguration.field_id == field.id
                    )
                )
                
                current_value = field.default_value
                if company_config.scalar_one_or_none():
                    current_value = company_config.scalar_one_or_none().value
                
                schema[category.name]['fields'].append({
                    'id': field.id,
                    'key': field.key,
                    'label': field.label,
                    'type': field.field_type,
                    'validation': field.validation_rules,
                    'defaultValue': field.default_value,
                    'currentValue': current_value,
                    'isOverridable': field.is_company_overridable,
                    'isRequired': field.is_required,
                    'description': field.description
                })
        
        return schema
    
    async def validate_configuration(self, config_data: Dict, company_id: int) -> Tuple[bool, List[str]]:
        """Валидация на конфигурационни данни"""
        
        errors = []
        
        for category_key, category_data in config_data.items():
            for field_key, value in category_data.items():
                # Взимане на field дефиниция
                field = await self.get_field_definition(field_key)
                if not field:
                    errors.append(f"Unknown field: {field_key}")
                    continue
                
                # Валидация
                validation_rules = field.validation_rules or {}
                
                # Required validation
                if validation_rules.get('required') and (value is None or value == ''):
                    errors.append(f"{field.label} is required")
                
                # Type validation
                if value is not None and value != '':
                    if field.field_type == 'number':
                        try:
                            num_value = float(value)
                            # Range validation
                            min_val = validation_rules.get('min')
                            max_val = validation_rules.get('max')
                            if min_val is not None and num_value < min_val:
                                errors.append(f"{field.label} must be at least {min_val}")
                            if max_val is not None and num_value > max_val:
                                errors.append(f"{field.label} must be at most {max_val}")
                        except ValueError:
                            errors.append(f"{field.label} must be a valid number")
                    
                    elif field.field_type == 'select':
                        options = validation_rules.get('options', [])
                        if value not in options:
                            errors.append(f"{field.label} must be one of: {', '.join(options)}")
                    
                    elif field.field_type == 'date':
                        try:
                            datetime.datetime.strptime(value, '%Y-%m-%d')
                        except ValueError:
                            errors.append(f"{field.label} must be a valid date (YYYY-MM-DD)")
        
        return len(errors) == 0, errors
    
    async def update_configuration(self, company_id: int, updates: Dict, user_id: int) -> Dict:
        """Актуализиране на фирмена конфигурация"""
        
        # Валидация
        is_valid, errors = await self.validate_configuration(updates, company_id)
        if not is_valid:
            raise ValueError(f"Validation failed: {', '.join(errors)}")
        
        # Запазване на текущата версия
        await self.create_configuration_snapshot(company_id, user_id, "Pre-update snapshot")
        
        # Обновяване на стойностите
        updated_fields = []
        for category_key, category_data in updates.items():
            for field_key, value in category_data.items():
                field = await self.get_field_definition(field_key)
                if field and field.is_company_overridable:
                    # Проверка за съществуваща конфигурация
                    existing_config = await self.db.execute(
                        select(CompanyConfiguration).where(
                            CompanyConfiguration.company_id == company_id,
                            CompanyConfiguration.field_id == field.id
                        )
                    )
                    
                    config = existing_config.scalar_one_or_none()
                    if config:
                        config.value = str(value)
                        config.updated_at = sofia_now()
                        config.updated_by = user_id
                    else:
                        new_config = CompanyConfiguration(
                            company_id=company_id,
                            field_id=field.id,
                            value=str(value),
                            updated_by=user_id
                        )
                        self.db.add(new_config)
                    
                    updated_fields.append(f"{category_key}.{field_key}")
        
        await self.db.commit()
        
        # Създаване на нова версия
        change_description = f"Updated {', '.join(updated_fields)}"
        await self.create_configuration_snapshot(company_id, user_id, change_description)
        
        return {
            'success': True,
            'updatedFields': updated_fields,
            'message': 'Configuration updated successfully'
        }
    
    async def create_configuration_snapshot(self, company_id: int, user_id: int, description: str):
        """Създаване на snapshot на текущата конфигурация"""
        
        current_config = await self.get_effective_config(company_id)
        
        # Взимане на последната версия
        last_version = await self.db.execute(
            select(ConfigurationVersions).where(
                ConfigurationVersions.company_id == company_id
            ).order_by(ConfigurationVersions.version_number.desc())
        )
        
        version_number = 1
        if last_version.scalar_one_or_none():
            version_number = last_version.scalar_one_or_none().version_number + 1
        
        # Създаване на нова версия
        snapshot = ConfigurationVersions(
            company_id=company_id,
            configuration_snapshot=current_config,
            version_number=version_number,
            created_by=user_id,
            change_description=description
        )
        
        self.db.add(snapshot)
        await self.db.commit()
    
    async def get_effective_config(self, company_id: int) -> Dict:
        """Получаване на ефективната конфигурация (system + company)"""
        
        # System конфигурация
        system_config = await self.get_system_config()
        
        # Company конфигурация
        company_config = await self.get_company_config(company_id)
        
        # Merge
        effective_config = self.merge_configurations(system_config, company_config)
        
        return effective_config
    
    def merge_configurations(self, system_config: Dict, company_config: Dict) -> Dict:
        """Merge на system и company конфигурации"""
        
        effective = copy.deepcopy(system_config)
        
        for category_key, category_data in company_config.items():
            if category_key not in effective:
                effective[category_key] = {}
            
            for field_key, value in category_data.items():
                effective[category_key][field_key] = value
        
        return effective
Default Configuration Categories
DEFAULT_CONFIGURATION_CATEGORIES = [
    {
        "name": "labor_law",
        "description": "Трудово законодателство и осигуровки",
        "is_system": True,
        "display_order": 1,
        "fields": [
            {
                "key": "minimum_wage",
                "label": "Минимална работна заплата",
                "field_type": "number",
                "default_value": "933.00",
                "validation_rules": {"required": True, "min": 0, "type": "currency"},
                "is_company_overridable": False,
                "description": "Минимална работна заплата за 2026 г."
            },
            {
                "key": "standard_work_hours",
                "label": "Стандартно работно време (седмично)",
                "field_type": "number",
                "default_value": "40",
                "validation_rules": {"required": True, "min": 1, "max": 48},
                "description": "Стандартно работно време в рамките на една седмица"
            },
            {
                "key": "health_insurance_employee_rate",
                "label": "Здравни осигуровки - служител (%)",
                "field_type": "number",
                "default_value": "8.33",
                "validation_rules": {"required": True, "min": 0, "max": 20},
                "description": "Процент здравни осигуровки за сметка на служителя"
            },
            {
                "key": "pension_insurance_employee_rate",
                "label": "Пенсионни осигуровки - служител (%)",
                "field_type": "number",
                "default_value": "7.71",
                "validation_rules": {"required": True, "min": 0, "max": 20},
                "description": "Процент пенсионни осигуровки за сметка на служителя"
            },
            {
                "key": "income_tax_rate",
                "label": "Данък общ доход (%)",
                "field_type": "number",
                "default_value": "10",
                "validation_rules": {"required": True, "min": 0, "max": 30},
                "is_company_overridable": False,
                "description": "Данък върху общ доход"
            }
        ]
    },
    {
        "name": "sick_leave",
        "description": "Болнични и здравни осигуровки",
        "is_system": True,
        "display_order": 2,
        "fields": [
            {
                "key": "employer_covered_days",
                "label": "Дни за сметка на работодателя",
                "field_type": "number",
                "default_value": "3",
                "validation_rules": {"required": True, "min": 0, "max": 30},
                "is_company_overridable": True,
                "description": "Брой дни, които се плащат от работодателя"
            },
            {
                "key": "employer_payment_percentage",
                "label": "Процент от работодателя (%)",
                "field_type": "number",
                "default_value": "75",
                "validation_rules": {"required": True, "min": 50, "max": 100},
                "is_company_overridable": True,
                "description": "Процент от възнаграждението, който се изплаща от работодателя"
            },
            {
                "key": "nss_payment_percentage",
                "label": "Процент от НОЙ (%)",
                "field_type": "number",
                "default_value": "80",
                "validation_rules": {"required": True, "min": 50, "max": 100},
                "is_company_overridable": False,
                "description": "Процент от възнаграждението, който се изплаща от НОЙ"
            },
            {
                "key": "minimum_sick_pay",
                "label": "Минимално дневно обезщетение",
                "field_type": "number",
                "default_value": "14.70",
                "validation_rules": {"required": True, "min": 0, "type": "currency"},
                "is_company_overridable": False,
                "description": "Минимален размер на дневно парично обезщетение"
            }
        ]
    },
    {
        "name": "leave_policy",
        "description": "Политика за отпуски",
        "is_system": False,
        "display_order": 3,
        "fields": [
            {
                "key": "minimum_paid_leave_days",
                "label": "Минимум платен отпуск (дни)",
                "field_type": "number",
                "default_value": "20",
                "validation_rules": {"required": True, "min": 20, "max": 30},
                "description": "Минимален брой дни платен отпуск годишно"
            },
            {
                "key": "maximum_unpaid_leave_days",
                "label": "Максимум неплатен отпуск (дни)",
                "field_type": "number",
                "default_value": "30",
                "validation_rules": {"required": True, "min": 0, "max": 365},
                "description": "Максимален брой дни неплатен отпуск"
            },
            {
                "key": "advance_leave_allowed",
                "label": "Позволен напредващ отпуск",
                "field_type": "checkbox",
                "default_value": "true",
                "description": "Дали служителите могат да ползват отпуск преди да са го натрупали"
            },
            {
                "key": "leave_approval_required",
                "label": "Изисква се одобрение за отпуск",
                "field_type": "checkbox",
                "default_value": "true",
                "description": "Дали всички молби за отпуск изискват одобрение"
            }
        ]
    },
    {
        "name": "payroll_settings",
        "description": "Настройки за заплати",
        "is_system": False,
        "display_order": 4,
        "fields": [
            {
                "key": "payment_day",
                "label": "Ден за изплащане на заплати",
                "field_type": "number",
                "default_value": "25",
                "validation_rules": {"required": True, "min": 1, "max": 31},
                "description": "Ден от месеца, в който се изплащат заплатите"
            },
            {
                "key": "rounding_rule",
                "label": "Правило за закръгляване",
                "field_type": "select",
                "default_value": "normal",
                "validation_rules": {"options": ["normal", "always_up", "always_down"]},
                "description": "Как да се закръгляват сумите в фишовете"
            },
            {
                "key": "decimal_places",
                "label": "Десетични знаци",
                "field_type": "number",
                "default_value": "2",
                "validation_rules": {"required": True, "min": 0, "max": 4},
                "description": "Брой десетични знаци за паричните суми"
            },
            {
                "key": "automatic_payment_generation",
                "label": "Автоматично генериране на плащания",
                "field_type": "checkbox",
                "default_value": "true",
                "description": "Да се генерират ли автоматично плащания при одобряване на заплати"
            }
        ]
    }
]
Dynamic Form Generation
// frontend/src/components/DynamicConfigurationForm.tsx
interface DynamicConfigurationFormProps {
  companyId: number;
  onSave: (config: any) => void;
  loading?: boolean;
}
const DynamicConfigurationForm: React.FC<DynamicConfigurationFormProps> = ({
  companyId,
  onSave,
  loading = false
}) => {
  const [configSchema, setConfigSchema] = useState<any>({});
  const [formData, setFormData] = useState<any>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(true);
  const { data } = useQuery(GET_CONFIGURATION_SCHEMA, {
    variables: { companyId },
    onCompleted: (data) => {
      const schema = data.configurationSchema;
      setConfigSchema(schema);
      
      // Initialize form data with current values
      const initialData: any = {};
      Object.keys(schema).forEach(categoryKey => {
        initialData[categoryKey] = {};
        schema[categoryKey].fields.forEach((field: any) => {
          initialData[categoryKey][field.key] = field.currentValue || field.defaultValue;
        });
      });
      setFormData(initialData);
      setIsLoading(false);
    }
  });
  const [updateConfiguration] = useMutation(UPDATE_CONFIGURATION, {
    onCompleted: (data) => {
      onSave(data.updateConfiguration);
    },
    onError: (error) => {
      console.error('Configuration update failed:', error);
    }
  });
  const handleFieldChange = (categoryKey: string, fieldKey: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [categoryKey]: {
        ...prev[categoryKey],
        [fieldKey]: value
      }
    }));
    
    // Clear field error when value changes
    if (errors[`${categoryKey}.${fieldKey}`]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[`${categoryKey}.${fieldKey}`];
        return newErrors;
      });
    }
  };
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};
    
    Object.keys(configSchema).forEach(categoryKey => {
      const category = configSchema[categoryKey];
      category.fields.forEach((field: any) => {
        const value = formData[categoryKey]?.[field.key];
        
        // Required validation
        if (field.isRequired && (!value || value === '')) {
          newErrors[`${categoryKey}.${field.key}`] = `${field.label} is required`;
        }
        
        // Type-specific validation
        if (value && value !== '') {
          switch (field.type) {
            case 'number':
              const numValue = parseFloat(value);
              if (isNaN(numValue)) {
                newErrors[`${categoryKey}.${field.key}`] = `${field.label} must be a valid number`;
              } else {
                if (field.validation?.min !== undefined && numValue < field.validation.min) {
                  newErrors[`${categoryKey}.${field.key}`] = `${field.label} must be at least ${field.validation.min}`;
                }
                if (field.validation?.max !== undefined && numValue > field.validation.max) {
                  newErrors[`${categoryKey}.${field.key}`] = `${field.label} must be at most ${field.validation.max}`;
                }
              }
              break;
            
            case 'select':
              if (field.validation?.options && !field.validation.options.includes(value)) {
                newErrors[`${categoryKey}.${field.key}`] = `${field.label} must be one of: ${field.validation.options.join(', ')}`;
              }
              break;
            
            case 'date':
              if (!isValid(new Date(value))) {
                newErrors[`${categoryKey}.${field.key}`] = `${field.label} must be a valid date`;
              }
              break;
          }
        }
      });
    });
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };
  const handleSubmit = async () => {
    if (!validateForm()) {
      return;
    }
    
    await updateConfiguration({
      variables: {
        companyId,
        updates: formData
      }
    });
  };
  const renderField = (categoryKey: string, field: any) => {
    const value = formData[categoryKey]?.[field.key] || '';
    const error = errors[`${categoryKey}.${field.key}`];
    const fieldId = `${categoryKey}.${field.key}`;
    switch (field.type) {
      case 'text':
      case 'number':
        return (
          <TextField
            key={field.id}
            id={fieldId}
            label={field.label}
            type={field.type}
            value={value}
            onChange={(e) => handleFieldChange(categoryKey, field.key, e.target.value)}
            error={!!error}
            helperText={error || field.description}
            fullWidth
            margin="normal"
            required={field.isRequired}
            inputProps={
              field.type === 'number' ? {
                min: field.validation?.min,
                max: field.validation?.max,
                step: field.validation?.step || 'any'
              } : {}
            }
          />
        );
      
      case 'textarea':
        return (
          <TextField
            key={field.id}
            id={fieldId}
            label={field.label}
            multiline
            rows={4}
            value={value}
            onChange={(e) => handleFieldChange(categoryKey, field.key, e.target.value)}
            error={!!error}
            helperText={error || field.description}
            fullWidth
            margin="normal"
            required={field.isRequired}
          />
        );
      
      case 'checkbox':
        return (
          <FormControlLabel
            key={field.id}
            control={
              <Checkbox
                id={fieldId}
                checked={value === 'true' || value === true}
                onChange={(e) => handleFieldChange(categoryKey, field.key, e.target.checked)}
              />
            }
            label={field.label}
          />
        );
      
      case 'select':
        return (
          <TextField
            key={field.id}
            id={fieldId}
            select
            label={field.label}
            value={value}
            onChange={(e) => handleFieldChange(categoryKey, field.key, e.target.value)}
            error={!!error}
            helperText={error || field.description}
            fullWidth
            margin="normal"
            required={field.isRequired}
          >
            {field.validation?.options?.map((option: string) => (
              <MenuItem key={option} value={option}>
                {option}
              </MenuItem>
            ))}
          </TextField>
        );
      
      case 'date':
        return (
          <TextField
            key={field.id}
            id={fieldId}
            label={field.label}
            type="date"
            value={value}
            onChange={(e) => handleFieldChange(categoryKey, field.key, e.target.value)}
            error={!!error}
            helperText={error || field.description}
            fullWidth
            margin="normal"
            required={field.isRequired}
            InputLabelProps={{
              shrink: true,
            }}
          />
        );
      
      default:
        return null;
    }
  };
  if (isLoading) {
    return <CircularProgress />;
  }
  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Company Configuration
      </Typography>
      
      {Object.keys(configSchema).map(categoryKey => {
        const category = configSchema[categoryKey];
        return (
          <Box key={categoryKey} sx={{ mb: 4 }}>
            <Typography variant="h6" color="primary" gutterBottom>
              {category.description || categoryKey}
            </Typography>
            
            {category.fields.map((field: any) => renderField(categoryKey, field))}
          </Box>
        );
      })}
      
      <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={loading}
          startIcon={loading ? <CircularProgress size={20} /> : null}
        >
          {loading ? 'Saving...' : 'Save Configuration'}
        </Button>
      </Box>
    </Paper>
  );
};
export default DynamicConfigurationForm;
---
Интеграционни Аспекти и Performance
Multi-Level Caching Strategy
class AdvancedCacheManager:
    """Multi-level caching за оптимална performance"""
    
    def __init__(self):
        self.memory_cache = {}
        self.redis_client = redis.Redis(decode_responses=True)
        self.cache_ttl = {
            'permissions': 300,      # 5 минути
            'configurations': 600,   # 10 минути
            'contracts': 1800,       # 30 минути
            'payroll_calculations': 600  # 10 минути
        }
    
    async def get_cached_data(self, key: str, category: str, fetch_func):
        """Generic cache getter"""
        
        # L1: Memory cache
        if key in self.memory_cache:
            cached_item = self.memory_cache[key]
            if cached_item['expires'] > time.time():
                return cached_item['data']
        
        # L2: Redis cache
        redis_data = await self.redis_client.get(f"{category}:{key}")
        if redis_data:
            parsed_data = json.loads(redis_data)
            # Update memory cache
            self.memory_cache[key] = {
                'data': parsed_data,
                'expires': time.time() + self.cache_ttl[category]
            }
            return parsed_data
        
        # L3: Database
        data = await fetch_func()
        
        # Cache in both layers
        ttl = self.cache_ttl[category]
        
        # Memory cache
        self.memory_cache[key] = {
            'data': data,
            'expires': time.time() + ttl
        }
        
        # Redis cache
        await self.redis_client.setex(
            f"{category}:{key}",
            ttl,
            json.dumps(data)
        )
        
        return data
    
    async def invalidate_cache(self, pattern: str):
        """Invalidate cache entries matching pattern"""
        
        # Clear memory cache
        keys_to_remove = [k for k in self.memory_cache.keys() if pattern in k]
        for key in keys_to_remove:
            del self.memory_cache[key]
        
        # Clear Redis cache
        redis_keys = await self.redis_client.keys(pattern)
        if redis_keys:
            await self.redis_client.delete(*redis_keys)
Database Optimization
-- Performance indexes за всички нови таблици
CREATE INDEX idx_permissions_name ON permissions(name);
CREATE INDEX idx_role_permissions_role_id ON role_permissions(role_id);
CREATE INDEX idx_company_role_assignments_user_company ON company_role_assignments(user_id, company_id);
CREATE INDEX idx_user_permission_cache_user_company ON user_permission_cache(user_id, company_id);
CREATE INDEX idx_permission_audit_log_user_id ON permission_audit_log(user_id);
CREATE INDEX idx_google_calendar_accounts_user_id ON google_calendar_accounts(user_id);
CREATE INDEX idx_google_calendar_events_user_source ON google_calendar_events(user_id, source_type);
CREATE INDEX idx_employment_contracts_user_active ON employment_contracts(user_id, is_active);
CREATE INDEX idx_payroll_periods_company_status ON payroll_periods(company_id, status);
CREATE INDEX idx_payslip_details_payslip ON payslip_details(payslip_id);
CREATE INDEX idx_additional_allowances_user_active ON additional_allowances(user_id, is_active);
CREATE INDEX idx_sick_leave_records_user_dates ON sick_leave_records(user_id, start_date, end_date);
CREATE INDEX idx_advance_payments_user_status ON advance_payments(user_id, status);
CREATE INDEX idx_payments_payslip ON payments(payslip_id);
CREATE INDEX idx_company_configurations_company_field ON company_configurations(company_id, field_id);
Background Job Management
class BackgroundJobManager:
    """Централизиран management на background jobs"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.jobs = {
            'google_sync': GoogleSyncJob(),
            'payroll_processing': PayrollProcessingJob(),
            'configuration_cleanup': ConfigurationCleanupJob(),
            'cache_cleanup': CacheCleanupJob()
        }
    
    async def start(self):
        """Стартиране на всички background jobs"""
        
        # Google Calendar sync - всеки 15 минути
        self.scheduler.add_job(
            self.jobs['google_sync'].process_all_user_syncs,
            'interval',
            minutes=15,
            id='google_calendar_sync'
        )
        
        # Payroll period reminders - всеки ден в 09:00
        self.scheduler.add_job(
            self.jobs['payroll_processing'].check_upcoming_periods,
            'cron',
            hour=9,
            minute=0,
            id='payroll_reminders'
        )
        
        # Configuration cleanup - всеки ден в 02:00
        self.scheduler.add_job(
            self.jobs['configuration_cleanup'].cleanup_old_versions,
            'cron',
            hour=2,
            minute=0,
            id='config_cleanup'
        )
        
        # Cache cleanup - всеки час
        self.scheduler.add_job(
            self.jobs['cache_cleanup'].cleanup_expired_entries,
            'interval',
            hours=1,
            id='cache_cleanup'
        )
        
        self.scheduler.start()
        logger.info("Background job manager started")
    
    async def stop(self):
        """Спиране на всички background jobs"""
        self.scheduler.shutdown()
        logger.info("Background job manager stopped")
---
Времева Рамка и Deployment
Обща Времева Рамка: 8-11 седмици
Фаза 1: RBAC Система (2-3 седмици)
- Week 1: Database migration, core RBAC models
- Week 2: Permission service, middleware implementation
- Week 3: Frontend integration, testing, deployment
Фаза 2: Google Calendar (1-2 седмици)
- Week 1: OAuth implementation, Google service
- Week 2: Background sync, frontend components
Фаза 3: Enhanced Payroll (3-4 седмици)
- Week 1: Contract management, database schema
- Week 2: Payroll calculator enhancement
- Week 3: Bulgarian sick leave implementation
- Week 4: Frontend components, testing
Фаза 4: Configuration Framework (2 седмици)
- Week 1: Dynamic configuration system
- Week 2: Frontend forms, deployment
Deployment Strategy
# docker-compose.yml - Extension for new services
version: '3.8'
services:
  # Съществуващи услуги...
  
  # Redis за multi-level caching
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
  
  # Background job worker
  worker:
    build: ./backend
    command: python -m backend.jobs.main
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
volumes:
  redis_data:
Testing Strategy
# Comprehensive testing pyramid
TEST_STRATEGY = {
    "unit_tests": {
        "rbac_system": "permission checks, role assignments, cache invalidation",
        "payroll_calculator": "contract types, tax calculations, sick leave logic",
        "google_calendar": "OAuth flow, event formatting, sync logic",
        "configuration": "validation rules, form generation, versioning"
    },
    "integration_tests": {
        "api_endpoints": "permission-based access, data consistency",
        "database_operations": "migrations, cascading deletes, performance",
        "external_apis": "Google Calendar API, error handling",
        "background_jobs": "sync operations, error recovery"
    },
    "e2e_tests": {
        "user_workflows": "contract creation → payroll calculation → payment",
        "admin_workflows": "user management → role assignment → configuration",
        "calendar_workflows": "OAuth setup → sync → verification"
    },
    "performance_tests": {
        "permission_checks": "< 50ms per check with 1000+ permissions",
        "payroll_calculations": "< 100ms per employee calculation",
        "calendar_sync": "< 30 seconds for 100 users",
        "configuration_load": "< 200ms for full schema load"
    }
}
---
Заключение
Този всеобхватен план предоставя детайлна техническа спецификация за трансформацията на WorkingTime системата с:
Ключови Постижения
1. Пълна RBAC Система - 45+ права, company-scoped достъп, performance optimization
2. Google Calendar Интеграция - Two-way sync, privacy controls, background processing  
3. Съвременна Payroll Система - Българско законодателство, граждански договори, реални болнични
4. Динамична Конфигурация - Company-specific настройки, version control, audit trail
Технически Предимства
- Scalability - Multi-level caching, optimized database queries
- Security - Comprehensive audit logging, permission-based access
- Flexibility - Configurable business rules, contract types
- User Experience - Permission-aware UI, real-time updates
- Maintainability - Clean architecture, comprehensive testing
Бизнес Предимства
- Legal Compliance - Пълно съответствие с българското законодателство
- Operational Efficiency - Автоматизирани процеси, намалени ръчни операции
- Data Privacy - Granular контрол над достъпа и синхронизацията
- Cost Optimization - Reduced manual work, improved accuracy
- Scalability - Лесно добавяне на нови компании и потребители

Фаза 3: Нова Система за Възнаграждения с Разширени Функционалности
Нови Изисквания:
1. Дата за заплати - Администраторът определя конкретна дата за изплащане
2. Допълнителни държания - Гъвкава система за различни видове удръжки
3. Реален болничен - Според българското законодателство
4. ДНИ за изплащане от НОЙ - С опция за 75% плащане от работодателя
Детайлна Спецификация:
1. Система за Дата на Заплащане:
CREATE TABLE payroll_payment_schedules (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    payment_day INTEGER NOT NULL, -- 25-то число например
    payment_month_offset INTEGER DEFAULT 0, -- 0 за текущия месец, 1 за следващия
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);
2. Допълнителни Държания:
CREATE TABLE payroll_deductions (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    name VARCHAR(100) NOT NULL,
    deduction_type VARCHAR(50) NOT NULL, -- 'fixed', 'percentage', 'conditional'
    amount DECIMAL(10,2),
    percentage DECIMAL(5,2),
    is_active BOOLEAN DEFAULT TRUE,
    apply_to_all BOOLEAN DEFAULT FALSE,
    employee_ids INTEGER[], -- Specific employees
    created_at TIMESTAMP DEFAULT NOW()
);
3. Болничен по Българско Законодателство:
CREATE TABLE sick_leave_records (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    sick_leave_type VARCHAR(50) NOT NULL, -- 'general', 'work_related', 'maternity', 'child_care'
    is_paid_by_noi BOOLEAN DEFAULT TRUE,
    employer_payment_percentage DECIMAL(5,2) DEFAULT 75.00, -- 75% от работодателя
    daily_amount DECIMAL(10,2), -- Дневно обезщетение
    total_days INTEGER NOT NULL,
    noi_payment_days INTEGER DEFAULT 0, -- Дни платени от НОЙ
    employer_payment_days INTEGER DEFAULT 0, -- Дни платени от работодателя
    medical_document_number VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);
4. НОЙ Дни за Изплащане:
CREATE TABLE noi_payment_days (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    year INTEGER NOT NULL,
    total_noi_days_available INTEGER DEFAULT 30, -- Според Кодекса на труда
    noi_days_used INTEGER DEFAULT 0,
    noi_days_remaining INTEGER GENERATED ALWAYS AS (total_noi_days_available - noi_days_used) STORED,
    employer_payment_percentage DECIMAL(5,2) DEFAULT 75.00,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, year)
);
Бизнес Логика за Болничен:
Типове Болнични:
1. Общ болничен - Първите 3 дни не се плащат, дни 4-30 се плащат от НОЙ (80%), дни 31+ от работодателя (100%)
2. Трудов traumatизъм - 100% се плаща от НОЙ от първия ден
3. Болничен за грижа за дете - По специални правила
4. Майчинство - По специални правила
Пресмятане на Болнични:
def calculate_sick_leave_payment(sick_record, user_salary):
    daily_gross = user_salary / 30  # Среднодневно възнаграждение
    
    if sick_record.sick_leave_type == 'general':
        # Първите 3 дни - без плащане
        unpaid_days = min(3, sick_record.total_days)
        
        # Дни 4-30 - НОЙ плаща 80%
        noi_days = max(0, min(27, sick_record.total_days - 3))
        noi_payment = noi_days * daily_gross * 0.80
        
        # Дни 31+ - Работодател плаща 100%
        employer_days = max(0, sick_record.total_days - 30)
        employer_payment = employer_days * daily_gross
        
        total_payment = noi_payment + employer_payment
        
    elif sick_record.sick_leave_type == 'work_related':
        # 100% от НОЙ от първия ден
        total_payment = sick_record.total_days * daily_gross * 1.00
        
    return {
        'unpaid_days': unpaid_days,
        'noi_payment': noi_payment,
        'employer_payment': employer_payment,
        'total_payment': total_payment,
        'daily_amount': daily_gross
    }
Удължен Payroll Calculator:
class EnhancedPayrollCalculator(PayrollCalculator):
    def __init__(self, db_session, company_id, user_id, calculation_period):
        super().__init__(db_session, company_id, user_id, calculation_period)
        self.payment_schedule = None
        self.additional_deductions = []
        self.sick_leave_records = []
        
    async def calculate_enhanced_payroll(self):
        """Изчислява пълна заплата с всички нови компоненти"""
        base_calculation = await self.calculate()  # Съществуващата логика
        
        # Добавяне на дата на плащане
        payment_date = await self.get_payment_date()
        
        # Допълнителни удръжки
        additional_deductions = await self.get_additional_deductions()
        
        # Болнични изчисления
        sick_payments = await self.calculate_sick_leave_payments()
        
        # НОЙ дни
        noi_payments = await self.calculate_noi_payments()
        
        return {
            **base_calculation,
            'payment_date': payment_date,
            'additional_deductions': additional_deductions,
            'sick_leave_payments': sick_payments,
            'noi_payments': noi_payments,
            'total_deductions': base_calculation['total_deductions'] + additional_deductions,
            'net_payable': self.calculate_final_net(base_calculation, additional_deductions, sick_payments, noi_payments)
        }
    
    async def get_payment_date(self):
        """Определя дата на плащане според company settings"""
        if not self.payment_schedule:
            self.payment_schedule = await self.db.execute(
                select(PayrollPaymentSchedule).where(
                    PayrollPaymentSchedule.company_id == self.company_id,
                    PayrollPaymentSchedule.active == True
                )
            ).scalar_one_or_none()
        
        if not self.payment_schedule:
            # Default: 25-то число на следващия месец
            return date(self.calculation_period.year, self.calculation_period.month + 1, 25)
        
        target_day = self.payment_schedule.payment_day
        target_month = self.calculation_period.month + self.payment_schedule.payment_month_offset
        
        return date(self.calculation_period.year, target_month, target_day)
    
    async def get_additional_deductions(self):
        """Взима всички приложими допълнителни удръжки"""
        deductions_query = select(PayrollDeduction).where(
            PayrollDeduction.company_id == self.company_id,
            PayrollDeduction.is_active == True
        )
        
        deductions = await self.db.execute(deductions_query)
        total_deduction = 0
        
        for deduction in deductions.scalars():
            if deduction.apply_to_all or self.user_id in deduction.employee_ids:
                if deduction.deduction_type == 'fixed':
                    total_deduction += float(deduction.amount)
                elif deduction.deduction_type == 'percentage':
                    base_salary = await self.get_base_salary()
                    total_deduction += base_salary * (float(deduction.percentage) / 100)
        
        return total_deduction
    
    async def calculate_sick_leave_payments(self):
        """Изчислява плащания за болнични за периода"""
        sick_records = await self.db.execute(
            select(SickLeaveRecord).where(
                SickLeaveRecord.user_id == self.user_id,
                SickLeaveRecord.start_date >= self.calculation_period.start_date,
                SickLeaveRecord.end_date <= self.calculation_period.end_date
            )
        )
        
        total_sick_payment = 0
        for record in sick_records.scalars():
            payment = calculate_sick_leave_payment(record, await self.get_base_salary())
            total_sick_payment += payment['total_payment']
        
        return total_sick_payment
    
    async def calculate_noi_payments(self):
        """Изчислява плащания за НОЙ дни, платени от работодателя"""
        noi_record = await self.db.execute(
            select(NOIPaymentDays).where(
                NOIPaymentDays.user_id == self.user_id,
                NOIPaymentDays.year == self.calculation_period.year
            )
        ).scalar_one_or_none()
        
        if not noi_record or noi_record.employer_payment_percentage <= 0:
            return 0
        
        # Ако са използвани НОЙ дни и има 75% плащане от работодателя
        if noi_record.noi_days_used > 0:
            daily_salary = await self.get_base_salary() / 30
            employer_payment_percentage = noi_record.employer_payment_percentage / 100
            return noi_record.noi_days_used * daily_salary * employer_payment_percentage
        
        return 0
Frontend Компоненти за Фаза 3:
1. Payment Schedule Manager:
interface PaymentScheduleForm {
  paymentDay: number;
  paymentMonthOffset: number;
  active: boolean;
}
const PaymentScheduleManager: React.FC = () => {
  const [schedule, setSchedule] = useState<PaymentScheduleForm>({
    paymentDay: 25,
    paymentMonthOffset: 0,
    active: true
  });
  
  const updatePaymentSchedule = async () => {
    // GraphQL мутация за обновяване на графика на плащания
  };
  
  return (
    <Card>
      <CardContent>
        <Typography variant="h6">График на Плащания</Typography>
        <TextField
          label="Ден от месеца"
          type="number"
          value={schedule.paymentDay}
          onChange={(e) => setSchedule({...schedule, paymentDay: parseInt(e.target.value)})}
        />
        <FormControlLabel
          control={
            <Switch
              checked={schedule.active}
              onChange={(e) => setSchedule({...schedule, active: e.target.checked})}
            />
          }
          label="Активен"
        />
      </CardContent>
    </Card>
  );
};
2. Additional Deductions Manager:
const DeductionManager: React.FC = () => {
  const [deductions, setDeductions] = useState<Deduction[]>([]);
  
  return (
    <Table>
      <TableHead>
        <TableRow>
          <TableCell>Име на Удръжка</TableCell>
          <TableCell>Тип</TableCell>
          <TableCell>Сума/Процент</TableCell>
          <TableCell>Приложими Служители</TableCell>
          <TableCell>Действия</TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {deductions.map(deduction => (
          <TableRow key={deduction.id}>
            <TableCell>{deduction.name}</TableCell>
            <TableCell>{deduction.deductionType}</TableCell>
            <TableCell>
              {deduction.deductionType === 'fixed' 
                ? `${deduction.amount} лв.` 
                : `${deduction.percentage}%`}
            </TableCell>
            <TableCell>
              {deduction.applyToAll ? 'Всички' : 'Избрани'}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
};
3. Enhanced Sick Leave Interface:
const SickLeaveForm: React.FC = () => {
  const [sickLeave, setSickLeave] = useState<SickLeaveData>({
    startDate: '',
    endDate: '',
    type: 'general',
    isPaidByNoi: true,
    employerPaymentPercentage: 75,
    medicalDocumentNumber: ''
  });
  
  return (
    <form>
      <TextField
        label="Начална дата"
        type="date"
        value={sickLeave.startDate}
        onChange={(e) => setSickLeave({...sickLeave, startDate: e.target.value})}
      />
      <TextField
        label="Крайна дата"
        type="date"
        value={sickLeave.endDate}
        onChange={(e) => setSickLeave({...sickLeave, endDate: e.target.value})}
      />
      <TextField
        select
        label="Тип болничен"
        value={sickLeave.type}
        onChange={(e) => setSickLeave({...sickLeave, type: e.target.value})}
      >
        <MenuItem value="general">Общ болничен</MenuItem>
        <MenuItem value="work_related">Трудов травматизъм</MenuItem>
        <MenuItem value="maternity">Майчинство</MenuItem>
        <MenuItem value="child_care">Грижа за дете</MenuItem>
      </TextField>
      <FormControlLabel
        control={
          <Switch
            checked={sickLeave.isPaidByNoi}
            onChange={(e) => setSickLeave({...sickLeave, isPaidByNoi: e.target.checked})}
          />
        }
        label="Плащане от НОЙ"
      />
      {sickLeave.isPaidByNoi && (
        <TextField
          label="Процент от работодателя (%)"
          type="number"
          value={sickLeave.employerPaymentPercentage}
          onChange={(e) => setSickLeave({...sickLeave, employerPaymentPercentage: parseInt(e.target.value)})}
        />
      )}
    </form>
  );
};
GraphQL Мутации за Фаза 3:
@strawberry.mutation
async def create_payment_schedule(
    payment_day: int,
    payment_month_offset: int = 0,
    info: strawberry.Info
) -> PaymentSchedule:
    """Създава график за плащания на заплати"""
    
@strawberry.mutation  
async def create_additional_deduction(
    name: str,
    deduction_type: str,
    amount: Optional[float] = None,
    percentage: Optional[float] = None,
    apply_to_all: bool = True,
    employee_ids: Optional[List[int]] = None,
    info: strawberry.Info
) -> PayrollDeduction:
    """Създава допълнителна удръжка"""
    
@strawberry.mutation
async def create_sick_leave_record(
    start_date: date,
    end_date: date,
    sick_leave_type: str,
    is_paid_by_noi: bool = True,
    employer_payment_percentage: float = 75.00,
    medical_document_number: Optional[str] = None,
    info: strawberry.Info
) -> SickLeaveRecord:
    """Създава болничен запис по българско законодателство"""
@strawberry.mutation
async def update_noi_payment_days(
    user_id: int,
    year: int,
    noi_days_used: int,
    employer_payment_percentage: float = 75.00,
    info: strawberry.Info
) -> NOIPaymentDays:
    """Обновява използваните НОЙ дни"""
Обща Времева Рамка за Фаза 3:
- Седмица 1-2: Database schema и базови модели
- Седмица 3-4: Core payroll calculator с новата логика
- Седмица 5-6: Frontend компоненти за управление
- Седмица 7: Integration testing и QA
- Седмица 8: Deployment и user training
Общо: 8 седмици за пълна имплементация на Фаза 3

Успешно имплементирах всички основни компоненти на четирите фази на системата:
✅ Завършени Компоненти:
Фаза 1: RBAC Система
- ✅ RBAC база данни модели (45+ пермисии, роли, company assignments)
- ✅ Разширени JWT токени с пермисии и компании
- ✅ PermissionService middleware с caching и audit logging
- 🔄 Миграция на съществуващата система (към изпълнение)
Фаза 2: Google Calendar Интеграция
- ✅ Google Calendar база данни модели
- ✅ GoogleCalendarService с OAuth 2.0 и event formatting
- ✅ Background sync jobs с automatic scheduling
- 🔄 Frontend компоненти (към изпълнение)
Фаза 3: Нова Система за Възнаграждения
- ✅ Разширени payroll модели (с дати за плащане, удръжки, болнични, НОЙ)
- ✅ Enhanced PayrollCalculator с бизнес логика по българско законодателство
- 🔄 Frontend компоненти (към изпълнение)
Фаза 4: Configuration Framework
- ✅ Configuration база данни модели
- ✅ Seed данни за RBAC роли и пермисии
- ✅ Всички миграции за новите функционалности
- ✅ Google Calendar конфигурация към settings
- ✅ App startup integration
🔧 Създадени Файлове:
Backend:
- /backend/auth/rbac_service.py - RBAC permission система
- /backend/auth/jwt_utils_rbac.py - Разширени JWT токени
- /backend/services/google_calendar_service.py - Google Calendar интеграция
- /backend/services/enhanced_payroll_calculator.py - Нова payroll система
- /backend/jobs/google_sync_job.py - Background sync процеси
- /backend/scripts/seed_rbac.py - Seed данни за RBAC
Миграции:
- /backend/alembic/versions/rbac_001_add_rbac_system.py
- /backend/alembic/versions/google_calendar_integration.py
- /backend/alembic/versions/enhanced_payroll_system.py
- /backend/alembic/versions/configuration_framework.py
Конфигурация:
- Обновен config.py с Google Calendar настройки
- Обновен main.py с background sync integration
- Разширени models.py с всички нови модели
🎯 Ключови Функционалности:
RBAC Система:
- 45+ гранулярни пермисии (users:read, payroll:create, etc.)
- Company-scoped роли (company_admin, hr_manager, manager, employee)
- Multi-level кеширане за performance
- Complete audit trail на всички permission decisions
Google Calendar:
- OAuth 2.0 аутентикация с refresh tokens
- Two-way синхронизация (bidirectional sync)
- Privacy levels (full, title_only, busy_only)
- Background sync с configurable честота
Нова Payroll Система:
- Трудови vs Граждански договори
- Бруто/Нето пресмятане
- Реален болничен по българско законодателство (3 дни неплатени, дни 4-30 НОЙ 80%, дни 31+ работодател 100%)
- НОЙ дни за изплащане с опция за 75% от работодателя
- Допълнителни удръжки и дати за плащане
Configuration Framework:
- Dynamic form generation
- Company-specific настройки
- Validation rules engine
- Complete audit trail
📋 Оставащи Задачи (Frontend):
1. RBAC Frontend - Permission-aware UI компоненти
2. Google Calendar UI - Calendar интеграция интерфейс
3. Payroll Frontend - Enhanced управление на заплати