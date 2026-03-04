# Сигурност - Имплементационен план

Тази документация обединява всички критични подобрения на сигурността:

---

## Стьпка 1: CSRF Защита

### 1.1 Инсталация на зависимости

```bash
pip install starlette-csrf
```

### 1.2 Конфигурация

**Промени в `backend/config.py`:**

CSRF_SECRET_KEY се генерира автоматично ако не съществува в `.env`:

```python
@computed_field
@property
def CSRF_SECRET_KEY(self) -> str:
    """Auto-generate CSRF_SECRET_KEY if not set"""
    return _ensure_env_key("CSRF_SECRET_KEY")
```

### 1.3 Промени в backend/main.py

Добави CSRFMiddleware след SecurityHeadersMiddleware:

```python
from starlette_csrf import CSRFMiddleware

# ... съществуващ код ...

app.add_middleware(
    CSRFMiddleware,
    secret=settings.CSRF_SECRET_KEY,
    cookie_name="csrf_token",
    cookie_path="/",
    cookie_domain=None,
    cookie_secure=True,
    cookie_httponly=False,  # False - JS трябва да го чете за AJAX
    cookie_samesite="lax",
    exempt_routes=[
        "/",                      # root
        "/auth/register",         # публична регистрация
        "/auth/token",            # login
        "/auth/forgot-password",
        "/auth/verify-reset-token",
        "/auth/reset-password",
        "/auth/refresh",          # token refresh
        "/google/login",          # OAuth
        "/google/callback",
        "/graphql",               # GraphQL използва JWT
        "/docs",                 # OpenAPI docs
        "/redoc",
        "/openapi.json",
        "/uploads/",             # статични файлове
    ],
)
```

### 1.4 Промени по Frontend

**AJAX заявки (JavaScript/fetch/axios):**

```javascript
// utils/csrf.js
export function getCSRFToken() {
    const name = 'csrf_token' + '=';
    const decodedCookie = decodeURIComponent(document.cookie);
    const ca = decodedCookie.split(';');
    for (let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) == ' ') c = c.substring(1);
        if (c.indexOf(name) == 0) return c.substring(name.length, c.length);
    }
    return '';
}

// Активиране на интерцептор за axios (препоръчително)
import axios from 'axios';

axios.interceptors.request.use(config => {
    config.headers['X-CSRFToken'] = getCSRFToken();
    return config;
});
```

---

## Стьпка 2: Rate Limiter - коректно вземане на IP адрес

### 2.1 Проблем

Текущата имплементация в `backend/auth/limiter.py` използва `get_remote_address` който не отчита прокси сървъри (Cloudflare, Nginx).

### 2.2 Решение

**Промени в `backend/auth/limiter.py`:**

```python
from slowapi import Limiter
from backend.auth.security import get_client_ip

limiter = Limiter(key_func=get_client_ip)
```

**Функцията `get_client_ip` от `backend/auth/security.py` вече поддържа:**
1. Cloudflare: `CF-Connecting-IP`
2. Nginx: `X-Forwarded-For`, `X-Real-IP`
3. Fallback: `request.client.host`

---

## Стьпка 3: Премахване на email constraint в БД

### 3.1 Проблем

Текущият constraint в `migrations/002_add_database_constraints.sql` отхвърля валидни email адреси:

```sql
CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
```

Това не позволява имейли като `user+tag@example.com`.

### 3.2 Решение

**Създай нова миграция: `migrations/004_remove_email_constraint.sql`:**

```sql
-- Премахни ограничението за email формат
-- Pydantic вече валидира EmailStr в схемите

ALTER TABLE users DROP CONSTRAINT IF EXISTS check_email_format;
```

**Защо това решение?**
- Pydantic вече валидира `EmailStr` в `backend/schemas.py`
- По-добра валидация - поддържа пълен RFC 5322
- По-малко ограничения в БД

---

## Стьпка 4: CORS конфигурация

### 4.1 Проблем

Текущата конфигурация в `backend/main.py` е рискова:

```python
# Това е НЕСЪВМЕСТИМО!
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,  # Може да е "*"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 4.2 Решение

**Промени в `backend/main.py`:**

```python
from starlette.middleware.cors import CORSMiddleware

# Дефинирай конкретни origin-и
ALLOWED_ORIGINS = [
    "https://dev.oblak24.org",
    "https://oblak24.org",
    "http://localhost:5173",   # Vite dev
    "http://localhost:14240",  # Tauri dev
    "http://192.168.1.92:5173",  # Local network dev
    "http://192.168.1.92:4173",  # Local network dev
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-CSRFToken",      # CSRF
        "X-Requested-With",
        "Accept",
        "Accept-Language",
    ],
    expose_headers=["Content-Length", "X-Request-ID"],
    allow_cookie=True,
)
```

---

## Стьпка 5: RBAC - Използвай декоратора за разрешения

### 5.1 Проблем

`require_permission` декораторът е дефиниран в `backend/auth/rbac_service.py:247` но НЕ се използва в нито един router.

### 5.2 Решение

**Създай dependencies файл: `backend/auth/dependencies.py`:**

```python
from fastapi import Depends, HTTPException, status
from backend.auth.rbac_service import PermissionService
from backend.auth.jwt_utils import get_current_user
from backend.database.database import get_db
from backend.database.models import User
from sqlalchemy.ext.asyncio import AsyncSession


async def get_current_user_required(
    current_user: User = Depends(get_current_user)
) -> User:
    return current_user


def require_permission(permission: str):
    async def permission_checker(
        current_user: User = Depends(get_current_user_required),
        db: AsyncSession = Depends(get_db)
    ) -> User:
        perm_service = PermissionService(db)
        has_perm = await perm_service.check_permission(
            current_user.id, 
            permission,
            company_id=getattr(current_user, 'company_id', None)
        )
        
        if not has_perm:
            await perm_service.log_permission_decision(
                user_id=current_user.id,
                permission=permission,
                decision=False
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Нямате разрешение за: {permission}"
            )
        
        await perm_service.log_permission_decision(
            user_id=current_user.id,
            permission=permission,
            decision=True
        )
        
        return current_user
    
    return permission_checker
```

### 5.3 Примери за използване

```python
from backend.auth.dependencies import require_permission

@router.post("/", response_model=schemas.TimeLog)
async def create_timelog(
    timelog: schemas.TimeLogCreate,
    current_user: schemas.User = Depends(require_permission("timelogs:create_own")),
    db: AsyncSession = Depends(get_db)
):
    # ... create logic
```

---

## Стьпка 6: Автоматично генериране на ключове

### 6.1 Функция за авто-генериране

В `backend/config.py` има функция която автоматично генерира ключовете ако липсват:

```python
def _ensure_env_key(key_name: str, value: str = None, generate: bool = True, key_type: str = "hex") -> str:
    """
    Ensures a key exists in .env file.
    If value is None and generate=True, generates and saves a new key.
    
    Args:
        key_name: Name of the environment variable
        value: Optional existing value
        generate: Whether to generate if not found
        key_type: "hex" for regular secrets, "fernet" for Fernet keys
    """
    if value:
        return value
    
    # Try to read from .env file directly
    if env_path.exists():
        with open(env_path, 'r') as f:
            content = f.read()
            for line in content.split('\n'):
                if line.startswith(f'{key_name}=') and not line.strip().startswith('#'):
                    return line.split('=', 1)[1].strip()
    
    # Generate new key if not found
    if generate:
        if key_type == "fernet":
            new_value = Fernet.generate_key().decode()
        else:
            new_value = secrets.token_hex(32)
        
        # Append to .env file
        with open(env_path, 'a') as f:
            f.write(f'\n# Auto-generated {key_name}\n{key_name}={new_value}\n')
        print(f"Auto-generated {key_name} and saved to .env")
        return new_value
    
    return None
```

### 6.2 Автоматично генерираните ключове

| Ключ | Тип | Генерира се с |
|------|-----|--------------|
| `JWT_SECRET_KEY` | hex (64 chars) | `secrets.token_hex(32)` |
| `ENCRYPTION_KEY` | Fernet | `Fernet.generate_key().decode()` |
| `CSRF_SECRET_KEY` | hex (64 chars) | `secrets.token_hex(32)` |

### 6.3 Конфигурация в Settings

```python
@computed_field
@property
def JWT_SECRET_KEY(self) -> str:
    return _ensure_env_key("JWT_SECRET_KEY")

@computed_field
@property
def ENCRYPTION_KEY(self) -> str:
    return _ensure_env_key("ENCRYPTION_KEY", key_type="fernet")

@computed_field
@property
def CSRF_SECRET_KEY(self) -> str:
    return _ensure_env_key("CSRF_SECRET_KEY")
```

---

## Стьпка 7: Backup - изключване на чувствителни данни

### 7.1 Проблем

`backend/services/backup_service.py` архивира всички данни включително хеширани пароли, auth ключове, криптирани ЕГН/IBAN.

### 7.2 Решение

```python
class BackupService:
    # Sensitive fields to exclude from backup
    SENSITIVE_FIELDS = {
        "users": ["hashed_password", "qr_secret", "qr_token", "locked_until"],
        "auth_keys": ["secret"],
        "user_sessions": ["refresh_token_jti"],
        "api_keys": ["hashed_key"],
    }

    @staticmethod
    def _filter_sensitive_fields(table_name: str, record_dict: dict) -> dict:
        """Filter out sensitive fields from a record"""
        if table_name in BackupService.SENSITIVE_FIELDS:
            for field in BackupService.SENSITIVE_FIELDS[table_name]:
                if field in record_dict:
                    record_dict[field] = "[REDACTED]"
        return record_dict
```

---

## Стьпка 8: Input Validation

### 8.1 Промени в `backend/schemas.py`

```python
from pydantic import field_validator
import re

class UserBase(BaseModel):
    # ... съществуващи полета ...

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if v is not None and (len(v) < 3 or len(v) > 50):
            raise ValueError('Потребителското име трябва да е между 3 и 50 символа')
        return v

    @field_validator('egn')
    @classmethod
    def validate_egn(cls, v):
        if v is not None:
            if not re.match(r'^\d{10}$', v):
                raise ValueError('ЕГН трябва да съдържа точно 10 цифри')
        return v

    @field_validator('iban')
    @classmethod
    def validate_iban(cls, v):
        if v is not None:
            v = v.replace(' ', '').upper()
            if not re.match(r'^[A-Z]{2}\d{2}[A-Z0-9]{4,}$', v):
                raise ValueError('Невалиден IBAN формат')
        return v

    @field_validator('phone_number')
    @classmethod
    def validate_phone(cls, v):
        if v is not None:
            v = v.replace(' ', '').replace('-', '')
            if not re.match(r'^\+?359?\d{9}$', v):
                raise ValueError('Невалиден телефонен номер')
        return v
```

---

## Стьпка 9: Автоматично създаване на работни станции

### 9.1 Проблем

При първоначално стартиране на `init_db()` трябва да се създадат 3-те работни станции за сладкарското производство.

### 9.2 Решение

**В `backend/init_db.py`** - автоматично се създават станциите:

```python
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
        logger.info(f"Създадена работна станция: {ws_data['name']}")
    else:
        logger.info(f"Работна станция вече съществува: {ws_data['name']}")
```

### 9.3 Функция за извикване при нова компания

```python
async def ensure_workstations_for_company(company_id: int, session=None):
    """
    Създава работни станции за дадена фирма ако не съществуват.
    """
    DEFAULT_WORKSTATIONS = [
        {"name": "Пекарна", "description": "Изпичане на блатове и основи"},
        {"name": "Кремове", "description": "Приготвяне на кремове и пълнежи"},
        {"name": "Декорация", "description": "Украса на готовите изделия"},
    ]
    
    # ... логика за създаване ...
```

---

## Пълен списък на файловете за промяна

| Файл | Промяна |
|------|---------|
| `requirements.txt` | Добави `starlette-csrf` |
| `backend/config.py` | Auto-generation на JWT_SECRET_KEY, ENCRYPTION_KEY, CSRF_SECRET_KEY |
| `backend/main.py` | Добави CSRFMiddleware + поправи CORS |
| `backend/auth/limiter.py` | Промени key_func да използва `get_client_ip` |
| `backend/auth/security.py` | Използва settings.ENCRYPTION_KEY |
| `backend/auth/dependencies.py` | Създай нов файл с `require_permission` |
| `migrations/004_remove_email_constraint.sql` | Създай нова миграция |
| `backend/services/backup_service.py` | Филтрирай чувствителни данни |
| `backend/schemas.py` | Добави field validators |
| `backend/init_db.py` | Автоматично създаване на работни станции |
| `frontend/utils/csrf.js` | Създай helper функция |
| `frontend/api/client.js` | Добави интерцептор |

---

## Тестване

### CSRF тест

```bash
# Опитай POST без CSRF токен
curl -X POST https://your-domain.com/api/endpoint \
  -H "Content-Type: application/json" \
  -d '{"data": "test"}'

# Очакван резултат: 403 Forbidden
```

### Тест на auto-generation

```python
# Ако премахнеш ключ от .env, автоматично ще се генерира нов
from backend.config import settings
print(settings.JWT_SECRET_KEY)   # Генерира се ако липсва
print(settings.ENCRYPTION_KEY)    # Генерира се ако липсва
print(settings.CSRF_SECRET_KEY)   # Генерира се ако липсва
```

### Тест на workstations

```bash
python -m backend.init_db
# Очакван изход:
# Създадена работна станция: Пекарна за фирма Основна Фирма
# Създадена работна станция: Кремове за фирма Основна Фирма
# Създадена работна станция: Декорация за фирма Основна Фирма
```

---

## Забележки

- Cookie е с `httponly=False` за да може JavaScript да го чете
- Cookie е с `samesite="lax"` - работи за same-site заявки
- За production използвай `secure=True` (HTTPS задължително)
- Всички stateful заявки (POST, PUT, DELETE) изискват X-CSRFToken header
- GraphQL е exempt защото използва JWT authentication
- ENCRYPTION_KEY трябва да е валиден Fernet ключ (base64, 32 bytes)
- Ключовете се генерират само веднъж при първо стартиране
- При следващи стартирания се използват съществуващите ключове
