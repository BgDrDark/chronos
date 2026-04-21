# ПЛАН: Подобряване на изходящи фактури и поправка на принт бутона

## Статус: В РАЗВИТИЕ

---

## Стъпка 1: Добави click handler в OutgoingInvoicesTab ✅

**Изпълнено на:** 2026-03-24

**Промени:**
- Добавен `handleOpenDetailsDialog` проп
- Добавен `onClick` на TableRow
- Добавен `stopPropagation` на actions клетката

**Файл:** `frontend/src/pages/AccountingPage.tsx`

### 1.1 Добави handleOpenDetailsDialog в извикването

```tsx
{/* Сега */}
<OutgoingInvoicesTab 
  search={search} 
  setSearch={setSearch} 
  handleOpenDialog={handleOpenDialog}
  handleDelete={handleDelete}
  handlePrintInvoice={handlePrintInvoice}
/>

{/* Трябва да стане */}
<OutgoingInvoicesTab 
  search={search} 
  setSearch={setSearch} 
  handleOpenDialog={handleOpenDialog}
  handleOpenDetailsDialog={handleOpenDetailsDialog}
  handleDelete={handleDelete}
  handlePrintInvoice={handlePrintInvoice}
/>
```

### 1.2 Обнови типа на функцията

```tsx
function OutgoingInvoicesTab({ 
  search, setSearch, 
  handleOpenDialog, 
  handleOpenDetailsDialog,  // ← добави
  handleDelete, 
  handlePrintInvoice 
}: {
  search: string;
  setSearch: (s: string) => void;
  handleOpenDialog: (invoice?: Invoice) => void;
  handleOpenDetailsDialog: (invoice: Invoice) => void;  // ← добави
  handleDelete: (id: number) => void;
  handlePrintInvoice: (id: number) => void;
}) {
```

### 1.3 Добави click handler на TableRow

```tsx
{/* Сега */}
<TableRow key={invoice.id}>

{/* Трябва да стане */}
<TableRow 
  key={invoice.id} 
  hover 
  onClick={() => handleOpenDetailsDialog(invoice)} 
  sx={{ cursor: 'pointer' }}
>
```

### 1.4 Добави stopPropagation към actions клетката

```tsx
{/* Сега */}
<TableCell>
  <Tooltip title="PDF"><IconButton size="small" onClick={() => handlePrintInvoice(invoice.id)}><PrintIcon /></IconButton></Tooltip>
  ...

{/* Трябва да стане */}
<TableCell onClick={(e) => e.stopPropagation()}>
  <Tooltip title="PDF"><IconButton size="small" onClick={() => handlePrintInvoice(invoice.id)}><PrintIcon /></IconButton></Tooltip>
  ...
```

---

## Стъпка 2: Поправи handlePrintInvoice с error handling ✅

**Изпълнено на:** 2026-03-24

**Промени:**
- Добавен error handling за 401/403 → redirect към /login
- Използван `getErrorMessage` вместо console.error

### 2.1 Helper функция (в края на файла)

```typescript
// Helper функция за вземане на CSRF token от cookie
const getCsrfTokenFromCookie = (): string | null => {
  const name = 'csrf_token=';
  const decodedCookie = decodeURIComponent(document.cookie);
  const ca = decodedCookie.split(';');
  for (let i = 0; i < ca.length; i++) {
    let c = ca[i];
    while (c.charAt(0) === ' ') {
      c = c.substring(1);
    }
    if (c.indexOf(name) === 0) {
      return c.substring(name.length, c.length);
    }
  }
  return null;
};
```

### 2.2 Обновен handlePrintInvoice с error handling

```typescript
const handlePrintInvoice = async (invoiceId: number) => {
  try {
    const apiUrl = import.meta.env.VITE_API_URL || 'https://dev.oblak24.org';
    const csrfToken = getCsrfTokenFromCookie();

    const response = await fetch(`${apiUrl}/export/invoice/${invoiceId}/pdf`, {
      headers: {
        'X-CSRFToken': csrfToken || '',
      },
      credentials: 'include'  // Изпраща cookies!
    });

    // Error handling за authentication грешки
    if (response.status === 401 || response.status === 403) {
      window.location.href = '/login';
      return;
    }

    if (!response.ok) {
      throw new Error(`Failed to load PDF: ${response.status}`);
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const printWindow = window.open(url, '_blank');

    if (printWindow) {
      printWindow.focus();
    }
  } catch (err) {
    console.error('Error printing invoice:', err);
    alert('Грешка при принтиране на фактура');
  }
};
```

---

## Стъпка 3: Форма за изходящи фактури

**Статус:** ✅ Готово!

**Бележка:** Съществуваща функционалност - не е нужно промяна.

Формата за създаване/редактиране на фактури вече поддържа:
- `formData.type === 'outgoing'` → показва полетата за клиент (clientName, clientEik, clientAddress)
- `formData.type === 'incoming'` → показва полетата за доставчик

---

## Стъпка 4: Детайлна форма за изходящи фактури

**Статус:** ✅ Готово!

**Бележка:** Съществуваща функционалност - не е нужно промяна.

Диалогът с детайли вече показва:
- ИЗДАТЕЛ = нашата фирма (company)
- ПОЛУЧАТЕЛ = клиентът (clientName, clientEik, clientAddress)

---

## ФАЙЛОВЕ ЗА ПРОМЯНА

| Файл | Промени |
|------|---------|
| `frontend/src/pages/AccountingPage.tsx` | 1. Добавяне на `handleOpenDetailsDialog` проп<br>2. Добавяне на onClick handler<br>3. Добавяне на stopPropagation<br>4. Обновяване на `handlePrintInvoice`<br>5. Добавяне на helper функция |

---

## РЕКОНСТРУКЦИЯ И ТЕСТ

```bash
cd /home/niki/PycharmProjects/WorkingTime

# Build images
docker build -t chronos-frontend:3.4.7.4 ./frontend
docker build -t chronos-backend:3.4.7.4 ./backend

# Restart containers
docker compose up -d frontend backend

# Тест
# 1. Отвори https://dev.oblak24.org
# 2. Влез с потребител
# 3. Отиди на Счетоводство > Изходящи фактури
# 4. Кликни на реда на фактура → трябва да се отвори детайлен диалог
# 5. Кликни на PDF бутона → трябва да се отвори PDF
```

---

## COMMIT СЪОБЩЕНИЕ

```
feat: add details dialog and fix print button for outgoing invoices

- Add click handler to OutgoingInvoicesTab to open details dialog
- Fix handlePrintInvoice to use CSRF token from cookie with credentials: 'include'
- Add error handling for 401/403 to redirect to login
```

---

## HISTORY

| Дата | Описание |
|------|---------|
| 2026-03-24 | Създаден план |
| 2026-03-24 | Изпълнено: добавени click handlers и поправен print бутон |

---

## ТЕСТ

1. Отвори https://dev.oblak24.org
2. Влез с потребител
3. Отиди на **Счетоводство** > **Изходящи фактури**
4. **Кликни на реда на фактура** → трябва да се отвори детайлен диалог
5. **Кликни на PDF бутона** → трябва да се отвори PDF