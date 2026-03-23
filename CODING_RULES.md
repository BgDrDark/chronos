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

### Error Handling
```python
# ❌ НЕ - използвай raise Exception
raise Exception("Грешка")

# ✅ ДА - използвай helpers от error_handling.py
from backend.utils.error_handling import bad_request, not_found, permission_denied

raise not_found("Рецептата не е намерена")
raise bad_request("Невалидни данни")
raise permission_denied("Нямате права")
```

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

---

## 4. Парични стойности (Decimal)

### Backend
```python
# ❌ НЕ - използвай float за пари
price = 19.99
total = subtotal * 0.2

# ✅ ДА - използвай Decimal за парични стойности
from decimal import Decimal

price = Decimal("19.99")
total = subtotal * Decimal("0.2")
```

### Frontend
```typescript
// Винаги форматирай Decimal стойности
const formatPrice = (value: number | string | null | undefined): string => {
  if (value === null || value === undefined) return '-';
  const num = typeof value === 'string' ? parseFloat(value) : Number(value);
  if (isNaN(num)) return '-';
  return num.toFixed(2) + ' лв.';
};
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

// ✅ ДА - създай helper функция
const formatPrice = (value: number | string | null | undefined): string => {
  if (value === null || value === undefined) return '-';
  const num = typeof value === 'string' ? parseFloat(value) : Number(value);
  if (isNaN(num)) return '-';
  return num.toFixed(2) + ' лв.';
};
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
- Премахвай technical debt

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
