# **Пълен Анализ на Бекенд Функционалността - Системен Одит**
## **Резюме на Одита**

Проведох задълбочен анализ на бекенда на WorkingTime система, фокусирайки се върху **Payroll изчисления** и **Time tracking функционалност** с цел **системен одит**. Анализът разкри **критични уязвимости** и **проблеми със съответствието**, които изискват незабавно внимание.

---

## **Критични Проблеми**

### 🔴 **Критични Уязвимости в Сигурността**

#### **1. Обход на Аутентикация в Kiosk Режим**
- **Локация**: `routers/kiosk.py:20`
- **Проблем**: `X-Kiosk-Secret` header е коментиран - **пълна липса на автентикация**
- **Рискове**: Всеки може да сканира QR кодове и да регистрира работно време
- **Влияние**: Директна възможност за фалшифициране на работно време

#### **2. Липса на Транзакционна Сигурност**
- **Локация**: `crud.py:1028-1267`
- **Проблем**: Операции с TimeLog и Payroll без атомарни транзакции
- **Рискове**: Частични актуализации, корупция на данни
- **Влияние**: Финансови загуби от неконсистентни данни

#### **3. Недостатъчна Валидация на Payroll**
- **Локация**: `payroll_calculator.py:78-87`
- **Проблем**: Няма валидация за минимална работна заплата
- **Рискове**: Незаконни конфигурации на заплати
- **Влияние**: Нарушения на българското трудово законодателство

### 🟡 **Проблеми в Съответствието (Compliance)**

#### **1. Нарушения на Българското Трудово Законодателство**
- **Налагаеми коефициенти**: 150% за извънредно време (делнични), 200% (празници)
- **Текущо**: Единен коефициент за всички извънредни часове
- **Максимален годишен извънреден труд**: 150 часа (не се следи)
- **Минимална почивка между смени**: 11 часа (не се валидира)

#### **2. Неточни Изчисления на Данъци**
- **Локация**: `payroll_calculator.py:262-284`
- **Проблем**: Данък се калкулира след осигуровки, но без валидация
- **Рискове**: Грешна данъчна основа
- **Влияние**: Наложителни корекции и глоби

---

## **Архитектурен Анализ**

### **1. Структура на Бекенда**

```
backend/
├── auth/           # JWT и сигурност ✅
├── database/       # SQLAlchemy модели ✅  
├── graphql/        # GraphQL API ⚠️ (липсващи валидации)
├── routers/        # REST API 🔴 (критични проблеми)
├── services/       # Business logic ⚠️ (precision проблеми)
├── jobs/           # Background jobs ✅
└── tests/          # Test suite 🟡 (broken references)
```

### **2. Основни Функции и Техните Проблеми**

#### **Authentication Functions**
- `create_tokens()` ✅ - Работи коректно
- `verify_and_decode_token()` ✅ - С key rotation
- `get_current_user()` ✅ - Правилна имплементация

#### **Payroll Functions** 
- `calculate()` ⚠️ - Floating-point precision проблеми
- `get_total_working_days_for_month()` 🟡 - Cache invalidation проблем
- `validate_payroll_config()` 🔴 - Липсва

#### **Time Tracking Functions**
- `start_time_log()` 🔴 - Без транзакционна защита
- `kiosk_scan()` 🔴 - Без автентикация
- `get_active_time_log()` ✅ - Работи коректно

---

## **Детайлен Анализ по Компоненти**

### **Payroll Calculator (`services/payroll_calculator.py`)**

#### **Силни Страни:**
- Комплексна логика за изчисления
- Поддръжка на бонуси и отпуски
- Правилни български данъчни ставки (в основата)

#### **Критични Проблеми:**
1. **Floating-Point Precision**: `round(сума, 2)` създава грешки при акумулация
2. **Липсваща Валидация**: Няма проверки за отрицателни ставки
3. **Overtime Logic**: Сложна логика с непокрити edge cases

### **Time Log Model (`database/models.py`)**

#### **Силни Страни:**
- Audit trail с IP адреси
- Геолокация поддръжка
- Различаване manual/automatic записи

#### **Критични Проблеми:**
1. **Missing Constraints**: Няма database валидации
2. **Overlap Detection**: Базова само, не покрива комплексни случаи
3. **Future Dating**: Възможни бъдещи записи

### **Kiosk Mode (`routers/kiosk.py`)**

#### **Критичен Проблем:**
```python
# ТЕКУЩО - РАЗКОМЕНТИРАНО!
# x_kiosk_secret: str = Header(..., alias="X-Kiosk-Secret")

# КРИТИЧНО: Всеки може да изпълни тази функция!
@router.post("/scan")
async def kiosk_scan(scan: KioskScan, db: AsyncSession = Depends(get_db)):
```

---

## **Мерки за Сигурност и Препоръки**

### **Незабавни Действия (Критични)**

#### **1. Поправка на Kiosk Автентикация**
```python
@router.post("/scan")
async def kiosk_scan(
    scan: KioskScan,
    db: AsyncSession = Depends(get_db),
    x_kiosk_secret: str = Header(..., alias="X-Kiosk-Secret"),
    x_device_id: str = Header(..., alias="X-Device-ID")
):
    if x_kiosk_secret != await get_kiosk_secret(db):
        raise HTTPException(401, "Invalid kiosk")
```

#### **2. Въвеждане на Transaction Safety**
```python
async def start_time_log(db: AsyncSession, user_id: int):
    async with db.begin():
        # Всички операции в една транзакция
        # Proper rollback при грешки
```

#### **3. Валидация на Минимална Заплата**
```python
def validate_payroll_config(hourly_rate: float):
    min_hourly = get_minimum_wage_bgn() / 168  # 168 часа месечно
    if hourly_rate < min_hourly:
        raise ValueError("Hourly rate below minimum wage")
```

### **Краткосрочни Мерки (Среден Приоритет)**

#### **1. Поправка на Bulgarian Labor Law Compliance**
- Коректни коефициенти за извънредно време
- Валидация за 150-часов годишен лимит
- 11-часова минимална почивка между смени

#### **2. Подобряване на Audit Trail**
- Добавяне на immutable флагове за одобрени записи
- Криптографски checksums за payroll изчисления
- Пълен лог на промени в geolocation

#### **3. Performance Optimizations**
- По-добро cache invalidation
- Batch операции за schedule създаване
- Database индекси за често търсени полета

---

## **Risk Assessment Matrix**

| Категория | Ниво на Риск | Финансово Влияние | Правно Влияние | Приоритет |
|-----------|--------------|-------------------|----------------|-----------|
| Kiosk Auth Bypass | **Критичен** | Висок | Среден | **1** |
| Payroll Integration | **Критичен** | Много Висок | Висок | **1** |
| Time Log Manipulation | **Висок** | Висок | Среден | **2** |
| BG Law Compliance | **Висок** | Среден | Много Висок | **2** |
| Floating Point Errors | **Среден** | Среден | Нисък | **3** |

---

## **Заключение и Следващи Стъпки**

**Системата НЕ е готова за production употреба** в текущия си вид поради:

1. **Критични уязвимости** в сигурността (особено kiosk режим)
2. **Проблеми със съответствието** на българското законодателство
3. **Рискове за интегритета** на финансовите данни

**Препоръчителен План:**
- **Седмица 1**: Поправка на критичните проблеми с автентикацията
- **Седмица 2-3**: Внедряване на compliance проверки
- **Седмица 4**: Подобряване на тест покритието и performance

След изпълнение на тези мерки, системата ще бъде готова за безопасна експлоатация съгласно българското законодателство и индустриалните стандарти за сигурност.

---

## **Приложение: Детайлен Технически Анализ**

### **Authentication & Security Functions**

#### **JWT Token Management (`/backend/auth/jwt_utils.py`)**

##### `create_tokens(db, user_id, email, ip_address=None, user_agent=None)`
- **Локация**: `/backend/auth/jwt_utils.py:19`
- **Предназначение**: Създава access и refresh JWT token двойка
- **Параметри**: Database session, user ID, email, IP адрес, user agent
- **Връща**: Tuple (access_token, refresh_token)
- **Употреба**: При login и refresh на токени
- **Зависимости**: AuthKey, UserSession

##### `verify_and_decode_token(db, token)`
- **Локация**: `/backend/auth/jwt_utils.py:73`
- **Предназначение**: Валидира JWT токени с key rotation
- **Параметри**: Database session, JWT token string
- **Връща**: Decoded claims dict или None
- **Употреба**: За всички автентикирани API заявки

##### `get_current_user(request, db)`
- **Локация**: `/backend/auth/jwt_utils.py:116`
- **Предназначение**: Основна authentication dependency
- **Параметри**: FastAPI Request, database session
- **Връща**: User schema object
- **Употреба**: FastAPI dependency в защитените endpoints

### **Payroll Calculation Functions**

#### **PayrollCalculator (`/backend/services/payroll_calculator.py`)**

##### `PayrollCalculator.__init__(db)`
- **Локация**: `/backend/services/payroll_calculator.py:15`
- **Предназначение**: Инициализация с caching
- **Функции**: Working days cache за performance

##### `get_total_working_days_for_month(user_id, year, month)`
- **Локация**: `/backend/services/payroll_calculator.py:19`
- **Предназначение**: Калкулира работни дни (безweekends и празници)
- **Връща**: Integer брой работни дни
- **Проблем**: Cache invalidation

##### `calculate(user_id, start_date, end_date)`
- **Локация**: `/backend/services/payroll_calculator.py:72`
- **Предназначение**: Основен payroll изчислителен engine
- **Процес**: 
  - Взима payroll конфигурация
  - Обработва time logs и schedules
  - Калкулира regular vs overtime
  - Прилага break deduction
- **Връща**: Dict с часове, суми, детайли
- **Критични проблеми**: Floating-point precision, липсваща валидация

### **Time Tracking Functions**

#### **Time Log CRUD (`/backend/crud.py`)**

##### `start_time_log(db, user_id, start_time=None, end_time=None, ...)`
- **Локация**: `crud.py:1028`
- **Предназначение**: Създаване на нов time log entry
- **Критичен проблем**: Без транзакционна защита
- **Рискове**: Race conditions, частични актуализации

##### `kiosk_scan(scan, db)`
- **Локация**: `/backend/routers/kiosk.py:16`
- **Предназначение**: QR code scanning за time tracking
- **Процес**: QR token validation, in/out action
- **Критичен проблем**: Коментиран autentikasyon header
- **Рискове**: Пълен обход на сигурността

##### `get_active_time_log(db, user_id)`
- **Локация**: `crud.py:1100`
- **Предназначение**: Намира активен time log
- **Състояние**: Работи коректно

### **Database Models Analysis**

#### **User Model (`database/models.py:75`)**
- **Предназначение**: Централен user entity със security полета
- **Ключови полета**: email, hashed_password, role_id, company_id, failed_login_attempts, locked_until, qr_token
- **Релации**: TimeLog, Payroll, Payslip, WorkSchedule, Notification, LeaveRequest

#### **TimeLog Model (`database/models.py:149`)**
- **Предназначение**: Записи за работно време
- **Ключови полета**: start_time, end_time, is_manual, break_duration_minutes, latitude, longitude
- **Проблеми**: Lipсващи database constraints

#### **Payroll Model (`database/models.py:167`)**
- **Предназначение**: Payroll конфигурация потребител/позиция
- **Ключови полета**: hourly_rate, monthly_salary, overtime_multiplier, tax_percent, insurance_percent
- **Проблеми**: Няма negative value checks

#### **Payslip Model (`database/models.py:191`)**
- **Предназначение**: Генерирани payslip записи
- **Ключови полета**: period_start/end, total_regular_hours, total_overtime_hours, amounts, tax/insurance
- **Проблеми**: Decimal precision може да е недостатъчна

### **API Endpoints Analysis**

#### **GraphQL Queries (`graphql/queries.py`)**

##### `me(info)`
- **Локация**: `queries.py:19`
- **Предназначение**: Връща текущия автентиран user
- **Състояние**: Работи коректно

##### `active_time_log(info)`
- **Локация**: `queries.py:26`
- **Предназначение**: Взима активен time log
- **Състояние**: Работи коректно

##### `users(info, skip, limit, search, sort_by, sort_order)`
- **Локация**: `queries.py:44`
- **Предназначение**: Paginated user listing за admins
- **Проблеми**: Input validation липсва

#### **GraphQL Mutations (`graphql/mutations.py`)**

##### `update_user_payroll(payroll, info)`
- **Локация**: `mutations.py:415-451`
- **Предназначение**: Актуализация на payroll конфигурация
- **Критичен проблем**: Няма валидация за минимална заплата

##### `generate_payslip(user_id, period_start, period_end, info)`
- **Локация**: `mutations.py:493-518`
- **Предназначение**: Генериране на payslip
- **Проблеми**: Authorization checks insufficient

---

## **Допълнителни Технически Детайли**

### **Environment Configuration**

#### **Database Configuration**
- **Engine**: Async SQLAlchemy с asyncpg driver
- **Connection Pooling**: SQLAlchemy defaults
- **Session Management**: LockedSession с asyncio.Lock

#### **Security Configuration**
- **JWT**: HS256 с key rotation
- **Password Hashing**: Argon2
- **CORS**: Конфигурируеми origins
- **Timezone**: Europe/Sofia

#### **Dependencies**
- **Web Framework**: FastAPI 0.128.0
- **Database**: SQLAlchemy 2.0.45, asyncpg 0.31.0
- **Authentication**: Authlib 1.5.1, passlib 1.7.4
- **GraphQL**: Strawberry GraphQL 0.288.2
- **Email**: fastapi-mail 1.4.1
- **OCR**: pytesseract
- **Background Jobs**: APScheduler 3.10.4

### **Security Middleware**
- **SecurityHeadersMiddleware**: HSTS, X-Content-Type-Options, X-Frame-Options, CSP
- **Authentication**: JWT с refresh tokens
- **Authorization**: Role-based access control
- **Audit Logging**: Комплексен audit trail

### **Performance Optimizations**
- **Caching**: Auth keys cached in memory
- **Connection Pooling**: Async database connections
- **Working Days Cache**: Cached в payroll calculator
- **DataLoader**: GraphQL N+1 query prevention

---

**Отчет създаден на**: 4 Февруари 2026
**Анализатор**: AI System Auditor
**Версия на системата**: Chronos API v1.3.0.0
**Фокус**: Payroll и Time Tracking Security Audit