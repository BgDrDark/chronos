# 📦 ПЪЛЕН ПЛАН: ПОДОБРЕНИЕ НА СКЛАДА И СТОКОВ ПОТОК

**Версия:** 1.0  
**Дата:** 21.03.2026  
**Статус:** Планиране завършено

---

## 1. АНАЛИЗ НА СЪЩЕСТВУВАЩИЯ СТОКОВ ПОТОК

### 1.1 Съществуваща архитектура

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         СЪЩЕСТВУВАЩ СТОКОВ ПОТОК                         │
└─────────────────────────────────────────────────────────────────────────────┘

    ═══════════════════════════════════════════════════════════════════════════
    ║                        ПРИЕМ НА СТОКА                                  ║
    ═══════════════════════════════════════════════════════════════════════════

    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
    │  Доставка   │────▶│  Партида    │────▶│  Фактура   │
    │  от достав.│     │  (Batch)   │     │ (Invoice)  │
    └─────────────┘     └─────────────┘     └─────────────┘
           │                   │                   │
           │                   │                   │
           ▼                   ▼                   ▼
    bulk_add_batches      quantity↑          InvoiceItem
    или REST /receipt   expiry_date      свързва партида

    ────────────────────────────────────────────────────────────────────────
    Код: mutations.py:3309-3410 (bulk_add_batches)
    Код: warehouse.py:49-118 (REST endpoint)
    ────────────────────────────────────────────────────────────────────────

    ═══════════════════════════════════════════════════════════════════════════
    ║                    ИЗРАЗХОДВАНЕ (FEFO)                              ║
    ═══════════════════════════════════════════════════════════════════════════

    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
    │ Произв.     │────▶│ Задача      │────▶│ FEFO       │
    │ наред       │     │ завършена   │     │ Изразход.  │
    └─────────────┘     └─────────────┘     └─────────────┘
                               │                   │
                               │                   │ 自动
                               ▼                   ▼
                    При всички задачи      Най-старият
                    завършени             срок годност

    ────────────────────────────────────────────────────────────────────────
    Код: mutations.py:2702-2727 (FEFO логика)
    Формула: current_stock = SUM(batch.quantity) WHERE status="active"
    ────────────────────────────────────────────────────────────────────────

    ═══════════════════════════════════════════════════════════════════════════
    ║                    КОРЕКЦИЯ НА СТОКА                                 ║
    ═══════════════════════════════════════════════════════════════════════════

    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
    │ Инвентари- │────▶│ Броене      │────▶│ Протокол   │
    │ зация      │     │ ( намерено) │     │ (Протокол) │
    └─────────────┘     └─────────────┘     └─────────────┘
                                              │         │
                                              │         │
                            ┌─────────────────┘         └─────────────────┐
                            │ diff > 0                                  │ diff < 0
                            ▼                                           ▼
                    ┌───────────────┐                           ┌───────────────┐
                    │ Нова партида  │                           │ FEFO          │
                    │ (+)          │                           │ намаление (-) │
                    └───────────────┘                           └───────────────┘

    ────────────────────────────────────────────────────────────────────────
    Код: mutations.py:2847-2893 (корекция)
    ────────────────────────────────────────────────────────────────────────
```

### 1.2 Съществуващи модели в базата данни

| Модел | Таблица | Ключови полета | Описание |
|-------|---------|----------------|----------|
| **Ingredient** | `ingredients` | name, unit, current_price, min_quantity | Артикули |
| **Batch** | `batches` | quantity, expiry_date, status, supplier_id | Партиди |
| **StorageZone** | `storage_zones` | name, temp_min, temp_max | Зони за съхранение |
| **Supplier** | `suppliers` | name, eik, vat_number | Доставчици |
| **InventorySession** | `inventory_sessions` | status, protocol_number | Инвентаризации |
| **InventoryItem** | `inventory_items` | found_quantity, system_quantity, difference | Артикули в инвентаризация |

### 1.3 Статуси на партиди

```
┌──────────┐     ┌──────────────┐     ┌──────────┐     ┌───────────┐
│  active  │────▶│ quarantined  │────▶│ expired  │────▶│ depleted  │
└──────────┘     └──────────────┘     └──────────┘     └───────────┘
      │                  │                                     │
      │                  │                                     │
      ▼                  ▼                                     ▼
┌──────────┐     ┌──────────┐                           ┌──────────┐
│ (usable) │     │  scrap  │                           │  (zero) │
└──────────┘     └──────────┘                           └──────────┘
```

---

## 2. ИДЕНТИФИЦИРАНИ ПРОБЛЕМИ

### 2.1 Проблеми в стоковия поток

| # | Проблем | Тежест | Описание |
|---|---------|--------|----------|
| P1 | **Няма ръчно изразходване** | 🔴 Критичен | Не може да се изразходва стока без производствена поръчка |
| P2 | **Няма проследяване на консумацията** | 🔴 Критичен | Липсва лог "какво е изразходвано от коя партида" |
| P3 | **Няма частично изразходване от партида** | 🔴 Критичен | Не може да се ползва част от партида |
| P4 | **Няма трансфер между зони** | 🟡 Среден | Не може да се прехвърля стока между складови зони |
| P5 | **Няма причина за корекция** | 🟡 Среден | Инвентаризацията не изисква обяснение за разлики |
| P6 | **Няма одобрение за корекции** | 🟡 Среден | Големи разлики не се одобряват |
| P7 | **Няма предупреждения за изтичане** | 🟢 Нисък | Няма имейл/SMS за партиди < 30 дни |
| P8 | **Няма история на партида** | 🟡 Среден | Не може да се види какво се е случило с партида |

### 2.2 Проблеми с качеството

| # | Проблем | Тежест | Описание |
|---|---------|--------|----------|
| Q1 | **Няма карантинна система** | 🟡 Среден | Не може да се маркира партида като "подозрителна" |
| Q2 | **Няма автоматично маркиране като изтекла** | 🟡 Среден | Изтеклите партиди не се маркират автоматично |
| Q3 | **Няма проследяване на доставчик** | 🟢 Нисък | Не се вижда лесно качеството по доставчик |

### 2.3 Проблеми с данните

| # | Проблем | Тежест | Описание |
|---|---------|--------|----------|
| D1 | **Няма валидация на температура** | 🟢 Нисък | Не се проверява дали партида е в правилната зона |
| D2 | **Няма стойностен отчет** | 🟡 Среден | Не може да се види стойността на стоката |
| D3 | **Няма ABC анализ** | 🟢 Нисък | Не се знае кое е най-важно |

---

## 3. ПРЕДХОДНИ ПОДОБРЕНИЯ (ВЕЧЕ ИМПЛЕМЕНТИРАНИ)

### 3.1 Интеграция с фактури (Фаза 2.1)
```
✅ batchId селектор при създаване на входящи фактури
✅ Показване на наличност и срок годност
✅ Линк между InvoiceItem и Batch
```

### 3.2 Accounting Entries (Счетоводни записи)
```
✅ Автоматични счетоводни записи при създаване/редактиране на фактури
✅ UI за счетоводни записи
✅ Филтриране по дата, сметка
```

### 3.3 Company Accounting Settings
```
✅ Подразбиращи се сметки за фирмата
✅ UI за настройка на сметки
✅ Свързване с Accounting Service
```

### 3.4 Bank Reconciliation
```
✅ Ръчно съпоставяне на банкови транзакции с фактури
✅ Автоматично съпоставяне по сума
✅ UI за съпоставяне
```

---

## 4. ЛИПСВАЩИ ФУНКЦИОНАЛНОСТИ

### 4.1 Стокови операции

| # | Функционалност | Описание | Приоритет |
|---|----------------|----------|-----------|
| F1 | **Ръчно изразходване** | Намаляване на партида без производство | 🔴 Критичен |
| F2 | **FEFO изразходване** | Автоматичен подбор на партиди по срок | 🔴 Критичен |
| F3 | **История на консумацията** | Лог на всички изразходвания | 🔴 Критичен |
| F4 | **Трансфер между зони** | Преместване на стока между зони | 🟡 Среден |
| F5 | **Разделяне на партида** | Създаване на нова партида от съществуваща | 🟡 Среден |

### 4.2 Качество

| # | Функционалност | Описание | Приоритет |
|---|----------------|----------|-----------|
| F6 | **Карантина** | Маркиране на партида като подозрителна | 🟡 Среден |
| F7 | **Автоматично маркиране** | Изтекли партиди → status="expired" | 🟡 Среден |
| F8 | **Предупреждения за изтичане** | Имейл/SMS за партиди < 7 дни | 🟢 Нисък |

### 4.3 Инвентаризация

| # | Функционалност | Описание | Приоритет |
|---|----------------|----------|-----------|
| F9 | **Причина за корекция** | Задължително поле при разлика | 🟡 Среден |
| F10 | **Одобрение за корекции** | При > 10% разлика | 🟡 Среден |
| F11 | **Протокол PDF** | Експорт на инвентарен протокол | 🟢 Нисък |

### 4.4 Анализи

| # | Функционалност | Описание | Приоритет |
|---|----------------|----------|-----------|
| F12 | **Стойностен отчет** | Стойност на стоката по артикули | 🟡 Среден |
| F13 | **Движение на стока** | Приход/разход за период | 🟡 Среден |
| F14 | **ABC анализ** | Класификация A/B/C | 🟢 Нисък |

---

## 5. ПЛАН ЗА ИМПЛЕМЕНТАЦИЯ

### ФАЗА 1: РЪЧНО ИЗРАЗХОДВАНЕ 🔴🔴🔴

#### 5.1 Нов модел: `StockConsumptionLog`

**Файл:** `backend/database/models.py`

```python
class StockConsumptionLog(Base):
    """Лог за изразходване на стока"""
    __tablename__ = "stock_consumption_logs"
    
    id = Column(Integer, primary_key=True)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), nullable=False)
    batch_id = Column(Integer, ForeignKey("batches.id"), nullable=False)
    quantity = Column(Numeric(12, 3), nullable=False)
    reason = Column(String(50), nullable=False)  # "manual", "production", "expiry", "damaged", "quality_check"
    production_order_id = Column(Integer, ForeignKey("production_orders.id"), nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    ingredient = relationship("Ingredient")
    batch = relationship("Batch")
    production_order = relationship("ProductionOrder")
    creator = relationship("User")
```

#### 5.2 GraphQL Mutations

**Файл:** `backend/graphql/mutations.py`

```python
@strawberry.mutation
async def consume_from_batch(
    self,
    batch_id: int,
    quantity: Decimal,
    reason: str,
    notes: Optional[str] = None,
    info: strawberry.Info
) -> types.Batch:
    """Ръчно изразходване от партида"""
    # 1. Валидация
    # 2. Намали партидата
    # 3. Създай лог
    # 4. Върни партида

@strawberry.mutation
async def auto_consume_fefo(
    self,
    ingredient_id: int,
    quantity: Decimal,
    reason: str,
    notes: Optional[str] = None,
    info: strawberry.Info
) -> List[types.StockConsumptionLog]:
    """Автоматично FEFO изразходване"""

@strawberry.mutation
async def get_fefo_suggestion(
    self,
    ingredient_id: int,
    quantity: Decimal,
    info: strawberry.Info
) -> List[types.FefoSuggestion]:
    """Предложение за FEFO изразходване"""
```

#### 5.3 GraphQL Types

**Файл:** `backend/graphql/types.py`

```python
@strawberry.type
class StockConsumptionLog:
    id: int
    ingredient_id: int
    batch_id: int
    quantity: Decimal
    reason: str
    notes: Optional[str]
    created_at: datetime.datetime
    
    @strawberry.field
    async def ingredient(self, info) -> Ingredient: ...
    
    @strawberry.field
    async def batch(self, info) -> Batch: ...
    
    @strawberry.field
    async def creator(self, info) -> User: ...

@strawberry.type
class FefoSuggestion:
    batch_id: int
    batch_number: str
    available_quantity: Decimal
    quantity_to_take: Decimal
    expiry_date: datetime.date
    days_until_expiry: int
```

#### 5.4 GraphQL Queries

**Файл:** `backend/graphql/queries.py`

```python
@strawberry.field
async def stock_consumption_logs(
    self,
    info: strawberry.Info,
    ingredient_id: Optional[int] = None,
    batch_id: Optional[int] = None,
    start_date: Optional[datetime.date] = None,
    end_date: Optional[datetime.date] = None
) -> List[types.StockConsumptionLog]:
    """История на консумацията"""

@strawberry.field
async def batch_history(
    self,
    info: strawberry.Info,
    batch_id: int
) -> List[types.BatchHistoryEntry]:
    """Пълна история на партида"""
```

#### 5.5 Frontend

**Нов таб: "Ръчно изразходване"**

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Ръчно Изразходване                                        [+] Нова    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Артикул:  [▼ Брашно тип 500                              ]              │
│                                                                         │
│  Количество: [________________________] кг                              │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │ Партиди (FEFO подреждане - най-стар срок първо):                │  │
│  │                                                                  │  │
│  │  ☑ #2026-03-15-001  │  50.000 кг │ до 15.06.2026 │ 5 дни     │  │
│  │  ☐ #2026-03-10-002  │  30.000 кг │ до 01.07.2026 │ 21 дни    │  │
│  │  ☐ #2026-03-01-003  │  25.000 кг │ до 10.07.2026 │ 30 дни    │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  Избрана партида: #2026-03-15-001 (50.000 кг)                        │
│                                                                         │
│  Причина: [▼ Ръчно / Изтекло / Повредено / Качествена проверка    ]   │
│                                                                         │
│  Бележки: [                                                     ]       │
│                                                                         │
│                                        [Изразходвай]                   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### ФАЗА 2: ПРОСЛЕДЯВАНЕ НА КОНСУМАЦИЯТА 🟢

#### 5.6 Логове за всички операции

```python
# При производство - ProductionRecordIngredient (съществуващ)
# При ръчно изразходване - StockConsumptionLog (нов)
# При инвентаризация - InventoryItem (съществуващ)
# При scrap - ProductionScrapLog (съществуващ)
```

#### 5.7 История на партида

**Frontend диалог:**

```
┌─────────────────────────────────────────────────────────────────────────┐
│  #BTH-2026-0015                                         [✕]            │
├─────────────────────────────────────────────────────────────────────────┤
│  Артикул: Брашно тип 500                                             │
│  Партида: 2026-03-15-001                                            │
│  Количество: 50.000 кг                                               │
│  Срок годност: 15.06.2026 (5 дни)                                   │
│  Статус: 🟢 Активна                                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  📋 История                                                           │
│  ────────────────────────────────────────────────────────────────────  │
│  📥 15.03.2026  Приета          +50.000 кг   ✅    Иван             │
│  📤 20.03.2026  Производство    -10.000 кг  #ПО-15   Мария          │
│  📤 21.03.2026  Производство    -15.000 кг  #ПО-16   Петер          │
│  📤 22.03.2026  Ръчно           -5.000 кг   -        Гошо           │
│  ────────────────────────────────────────────────────────────────────  │
│  📊 Остатък: 20.000 кг                                              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### ФАЗА 3: ТРАНСФЕР МЕЖДУ ЗОНИ 🟡

#### 5.8 Нов модел: `StockTransfer`

```python
class StockTransfer(Base):
    """Трансфер на стока между зони"""
    __tablename__ = "stock_transfers"
    
    id = Column(Integer, primary_key=True)
    from_zone_id = Column(Integer, ForeignKey("storage_zones.id"), nullable=False)
    to_zone_id = Column(Integer, ForeignKey("storage_zones.id"), nullable=False)
    status = Column(String(20), default="pending")  # pending, completed, cancelled
    notes = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    from_zone = relationship("StorageZone", foreign_keys=[from_zone_id])
    to_zone = relationship("StorageZone", foreign_keys=[to_zone_id])
    items = relationship("StockTransferItem", cascade="all, delete-orphan")

class StockTransferItem(Base):
    """Артикули в трансфер"""
    __tablename__ = "stock_transfer_items"
    
    id = Column(Integer, primary_key=True)
    transfer_id = Column(Integer, ForeignKey("stock_transfers.id"), nullable=False)
    batch_id = Column(Integer, ForeignKey("batches.id"), nullable=False)
    quantity = Column(Numeric(12, 3), nullable=False)
    
    batch = relationship("Batch")
```

#### 5.9 Mutations за трансфер

```python
@strawberry.mutation
async def create_stock_transfer(
    self,
    from_zone_id: int,
    to_zone_id: int,
    items: List[StockTransferItemInput],
    notes: Optional[str],
    info: strawberry.Info
) -> types.StockTransfer:
    """Създай трансфер"""

@strawberry.mutation
async def complete_transfer(
    self,
    transfer_id: int,
    info: strawberry.Info
) -> types.StockTransfer:
    """Завърши трансфер - промени storage_zone_id на партидите"""

@strawberry.mutation
async def cancel_transfer(
    self,
    transfer_id: int,
    info: strawberry.Info
) -> types.StockTransfer:
    """Откажи трансфер"""
```

#### 5.10 Frontend - Трансфери

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Трансфери                                                [+ Нов]        │
├─────────────────────────────────────────────────────────────────────────┤
│  [Филтър: ▼ Всички] [Зона: ▼ Всички]                               │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │ №150 | Статус: 🟡 Чакащ                                         │  │
│  │ От: Сух склад (#1) → Към: Хладилник #2                         │  │
│  │ 22.03.2026 | 3 артикула | 25.000 кг | Иван                     │  │
│  │                                                    [✓ Потвърди] │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │ №149 | Статус: ✅ Завршен                                        │  │
│  │ От: Хладилник #1 → Към: Сух склад                              │  │
│  │ 21.03.2026 | 1 артикул | 10.000 кг | Мария                   │  │
│  └─────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### ФАЗА 4: ПОДОБРЕНИЕ НА ИНВЕНТАРИЗАЦИЯТА 🟡

#### 5.11 Промяна на InventoryItem

```python
class InventoryItem(Base):
    # ... съществуващи полета ...
    reason = Column(String(100), nullable=True)  # "theft", "damage", "expiry", "error", "found"
    notes = Column(Text, nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    adjustment_batch_id = Column(Integer, ForeignKey("batches.id"), nullable=True)
```

#### 5.12 Mutations за одобрение

```python
@strawberry.mutation
async def request_adjustment_approval(
    self,
    session_id: int,
    item_id: int,
    reason: str,
    notes: Optional[str],
    info: strawberry.Info
) -> types.InventoryItem:
    """Заяви корекция за одобрение (при > 10% разлика)"""

@strawberry.mutation
async def approve_adjustment(
    self,
    item_id: int,
    info: strawberry.Info
) -> types.InventoryItem:
    """Одобри корекция"""

@strawberry.mutation
async def reject_adjustment(
    self,
    item_id: int,
    reason: str,
    info: strawberry.Info
) -> types.InventoryItem:
    """Откажи корекция"""
```

#### 5.13 Frontend - Подобрена инвентаризация

```
┌─────────────────────────────────────────────────────────────────────────┐
│  ⚠️ Голема разлика: -15.000 кг (25% от наличността)                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Артикул: Брашно тип 500                                              │
│  По система: 60.000 кг                                                │
│  Намерено: 45.000 кг                                                  │
│  Разлика: -15.000 кг ⚠️                                               │
│                                                                         │
│  Задължително одобрение от ръководител!                                 │
│                                                                         │
│  Причина: [▼ Изтичане / Повреда / Кражба / Друго                   ]   │
│                                                                         │
│  Бележки: [                                                     ]       │
│                                                                         │
│                                        [Изпрати за одобрение]           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### ФАЗА 5: ПРЕДУПРЕЖДЕНИЯ ЗА ИЗТИЧАНЕ 🟢

#### 5.14 Нов Job

**Файл:** `backend/jobs/expiry_alert_job.py`

```python
@job("cron", day_of_week="mon-fri", hour=8, minute=0)
async def check_expiring_batches():
    """Проверка за изтичащи партиди всяка сутрин"""
    
    # Партиди с < 7 дни - ИМЕЙЛ
    expiring_critical = select(Batch).where(
        Batch.expiry_date <= date.today() + timedelta(days=7),
        Batch.expiry_date > date.today(),
        Batch.status == "active",
        Batch.quantity > 0
    )
    
    for batch in expiring_critical:
        await send_email_alert(
            to=get_warehouse_managers(),
            subject=f"⚠️ КРИТИЧНО: Партида {batch.batch_number} изтича скоро!",
            template="expiry_critical",
            context={"batch": batch, "days": (batch.expiry_date - date.today()).days}
        )
    
    # Партиди с < 30 дни - СИСТЕМНО УВЕДОМЛЕНИЕ
    expiring_warning = select(Batch).where(...)
    await create_system_notifications(expiring_warning, type="expiry_warning")
```

#### 5.15 Dashboard Widget

```
┌─────────────────────────────────────────┐
│  ⚠️ Изтичащи партиди                     │
├─────────────────────────────────────────┤
│  🔴 Брашно - #2026-03-25-001           │
│     Изтича след: 3 дни (18.03.2026)    │
│                                         │
│  🟡 Масло - #2026-03-28-002            │
│     Изтича след: 6 дни (25.03.2026)    │
│                                         │
│  🟡 Яйца - #2026-03-28-003             │
│     Изтича след: 6 дни (25.03.2026)    │
└─────────────────────────────────────────┘
```

---

## 6. ТЕХНИЧЕСКИ ЗАВИСИМОСТИ

```
ФАЗА 1: Ръчно изразходване
    │
    ├── Нов модел: StockConsumptionLog
    ├── mutations: consume_from_batch, auto_consume_fefo
    ├── types: StockConsumptionLog, FefoSuggestion
    ├── queries: get_fefo_suggestion
    └── Frontend: Нов таб "Ръшно изразходване"
         │
         ▼
ФАЗА 2: Проследяване
    │
    ├── Използва: StockConsumptionLog от Фаза 1
    ├── queries: stock_consumption_logs, batch_history
    └── Frontend: Бутон "История" в партида
         │
         ▼
ФАЗА 3: Трансфери (НЕЗАВИСИМА)
    │
    ├── Нов модел: StockTransfer, StockTransferItem
    ├── mutations: create_transfer, complete_transfer, cancel_transfer
    └── Frontend: Нов таб "Трансфери"
         │
         ▼
ФАЗА 4: Инвентаризация (НЕЗАВИСИМА)
    │
    ├── Промяна: InventoryItem модел
    ├── mutations: request_adjustment_approval, approve_adjustment
    └── Frontend: Подобрено UI
         │
         ▼
ФАЗА 5: Предупреждения (НЕЗАВИСИМА)
    │
    ├── Job: expiry_alert_job
    ├── Notification система
    └── Frontend: Dashboard widget
```

---

## 7. ФАЙЛОВЕ ЗА ПРОМЯНА

### 7.1 Нов файлове

| Файл | Описание |
|------|----------|
| `backend/jobs/expiry_alert_job.py` | Job за предупреждения |
| `backend/services/stock_service.py` | Business логика за стока |
| `frontend/src/components/BatchHistoryDialog.tsx` | Диалог за история |
| `frontend/src/components/StockConsumptionDialog.tsx` | Диалог за изразходване |
| `frontend/src/components/TransferDialog.tsx` | Диалог за трансфер |

### 7.2 Модифицирани файлове

| Файл | Промени |
|------|---------|
| `backend/database/models.py` | +StockConsumptionLog, +StockTransfer, +StockTransferItem |
| `backend/graphql/inputs.py` | +StockConsumptionInput, +StockTransferInput, +FefoSuggestion |
| `backend/graphql/types.py` | +StockConsumptionLog, +StockTransfer, +BatchHistoryEntry types |
| `backend/graphql/mutations.py` | +consume_from_batch, +auto_consume_fefo, +create_transfer, etc. |
| `backend/graphql/queries.py` | +stock_consumption_logs, +batch_history, +pending_transfers |
| `backend/init_db.py` | +ALTER TABLE за нови колони |
| `frontend/src/types.ts` | +StockConsumptionLog, +StockTransfer типове |
| `frontend/src/graphql/warehouseMutations.ts` | +mutations за склада |
| `frontend/src/pages/WarehousePage.tsx` | +табове за нови функции |
| `frontend/src/components/MainLayout.tsx` | +навигация за нови табове |
| `frontend/src/components/Dashboard.tsx` | +widget за изтичащи партиди |

---

## 8. ПОДРЕДБА ЗА ИМПЛЕМЕНТАЦИЯ

| Фаза | Описание | Сложност | Време | Зависимости |
|------|---------|-----------|--------|-------------|
| **1** | Ръчно изразходване | Средна | 2-3 дни | Няма |
| **2** | Проследяване | Ниска | 1 ден | Фаза 1 |
| **3** | Трансфери | Средна | 2 дни | Няма |
| **4** | Инвентаризация | Средна | 2 дни | Няма |
| **5** | Предупреждения | Ниска | 1 ден | Няма |
| **ОБЩО** | | | **~8-10 дни** | |

---

## 9. МИГРАЦИЯ НА БАЗАТА ДАННИ

```sql
-- StockConsumptionLog
CREATE TABLE IF NOT EXISTS stock_consumption_logs (
    id SERIAL PRIMARY KEY,
    ingredient_id INTEGER NOT NULL REFERENCES ingredients(id),
    batch_id INTEGER NOT NULL REFERENCES batches(id),
    quantity NUMERIC(12, 3) NOT NULL,
    reason VARCHAR(50) NOT NULL,
    production_order_id INTEGER REFERENCES production_orders(id),
    notes TEXT,
    created_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_consumption_ingredient ON stock_consumption_logs (ingredient_id);
CREATE INDEX IF NOT EXISTS idx_consumption_batch ON stock_consumption_logs (batch_id);
CREATE INDEX IF NOT EXISTS idx_consumption_created ON stock_consumption_logs (created_at);

-- StockTransfer
CREATE TABLE IF NOT EXISTS stock_transfers (
    id SERIAL PRIMARY KEY,
    from_zone_id INTEGER NOT NULL REFERENCES storage_zones(id),
    to_zone_id INTEGER NOT NULL REFERENCES storage_zones(id),
    status VARCHAR(20) DEFAULT 'pending',
    notes TEXT,
    created_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_transfer_status ON stock_transfers (status);

-- StockTransferItem
CREATE TABLE IF NOT EXISTS stock_transfer_items (
    id SERIAL PRIMARY KEY,
    transfer_id INTEGER NOT NULL REFERENCES stock_transfers(id) ON DELETE CASCADE,
    batch_id INTEGER NOT NULL REFERENCES batches(id),
    quantity NUMERIC(12, 3) NOT NULL
);

-- InventoryItem - нови колони
ALTER TABLE inventory_items ADD COLUMN IF NOT EXISTS reason VARCHAR(100);
ALTER TABLE inventory_items ADD COLUMN IF NOT EXISTS notes TEXT;
ALTER TABLE inventory_items ADD COLUMN IF NOT EXISTS approved_by INTEGER REFERENCES users(id);
ALTER TABLE inventory_items ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP;
```

---

## 10. ТЕСТВАНЕ

### 10.1 Unit тестове

```python
# tests/test_stock_consumption.py
async def test_consume_from_batch():
    """Тест за ръчно изразходване"""
    pass

async def test_fefo_consumption():
    """Тест за FEFO изразходване"""
    pass

async def test_transfer_complete():
    """Тест за завършване на трансфер"""
    pass

async def test_batch_history():
    """Тест за история на партида"""
    pass
```

### 10.2 Integration тестове

```python
# tests/test_inventory_adjustment.py
async def test_adjustment_requires_approval():
    """Тест че > 10% разлика изисква одобрение"""
    pass
```

---

## 11. РИСКОВЕ И ОГРАНИЧЕНИЯ

| Риск | Вероятност | Влияние | Мотигация |
|------|-----------|---------|-----------|
| Забавяне на FEFO при голями партиди | Средна | Ниска | Индексиране, пагинация |
| Конфликт при паралелно изразходване | Ниска | Средна | Transaction locking |
| Загуба на данни при неправилна корекция | Ниска | Висока | Audit log, backup |

---

## 12. SUCCESS CRITERIA

| Критерий | Мярка |
|----------|--------|
| Ръчно изразходване | < 3 клика за операция |
| FEFO предложение | Точност > 95% |
| История на партида | Пълен audit log |
| Трансфери | Всички прехвърляния проследени |
| Инвентаризация | 0 неоторизирани корекции |
| Предупреждения | 100% покритие на < 7 дни |

---

## 13. СТАТУС

| Фаза | Статус | Бележки |
|------|--------|---------|
| Фаза 1: Ръчно изразходване | 📋 Планирана | |
| Фаза 2: Проследяване | 📋 Планирана | Зависи от Фаза 1 |
| Фаза 3: Трансфери | 📋 Планирана | |
| Фаза 4: Инвентаризация | 📋 Планирана | |
| Фаза 5: Предупреждения | 📋 Планирана | |

---

*Създаден на: 21.03.2026*  
*Базиран на: Анализ на стоковия поток и липсващи функционалности*  
*Версия: 1.0*
