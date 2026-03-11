# Production Terminal - Имплементационен План

## Преглед

Този документ описва пълната имплементация на **Production Terminal** - терминал за производствения цех, който позволява на служителите да се идентифицират, да избират работна станция и да изпълняват производствени задачи.

---

## 1. Поток (User Flow)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PRODUCTION TERMINAL - USER FLOW                         │
├─────────────────────────────────────────────────────────────────────────────┤
│  🚪 (top-right corner - always visible)                                    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  1. ИДЕНТИФИКАЦИЯ                                                  │   │
│  │     📷 Сканирай QR                                                  │   │
│  │     └─► POST /terminal/identify -> Return employee                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  2. ПОТВЪРДЖЕНЕ                                                    │   │
│  │     👤 Здравей, {Име}!                                             │   │
│  │     └─► GET /terminal/workstations                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  3. ИЗБОР НА СТАНЦИЯ                                              │   │
│  │     📋 Списък workstations                                         │   │
│  │     └─► GET /terminal/workstations/{id}/orders                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  4. ЗАДАЧИ ЗА {СТАНЦИЯ}                                          │   │
│  │     ┌─────────────────────────────────────────────────────────┐   │   │
│  │     │ 🔵 Задача #1 - 10 бр                                    │   │   │
│  │     │ 🔵 Задача #2 - 5 бр                                     │   │   │
│  │     │ 🔵 Задача #3 - 20 бр                                    │   │   │
│  │     └─────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  5. РЕЦЕПТА ЗА {ПРОДУКТ}                                        │   │
│  │     ┌─────────────────────────────────────────────────────────┐   │   │
│  │     │ Стъпка 1: Разтопяне... ✅                               │   │   │
│  │     │ Стъпка 2: Добавяне... ⏳                               │   │   │
│  │     │ Стъпка 3: Бъркане...                                     │   │   │
│  │     │ ──────────────────────────────────────────             │   │   │
│  │     │ [▶️ СТАРТ]  [📦 БРАК]  [🚪 ИЗХОД]                   │   │   │
│  │     └─────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  6. В ПРОЦЕС                                                       │   │
│  │     ┌─────────────────────────────────────────────────────────┐   │   │
│  │     │ ⏳ Стъпка 1: Разтопяне... ✅                           │   │   │
│  │     │ ⏳ Стъпка 2: Добавяне... ✅                            │   │   │
│  │     │ ⏳ Стъпка 3: Бъркане... ✅                             │   │   │
│  │     │ ──────────────────────────────────────────             │   │   │
│  │     │ [📦 БРАК]        [✅ ЗАВЪРШИ]        [🚪 ИЗХОД]     │   │   │
│  │     │   ↑                                                     │   │   │
│  │     │   └─ горния ляв ъгъл                                    │   │   │
│  │     └─────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. База Данни

### 2.1 terminal_sessions

Следи кой служител на коя станция работи.

```python
class TerminalSession(Base):
    __tablename__ = "terminal_sessions"
    
    id = Column(Integer, primary_key=True)
    terminal_id = Column(String(100))  # Hardware UUID на терминала
    employee_id = Column(Integer, ForeignKey("users.id"))
    workstation_id = Column(Integer, ForeignKey("workstations.id"))
    
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    
    gateway_id = Column(Integer, ForeignKey("gateways.id"), nullable=True)
    
    # Relations
    employee = relationship("User")
    workstation = relationship("Workstation")
    task_logs = relationship("ProductionTaskLog", back_populates="session")
```

### 2.2 production_task_logs

Логове за изпълнението на задачите.

```python
class ProductionTaskLog(Base):
    __tablename__ = "production_task_logs"
    
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("terminal_sessions.id"))
    production_order_id = Column(Integer, ForeignKey("production_orders.id"))
    production_task_id = Column(Integer, ForeignKey("production_tasks.id"))
    
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    quantity_produced = Column(Integer, default=0)
    scrap_quantity = Column(Integer, default=0)
    
    status = Column(String(20))  # "in_progress", "completed"
    
    # Relations
    session = relationship("TerminalSession", back_populates="task_logs")
    production_order = relationship("ProductionOrder")
    production_task = relationship("ProductionTask")
```

---

## 3. API Endpoints

### 3.1 Terminal Authentication

| Endpoint | Method | Description |
|---------|--------|-------------|
| `/terminal/identify` | POST | Идентификация с QR код |
| `/terminal/session/start` | POST | Старт на сесия (избор станция) |
| `/terminal/session/end` | POST | край на сесия |
| `/terminal/status` | GET | Текуща сесия на терминала |

### 3.2 Workstations & Orders

| Endpoint | Method | Description |
|---------|--------|-------------|
| `/terminal/workstations` | GET | Списък всички станции |
| `/terminal/orders` | GET | Поръчки за станция |
| `/terminal/tasks` | GET | Задачи за поръчка |

### 3.3 Task Execution

| Endpoint | Method | Description |
|---------|--------|-------------|
| `/terminal/task/start` | POST | Старт на задача |
| `/terminal/task/complete` | POST | Завършване (+ quantity) |
| `/terminal/task/scrap` | POST | Добавяне на брак |

### 3.4 Real-time

| Endpoint | Method | Description |
|---------|--------|-------------|
| `/ws/orders` | WebSocket | Real-time ъпдейти за всички терминали |

---

## 4. Gateway

Gateway-ът проксира всички заявки от терминалите към бекенда.

### 4.1 Terminal Hub Endpoints

```
POST /terminal/identify      -> Backend /terminal/identify
GET  /terminal/workstations -> Backend /terminal/workstations
GET  /terminal/orders       -> Backend /terminal/orders
POST /terminal/session/start -> Backend /terminal/session/start
POST /terminal/session/end   -> Backend /terminal/session/end
POST /terminal/task/start   -> Backend /terminal/task/start
POST /terminal/task/complete -> Backend /terminal/task/complete
POST /terminal/task/scrap   -> Backend /terminal/task/scrap
POST /terminal/print-label  -> Local print
WS   /ws/orders            -> Real-time updates
```

### 4.2 Configuration

```yaml
gateway:
  mode: "production"  # kiosk or production
```

---

## 5. PWA Терминал

Production Kiosk страницата (/production-kiosk) ще бъде актуализирана с новия flow.

### 5.1 Компоненти

1. **TerminalLogin** - Сканиране на QR
2. **WorkstationSelector** - Избор на станция
3. **OrderList** - Списък с поръчки
4. **RecipeView** - Рецепта със стъпките
5. **TaskExecution** - Изпълнение на задача
6. **Header** - Бутон ИЗХОД (винаги видим)

### 5.2 State Management

```typescript
interface TerminalState {
  employee: User | null;
  workstation: Workstation | null;
  session: TerminalSession | null;
  currentOrder: ProductionOrder | null;
  currentTask: ProductionTask | null;
  taskStatus: 'idle' | 'in_progress' | 'completed';
}
```

---

## 6. Real-time Updates

Всички терминали ще получават ъпдейти когато:

- Поръчка бъде маркирана като завършена
- Поръчка бъде променена
- Нова поръчка бъде създадена

### WebSocket Message Format

```json
{
  "type": "order_updated",
  "data": {
    "order_id": 123,
    "status": "completed",
    "completed_by": "Иван Иванов",
    "completed_at": "2026-02-19T12:00:00Z"
  }
}
```

---

## 7. Имплементационни Стъпки

| Стъпка | Описание | Приоритет |
|--------|----------|-----------|
| 1 | Създаване на таблици terminal_sessions, production_task_logs | Висок |
| 2 | Backend API endpoints за terminal | Висок |
| 3 | Gateway terminal endpoints | Висок |
| 4 | PWA - Terminal Login | Висок |
| 5 | PWA - Workstation Selection | Висок |
| 6 | PWA - Order/Task List | Висок |
| 7 | PWA - Recipe View | Висок |
| 8 | PWA - Task Execution (+scrap) | Висок |
| 9 | Real-time WebSocket | Среден |
| 10 | Testing | Среден |

---

## 8. Забележки

- Всички времена са в UTC ( Europe/Sofia за display)
- QR формат: `{user_id}:{dynamic_token}`
- Gateway работи в mode "production"
- Терминалите получават real-time ъпдейти през WebSocket
