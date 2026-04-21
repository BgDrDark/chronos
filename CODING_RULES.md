# Правила за писане на качествен код

## 1. Именуване

### Конвенции
| Елемент | Стил | Пример |
|---------|------|--------|
| Frontend променливи | camelCase | `userName`, `totalPrice` |
| Frontend функции | camelCase | `handleSavePrice`, `calculateTotal` |
| Backend променливи | snake_case | `user_name`, `total_price` |
| База данни колони | snake_case | `created_at`, `company_id` |
| GraphQL полета | snake_case | `createdAt` → `created_at` (backend) |

### Правила
- Използвай смислени имена: `userCount` вместо `x`
- Спазвай конвенциите на езика
- НЕ използвай уникални съкращения

---

## 2. Frontend TypeScript правила

### Типизация
```typescript
// ❌ НЕ - използвай any
const data: any = response.json();

// ✅ ДА - използвай конкретни типове
const data: RecipeWithPrice[] = response.data;
```

### Error Handling
```typescript
// ❌ НЕ - използвай console.error
} catch (err) {
  console.error(err);
}

// ✅ ДА - използвай getErrorMessage от types.ts
} catch (err) {
  setError(getErrorMessage(err));
}
```

### GraphQL операции
```typescript
// ❌ НЕ - пиши GraphQL заявки в компонента
const { data } = useQuery(gql`query { recipes }`);

// ✅ ДА - екстрахирай в отделен файл
import { GET_RECIPES } from '../graphql/confectioneryQueries';
```

### GraphQL Naming
```typescript
// Frontend изпраща camelCase
mutation UpdateRecipe($input: RecipeInput!) {
  updateRecipe(input: $input) {  // camelCase в заявката
    recipeId    // camelCase
  }
}

// Backend получава snake_case
async def update_recipe(
    self,
    recipe_id: int,  // snake_case в Python
    input: RecipeInput,
    info: strawberry.Info
):
```

---

## 3. Backend Python правила

### Типизация
```python
# ❌ НЕ - използвай typing.Any
from typing import Any
def process(data: Any):

# ✅ ДА - използвай конкретни типове
from typing import Optional
def process(data: dict[str, int]):
```

### Error Handling - exceptions.py

Използвай централизираните exceptions от `backend/exceptions.py`:

```python
from backend.exceptions import (
    NotFoundException,
    PermissionDeniedException,
    ValidationException,
    DatabaseException,
    AuthenticationException,
)

# ✅ ДА - използвай presets за конкретни грешки
raise NotFoundException.user(user_id=123)
raise NotFoundException.recipe(recipe_id=456)
raise ValidationException.field("email", "Невалиден формат")
raise PermissionDeniedException.for_resource("invoice", "delete")
```

**Presets за NotFoundException:**
```python
NotFoundException.user(user_id=123)
NotFoundException.vehicle(vehicle_id=1)
NotFoundException.recipe(recipe_id=1)
NotFoundException.ingredient(ingredient_id=1)
NotFoundException.order(order_id=1)
NotFoundException.request(request_id=1)
NotFoundException.session(session_id=1)
NotFoundException.record("Invoice", invoice_id=1)
NotFoundException.resource("warehouse", warehouse_id=1)
```

**Presets за ValidationException:**
```python
ValidationException.field("email", "Невалиден формат")
ValidationException.required_field("password")
ValidationException.email("Липсва @")
ValidationException.password("Твърде кратка")
```

**Presets за PermissionDeniedException:**
```python
PermissionDeniedException.for_resource("invoice", "edit")
PermissionDeniedException.for_action("approve")
```

**Presets за DatabaseException:**
```python
DatabaseException.duplicate("Потребител")
DatabaseException.foreign_key("company_id")
DatabaseException.constraint("unique_email")
```

### Error Handling - backwards compatibility

За постепенна миграция, aliases-ите работят:

```python
from backend.exceptions import not_found, bad_request, permission_denied

# Работи, но е deprecated
raise not_found("User not found")
raise bad_request("Invalid data")
raise permission_denied("No rights")
```

### Error Handling - error_handling.py utilities

Използвай utils за специфични случаи:

```python
from backend.utils.error_handling import handle_db_error, get_error_message

# Обработка на DB грешки
try:
    await db.execute(stmt)
except Exception as e:
    raise handle_db_error(e)

# Извличане на съобщение от грешка
error_msg = get_error_message(exception)
```

### Error Response формат

Всички грешки връщат консистентен формат:

```json
{
    "error": "USER_NOT_FOUND",
    "message": "Потребител не е намерен (ID: 123)",
    "timestamp": "2024-01-01T12:00:00",
    "context": {
        "resource": "user",
        "id": 123
    }
}
```

### Error Handling - Frontend

Използвай `useError` hook за показване на грешки и успешни съобщения:

```typescript
// ✅ ДА - използвай централизирания ErrorContext
import { useError, extractErrorMessage } from '../context/ErrorContext';

const MyComponent = () => {
  const { showError, showSuccess, showWarning } = useError();

  const handleDelete = async (id: number) => {
    try {
      await deleteMutation({ variables: { id } });
      showSuccess('Записът е изтрит успешно');
    } catch (error) {
      showError(extractErrorMessage(error));
    }
  };
};
```

**Налични методи:**
- `showError(message)` - Червено съобщение за грешки
- `showSuccess(message)` - Зелено съобщение за успех
- `showWarning(message)` - Жълто съобщение за предупреждения
- `showInfo(message)` - Синьо съобщение за информация

**extractErrorMessage()** - извлича съобщението от различни формати:
- GraphQL errors (`error.graphQLErrors[0].message`)
- Regular errors (`error.message`)
- String errors
- Fallback: `'Възникна грешка'`

### Strawberry GraphQL параметри
```python
# ❌ НЕ - optional параметри преди info
async def update_recipe(
    self,
    notes: Optional[str] = None,  # ❌ Грешно
    info: strawberry.Info
):

# ✅ ДА - info ПЪРВО, после optional
async def update_recipe(
    self,
    info: strawberry.Info,
    notes: Optional[str] = None
):
```

### SQLAlchemy и Асинхронност (MissingGreenlet)
```python
# ❌ НЕ - мързеливо зареждане (lazy loading) в асинхронна среда
# Това ще предизвика sqlalchemy.exc.MissingGreenlet при достъп до релация
stmt = select(User).where(User.id == user_id)
user = (await db.execute(stmt)).scalar_one()
return UserType.from_instance(user) # Ако from_instance достъпва user.role синхронно

# ✅ ДА - използвай selectinload за предварително зареждане
from sqlalchemy.orm import selectinload

stmt = select(User).options(
    selectinload(User.role),
    selectinload(User.company_rel)
).where(User.id == user_id)
```
1. **V2.0**: При възможност използвай SQLAlchemy(v2.0)
**Правила за релации:**
2. **Винаги** използвай `selectinload` в заявките (`select`), ако методът `from_instance` на съответния тип достъпва тези релации.
3. **Избягвай** достъп до релации в `from_instance`, ако те са тежки. Вместо това дефинирай асинхронно поле (`@strawberry.field`) в типа, което използва `DataLoader`.
4. **Shadowing**: При импорт на модели в GraphQL типовете, винаги използвай алиас (`from models import User as DbUser`), за да не презапишеш името на GraphQL класа и да получиш `AttributeError`.
5. **Refresh**: При използване на `db.refresh()`, винаги изброявай нужните релации: `await db.refresh(instance, ["company", "position"])`.

---

## 4. Форматиране на валута

### Централизирана валута
```typescript
// ✅ ДА - използвай централизирани функции
import { useCurrency, formatCurrencyValue } from '../currencyContext';

const MyComponent = () => {
  const { currency } = useCurrency();
  // currency: 'EUR' | 'USD' | 'BGN'
  
  const formatted = formatCurrencyValue(19.99, currency);
  // EUR → "19.99 €"
  // USD → "$19.99"
  // BGN → "19.99 лв."
};
```

### Правила
- **Винаги** използвай `formatCurrencyValue()` от `currencyContext`
- **Никога** не пиши hardcoded валутни символи (`лв.`, `€`, `$`)
- Символите се определят от `globalPayrollConfig.currency` в настройките
- За ценови компоненти в подкомпоненти - винаги дефинирай `formatPrice` локално с `useCurrency()`

### Backend (Decimal)
```python
# ❌ НЕ - използвай float за пари
price = 19.99
total = subtotal * 0.2

# ✅ ДА - използвай Decimal за парични стойности
from decimal import Decimal

price = Decimal("19.99")
total = subtotal * Decimal("0.2")
```

---

## 5. Plan Mode (Режим "План")

### Преди имплементация
1. Запиши план във файл с разширение `.md`
2. Опиши какво трябва да се направи
3. Списък със стъпки за изпълнение

### След имплементация
1. Маркирай завършените стъпки с `[x]`
2. Актуализирай плана с направените промени
3. Запиши промените в git ако е нужно

### Пример структура
```markdown
# ПЛАН: Име на функционалността

## ЦЕЛ
Какво трябва да се постигне

## ПРОБЛЕМ
Съществуващ проблем или липсваща функционалност

## РЕШЕНИЕ
Какво ще се направи

## Стъпки
- [ ] Стъпка 1
- [ ] Стъпка 2
- [ ] Стъпка 3 (завършена)
```

---

## 6. React/Component правила

### Tooltips
```tsx
// ❌ НЕ - hover tooltips (забранени)
// ✅ ДА - onClick tooltips

<Tooltip title="Help info" onClick={handleHelpClick}>
  <IconButton>?</IconButton>
</Tooltip>
```

### Централизирани компоненти
```tsx
// ❌ НЕ - повтаряй TextField с валидация
<TextField error={!!errors.name} helperText={errors.name} ... />

// ✅ ДА - използвай централизиран ValidatedTextField
<ValidatedTextField
  label="Име"
  value={form.name}
  onChange={handleNameChange}
  error={validationErrors.name}
  required
/>
```

### Tooltips с InfoIcon (onClick)

Всички form field-ове с помощни текстове използват **InfoIcon** компонент с onClick (НЕ hover):

```tsx
import { InputAdornment } from '@mui/material';
import { InfoIcon } from '../components/ui/InfoIcon';
import { someFieldsHelp } from '../components/ui/fieldsHelpText';

// ✅ ДА - InfoIcon с onClick в slotProps.input.endAdornment
<TextField
  label="Име на полето"
  value={value}
  onChange={handleChange}
  slotProps={{
    input: {
      endAdornment: (
        <InputAdornment position="end">
          <InfoIcon helpText="Текст за помощната подсказка" />
        </InputAdornment>
      )
    }
  }}
/>

// ❌ НЕ - MUI Tooltip с hover (за field-ове)
// Hover tooltips СЕ запазват само за бутони и действия
<Tooltip title="Редактирай">
  <IconButton onClick={handleEdit}>
    <EditIcon />
  </IconButton>
</Tooltip>
```

**Правила за tooltips:**
1. `InputLabelProps={{ shrink: true }}` - САМО за `type="date"` полета
2. Селектите НЯМАТ shrink (label-а плава)
3. Help text-овете са в `fieldsHelpText.ts`
4. Hover tooltips остават за действия (бутони, иконки)

### MUI конвенции
```tsx
// Използвай Grid size вместо xs/md
// ❌
<Grid item xs={12} sm={6}>

// ✅
<Grid size={{ xs: 12, sm: 6 }}>
```

---

## 7. DRY принцип (Don't Repeat Yourself)

### Повтаряне на код
```tsx
// ❌ НЕ - повтаряй форматиране на цени
const price1 = data.price.toFixed(2) + ' лв.';
const price2 = order.total.toFixed(2) + ' лв.';

// ✅ ДА - използвай централизираната функция
import { useCurrency, formatCurrencyValue } from '../currencyContext';

const { currency } = useCurrency();
const formatted1 = formatCurrencyValue(data.price, currency);
const formatted2 = formatCurrencyValue(order.total, currency);
```

---

## 8. Функции

### Размер
- Една функция = едно нещо
- Максимум 30-50 реда
- Ако е по-дълга, раздели на по-малки

### Именуване
```tsx
// Event handlers
handleSave()         // camelCase
onSubmit()           // camelCase с on prefix

// API calls
fetchRecipes()       // camelCase
createInvoice()       // camelCase

// Getters
getRecipes()         // camelCase
getInvoiceStatus()    // camelCase
```

---

## 9. Коментари

### Правило
- Коментирай "защо" не "какво"
- Не коментирай очевидното

```tsx
// ❌ Излишен коментар
// Сумира числата
const total = prices.reduce((a, b) => a + b, 0);

// ✅ Смислен коментар
// FEFO: първо използвай партидите с най-близка годност
const sortedBatches = batches.sort((a, b) => 
  new Date(a.expiryDate).getTime() - new Date(b.expiryDate).getTime()
);
```

---

## 10. Разделяне на компоненти

### Принцип
Големи компоненти се разделят на по-малки, специализирани.

### Пример
```tsx
// ❌ Компонент с много отговорности
function RecipesPage() {
  //... 500 реда код
}

// ✅ Разделени компоненти
function RecipesPage() {
  return (
    <RecipeList />
    <RecipeDialog />
    <RecipeDetails />
  );
}
```

### Кога да разделяш?
- Компонент > 200 реда
- Логика за различни табове/секции
- Повтаряща се UI структура

---

## 11. Тестване

- Пиши тестове за критични функции
- Покрий edge cases
- Тествай error handling

---

## 12. Рефакторинг

- Преглеждай кода редовно
- Подобрявай структурата
- Използвай technical debt за коментари на функциите


---

## 12.1 Alembic Миграции

### Правила за работа с Alembic

1. **Винаги поддържай ЕДИН head**
   - Ако имаш множество head-ове, `alembic revision --autogenerate` няма да работи
   - Преди да създадеш нова миграция, провери с `alembic heads`

2. **Сливане на множество head-ове**
   ```bash
   # Когато имаш повече от един head:
   alembic merge head1 head2 head3 -m "merge_all_heads"
   ```

3. **Създаване на миграция**
   ```bash
   cd backend
   alembic revision --autogenerate -m "add_new_column"
   alembic upgrade head
   ```

4. **Проверка на състоянието**
   ```bash
   alembic current          # Къде е текущата миграция
   alembic heads            # Колко head-а има
   alembic history          # История на миграциите
   ```

5. **Когато нещо се обърка**
   ```bash
   # Ако autogenerate дава грешка за multiple heads:
   alembic merge <head1> <head2> -m "merge_heads"
   alembic upgrade <нов_head>
   ```

### Структура на alembic.ini

```ini
[alembic]
sqlalchemy.url = postgresql://postgres:postgres@localhost:5432/workingtimedb
```

**Важно:** URL-ът трябва да е синхронен (без `+asyncpg`).

### Чести грешки

1. **Липсващ company_id при нов модел**
   ```python
   # ❌ НЕ - моделът няма company_id
   class ScheduleTemplate(Base):
       id: Mapped[int] = mapped_column(Integer, primary_key=True)
       name: Mapped[str] = mapped_column(String)
   
   # ✅ ДА - добави company_id
   class ScheduleTemplate(Base):
       id: Mapped[int] = mapped_column(Integer, primary_key=True)
       company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), nullable=False)
       name: Mapped[str] = mapped_column(String)
       company = relationship("Company")
   ```

2. **Липсващ company_id filter в queries**
   ```python
   # ❌ НЕ - връща всички записи
   async def schedule_templates(self, info):
       stmt = select(ScheduleTemplate)
   
   # ✅ ДА - филтрирай по company_id
   async def schedule_templates(self, info):
       current_user = info.context["current_user"]
       stmt = select(ScheduleTemplate).where(
           ScheduleTemplate.company_id == current_user.company_id
       )
   ```

3. **Неподходящ revision ID**
   ```python
   # ❌ НЕ - твърде дълго име
   revision: str = 'add_company_id_to_schedule_template_version_2_final'
   
   # ✅ ДА - кратко име
   revision: str = 'add_st_company_id'
   ```

---

## 13. Бизнес логика

### 13.1 Склад (Warehouse)

```typescript
// FEFO - First Expired First Out
// Винаги първо използвай партидите с най-близка годност

// При ръчно изразходване - позволи избор на конкретна партида
// При автоматично изразходване - използвай FEFO логика

// Партида структура:
interface Batch {
  id: number;
  batchNumber: string;      // Номер на партидата
  expiryDate: string;       // Срок на годност
  availableStock: number;    // Налично количество
  supplier?: Supplier;        // Доставчик
}
```

### 13.2 Фактури (Invoices)

```typescript
// Статус преходи (валидирани):
const ALLOWED_TRANSITIONS = {
  'draft': ['sent', 'paid', 'cancelled'],
  'sent': ['paid', 'cancelled'],
  'paid': ['cancelled'],     // Само super_admin
  'overdue': ['paid', 'cancelled'],
  'cancelled': []            // Краен статус
};

// Полета:
// incoming: ИЗДАТЕЛ = доставчик, ПОЛУЧАТЕЛ = нашата фирма
// outgoing: ИЗДАТЕЛ = нашата фирма, ПОЛУЧАТЕЛ = клиент

// При редакция - артикулите са само за четене
```

### 13.3 Рецепти (Recipes)

```typescript
// Бр. парчета (defaultPieces):
// Използва се за изчисляване на количества
// При промяна → преизчислявай съставките пропорционално

// Формула:
// ново_количество = старо_количество × (нови_парчета / стари_парчета)

// Секции на рецепта:
type SectionType = 'dough' | 'cream' | 'decoration';
// dough   - ПЕКАРНА (блатове)
// cream   - КРЕМОВЕ (кремове)
// decoration - ДЕКОРАЦИЯ (декорации)

// Цени:
// себестойност (costPrice)     - изчислена от съставките
// markup %                     - надценка над себестойността
// premiumAmount               - допълнителна надценка
// finalPrice = costPrice + (costPrice × markup%) + premiumAmount
```

### 13.4 Поръчки (Orders)

```typescript
// Статуси:
// awaiting_stock → ready → in_progress → completed

// При ready → потребителят потвърждава за стартиране
// При completed → стоките се добавят в склада

// Свързани са с рецепти и техните съставки
```

### 13.5 Ценообразуване (Menu Pricing)

```typescript
// Формула за крайна цена:
finalPrice = costPrice + markup + premiumAmount
where: markup = costPrice × (markupPercentage / 100)

// Price History - записва всички промени на цените
interface PriceHistory {
  oldPrice: number;
  newPrice: number;
  reason: string;
  timestamp: string;
  user: User;
}
```

---

## 14. Docker/Deployment

```bash
# При промяна на мрежови настройки - винаги рестартирай nginx-proxy-manager
docker restart workingtime-nginx-proxy-manager-1

# При проблеми с container-и - провери мрежата
docker network ls
docker network inspect workingtime_default

# Ако container-и не са в една мрежа:
docker network connect workingtime_default <container_name>

# Build с --no-cache ако има проблеми
docker build --no-cache -t <image>:<tag> <context>
```

---

## Бързи справки

### Frontend helpers
```typescript
import { getErrorMessage } from '../types';
import ValidatedTextField from '../components/ui/ValidatedTextField';
import { useCurrency, formatCurrencyValue } from '../currencyContext';
```

### Backend helpers
```python
from backend.utils.error_handling import (
    bad_request, not_found, permission_denied,
    unauthorized, internal_server_error
)
```

### GraphQL naming map
```
Frontend (camelCase)  →  Backend (snake_case)
────────────────────────────────────────────
recipeId              →  recipe_id
markupPercentage      →  markup_percentage
finalPrice            →  final_price
```

### GraphQL JSON типове

За връщане на JSON/dict от GraphQL mutations, използвай `JSONScalar`:

```python
# ✅ ДА - използвай JSONScalar от utils
from backend.utils.json_type import JSONScalar

@strawberry.mutation
async def generate_report(...) -> JSONScalar:
    return await generator.generate_data()

# ❌ НЕ - не използвай Python dict директно
@strawberry.mutation
async def generate_report(...) -> dict:  # Грешка!
    return {"data": "value"}
```

**Защо?** Strawberry GraphQL не поддържа Python `dict` като return тип в mutations.

---

## 15. Проверка на грешки в Backend

### Python типове (mypy)

```bash
# Проверка на конкретен файл преди билд
cd backend
mypy routers/gateway.py

# Проверка на цялия backend
mypy . --ignore-missing-imports

# Само грешки (без предупреждения)
mypy . --no-error-summary
```

### Docker логове

```bash
# Основни логове
docker compose logs backend

# Само грешки
docker compose logs backend 2>&1 | grep -E "ERROR|Traceback"

# Реално време
docker compose logs -f backend
```

### Чести грешки

- **MissingGreenlet** - липсващ `selectinload` при async заявки
- **InvalidRequestError** - липсващ `back_populates` relationship
- **AttributeError** - грешен тип на променлива
- **sqlalchemy.exc.*** - SQLAlchemy грешки

### Health check

```bash
# Проверка на backend
curl http://localhost:14240/health

# Проверка на GraphQL
curl -X POST http://localhost:14240/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ __typename }"}'
```

---

## 16. Архитектура на Проекта

### 1. База Данни (`backend/database/`)

```
backend/database/
├── models.py          # SQLAlchemy модели (~169 класа)
├── database.py         # DB връзка
├── session_proxy.py    # Session proxy
└── transaction_manager.py  # Транзакци управление
```

**Основни Модели:**

| Категория | Модели |
|-----------|--------|
| HR | User, Role, Permission, Company, Department, Position |
| Трудови договори | EmploymentContract, ContractAnnex, ContractTemplate |
| Отчитане | TimeLog, Shift, WorkSchedule |
| Заплати | Payroll, Payslip, Bonus |
| Отпуски | LeaveRequest, LeaveBalance |
| Производство | Recipe, Ingredient, Batch, ProductionOrder, ProductionTask |
| Склад | Supplier, WarehouseItem |
| Фактури | Invoice, InvoiceItem |
| Автопарк | Vehicle, VehicleTrip, VehicleFuel |
| Хардуер | Gateway, Terminal, AccessDoor, AccessZone |

### 2. Бизнес Логика (`backend/services/`)

```
backend/services/
├── payroll_calculator.py         # Основни изчисления
├── enhanced_payroll_calculator.py  # TRZ изчисления
├── trz_calculators.py            # Нощен/извънреден труд
├── recipe_cost_calculator.py     # Себестойност
├── saft_generator.py             # SAF-T справки
├── accounting_service.py          # Счетоводство
├── compliance_service.py          # Законова съответствие
├── google_calendar_service.py    # Google Calendar
└── holiday_service.py           # Празници
```

### 3. API Слой (`backend/routers/` + `backend/graphql/`)

**REST Рутери:**

| Рутер | Път | Описание |
|-------|-----|----------|
| auth | `/auth/*` | OAuth, login, tokens |
| export | `/export/*` | Excel, PDF експорт |
| warehouse | `/warehouse/*` | Склад |
| kiosk | `/kiosk/*` | Терминали |
| gateway | `/gateways/*` | Хардуер |
| terminal | `/terminal/*` | Комуникация |

**GraphQL:**

| Файл | Редове |
|------|--------|
| queries.py | 2779 |
| mutations.py | 7852 |
| types.py | 4549 |

### 4. Frontend (`frontend/src/`)

```
frontend/src/
├── components/     # Reusable компоненти
├── pages/          # Страници
├── graphql/        # GraphQL заявки
├── context/        # React contexts
├── hooks/          # Custom hooks
├── services/       # API услуги
├── utils/          # Помощни фунцкии
└── types.ts        # TypeScript интерфейси
```

### 5. Ключови Технологии

| Технология | Употреба |
|-------------|----------|
| FastAPI | REST API |
| SQLAlchemy (async) | ORM |
| Strawberry GraphQL | GraphQL API |
| PostgreSQL | База данни |
| React 18 | Frontend |
| Apollo Client | GraphQL клиент |
| MUI | UI компоненти |

### 6. Зависимости

```
Backend:
├── FastAPI
├── SQLAlchemy (async)
├── Strawberry GraphQL
├── PostgreSQL
├── Pydantic
└── Aiohttp

Frontend:
├── React 18
├── TypeScript
├── Apollo Client
├── MUI
└── React Router
```

---

## 17. Изведени Правила от Практиката

### 17.1 Използвай logging, не print()

```python
# ❌ НЕ
print(f"Error: {e}")

# ✅ ДА
logger = logging.getLogger(__name__)
logger.error(f"Error: {e}")
```

### 17.2 Не използвай bare except:

```python
# ❌ НЕ
except:
    pass

# ✅ ДА
except (ValueError, TypeError):
    pass

# ИЛИ
except Exception as e:
    logger.error(f"Error: {e}")
    raise
```

### 17.3 Annotated със Depends - внимавай с подредбата

```python
# ⚠️ Внимавай - параметри без default трябва да са преди параметри със default
# Това работи:
async def my_endpoint(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):

# Това НЕ работи (SyntaxError):
async def my_endpoint(skip: int, limit: int, db: AsyncSession = Depends(get_db)):
```

### 17.4 DRY - извличай дублиран код

```python
# ❌ НЕ - дублиране на функция
def calculate_distance(...):
    ...

# В различни файлове

# ✅ ДА - един път
# backend/utils/geo.py
def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    ...

# Използвай навсякъде
from backend.utils.geo import calculate_distance
```

### 17.5 Hardcoded стойности - използвай config

```python
# ❌ НЕ
ALLOWED_ORIGINS = ["https://dev.oblak24.org", ...]

# ✅ ДА
from backend.config import settings
cors_origins = settings.BACKEND_CORS_ORIGINS if settings.BACKEND_CORS_ORIGINS else DEFAULT_ORIGINS
```

---

## 18. База Данни - Най-добри Практики

### 18.1 Connection Pool

```python
# ❌ НЕ - използвай default конфигурация
engine = create_async_engine(str(settings.DATABASE_URL))

# ✅ ДА - експлицитна конфигурация
engine = create_async_engine(
    str(settings.DATABASE_URL),
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
)
```

### 18.2 N+1 Queries - Използвай selectinload

```python
# ❌ НЕ - N+1 проблем
for user in users:
    print(user.role.name)  # За всяка итерация = нова заявка

# ✅ ДА - eager loading
result = await db.execute(
    select(User).options(selectinload(User.role))
)
```

### 18.3 Паралелни Заявки - asyncio.gather

```python
# ❌ НЕ - последователно изпълнение
for u in users:
    amount = await calc.calculate_forecast(u.id, year, month)

# ✅ ДА - паралелно изпълнение
import asyncio
amounts = await asyncio.gather(*[
    calc.calculate_forecast(u.id, year, month) 
    for u in users
])
```

### 18.4 Transaction Management

```python
# ✅ ДА - използвай atomic_transaction
from backend.database.transaction_manager import atomic_transaction

async def my_mutation(db: AsyncSession, ...):
    async with atomic_transaction(db) as tx:
        #，自动ни commit/rollback
        await tx.execute(...)
```

### 18.5 SQL Injection - Използвай ORM

```python
# ❌ НЕ - raw SQL
await db.execute(f"SELECT * FROM users WHERE email = '{email}'")

# ✅ ДА - ORM parameter binding
await db.execute(select(User).where(User.email == email))
```

---

## 19. Repository Pattern & GraphQL Mutations

### 19.1 Структура

```
backend/crud/repositories/
├── __init__.py           # Експортира всички repositories
├── base.py             # BaseRepository с основни CRUD методи
├── user_repo.py        # UserRepository
├── company_repo.py    # CompanyRepository
├── time_repo.py       # TimeTrackingRepository
├── payroll_repo.py    # PayrollRepository
├── trz_repo.py       # TRZRepository
├── production_repo.py # ProductionRepository
├── warehouse_repo.py # WarehouseRepository
├── access_repo.py    # AccessRepository
├── settings_repo.py   # SettingsRepository
└── vehicle_repo.py   # VehicleRepository
```

### 18.2 Импорт и използване

```python
# ❌ НЕ - директен import от crud
from backend import crud
await crud.create_user(db, ...)

# ✅ ДА - от repositories
from backend.crud.repositories import user_repo, time_repo, settings_repo, vehicle_repo

# Използване:
await user_repo.create_user(db, user_data=..., role_id=1)
await time_repo.create_shift(db, name="Сутрешна", ...)
await settings_repo.set_setting(db, key="smtp_server", value="smtp.example.com")
```

### 18.3 Правила за Strawberry mutations

**Подредба на параметрите:**
```python
# ❌ НЕ - optional параметри преди info
async def my_mutation(
    self,
    optional_param: str = None,  # ❌ Грешно
    info: strawberry.Info
):

# ✅ ДА - info ПЪРВО, после optional
async def my_mutation(
    self,
    info: strawberry.Info,
    required_param: int,           # Задължителни първо
    optional_param: str = None   # Optional след това
):
```

**Mutation имена:**
```python
# Когато GraphQL името се различава от Python функцията
@strawberry.mutation(name="requestLeave")  # GraphQL име
async def create_leave_request(...):       # Python име

@strawberry.mutation(name="approveLeave")
async def approve_leave(...):

@strawberry.mutation(name="rejectLeave")
async def reject_leave(...):
```

### 19.4 Мигрирани Mutations

| GraphQL функция | Repository | Бележки |
|---------------|-----------|---------|
| `requestLeave` | - | Директен model |
| `approveLeave` | `time_repo.update_leave_request_status` | |
| `rejectLeave` | `time_repo.update_leave_request_status` | |
| `createCompany` | `company_repo.create_company` | |
| `updateCompany` | `company_repo.update_company` | |
| `createDepartment` | `company_repo.create_department` | |
| `createPosition` | `company_repo.create_position` | |
| `deletePosition` | `company_repo.delete_position` | |
| `createShift` | `time_repo.create_shift` | |
| `updateShift` | `time_repo.update_shift` | |
| `deleteShift` | `time_repo.delete_shift` | |
| `createRole` | `time_repo.create_role` | |
| `deleteRole` | `time_repo.delete_role` | |
| `createScheduleTemplate` | `time_repo.create_schedule_template` | |
| `deleteScheduleTemplate` | `time_repo.delete_schedule_template` | |
| `updateLeaveRequestStatus` | `time_repo.update_leave_request_status` | |
| `deleteLeaveRequest` | `time_repo.delete_leave_request` | |
| `setWorkSchedule` | `time_repo.create_or_update_schedule` | |
| `deleteWorkSchedule` | `time_repo.delete_schedule` | |
| `bulkSetSchedule` | `time_repo.create_bulk_schedules` | |
| `createVehicle` | `vehicle_repo.create_vehicle` | |
| `updateVehicle` | `vehicle_repo.update_vehicle` | |
| `deleteVehicle` | `vehicle_repo.delete_vehicle` | |
| `createVehicleMileage` | `vehicle_repo.create_vehicle_mileage` | |
| `updateVehicleMileage` | `vehicle_repo.update_vehicle_mileage` | |
| `createVehicleFuel` | `vehicle_repo.create_vehicle_fuel` | |
| `updateVehicleFuel` | `vehicle_repo.update_vehicle_fuel` | |
| `createVehicleRepair` | `vehicle_repo.create_vehicle_repair` | |
| `updateVehicleRepair` | `vehicle_repo.update_vehicle_repair` | |
| `createVehicleInsurance` | `vehicle_repo.create_vehicle_insurance` | |
| `updateVehicleInsurance` | `vehicle_repo.update_vehicle_insurance` | |
| `createVehicleInspection` | `vehicle_repo.create_vehicle_inspection` | |
| `updateVehicleInspection` | `vehicle_repo.update_vehicle_inspection` | |
| `createVehicleDriver` | `vehicle_repo.create_vehicle_driver` | |
| `updateVehicleDriver` | `vehicle_repo.update_vehicle_driver` | |
| `createVehicleTrip` | `vehicle_repo.create_vehicle_trip` | |
| `updateVehicleTrip` | `vehicle_repo.update_vehicle_trip` | |
| `invalidateSession` | `user_repo.invalidate_user_session` | |
| `setGlobalSetting` | `settings_repo.set_setting` | |
| SMTP настройки | `settings_repo.set_setting` | |
| Payroll настройки | `settings_repo.set_setting` | |
| Office location | `settings_repo.set_setting` | |
| Password settings | `settings_repo.set_setting` | |
| Security config | `settings_repo.set_setting` | |

### 19.5 GraphQL Queries миграции

| Query | Repository |
|-------|----------|
| `activeTimeLog` | `time_repo.get_active_timelog` |
| `shifts` | `time_repo.get_all_shifts` |
| `role` | `time_repo.get_role_by_id` |
| `roles` | `time_repo.get_all_roles` |
| `workSchedules` | `time_repo.get_schedules_by_period` |
| `myLeaveRequests` | `time_repo.get_leave_requests` |
| `pendingLeaveRequests` | `time_repo.get_leave_requests` |
| `allLeaveRequests` | `time_repo.get_leave_requests` |
| `smtpSettings` | `settings_repo.get_setting` |
| `officeLocation` | `settings_repo.get_setting` |
| `passwordSettings` | `settings_repo.get_setting` |
| `kioskSettings` | `settings_repo.get_setting` |
| `activeSessions` | `user_repo.get_active_sessions` |
| `payrollLegalSettings` | `settings_repo.get_setting` |
| `vapidPublicKey` | `settings_repo.get_setting` |
