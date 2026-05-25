# FastAPI Best Practices — Анализ и План

Сравнение на текущия backend спрямо [zhanymkanov/fastapi-best-practices](https://github.com/zhanymkanov/fastapi-best-practices).
https://github.com/zhanymkanov/fastapi-best-practices/issues/4

---

## 1. Project Structure

### Best Practice
```
src/
├── auth/          # router.py, schemas.py, models.py, dependencies.py, service.py
├── posts/         # собствен router, schemas, models, service
├── config.py      # global config
├── database.py    # DB connection
└── main.py
```

### Текущо състояние

| Критерий | Статус | Проблем |
|----------|--------|---------|
| Domain-based structure | ⚠️ Частично | `auth/`, `services/`, `routers/` са разделени, но **GraphQL слоят е монолитен** (няма разделение по домейни) |
| `graphql/mutations.py` | ❌ 8 488 реда | Всички mutation-и в един файл |
| `graphql/types.py` | ❌ 4 630 реда | Всички GraphQL типове в един файл |
| `graphql/queries.py` | ❌ 2 955 реда | Всички query-та в един файл |
| `graphql/inputs.py` | ❌ 892 реда | Всички input типове в един файл |
| `database/models.py` | ❌ 3 079 реда | Всички SQLAlchemy модели в един файл |
| `crud_legacy.py` | ❌ 3 231 реда | Legacy CRUD, все още импортиран за backward compat |
| Behavioral analysis module | ✅ | Правилно разделен — собствен `router.py`, `mutations.py`, `queries.py`, `types.py`, `models.py` |
| Tests outside `tests/` dir | ❌ | 7 тест-файла в корена на backend/ |

### План

1. **Раздели `graphql/` по домейни:**
   ```
   graphql/
   ├── auth/
   │   ├── mutations.py
   │   ├── queries.py
   │   └── types.py
   ├── payroll/
   ├── time_tracking/
   ├── leave/
   ├── warehouse/
   ├── fleet/
   ├── notifications/
   ├── settings/
   └── schema.py
   ```

2. **Раздели `database/models.py` по домейни:**
   ```
   database/models/
   ├── __init__.py
   ├── user.py
   ├── payroll.py
   ├── time_tracking.py
   ├── warehouse.py
   ├── fleet.py
   └── ...
   ```

3. **Премахни `crud_legacy.py`** — мигрирай останалите употреби към repository pattern.

4. **Премести root-level тестове в `tests/`.**

---

## 2. Async Routes

### Best Practice
- `async` routes само за non-blocking I/O
- `sync` routes за blocking I/O (FastAPI ги пуска в threadpool)
- Никога `time.sleep()` в async route
- CPU-intensive задачи → отделен worker (Celery/multiprocessing)
- `BackgroundTasks` само за бързи задачи (< 1 сек)

### Текущо състояние

| Критерий | Статус | Проблем |
|----------|--------|---------|
| Async routes | ✅ | Всички FastAPI routes и GraphQL mutation-и са `async` |
| `time.sleep()` в async | ❌ | `time.sleep(10)` в `delayed_startup_jobs` (main.py:72) — блокира event loop |
| Thread pool за sync SDK | ❌ | Няма `run_in_threadpool` — sync SDK-та се викат директно в async контекст |
| CPU-intensive (payroll) | ❌ | `enhanced_payroll_calculator.py` (1 207 реда) се изпълнява в async контекст |
| LockedSession | ⚠️ | Serialize-ва всички DB операции с `asyncio.Lock()` |
| `BackgroundTasks` vs task queue | ⚠️ | `threading.Thread` за deploy |

### План

1. **Замени `time.sleep()` с `asyncio.sleep()`** в `main.py:72`.

2. **Добави `run_in_threadpool`** за sync SDK (`smtplib`, etc.).

3. **Премести payroll калкулациите** в отделен worker процес или `run_in_threadpool`.

4. **Замени `threading.Thread`** с `BackgroundTasks` за deploy.

---

## 3. Pydantic

### Best Practice
- Екстензивна употреба на Pydantic с богати валидации
- Custom BaseModel с глобална конфигурация
- Разделени BaseSettings per domain
- `field_validator` и `model_validator` вместо @validator (deprecated)

### Текущо състояние

| Критерий | Статус | Проблем |
|----------|--------|---------|
| Pydantic v2 | ✅ | Използва се Pydantic v2 |
| Custom BaseModel | ✅ | `backend/utils/base_model.py` — `CustomBaseModel` с `from_attributes=True` и ISO 8601 datetime |
| Domain-specific BaseSettings | ❌ | Един `Settings` клас (config.py:182 реда) |
| Schema duplication | ❌ | `schemas.py` + `types.py`/`inputs.py` — едни и същи полета |
| `strawberry.experimental.pydantic` | ❌ | Не се използва |

### План

1. **Създай `CustomBaseModel`** с централизирано datetime форматиране.

2. **Раздели `config.py` Settings:** `AuthConfig`, `DatabaseConfig`, `GoogleConfig`, `SmtpConfig`, `AppConfig`.

3. **Използвай `strawberry.experimental.pydantic`** за да елиминираш дублирането.

---

## 4. Dependencies (FastAPI Depends)

### Best Practice
- Dependencies за комплексна валидация
- Chain-ване на dependencies
- Dependency caching per request
- Prefer async dependencies

### Текущо състояние

| Критерий | Статус | Проблем |
|----------|--------|---------|
| `auth/dependencies.py` | ✅ | Има `get_current_user_required()`, `require_permission()` |
| Complex validation deps | ❌ | Няма `valid_post_id` / `valid_user_id` dependencies |
| Dependency chaining | ❌ | Не се използва |
| GraphQL DI | ❌ | GraphQL не ползва FastAPI DI |

### План

1. **Създай resource validation dependencies:**
   ```
   backend/dependencies/
   ├── user_validators.py
   ├── post_validators.py
   └── common.py
   ```

2. **Chain dependencies** за owned resources.

3. **Използвай `app.dependency_overrides`** за тестове.

---

## 5. Miscellaneous

### 5.1 REST Routes

| Критерий | Статус | Проблем |
|----------|--------|---------|
| `response_model` | ⚠️ | Някои endpoints го имат, други не |
| `status_code` | ⚠️ | Не всички указват статус код |
| `description`, `summary`, `tags` | ⚠️ | Повечето ги нямат |

### 5.2 Docs

| Критерий | Статус | Проблем |
|----------|--------|---------|
| Hide docs in production | ✅ | `docs_url=None` когато `DEBUG=False` |
| OpenAPI metadata | ⚠️ | Само `title` и `version` |

### 5.3 Tests

| Критерий | Статус | Проблем |
|----------|--------|---------|
| Async test client (httpx) | ❌ | Няма `AsyncClient` fixture |
| `conftest.py` | ❌ | Липсва — файлът е `.bak` |
| `dependency_overrides` | ❌ | Не се използва |
| Test coverage | ⚠️ | 9 500+ реда, но липсва conftest и shared fixtures |
| pytest.ini | ✅ | `asyncio_mode = auto` |

### 5.4 Alembic

| Критерий | Статус | Проблем |
|----------|--------|---------|
| `file_template` | ❌ | Коментиран в `alembic.ini` |
| DB naming conventions | ❌ | Няма `MetaData(naming_convention=...)` |
| Snake_case tables | ✅ | Използва се |
| `_at` suffix | ✅ | `created_at`, `updated_at` |

### 5.5 Други

| Критерий | Статус | Проблем |
|----------|--------|---------|
| `ruff` | ❌ | Не се използва |
| BackgroundTasks | ⚠️ | `threading.Thread` за deploy |
| OpenAPI tags | ❌ | Липсват на повечето router-и |

### План

**REST:**
- Добави `response_model`, `status_code`, `description`, `summary`, `tags` на всички REST endpoints.
- Премини към RESTful naming: `/users/{user_id}`.

**Tests:**
- Създай `tests/conftest.py` с `httpx.AsyncClient`, DB fixture, `dependency_overrides`.
- Премести root-level тестове в `tests/`.

**Alembic:**
- Унифицирай `file_template = %%(year)d-%%(month).2d-%%(day).2d_%%(slug)s`.
- Добави `MetaData(naming_convention=...)` в `database.py`.

**Linting:**
- Добави `ruff` в `requirements.txt` и `pyproject.toml`.
- Добави `pre-commit` hooks.

---

## Приоритети

### P0 — Критични (стабилност/сигурност)
- [ ] `time.sleep()` → `asyncio.sleep()` в main.py
- [ ] `threading.Thread` → `BackgroundTasks` в deploy.py

### P1 — Висока (поддръжка)
- [ ] Раздели `graphql/mutations.py` (8 488 реда) по домейни
- [ ] Раздели `graphql/types.py` (4 630 реда) по домейни
- [ ] Създай `tests/conftest.py`
- [x] Добави CustomBaseModel за unified datetime форматиране

### P2 — Средна (код качество)
- [ ] Раздели `database/models.py` (3 079 реда) по домейни
- [ ] Мигрирай `crud_legacy.py` → repository pattern
- [ ] Добави `ruff` конфигурация
- [ ] Унифицирай Pydantic ↔ Strawberry schema дефиниции
- [ ] Chain dependencies за resource validation

### P3 — Ниска (документация/конвенции)
- [ ] Отключи `file_template` в `alembic.ini`
- [ ] Добави `MetaData(naming_convention=...)`
- [ ] Раздели `config.py` Settings per domain
- [ ] OpenAPI tags на всички router-и
- [ ] Премести root-level тестове в `tests/`

---

## Файлове за промяна по фази

### Phase 1 (P0 + P1 най-лесните)
| Файл | Промяна |
|------|---------|
| `main.py` | `time.sleep` → `asyncio.sleep` |
| `routers/deploy.py` | `threading.Thread` → `BackgroundTasks` |
| `tests/conftest.py` | NEW — httpx AsyncClient fixture |
| `utils/base_model.py` | NEW — CustomBaseModel ✅ DONE |

### Phase 2 (P1/P2)
| Файл | Промяна |
|------|---------|
| `graphql/` | Раздели на поддиректории |
| `database/models.py` | Раздели на поддиректории |
| `crud_legacy.py` | Мигрирай останалите употреби |
| `config.py` | Раздели на domain Settings |
| `pyproject.toml` | NEW — ruff конфигурация |
| `requirements.txt` | Добави `ruff` |

### Phase 3 (P3)
| Файл | Промяна |
|------|---------|
| `alembic.ini` | Отключи `file_template` |
| `database/database.py` | Добави `MetaData(naming_convention=...)` |
| `routers/*.py` | Добави `tags` на router-ите |
| Root-level test файлове | Премести в `tests/` |
