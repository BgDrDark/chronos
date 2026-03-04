# Chronos Gateway - Система за контрол на достъп

## ПЛАН ЗА ИМПЛЕМЕНТАЦИЯ

**Версия:** 1.0  
**Дата:** 2026-03-01  
**Статус:** Очаква имплементация

---

## СЪДЪРЖАНИЕ

1. [Общ преглед](#1-общ-преглед)
2. [Конфигурация](#2-конфигурация)
3. [Хардуерна поддръжка](#3-хардуерна-поддръжка)
4. [Управление на зони](#4-управление-на-зони)
5. [Anti-Passback](#5-anti-passback)
6. [Еднократни кодове](#6-еднократни-кодове)
7. [API Endpoints](#7-api-endpoints)
8. [Уеб интерфейс](#8-уеб-интерфейс)
9. [Интеграция с терминали](#9-интеграция-с-терминали)
10. [Синхронизация с Backend](#10-синхронизация-с-backend)
11. [Стъпки за имплементация](#11-стъпки-за-имплементация)

---

## 1. ОБЩ ПРЕГЛЕД

### Архитектура

```
┌────────────────────────────────────────────────────────────────────────┐
│                         GATEWAY (локално)                              │
│                                                                        │
│  ┌──────────────┐  ┌────────────────┐  ┌──────────────────────────┐   │
│  │  Access     │  │  Zone         │  │  SR201                  │   │
│  │  Controller │──│  Manager      │──│  Controller             │   │
│  │              │  │  (hierarchical)│  │  (TCP port 6722)        │   │
│  └──────────────┘  └────────────────┘  └──────────────────────────┘   │
│         │                   │                     │                    │
│         │                   ▼                     │                    │
│         │          ┌────────────────┐           │                    │
│         │          │  Zone State    │           │                    │
│         │          │  (who is in    │           │                    │
│         │          │   which zone)  │           │                    │
│         │          └────────────────┘           │                    │
│         │                                     │                    │
│         └─────────────┬───────────────────────┘                    │
│                       ▼                                                │
│              ┌────────────────┐                                       │
│              │  Access Logs   │  ◄─────── sync to backend             │
│              │  (local +     │                                       │
│              │   synced)     │                                       │
│              └────────────────┘                                       │
└────────────────────────────────────────────────────────────────────────┘
```

### Поддържани хардуерни устройства

| Устройство | Канали | Протокол | Порт |
|------------|--------|----------|------|
| SR201 Ethernet Relay | 2 | TCP | 6722 |

---

## 2. КОНФИГУРАЦИЯ

### config.yaml структура

```yaml
# Контрол на достъп
access_control:
  # Глобални настройки
  enabled: true
  auto_reset_time: "23:00"        # Автоматичен ресет на потребителите
  auto_reset_enabled: true        # Дали автоматичният ресет е активен
  
  # Anti-Passback настройки по подразбиране
  anti_passback:
    enabled: false
    default_type: "soft"         # soft, hard, timed
    timeout_minutes: 5
  
  # Настройки за еднократни кодове
  one_time_codes:
    enabled: true
    prefix: "G"                   # Префикс за генериране
  
  # Зони
  zones:
    - id: "zone_1"
      name: "Главен вход"
      level: 1                   # 1 = главна, 2 = второстепенна, 3 = третостепенна
      depends_on: []             # Списък с zone_id, от които зависи
      required_hours:
        start: "06:00"
        end: "22:00"
      anti_passback:
        enabled: false
        type: "soft"
      description: "2 терминала на входни врати"
      active: true
    
    - id: "zone_2a"
      name: "Склад"
      level: 2
      depends_on: ["zone_1"]
      required_hours:
        start: "08:00"
        end: "18:00"
      anti_passback:
        enabled: true
        type: "hard"
      active: true
    
    - id: "zone_2b"
      name: "Производство"
      level: 2
      depends_on: ["zone_1"]
      required_hours:
        start: "07:00"
        end: "20:00"
      anti_passback:
        enabled: true
        type: "soft"
      active: true
    
    - id: "zone_3"
      name: "Офис"
      level: 3
      depends_on: ["zone_1", "zone_2b"]
      required_hours:
        start: "09:00"
        end: "18:00"
      anti_passback:
        enabled: true
        type: "timed"
        timeout_minutes: 10
      active: true
  
  # Врати
  doors:
    - id: "door_entrance_1"
      name: "Входна врата 1"
      zone_id: "zone_1"
      device_ip: "192.168.1.100"
      relay_number: 1
      terminal_id: "terminal_entrance_1"
      description: "Главна входна врата"
      active: true
    
    - id: "door_entrance_2"
      name: "Входна врата 2"
      zone_id: "zone_1"
      device_ip: "192.168.1.100"
      relay_number: 2
      terminal_id: "terminal_entrance_2"
      active: true
    
    - id: "door_warehouse"
      name: "Складова врата"
      zone_id: "zone_2a"
      device_ip: "192.168.1.101"
      relay_number: 1
      terminal_id: "terminal_warehouse"
      active: true
    
    - id: "door_production"
      name: "Производство врата"
      zone_id: "zone_2b"
      device_ip: "192.168.1.102"
      relay_number: 1
      terminal_id: "terminal_production"
      active: true
  
  # SRAM базирани устройства (SR201)
  hardware:
    devices:
      - id: "sr201_1"
        name: "SR201 Вход"
        ip: "192.168.1.100"
        port: 6722
        type: "sr201"
        active: true
        # Настройки за времето на активация (в милисекунди)
        relay_1_duration: 500  # 0-10000ms
        relay_2_duration: 500  # 0-10000ms
        # Ръчен режим (само за тестове през UI)
        relay_1_manual: false
        relay_2_manual: false
      
      - id: "sr201_2"
        name: "SR201 Склад"
        ip: "192.168.1.101"
        port: 6722
        type: "sr201"
        active: true
        relay_1_duration: 500
        relay_2_duration: 500
        relay_1_manual: false
        relay_2_manual: false
      
      - id: "sr201_3"
        name: "SR201 Производство"
        ip: "192.168.1.102"
        port: 6722
        type: "sr201"
        active: true
        relay_1_duration: 500
        relay_2_duration: 500
        relay_1_manual: false
        relay_2_manual: false
```

**Ограничения:**
- `relay_X_duration`: 0 - 10000 ms (10 секунди)
- При 0ms: само ВКЛ без автоматично ИЗКЛ (изисква ръчно ИЗКЛ)
- Ръчен режим (`relay_X_manual: true`): само за тестове, не за продукция
```

---

## 3. ХАРДУЕРНА ПОДДРЪЖКА

### 3.1 SR201 Ethernet Relay Controller

**Клас:** `SR201Relay`

| Метод | Параметри | Описание |
|-------|-----------|----------|
| `__init__` | device_id, name, ip, port=6722 | Инициализация |
| `trigger` | relay_number, duration_ms=500 | Активира за X милисекунди |
| `on` | relay_number | Включва (затваря) - без auto-off |
| `off` | relay_number | Изключва (отваря) |
| `pulse` | relay_number, duration_ms=500 | ВКЛ → чака → ИЗКЛ |
| `status` | - | Връща статус |

**TCP Команди:**

| Команда | Описание |
|---------|----------|
| `{n}R` | Активира реле n (затваря и отваря автоматично) |
| `{n}ON` | Включва реле n (затваря) - остава ВКЛ |
| `{n}OF` | Изключва реле n (отваря) |
| `0R` | Връща статус |

**Поток при активация (pulse):**

```
1. Gateway изпраща "{n}ON" команда
          │
          ▼
2. Релето е ВКЛ (затворено)
          │
          ▼
3. Gateway чака [relay_X_duration] ms
          │
          ▼
4. Gateway изпраща "{n}OF" команда
          │
          ▼
5. Релето е ИЗКЛ (отворено)
```

**Ограничения:**
- Минимално време: 0ms (изисква ръчно изключване)
- Максимално време: 10000ms (10 секунди)
- Препоръчително: 200-2000ms за врати

**Пример:**

```python
relay = SR201Relay("sr201_1", "Вход", "192.168.1.100", 6722)

# Активира за 500ms (default)
await relay.pulse(1)

# Активира за 1000ms
await relay.pulse(1, duration_ms=1000)

# Ръчно включване (за тестване)
await relay.on(1)

# Ръчно изключване
await relay.off(1)
```

### 3.2 Relay Controller Manager

**Клас:** `RelayController`

```python
class RelayController:
    """Мениджър на всички релета"""
    
    def add_device(self, device_id, name, ip, port, device_type="sr201"):
        """Добавя устройство"""
    
    async def trigger(self, device_id, relay_number, duration=1.0):
        """Активира реле"""
    
    async def on(self, device_id, relay_number):
        """Включва реле"""
    
    async def off(self, device_id, relay_number):
        """Изключва реле"""
    
    def get_all_devices(self):
        """Списък с всички устройства"""
    
    def get_device(self, device_id):
        """Информация за устройство"""
```

---

## 4. УПРАВЛЕНИЕ НА ЗОНИ

### 4.1 Zone State

**Клас:** `ZoneState`

Проследява текущата зона на всеки потребител.

```python
class ZoneState:
    """Проследява зоните на потребителите"""
    
    def check_access(self, user_id, target_zone) -> tuple[bool, str]:
        """
        Проверява дали потребителят има достъп до зоната
        Returns: (allowed, reason)
        """
    
    def enter_zone(self, user_id, zone_id):
        """Потребител влиза в зона"""
    
    def leave_zone(self, user_id, zone_id):
        """Потребител напуска зона"""
    
    def get_user_zones(self, user_id):
        """Връща всички зони на потребителя"""
    
    def reset_user(self, user_id):
        """Ресет на потребител"""
    
    def reset_all(self):
        """Ресет на всички потребители"""
```

### 4.2 Zone Manager

**Клас:** `ZoneManager`

Управлява зоните и техните зависимости.

```python
class ZoneManager:
    """Управление на зоните"""
    
    def add_zone(self, zone_config):
        """Добавя зона"""
    
    def remove_zone(self, zone_id):
        """Премахва зона"""
    
    def update_zone(self, zone_id, zone_config):
        """Обновява зона"""
    
    def get_zone(self, zone_id):
        """Връща зона"""
    
    def get_all_zones(self):
        """Списък със зони"""
    
    def get_zone_by_door(self, door_id):
        """Връща зона по door_id"""
    
    def check_schedule(self, zone_id) -> tuple[bool, str]:
        """Проверява работното време"""
    
    def check_dependencies(self, user_id, zone_id) -> tuple[bool, str]:
        """Проверява зависимостите"""
```

### 4.3 Zone Configuration

```python
@dataclass
class Zone:
    id: str
    name: str
    level: int                    # 1 = главна, 2 = второстепенна, 3 = третостепенна
    depends_on: List[str]        # Списък с zone_id
    required_hours: dict          # {"start": "08:00", "end": "18:00"}
    anti_passback: dict           # {"enabled": true, "type": "hard"}
    description: str
    active: bool = True
```

---

## 5. ANTI-PASSBACK

### 5.1 Типове

| Тип | Поведение при повторно сканиране |
|-----|--------------------------------|
| **Soft** | Предупреждава, но пуска |
| **Hard** | Отказва достъп |
| **Timed** | Отказва за X минути |

### 5.2 Anti-Passback State

**Клас:** `AntiPassbackState`

```python
class AntiPassbackState:
    """Проследява последното сканиране на всеки потребител"""
    
    def check(self, user_id, zone_id, config) -> tuple[bool, str]:
        """
        Проверява anti-passback правилата
        Returns: (allowed, message)
        """
    
    def record(self, user_id, zone_id, scan_type="in"):
        """Записва сканирането"""
    
    def can_exit(self, user_id, zone_id) -> bool:
        """Проверява дали може да излезе"""
    
    def get_last_scan(self, user_id):
        """Връща последното сканиране"""
```

### 5.3 Anti-Passback изход

При изход от зоната:
1. Проверява дали потребителят е влязъл в тази зона
2. Ако не е - предупреждение/отказ
3. Ако е - премахва зоната от списъка

---

## 6. ЕДНОКРАТНИ КОДОВЕ

### 6.1 Code Types

| Тип | Описание |
|-----|----------|
| `one_time` | Еднократно използване |
| `daily` | Валиден за целия ден |
| `guest` | Валиден за X часа |
| `permanent` | Постоян код |

### 6.2 Code Manager

**Клас:** `CodeManager`

```python
class CodeManager:
    """Управление на еднократни кодове"""
    
    def create_code(self, code_config) -> str:
        """Създава нов код"""
        # code_config = {
        #     "type": "one_time",
        #     "zones": ["zone_1", "zone_2a"],
        #     "expires_hours": 24,
        #     "max_uses": 1,
        #     "created_by": "admin"
        # }
    
    def validate_code(self, code, zone_id) -> tuple[bool, str, dict]:
        """
        Валидира кода
        Returns: (valid, message, code_data)
        """
    
    def use_code(self, code, user_id):
        """Отбелязва кода като използван"""
    
    def revoke_code(self, code):
        """Отнема кода"""
    
    def get_codes(self, filters=None):
        """Списък с кодове"""
    
    def generate_code(self, length=6, prefix="") -> str:
        """Генерира случаен код"""
```

### 6.3 Code Configuration

```python
@dataclass
class AccessCode:
    code: str
    code_type: str               # one_time, daily, guest, permanent
    zones: List[str]             # Зони с достъп
    uses_remaining: int          # -1 = неограничено
    expires_at: datetime
    created_by: str
    created_at: datetime
    last_used_at: datetime = None
    active: bool = True
```

---

## 7. API ENDPOINTS

### 7.1 Зони

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/access/zones` | GET | Списък със зони |
| `/access/zones` | POST | Създаване на зона |
| `/access/zones/{id}` | GET | Информация за зона |
| `/access/zones/{id}` | PUT | Редакция на зона |
| `/access/zones/{id}` | DELETE | Изтриване на зона |

### 7.2 Врати

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/access/doors` | GET | Списък с врати |
| `/access/doors` | POST | Добавяне на врата |
| `/access/doors/{id}` | GET | Информация за врата |
| `/access/doors/{id}` | PUT | Редакция на врата |
| `/access/doors/{id}` | DELETE | Изтриване на врата |
| `/access/doors/{id}/trigger` | POST | Ръчно отваряне |

### 7.3 Хардуер

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/access/hardware` | GET | Списък с устройства |
| `/access/hardware` | POST | Добавяне на устройство |
| `/access/hardware/{id}` | PUT | Редакция |
| `/access/hardware/{id}` | DELETE | Премахване |
| `/access/hardware/{id}/test` | POST | Тест на устройство |

### 7.4 Кодове

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/access/codes` | GET | Списък с кодове |
| `/access/codes` | POST | Създаване на код |
| `/access/codes/{code}` | GET | Информация за код |
| `/access/codes/{code}/revoke` | POST | Отнемане на код |
| `/access/codes/generate` | POST | Генериране на код |

### 7.5 Състояние

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/access/state` | GET | Кой потребител в коя зона |
| `/access/state/{user_id}` | GET | Зони на потребител |
| `/access/state/{user_id}/enter` | POST | Ръчен вход |
| `/access/state/{user_id}/exit` | POST | Ръчен изход |
| `/access/state/reset` | POST | Ресет на всички |

### 7.6 Логове

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/access/logs` | GET | Логове за достъп |
| `/access/logs/sync` | POST | Sync към backend |
| `/access/logs/clear` | POST | Изчистване на локални логове |

### 7.7 Сканиране

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/access/scan` | POST | Сканиране + достъп |
| `/access/verify` | POST | Само проверка на достъп |

---

## 8. УЕБ ИНТЕРФЕЙС

### 8.1 Страница "Отдел КД"

```
┌────────────────────────────────────────────────────────────────────────┐
│  Chronos Gateway                                           [Zone Admin]│
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │  КОНТРОЛ НА ДОСТЪП                                            │   │
│  │                                                                │   │
│  │  [Таб: Зони] [Таб: Врати] [Таб: Кодове] [Таб: Логове]        │   │
│  │                                                                │   │
│  │  ────────────────────────────────────────────────────────────  │   │
│  │                                                                │   │
│  │  ЗОНИ:                                                        │   │
│  │  ┌────────────────────────────────────────────────────────┐   │   │
│  │  │ 🟢 Зона 1 - Главен вход           [Level: 1] [●]    │   │   │
│  │  │      └─ Входна врата 1, Входна врата 2               │   │   │
│  │  │      └─ Работно време: 06:00 - 22:00                  │   │   │
│  │  │                                                         │   │   │
│  │  │ 🟠 Зона 2a - Склад                 [Level: 2] [●]    │   │   │
│  │  │      └─ depends_on: Зона 1                            │   │   │
│  │  │      └─ Anti-Passback: Hard                           │   │   │
│  │  │                                                         │   │   │
│  │  │ 🟠 Зона 2b - Производство         [Level: 2] [●]    │   │   │
│  │  │      └─ depends_on: Зона 1                            │   │   │
│  │  │                                                         │   │   │
│  │  │ 🔴 Зона 3 - Офис                   [Level: 3] [●]    │   │   │
│  │  │      └─ depends_on: Зона 1, Зона 2b                   │   │   │
│  │  └────────────────────────────────────────────────────────┘   │   │
│  │                                                                │   │
│  │  [+ Добави зона]  [Настройки]                                  │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                        │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │  АКТИВНИ ПОТРЕБИТЕЛИ В ЗОНИ                                   │   │
│  │  ──────────────────────────────────────────────────────────── │   │
│  │  Потребител   │  Зона         │  Влязъл        │  [Изход]    │   │
│  │  Иван П.     │  Главен вход  │  10:30         │  [Изход]    │   │
│  │  Мария Д.   │  Склад        │  09:15         │  [Изход]    │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                        │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │  ЛОГОВЕ (LIVE)                                    [sync ↓]   │   │
│  │  ──────────────────────────────────────────────────────────── │   │
│  │  Време   │  Потребител │  Зона          │  Резултат       │   │
│  │  10:32   │  Иван П.    │  Главен вход   │  ✓ Влязъл      │   │
│  │  10:30   │  Мария Д.  │  Склад         │  ✓ Влязъл      │   │
│  │  09:45   │  (unknown)  │  Главен вход   │  ✗ Отказано    │   │
│  │  09:15   │  Иван П.    │  Производство  │  ✗ Липсва зона │   │
│  └────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────┘
```

### 8.2 Модал за добавяне на зона

```
┌─────────────────────────────────────┐
│  Добави зона                      │
├─────────────────────────────────────┤
│                                      │
│  ID: [________________]              │
│                                      │
│  Име: [________________]             │
│                                      │
│  Ниво: (●) 1  ( ) 2  ( ) 3         │
│                                      │
│  Зависи от: ☐ Зона 1                │
│             ☐ Зона 2a               │
│             ☐ Зона 2b               │
│                                      │
│  Работно време:                     │
│    От: [08:00]  До: [18:00]         │
│                                      │
│  ☑ Anti-Passback                    │
│     Тип: (●) Soft  ( ) Hard ( ) Timed│
│                                      │
│  Описание: [________________]       │
│                                      │
│  [Отмени]  [Запази]                  │
└─────────────────────────────────────┘
```

### 8.3 Модал за добавяне на врата

```
┌─────────────────────────────────────┐
│  Добави врата                      │
├─────────────────────────────────────┤
│                                      │
│  ID: [________________]              │
│                                      │
│  Име: [________________]             │
│                                      │
│  Зона: [Избери зона ▼]              │
│                                      │
│  SR201 Устройство:                   │
│    IP: [192.168.1.______]            │
│    Реле: (●) 1  ( ) 2               │
│                                      │
│  Terminal ID: [________________]      │
│                                      │
│  [Отмени]  [Запази]                  │
└─────────────────────────────────────┘
```

---

## 9. ИНТЕГРАЦИЯ С ТЕРМИНАЛИ

### 9.1 Терминал конфигурация

```yaml
terminal:
  # Zone на терминала
  access_zone: "zone_1"
  
  # Дали да отваря врата автоматично
  auto_open_door: true
  
  # Дали да позволява изход
  allow_exit: true
  
  # Съобщения при отказ
  denied_messages:
    no_access: "Нямате достъп до тази зона"
    missing_zone: "Първо маркирайте на: {zone_name}"
    outside_hours: "Зоната е активна от {start} до {end}"
    anti_passback: "Вече сте в тази зона"
    anti_passback_exit: "Не сте в тази зона"
```

### 9.2 Поток при сканиране

```
1. Терминал сканира QR код
          │
          ▼
2. Gateway получава /scan или /access/scan
          │
          ▼
3. Ако е еднократен код → проверка
          │
          ▼
4. Намира зоната на терминала
          │
          ▼
5. Проверява работното време
          │
          ▼
6. Проверява зависимостите (zone level)
          │
          ▼
7. Anti-passback проверка (entry)
          │
          ▼
8. Anti-passback проверка (exit) - ако е изход
          │
          ▼
9. Активира SR201 релето
          │
          ▼
10. Записва в зона state
          │
          ▼
11. Записва в Access Log
          │
          ▼
12. Sync-ва към backend
```

### 9.3 Отговор на терминала

```json
{
  "status": "success",
  "message": "Достъп разрешен",
  "zone": "Главен вход",
  "user": "Иван Петров",
  "door_opened": true,
  "current_zones": ["zone_1"]
}
```

```json
{
  "status": "denied",
  "message": "Първо маркирайте на: Главен вход",
  "reason": "missing_dependency",
  "required_zones": ["zone_1"],
  "current_zones": []
}
```

---

## 10. СИНХРОНИЗАЦИЯ С BACKEND

### 10.1 Sync логове

```python
class BackendSync:
    """Синхронизация на логовете с backend"""
    
    def __init__(self, backend_url, api_key):
        self.backend_url = backend_url
        self.api_key = api_key
        self.pending_logs = []
    
    async def sync_logs(self):
        """Синхронизира логовете"""
        
        unsynced = get_unsynced_logs()
        
        for log in unsynced:
            try:
                await self._send_log(log)
                mark_as_synced(log.id)
            except Exception as e:
                logger.error(f"Sync failed: {e}")
    
    async def _send_log(self, log):
        """Изпраща един лог"""
        
        url = f"{self.backend_url}/access/logs"
        headers = {
            "X-Kiosk-Secret": self.api_key,
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=log, headers=headers) as resp:
                return await resp.json()
```

### 10.2 Log структура

```json
{
  "id": "log_123",
  "timestamp": "2026-03-01T10:30:00Z",
  "user_id": "user_456",
  "user_name": "Иван Петров",
  "zone_id": "zone_1",
  "zone_name": "Главен вход",
  "door_id": "door_entrance_1",
  "door_name": "Входна врата 1",
  "action": "enter",
  "result": "granted",
  "reason": "OK",
  "method": "qr_scan",
  "terminal_id": "terminal_entrance_1",
  "synced": false,
  "synced_at": null
}
```

---

## 11. СТЪПКИ ЗА ИМПЛЕМЕНТАЦИЯ

### Етап 1: Хардуерен слой (SR201)

| # | Задача | Файл |
|---|--------|------|
| 1.1 | Създай SR201Relay клас | `gateway/devices/sr201_relay.py` |
| 1.2 | Създай RelayController мениджър | `gateway/devices/relay_controller.py` |
| 1.3 | Добави конфигурация в config.py | `gateway/config.py` |
| 1.4 | Добави device management API | `gateway/server/terminal_hub.py` |

### Етап 2: Zone Management

| # | Задача | Файл |
|---|--------|------|
| 2.1 | Създай ZoneState клас | `gateway/access/zone_state.py` |
| 2.2 | Създай ZoneManager клас | `gateway/access/zone_manager.py` |
| 2.3 | Създай AccessController | `gateway/access/controller.py` |
| 2.4 | Интегрирай в GatewayService | `gateway/main.py` |

### Етап 3: Anti-Passback

| # | Задача | Файл |
|---|--------|------|
| 3.1 | Създай AntiPassbackState клас | `gateway/access/anti_passback.py` |
| 3.2 | Интегрирай в AccessController | `gateway/access/controller.py` |

### Етап 4: Еднократни кодове

| # | Задача | Файл |
|---|--------|------|
| 4.1 | Създай CodeManager клас | `gateway/access/code_manager.py` |
| 4.2 | Добави кодове API endpoints | `gateway/server/terminal_hub.py` |

### Етап 5: API Endpoints

| # | Задача | Файл |
|---|--------|------|
| 5.1 | Добави zones CRUD endpoints | `gateway/server/terminal_hub.py` |
| 5.2 | Добави doors CRUD endpoints | `gateway/server/terminal_hub.py` |
| 5.3 | Добави access/scan endpoint | `gateway/server/terminal_hub.py` |
| 5.4 | Добави access/logs endpoints | `gateway/server/terminal_hub.py` |

### Етап 6: Уеб интерфейс

| # | Задача | Файл |
|---|--------|------|
| 6.1 | Обнови dashboard API | `gateway/server/web_dashboard.py` |
| 6.2 | Добави "Отдел КД" tab в index.html | `static/index.html` |
| 6.3 | Добави JS за зони | `static/index.html` |
| 6.4 | Добави JS за врати | `static/index.html` |
| 6.5 | Добави JS за кодове | `static/index.html` |
| 6.6 | Добави JS за логове | `static/index.html` |

### Етап 7: Интеграция с терминали

| # | Задача | Файл |
|---|--------|------|
| 7.1 | Обнови /scan endpoint да връща door trigger | `gateway/server/terminal_hub.py` |
| 7.2 | Добави access/verify endpoint | `gateway/server/terminal_hub.py` |

### Етап 8: Backend Sync

| # | Задача | Файл |
|---|--------|------|
| 8.1 | Създай BackendSync клас | `gateway/access/sync.py` |
| 8.2 | Добави sync логика | `gateway/access/controller.py` |

---

## ПРИЛОЖЕНИЯ

### А. Примерни конфигурации

#### Зона с анти-passback
```yaml
- id: "zone_warehouse"
  name: "Склад"
  level: 2
  depends_on: ["zone_1"]
  required_hours:
    start: "08:00"
    end: "18:00"
  anti_passback:
    enabled: true
    type: "hard"
  active: true
```

#### Еднократен код
```python
{
  "code": "G123456",
  "type": "one_time",
  "zones": ["zone_1", "zone_2a"],
  "uses_remaining": 1,
  "expires_at": "2026-03-01T20:00:00Z",
  "created_by": "admin",
  "active": true
}
```

### Б. Error кодове

| Код | Съобщение | Описание |
|-----|-----------|----------|
| `OK` | Достъп разрешен | Успешно |
| `DENIED_NO_ACCESS` | Нямате достъп | Няма права |
| `DENIED_MISSING_ZONE` | Липсва {zone} | Не е влязъл в предишна зона |
| `DENIED_OUTSIDE_HOURS` | Извън работно време | Зоната не работи |
| `DENIED_ANTI_PASSBACK` | Вече сте в зоната | Anti-passback |
| `DENIED_NOT_IN_ZONE` | Не сте в зоната | При опит за изход |
| `DENIED_INVALID_CODE` | Невалиден код | Грешен код |
| `DENIED_CODE_USED` | Кодът е използван | Еднократен код |
| `DENIED_CODE_EXPIRED` | Кодът е изтекъл | Кодът е изтекъл |

---

## ИСТОРИЯ НА ВЕРСИИТЕ

| Версия | Дата | Описание |
|--------|------|----------|
| 1.0 | 2026-03-01 | Първоначална версия |

---

*Този документ е създаден като част от проекта Chronos Gateway*
