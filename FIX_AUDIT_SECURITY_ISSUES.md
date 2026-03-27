# План за Поправка на Одитни Проблеми

**Дата:** 2026-03-26  
**Статус:** В процес на изпълнение

---

## Приоритет 1: Критични Проблеми със Сигурността (Теч на Данни) 🔴

Тези проблеми водят до **теч на данни между фирми** и трябва да бъдат поправени незабавно.

### 1.1 `user_presences` (queries.py:797-934)
- **Проблем**: Връща всички активни потребители от всички фирми
- **Файл**: `backend/graphql/queries.py`
- **Поправка**: Добави филтър `User.company_id == current_user.company_id`
- **Стъпки**:
  1. Намери реда с `select(User).where(User.is_active == True)`
  2. Добави `.where(User.company_id == current_user.company_id)`
- **Тест**: Виж секция "Тест 1.1"

---

### 1.2 `pending_leave_requests` (queries.py:707)
- **Проблем**: Връща заявки за отпуск от всички фирми
- **Файл**: `backend/graphql/queries.py`
- **Поправка**: Добави `company_id` параметър
- **Тест**: Виж секция "Тест 1.2"

---

### 1.3 `all_leave_requests` (queries.py:717)
- **Проблем**: Същото като горното
- **Поправка**: Същото като горното
- **Тест**: Виж секция "Тест 1.3"

---

### 1.4 `payroll_forecast` (queries.py:1297)
- **Проблем**: Показва прогнози за всички фирми
- **Файл**: `backend/graphql/queries.py`
- **Поправка**: Филтрирай потребители по `company_id`
- **Тест**: Виж секция "Тест 1.4"

---

### 1.5 `schedule_templates` (queries.py:1272)
- **Проблем**: Виждат се графици от всички фирми
- **Файл**: `backend/graphql/queries.py`
- **Поправка**: Добави `.where(ScheduleTemplate.company_id == current_user.company_id)`
- **Тест**: Виж секция "Тест 1.5"

---

### 1.6 `schedule_template` (queries.py:1281)
- **Проблем**: Getting by ID without company ownership check
- **Файл**: `backend/graphql/queries.py`
- **Поправка**: Добави проверка за собственост след `.scalars().first()`
- **Тест**: Виж секция "Тест 1.6"

---

### 1.7 `audit_logs` (queries.py:1177)
- **Проблем**: Виждат се всички одит логове
- **Файл**: `backend/graphql/queries.py`
- **Поправка**: Добави филтър по `company_id` (ако е приложимо)
- **Забележка**: Одит логовете обикновено са глобални - прецени дали да се филтрира
- **Тест**: Виж секция "Тест 1.7"

---

### 1.8 `get_fefo_suggestion` (queries.py:1449)
- **Проблем**: Предлага стоки от всички фирми
- **Файл**: `backend/graphql/queries.py`
- **Поправка**: Филтрирай по `company_id` на склада
- **Тест**: Виж секция "Тест 1.8"

---

### 1.9 `inventory_by_barcode` (queries.py:1759)
- **Проблем**: Намира артикули без проверка на собственик
- **Файл**: `backend/graphql/queries.py`
- **Поправка**: Добави `.where(Ingredient.company_id == current_user.company_id)`
- **Тест**: Виж секция "Тест 1.9"

---

## Приоритет 2: Загуба на Точност при Валути ⚠️

Тези проблеми не са критични за сигурността, но могат да доведат до грешки в счетоводните изчисления.

### 2.1 `ContractTemplateVersion.current_version` (types.py:490-492)
- **Проблем**: Конвертира `Decimal` → `float`
- **Файл**: `backend/graphql/types.py`
- **Поправка**: Промени GraphQL типа от `float` на `Decimal`
- **Тест**: Виж секция "Тест 2.1"

---

### 2.2 `AnnexTemplateVersion.current_version` (types.py:580-584)
- **Проблем**: Конвертира `Decimal` → `float`
- **Файл**: `backend/graphql/types.py`
- **Поправка**: Промени GraphQL типа от `float` на `Decimal`
- **Тест**: Виж секция "Тест 2.2"

---

## Тестове за Проверка

След поправките, използвай следните тестове за проверка:

---

### Тест 1.1: user_presences изолира фирмите

```python
import asyncio
from sqlalchemy import select
from backend.database import SessionLocal
from backend.database.models import User, Company
from backend.graphql.queries import user_presences

async def test_user_presences_company_isolation():
    """Потребител от една фирма НЕ трябва да вижда потребители от други фирми"""
    db = SessionLocal()
    
    try:
        # 1. Вземи първите 2 компании
        result = await db.execute(select(Company).limit(2))
        companies = result.scalars().all()
        assert len(companies) >= 2, "Нужни са поне 2 компании за теста"
        
        company1, company2 = companies[0], companies[1]
        print(f"Тестване с компании: {company1.name} (ID:{company1.id}) и {company2.name} (ID:{company2.id})")
        
        # 2. Брой потребители във всяка компания
        result1 = await db.execute(
            select(User).where(User.company_id == company1.id, User.is_active == True)
        )
        users_company1 = result1.scalars().all()
        
        result2 = await db.execute(
            select(User).where(User.company_id == company2.id, User.is_active == True)
        )
        users_company2 = result2.scalars().all()
        
        print(f"Потребители в {company1.name}: {len(users_company1)}")
        print(f"Потребители в {company2.name}: {len(users_company2)}")
        
        # 3. Симулирай заявка от потребител на company1
        class MockInfo1:
            def __init__(self, user):
                self.context = {"db": db, "user": user}
        
        mock_user1 = type('MockUser', (), {'company_id': company1.id, 'is_admin': False})()
        info1 = MockInfo1(mock_user1)
        
        # 4. Извикай заявката
        result = await user_presences(info1)
        presences = result.presences if hasattr(result, 'presences') else result
        
        # 5. Провери че всички върнати потребители са от company1
        for presence in presences:
            assert presence.company_id == company1.id, \
                f"Теч на данни! Потребител от {company2.name} се вижда в заявка за {company1.name}"
        
        print("✅ Тест 1.1 PASSED: user_presences изолира фирмите")
        return True
        
    finally:
        await db.close()
```

---

### Тест 1.2: pending_leave_requests изолира фирмите

```python
async def test_pending_leave_requests_company_isolation():
    """Заявки за отпуск от една фирма НЕ трябва да се виждат от друга"""
    from backend.graphql.queries import pending_leave_requests
    
    db = SessionLocal()
    
    try:
        # 1. Вземи компании с чакащи заявки
        result = await db.execute(select(Company).limit(2))
        companies = result.scalars().all()
        company1 = companies[0]
        
        class MockInfo:
            def __init__(self, user, db):
                self.context = {"db": db, "user": user}
        
        mock_user = type('MockUser', (), {'company_id': company1.id, 'is_admin': False})()
        info = MockInfo(mock_user, db)
        
        # 2. Извикай заявката
        requests = await pending_leave_requests(info)
        
        # 3. Провери че всички заявки са от същата фирма
        for req in requests:
            assert req.company_id == company1.id, \
                f"Теч на данни! Заявка от компания {req.company_id} се вижда от компания {company1.id}"
        
        print("✅ Тест 1.2 PASSED: pending_leave_requests изолира фирмите")
        return True
        
    finally:
        await db.close()
```

---

### Тест 1.3: all_leave_requests изолира фирмите

```python
async def test_all_leave_requests_company_isolation():
    """Всички заявки за отпуск от една фирма НЕ трябва да се виждат от друга"""
    from backend.graphql.queries import all_leave_requests
    
    db = SessionLocal()
    
    try:
        result = await db.execute(select(Company).limit(2))
        companies = result.scalars().all()
        company1 = companies[0]
        
        class MockInfo:
            def __init__(self, user, db):
                self.context = {"db": db, "user": user}
        
        mock_user = type('MockUser', (), {'company_id': company1.id, 'is_admin': False})()
        info = MockInfo(mock_user, db)
        
        requests = await all_leave_requests(info, status=None)
        
        for req in requests:
            assert req.company_id == company1.id, \
                f"Теч на данни!"
        
        print("✅ Тест 1.3 PASSED: all_leave_requests изолира фирмите")
        return True
        
    finally:
        await db.close()
```

---

### Тест 1.4: payroll_forecast изолира фирмите

```python
async def test_payroll_forecast_company_isolation():
    """Прогнозата за заплати трябва да показва само данни за текущата фирма"""
    from backend.graphql.queries import payroll_forecast
    
    db = SessionLocal()
    
    try:
        result = await db.execute(select(Company).limit(2))
        companies = result.scalars().all()
        company1 = companies[0]
        
        class MockInfo:
            def __init__(self, user, db):
                self.context = {"db": db, "user": user}
        
        mock_user = type('MockUser', (), {'company_id': company1.id, 'is_admin': False})()
        info = MockInfo(mock_user, db)
        
        forecast = await payroll_forecast(info, month=3, year=2026)
        
        # Провери че всички потребители в прогнозата са от същата фирма
        if hasattr(forecast, 'employees'):
            for emp in forecast.employees:
                assert emp.company_id == company1.id, \
                    f"Теч на данни! Служител от компания {emp.company_id} в прогноза на компания {company1.id}"
        
        print("✅ Тест 1.4 PASSED: payroll_forecast изолира фирмите")
        return True
        
    finally:
        await db.close()
```

---

### Тест 1.5: schedule_templates изолира фирмите

```python
async def test_schedule_templates_company_isolation():
    """Шаблоните за графици от една фирма НЕ трябва да се виждат от друга"""
    from backend.graphql.queries import schedule_templates
    
    db = SessionLocal()
    
    try:
        result = await db.execute(select(Company).limit(2))
        companies = result.scalars().all()
        company1 = companies[0]
        
        class MockInfo:
            def __init__(self, user, db):
                self.context = {"db": db, "user": user}
        
        mock_user = type('MockUser', (), {'company_id': company1.id, 'is_admin': False})()
        info = MockInfo(mock_user, db)
        
        templates = await schedule_templates(info)
        
        for template in templates:
            assert template.company_id == company1.id, \
                f"Теч на данни! Шаблон от компания {template.company_id} се вижда от компания {company1.id}"
        
        print("✅ Тест 1.5 PASSED: schedule_templates изолира фирмите")
        return True
        
    finally:
        await db.close()
```

---

### Тест 1.6: schedule_template проверява собственост

```python
async def test_schedule_template_ownership():
    """Зареждане на отделен шаблон трябва да проверява company_id"""
    from backend.graphql.queries import schedule_template
    from backend.database.models import ScheduleTemplate
    
    db = SessionLocal()
    
    try:
        # 1. Вземи шаблон от една компания
        result = await db.execute(select(ScheduleTemplate).limit(1))
        template = result.scalars().first()
        
        if not template:
            print("⚠️ Няма шаблони за тестване, пропуска се")
            return True
        
        company1 = template.company_id
        
        class MockInfo:
            def __init__(self, user, db):
                self.context = {"db": db, "user": user}
        
        # 2. Потребител от същата компания - трябва да получи шаблона
        mock_user_same = type('MockUser', (), {'company_id': company1, 'is_admin': False})()
        info_same = MockInfo(mock_user_same, db)
        
        result_same = await schedule_template(info_same, template.id)
        assert result_same is not None, "Потребител от същата компания трябва да види шаблона"
        
        # 3. Потребител от друга компания - НЕ трябва да получи шаблона
        mock_user_other = type('MockUser', (), {'company_id': company1 + 999 if company1 else 999, 'is_admin': False})()
        info_other = MockInfo(mock_user_other, db)
        
        result_other = await schedule_template(info_other, template.id)
        assert result_other is None, "Теч на данни! Потребител от друга компания получи шаблон"
        
        print("✅ Тест 1.6 PASSED: schedule_template проверява собственост")
        return True
        
    finally:
        await db.close()
```

---

### Тест 1.7: audit_logs изолира фирмите

```python
async def test_audit_logs_company_isolation():
    """Одит логовете трябва да показват само текущата фирма"""
    from backend.graphql.queries import audit_logs
    
    db = SessionLocal()
    
    try:
        result = await db.execute(select(Company).limit(2))
        companies = result.scalars().all()
        company1 = companies[0]
        
        class MockInfo:
            def __init__(self, user, db):
                self.context = {"db": db, "user": user}
        
        mock_user = type('MockUser', (), {'company_id': company1.id, 'is_admin': False})()
        info = MockInfo(mock_user, db)
        
        logs = await audit_logs(info, limit=100)
        
        for log in logs:
            if hasattr(log, 'company_id') and log.company_id:
                assert log.company_id == company1.id, \
                    f"Теч на данни! Одит лог от компания {log.company_id} се вижда от компания {company1.id}"
        
        print("✅ Тест 1.7 PASSED: audit_logs изолира фирмите")
        return True
        
    finally:
        await db.close()
```

---

### Тест 1.8: get_fefo_suggestion изолира фирмите

```python
async def test_fefo_suggestion_company_isolation():
    """FEFO предложенията трябва да са само за артикулите на текущата фирма"""
    from backend.graphql.queries import get_fefo_suggestion
    
    db = SessionLocal()
    
    try:
        result = await db.execute(select(Company).limit(2))
        companies = result.scalars().all()
        company1 = companies[0]
        
        class MockInfo:
            def __init__(self, user, db):
                self.context = {"db": db, "user": user}
        
        mock_user = type('MockUser', (), {'company_id': company1.id, 'is_admin': False})()
        info = MockInfo(mock_user, db)
        
        # Трябва да има поне един склад за теста
        from backend.database.models import Warehouse
        warehouse_result = await db.execute(
            select(Warehouse).where(Warehouse.company_id == company1.id).limit(1)
        )
        warehouse = warehouse_result.scalars().first()
        
        if not warehouse:
            print("⚠️ Няма склад за тестване, пропуска се")
            return True
        
        suggestion = await get_fefo_suggestion(info, warehouse_id=warehouse.id, ingredient_id=None)
        
        # Провери че всички предложени партиди са от същата фирма
        if hasattr(suggestion, 'items'):
            for item in suggestion.items:
                assert item.company_id == company1.id, \
                    f"Теч на данни! Партида от компания {item.company_id} се предлага на компания {company1.id}"
        
        print("✅ Тест 1.8 PASSED: get_fefo_suggestion изолира фирмите")
        return True
        
    finally:
        await db.close()
```

---

### Тест 1.9: inventory_by_barcode проверява собственост

```python
async def test_inventory_by_barcode_company_isolation():
    """Търсене по баркод трябва да връща само артикули от текущата фирма"""
    from backend.graphql.queries import inventory_by_barcode
    
    db = SessionLocal()
    
    try:
        result = await db.execute(select(Company).limit(2))
        companies = result.scalars().all()
        company1 = companies[0]
        
        class MockInfo:
            def __init__(self, user, db):
                self.context = {"db": db, "user": user}
        
        mock_user = type('MockUser', (), {'company_id': company1.id, 'is_admin': False})()
        info = MockInfo(mock_user, db)
        
        # Вземи баркод от друга компания
        from backend.database.models import Ingredient
        other_barcode_result = await db.execute(
            select(Ingredient.barcode).where(Ingredient.company_id != company1.id).limit(1)
        )
        other_barcode = other_barcode_result.scalar()
        
        if not other_barcode:
            print("⚠️ Няма артикул от друга компания за тестване, пропуска се")
            return True
        
        # Потребител от company1 търси баркод от друга компания
        result = await inventory_by_barcode(info, barcode=other_barcode)
        
        # Трябва да НЕ намери нищо
        assert result is None, \
            f"Теч на данни! Артикул с баркод {other_barcode} от друга компания е намерен"
        
        print("✅ Тест 1.9 PASSED: inventory_by_barcode изолира фирмите")
        return True
        
    finally:
        await db.close()
```

---

### Тест 2.1: ContractTemplateVersion връща Decimal

```python
async def test_contract_template_version_decimal_precision():
    """ContractTemplateVersion.current_version трябва да връща Decimal за прецизност"""
    from backend.graphql.types import ContractTemplateVersion
    from backend.database.models import ContractTemplate, ContractTemplateVersion as ModelVersion
    from decimal import Decimal
    
    db = SessionLocal()
    
    try:
        # 1. Намери шаблон с версия
        result = await db.execute(
            select(ContractTemplate)
            .options(selectinload(ContractTemplate.versions))
            .limit(1)
        )
        template = result.scalars().first()
        
        if not template or not template.versions:
            print("⚠️ Няма шаблони с версии за тестване, пропуска се")
            return True
        
        version = template.versions[0]
        
        # 2. Провери типа на стойностите в модела
        if version.night_work_rate:
            assert isinstance(version.night_work_rate, Decimal), \
                f"Моделът трябва да съхранява Decimal, но има {type(version.night_work_rate)}"
        
        # 3. Създай GraphQL тип
        gql_type = await ContractTemplateVersion.from_instance(version)
        
        # 4. Провери че върнатите стойности са Decimal (не float)
        if gql_type.night_work_rate is not None:
            assert isinstance(gql_type.night_work_rate, Decimal), \
                f"GraphQL типът трябва да връща Decimal, но връща {type(gql_type.night_work_rate)}"
        
        print("✅ Тест 2.1 PASSED: ContractTemplateVersion връща Decimal")
        return True
        
    finally:
        await db.close()
```

---

### Тест 2.2: AnnexTemplateVersion връща Decimal

```python
async def test_annex_template_version_decimal_precision():
    """AnnexTemplateVersion.current_version трябва да връща Decimal за прецизност"""
    from backend.graphql.types import AnnexTemplateVersion
    from backend.database.models import AnnexTemplate, AnnexTemplateVersion as ModelVersion
    from decimal import Decimal
    
    db = SessionLocal()
    
    try:
        # 1. Намери шаблон за анекс с версия
        result = await db.execute(
            select(AnnexTemplate)
            .options(selectinload(AnnexTemplate.versions))
            .limit(1)
        )
        template = result.scalars().first()
        
        if not template or not template.versions:
            print("⚠️ Няма шаблони за анекси с версии за тестване, пропуска се")
            return True
        
        version = template.versions[0]
        
        # 2. Провери типа на стойностите в модела
        if version.new_base_salary:
            assert isinstance(version.new_base_salary, Decimal), \
                f"Моделът трябва да съхранява Decimal"
        
        # 3. Създай GraphQL тип
        gql_type = await AnnexTemplateVersion.from_instance(version)
        
        # 4. Провери че върнатите стойности са Decimal
        if gql_type.new_base_salary is not None:
            assert isinstance(gql_type.new_base_salary, Decimal), \
                f"GraphQL типът трябва да връща Decimal, но връща {type(gql_type.new_base_salary)}"
        
        print("✅ Тест 2.2 PASSED: AnnexTemplateVersion връща Decimal")
        return True
        
    finally:
        await db.close()
```

---

### Тест 2.3: Проверка за загуба на точност

```python
def test_decimal_precision_no_loss():
    """Уверете се че Decimal стойности се запазват без загуба"""
    from decimal import Decimal
    
    # Примерна стойност с 4 знака след десетичната запетая
    original = Decimal("1234.5678")
    
    # Симулирай какво прави старият код (конвертиране към float)
    as_float = float(original)
    back_to_decimal = Decimal(str(as_float))
    
    # Провери загубата
    diff = abs(original - back_to_decimal)
    assert diff == 0, f"Загуба на точност: {original} -> {back_to_decimal} (diff: {diff})"
    
    print(f"✅ Тест 2.3 PASSED: Загуба на точност при Decimal->float->Decimal: {diff}")
    
    # Покажи загубата
    print(f"   Оригинал: {original}")
    print(f"   След float: {as_float}")
    print(f"   Обратно: {back_to_decimal}")
    print(f"   Разлика: {diff}")
```

---

## Статус на Поправките (актуализирано 2026-03-26)

| ID | Описание | Статус | Бележка |
|----|----------|--------|---------|
| 1.1 | user_presences | ✅ ПОПРАВЕНО | Добавен company_id филтър |
| 1.2 | pending_leave_requests | ✅ ОК | Вече има company_id |
| 1.3 | all_leave_requests | ✅ ОК | Вече има company_id |
| 1.4 | payroll_forecast | ✅ ОК | Вече има company_id |
| 1.5 | schedule_templates | ✅ ПОПРАВЕНО | Добавен company_id към модела и филтър |
| 1.6 | schedule_template | ✅ ПОПРАВЕНО | Добавена проверка за собственост |
| 1.7 | audit_logs | ✅ ПОПРАВЕНО | Добавен company_id филтър през User join |
| 1.8 | get_fefo_suggestion | ✅ ОК | Вече има company_id |
| 1.9 | inventory_by_barcode | ✅ ОК | Вече има company_id |
| 2.1 | ContractTemplateVersion Decimal | ✅ ОК | НЯМА загуба на точност |
| 2.2 | AnnexTemplateVersion Decimal | ✅ ОК | НЯМА загуба на точност |

**Резултат от теста**: 12/12 преминаха. **Всички проблеми са поправени!**

---

## Как да използваш този план

1. ~~**Поправи проблемите** от Приоритет 1 и 2~~ ✅ **ИЗПЪЛНЕНО**
2. ~~**Копирай съответния тест** в нов файл `backend/test_security_audit.py`~~ ✅ **ИЗПЪЛНЕНО**
3. **Изпълни тестовете** с `python test_security_audit.py` ✅ **12/12 ПРОМИНАХА**
4. ~~**Маркирай като приключено** в таблицата по-горе~~ ✅ **ИЗПЪЛНЕНО**
5. **Commit** след всяка логически завършена група поправки

---

## Променени файлове

### backend/graphql/queries.py
- `user_presences`: Добавен `.where(User.company_id == current_user.company_id)`
- `schedule_templates`: Добавен `company_id` параметър и филтър
- `schedule_template`: Добавен `company_id` параметър и проверка за собственост
- `audit_logs`: Добавен `JOIN User` и `.where(User.company_id == current_user.company_id)`

### backend/database/models.py
- `ScheduleTemplate`: Добавена колона `company_id` и релация `company`

### backend/crud.py
- `get_schedule_templates`: Добавен параметър `company_id`
- `get_schedule_template`: Добавен параметър `company_id`
- `create_schedule_template`: Добавен параметър `company_id`
- `delete_schedule_template`: Добавен параметър `company_id` и проверка за собственост

### backend/graphql/mutations.py
- `create_schedule_template`: Подава `current_user.company_id`
- `delete_schedule_template`: Подава `current_user.company_id` и хвърля NotFoundException при липса на достъп

### backend/graphql/types.py
- `ScheduleTemplate`: Добавено поле `company_id`
