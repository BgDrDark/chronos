# 📋 ПЛАН ЗА РЕФАКТОРИНГ НА BACKEND - REPOSITORY PATTERN

## Обзор

| Параметър | Стойност |
|-----------|----------|
| **Цел** | Подобряване на code quality чрез Repository Pattern |
| **Приоритет** | Code Quality (c) |
| **Дата на старт** | 2026-04-18 |
| **Очаквано време** | 3.5 часа |

---

## 1. ТЕКУЩО СЪСТОЯНИЕ

### Проблеми

| # | Проблем | Файл | Редове |
|---|---------|------|--------|
| 1 | Твърде голям файл | `crud.py` | 3231 |
| 2 | Дублиране на SQL заявки | `crud.py` | 50+ |
| 3 | Липса на модулност | `crud.py` | - |
| 4 | Трудно за поддръжка | `crud.py` | - |
| 5 | Дублирани файлове | `crud copy.py`, `crud_backup.py` | 5600 |

### Съществуващи модели (141 модела)

- Core: User, Role, Company, Department, Position (10)
- Time Tracking: TimeLog, Shift, WorkSchedule, LeaveRequest (8)
- Payroll: Payroll, Payslip, Bonus, AdvancePayment (15+)
- TRZ: EmploymentContract, ContractAnnex (20+)
- Production: ProductionOrder, Recipe, Batch (20+)
- Warehouse: Ingredient, StockConsumptionLog (15+)
- Access Control: Gateway, Terminal (10+)
- Other (40+)

---

## 2. ПЛАН ЗА ИМПЛЕМЕНТАЦИЯ

### Фаза 1: Подготовка

#### Стъпка 1.1: Анализ на съществуващия код
- [x] Идентифицирани 19+ повтарящи се SQL заявки
- [x] Идентифицирани категории модели
- [x] Определени dependencies между модулите

#### Стъпка 1.2: Създаване на директория структура
```
backend/crud/
├── __init__.py
├── repositories/
│   ├── __init__.py
│   ├── base.py          # BaseRepository class
│   ├── user_repo.py     # User-related CRUD
│   ├── company_repo.py  # Company-related CRUD
│   ├── time_repo.py     # Time tracking CRUD
│   ├── payroll_repo.py  # Payroll CRUD
│   ├── trz_repo.py      # TRZ/Employment CRUD
│   ├── production_repo.py
│   ├── warehouse_repo.py
│   └── access_repo.py
├── helpers.py
└── utils.py
```

#### Стъпка 1.3: Почистване на дублирани файлове
- [ ] Изтриване на `crud copy.py`
- [ ] Изтриване на `crud_backup.py`

---

### Фаза 2: Base Repository (30 мин)

#### Стъпка 2.1: Създаване на base.py

```python
# backend/crud/repositories/base.py

from typing import TypeVar, Generic, Optional, List, Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

T = TypeVar('T')

class BaseRepository(Generic[T]):
    """Базов клас за всички repositories"""
    
    model: Type[T]
    
    async def get_by_id(self, db: AsyncSession, id: int) -> Optional[T]:
        """Връща запис по ID"""
        result = await db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_all(
        self, 
        db: AsyncSession, 
        limit: int = 100, 
        offset: int = 0,
        filters: dict = None,
        order_by: str = None,
        order_desc: bool = False
    ) -> List[T]:
        """Връща всички записи с pagination"""
        query = select(self.model)
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)
        
        if order_by and hasattr(self.model, order_by):
            col = getattr(self.model, order_by)
            query = query.order_by(col.desc() if order_desc else col.asc())
        
        query = query.limit(limit).offset(offset)
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def count(self, db: AsyncSession, filters: dict = None) -> int:
        """Брой на записите"""
        query = select(func.count(self.model.id))
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)
        
        result = await db.execute(query)
        return result.scalar() or 0
    
    async def create(self, db: AsyncSession, **kwargs) -> T:
        """Създава нов запис"""
        instance = self.model(**kwargs)
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
        return instance
    
    async def update(self, db: AsyncSession, id: int, **kwargs) -> Optional[T]:
        """Обновява запис"""
        instance = await self.get_by_id(db, id)
        if instance:
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            await db.flush()
            await db.refresh(instance)
        return instance
    
    async def delete(self, db: AsyncSession, id: int) -> bool:
        """Изтрива запис"""
        instance = await self.get_by_id(db, id)
        if instance:
            await db.delete(instance)
            await db.flush()
            return True
        return False
    
    async def exists(self, db: AsyncSession, id: int) -> bool:
        """Проверява дали записът съществува"""
        result = await db.execute(
            select(func.count(self.model.id)).where(self.model.id == id)
        )
        return (result.scalar() or 0) > 0
```

#### Стъпка 2.2: Създаване на __init__.py в repositories/
```python
# backend/crud/repositories/__init__.py

from .base import BaseRepository
from .user_repo import UserRepository
from .company_repo import CompanyRepository
from .time_repo import TimeTrackingRepository
from .payroll_repo import PayrollRepository
from .trz_repo import TRZRepository
from .production_repo import ProductionRepository
from .warehouse_repo import WarehouseRepository
from .access_repo import AccessRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
    "CompanyRepository", 
    "TimeTrackingRepository",
    "PayrollRepository",
    "TRZRepository",
    "ProductionRepository",
    "WarehouseRepository",
    "AccessRepository",
]
```

---

### Фаза 3: Category Repositories (2 часа)

#### Стъпка 3.1: UserRepository (15 мин)

```python
# backend/crud/repositories/user_repo.py

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from backend.database.models import User, UserSession, AuthKey, Role
from .base import BaseRepository


class UserRepository(BaseRepository):
    """Repository за потребители"""
    
    model = User
    
    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """Връща потребител по email"""
        result = await db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_by_username(self, db: AsyncSession, username: str) -> Optional[User]:
        """Връща потребител по username"""
        result = await db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()
    
    async def get_with_relations(self, db: AsyncSession, user_id: int) -> Optional[User]:
        """Връща потребител с role и company"""
        result = await db.execute(
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.role), selectinload(User.company))
        )
        return result.scalar_one_or_none()
    
    async def get_active_sessions(self, db: AsyncSession, user_id: int) -> List[UserSession]:
        """Връща активните сесии на потребителя"""
        result = await db.execute(
            select(UserSession)
            .where(UserSession.user_id == user_id)
            .where(UserSession.is_active == True)
        )
        return list(result.scalars().all())


user_repo = UserRepository()
```

#### Стъпка 3.2: CompanyRepository (15 мин)

```python
# backend/crud/repositories/company_repo.py

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.database.models import Company, Department, Position
from .base import BaseRepository


class CompanyRepository(BaseRepository):
    """Repository за компания"""
    
    model = Company
    
    async def get_with_departments(self, db: AsyncSession, company_id: int) -> Optional[Company]:
        """Връща компания с департаменти"""
        result = await db.execute(
            select(Company)
            .where(Company.id == company_id)
            .options(selectinload(Company.departments))
        )
        return result.scalar_one_or_none()
    
    async def get_departments(self, db: AsyncSession, company_id: int) -> List[Department]:
        """Връща департаментите на компанията"""
        result = await db.execute(
            select(Department).where(Department.company_id == company_id)
        )
        return list(result.scalars().all())
    
    async def get_positions(self, db: AsyncSession, department_id: int) -> List[Position]:
        """Връща позициите в департамента"""
        result = await db.execute(
            select(Position).where(Position.department_id == department_id)
        )
        return list(result.scalars().all())


company_repo = CompanyRepository()
```

#### Стъпка 3.3: TimeTrackingRepository (15 мин)

```python
# backend/crud/repositories/time_repo.py

from typing import Optional, List
from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from backend.database.models import TimeLog, Shift, WorkSchedule, LeaveRequest
from .base import BaseRepository


class TimeTrackingRepository(BaseRepository):
    """Repository за проследяване на работно време"""
    
    model = TimeLog
    
    async def get_active_timelog(
        self, 
        db: AsyncSession, 
        user_id: int
    ) -> Optional[TimeLog]:
        """Връща активния TimeLog за потребител"""
        result = await db.execute(
            select(TimeLog)
            .where(TimeLog.user_id == user_id)
            .where(TimeLog.end_time == None)
        )
        return result.scalar_one_or_none()
    
    async def get_user_timelogs(
        self, 
        db: AsyncSession, 
        user_id: int,
        start_date: date = None,
        end_date: date = None,
        limit: int = 100
    ) -> List[TimeLog]:
        """Връща всички TimeLog за потребител"""
        query = select(TimeLog).where(TimeLog.user_id == user_id)
        
        if start_date:
            query = query.where(TimeLog.start_time >= start_date)
        if end_date:
            query = query.where(TimeLog.start_time <= end_date)
        
        query = query.order_by(TimeLog.start_time.desc()).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_schedule_for_date(
        self,
        db: AsyncSession,
        user_id: int,
        date: date
    ) -> Optional[WorkSchedule]:
        """Връща график за конкретна дата"""
        result = await db.execute(
            select(WorkSchedule)
            .where(WorkSchedule.user_id == user_id)
            .where(WorkSchedule.date == date)
        )
        return result.scalar_one_or_none()


time_repo = TimeTrackingRepository()
```

#### Стъпка 3.4: PayrollRepository (15 мин)

```python
# backend/crud/repositories/payroll_repo.py

from typing import Optional, List
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.database.models import Payroll, Payslip, Bonus, AdvancePayment
from .base import BaseRepository


class PayrollRepository(BaseRepository):
    """Repository за Payroll"""
    
    model = Payroll
    
    async def get_user_payrolls(
        self,
        db: AsyncSession,
        user_id: int,
        year: int = None,
        month: int = None
    ) -> List[Payroll]:
        """Връща Payroll записи за потребител"""
        query = select(Payroll).where(Payroll.user_id == user_id)
        
        if year:
            query = query.where(Payroll.year == year)
        if month:
            query = query.where(Payroll.month == month)
        
        query = query.order_by(Payroll.year.desc(), Payroll.month.desc())
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_payslips(
        self,
        db: AsyncSession,
        payroll_id: int
    ) -> List[Payslip]:
        """Връща всики Payslip за Payroll"""
        result = await db.execute(
            select(Payslip).where(Payslip.payroll_id == payroll_id)
        )
        return list(result.scalars().all())


payroll_repo = PayrollRepository()
```

#### Стъпка 3.5: TRZRepository (15 мин)

```python
# backend/crud/repositories/trz_repo.py

from typing import Optional, List
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.database.models import EmploymentContract, ContractAnnex
from .base import BaseRepository


class TRZRepository(BaseRepository):
    """Repository за TRZ (Трудови договори)"""
    
    model = EmploymentContract
    
    async def get_user_contracts(
        self,
        db: AsyncSession,
        user_id: int
    ) -> List[EmploymentContract]:
        """Връща договорите на потребител"""
        result = await db.execute(
            select(EmploymentContract)
            .where(EmploymentContract.user_id == user_id)
            .order_by(EmploymentContract.start_date.desc())
        )
        return list(result.scalars().all())
    
    async def get_active_contract(
        self,
        db: AsyncSession,
        user_id: int
    ) -> Optional[EmploymentContract]:
        """Връща активния договор на потребител"""
        result = await db.execute(
            select(EmploymentContract)
            .where(EmploymentContract.user_id == user_id)
            .where(EmploymentContract.status == "active")
            .order_by(EmploymentContract.start_date.desc())
        )
        return result.scalar_one_or_none()
    
    async def get_contract_annexes(
        self,
        db: AsyncSession,
        contract_id: int
    ) -> List[ContractAnnex]:
        """Връща анексите на договор"""
        result = await db.execute(
            select(ContractAnnex)
            .where(ContractAnnex.contract_id == contract_id)
            .order_by(ContractAnnex.created_at.desc())
        )
        return list(result.scalars().all())


trz_repo = TRZRepository()
```

#### Стъпка 3.6: ProductionRepository (15 мин)

```python
# backend/crud/repositories/production_repo.py

from typing import Optional, List
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.database.models import ProductionOrder, Recipe, Batch
from .base import BaseRepository


class ProductionRepository(BaseRepository):
    """Repository за производство"""
    
    model = ProductionOrder
    
    async def get_active_orders(
        self,
        db: AsyncSession,
        company_id: int = None
    ) -> List[ProductionOrder]:
        """Връща активните производствени поръчки"""
        query = select(ProductionOrder).where(ProductionOrder.status.in_(["pending", "in_progress"]))
        
        if company_id:
            query = query.where(ProductionOrder.company_id == company_id)
        
        result = await db.execute(query.order_by(ProductionOrder.scheduled_date))
        return list(result.scalars().all())
    
    async def get_recipes(
        self,
        db: AsyncSession,
        company_id: int = None,
        category: str = None
    ) -> List[Recipe]:
        """Връща рецепти"""
        query = select(Recipe)
        
        if company_id:
            query = query.where(Recipe.company_id == company_id)
        if category:
            query = query.where(Recipe.category == category)
        
        result = await db.execute(query.order_by(Recipe.name))
        return list(result.scalars().all())


production_repo = ProductionRepository()
```

#### Стъпка 3.7: WarehouseRepository (15 мин)

```python
# backend/crud/repositories/warehouse_repo.py

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.database.models import Ingredient, StockConsumptionLog, Supplier
from .base import BaseRepository


class WarehouseRepository(BaseRepository):
    """Repository за склад"""
    
    model = Ingredient
    
    async def get_ingredients_low_stock(
        self,
        db: AsyncSession,
        company_id: int,
        threshold: float = 10.0
    ) -> List[Ingredient]:
        """Връща съставки с ниска наличност"""
        result = await db.execute(
            select(Ingredient)
            .where(Ingredient.company_id == company_id)
            .where(Ingredient.quantity <= threshold)
        )
        return list(result.scalars().all())
    
    async def get_suppliers(
        self,
        db: AsyncSession,
        company_id: int
    ) -> List[Supplier]:
        """Връща доставчиците на компанията"""
        result = await db.execute(
            select(Supplier).where(Supplier.company_id == company_id)
        )
        return list(result.scalars().all())


warehouse_repo = WarehouseRepository()
```

#### Стъпка 3.8: AccessRepository (15 мин)

```python
# backend/crud/repositories/access_repo.py

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.database.models import Gateway, Terminal, TerminalSession
from .base import BaseRepository


class AccessRepository(BaseRepository):
    """Repository за контрол на достъп"""
    
    model = Gateway
    
    async def get_online_gateways(
        self,
        db: AsyncSession,
        company_id: int = None
    ) -> List[Gateway]:
        """Връща онлайн gateway-ове"""
        query = select(Gateway).where(Gateway.is_online == True)
        
        if company_id:
            query = query.where(Gateway.company_id == company_id)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_active_sessions(
        self,
        db: AsyncSession,
        terminal_id: int = None
    ) -> List[TerminalSession]:
        """Връща активни терминални сесии"""
        query = select(TerminalSession).where(TerminalSession.end_time == None)
        
        if terminal_id:
            query = query.where(TerminalSession.terminal_id == terminal_id)
        
        result = await db.execute(query)
        return list(result.scalars().all())


access_repo = AccessRepository()
```

---

### Фаза 4: Backward Compatibility (30 мин)

#### Стъпка 4.1: Създаване на __init__.py

```python
# backend/crud/__init__.py

"""
CRUD модул с Repository Pattern

Забележка: Този модул поддържа backward compatibility със стария crud.py
Новият код трябва да използва repositories директно:
    from backend.crud.repositories import user_repo, company_repo
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

# Import repositories
from backend.crud.repositories import (
    user_repo,
    company_repo,
    time_repo,
    payroll_repo,
    trz_repo,
    production_repo,
    warehouse_repo,
    access_repo,
)

# Aliases за backward compatibility
UserRepository = user_repo.__class__
CompanyRepository = company_repo.__class__

# Запазване на старите функции като wrapper-и
# Това осигурява backward compatibility с mutations.py

async def get_user(db: AsyncSession, user_id: int):
    """Backward compatible wrapper"""
    return await user_repo.get_by_id(db, user_id)

async def get_company(db: AsyncSession, company_id: int):
    """Backward compatible wrapper"""
    return await company_repo.get_by_id(db, company_id)

# Добави останалите wrapper функции тук...
# Пълният списък ще бъде генериран автоматично
```

#### Стъпка 4.2: Exports
```python
# Export на всички публични функции за backward compatibility
__all__ = [
    "user_repo",
    "company_repo", 
    "time_repo",
    "payroll_repo",
    "trz_repo",
    "production_repo",
    "warehouse_repo",
    "access_repo",
    # Backward compatible functions
    "get_user",
    "get_company",
    # ... ще бъдат добавени автоматично
]
```

---

### Фаза 5: Migration на mutations.py (30 мин)

#### Стъпка 5.1: Анализ на imports
```bash
# Намира всички места, които използват crud.py
grep -r "from backend import crud" --include="*.py" backend/
grep -r "from backend.crud import" --include="*.py" backend/
```

#### Стъпка 5.2: Update на imports
```python
# Промени от:
from backend import crud
user = await crud.get_user(db, user_id)

# На:
from backend.crud.repositories import user_repo
user = await user_repo.get_by_id(db, user_id)
```

#### Стъпка 5.3: Тестване
```bash
# Пускане на тестовете
cd backend
pytest tests/ -v
```

---

## 3. ОЧАКВАНИ РЕЗУЛТАТИ

### Преди vs След

| Метрика | Преди | След |
|---------|-------|------|
| Основни файлове | 1 (`crud.py` - 3231 реда) | 8+ repositories |
| Дублирани SQL | 50+ | 0 |
| Модулност | Липсва | Добра |
| Тестваемост | Лоша | Добра |
| Type safety | Липсва | Добавен |

### Спестявания

- ~500 реда код чрез generic BaseRepository
- По-добра организация
- Лесна поддръжка

---

## 4. РИСКОВЕ И МИНИМИЗАЦИЯ

| Риск | Вероятност | Въздействие | Митигация |
|------|------------|-------------|-----------|
| Breaking changes | Средна | Високо | Backward compatibility |
| грешки в миграцията | Средна | Средно | Тестване след всяка стъпка |
| Загуба на функционалност | Ниска | Високо | Пълен review преди merge |

---

## 5. СТЪПКИ ЗА ИЗПЪЛНЕНИЕ

### Ден 1
- [ ] Създаване на директории
- [ ] BaseRepository implementation
- [ ] repositories/__init__.py

### Ден 2
- [ ] UserRepository
- [ ] CompanyRepository
- [ ] TimeTrackingRepository
- [ ] PayrollRepository

### Ден 3
- [ ] TRZRepository
- [ ] ProductionRepository
- [ ] WarehouseRepository
- [ ] AccessRepository

### Ден 4
- [ ] CRUD __init__.py с backward compatibility
- [ ] Тестване на всички repositories
- [ ] Update на imports в mutations.py (ако е необходимо)

---

## 6. VERIFICATION

След всяка стъпка:
1. Пускай тестовете: `pytest tests/ -v`
2. Проверявай че core функционалността работи
3. Документирай промените

---

## 7. ALTERNATIVES CONSIDERED

### Вариант 1: Generic Helpers (отхвърлен)
- По-бързо, но по-малко структурирано
- Губи type safety

### Вариант 2: Plugin Pattern (отложен)
- По-добра модулност, но по-сложно
- За бъдеща имплементация

---

## 8. REFERENCES

- FastAPI Best Practices: https://fastapi.tiangolo.com/best-practices/
- SQLAlchemy Async: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- Repository Pattern: https://docs.microsoft.com/en-us/aspnet/mvc/overview/older-versions/getting-started-with-ef-5-using-mvc-4/implementing-the-repository-and-unit-of-work-patterns

---

## VERSION HISTORY

| Версия | Дата | Автор | Описание |
|--------|------|-------|----------|
| 1.0 | 2026-04-18 | OpenCode | Първоначален план |

---

**Край на плана**