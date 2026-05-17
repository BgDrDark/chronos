# Maintenance Mode Plan

## Концепция

### Flow

**1. Насрочване (Super Admin)**
- Super admin задава: причина + забавяне (минути)
- Пример: "Ъпгрейд на базата" след 60 мин

**2. Countdown фаза (всички потребители)**
- Логнатите потребители виждат **жълт банър** в горната част:
  > ⚠️ Системата ще премине в режим поддръжка след **45 мин.**
  > Причина: "Ъпгрейд на базата данни"

**3. Активация (когато настъпи времето)**
- **Логнати потребители (не-admin)** → автоматичен logout → пренасочване към login страницата
- **Нови login опити (не-admin)** → блокирани със съобщение:
  > 🔧 Системата е в режим поддръжка
  > Причина: "Ъпгрейд на базата данни"
  > Моля, опитайте по-късно.
- **Super Admin** → може да се логва и работи нормално

**4. Деактивация (Super Admin)**
- Super admin изключва maintenance mode → всички потребители могат да се логват отново

---

## Технически детайли

| Компонент | Детайл |
|-----------|--------|
| **DB** | Нова таблица `maintenance_settings` (enabled, scheduled_at, reason, updated_by) |
| **Migration** | Alembic migration за създаване на таблицата |
| **Background job** | APScheduler на 1 мин → проверява `enabled=True` + `scheduled_at <= now` → активира |
| **Login block** | `/auth/token` endpoint → проверява maintenance → block non-admin с message |
| **Auto-logout** | GraphQL middleware → ако maintenance active → връща error → frontend logout |
| **Frontend polling** | MainLayout → `maintenanceStatus` query на 10 сек → показва банър/overlay |
| **Admin UI** | Settings страница → секция "Режим поддръжка" с toggle, reason, delay |

---

## Стъпки за имплементация

### 1. Backend - DB Model
- Нова таблица `maintenance_settings` в `models.py`

### 2. Backend - Alembic Migration
- Създаване на таблицата

### 3. Backend - GraphQL Types & Inputs
- `MaintenanceStatus` type
- `MaintenanceInput` input
- `MaintenanceStatusResponse` type

### 4. Backend - GraphQL Query & Mutation
- `maintenanceStatus` query
- `scheduleMaintenance` mutation
- `cancelMaintenance` mutation

### 5. Backend - Auth Integration
- `/auth/token` → проверка дали maintenance е active → block non-admin
- `get_current_user` → ако maintenance active и user не е super_admin → raise exception

### 6. Backend - Background Job
- APScheduler job на 1 мин → проверява `enabled=True` + `scheduled_at <= now` → активира

### 7. Frontend - GraphQL Queries
- `GET_MAINTENANCE_STATUS` query
- `SCHEDULE_MAINTENANCE` mutation
- `CANCEL_MAINTENANCE` mutation

### 8. Frontend - MainLayout Global Polling
- `useQuery(maintenanceStatus, { pollInterval: 10000 })`
- При `scheduledAt` → жълт банър с countdown
- При `enabled = true` и user не е admin → червен full-screen overlay + auto-logout

### 9. Frontend - Settings Page Admin UI
- Нова секция "Режим поддръжка"
- Toggle ON/OFF
- Textarea за причина
- Number input за забавяне (минути, 0 = веднага)
- Показва текущ статус + countdown ако е насрочено
- Бутон "Отмени" при насрочен maintenance

---

## DB Schema

```sql
CREATE TABLE maintenance_settings (
    id SERIAL PRIMARY KEY,
    enabled BOOLEAN NOT NULL DEFAULT FALSE,
    scheduled_at TIMESTAMP WITHOUT TIME ZONE,
    reason TEXT NOT NULL DEFAULT '',
    updated_by INTEGER REFERENCES users(id),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);
```

---

## GraphQL Schema

```graphql
type MaintenanceStatus {
  enabled: Boolean!
  scheduledAt: DateTime
  reason: String!
  minutesUntil: Int
  updatedBy: User
}

input MaintenanceInput {
  enabled: Boolean!
  delayMinutes: Int!
  reason: String!
}

type Query {
  maintenanceStatus: MaintenanceStatus!
}

type Mutation {
  scheduleMaintenance(input: MaintenanceInput!): Boolean!
  cancelMaintenance: Boolean!
}
```
