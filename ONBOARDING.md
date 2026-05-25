# Chronos — Onboarding за младши програмист

> **Версия:** 3.7.2.0 | **Последна актуализация:** 25 май 2026

Този документ е пълен наръчник за новопостъпил програмист в проекта Chronos. Тук ще намериш всичко необходимо, за да започнеш да работиш ефективно — от общата картина на системата до конкретни примери за добавяне на нова функционалност.

---

## Съдържание

1. [Какво е Chronos?](#1-какво-е-chronos)
2. [Технологичен стек](#2-технологичен-стек)
3. [Структура на проекта](#3-структура-на-проекта)
4. [Поток на данните](#4-поток-на-данните)
5. [Как да добавим нова функционалност](#5-как-да-добавим-нова-функционалност)
6. [Пълен пример: Категории разходи](#6-пълен-пример-категории-разходи)
7. [Обработка на грешки](#7-обработка-на-грешки)
8. [Cheatsheet с команди](#8-cheatsheet-с-команди)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Какво е Chronos?

Chronos е **цялостна ERP система** за управление на бизнес процеси в малки и средни предприятия. Системата покрива пълния цикъл от отчитане на работно време, през заплати и складово стопанство, до счетоводство и флот мениджмънт.

### Основни модули

Системата е изградена на **модулен принцип** — има 4 задължителни (core) модула и 7 опционални, които могат да се включват/изключват за всеки клиент:

| Модул | Тип | Описание |
|-------|-----|----------|
| **shifts** | Core | Управление на смени, работно време, присъствия |
| **accounting** | Core | Счетоводство, фактури, плащания, ДДС |
| **confectionery** | Core | Производство на сладкарски изделия, рецепти, съставки |
| **cost_centers** | Core | Разпределение на разходи по центрове |
| **salaries** | Optional | Заплати, бонуси, удръжки, осигуровки |
| **kiosk** | Optional | Киоск режим за служители (clock in/out) |
| **integrations** | Optional | Външни интеграции (банки, касови апарати) |
| **notifications** | Optional | Известия, email, SMS |
| **fleet** | Optional | Флот мениджмънт — автомобили, шофьори, маршрути |
| **inventory** | Optional | Складово стопанство, стоки, доставки |
| **payroll** | Optional | Пълна система за заплати и осигуровки |

### Потребителски роли

Системата има **12 нива на достъп**, подредени по йерархия:

1. **super_admin** — пълен достъп до всичко, включително системни настройки
2. **admin** — администраторски достъп без системни настройки
3. **manager** — управление на екипи и одобрения
4. **accountant** — счетоводни операции
5. **hr_manager** — човешки ресурси, заплати
6. **warehouse_manager** — складови операции
7. **production_manager** — производство и рецепти
8. **fleet_manager** — флот мениджмънт
9. **supervisor** — надзор на смени
10. **employee** — обикновен служител (вижда само своите данни)
11. **kiosk** — ограничен достъп за киоск режим
12. **viewer** — само четене

### Технологична архитектура

Chronos е **монолитно приложение** с два основни компонента:

- **Backend:** Python FastAPI приложение, което предоставя GraphQL API
- **Frontend:** React Single Page Application (SPA), което комуникира с backend-а чрез GraphQL

Двата компонента работят в Docker контейнери и комуникират помежду си чрез HTTP.

---

## 2. Технологичен стек

### Python 3.13

Python е основният език за backend частта на Chronos. Използваме версия 3.13, която е най-новата стабилна версия към момента. Python е избран заради богатата си екосистема от библиотеки за уеб разработка, лесната интеграция с бази данни и отличната поддръжка на асинхронно програмиране. В проекта използваме модерен Python синтаксис — type hints навсякъде, dataclasses, pattern matching (match/case), и async/await за всички I/O операции. Кодът следва PEP 8 стандарти и се проверява автоматично с Ruff linter.

### FastAPI

FastAPI е модерен уеб фреймуърк за Python, изграден върху Starlette и Pydantic. Той е избран заради високата си производителност (сравнима с Node.js и Go), автоматичната генерация на OpenAPI документация и вградената поддръжка на async/await. В Chronos FastAPI служи като HTTP сървър, който приема GraphQL заявки и ги насочва към Strawberry resolver-ите. Фреймуъркът също така управлява middleware слоевете — CORS, authentication, rate limiting и module throttling. Конфигурацията на FastAPI се намира в `backend/main.py`, където се регистрират всички middleware и routes.

### Strawberry GraphQL

Strawberry е Python библиотека за GraphQL, която използва type hints вместо DSL (domain-specific language). За разлика от Graphene (по-старата алтернатива), Strawberry генерира GraphQL схемата директно от Python типовете, което прави кода по-четим и type-safe. В Chronos всички GraphQL типове, мутации и заявки са дефинирани със Strawberry декоратори (`@strawberry.type`, `@strawberry.mutation`, `@strawberry.field`). Използваме `strawberry.auto` за автоматично мапване на полета от Pydantic схеми към GraphQL типове. Схемата се компилира при стартиране на приложението и се сервира на endpoint `/graphql`.

### SQLAlchemy 2.0 (async)

SQLAlchemy е ORM (Object-Relational Mapping) библиотека, която мапва Python класове към таблици в базата данни. Версия 2.0 въвежда пълна поддръжка на асинхронни сесии чрез `AsyncSession`, което е критично за производителността на FastAPI. В Chronos използваме декларативен стил (`DeclarativeBase`) за дефиниране на модели. Всеки модел наследява `Base` класа и дефинира колони, релации и индекси. **Важно:** използваме `selectinload` за eagerly loading на релации, защото lazy loading не работи с асинхронни сесии (хвърля `MissingGreenlet` грешка). Всички модели са дефинирани в `backend/database/models.py`.

### PostgreSQL 18

PostgreSQL е релационна база данни с отворен код, избрана заради надеждността си, поддръжката на JSONB полета, full-text search и разширения като `uuid-ossp`. В Chronos PostgreSQL съхранява всички бизнес данни — потребители, компании, смени, фактури, складови записи и т.н. Базата данни се управлява чрез Alembic миграции и се достъпва от backend-а чрез async connection pool (настройки: `pool_size=20, max_overflow=10, pool_pre_ping=True, pool_recycle=3600`). Connection string-ът се конфигурира чрез environment variables (`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`).

### Alembic

Alembic е инструмент за управление на миграции на базата данни, интегриран със SQLAlchemy. Всяка промяна в структурата на базата данни (нова таблица, колона, индекс) се записва като миграционен файл в `backend/alembic/versions/`. Миграциите са версионирани и могат да се прилагат/връщат последователно. В Chronos имаме над 67 миграции, които отразяват еволюцията на схемата. Командите за работа с Alembic са: `alembic revision --autogenerate -m "описание"` (създаване на нова миграция), `alembic upgrade head` (прилагане на всички неприложени миграции), `alembic downgrade -1` (връщане на последната миграция). Преди създаване на нова миграция винаги проверяваме `alembic heads` — трябва да има точно един head.

### Pydantic V2

Pydantic е библиотека за валидация и сериализация на данни, изградена върху type hints. Версия 2 е значително по-бърза от V1 благодарение на Rust ядрото си. В Chronos Pydantic се използва на два места: (1) за валидация на входни данни в GraphQL мутациите и (2) като междинен слой между SQLAlchemy моделите и GraphQL типовете. Всяка Pydantic схема има `model_config = ConfigDict(from_attributes=True)`, което позволява автоматично конвертиране от ORM обекти. Схемите са организирани в `backend/schemas/` — по един файл за всеки домейн (user.py, company.py, shifts.py и т.н.).

### React 19

React е JavaScript библиотека за изграждане на потребителски интерфейси, разработена от Meta. Версия 19 въвежда подобрения в производителността и нови hooks. В Chronos React е основата на frontend-а — всеки екран е React компонент, който комуникира с backend-а чрез GraphQL. Използваме функционални компоненти с hooks (useState, useEffect, useMemo, useCallback) и Context API за глобално състояние. Компонентите са организирани в `frontend/src/components/` (преизползваеми UI елементи) и `frontend/src/pages/` (цели страници).

### TypeScript

TypeScript е типизиран superset на JavaScript, разработен от Microsoft. Той добавя статични типове, които се проверяват при компилация и елиминират цели класове грешки. В Chronos целият frontend код е написан на TypeScript. Типовете за GraphQL операции се генерират автоматично от `graphql-codegen` (виж по-долу), което гарантира, че frontend-ът и backend-ът винаги са синхронизирани. Конфигурацията на TypeScript е в `frontend/tsconfig.json` и включва strict mode за максимална безопасност.

### Vite

Vite е модерен build tool за frontend приложения, създаден от автора на Vue.js. Той е значително по-бърз от Webpack благодарение на native ES modules в development и Rollup за production builds. В Chronos Vite управлява development сървъра (с Hot Module Replacement за мигновено отразяване на промени) и production build-а. Конфигурацията е в `frontend/vite.config.ts` и включва proxy за GraphQL endpoint-а, path aliases за по-чисти import-и, и `esbuild.drop: ['console', 'debugger']` за production builds (автоматично премахване на console.log и debugger statements).

### Apollo Client

Apollo Client е най-популярната GraphQL клиентска библиотека за React. Тя управлява кеширането на данни, автоматичното обновяване на UI при мутации, optimistic updates и error handling. В Chronos Apollo Client е конфигуриран в `frontend/src/apolloClient.ts` с HTTP link към `/graphql`, автоматично добавяне на authentication cookies и CSRF token. Използваме `useQuery` за четене на данни и `useMutation` за промени. Всяка GraphQL операция е дефинирана в отделен файл под `frontend/src/graphql/` (никога inline в компонентите).

### MUI 7 (Material UI)

MUI е React компонентна библиотека, базирана на Material Design. Версия 7 е най-новата и включва подобрения в производителността и достъпността. В Chronos MUI предоставя всички UI компоненти — бутони, текстови полета, таблици, диалози, навигация, дати и т.н. Използваме `ThemeProvider` за глобална тема с custom цветове и типография. Grid системата използва новия синтаксис `size={{ xs: 12, sm: 6 }}` (не стария `item xs={12} sm={6}`). Компонентите са стилизирани с `sx` prop или `styled()` за по-сложни случаи.

### GraphQL Codegen

GraphQL Code Generator е инструмент, който автоматично генерира TypeScript типове от GraphQL схеми и операции. В Chronos конфигурацията е в `frontend/codegen.yml` и генерира `frontend/src/generated/graphql.ts` — файл с всички типове, hooks и документи. Командата `npm run codegen` трябва да се изпълнява след всяка промяна в GraphQL операциите. Това гарантира, че TypeScript типовете винаги съвпадат с реалната GraphQL схема и елиминира runtime грешки от несъответствие.

### Vitest

Vitest е тестов фреймуърк за JavaScript/TypeScript, изграден върху Vite. Той е съвместим с Jest API (`describe`, `it`, `expect`, `vi.fn`, `vi.mock`), но е значително по-бърз благодарение на Vite's native ES modules. В Chronos използваме Vitest за unit и integration тестове на frontend компонентите. Тестовете са в `frontend/src/__tests__/` и се изпълняват с `npm run test` (watch mode) или `npm run test:run` (еднократно). Mock-ването на GraphQL операции става с `vi.mock` и custom mock providers.

### Playwright

Playwright е инструмент за end-to-end (E2E) тестване на уеб приложения, разработен от Microsoft. Той поддържа Chromium, Firefox и WebKit и може да симулира реални потребителски взаимодействия — кликвания, попълване на форми, навигация. В Chronos Playwright тестовете са в `frontend/e2e/` и се изпълняват с `npm run test:e2e`. Те тестват критични потребителски потоци — логин, създаване на смяна, одобрение на молба и т.н.

### Docker & Docker Compose

Docker е платформа за контейнеризация, която опакова приложението и всички негови зависимости в изолиран контейнер. Docker Compose позволява дефиниране на multi-container приложения в един YAML файл. В Chronos `docker-compose.yml` дефинира 4 основни сервиса: `db` (PostgreSQL), `backend` (FastAPI), `frontend` (React/Vite), и `redis` (за кеширане, ако е активиран). Командата `docker compose up -d` стартира цялата система. За development използваме profiles: `docker compose --profile dev up -d` стартира с hot reload.

### Ruff

Ruff е изключително бърз Python linter и formatter, написан на Rust. Той заменя едновременно flake8, isort, black и pyupgrade с един инструмент, който е 10-100 пъти по-бърз. В Chronos Ruff е конфигуриран в `backend/pyproject.toml` с правила: select E,F,I,N,UP,B,SIM; ignore E501,E402,N999,SIM108,SIM115. Командата `ruff check .` проверява кода за грешки, а `ruff format .` го форматира. Ruff се изпълнява автоматично в CI/CD pipeline-а и като pre-commit hook.

---

## 3. Структура на проекта

### Обща структура

```
WorkingTime/
├── backend/              # Python FastAPI приложение
├── frontend/             # React SPA
├── chronos-gateway/      # Reverse proxy gateway (desktop app)
├── scripts/              # Deploy, backup, rollback скриптове
├── docker-compose.yml    # Docker Compose конфигурация
├── .env                  # Environment variables (НЕ се commit-ва)
├── AGENTS.md             # AI agent контекст (ignored by git)
└── ONBOARDING.md         # Този документ
```

### Backend структура

```
backend/
├── main.py               # Entry point — FastAPI app, middleware, routes
├── config.py             # Configuration от environment variables
├── exceptions.py         # Йерархия на грешките (CHRONOSException и наследници)
├── init_db.py            # Инициализация на базата данни
│
├── database/
│   ├── models.py         # ВСИЧКИ SQLAlchemy модели (~80+ модела, 180KB)
│   ├── connection.py     # Async engine и session factory
│   ├── base.py           # DeclarativeBase за моделите
│   └── transaction_manager.py  # atomic_transaction context manager
│
├── alembic/
│   ├── alembic.ini       # Alembic конфигурация
│   ├── env.py            # Alembic environment (async migration)
│   └── versions/         # Миграционни файлове (67+)
│
├── schemas/              # Pydantic V2 схеми (23 модула)
│   ├── base.py           # Базови схеми и конфигурация
│   ├── auth.py           # Authentication схеми
│   ├── user.py           # User, Role, Permission
│   ├── company.py        # Company, Branch, Department
│   ├── shifts.py         # Shift, ShiftType, Schedule
│   ├── accounting.py     # Invoice, Payment, Account
│   ├── production.py     # Recipe, Ingredient, Batch
│   ├── payroll.py        # Salary, Payslip, Deduction
│   ├── inventory.py      # Product, Warehouse, Stock
│   ├── vehicle.py        # Vehicle, Trip, FuelLog
│   ├── leave.py          # LeaveRequest, LeaveType
│   ├── notification.py   # Notification, Template
│   ├── cost_center.py    # CostCenter, Allocation
│   ├── calendar.py       # Calendar, Holiday
│   ├── contract.py       # Contract, Amendment
│   ├── logistics.py      # Route, Delivery
│   ├── trz.py            # TRZ специфични схеми
│   ├── access_control.py # Permission, Role mapping
│   └── system.py         # SystemConfig, AuditLog
│
├── graphql/
│   ├── schema.py         # Компилация на GraphQL схемата
│   ├── module_middleware.py  # Module throttling (209 мапнати операции)
│   │
│   ├── types/            # GraphQL типове (Strawberry)
│   │   ├── __init__.py   # Регистрация на всички типове
│   │   ├── user.py       # UserType, RoleType
│   │   ├── company.py    # CompanyType, BranchType
│   │   ├── shifts.py     # ShiftType, ScheduleType
│   │   ├── accounting.py # InvoiceType, PaymentType
│   │   └── ...           # Още ~20 файла
│   │
│   ├── mutations/        # GraphQL мутации (22 класа)
│   │   ├── __init__.py   # Регистрация на всички мутации
│   │   ├── auth.py       # login, logout, refreshToken
│   │   ├── user.py       # createUser, updateUser, deleteUser
│   │   ├── company.py    # createCompany, updateCompany
│   │   ├── shifts.py     # createShift, approveShift
│   │   ├── accounting.py # createInvoice, approvePayment
│   │   ├── payroll.py    # calculateSalary, generatePayslip
│   │   ├── inventory.py  # createProduct, updateStock
│   │   └── ...           # Още ~15 файла
│   │
│   └── queries/          # GraphQL заявки
│       ├── __init__.py   # Регистрация на всички заявки
│       ├── user.py       # users, user, me
│       ├── company.py    # companies, company
│       ├── shifts.py     # shifts, shift, myShifts
│       └── ...           # Още ~15 файла
│
├── services/             # Бизнес логика
│   ├── auth_service.py   # Authentication и token management
│   ├── user_service.py   # User CRUD и валидация
│   ├── shift_service.py  # Shift бизнес логика
│   ├── invoice_service.py # Invoice status transitions
│   ├── module_service.py # Module enable/disable
│   └── ...               # Още ~20 файла
│
├── repositories/         # Data access layer
│   ├── user_repository.py
│   ├── shift_repository.py
│   ├── invoice_repository.py
│   └── ...               # Един repository за всеки модел
│
├── auth/
│   ├── jwt_handler.py    # JWT token generation/validation
│   ├── rbac_service.py   # Role-based access control
│   ├── limiter.py        # Rate limiting
│   └── csrf.py           # CSRF protection
│
├── utils/
│   ├── json_type.py      # JSONScalar за GraphQL
│   ├── encryption.py     # AES encryption utilities
│   ├── date_utils.py     # Date/time helpers
│   └── currency.py       # Currency formatting
│
└── tests/
    ├── test_pydantic_schemas.py  # 25 теста за Pydantic схеми
    ├── test_auth.py              # Authentication тестове
    ├── test_shifts.py            # Shift тестове
    └── ...
```

### Frontend структура

```
frontend/
├── index.html            # HTML entry point
├── vite.config.ts        # Vite конфигурация
├── tsconfig.json         # TypeScript конфигурация
├── codegen.yml           # GraphQL Codegen конфигурация
├── package.json          # Dependencies и scripts
│
├── src/
│   ├── main.tsx          # React entry point
│   ├── App.tsx           # Root компонент с routing
│   ├── apolloClient.ts   # Apollo Client конфигурация
│   ├── theme.ts          # MUI тема (цветове, типография)
│   │
│   ├── components/       # Преизползваеми UI компоненти
│   │   ├── Layout/       # AppShell, Sidebar, Header
│   │   ├── DataTable/    # Generic data table с пагинация
│   │   ├── FormFields/   # ValidatedTextField, DateField
│   │   ├── Modals/       # ConfirmDialog, FormDialog
│   │   └── ...           # Още ~50 компонента
│   │
│   ├── pages/            # Страници (routes)
│   │   ├── DashboardPage.tsx
│   │   ├── ShiftsPage.tsx
│   │   ├── LeavesPage.tsx
│   │   ├── InvoicesPage.tsx
│   │   ├── EmployeesPage.tsx
│   │   └── ...           # Още ~30 страници
│   │
│   ├── graphql/          # GraphQL операции
│   │   ├── queries/      # useQuery дефиниции
│   │   │   ├── users.ts
│   │   │   ├── shifts.ts
│   │   │   └── ...
│   │   ├── mutations/    # useMutation дефиниции
│   │   │   ├── auth.ts
│   │   │   ├── shifts.ts
│   │   │   └── ...
│   │   └── fragments/    # GraphQL fragments
│   │
│   ├── generated/
│   │   └── graphql.ts    # AUTO-GENERATED — не се редактира ръчно!
│   │
│   ├── hooks/            # Custom React hooks
│   │   ├── useError.ts   # Error handling hook
│   │   ├── useAuth.ts    # Authentication hook
│   │   ├── usePagination.ts
│   │   └── ...
│   │
│   ├── contexts/         # React Context providers
│   │   ├── AuthContext.tsx
│   │   ├── CurrencyContext.tsx
│   │   ├── ModuleContext.tsx
│   │   └── ThemeContext.tsx
│   │
│   ├── utils/            # Utility функции
│   │   ├── dateUtils.ts  # formatDate, parseDate (dayjs)
│   │   ├── formatters.ts # formatCurrencyValue
│   │   └── validators.ts # Zod схеми
│   │
│   └── __tests__/        # Vitest тестове
│       ├── components/
│       └── pages/
│
├── e2e/                  # Playwright E2E тестове
│   ├── login.spec.ts
│   ├── shifts.spec.ts
│   └── ...
│
└── public/               # Статични файлове
    └── favicon.ico
```

### Ключови конфигурационни файлове

| Файл | Описание |
|------|----------|
| `.env` | Environment variables (DB credentials, JWT secret, API keys) — **НЕ се commit-ва** |
| `docker-compose.yml` | Docker Compose конфигурация за целия стек |
| `backend/pyproject.toml` | Python dependencies и Ruff конфигурация |
| `frontend/package.json` | Node.js dependencies и npm scripts |
| `frontend/codegen.yml` | GraphQL Code Generator конфигурация |
| `frontend/vite.config.ts` | Vite build и dev server конфигурация |

---

## 4. Поток на данните

### Обща архитектура

```
┌─────────────────────────────────────────────────────────────────┐
│                        BROWSER (React)                           │
│  ┌──────────┐    ┌──────────────┐    ┌───────────────────────┐  │
│  │ Component │───▶│ useQuery/    │───▶│ Apollo Client         │  │
│  │ (MUI)    │◀───│ useMutation  │◀───│ (cache + HTTP link)   │  │
│  └──────────┘    └──────────────┘    └───────────┬───────────┘  │
└──────────────────────────────────────────────────┼──────────────┘
                                                   │ HTTP POST
                                                   │ /graphql
                                                   │ + cookies
                                                   │ + CSRF token
┌──────────────────────────────────────────────────┼──────────────┐
│                     FASTAPI SERVER                ▼              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Middleware Stack                                         │   │
│  │ CORS → Auth → CSRF → Module Throttle → Rate Limit       │   │
│  └──────────────────────┬───────────────────────────────────┘   │
│                         ▼                                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Strawberry GraphQL Engine                                │   │
│  │ schema.py → Query/Mutation resolvers                     │   │
│  └──────────────────────┬───────────────────────────────────┘   │
│                         ▼                                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Service Layer (бизнес логика)                            │   │
│  │ Валидация, оркестрация, permission checks                │   │
│  └──────────────────────┬───────────────────────────────────┘   │
│                         ▼                                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Repository Layer (data access)                           │   │
│  │ db.add() + db.flush() — НИКОГА db.commit()               │   │
│  └──────────────────────┬───────────────────────────────────┘   │
│                         ▼                                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ SQLAlchemy AsyncSession                                  │   │
│  │ Connection pool → PostgreSQL                             │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                                   │
                                                   ▼
                              ┌──────────────────────────────────┐
                              │       PostgreSQL 18              │
                              │  (67+ таблици, миграции)         │
                              └──────────────────────────────────┘
```

### Authentication flow

1. **Login:** Потребителят изпраща email + password → `login` mutation → backend валидира → генерира JWT access token (15 мин) + refresh token (7 дни) → записва ги в HttpOnly cookies → връща user data
2. **Заявки:** Apollo Client автоматично изпраща cookies с всяка заявка → Auth middleware валидира JWT → RBAC service проверява permissions → resolver изпълнява операцията
3. **Token refresh:** Когато access token изтече, frontend извиква `refreshToken` mutation → backend валидира refresh token → генерира нов access token
4. **Logout:** `logout` mutation → backend изтрива cookies → frontend пренасочва към login страница

### Transaction management

#### Защо не commit-ваме директно в repository-ите?

В Chronos следваме **строг separation of concerns** — всеки слой има ясна отговорност:

- **Repository layer:** Само подготвя данните (`db.add()`, `db.flush()`) — **никога не commit-ва**
- **Service layer:** Координира бизнес логиката — **никога не commit-ва**
- **Mutation layer:** Контролира transaction boundaries — **единственият слой, който commit-ва**

**Защо това е важно?**

Ако repository-ите commit-ваха сами, щяхме да имаме сериозни проблеми:

1. **Невъзможност за отмяна:** Ако mutation изпълнява 3 операции и втората се провали, първата вече е commit-ната и не може да се отмени
2. **Нарушена консистентност:** Частично записани данни оставят базата в невалидно състояние
3. **Трудно тестване:** Не можеш да тестваш операция без реално да промениш базата данни
4. **Невъзможност за batch операции:** Не можеш да групираш множество операции в една транзакция

**Пример за проблем:**

```python
# ГРЕШЕН ПОДХОД (ако repository commit-ваше):
async def create_order_with_items(db, order_data, items_data):
    order = await order_repo.create(db, order_data)  # commit тук!
    
    for item in items_data:
        await item_repo.create(db, item)  # commit тук!
        # Ако третият item се провали, първите два вече са записани
        # → Поръчка с непълни items = невалидно състояние!
```

**Правилен подход:**

```python
# ПРАВИЛНО: mutation контролира commit-а
async def create_order_with_items(db, order_data, items_data):
    order = await order_repo.create(db, order_data)  # само flush
    
    for item in items_data:
        await item_repo.create(db, item)  # само flush
    
    # Ако всичко е OK, commit-ваме ВСИЧКО наведнъж
    await db.commit()
    # Ако нещо се провали, нищо не е записано
```

#### Какво е атомична транзакция?

**Атомична транзакция** е група от операции, които се изпълняват като **едно цяло** — или всички успяват, или нито една не се записва. Това е фундаментален принцип на релационните бази данни (ACID properties).

**Защо я използваме?**

Когато бизнес операция изисква промяна в множество таблици, трябва да гарантираме, че:
- Ако **всички** операции успеят → commit-ваме
- Ако **поне една** операция се провали → rollback-ваме всичко

**Пример от реалния свят:**

Създаване на фактура с плащане:
1. Създай `Invoice` запис
2. Създай `Payment` запис
3. Обнови `Account` баланс
4. Създай `AuditLog` запис

Ако стъпка 3 се провали (например недостатъчен баланс), искаме **всички** предишни стъпки да се отменят — иначе ще имаме фактура без плащане, или плащане без фактура.

#### Два модела за управление на транзакции

**Модел 1: Прост CRUD (ръчен commit)**

За операции, които променят само една таблица:

```python
# В mutation resolver
result = await service.create_item(db, data)
await db.commit()  # Ръчен commit
await db.refresh(result)
return result
```

**Модел 2: Сложни операции (atomic_transaction)**

За операции, които променят множество таблици:

```python
from backend.database.transaction_manager import atomic_transaction

async def complex_mutation(db: AsyncSession, ...):
    async with atomic_transaction(db) as tx:
        # Всички операции в този блок са в една транзакция
        item = await repo1.create(tx, data1)
        related = await repo2.create(tx, data2)
        await service.update(tx, item.id, ...)
        
        # commit става АВТОМАТИЧНО при излизане от блока
        # rollback става АВТОМАТИЧНО при грешка
```

**Предимства на `atomic_transaction`:**

1. **Автоматичен rollback:** Ако се хвърли exception, транзакцията се отменя автоматично
2. **Автоматичен commit:** Ако всичко е OK, commit-ва се автоматично
3. **Ясни граници:** Виждаш точно кои операции са в една транзакция
4. **По-малко boilerplate:** Не трябва ръчно да пишеш try/except/rollback

### DataLoader pattern

За предотвратяване на N+1 query проблема, Chronos използва DataLoader за batch loading на релации:

```python
# Вместо N+1:
for shift in shifts:
    user = await db.get(User, shift.user_id)  # N заявки!

# С DataLoader:
user_loader = DataLoader(load_users_batch)
for shift in shifts:
    user = await user_loader.load(shift.user_id)  # 1 batch заявка
```

---

## 5. Как да добавим нова функционалност

Добавянето на нова функционалност в Chronos следва **строг layered подход** — всеки слой има ясна отговорност и комуникира само със съседните слоеве.

### Стъпка 1: SQLAlchemy модел

**Файл:** `backend/database/models.py`

Дефинираш нов ORM модел, който наследява `Base`:

```python
class ExpenseCategory(Base):
    __tablename__ = "expense_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    company: Mapped["Company"] = relationship(back_populates="expense_categories")
```

**Правила:**

- Винаги използвай `Mapped[]` type hints
- Винаги добавяй `ForeignKey` за релации
- Използвай `server_default=func.now()` за timestamps (не Python `datetime.now()`)

### Стъпка 2: Alembic миграция

```bash
cd backend
alembic revision --autogenerate -m "add_expense_categories"
alembic upgrade head
```

**Провери** генерирания файл в `backend/alembic/versions/` — понякога autogenerate пропуска индекси или constraints.

### Стъпка 3: Pydantic схема

**Файл:** `backend/schemas/expense.py`

```python
from pydantic import BaseModel, ConfigDict

class ExpenseCategoryBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    description: str | None = None
    is_active: bool = True

class ExpenseCategoryCreate(ExpenseCategoryBase):
    pass

class ExpenseCategoryUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str | None = None
    description: str | None = None
    is_active: bool | None = None

class ExpenseCategoryResponse(ExpenseCategoryBase):
    id: int
    company_id: int
    created_at: datetime
```

### Стъпка 4: Repository

**Файл:** `backend/repositories/expense_category_repository.py`

```python
class ExpenseCategoryRepository:
    async def create(self, db: AsyncSession, data: ExpenseCategoryCreate, company_id: int) -> ExpenseCategory:
        category = ExpenseCategory(**data.model_dump(), company_id=company_id)
        db.add(category)
        await db.flush()  # ВАЖНО: flush, НЕ commit!
        return category

    async def get_by_id(self, db: AsyncSession, id: int) -> ExpenseCategory | None:
        result = await db.execute(
            select(ExpenseCategory).where(ExpenseCategory.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(self, db: AsyncSession, company_id: int) -> list[ExpenseCategory]:
        result = await db.execute(
            select(ExpenseCategory)
            .where(ExpenseCategory.company_id == company_id)
            .order_by(ExpenseCategory.name)
        )
        return list(result.scalars().all())
```

**Правило:** Repository-ите **никога** не правят `db.commit()` — само `db.add()` + `db.flush()`. Commit-ът се контролира от mutation-а.

### Стъпка 5: GraphQL Input + Type

**Файл:** `backend/graphql/types/expense.py`

```python
import strawberry
from backend.schemas import expense as schemas

@strawberry.type
class ExpenseCategoryType:
    id: strawberry.auto
    name: strawberry.auto
    description: strawberry.auto
    is_active: strawberry.auto
    company_id: strawberry.auto
    created_at: strawberry.auto
```

**Файл:** `backend/graphql/mutations/expense.py`

```python
import strawberry
from strawberry.types import Info

@strawberry.input
class ExpenseCategoryInput:
    name: str
    description: str | None = None
    is_active: bool = True

@strawberry.input
class ExpenseCategoryUpdateInput:
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None
```

### Стъпка 6: GraphQL Query + Mutation

**Query** (в `backend/graphql/queries/expense.py`):

```python
@strawberry.field
async def expense_categories(info: Info) -> list[ExpenseCategoryType]:
    db = info.context["db"]
    user = info.context["user"]
    repo = ExpenseCategoryRepository()
    items = await repo.get_all(db, company_id=user.company_id)
    return [
        ExpenseCategoryType.from_pydantic(
            schemas.ExpenseCategoryResponse.model_validate(i)
        )
        for i in items
    ]
```

**Mutation** (в `backend/graphql/mutations/expense.py`):

```python
@strawberry.mutation
async def create_expense_category(
    info: Info,
    input: ExpenseCategoryInput,
) -> ExpenseCategoryType:
    db = info.context["db"]
    user = info.context["user"]

    repo = ExpenseCategoryRepository()
    category = await repo.create(
        db,
        schemas.ExpenseCategoryCreate(**input.__dict__),
        company_id=user.company_id
    )
    await db.commit()
    await db.refresh(category)
    return ExpenseCategoryType.from_pydantic(
        schemas.ExpenseCategoryResponse.model_validate(category)
    )
```

### Стъпка 7: Регистрация в `__init__.py`

Добави новите типове и мутации в съответните `__init__.py` файлове, за да бъдат включени в GraphQL схемата.

### Стъпка 8: Frontend GraphQL операция

**Файл:** `frontend/src/graphql/queries/expense.ts`

```typescript
import { gql } from "@apollo/client";

export const GET_EXPENSE_CATEGORIES = gql`
  query GetExpenseCategories {
    expenseCategories {
      id
      name
      description
      isActive
      createdAt
    }
  }
`;
```

**Файл:** `frontend/src/graphql/mutations/expense.ts`

```typescript
import { gql } from "@apollo/client";

export const CREATE_EXPENSE_CATEGORY = gql`
  mutation CreateExpenseCategory($input: ExpenseCategoryInput!) {
    createExpenseCategory(input: $input) {
      id
      name
      description
      isActive
    }
  }
`;
```

### Стъпка 9: Codegen + Frontend компонент

```bash
cd frontend
npm run codegen  # Генерира TypeScript типове
```

**Файл:** `frontend/src/pages/ExpenseCategoriesPage.tsx`

```typescript
import { useQuery, useMutation } from "@apollo/client";
import { GET_EXPENSE_CATEGORIES } from "../graphql/queries/expense";
import { CREATE_EXPENSE_CATEGORY } from "../graphql/mutations/expense";
import { useError } from "../hooks/useError";

function ExpenseCategoriesPage() {
  const { showError, showSuccess } = useError();
  const { data, loading } = useQuery(GET_EXPENSE_CATEGORIES);
  const [createCategory] = useMutation(CREATE_EXPENSE_CATEGORY, {
    refetchQueries: [{ query: GET_EXPENSE_CATEGORIES }],
    onError: (error) => showError(error),
    onCompleted: () => showSuccess("Категорията е създадена успешно"),
  });

  // ... рендиране на MUI компоненти
}
```

---

## 6. Пълен пример: Категории разходи

Нека проследим **пълния път** на добавяне на нова функционалност — управление на категории разходи (ExpenseCategory). Това е прост CRUD модул, който илюстрира всички слоеве.

### 6.1. Дефиниране на модела

**Файл:** `backend/database/models.py`

```python
class ExpenseCategory(Base):
    __tablename__ = "expense_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    code: Mapped[str | None] = mapped_column(String(20), unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    color: Mapped[str | None] = mapped_column(String(7))  # HEX цвят
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        default=True, server_default="true"
    )
    sort_order: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    # Релации
    company: Mapped["Company"] = relationship(
        back_populates="expense_categories"
    )
    expenses: Mapped[list["Expense"]] = relationship(
        back_populates="category"
    )
```

### 6.2. Създаване на миграция

```bash
cd backend
alembic revision --autogenerate -m "add_expense_categories_table"
# Провери генерирания файл
alembic upgrade head
```

### 6.3. Pydantic схеми

**Файл:** `backend/schemas/expense.py`

```python
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class ExpenseCategoryBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(min_length=1, max_length=100)
    code: str | None = Field(default=None, max_length=20)
    description: str | None = None
    color: str | None = Field(
        default=None, pattern=r"^#[0-9a-fA-F]{6}$"
    )
    is_active: bool = True
    sort_order: int = 0

class ExpenseCategoryCreate(ExpenseCategoryBase):
    pass

class ExpenseCategoryUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str | None = Field(default=None, min_length=1, max_length=100)
    code: str | None = Field(default=None, max_length=20)
    description: str | None = None
    color: str | None = Field(
        default=None, pattern=r"^#[0-9a-fA-F]{6}$"
    )
    is_active: bool | None = None
    sort_order: int | None = None

class ExpenseCategoryResponse(ExpenseCategoryBase):
    id: int
    company_id: int
    created_at: datetime
    updated_at: datetime
```

### 6.4. Repository

**Файл:** `backend/repositories/expense_category_repository.py`

```python
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models import ExpenseCategory

class ExpenseCategoryRepository:
    async def create(
        self, db: AsyncSession, data: dict, company_id: int
    ) -> ExpenseCategory:
        category = ExpenseCategory(**data, company_id=company_id)
        db.add(category)
        await db.flush()
        return category

    async def get_by_id(
        self, db: AsyncSession, category_id: int
    ) -> ExpenseCategory | None:
        result = await db.execute(
            select(ExpenseCategory).where(
                ExpenseCategory.id == category_id
            )
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        db: AsyncSession,
        company_id: int,
        include_inactive: bool = False,
    ) -> list[ExpenseCategory]:
        query = select(ExpenseCategory).where(
            ExpenseCategory.company_id == company_id
        )
        if not include_inactive:
            query = query.where(ExpenseCategory.is_active == True)
        query = query.order_by(
            ExpenseCategory.sort_order, ExpenseCategory.name
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def update(
        self,
        db: AsyncSession,
        category: ExpenseCategory,
        data: dict,
    ) -> ExpenseCategory:
        for key, value in data.items():
            if value is not None:
                setattr(category, key, value)
        await db.flush()
        return category

    async def delete(
        self, db: AsyncSession, category: ExpenseCategory
    ) -> None:
        await db.delete(category)
        await db.flush()

    async def count(
        self, db: AsyncSession, company_id: int
    ) -> int:
        result = await db.execute(
            select(func.count())
            .select_from(ExpenseCategory)
            .where(ExpenseCategory.company_id == company_id)
        )
        return result.scalar_one()
```

### 6.5. GraphQL типове

**Файл:** `backend/graphql/types/expense.py`

```python
import strawberry
from backend.schemas import expense as schemas

@strawberry.type
class ExpenseCategoryType:
    id: strawberry.auto
    name: strawberry.auto
    code: strawberry.auto
    description: strawberry.auto
    color: strawberry.auto
    is_active: strawberry.auto
    sort_order: strawberry.auto
    company_id: strawberry.auto
    created_at: strawberry.auto
    updated_at: strawberry.auto

    @strawberry.field
    def display_name(self) -> str:
        if self.code:
            return f"[{self.code}] {self.name}"
        return self.name
```

### 6.6. GraphQL мутации

**Файл:** `backend/graphql/mutations/expense.py`

```python
import strawberry
from strawberry.types import Info

from backend.exceptions import NotFoundException, ValidationException
from backend.repositories.expense_category_repository import (
    ExpenseCategoryRepository,
)
from backend.schemas.expense import (
    ExpenseCategoryCreate,
    ExpenseCategoryUpdate,
    ExpenseCategoryResponse,
)
from backend.graphql.types.expense import ExpenseCategoryType


@strawberry.input
class ExpenseCategoryInput:
    name: str
    code: str | None = None
    description: str | None = None
    color: str | None = None
    is_active: bool = True
    sort_order: int = 0


@strawberry.input
class ExpenseCategoryUpdateInput:
    name: str | None = None
    code: str | None = None
    description: str | None = None
    color: str | None = None
    is_active: bool | None = None
    sort_order: int | None = None


@strawberry.type
class ExpenseCategoryMutations:
    @strawberry.mutation
    async def create_expense_category(
        self, info: Info, input: ExpenseCategoryInput
    ) -> ExpenseCategoryType:
        db = info.context["db"]
        user = info.context["user"]
        repo = ExpenseCategoryRepository()

        existing = await repo.get_all(
            db, company_id=user.company_id
        )
        if any(
            c.name.lower() == input.name.lower() for c in existing
        ):
            raise ValidationException.field(
                "name", "Категория с това име вече съществува"
            )

        data = ExpenseCategoryCreate(
            name=input.name,
            code=input.code,
            description=input.description,
            color=input.color,
            is_active=input.is_active,
            sort_order=input.sort_order,
        )
        category = await repo.create(
            db, data.model_dump(), company_id=user.company_id
        )
        await db.commit()
        await db.refresh(category)

        return ExpenseCategoryType.from_pydantic(
            ExpenseCategoryResponse.model_validate(category)
        )

    @strawberry.mutation
    async def update_expense_category(
        self, info: Info, id: int, input: ExpenseCategoryUpdateInput
    ) -> ExpenseCategoryType:
        db = info.context["db"]
        repo = ExpenseCategoryRepository()

        category = await repo.get_by_id(db, id)
        if not category:
            raise NotFoundException(
                model="ExpenseCategory", id=id
            )

        update_data = {
            k: v
            for k, v in input.__dict__.items()
            if v is not None
        }

        category = await repo.update(db, category, update_data)
        await db.commit()
        await db.refresh(category)

        return ExpenseCategoryType.from_pydantic(
            ExpenseCategoryResponse.model_validate(category)
        )

    @strawberry.mutation
    async def delete_expense_category(
        self, info: Info, id: int
    ) -> bool:
        db = info.context["db"]
        repo = ExpenseCategoryRepository()

        category = await repo.get_by_id(db, id)
        if not category:
            raise NotFoundException(
                model="ExpenseCategory", id=id
            )

        await repo.delete(db, category)
        await db.commit()
        return True
```

### 6.7. GraphQL заявки

**Файл:** `backend/graphql/queries/expense.py`

```python
import strawberry
from strawberry.types import Info

from backend.exceptions import NotFoundException
from backend.repositories.expense_category_repository import (
    ExpenseCategoryRepository,
)
from backend.schemas.expense import ExpenseCategoryResponse
from backend.graphql.types.expense import ExpenseCategoryType


@strawberry.type
class ExpenseCategoryQueries:
    @strawberry.field
    async def expense_categories(
        self, info: Info, include_inactive: bool = False
    ) -> list[ExpenseCategoryType]:
        db = info.context["db"]
        user = info.context["user"]
        repo = ExpenseCategoryRepository()

        items = await repo.get_all(
            db,
            company_id=user.company_id,
            include_inactive=include_inactive,
        )
        return [
            ExpenseCategoryType.from_pydantic(
                ExpenseCategoryResponse.model_validate(item)
            )
            for item in items
        ]

    @strawberry.field
    async def expense_category(
        self, info: Info, id: int
    ) -> ExpenseCategoryType:
        db = info.context["db"]
        repo = ExpenseCategoryRepository()

        category = await repo.get_by_id(db, id)
        if not category:
            raise NotFoundException(
                model="ExpenseCategory", id=id
            )

        return ExpenseCategoryType.from_pydantic(
            ExpenseCategoryResponse.model_validate(category)
        )
```

### 6.8. Регистрация в `__init__.py`

**`backend/graphql/types/__init__.py`:**

```python
from .expense import ExpenseCategoryType
```

**`backend/graphql/mutations/__init__.py`:**

```python
from .expense import ExpenseCategoryMutations
```

**`backend/graphql/queries/__init__.py`:**

```python
from .expense import ExpenseCategoryQueries
```

### 6.9. Frontend GraphQL операции

**`frontend/src/graphql/queries/expense.ts`:**

```typescript
import { gql } from "@apollo/client";

export const GET_EXPENSE_CATEGORIES = gql`
  query GetExpenseCategories($includeInactive: Boolean) {
    expenseCategories(includeInactive: $includeInactive) {
      id
      name
      code
      description
      color
      isActive
      sortOrder
      displayName
      createdAt
    }
  }
`;

export const GET_EXPENSE_CATEGORY = gql`
  query GetExpenseCategory($id: Int!) {
    expenseCategory(id: $id) {
      id
      name
      code
      description
      color
      isActive
      sortOrder
      createdAt
      updatedAt
    }
  }
`;
```

**`frontend/src/graphql/mutations/expense.ts`:**

```typescript
import { gql } from "@apollo/client";

export const CREATE_EXPENSE_CATEGORY = gql`
  mutation CreateExpenseCategory($input: ExpenseCategoryInput!) {
    createExpenseCategory(input: $input) {
      id
      name
      code
      color
      isActive
    }
  }
`;

export const UPDATE_EXPENSE_CATEGORY = gql`
  mutation UpdateExpenseCategory(
    $id: Int!
    $input: ExpenseCategoryUpdateInput!
  ) {
    updateExpenseCategory(id: $id, input: $input) {
      id
      name
      code
      color
      isActive
    }
  }
`;

export const DELETE_EXPENSE_CATEGORY = gql`
  mutation DeleteExpenseCategory($id: Int!) {
    deleteExpenseCategory(id: $id)
  }
`;
```

### 6.10. Frontend компонент

**`frontend/src/pages/ExpenseCategoriesPage.tsx`:**

```typescript
import { useState } from "react";
import { useQuery, useMutation } from "@apollo/client";
import {
  Box, Button, Dialog, DialogTitle, DialogContent,
  DialogActions, TextField, Table, TableHead, TableRow,
  TableCell, TableBody, IconButton, Chip, Typography,
} from "@mui/material";
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
} from "@mui/icons-material";

import { GET_EXPENSE_CATEGORIES } from "../graphql/queries/expense";
import {
  CREATE_EXPENSE_CATEGORY,
  UPDATE_EXPENSE_CATEGORY,
  DELETE_EXPENSE_CATEGORY,
} from "../graphql/mutations/expense";
import { useError } from "../hooks/useError";

export default function ExpenseCategoriesPage() {
  const { showError, showSuccess } = useError();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [formData, setFormData] = useState({
    name: "", code: "", description: "", color: "#1976d2",
  });

  const { data, loading, refetch } = useQuery(
    GET_EXPENSE_CATEGORIES,
    { variables: { includeInactive: true } }
  );

  const [createCategory, { loading: creating }] = useMutation(
    CREATE_EXPENSE_CATEGORY,
    {
      onCompleted: () => {
        showSuccess("Категорията е създадена успешно");
        handleClose();
        refetch();
      },
      onError: (error) => showError(error),
    }
  );

  const [updateCategory] = useMutation(
    UPDATE_EXPENSE_CATEGORY,
    {
      onCompleted: () => {
        showSuccess("Категорията е обновена");
        handleClose();
        refetch();
      },
      onError: (error) => showError(error),
    }
  );

  const [deleteCategory] = useMutation(
    DELETE_EXPENSE_CATEGORY,
    {
      onCompleted: () => {
        showSuccess("Категорията е изтрита");
        refetch();
      },
      onError: (error) => showError(error),
    }
  );

  const handleSubmit = async () => {
    if (editingId) {
      await updateCategory({
        variables: { id: editingId, input: formData },
      });
    } else {
      await createCategory({
        variables: { input: formData },
      });
    }
  };

  const handleClose = () => {
    setDialogOpen(false);
    setEditingId(null);
    setFormData({
      name: "", code: "", description: "", color: "#1976d2",
    });
  };

  const categories = data?.expenseCategories ?? [];

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{
        display: "flex",
        justifyContent: "space-between",
        mb: 3,
      }}>
        <Typography variant="h4">Категории разходи</Typography>
        <Button
          startIcon={<AddIcon />}
          variant="contained"
          onClick={() => setDialogOpen(true)}
        >
          Нова категория
        </Button>
      </Box>

      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Име</TableCell>
            <TableCell>Код</TableCell>
            <TableCell>Описание</TableCell>
            <TableCell>Статус</TableCell>
            <TableCell>Действия</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {categories.map((cat: any) => (
            <TableRow key={cat.id}>
              <TableCell>
                <Box sx={{
                  display: "flex",
                  alignItems: "center",
                  gap: 1,
                }}>
                  <Box sx={{
                    width: 16, height: 16,
                    borderRadius: "50%",
                    bgcolor: cat.color,
                  }} />
                  {cat.displayName}
                </Box>
              </TableCell>
              <TableCell>{cat.code || "—"}</TableCell>
              <TableCell>{cat.description || "—"}</TableCell>
              <TableCell>
                <Chip
                  label={cat.isActive ? "Активна" : "Неактивна"}
                  color={cat.isActive ? "success" : "default"}
                  size="small"
                />
              </TableCell>
              <TableCell>
                <IconButton onClick={() => {
                  setEditingId(cat.id);
                  setFormData(cat);
                  setDialogOpen(true);
                }}>
                  <EditIcon />
                </IconButton>
                <IconButton
                  onClick={() =>
                    deleteCategory({ variables: { id: cat.id } })
                  }
                  color="error"
                >
                  <DeleteIcon />
                </IconButton>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <Dialog
        open={dialogOpen}
        onClose={handleClose}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          {editingId ? "Редакция" : "Нова категория"}
        </DialogTitle>
        <DialogContent>
          <TextField
            label="Име"
            fullWidth
            margin="normal"
            value={formData.name}
            onChange={(e) =>
              setFormData({ ...formData, name: e.target.value })
            }
          />
          <TextField
            label="Код"
            fullWidth
            margin="normal"
            value={formData.code}
            onChange={(e) =>
              setFormData({ ...formData, code: e.target.value })
            }
          />
          <TextField
            label="Описание"
            fullWidth
            margin="normal"
            multiline
            rows={3}
            value={formData.description}
            onChange={(e) =>
              setFormData({
                ...formData, description: e.target.value,
              })
            }
          />
          <TextField
            label="Цвят"
            type="color"
            fullWidth
            margin="normal"
            value={formData.color}
            onChange={(e) =>
              setFormData({ ...formData, color: e.target.value })
            }
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Отказ</Button>
          <Button
            variant="contained"
            onClick={handleSubmit}
            disabled={creating || !formData.name}
          >
            {editingId ? "Запази" : "Създай"}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
```

### 6.11. Тестване

```bash
# Backend: стартирай dev server
cd backend && uvicorn main:app --reload --port 14240

# Frontend: генерирай типове и стартирай dev server
cd frontend && npm run codegen && npm run dev

# Отвори http://localhost:3001 и тествай CRUD операциите
```

---

## 7. Обработка на грешки

### Backend: Йерархия на грешките

Всички грешки в Chronos наследяват базовия клас `CHRONOSException`:

```
CHRONOSException (базов клас)
├── NotFoundException         # Ресурсът не е намерен (404)
├── ValidationException       # Невалидни входни данни (422)
├── PermissionDeniedException # Няма permission (403)
├── AuthenticationException   # Неоторизиран достъп (401)
├── DatabaseException         # Грешка в базата данни (500)
├── InvalidOperationException # Невалидна операция (400)
└── ModuleDisabledException   # Модулът е изключен (403)
```

### Примери за хвърляне на грешки

**NotFoundException:**

```python
from backend.exceptions import NotFoundException

user = await repo.get_by_id(db, user_id)
if not user:
    raise NotFoundException.user(id=user_id)
    # Връща: {"message": "User with id=5 not found", "code": "NOT_FOUND"}
```

**ValidationException:**

```python
from backend.exceptions import ValidationException

if len(name) < 3:
    raise ValidationException.field(
        "name", "Името трябва да е поне 3 символа"
    )
    # Връща: {
    #   "message": "Invalid field 'name': ...",
    #   "code": "VALIDATION_ERROR"
    # }

# Множество грешки:
raise ValidationException.multiple([
    ("email", "Невалиден email формат"),
    ("password", "Паролата трябва да е поне 8 символа"),
])
```

**PermissionDeniedException:**

```python
from backend.exceptions import PermissionDeniedException

if user.role not in ["admin", "super_admin"]:
    raise PermissionDeniedException(
        action="delete", resource="Invoice"
    )
    # Връща: {
    #   "message": "Permission denied: cannot delete Invoice",
    #   "code": "PERMISSION_DENIED"
    # }
```

**InvalidOperationException:**

```python
from backend.exceptions import InvalidOperationException

if invoice.status == "paid":
    raise InvalidOperationException(
        "Не може да изтриете платена фактура"
    )
    # Връща: {
    #   "message": "Не може да изтриете платена фактура",
    #   "code": "INVALID_OPERATION"
    # }
```

### Frontend: Error handling

**useError hook:**

```typescript
import { useError } from "../hooks/useError";

function MyComponent() {
  const { showError, showSuccess, showWarning, showInfo } = useError();

  const [createItem] = useMutation(CREATE_ITEM, {
    onError: (error) => showError(error),
    onCompleted: () => showSuccess("Успешно!"),
  });

  return <Button onClick={() => createItem()}>Създай</Button>;
}
```

**extractErrorMessage:**

```typescript
import { extractErrorMessage } from "../utils/errorUtils";

try {
  await someOperation();
} catch (error) {
  const message = extractErrorMessage(error);
  // "Validation error: Invalid field 'email': ..."
  console.error(message);
}
```

### Transaction rollback

При грешка в `atomic_transaction`, транзакцията се връща автоматично:

```python
from backend.database.transaction_manager import atomic_transaction

async def complex_operation(db: AsyncSession):
    async with atomic_transaction(db) as tx:
        invoice = await create_invoice(tx, data)
        payment = await create_payment(tx, invoice)

        if some_condition_fails:
            raise InvalidOperationException("Условието не е изпълнено")
            # → автоматичен rollback, нищо не се записва в БД

        # commit става автоматично тук, ако няма грешка
```

### Deadlock retry

За операции, които могат да причинят deadlock:

```python
from backend.database.transaction_manager import retry_on_deadlock

@retry_on_deadlock(max_retries=3)
async def high_concurrency_operation(db: AsyncSession):
    # Ако се случи deadlock, операцията се опитва
    # отново до 3 пъти
    ...
```

### Неочаквани грешки (AttributeError, TypeError, KeyError и др.)

#### Какво се случва?

Chronos има exception handlers **само** за познатите грешки:

| Handler | Хваща |
|---------|-------|
| `chronos_exception_handler` | `CHRONOSException` и наследници |
| `transaction_exception_handler` | `TransactionError` |
| `deadlock_exception_handler` | `DeadlockError` |
| `concurrent_modification_handler` | `ConcurrentModificationError` |
| `rate_limit_exceeded_handler` | `RateLimitExceeded` |

**Няма global handler за generic `Exception`.** Това означава:

- `AttributeError`, `TypeError`, `KeyError`, `ValueError`, `IndexError` и подобни **не се хващат** от нашите handlers
- FastAPI връща **500 Internal Server Error** с дефолтния си формат
- В GraphQL (Strawberry) грешката се връща в `errors` масива:

```json
{
  "data": null,
  "errors": [
    {
      "message": "'NoneType' object has no attribute 'name'",
      "locations": [{"line": 2, "column": 3}],
      "path": ["createInvoice"]
    }
  ]
}
```

- В **production** (`DEBUG=False`): потребителят вижда generic съобщение, детайлите са скрити
- В **development** (`DEBUG=True`): виждаш пълния traceback в логовете

#### Как да debug-ваш?

**1. Провери логовете:**

```bash
docker compose logs -f backend | grep -i "error\|traceback"
```

**2. Възпроизведи локално:**

```bash
# Стартирай бекенда с DEBUG=True
DEBUG=true uvicorn backend.main:app --reload --port 14240
```

**3. Чести причини:**

| Грешка | Причина | Решение |
|--------|---------|---------|
| `AttributeError: 'NoneType' has no attribute 'x'` | Обектът е `None` (не е намерен в БД) | Добави `if not obj: raise NotFoundException...` |
| `TypeError: expected X, got Y` | Грешен тип данни | Провери Pydantic схемата и input валидацията |
| `KeyError: 'field_name'` | Липсващ ключ в dict | Използвай `.get("field_name")` вместо `["field_name"]` |
| `ValueError: invalid literal` | Невалидна стойност (напр. `int("abc")`) | Валидирай входа преди конвертиране |
| `sqlalchemy.exc.MissingGreenlet` | Lazy loading в async контекст | Добави `selectinload()` или `await db.refresh(obj, ["relation"])` |

#### Кога да обвиваш в CHRONOSException?

**Винаги обвивай** неочаквани грешки, когато:

1. **Можеш да предвидиш грешката** — напр. обект може да е `None`:

```python
# ГРЕШНО — ще хвърли AttributeError
user = await repo.get_by_id(db, user_id)
return user.name  # 💥 ако user е None

# ПРАВИЛНО
user = await repo.get_by_id(db, user_id)
if not user:
    raise NotFoundException.user(id=user_id)
return user.name
```

2. **Операцията е критична** и искаш смислено съобщение:

```python
try:
    result = await external_api.call(data)
except (AttributeError, TypeError) as e:
    logger.error(f"External API error: {e}", exc_info=True)
    raise DatabaseException(
        detail="Грешка при комуникация с външна система",
        original_error=e,
    )
```

3. **В service layer** — за да не изтичат вътрешни детайли към клиента:

```python
class InvoiceService:
    async def calculate_total(self, db, invoice_id):
        try:
            invoice = await self.repo.get_with_items(db, invoice_id)
            total = sum(item.price * item.quantity for item in invoice.items)
            return total
        except AttributeError as e:
            logger.error(f"Missing data for invoice {invoice_id}: {e}")
            raise ValidationException(
                detail="Фактурата има непълни данни. Проверете позициите."
            )
```

#### Правило за младши програмиста

> **Ако видиш `AttributeError` или `TypeError` в логовете — това е бъг в кода, не "нормална" грешка.**
> Не я оставяй да стигне до потребителя. Добави проверка **преди** операцията или я обвий в `CHRONOSException` с ясно съобщение.

---

## 8. Cheatsheet с команди

### Docker Compose

```bash
# Стартиране на целия стек
docker compose up -d

# Стартиране в dev mode (с hot reload)
docker compose --profile dev up -d db backend-dev frontend-dev

# Спиране на всички контейнери
docker compose down

# Рестартиране на backend
docker compose restart backend

# Логи в реално време
docker compose logs -f backend
docker compose logs -f frontend

# Изпълнение на команда в контейнер
docker compose exec backend bash
docker compose exec db psql -U chronos -d chronos_db
```

### Alembic (миграции)

```bash
# Създаване на нова миграция
cd backend
alembic revision --autogenerate -m "описание на промяната"

# Прилагане на всички неприложени миграции
alembic upgrade head

# Връщане на последната миграция
alembic downgrade -1

# Проверка на текущото състояние
alembic heads          # Трябва да има точно 1 head
alembic current        # Текуща версия
alembic history        # История на всички миграции

# Merge на multiple heads
alembic merge HEAD1 HEAD2 -m "merge_heads"
```

### Frontend (npm)

```bash
cd frontend

# Инсталиране на зависимости
npm install

# Development server (HMR)
npm run dev

# Production build
npm run build

# Генериране на GraphQL типове
npm run codegen

# Unit тестове (watch mode)
npm run test

# Unit тестове (еднократно)
npm run test:run

# E2E тестове
npm run test:e2e

# Lint
npm run lint
```

### Backend (Python)

```bash
cd backend

# Активиране на virtual environment
source .venv/bin/activate

# Development server (с hot reload)
uvicorn main:app --host 0.0.0.0 --port 14240 --reload

# Lint проверка
ruff check .

# Автоматично форматиране
ruff format .

# Стартиране на тестове
pytest tests/ -v

# Стартиране на конкретен тест
pytest tests/test_pydantic_schemas.py -v

# Seed на модули
python -m backend.seed_modules
```

### Git

```bash
# Създаване на нов branch
git checkout -b feature/my-feature

# Commit с conventional commit message
git add .
git commit -m "feat(expense): add expense category CRUD"

# Push към remote
git push origin feature/my-feature

# Създаване на release tag
git tag -a v3.8.0.0 -m "Release v3.8.0.0"
git push origin main --tags
```

---

## 9. Troubleshooting

### MissingGreenlet грешка

**Симптом:**

```
sqlalchemy.exc.MissingGreenlet: greenlet_spawn has not been called
```

**Причина:** Lazy loading на релации не работи с асинхронни сесии.

**Решение:** Използвай `selectinload` или `await db.refresh()`:

```python
# ГРЕШНО:
user = await db.get(User, user_id)
print(user.company.name)  # MissingGreenlet!

# ПРАВИЛНО (вариант 1 — selectinload):
from sqlalchemy.orm import selectinload
result = await db.execute(
    select(User)
    .options(selectinload(User.company))
    .where(User.id == user_id)
)
user = result.scalar_one()
print(user.company.name)  # OK

# ПРАВИЛНО (вариант 2 — refresh):
user = await db.get(User, user_id)
await db.refresh(user, ["company"])
print(user.company.name)  # OK
```

### N+1 Query проблем

**Симптом:** Бавни заявки, стотици SQL queries в логовете.

**Причина:** Зареждане на релации в цикъл.

**Решение:** Използвай DataLoader или `selectinload`:

```python
# ГРЕШНО (N+1):
shifts = await repo.get_all_shifts(db)
for shift in shifts:
    user = await db.get(User, shift.user_id)  # N заявки!

# ПРАВИЛНО (DataLoader):
user_loader = DataLoader(load_users_batch)
shifts = await repo.get_all_shifts(db)
users = await asyncio.gather(
    *[user_loader.load(s.user_id) for s in shifts]
)

# ПРАВИЛНО (selectinload):
result = await db.execute(
    select(Shift).options(selectinload(Shift.user))
)
shifts = result.scalars().all()
for shift in shifts:
    print(shift.user.name)  # Вече заредено!
```

### CORS грешки

**Симптом:**

```
Access to fetch at 'http://localhost:14240/graphql'
from origin 'http://localhost:3001'
has been blocked by CORS policy
```

**Решение:** Провери `backend/main.py` — CORS middleware трябва да включва frontend origin:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3001",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Alembic: Multiple heads

**Симптом:**

```
FAILED: Multiple head revisions are present;
please specify a specific target
```

**Решение:**

```bash
# Виж кои са heads
alembic heads

# Merge ги
alembic merge HEAD1 HEAD2 -m "merge_heads"

# Приложи
alembic upgrade head
```

### CSRF Token грешки

**Симптом:**

```
403 Forbidden: CSRF token missing or invalid
```

**Решение:**

1. Провери, че Apollo Client изпраща CSRF token:

```typescript
const csrfToken = document.cookie
  .split("; ")
  .find((row) => row.startsWith("csrf_token="))
  ?.split("=")[1];

const link = new HttpLink({
  uri: "/graphql",
  headers: { "X-CSRF-Token": csrfToken },
});
```

2. Изчисти cookies и се логни отново.

### Token expired / 401

**Симптом:** Всички заявки връщат 401 Unauthorized.

**Решение:**

1. Провери, че `refreshToken` mutation се извиква автоматично
2. Изчисти browser cookies и се логни отново
3. Провери `JWT_SECRET_KEY` в `.env` — не трябва да се променя между рестарти

### Docker build грешки

**Симптом:** `docker compose build` се проваля.

**Решение:**

```bash
# Изчисти cache и rebuild
docker compose build --no-cache

# Ако има проблем с Python dependencies:
docker compose exec backend pip install -r requirements.txt

# Ако има проблем с Node dependencies:
docker compose exec frontend npm install
```

### Портът е зает

**Симптом:**

```
Error: Port 14240 is already in use
```

**Решение:**

```bash
# Намери процеса
lsof -i :14240

# Убий го
kill -9 <PID>

# Или промени порта в docker-compose.yml
```

---

## Заключение

Този документ покрива основните аспекти на работата с Chronos. Когато имаш въпроси:

1. **Провери този документ** — вероятно отговорът е тук
2. **Провери `AGENTS.md`** — там има допълнителни архитектурни детайли
3. **Питай в екипния чат** — не се колебай да питаш, дори да изглежда "глупав" въпрос
4. **Чети кода** — най-добрият начин да разбереш как работи нещо е да го прочетеш

Успех!
