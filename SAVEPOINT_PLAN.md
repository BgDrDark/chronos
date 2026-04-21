# ПЛАН: Savepoints за GraphQL Mutations

## ЦЕЛ
Добавяне на `atomic_with_savepoint` в GraphQL mutations за по-добра rollback логика при optional операции (notifications).

## РЕШЕНИЕ
Използване на savepoints за optional операции (notifications) - ако notification fail, data-то остава.

---

## Стъпки за имплементация

### Стъпка 1: clock_in mutation
- [ ] Намери `clock_in` в mutations.py
- [ ] Добави savepoint около notification логиката
- [ ] При fail на notification - timelog остава

### Стъпка 2: clock_out mutation  
- [ ] Намери `clock_out` в mutations.py
- [ ] Добави savepoint около notification логиката

### Стъпка 3: create_manual_time_log mutation
- [ ] Намери `create_manual_time_log` в mutations.py
- [ ] Добави savepoint

### Стъпка 4: create_swap_request mutation
- [ ] Намери `create_swap_request` в mutations.py
- [ ] Добави savepoint за notification

### Стъпка 5: approve_swap mutation
- [ ] Намери `approve_swap` в mutations.py
- [ ] Добави savepoint

### Стъпка 6: apply_schedule_template mutation
- [ ] Намери `apply_schedule_template` в mutations.py
- [ ] Добави savepoint

### Стъпка 7: approve_leave / reject_leave mutations
- [ ] Намери mutations в mutations.py
- [ ] Добави savepoint за notification

### Стъпка 8: add_bonus mutation
- [ ] Намери `add_bonus` в mutations.py
- [ ] Добави savepoint

---

## Пример код

### Преди (без savepoint):
```python
async def clock_in(...):
    async with atomic_transaction(db):
        await create_timelog(...)
        await send_notification(...)  # Ако fail - rollback на всичко
```

### Със savepoint:
```python
async def clock_in(...):
    async from atomic_transaction(db):
        await create_timelog(...)
        async with atomic_with_savepoint(db, "timelog_created"):
            await send_notification(...)  # Ако fail - timelog остава
```

---

## Принцип

| Операция | Savepoint | Защо |
|----------|-----------|------|
| create_timelog | ❌ | Critical - трябва да остане |
| send_notification | ✅ | Optional - не е critical |
| send_push | ✅ | Optional |
| audit_log | ❌ | Важно за debugging |

---

## Тестване

### Тест 1: Savepoint rollback при notification failure
- Създай timelog
- Направи notification да хвърли грешка
- Провери че timelog остава в базата

### Тест 2: Normal operation (without failure)
- Създай timelog с успешен notification
- Провери че всичко е записано

### Тест 3: Nested savepoints
- Тествай множество nested savepoints

---

## Имплементирани mutations (done):
- ✅ clock_in
- ✅ clock_out
- ✅ create_manual_time_log
- ✅ create_swap_request
- ✅ approve_swap
- ✅ apply_schedule_template
- ✅ approve_leave
- ✅ reject_leave
- ✅ add_bonus
- ⏳ Тестване

---

## Бележки
- Notifications не са critical - user-ът иска да знае, но не е блокиращо
- Audit logging може да остане без savepoint
- Да тестваш rollback логиката
