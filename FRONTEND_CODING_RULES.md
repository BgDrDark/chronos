# Правила за писане на качествен Frontend код

## 1. Именуване

| Елемент | Стил | Пример |
|---------|------|--------|
| Променливи | camelCase | `userName`, `totalPrice` |
| Функции | camelCase | `handleSavePrice`, `calculateTotal` |
| Компоненти | PascalCase | `UserManagementPage`, `ValidatedTextField` |
| Типове/Интерфейси | PascalCase | `RecipeWithPrice`, `UserDailyStat` |
| GraphQL операции | UPPER_SNAKE_CASE | `GET_RECIPES`, `CREATE_USER` |

### Правила
- Използвай смислени имена: `userCount` вместо `x`
- НЕ използвай съкращения: `handleClick` вместо `handleClk`
- Event handlers: `handleSave`, `onSubmit`, `handleDelete`
- Getters: `getRecipes`, `getInvoiceStatus`

---

## 2. TypeScript правила

### Типизация
```typescript
// ❌ НЕ - използвай any
const data: any = response.json();

// ✅ ДА - използвай конкретни типове
const data: RecipeWithPrice[] = response.data;
```

### Error Handling
```typescript
// ❌ НЕ - console.error
} catch (err) {
  console.error(err);
}

// ✅ ДА - getErrorMessage от types
} catch (err) {
  setError(getErrorMessage(err));
}

// ✅ ДА - ErrorContext
import { useError, extractErrorMessage } from '../context/ErrorContext';

const { showError, showSuccess, showWarning, showInfo } = useError();

try {
  await deleteMutation({ variables: { id } });
  showSuccess('Записът е изтрит успешно');
} catch (error) {
  showError(extractErrorMessage(error));
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
  updateRecipe(input: $input) {
    recipeId    // camelCase
  }
}
```

---

## 3. React/Component правила

### Tooltips
```tsx
// ❌ НЕ - hover tooltips за form field-ове
// ✅ ДА - onClick tooltips за InfoIcon

import { InfoIcon } from '../components/ui/InfoIcon';

<TextField
  slotProps={{
    input: {
      endAdornment: (
        <InputAdornment position="end">
          <InfoIcon helpText="Текст за помощ" />
        </InputAdornment>
      )
    }
  }}
/>

// Hover tooltips остават САМО за бутони и действия
<Tooltip title="Редактирай">
  <IconButton onClick={handleEdit}><EditIcon /></IconButton>
</Tooltip>
```

**Правила за tooltips:**
1. `InputLabelProps={{ shrink: true }}` - САМО за `type="date"` полета
2. Селектите НЯМАТ shrink (label-а плава)
3. Help text-овете са в `fieldsHelpText.ts`

### Централизирани компоненти
```tsx
// ❌ НЕ - повтаряй TextField с валидация
<TextField error={!!errors.name} helperText={errors.name} ... />

// ✅ ДА - използвай ValidatedTextField
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

### Разделяне на компоненти
- Компонент > 200 реда → раздели
- Логика за различни табове/секции → отделни компоненти
- Повтаряща се UI структура → reusable компонент

---

## 4. Форматиране на валута

```typescript
// ✅ ДА - използвай централизирани функции
import { useCurrency, formatCurrencyValue } from '../currencyContext';

const { currency } = useCurrency();
const formatted = formatCurrencyValue(19.99, currency);
// EUR → "19.99 €" | USD → "$19.99" | BGN → "19.99 лв."
```

**Правила:**
- **Винаги** използвай `formatCurrencyValue()`
- **Никога** не пиши hardcoded валутни символи (`лв.`, `€`, `$`)
- За подкомпоненти - дефинирай `formatPrice` локално с `useCurrency()`

---

## 5. Дата формат

```typescript
// ✅ ДА - използвай централизирана функция
import { formatDate } from '../utils/dateUtils';

formatDate('2026-05-02')  // → "02-05-2026" (DD-MM-YYYY)
```

**Правила:**
- Default формат: `DD-MM-YYYY`
- НЕ използвай `toLocaleDateString` директно
- НЕ използвай date-fns (мигрирано към dayjs)

---

## 6. DRY принцип

```tsx
// ❌ НЕ - повтаряй форматиране
const price1 = data.price.toFixed(2) + ' лв.';
const price2 = order.total.toFixed(2) + ' лв.';

// ✅ ДА - централизирана функция
const formatted1 = formatCurrencyValue(data.price, currency);
const formatted2 = formatCurrencyValue(order.total, currency);
```

---

## 7. Функции

- Една функция = едно нещо
- Максимум 30-50 реда
- Ако е по-дълга, раздели на по-малки

---

## 8. Коментари

- Коментирай "защо" не "какво"
- Не коментирай очевидното

```tsx
// ❌ Излишен
// Сумира числата
const total = prices.reduce((a, b) => a + b, 0);

// ✅ Смислен
// FEFO: първо използвай партидите с най-близка годност
const sortedBatches = batches.sort((a, b) => 
  new Date(a.expiryDate).getTime() - new Date(b.expiryDate).getTime()
);
```

---

## 9. Навигация

### Routing
- Всички страници с табове използват `TabbedPage` компонент
- URL-то винаги sync с активния таб
- Parent пътищата redirect-ват към първия таб

```tsx
// ✅ ДА - TabbedPage
<TabbedPage tabs={tabs} defaultTabPath="/admin/users/list">
  {tab === 'list' && <UserList />}
  {tab === 'org-structure' && <OrganizationManager />}
</TabbedPage>
```

### Sidebar
- SidebarMenu използва expand/collapse секции
- Collapsed mode показва само икони с tooltips
- Active state се определя от текущия URL

---

## 10. Тестване

- Пиши тестове за критични функции
- Покрий edge cases
- Тествай error handling
- Използвай Vitest (НЕ Jest)

```typescript
import { describe, it, expect, vi } from 'vitest';

describe('formatCurrencyValue', () => {
  it('formats BGN correctly', () => {
    expect(formatCurrencyValue(19.99, 'BGN')).toBe('19.99 лв.');
  });
});
```

---

## 11. Рефакторинг

- Преглеждай кода редовно
- Подобрявай структурата
- Използвай `// technical debt` за коментари на функциите

---

## 12. Бизнес логика (TypeScript интерфейси)

### Склад (Warehouse)
```typescript
// FEFO - First Expired First Out
interface Batch {
  id: number;
  batchNumber: string;
  expiryDate: string;
  availableStock: number;
  supplier?: Supplier;
}
```

### Фактури (Invoices)
```typescript
const ALLOWED_TRANSITIONS = {
  'draft': ['sent', 'paid', 'cancelled'],
  'sent': ['paid', 'cancelled'],
  'paid': ['cancelled'],     // Само super_admin
  'overdue': ['paid', 'cancelled'],
  'cancelled': []
};
```

### Рецепти (Recipes)
```typescript
type SectionType = 'dough' | 'cream' | 'decoration';
// dough = ПЕКАРНА, cream = КРЕМОВЕ, decoration = ДЕКОРАЦИЯ

// finalPrice = costPrice + (costPrice × markup%) + premiumAmount
```

### Поръчки (Orders)
```typescript
// Статуси: awaiting_stock → ready → in_progress → completed
```

---

## 13. Архитектура

```
frontend/src/
├── components/     # Reusable компоненти
│   ├── ui/         # UI примитиви (InfoIcon, ValidatedTextField)
│   ├── accounting/ # Accounting подкомпоненти
│   └── ...
├── pages/          # Страници
├── graphql/        # GraphQL заявки
├── context/        # React contexts (ErrorContext, CurrencyContext)
├── hooks/          # Custom hooks
├── services/       # API услуги
├── utils/          # Помощни функции (dateUtils)
├── types/          # TypeScript интерфейси (домейн файлове)
├── generated/      # GraphQL Codegen output
└── test/           # Vitest setup
```

---

## 14. Бързи справки

### Helpers
```typescript
import { getErrorMessage } from '../types';
import { formatDate } from '../utils/dateUtils';
import ValidatedTextField from '../components/ui/ValidatedTextField';
import { useCurrency, formatCurrencyValue } from '../currencyContext';
import { useError, extractErrorMessage } from '../context/ErrorContext';
import { TabbedPage } from '../components/TabbedPage';
```

### GraphQL naming map
```
Frontend (camelCase)  →  Backend (snake_case)
────────────────────────────────────────────
recipeId              →  recipe_id
markupPercentage      →  markup_percentage
finalPrice            →  final_price
```

### Технологии
| Технология | Употреба |
|------------|----------|
| React 18 | UI framework |
| TypeScript | Типизация |
| Apollo Client | GraphQL клиент |
| MUI | UI компоненти |
| dayjs | Дата манипулация |
| Vitest | Тестове |
| React Router | Навигация |
| Zod | Validation schemas |

---

## 15. Plan Mode

### Преди имплементация
1. Запиши план във файл с разширение `.md`
2. Опиши какво трябва да се направи
3. Списък със стъпки за изпълнение

### След имплементация
1. Маркирай завършените стъпки с `[x]`
2. Актуализирай плана с направените промени
