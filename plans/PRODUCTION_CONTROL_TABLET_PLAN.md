# ПЛАН: Производствен Контролен Таблет

## 1. Преглед

Добавяне на "Контролен таблет" за началници на отдели в системата, който позволява:
- Управление на поръчки за деня
- Промяна на количество за производство
- Преместване на работници между станции

## 2. База Данни

### 2.1 Нови Поля в models.py

**Recipe (backend/database/models.py):**
```python
production_deadline_days = Column(Integer, nullable=True)  # Колко дни преди expiry да се произведе
```

**ProductionOrder (backend/database/models.py):**
```python
production_deadline = Column(DateTime, nullable=True)  # Изчислена дата за производство
```

### 2.2 Alembic Миграция
- Създаване на миграция за новите полета

## 3. Бекенд

### 3.1 Обновяване на create_production_order mutation
- При създаване на поръчка, изчисляване на production_deadline:
  - production_deadline = expiry_date - production_deadline_days

### 3.2 GraphQL Queries
```graphql
# Поръчки за конкретен ден
productionOrdersForDay(date: Date!): [ProductionOrder!]!

# Поръчки с production_deadline <= днес
overdueProductionOrders: [ProductionOrder!]!
```

### 3.3 GraphQL Mutations
```graphql
# Промяна на количество за ден
updateOrderDailyQuantity(
  orderId: Int!
  date: Date!
  quantity: Float!
): ProductionOrder!

# Преместване на работник между станции
reassignTaskWorkstation(
  taskId: Int!
  newWorkstationId: Int!
): ProductionTask!
```

## 4. Фронтенд

### 4.1 Рецепти (RecipesPage.tsx)
- Добавяне на поле "Срок за производство (дни)" в редактиране на рецепта

### 4.2 Поръчки (OrdersPage.tsx)
- Показване на production_deadline в списъка
- Филтър по просрочени поръчки

### 4.3 Нова Страница: ProductionControlPage.tsx
- **Път**: `/admin/production/control`
- **Достъп**: Началници на отдели + Админи

#### Функционалност:
1. **Списък с поръчки за деня**
   - production_deadline <= днес
   - Филтър по отдел/рецепта
   
2. **Промяна на количество за ден**
   - Сплитване на количествотото по дни
   - Пример: поръчка 120бр, expiry 10 дни, production_deadline_days=1
     - Днес: 40бр, Утре: 80бр

3. **Преместване на работник**
   - Преместване на работник от една станция на друга
   - Всички поръчки го следват

### 4.4 MainLayout Меню
```
Производство
├── Поръчки (/admin/orders)
└── Контрол (/admin/production/control) [НОВО]
```

## 5. Flow

### 5.1 Създаване на Поръчка
1. Админ създава поръчка с рецепта
2. Системата изчислява production_deadline
3. Поръчката се показва в Контролния таблет

### 5.2 Контролен Таблет
1. Началник отваря `/admin/production/control`
2. Вижда поръчките за деня (production_deadline <= днес)
3. Може да:
   - Промени количество за деня
   - Премести работник между станции
   - Прегледа статуса на задачите

## 6. Примери

### Пример 1: Промяна на количество
- Поръчка: 120 блата
- expiry: след 10 дни
- production_deadline_days: 1

| Ден | Количество |
|-----|-----------|
| Днес (Ден 9) | 40бр |
| Утре (Ден 10) | 80бр |

Началникът избира: "Днес 40, Утре 80"

### Пример 2: Преместване на работник
| Станция | Работник |
|---------|----------|
| Блатове | Иван (закъснява) |
| Крем | Мария |
| Декорация | Петър |

Началникът премества Петър от "Декорация" → "Блатове"

## 7. Достъп

| Роля | Достъп |
|------|--------|
| super_admin | Всички поръчки, всички отдели |
| admin | Всички поръчки, всички отдели |
| Началник на отдел | Само своите отдели |
