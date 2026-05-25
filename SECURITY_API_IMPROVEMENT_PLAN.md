# Chronos Security & API Design Improvement Plan

**Дата:** 2026-05-25  
**Статус:** Draft  
**Приоритет:** Висок  
**Очаквана продължителност:** 4-6 седмици

---

## 📋 Executive Summary

Този план адресира критичните и средни слабости, идентифицирани в Security Audit и API Design Review. Целта е да се подобри сигурността, производителността и developer experience на Chronos GraphQL API.

**Ключови области:**
1. SQL Injection Prevention
2. Distributed Caching (Redis)
3. API Pagination
4. N+1 Query Optimization
5. Input Validation Hardening
6. Rate Limiting & DoS Protection

---

## 🎯 Phase 1: Critical Security Fixes (Седмица 1-2)

### 1.1 SQL Injection Prevention

**Проблем:** Използване на f-strings в SQL queries създава SQL injection риск.

**Засегнати файлове:**
- `backend/database/transaction_manager.py` (5 локации)
- `backend/routers/deploy.py` (8 локации)
- `backend/init_db.py` (множество локации)

**Задачи:**

#### Task 1.1.1: Fix transaction_manager.py
**Файл:** `backend/database/transaction_manager.py`

**Текущ код (ред 163):**
```python
await tx.execute(text(f"SET lock_timeout = {lock_timeout * 1000}"))
```

**Нов код:**
```python
await tx.execute(
    text("SET lock_timeout = :timeout"),
    {"timeout": lock_timeout * 1000}
)
```

**Текущ код (ред 269):**
```python
await db.execute(text(f"SAVEPOINT {safe_name}"))
```

**Нов код:**
```python
# Savepoint names cannot be parameterized, but we validate them
import re
if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', safe_name):
    raise ValueError(f"Invalid savepoint name: {safe_name}")
await db.execute(text(f"SAVEPOINT {safe_name}"))
```

**Приемни критерии:**
- [ ] Всички f-string SQL queries са заменени с parameterized queries
- [ ] Savepoint names се валидират с regex
- [ ] Unit тестове минават
- [ ] Няма lint warnings

---

#### Task 1.1.2: Fix deploy.py
**Файл:** `backend/routers/deploy.py`

**Текущ код (ред 75-78):**
```python
await db.execute(text(f"SELECT pg_advisory_lock({lock_id})"))
await db.execute(text(f"SELECT set_config('app.maintenance_reason', '{reason}', false)"))
```

**Нов код:**
```python
await db.execute(
    text("SELECT pg_advisory_lock(:lock_id)"),
    {"lock_id": lock_id}
)
await db.execute(
    text("SELECT set_config('app.maintenance_reason', :reason, false)"),
    {"reason": reason}
)
```

**Приемни критерии:**
- [ ] Всички SQL queries използват parameterized syntax
- [ ] Maintenance reason се escape-ва правилно
- [ ] Integration тестове минават

---

#### Task 1.1.3: Fix init_db.py
**Файл:** `backend/init_db.py`

**Стратегия:** Тези queries са за DDL (ALTER TABLE), които не поддържат parameterized queries. Вместо това:
1. Валидирай table/column names с whitelist
2. Използвай SQLAlchemy Core вместо raw SQL

**Нов подход:**
```python
from sqlalchemy import text
from sqlalchemy.dialects import postgresql

# Whitelist на позволени table names
ALLOWED_TABLES = {
    "shifts", "timelogs", "users", "employment_contracts",
    "payroll_deductions", "leave_requests", "recipes",
    "production_orders", "companies"
}

# Whitelist на позволени column names
ALLOWED_COLUMNS = {
    "pay_multiplier", "break_duration_minutes", "qr_secret",
    "failed_login_attempts", "locked_until", "salary_calculation_type",
    # ... добави всички
}

def validate_table_name(table_name: str):
    if table_name not in ALLOWED_TABLES:
        raise ValueError(f"Table '{table_name}' not in whitelist")

def validate_column_name(column_name: str):
    if column_name not in ALLOWED_COLUMNS:
        raise ValueError(f"Column '{column_name}' not in whitelist")

# Пример за безопасно използване:
validate_table_name("users")
validate_column_name("phone_number")
await conn.execute(text(
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS phone_number VARCHAR(20)"
))
```

**Приемни критерии:**
- [ ] Всички table/column names са в whitelist
- [ ] Validation функции са добавени
- [ ] Init script работи без грешки

---

### 1.2 Distributed Caching с Redis

**Проблем:** In-memory permission cache не се споделя между worker processes.

**Засегнат файл:** `backend/auth/rbac_service.py`

#### Task 1.2.1: Инсталирай Redis dependencies
**Команда:**
```bash
pip install redis[hiredis] async-redis
```

**Обнови `backend/requirements.txt`:**
```
redis[hiredis]>=5.0.0
async-redis>=0.1.0
```

---

#### Task 1.2.2: Създай Redis client
**Нов файл:** `backend/cache/redis_client.py`

```python
import json
import logging
from typing import Any

import redis.asyncio as redis
from backend.config import settings

logger = logging.getLogger(__name__)

class RedisCache:
    def __init__(self):
        self.redis_url = settings.REDIS_URL or "redis://localhost:6379/0"
        self.client = None
    
    async def connect(self):
        if not self.client:
            self.client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            logger.info("Redis cache connected")
    
    async def disconnect(self):
        if self.client:
            await self.close()
            logger.info("Redis cache disconnected")
    
    async def get(self, key: str) -> Any | None:
        if not self.client:
            await self.connect()
        
        try:
            value = await self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis GET error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 300):
        if not self.client:
            await self.connect()
        
        try:
            await self.client.setex(
                key,
                ttl,
                json.dumps(value)
            )
        except Exception as e:
            logger.error(f"Redis SET error: {e}")
    
    async def delete(self, key: str):
        if not self.client:
            await self.connect()
        
        try:
            await self.client.delete(key)
        except Exception as e:
            logger.error(f"Redis DELETE error: {e}")
    
    async def delete_pattern(self, pattern: str):
        """Delete all keys matching pattern"""
        if not self.client:
            await self.connect()
        
        try:
            async for key in self.client.scan_iter(match=pattern):
                await self.client.delete(key)
        except Exception as e:
            logger.error(f"Redis DELETE pattern error: {e}")

# Global instance
cache = RedisCache()
```

---

#### Task 1.2.3: Обнови rbac_service.py
**Файл:** `backend/auth/rbac_service.py`

**Промени:**
```python
from backend.cache.redis_client import cache

class PermissionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        # Премахни in-memory cache
    
    async def get_user_permissions(
        self,
        user_id: int,
        company_id: int | None = None,
    ) -> set[str]:
        cache_key = f"permissions:user_{user_id}:company_{company_id}"
        
        # Try Redis cache first
        cached = await cache.get(cache_key)
        if cached:
            return set(cached["permissions"])
        
        # Build permissions from DB (existing code)
        permissions = set()
        # ... existing query logic ...
        
        # Cache for 2 minutes (по-кратко от 5)
        await cache.set(
            cache_key,
            {"permissions": list(permissions)},
            ttl=120  # 2 минути
        )
        
        return permissions
    
    async def clear_cache(self, user_id: int | None = None):
        """Clear permission cache"""
        if user_id:
            pattern = f"permissions:user_{user_id}:*"
            await cache.delete_pattern(pattern)
        else:
            await cache.delete_pattern("permissions:*")
```

**Приемни критерии:**
- [ ] Redis client е създаден
- [ ] Permission cache използва Redis
- [ ] TTL е намален на 2 минути
- [ ] Cache invalidation работи
- [ ] Fallback към in-memory cache ако Redis е недостъпен

---

#### Task 1.2.4: Добави Redis в docker-compose
**Файл:** `docker-compose.yml`

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes
    restart: unless-stopped

volumes:
  redis-data:
```

**Обнови `backend/config.py`:**
```python
class Settings(BaseSettings):
    # ... existing settings ...
    REDIS_URL: str = "redis://redis:6379/0"
```

---

### 1.3 API Key Rate Limiting

**Проблем:** API keys нямат rate limiting.

**Засегнат файл:** `backend/auth/jwt_utils.py`

#### Task 1.3.1: Добави rate limiting за API keys
**Файл:** `backend/auth/limiter.py` (вече съществува)

**Обнови:**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],
    storage_uri=settings.REDIS_URL,
)

# Специфични лимити за API keys
API_KEY_LIMITS = {
    "default": "1000/hour",
    "premium": "10000/hour",
}
```

**Обнови `backend/auth/jwt_utils.py`:**
```python
from backend.auth.limiter import limiter

async def get_current_user(
    request: Request, db: AsyncSession = Depends(get_db),
) -> schemas.User:
    # ... existing code ...
    
    # API Key authentication
    api_key = request.headers.get("X-API-Key")
    if api_key:
        # Rate limit per API key
        limiter.limit(API_KEY_LIMITS.get(api_key.tier, "default"))(request)
        
        key_obj = await crud.verify_api_key(db, api_key)
        # ... rest of logic ...
```

**Приемни критерии:**
- [ ] Rate limiting е добавен за API keys
- [ ] Лимитите се съхраняват в Redis
- [ ] 429 Too Many Requests се връща при превишаване

---

## 🎯 Phase 2: API Design Improvements (Седмица 3-4)

### 2.1 Cursor-Based Pagination

**Проблем:** List queries връщат всички резултати без pagination.

**Засегнати файлове:**
- `backend/graphql/queries/*.py` (всички list queries)

#### Task 2.1.1: Създай pagination utilities
**Нов файл:** `backend/graphql/utils/pagination.py`

```python
import base64
from typing import Any, Generic, TypeVar
from dataclasses import dataclass

import strawberry

T = TypeVar("T")

@strawberry.type
class PageInfo:
    has_next_page: bool
    has_previous_page: bool
    start_cursor: str | None
    end_cursor: str | None

@strawberry.type
class Edge(Generic[T]):
    node: T
    cursor: str

@strawberry.type
class Connection(Generic[T]):
    edges: list[Edge[T]]
    page_info: PageInfo

def encode_cursor(id: int) -> str:
    """Encode ID to cursor string"""
    return base64.b64encode(f"cursor:{id}".encode()).decode()

def decode_cursor(cursor: str) -> int:
    """Decode cursor string to ID"""
    decoded = base64.b64decode(cursor.encode()).decode()
    if not decoded.startswith("cursor:"):
        raise ValueError("Invalid cursor format")
    return int(decoded.split(":")[1])

async def paginate_query(
    query,
    db: AsyncSession,
    first: int | None = None,
    after: str | None = None,
    last: int | None = None,
    before: str | None = None,
) -> Connection:
    """Apply cursor-based pagination to SQLAlchemy query"""
    
    # Default page size
    limit = first or last or 20
    limit = min(limit, 100)  # Max 100 items per page
    
    # Apply cursor filter
    if after:
        after_id = decode_cursor(after)
        query = query.where(query.column_descriptions[0]["entity"].id > after_id)
    
    if before:
        before_id = decode_cursor(before)
        query = query.where(query.column_descriptions[0]["entity"].id < before_id)
    
    # Apply limit + 1 to check if there's a next page
    query = query.limit(limit + 1)
    
    # Execute query
    result = await db.execute(query)
    items = result.scalars().all()
    
    # Check if there's a next page
    has_next_page = len(items) > limit
    if has_next_page:
        items = items[:limit]
    
    # Build edges
    edges = [
        Edge(node=item, cursor=encode_cursor(item.id))
        for item in items
    ]
    
    # Build page info
    page_info = PageInfo(
        has_next_page=has_next_page,
        has_previous_page=after is not None,
        start_cursor=edges[0].cursor if edges else None,
        end_cursor=edges[-1].cursor if edges else None,
    )
    
    return Connection(edges=edges, page_info=page_info)
```

---

#### Task 2.1.2: Обнови User query
**Файл:** `backend/graphql/queries/user.py`

**Текущ код:**
```python
@strawberry.field
async def users(self, info: Info) -> list[User]:
    db = info.context["db"]
    result = await db.execute(select(DbUser))
    users = result.scalars().all()
    return [User.from_pydantic(u) for u in users]
```

**Нов код:**
```python
from backend.graphql.utils.pagination import Connection, Edge, PageInfo, paginate_query

@strawberry.type
class UserConnection(Connection[User]):
    pass

@strawberry.field
async def users(
    self,
    info: Info,
    first: int | None = None,
    after: str | None = None,
    last: int | None = None,
    before: str | None = None,
) -> UserConnection:
    db = info.context["db"]
    query = select(DbUser).order_by(DbUser.id)
    
    connection = await paginate_query(
        query, db,
        first=first,
        after=after,
        last=last,
        before=before,
    )
    
    # Convert nodes to GraphQL types
    edges = [
        Edge(node=User.from_pydantic(edge.node), cursor=edge.cursor)
        for edge in connection.edges
    ]
    
    return UserConnection(edges=edges, page_info=connection.page_info)
```

**GraphQL Schema:**
```graphql
type UserConnection {
  edges: [UserEdge!]!
  pageInfo: PageInfo!
}

type UserEdge {
  node: User!
  cursor: String!
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}

type Query {
  users(
    first: Int
    after: String
    last: Int
    before: String
  ): UserConnection!
}
```

**Приемни критерии:**
- [ ] Pagination utility е създаден
- [ ] User query поддържа cursor-based pagination
- [ ] Frontend е обновен да използва pagination
- [ ] Unit тестове минават

---

#### Task 2.1.3: Обнови останалите list queries
**Файлове:**
- `backend/graphql/queries/invoice.py`
- `backend/graphql/queries/vehicle.py`
- `backend/graphql/queries/recipe.py`
- `backend/graphql/queries/contract.py`
- (и всички останали)

**Стратегия:** Приложи същия pattern като Task 2.1.2 за всички list queries.

**Приоритет:**
1. Users (вече направено)
2. Invoices (висок трафик)
3. Vehicles
4. Recipes
5. Contracts
6. Останалите

---

### 2.2 DataLoader за N+1 Query Prevention

**Проблем:** Resolvers правят отделни queries за всеки item.

**Засегнати файлове:**
- `backend/graphql/types/user.py`
- `backend/graphql/types/invoice.py`
- `backend/graphql/types/vehicle.py`

#### Task 2.2.1: Създай DataLoader factory
**Нов файл:** `backend/graphql/dataloaders/__init__.py`

```python
from typing import Any
from collections import defaultdict

from aiodataloader import DataLoader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

class SQLAlchemyDataLoader(DataLoader):
    """Generic DataLoader for SQLAlchemy models"""
    
    def __init__(
        self,
        model_class,
        db: AsyncSession,
        key_field: str = "id",
    ):
        super().__init__()
        self.model_class = model_class
        self.db = db
        self.key_field = key_field
    
    async def batch_load_fn(self, keys: list[Any]) -> list[Any]:
        """Batch load entities by keys"""
        query = select(self.model_class).where(
            getattr(self.model_class, self.key_field).in_(keys)
        )
        result = await self.db.execute(query)
        entities = result.scalars().all()
        
        # Create lookup dict
        entity_map = {
            getattr(entity, self.key_field): entity
            for entity in entities
        }
        
        # Return in same order as keys
        return [entity_map.get(key) for key in keys]

def create_dataloaders(db: AsyncSession) -> dict[str, DataLoader]:
    """Create all dataloaders for GraphQL context"""
    from backend.database.models import (
        Company, Department, Position, Role,
        Invoice, Vehicle, Recipe, User,
    )
    
    return {
        "company_by_id": SQLAlchemyDataLoader(Company, db),
        "department_by_id": SQLAlchemyDataLoader(Department, db),
        "position_by_id": SQLAlchemyDataLoader(Position, db),
        "role_by_id": SQLAlchemyDataLoader(Role, db),
        "user_by_id": SQLAlchemyDataLoader(User, db),
        "invoice_by_id": SQLAlchemyDataLoader(Invoice, db),
        "vehicle_by_id": SQLAlchemyDataLoader(Vehicle, db),
        "recipe_by_id": SQLAlchemyDataLoader(Recipe, db),
    }
```

---

#### Task 2.2.2: Обнови GraphQL context
**Файл:** `backend/main.py`

**Текущ код:**
```python
async def get_context(request: Request):
    return {
        "db": request.state.db,
        "user": request.state.user,
        "dataloaders": {
            "role_by_id": ...,  # existing
        },
    }
```

**Нов код:**
```python
from backend.graphql.dataloaders import create_dataloaders

async def get_context(request: Request):
    db = request.state.db
    
    return {
        "db": db,
        "user": request.state.user,
        "dataloaders": create_dataloaders(db),
    }
```

---

#### Task 2.2.3: Обнови User type resolvers
**Файл:** `backend/graphql/types/user.py`

**Текущ код:**
```python
@strawberry.field
async def company(self, info: Info) -> Company | None:
    if not self.company_id:
        return None
    db = info.context["db"]
    res = await db.get(DbCompany, self.company_id)
    return Company.from_pydantic(res) if res else None
```

**Нов код:**
```python
@strawberry.field
async def company(self, info: Info) -> Company | None:
    if not self.company_id:
        return None
    loader = info.context["dataloaders"]["company_by_id"]
    result = await loader.load(self.company_id)
    return Company.from_pydantic(result) if result else None
```

**Приложи за:**
- `company` resolver
- `department` resolver
- `position` resolver
- `role` resolver (вече използва DataLoader)

**Приемни критерии:**
- [ ] DataLoader factory е създаден
- [ ] Всички relation resolvers използват DataLoader
- [ ] N+1 queries са елиминирани
- [ ] Performance тестове показват подобрение

---

### 2.3 Input Validation Hardening

**Проблем:** Някои mutations нямат explicit input validation.

**Засегнати файлове:**
- `backend/schemas/user.py`
- `backend/schemas/invoice.py`
- `backend/schemas/contract.py`

#### Task 2.3.1: Добави Pydantic validators
**Файл:** `backend/schemas/user.py`

**Текущ код:**
```python
class UserCreate(UserBase):
    password: str
    password_force_change: bool = False
```

**Нов код:**
```python
from pydantic import Field, field_validator

class UserCreate(UserBase):
    password: str = Field(
        min_length=8,
        max_length=128,
        description="Password must be at least 8 characters"
    )
    password_force_change: bool = False
    
    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password has minimum strength"""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v
```

---

#### Task 2.3.2: Добави email validation
**Файл:** `backend/schemas/user.py`

**Нов код:**
```python
from pydantic import EmailStr, field_validator

class UserBase(CustomBaseModel):
    email: EmailStr | None = None
    
    @field_validator("email")
    @classmethod
    def validate_email_domain(cls, v: str | None) -> str | None:
        """Validate email is from allowed domain"""
        if v is None:
            return v
        
        # Optional: restrict to company domain
        # allowed_domains = ["company.com", "partner.com"]
        # domain = v.split("@")[1]
        # if domain not in allowed_domains:
        #     raise ValueError(f"Email must be from {allowed_domains}")
        
        return v.lower()
```

---

#### Task 2.3.3: Добави invoice validation
**Файл:** `backend/schemas/invoice.py`

**Нов код:**
```python
from pydantic import Field, field_validator
from decimal import Decimal

class Invoice(CustomBaseModel):
    id: int
    number: str = Field(min_length=1, max_length=50)
    type: str = Field(pattern="^(incoming|outgoing)$")
    status: str = Field(pattern="^(draft|sent|paid|cancelled)$")
    subtotal: Decimal = Field(ge=0)
    vat_amount: Decimal = Field(ge=0)
    total: Decimal = Field(ge=0)
    
    @field_validator("total")
    @classmethod
    def validate_total(cls, v: Decimal, info) -> Decimal:
        """Validate total = subtotal + vat_amount"""
        if "subtotal" in info.data and "vat_amount" in info.data:
            expected = info.data["subtotal"] + info.data["vat_amount"]
            if v != expected:
                raise ValueError(
                    f"Total ({v}) must equal subtotal + vat_amount ({expected})"
                )
        return v
```

**Приемни критерии:**
- [ ] Всички input полета имат validation
- [ ] Pydantic validators са добавени
- [ ] Error messages са ясни и информативни
- [ ] Unit тестове покриват validation cases

---

## 🎯 Phase 3: Advanced Improvements (Седмица 5-6)

### 3.1 Standardized Mutation Responses

**Проблем:** Mutations връщат директно entity вместо wrapper.

#### Task 3.1.1: Създай response types
**Нов файл:** `backend/graphql/types/response.py`

```python
from typing import Generic, TypeVar
import strawberry

T = TypeVar("T")

@strawberry.type
class MutationError:
    field: str | None
    message: str
    code: str | None = None

@strawberry.type
class MutationResponse(Generic[T]):
    success: bool
    data: T | None = None
    errors: list[MutationError] = strawberry.field(default_factory=list)
    
    @classmethod
    def success_response(cls, data: T) -> "MutationResponse[T]":
        return cls(success=True, data=data, errors=[])
    
    @classmethod
    def error_response(
        cls,
        field: str | None,
        message: str,
        code: str | None = None,
    ) -> "MutationResponse[T]":
        error = MutationError(field=field, message=message, code=code)
        return cls(success=False, data=None, errors=[error])
```

---

#### Task 3.1.2: Обнови createUser mutation
**Файл:** `backend/graphql/mutations/user.py`

**Текущ код:**
```python
@strawberry.mutation
async def create_user(
    self,
    info: Info,
    user_input: UserCreate,
) -> User:
    # ... logic ...
    return User.from_pydantic(user)
```

**Нов код:**
```python
from backend.graphql.types.response import MutationResponse

@strawberry.type
class CreateUserResponse(MutationResponse[User]):
    pass

@strawberry.mutation
async def create_user(
    self,
    info: Info,
    user_input: UserCreate,
) -> CreateUserResponse:
    try:
        # ... existing logic ...
        user = await create_user_service(db, user_input)
        return CreateUserResponse.success_response(User.from_pydantic(user))
    
    except ValidationException as e:
        return CreateUserResponse.error_response(
            field=e.field,
            message=str(e),
            code="VALIDATION_ERROR",
        )
    
    except Exception as e:
        logger.error(f"Create user error: {e}")
        return CreateUserResponse.error_response(
            field=None,
            message="An unexpected error occurred",
            code="INTERNAL_ERROR",
        )
```

**GraphQL Schema:**
```graphql
type CreateUserResponse {
  success: Boolean!
  data: User
  errors: [MutationError!]!
}

type MutationError {
  field: String
  message: String!
  code: String
}

type Mutation {
  createUser(userInput: UserCreateInput!): CreateUserResponse!
}
```

**Приемни критерии:**
- [ ] Response types са създадени
- [ ] Всички mutations използват standardized response
- [ ] Frontend е обновен да обработва errors
- [ ] Error messages са user-friendly

---

### 3.2 Query Complexity Limiting

**Проблем:** Липсва защита срещу complex queries (DoS risk).

#### Task 3.2.1: Добави query depth limiter
**Файл:** `backend/graphql/schema.py`

**Нов код:**
```python
from strawberry.extensions import QueryDepthLimiter, AddValidationRules
from graphql.validation import NoFragmentCyclesRule

schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    extensions=[
        ModuleGuardMiddleware,
        ChronosErrorExtension,
        QueryDepthLimiter(max_depth=10),  # Limit query depth
        AddValidationRules([NoFragmentCyclesRule]),
    ],
)
```

---

#### Task 3.2.2: Добави query complexity analyzer
**Нов файл:** `backend/graphql/extensions/complexity_limiter.py`

```python
import logging
from typing import Any

from strawberry.extensions import SchemaExtension

logger = logging.getLogger(__name__)

class QueryComplexityLimiter(SchemaExtension):
    """Limit query complexity to prevent DoS attacks"""
    
    def __init__(
        self,
        max_complexity: int = 1000,
        max_depth: int = 10,
        max_aliases: int = 10,
    ):
        self.max_complexity = max_complexity
        self.max_depth = max_depth
        self.max_aliases = max_aliases
    
    def on_operation(self):
        # Analyze query complexity
        query = self.execution_context.query
        
        # Count depth
        depth = self._calculate_depth(query)
        if depth > self.max_depth:
            raise Exception(
                f"Query depth {depth} exceeds maximum {self.max_depth}"
            )
        
        # Count aliases
        aliases = self._count_aliases(query)
        if aliases > self.max_aliases:
            raise Exception(
                f"Query has {aliases} aliases, maximum is {self.max_aliases}"
            )
        
        # Calculate complexity (simplified)
        complexity = self._calculate_complexity(query)
        if complexity > self.max_complexity:
            raise Exception(
                f"Query complexity {complexity} exceeds maximum {self.max_complexity}"
            )
        
        yield
    
    def _calculate_depth(self, query: str) -> int:
        """Calculate query depth by counting braces"""
        depth = 0
        max_depth = 0
        for char in query:
            if char == "{":
                depth += 1
                max_depth = max(max_depth, depth)
            elif char == "}":
                depth -= 1
        return max_depth
    
    def _count_aliases(self, query: str) -> int:
        """Count query aliases"""
        return query.count(":")
    
    def _calculate_complexity(self, query: str) -> int:
        """Calculate query complexity (simplified)"""
        # Count fields, connections, etc.
        # This is a simplified version - production should use graphql-core
        return query.count("{") * 10
```

**Обнови `backend/graphql/schema.py`:**
```python
from backend.graphql.extensions.complexity_limiter import QueryComplexityLimiter

schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    extensions=[
        ModuleGuardMiddleware,
        ChronosErrorExtension,
        QueryComplexityLimiter(
            max_complexity=1000,
            max_depth=10,
            max_aliases=10,
        ),
    ],
)
```

**Приемни критерии:**
- [ ] Query depth limiter е добавен
- [ ] Query complexity analyzer е създаден
- [ ] DoS protection е активна
- [ ] Логове за blocked queries

---

## 📊 Success Metrics

### Security Metrics
- [ ] 0 SQL injection vulnerabilities
- [ ] Permission cache hit rate > 90%
- [ ] API key rate limiting active
- [ ] 0 critical security findings

### Performance Metrics
- [ ] N+1 queries eliminated (verify with query logging)
- [ ] Average query time < 100ms
- [ ] Pagination reduces response size by 80%
- [ ] DataLoader reduces DB queries by 70%

### Developer Experience Metrics
- [ ] All mutations have standardized responses
- [ ] Error messages are clear and actionable
- [ ] API documentation is complete
- [ ] Frontend migration to new patterns complete

---

## 🔄 Migration Strategy

### Backward Compatibility
1. **Pagination:** Добави нови paginated queries, запази старите за 2 седмици
2. **Mutation Responses:** Добави нови response types, запази старите за 1 месец
3. **DataLoader:** Transparent за frontend, няма breaking changes

### Rollout Plan
1. **Week 1-2:** Security fixes (SQL injection, Redis, rate limiting)
2. **Week 3-4:** API improvements (pagination, DataLoader, validation)
3. **Week 5-6:** Advanced features (mutation responses, complexity limiting)
4. **Week 7:** Testing, documentation, frontend migration
5. **Week 8:** Production deployment

---

## 📝 Documentation Updates

### Required Documentation
1. **API Documentation:**
   - Pagination guide
   - Error handling guide
   - Rate limiting documentation

2. **Security Documentation:**
   - SQL injection prevention guidelines
   - Redis caching best practices
   - API key management

3. **Developer Guide:**
   - How to use DataLoader
   - How to add validation
   - How to create mutations

---

## ✅ Checklist

### Phase 1: Security
- [ ] SQL injection fixes complete
- [ ] Redis caching implemented
- [ ] Rate limiting active
- [ ] Security tests passing

### Phase 2: API Design
- [ ] Pagination implemented
- [ ] DataLoader integrated
- [ ] Input validation hardened
- [ ] Performance tests passing

### Phase 3: Advanced
- [ ] Mutation responses standardized
- [ ] Query complexity limiting active
- [ ] Documentation complete
- [ ] Frontend migration complete

---

## 🎓 Training & Knowledge Transfer

### Team Training Sessions
1. **SQL Injection Prevention** (1 hour)
2. **Redis Caching Patterns** (1 hour)
3. **GraphQL Pagination** (1.5 hours)
4. **DataLoader Best Practices** (1 hour)

### Code Review Guidelines
- All PRs must include:
  - Security review checklist
  - Performance impact assessment
  - Validation coverage verification

---

**Краен срок:** 8 седмици от стартиране  
**Отговорник:** Tech Lead  
**Статус:** Готов за одобрение
