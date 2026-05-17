# Shift & Schedule System - Refactoring Plan

## Текущо състояние

| Компонент | Статус | Бележки |
|-----------|--------|---------|
| Shift Model | ⚠️ | Няма company_id, create_shift игнорира параметри |
| WorkSchedule Model | ⚠️ | Няма unique constraint, N+1 query при shift resolver |
| ScheduleTemplate | ⚠️ | Input mismatch, няма update mutation, няма preview |
| ScheduleTemplateService | ❌ | Дублира time_repo, не се използва |
| Audit Logging | ❌ | Липсва напълно |

---

## Фаза 1: Критични фиксове (1-2 часа)

### 1.1 Fix `create_shift` mutation параметри

**Файлове:**
- `backend/graphql/mutations.py` → `create_shift` mutation (ред ~1197)
- `backend/graphql/inputs.py` → `ShiftInput` (ако съществува)

**Промени:**

```python
# СЕГА (mutations.py):
@strawberry.mutation
async def create_shift(
    self,
    name: str,
    start_time: datetime.time,
    end_time: datetime.time,
    info: strawberry.types.Info,
) -> ShiftType:
    ...
    shift = await time_repo.create_shift(
        name=name,
        start_time=start_time,
        end_time=end_time,
    )

# ТРЯБВА ДА СТАНЕ:
@strawberry.mutation
async def create_shift(
    self,
    name: str,
    start_time: datetime.time,
    end_time: datetime.time,
    tolerance_minutes: int = 15,
    break_duration_minutes: int = 0,
    pay_multiplier: float = 1.0,
    shift_type: str = "regular",
    info: strawberry.types.Info,
) -> ShiftType:
    ...
    shift = await time_repo.create_shift(
        name=name,
        start_time=start_time,
        end_time=end_time,
        tolerance_minutes=tolerance_minutes,
        break_duration_minutes=break_duration_minutes,
        pay_multiplier=pay_multiplier,
        shift_type=shift_type,
    )
```

**Тест:** Създай смяна с custom tolerance/break/pay_multiplier → провери в DB че стойностите са запазени.

---

### 1.2 Добави company изолация на Shift

**Файлове:**
- `backend/database/models.py` → `Shift` модел (ред ~563)
- `backend/crud/repositories/time_repo.py` → `get_all_shifts()`, `create_shift()`
- `backend/graphql/queries.py` → `shifts` query

**Стъпка A: Добави company_id в Shift модел**

```python
# models.py:
class Shift(Base):
    __tablename__ = "shifts"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True, index=True)
    company_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("companies.id"), nullable=True, index=True
    )
    start_time: Mapped[datetime.time]
    end_time: Mapped[datetime.time]
    tolerance_minutes: Mapped[int] = mapped_column(default=15)
    break_duration_minutes: Mapped[int] = mapped_column(default=0)
    pay_multiplier: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=1.0)
    shift_type: Mapped[str] = mapped_column(default="regular")

    company: Mapped[Optional["Company"]] = relationship("Company", back_populates="shifts")
```

**Стъпка B: Alembic миграция**

```bash
cd backend && alembic revision -m "add_company_id_to_shifts"
```

```python
# migration file:
def upgrade():
    op.add_column("shifts", sa.Column("company_id", sa.Integer(), nullable=True))
    op.create_index("ix_shifts_company_id", "shifts", ["company_id"])
    op.create_foreign_key("fk_shifts_company", "shifts", "companies", ["company_id"], ["id"])

    # Assign existing shifts to first company (or default)
    op.execute("""
        UPDATE shifts SET company_id = (SELECT id FROM companies LIMIT 1)
        WHERE company_id IS NULL
    """)

def downgrade():
    op.drop_constraint("fk_shifts_company", "shifts", type_="foreignkey")
    op.drop_index("ix_shifts_company_id", "shifts")
    op.drop_column("shifts", "company_id")
```

**Стъпка C: Филтриране в repository**

```python
# time_repo.py:
async def get_all_shifts(self, company_id: Optional[int] = None) -> List[Shift]:
    stmt = select(Shift)
    if company_id:
        stmt = stmt.where(Shift.company_id == company_id)
    result = await self.db.execute(stmt)
    return list(result.scalars().all())
```

**Стъпка D: GraphQL query update**

```python
# queries.py:
@strawberry.field
async def shifts(self, info: strawberry.types.Info) -> List[ShiftType]:
    time_repo = TimeRepository(info.context["db_session"])
    user = info.context.get("current_user")
    company_id = user.company_id if user and not user.is_super_admin else None
    return await time_repo.get_all_shifts(company_id=company_id)
```

---

### 1.3 Добави DB unique constraint на WorkSchedule

**Файлове:**
- `backend/database/models.py` → `WorkSchedule` модел (ред ~578)
- `backend/crud/repositories/time_repo.py` → `create_or_update_schedule()`

**Стъпка A: Добави UniqueConstraint**

```python
# models.py:
class WorkSchedule(Base):
    __tablename__ = "work_schedules"
    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uq_user_date_schedule"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime.date] = mapped_column(index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    shift_id: Mapped[Optional[int]] = mapped_column(ForeignKey("shifts.id"))
```

**Стъпка B: Alembic миграция**

```bash
cd backend && alembic revision -m "add_unique_constraint_work_schedules"
```

```python
def upgrade():
    # First remove duplicates (keep latest by id)
    op.execute("""
        DELETE FROM work_schedules
        WHERE id NOT IN (
            SELECT MAX(id) FROM work_schedules
            GROUP BY user_id, date
        )
    """)
    op.create_unique_constraint("uq_user_date_schedule", "work_schedules", ["user_id", "date"])

def downgrade():
    op.drop_constraint("uq_user_date_schedule", "work_schedules", type_="unique")
```

**Стъпка C: Конвертирай create_or_update_schedule да ползва ON CONFLICT**

```python
# time_repo.py:
async def create_or_update_schedule(
    self, user_id: int, shift_id: Optional[int], date: datetime.date
) -> WorkSchedule:
    from sqlalchemy.dialects.postgresql import insert

    stmt = insert(WorkSchedule).values(
        user_id=user_id,
        date=date,
        shift_id=shift_id,
    )
    stmt = stmt.on_conflict_do_update(
        constraint="uq_user_date_schedule",
        set_={"shift_id": stmt.excluded.shift_id},
    )
    stmt = stmt.returning(WorkSchedule)
    result = await self.db.execute(stmt)
    await self.db.flush()
    return result.scalar_one()
```

---

### 1.4 Fix ScheduleTemplateItemInput

**Файлове:**
- `backend/graphql/inputs.py` → `ScheduleTemplateItemInput`
- `backend/graphql/mutations.py` → `create_schedule_template`, `apply_schedule_template`

**Стъпка A: Дефинирай нов Input**

```python
# inputs.py:
@strawberry.input
class ScheduleTemplateItemInput:
    day_index: int
    shift_id: Optional[int] = None  # None = day off
```

**Стъпка B: Fix mutation да ползва новите полета**

```python
# mutations.py:
@strawberry.mutation
async def create_schedule_template(
    self,
    name: str,
    items: List[ScheduleTemplateItemInput],
    description: Optional[str] = None,
    info: strawberry.types.Info,
) -> ScheduleTemplateType:
    time_repo = TimeRepository(info.context["db_session"])
    user = info.context.get("current_user")

    template = await time_repo.create_schedule_template(
        company_id=user.company_id,
        name=name,
        description=description,
        items=[
            {"day_index": item.day_index, "shift_id": item.shift_id}
            for item in items
        ],
    )
    return ScheduleTemplateType.from_instance(template)
```

---

## Фаза 2: Валидации и UX (2-3 часа)

### 2.1 Валидация на shift времена

**Файлове:**
- `backend/crud/repositories/time_repo.py` → `create_shift()`, `update_shift()`

```python
# time_repo.py:
async def create_shift(
    self,
    name: str,
    start_time: datetime.time,
    end_time: datetime.time,
    tolerance_minutes: int = 15,
    break_duration_minutes: int = 0,
    pay_multiplier: float = 1.0,
    shift_type: str = "regular",
    company_id: Optional[int] = None,
    overnight: bool = False,
) -> Shift:
    # Validate times
    if not overnight and end_time <= start_time:
        raise ValueError("end_time must be after start_time (or set overnight=True)")
    if overnight and end_time >= start_time:
        raise ValueError("overnight shifts require end_time < start_time")

    shift = Shift(
        name=name,
        start_time=start_time,
        end_time=end_time,
        tolerance_minutes=tolerance_minutes,
        break_duration_minutes=break_duration_minutes,
        pay_multiplier=pay_multiplier,
        shift_type=shift_type,
        company_id=company_id,
    )
    self.db.add(shift)
    await self.db.flush()
    await self.db.refresh(shift)
    return shift
```

**Добави overnight поле в модела:**

```python
# models.py:
class Shift(Base):
    ...
    overnight: Mapped[bool] = mapped_column(default=False)
```

**Добави overnight параметър на mutation:**

```python
# mutations.py:
async def create_shift(
    ...
    overnight: bool = False,
) -> ShiftType:
```

---

### 2.2 update_schedule_template mutation

**Файлове:**
- `backend/graphql/mutations.py` → нова mutation
- `backend/crud/repositories/time_repo.py` → нов метод

**Repository:**

```python
# time_repo.py:
async def update_schedule_template(
    self,
    template_id: int,
    company_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    items: Optional[List[dict]] = None,
) -> ScheduleTemplate:
    stmt = select(ScheduleTemplate).where(
        ScheduleTemplate.id == template_id,
        ScheduleTemplate.company_id == company_id,
    )
    result = await self.db.execute(stmt)
    template = result.scalar_one_or_none()
    if not template:
        raise ValueError("Template not found")

    if name is not None:
        template.name = name
    if description is not None:
        template.description = description

    if items is not None:
        # Delete old items
        delete_stmt = delete(ScheduleTemplateItem).where(
            ScheduleTemplateItem.template_id == template_id
        )
        await self.db.execute(delete_stmt)

        # Create new items
        for item_data in items:
            item = ScheduleTemplateItem(
                template_id=template_id,
                day_index=item_data["day_index"],
                shift_id=item_data.get("shift_id"),
            )
            self.db.add(item)

    await self.db.commit()
    await self.db.refresh(template)
    return template
```

**Mutation:**

```python
# mutations.py:
@strawberry.mutation
async def update_schedule_template(
    self,
    id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    items: Optional[List[ScheduleTemplateItemInput]] = None,
    info: strawberry.types.Info,
) -> ScheduleTemplateType:
    time_repo = TimeRepository(info.context["db_session"])
    user = info.context.get("current_user")

    template_items = None
    if items is not None:
        template_items = [
            {"day_index": item.day_index, "shift_id": item.shift_id}
            for item in items
        ]

    template = await time_repo.update_schedule_template(
        template_id=id,
        company_id=user.company_id,
        name=name,
        description=description,
        items=template_items,
    )
    return ScheduleTemplateType.from_instance(template)
```

---

### 2.3 Bulk delete графици

**Файлове:**
- `backend/graphql/mutations.py` → нова mutation
- `backend/crud/repositories/time_repo.py` → нов метод

**Repository:**

```python
# time_repo.py:
async def bulk_delete_schedules(
    self,
    user_ids: List[int],
    start_date: datetime.date,
    end_date: datetime.date,
) -> int:
    stmt = delete(WorkSchedule).where(
        WorkSchedule.user_id.in_(user_ids),
        WorkSchedule.date >= start_date,
        WorkSchedule.date <= end_date,
    )
    result = await self.db.execute(stmt)
    await self.db.commit()
    return result.rowcount
```

**Mutation:**

```python
# mutations.py:
@strawberry.mutation
async def bulk_delete_schedules(
    self,
    user_ids: List[int],
    start_date: datetime.date,
    end_date: datetime.date,
    info: strawberry.types.Info,
) -> int:
    time_repo = TimeRepository(info.context["db_session"])
    return await time_repo.bulk_delete_schedules(
        user_ids=user_ids,
        start_date=start_date,
        end_date=end_date,
    )
```

---

### 2.4 Template preview

**Файлове:**
- `backend/graphql/queries.py` → нов query
- `backend/crud/repositories/time_repo.py` → `get_template_preview()` (вече съществува в service)
- `frontend/src/components/ScheduleTemplatesManager.tsx` → UI

**Repository (премести от service):**

```python
# time_repo.py:
async def get_template_preview(
    self,
    template_id: int,
    start_date: datetime.date,
    end_date: datetime.date,
) -> List[dict]:
    """Returns preview of what applying a template would create."""
    stmt = select(ScheduleTemplate).options(
        selectinload(ScheduleTemplate.items).selectinload(ScheduleTemplateItem.shift)
    ).where(ScheduleTemplate.id == template_id)
    result = await self.db.execute(stmt)
    template = result.scalar_one_or_none()
    if not template:
        return []

    items = sorted(template.items, key=lambda x: x.day_index)
    if not items:
        return []

    preview = []
    days_processed = 0
    current_date = start_date

    while current_date <= end_date:
        item = items[days_processed % len(items)]
        preview.append({
            "date": current_date,
            "shift_id": item.shift_id,
            "shift_name": item.shift.name if item.shift else "Почивен ден",
            "day_index": days_processed % len(items),
        })
        days_processed += 1
        current_date += datetime.timedelta(days=1)

    return preview
```

**Query:**

```python
# queries.py:
@strawberry.type
class TemplatePreviewItem:
    date: datetime.date
    shift_id: Optional[int]
    shift_name: str
    day_index: int

@strawberry.field
async def template_preview(
    self,
    template_id: int,
    start_date: datetime.date,
    end_date: datetime.date,
    info: strawberry.types.Info,
) -> List[TemplatePreviewItem]:
    time_repo = TimeRepository(info.context["db_session"])
    preview = await time_repo.get_template_preview(
        template_id=template_id,
        start_date=start_date,
        end_date=end_date,
    )
    return [TemplatePreviewItem(**item) for item in preview]
```

---

## Фаза 3: Performance и Quality (2-3 часа)

### 3.1 Dataloader за WorkSchedule.shift

**Файлове:**
- `backend/graphql/dataloaders.py` → нов loader
- `backend/graphql/types.py` → `WorkSchedule.shift` resolver

**Dataloader:**

```python
# dataloaders.py:
from aiodataloader import DataLoader

class ShiftLoader(DataLoader):
    async def batch_load_fn(self, shift_ids):
        from backend.database.models import Shift
        from sqlalchemy import select

        stmt = select(Shift).where(Shift.id.in_(shift_ids))
        result = await self.db.execute(stmt)
        shifts = {s.id: s for s in result.scalars().all()}
        return [shifts.get(sid) for sid in shift_ids]
```

**Types update:**

```python
# types.py:
@strawberry.type
class WorkSchedule:
    ...
    @strawberry.field
    async def shift(self, info: strawberry.types.Info) -> Optional[ShiftType]:
        if not self.shift_id:
            return None
        loader = info.context["shift_loader"]
        shift = await loader.load(self.shift_id)
        return ShiftType.from_instance(shift) if shift else None
```

**Context setup (в main.py или graphql router):**

```python
# Add to request context:
context["shift_loader"] = ShiftLoader()
```

---

### 3.2 Audit logging

**Файлове:**
- `backend/database/models.py` → нов модел
- `backend/crud/repositories/time_repo.py` → логване в create/update/delete

**Модел:**

```python
# models.py:
class ScheduleAuditLog(Base):
    __tablename__ = "schedule_audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    action: Mapped[str]  # 'create', 'update', 'delete', 'bulk_create', 'bulk_delete'
    schedule_id: Mapped[Optional[int]]
    old_value: Mapped[Optional[dict]] = mapped_column(JSON)
    new_value: Mapped[Optional[dict]] = mapped_column(JSON)
    timestamp: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    user: Mapped["User"] = relationship("User")
```

**Alembic миграция:**

```bash
cd backend && alembic revision -m "add_schedule_audit_log"
```

**Логване в repository:**

```python
# time_repo.py:
async def _log_schedule_action(
    self,
    user_id: int,
    action: str,
    schedule_id: Optional[int] = None,
    old_value: Optional[dict] = None,
    new_value: Optional[dict] = None,
):
    log = ScheduleAuditLog(
        user_id=user_id,
        action=action,
        schedule_id=schedule_id,
        old_value=old_value,
        new_value=new_value,
    )
    self.db.add(log)

# Пример в create_or_update_schedule:
async def create_or_update_schedule(self, user_id, shift_id, date):
    existing = await self.get_schedule_for_date(user_id, date)
    old_value = {"shift_id": existing.shift_id} if existing else None

    schedule = await self._upsert_schedule(user_id, shift_id, date)

    await self._log_schedule_action(
        user_id=user_id,
        action="update" if existing else "create",
        schedule_id=schedule.id,
        old_value=old_value,
        new_value={"shift_id": shift_id, "date": str(date)},
    )
    return schedule
```

---

### 3.3 Премахни ScheduleTemplateService

**Файлове:**
- `backend/services/schedule_template_service.py` → ИЗТРИЙ
- Провери дали някой го импортира:

```bash
grep -r "schedule_template_service" backend/
```

Ако има импорти, замени ги с `time_repo` еквиваленти:

| Service метод | time_repo еквивалент |
|---------------|---------------------|
| `create_template()` | `create_schedule_template()` |
| `get_templates()` | `get_schedule_templates()` |
| `get_template()` | `get_schedule_template()` |
| `delete_template()` | `delete_schedule_template()` |
| `apply_template()` | `apply_schedule_template()` |
| `get_template_preview()` | `get_template_preview()` (нови) |

---

## Миграции - ред на изпълнение

1. `add_company_id_to_shifts`
2. `add_unique_constraint_work_schedules`
3. `add_overnight_to_shifts`
4. `add_schedule_audit_log`

```bash
cd backend
alembic revision -m "add_company_id_to_shifts"
alembic revision -m "add_unique_constraint_work_schedules"
alembic revision -m "add_overnight_to_shifts"
alembic revision -m "add_schedule_audit_log"
alembic upgrade head
```

---

## Frontend промени

| Файл | Промяна |
|------|---------|
| `frontend/src/pages/SchedulesPage.tsx` | Добави overnight toggle, fix CREATE_SHIFT mutation params |
| `frontend/src/components/ScheduleTemplatesManager.tsx` | Добави edit template dialog, preview dialog |
| `frontend/src/graphql/` | Добави `UPDATE_TEMPLATE_MUTATION`, `BULK_DELETE_MUTATION`, `TEMPLATE_PREVIEW_QUERY` |

---

## Тест план

| Тест | Описание | Очакван резултат |
|------|----------|------------------|
| 1.1 | Създай смяна с custom tolerance/break/pay | Стойностите са запазени в DB |
| 1.2 | Виж смени от компания A | Само смени на компания A |
| 1.3 | Опитай дублиран график за user+date | DB връща conflict, mutation handle-ва |
| 1.4 | Създай template с day_index/shift_id | Template се създава коректно |
| 2.1 | Създай смяна end < start без overnight | Грешка |
| 2.1b | Създай смяна end < start с overnight=True | Успех |
| 2.2 | Редактирай template име + items | Промените са запазени |
| 2.3 | Bulk delete графици за 5 users, 7 дни | Всички са изтрити, върнат count |
| 2.4 | Template preview за 30 дни | 30 items с правилни ротации |
| 3.1 | Load 100 schedules with shifts | 1 query за shifts (не 100) |
| 3.2 | Създай/обнови/изтрий график | Audit log записан |
