# Chronos Gateway SQLite Синхронизация План

## Общ преглед

Този документ описва плана за имплементация на SQLite бази данни в chronos-gateway за локално запазване и синхронизация с бекенда.

---

## 1. Компоненти за Синхронизация

| Компонент | Локално SQLite | → Бекенд | ← Бекенд |
|----------|---------------|---------|----------|
| Зони | ✅ | ✅ | ✅ |
| Врати | ✅ | ✅ | ✅ |
| SR201 Устройства | ✅ | ✅ | ✅ |
| Терминали | ✅ | ✅ | ✅ |
| Принтери | ✅ | ✅ | ✅ |
| Кодове | ✅ | ❌ | ❌ |
| Логове | ✅ (logs.db) | ✅ | - |

---

## 2. SQLite Бази Данни

### Структура на файловете

```
chronos-gateway/
├── config/
│   ├── config.db    # zones, doors, devices, terminals, printers
│   └── logs.db     # access_logs
```

### config.db - Конфигурация

```sql
-- Devices (SR201)
CREATE TABLE devices (
    id TEXT PRIMARY KEY,
    name TEXT,
    ip TEXT,
    port INTEGER DEFAULT 6722,
    mac_address TEXT,
    relay_1_duration INTEGER DEFAULT 500,
    relay_2_duration INTEGER DEFAULT 500,
    relay_1_manual BOOLEAN DEFAULT FALSE,
    relay_2_manual BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Zones
CREATE TABLE zones (
    id TEXT PRIMARY KEY,
    name TEXT,
    level INTEGER DEFAULT 0,
    depends_on TEXT,
    anti_passback_enabled BOOLEAN DEFAULT FALSE,
    anti_passback_type TEXT DEFAULT 'soft',
    anti_passback_timeout INTEGER DEFAULT 5,
    required_hours_start TEXT,
    required_hours_end TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Doors
CREATE TABLE doors (
    id TEXT PRIMARY KEY,
    name TEXT,
    zone_id TEXT,
    device_id TEXT,
    relay_number INTEGER DEFAULT 1,
    terminal_id TEXT,
    description TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (zone_id) REFERENCES zones(id),
    FOREIGN KEY (device_id) REFERENCES devices(id)
);

-- Terminals
CREATE TABLE terminals (
    id TEXT PRIMARY KEY,
    name TEXT,
    ip_address TEXT,
    device_type TEXT,
    status TEXT DEFAULT 'offline',
    last_seen TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Printers
CREATE TABLE printers (
    id TEXT PRIMARY KEY,
    name TEXT,
    ip_address TEXT,
    port INTEGER DEFAULT 9100,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- One-time codes
CREATE TABLE access_codes (
    code TEXT PRIMARY KEY,
    user_id TEXT,
    used BOOLEAN DEFAULT FALSE,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sync metadata
CREATE TABLE sync_meta (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### logs.db - Логове за Достъп

```sql
CREATE TABLE access_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id TEXT,
    user_name TEXT,
    door_id TEXT,
    door_name TEXT,
    zone_id TEXT,
    zone_name TEXT,
    result TEXT,  -- 'granted', 'denied', 'error'
    reason TEXT,  -- 'OK', 'no_zone', 'not_authorized', etc.
    method TEXT,  -- 'card', 'code', 'rfid', 'manual'
    terminal_id TEXT,
    gateway_id TEXT,
    synced BOOLEAN DEFAULT FALSE
);

-- Indexes
CREATE INDEX idx_access_logs_timestamp ON access_logs(timestamp);
CREATE INDEX idx_access_logs_user ON access_logs(user_id);
CREATE INDEX idx_access_logs_door ON access_logs(door_id);
CREATE INDEX idx_access_logs_synced ON access_logs(synced);
```

---

## 3. Работопоток

```
┌─────────────────────────────────────────────────────────────┐
│                     GATEWAY                                   │
│                                                              │
│  1. Промяна (UI/Add/Edit/Delete)                           │
│         ↓                                                    │
│  2. Запазва в SQLite (config.db)                           │
│         ↓                                                    │
│  3. Пушва към Backend (POST /gateways/{id}/push-config)   │
│         ↓                                                    │
│  4. Ако offline → чака + retry (3 опита)                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. API Ендпоинти

### Backend → Gateway

| Метод | Път | Описание |
|-------|-----|---------|
| GET | `/gateways/{id}/config` | Тегли конфигурацията |
| POST | `/gateways/{id}/push-config` | Пушва конфигурация |

### Gateway → Backend

| Метод | Път | Описание |
|-------|-----|---------|
| POST | `/gateways/{id}/access/sync-logs` | Пушва логове |
| POST | `/gateways/{id}/push-config` | Пушва конфигурацията |

### Gateway Локални

| Метод | Път | Описание |
|-------|-----|---------|
| GET | `/sync/status` | Статус на синхронизацията |
| GET | `/access/logs` | Логове от SQLite |
| POST | `/sync/push` | Ръчно sync |

---

## 5. Конфигурация

### config.yaml

```yaml
sync:
  enabled: true
  interval_minutes: 15        # Конфигурируем
  retry_attempts: 3           # Брой опити при неуспех
  batch_size: 100             # Брой записи на партида
  
backend:
  url: http://localhost:14240
  verify_ssl: false
```

---

## 6. Frontend - Врати

### Страница "Врати"

```
┌─────────────────────────────────────────────────────────────┐
│  Врати                                                    │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ Име          │ Зона    │ Устройство │ Реле │       │ │
│  ├──────────────────────────────────────────────────────┤ │
│  │ Вход          │ Зона 1  │ SR201-1   │ 1    │ [✏️] [🗑️] │ │
│  │ Заден изход   │ Зона 1  │ SR201-1   │ 2    │ [✏️] [🗑️] │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                              │
│  [+ Добави врата]  [Синхронизирай]                         │
└─────────────────────────────────────────────────────────────┘
```

### Действия

- **✏️ Редакция** - Отваря модал за промяна
- **🗑️ Изтрий** - Премахва вратата
- **Отвори** - Активира релето

---

## 7. Задачи за Имплементация

1. [ ] Създай SQLite бази (`config.db`, `logs.db`)
2. [ ] Добави SQLite мениджър в gateway
3. [ ] Промени `zone_manager` да използва SQLite
4. [ ] Промени `relay_controller` да използва SQLite
5. [ ] Добави SyncManager за push/pull
6. [ ] Добави Frontend бутони за врати
7. [ ] Добави push endpoint в web_dashboard.py
8. [ ] Тествай

---

## 8. Retry Логика

```python
async def push_with_retry(data: dict, max_attempts: int = 3):
    """Пушва с retry при неуспех"""
    for attempt in range(max_attempts):
        try:
            await post_to_backend('/gateways/{id}/push-config', data)
            return True  # Успех
        except Exception as e:
            if attempt < max_attempts - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            else:
                log_error(f"Failed after {max_attempts} attempts: {e}")
                return False
    return False
```

---

## 9. Интервали

| Параметьр | Стойност |
|-----------|----------|
| Синхронизация на логове | 15 мин |
| Retry интервал | 2^n секунди (exponential backoff) |
| Max retry опита | 3 |

---

## 10. Статуси

| Статус | Описание |
|--------|----------|
| online | Gateway-ът е свързан |
| offline | Gateway-ът не е свързан |
| syncing | В процес на синхронизация |
| error | Грешка при синхронизация |

---

## 11. Бележки

- Кодовете (one-time codes) не се синхронизират с бекенд - пазят се само локално
- Логовете се запазват локално докато бекендът не потвърди получаване
- Конфигурацията се пушва автоматично при всяка промяна (Add/Edit/Delete)
- Възможност за ръчно sync от Frontend
