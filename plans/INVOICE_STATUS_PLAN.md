# ПЛАН: Подобряване на статусите във фактурите

## ЦЕЛ

Подобряване на системата за статуси във фактурите - по-добра визуализация, валидация и защита.

---

## 1. СТАТУСИ ВЪВ ФАКТУРИТЕ

### Налични статуси:

| Статус | Стойност | Описание | Цвят в Chip |
|--------|----------|----------|--------------|
| Чернова | `draft` | Фактурата е в процес на съставяне | `default` (сив) |
| Изпратена | `sent` | Фактурата е изпратена/приета | `info` (син) |
| Платена | `paid` | Фактурата е платена | `success` (зелен) |
| Просрочена | `overdue` | Фактурата е просрочена | `warning` (оранжев) |
| Анулирана | `cancelled` | Фактурата е анулирана | `error` (червен) |

---

## 2. ИДЕНТИФИЦИРАНИ ПРОБЛЕМИ

### Проблем 1: Chip показва английски стойности
**Файл:** `frontend/src/pages/AccountingPage.tsx`

**Преди:**
```tsx
<Chip label={inv.status} color="info" size="small" />
// Показва: "draft", "sent", "paid"
```

**След:**
```tsx
<Chip label={getInvoiceStatusText(inv.status)} color={getInvoiceStatusColor(inv.status)} size="small" />
// Показва: "Чернова", "Изпратена", "Платена"
```

---

### Проблем 2: Липса на валидация за преходи между статуси
**Файл:** `backend/graphql/mutations.py`

**Преди:**
```python
# Приема всякаква стойност без валидация
invoice.status = invoice_data.status
```

**След:**
```python
# Валидира преходите между статуси
ALLOWED_TRANSITIONS = {
    'draft': ['sent', 'paid', 'cancelled'],
    'sent': ['paid', 'cancelled'],
    'paid': ['cancelled'],  # Възможно анулиране
    'overdue': ['paid', 'cancelled'],
    'cancelled': []  # Краен статус
}

def validate_status_transition(current_status, new_status):
    if new_status not in ALLOWED_TRANSITIONS.get(current_status, []):
        raise BadRequest(f"Не може да промените статус от '{current_status}' на '{new_status}'")
```

---

### Проблем 3: Липса на защита при анулиране на платени фактури
**Файл:** `backend/graphql/mutations.py`

**Преди:**
```python
# Позволява анулиране на платени фактури
invoice.status = invoice_data.status
```

**След:**
```python
# Забранява анулиране на платени фактури (освен ако не е super_admin)
if current_status == 'paid' and new_status == 'cancelled':
    if current_user.role.name != "super_admin":
        raise permission_denied("Не можете да анулирате платена фактура. Свържете се с администратор.")
```

---

## 3. ФАЙЛОВЕ ЗА ПРОМЯНА

### Frontend:
| Файл | Промяна |
|------|---------|
| `frontend/src/pages/AccountingPage.tsx` | Добави helper функции за статуси и ги използвай в Chip компонентите |

### Backend:
| Файл | Промяна |
|------|---------|
| `backend/graphql/mutations.py` | Добави валидация за преходи между статуси |
| `backend/graphql/mutations.py` | Добави защита при анулиране на платени фактури |

---

## 4. СТЪПКИ ЗА ИМПЛЕМЕНТАЦИЯ

### Стъпка 1: Подобряване на визуализацията (Frontend)
- [x] Добави `getInvoiceStatusText()` функция
- [x] Добави `getInvoiceStatusColor()` функция
- [x] Замени всички `<Chip label={...status...}>` с новите функции

### Стъпка 2: Валидация на преходи (Backend)
- [x] Добави `ALLOWED_TRANSITIONS` константа
- [x] Добави валидация в `update_invoice` мутацията

### Стъпка 3: Защита при анулиране (Backend)
- [x] Добави проверка за `paid` → `cancelled` преход
- [x] Ограничи до `super_admin` роля

### Стъпка 4: Тестване
- [x] Тествай визуализацията на статусите
- [x] Тествай валидацията на преходите
- [x] Тествай защитата при анулиране

---

## 5. ЗАБЕЛЕЖКИ

### Цветово кодиране:
- 🟢 Зелен (`success`) - Платена - всичко е наред
- 🔵 Син (`info`) - Изпратена - чака плащане
- ⚪ Сив (`default`) - Чернова - в процес
- 🟠 Оранжев (`warning`) - Просрочена - забавено плащане
- 🔴 Червен (`error`) - Анулирана - невалидна

### Бъдещи подобрения:
- [ ] Автоматично маркиране на `overdue` при изтичане на `dueDate`
- [ ] Известия при преминаване в `overdue` статус
- [ ] История на промените на статуса

