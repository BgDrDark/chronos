# ПЛАН ЗА РЕАЛИЗАЦИЯ - ЛОГИСТИКА И АВТОМОДУЛ (FLEET MANAGEMENT)

## Съдържание
1. [Общ преглед](#1-общ-преглед)
2. [Логистика](#2-логистика)
3. [Автомодул / Fleet](#3-автомодул--fleet)
4. [Авто-заявки от склад](#4-авто-заявки-от-склад)
5. [Нотификации](#5-нотификации)
6. [Frontend страници](#6-frontend-страници)
7. [Dashboard](#7-dashboard)
8. [Счетоводство](#8-счетоводство)
9. [Разрешения (RBAC)](#9-разрешения-rbac)
10. [Стъпки за реализация](#10-стъпки-за-реализация)

---

## 1. ОБЩ ПРЕГЛЕД

### Technology Stack
- **Backend**: FastAPI, PostgreSQL, SQLAlchemy, GraphQL (Strawberry)
- **Frontend**: React 19, TypeScript, Material UI, Apollo Client
- **Background Jobs**: APScheduler

---

## 2. ЛОГИСТИКА

### 2.1 Модели

#### Supplier (Доставчици)
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID | PK |
| name | String(255) | Име на фирмата |
| eik | String(20) | ЕИК/БУЛСТАТ |
| mol | String(255) | МОЛ |
| address | String(500) | Адрес |
| phone | String(50) | Телефон |
| email | String(255) | Имейл |
| is_active | Boolean | Активен/неактивен |
| notes | Text | Забележки |
| company_id | UUID | FK → Company |

#### RequestTemplate (Шаблони за заявки)
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID | PK |
| name | String(255) | Име на шаблона |
| items | JSON | Списък с артикули |
| default_department_id | UUID | FK → Department |
| notes | Text | Забележки |
| company_id | UUID | FK → Company |

#### PurchaseRequest (Вътрешни заявки)
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID | PK |
| request_number | String(50) | Номер: AR/PR-YYYY-NNNNN |
| requested_by_id | UUID | FK → User (който иска) |
| department_id | UUID | FK → Department |
| status | Enum | draft, pending, approved, rejected, fulfilled |
| priority | Enum | low, medium, high, urgent |
| reason | Text | Мотивировка |
| due_date | Date | Срок |
| approved_by_id | UUID | FK → User (одобрил) |
| approved_at | DateTime | Кога е одобрена |
| is_auto | Boolean | Автоматично генерирана |
| notes | Text | Забележки |
| company_id | UUID | FK → Company |

#### PurchaseRequestItem (Артикули в заявката)
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID | PK |
| purchase_request_id | UUID | FK |
| item_name | String(255) | Име на артикул |
| quantity | Decimal | Количество |
| unit | String(20) | бр, кг, л, м |
| notes | String(500) | Забележки |

#### PurchaseRequestApproval (История на одобрения)
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID | PK |
| request_id | UUID | FK → PurchaseRequest |
| action | Enum | approved, rejected |
| user_id | UUID | FK → User |
| action_date | DateTime | Кога |
| reason | String | Причина (особено при отказ) |
| is_auto | Boolean | Дали е auto-generated заявка |

#### PurchaseRequestHistory (История на промените)
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID | PK |
| request_id | UUID | FK → PurchaseRequest |
| field_name | String(100) | Име на полето |
| old_value | Text | Стара стойност |
| new_value | Text | Нова стойност |
| changed_by_id | UUID | FK → User |
| changed_at | DateTime | Кога |

#### PurchaseOrder (Покупни поръчки)
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID | PK |
| order_number | String(50) | Номер на поръчка |
| supplier_id | UUID | FK → Supplier |
| purchase_request_id | UUID | FK → PurchaseRequest (опционално) |
| status | Enum | draft, sent, confirmed, partial, received, cancelled |
| order_date | Date | Дата на поръчка |
| expected_date | Date | Очаквана доставка |
| received_date | Date | Получена на |
| total_amount | Decimal | Обща сума |
| vat_amount | Decimal | ДДС |
| notes | Text | Забележки |
| company_id | UUID | FK → Company |

#### PurchaseOrderItem (Артикули в поръчката)
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID | PK |
| purchase_order_id | UUID | FK |
| item_name | String(255) | Име |
| quantity | Decimal | Количество |
| received_quantity | Decimal | Получено количество |
| unit_price | Decimal | Единична цена |
| vat_rate | Decimal | ДДС % |
| unit | String(20) | бр, кг, л, м |

#### Delivery (Доставки)
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID | PK |
| delivery_number | String(50) | Номер |
| purchase_order_id | UUID | FK → PurchaseOrder |
| vehicle_id | UUID | FK → Vehicle |
| driver_id | UUID | FK → User/Driver |
| status | Enum | pending, in_transit, delivered, cancelled |
| shipped_date | DateTime | Дата на изпращане |
| delivery_date | DateTime | Дата на доставка |
| tracking_number | String(100) | Проследяване |
| notes | Text | Забележки |
| company_id | UUID | FK → Company |

### 2.2 Flow

```
Потребител или Авто-Заявка
        │
        ▼
   PurchaseRequest
   (номер: PR/AR-YYYY-NNNNN)
        │
        ▼
   [Одобрение от мениджър]
        │
        ▼
   PurchaseOrder
        │
        ▼
   Delivery (+ Vehicle, Driver)
        │
        ▼
   Inventory (склад)
```

---

## 3. АВТОМОДУЛ / FLEET

### 3.1 Модели

#### VehicleType (Типове автомобили)
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID | PK |
| name | String(100) | Име (леков, камион, бус) |
| code | String(20) | Код |

#### Vehicle (Автомобили)
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID | PK |
| registration_number | String(20) | Рег. номер (уникално) |
| vin | String(50) | VIN номер |
| make | String(100) | Марка |
| model | String(100) | Модел |
| year | Integer | Година на производство |
| vehicle_type_id | UUID | FK → VehicleType |
| fuel_type | Enum | benzin, dizel, electric, hybrid, lng, cng |
| engine_number | String(100) | № двигател |
| chassis_number | String(100) | № рама |
| color | String(50) | Цвят |
| initial_mileage | Integer | Начален километраж |
| is_company | Boolean | Фирмен/личен |
| owner_name | String(255) | Собственик (за лични) |
| status | Enum | active, in_repair, out_of_service, sold |
| notes | Text | Забележки |
| company_id | UUID | FK → Company |

#### VehicleDocument (Документи)
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID | PK |
| vehicle_id | UUID | FK |
| document_type | Enum | invoice, policy, inspection, contract, other |
| title | String(255) | Заглавие |
| file_url | String(500) | Път до файла |
| issue_date | Date | Дата на издаване |
| expiry_date | Date | Дата на изтичане |
| notes | Text | Забележки |

#### VehicleFuelCard (Горивни карти)
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID | PK |
| vehicle_id | UUID | FK |
| card_number | String(50) | Номер на картата |
| provider | String(255) | Доставчик |
| pin | String(10) | ПИН |
| limit | Decimal | Лимит |
| is_active | Boolean | Активна |
| expiry_date | Date | Валидност |

#### VehicleVignette (Е-винетки)
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID | PK |
| vehicle_id | UUID | FK |
| vignette_type | Enum | week, month, year |
| purchase_date | Date | Дата на покупка |
| valid_from | Date | Валидна от |
| valid_until | Date | Валидна до |
| price | Decimal | Цена |
| provider | String(255) | Доставчик |
| document_url | String(500) | Документ |

#### VehicleToll (Тол такси)
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID | PK |
| vehicle_id | UUID | FK |
| route | String(255) | Маршрут |
| toll_amount | Decimal | Сума |
| toll_date | DateTime | Дата |
| section | String(100) | Участък |
| document_url | String(500) | Документ |

#### VehicleMileage (Километраж)
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID | PK |
| vehicle_id | UUID | FK |
| date | Date | Дата |
| mileage | Integer | Километри |
| source | Enum | manual, gps, tacho |
| notes | String(500) | Забележки |

#### VehicleFuel (Гориво)
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID | PK |
| vehicle_id | UUID | FK |
| date | DateTime | Дата/час |
| fuel_type | String(20) | Вид гориво |
| quantity | Decimal | Литри |
| price_per_liter | Decimal | Цена/литър |
| total_amount | Decimal | Обща сума |
| mileage | Integer | Километри при зареждане |
| location | String(255) | Място (газстанция) |
| invoice_number | String(50) | Фактура |
| fuel_card_id | UUID | FK → VehicleFuelCard |
| driver_id | UUID | FK → User |

#### VehicleRepair (Ремонти)
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID | PK |
| vehicle_id | UUID | FK |
| repair_date | DateTime | Дата |
| repair_type | Enum | scheduled, unscheduled, inspection |
| description | Text | Описание |
| parts | JSON | Използвани части |
| labor_hours | Decimal | Работни часове |
| labor_cost | Decimal | Цена труд |
| parts_cost | Decimal | Цена части |
| total_cost | Decimal | Обща цена |
| mileage | Integer | Километри |
| vehicle_service_id | UUID | FK → VehicleService |
| warranty_months | Integer | Гаранция (месеци) |
| next_service_km | Integer | Следващ сервиз (км) |
| notes | Text | Забележки |

#### VehicleService (Сервизи)
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID | PK |
| name | String(255) | Име |
| address | String(500) | Адрес |
| phone | String(50) | Телефон |
| email | String(255) | Имейл |
| contact_person | String(255) | Контакт |
| notes | Text | Забележки |

#### VehicleSchedule (График за поддръжка)
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID | PK |
| vehicle_id | UUID | FK |
| schedule_type | Enum | oil_change, tire_rotation, inspection, general |
| interval_km | Integer | Интервал (км) |
| interval_months | Integer | Интервал (месеци) |
| last_service_date | Date | Последно обслужване |
| last_service_km | Integer | Последно (км) |
| next_service_date | Date | Следващо обслужване |
| next_service_km | Integer | Следващо (км) |
| notes | Text | Забележки |

#### VehicleInsurance (Застраховки)
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID | PK |
| vehicle_id | UUID | FK |
| insurance_type | Enum | civil, kasko, border |
| policy_number | String(50) | № полица |
| insurance_company | String(255) | Застраховател |
| start_date | Date | Начална дата |
| end_date | Date | Крайна дата |
| premium | Decimal | Премия |
| coverage_amount | Decimal | Покритие |
| payment_type | Enum | annual, semi_annual, quarterly |
| document_url | String(500) | Документ |
| notes | Text | Забележки |

#### VehicleInspection (ГТП)
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID | PK |
| vehicle_id | UUID | FK |
| inspection_date | Date | Дата на преглед |
| valid_until | Date | Валиден до |
| result | Enum | passed, failed, pending |
| mileage | Integer | Километри |
| inspector | String(255) | Прегледал |
| certificate_number | String(50) | № протокол |
| next_inspection_date | Date | Следващ преглед |
| notes | Text | Забележки |

#### VehiclePreTripInspection (Инспекция преди път)
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID | PK |
| vehicle_id | UUID | FK |
| driver_id | UUID | FK → User |
| inspection_date | DateTime | Дата/час |
| tires_condition | Boolean | Гуми - OK/Не |
| tires_pressure | Boolean | Налягане на гуми |
| tires_tread | Boolean | Дълбочина на грайфера |
| brakes_condition | Boolean | Спирачки - OK/Не |
| brakes_parking | Boolean | Ръчна спирачка |
| lights_headlights | Boolean | Главни светлини |
| lights_brake | Boolean | Стоп светлини |
| lights_turn | Boolean | Мигачи |
| lights_warning | Boolean | Аварийни |
| fluids_oil | Boolean | Масло |
| fluids_coolant | Boolean | Охлаждаща течност |
| fluids_washer | Boolean | Течност за чистачки |
| fluids_brake | Boolean | Спирачна течност |
| mirrors | Boolean | Огледала |
| wipers | Boolean | Чистачки |
| horn | Boolean | Клаксон |
| seatbelts | Boolean | Колани |
| first_aid_kit | Boolean | Аптечка |
| fire_extinguisher | Boolean | Пожарогасител |
| warning_triangle | Boolean | Триъгълник |
| overall_status | Enum | passed, failed |
| notes | Text | Забележки |
| photos | JSON | Снимки |

#### VehicleDriver (Водачи)
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID | PK |
| vehicle_id | UUID | FK |
| user_id | UUID | FK → User |
| assigned_from | Date | От дата |
| assigned_to | Date | До дата |
| is_primary | Boolean | Основен водач |

#### VehicleTrip (Маршрути)
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID | PK |
| vehicle_id | UUID | FK |
| driver_id | UUID | FK → User |
| delivery_id | UUID | FK → Delivery (опционално) |
| start_address | String(500) | Начален адрес |
| end_address | String(500) | Краен адрес |
| start_time | DateTime | Начало |
| end_time | DateTime | Край |
| distance_km | Integer | Разстояние |
| purpose | String(255) | Цел |
| expenses | Decimal | Разходи (паркинг, пътни) |
| notes | Text | Забележки |

#### VehicleExpense (Разходи)
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID | PK |
| vehicle_id | UUID | FK |
| expense_type | Enum | fuel, repair, insurance, inspection, vignette, toll, tax, other |
| expense_date | Date |
| amount | Decimal | Сума без ДДС |
| vat_amount | Decimal | ДДС |
| total_amount | Decimal | Общо с ДДС |
| description | String |
| reference_id | UUID | FK → съответния запис |
| reference_type | String | fuel, repair, insurance, inspection |
| is_deductible | Boolean | Данъчно приспадане |
| cost_center_id | UUID | FK → VehicleCostCenter |
| company_id | UUID | FK → Company |

#### VehicleCostCenter (Разходни центрове)
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID | PK |
| name | String(255) | Име |
| department_id | UUID | FK → Department |
| is_active | Boolean | Активен |
| company_id | UUID | FK → Company |

### 3.2 VehicleProfile структура

```
┌─────────────────────────────────────────────────────────┐
│  🚗 TOYOTA COROLLA (EO1234AB)                          │
│  ─────────────────────────────────────────────────────  │
│  VIN: ABC123456789   Година: 2020   Тип: Лека кола     │
│  Гориво: Дизел   Цвят: Син   Собственик: Фирма        │
│  Статус: ✅ Активен                                  │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  Шофьор: [Петър Петров ▼] [+ Добави период]           │
└─────────────────────────────────────────────────────────┘

┌──────────┬──────────┬──────────┬──────────┬──────────┐
│Километри │  Гориво  │  Ремонти  │Застрахов.│   ГТП    │
└──────────┴──────────┴──────────┴──────────┴──────────┘

┌─────────────────────────────────────────────────────────┐
│ 📊 РАЗХОДИ                                             │
│  ─────────────────────────────────────────────────────  │
│  Гориво: 2,450 лв  │  Ремонти: 800 лв                  │
│  Застраховки: 600 лв  │  ГТП: 100 лв                    │
│  ОБЩО: 3,950 лв                                    │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ 📅 ИСТОРИЯ                                             │
│  ─────────────────────────────────────────────────────  │
│  10.03.2026 - ГТП - Passed                            │
│  05.03.2026 - Застраховка - Гражданска                │
│  01.03.2026 - Ремонт - Смяна на гуми                   │
│  15.02.2026 - Гориво - 50 л                            │
└─────────────────────────────────────────────────────────┘
```

---

## 4. АВТО-ЗАЯВКИ ОТ СКЛАД

### Промени по Ingredient
| Поле | Тип | Описание |
|------|-----|----------|
| min_quantity | Decimal | Минимално количество (праг) |
| reorder_quantity | Decimal | Препоръчително количество за поръчка |
| is_auto_reorder | Boolean | Автоматично създаване на заявка |
| preferred_supplier_id | UUID | FK → Supplier |

### Background Job
- **График**: Всеки ден в 2:00 часа
- **Логика**:
  1. Вземи всички ingredients с is_auto_reorder = True
  2. Провери текущото количество
  3. Ако quantity < min_quantity → създай PurchaseRequest с is_auto=True
  4. Номер: AR-YYYY-NNNNN

### Нотификация
- Изпраща се до всички с permission `logistics:requests:approve`

### Потвърждение
- Ръчно потвърждение от потребител с `logistics:requests:approve`
- Създава се запис в PurchaseRequestApproval

---

## 5. НОТИФИКАЦИИ

| Тригер | Кога | Кому |
|--------|------|------|
| Изтичане застраховка | 30 дни преди | fleet:insurances:* |
| Изтичане ГТП | 30 дни преди | fleet:inspections:* |
| Изтичане винетка | 7 дни прени | fleet:vignettes:* |
| Поддръжка по километри | При достигане на праг | fleet:schedules:* |
| Поддръжка по дата | 7 дни преди | fleet:schedules:* |
| Инспекция преди път | При назначаване на нов шофьор | fleet:pretrip:* |

---

## 6. FRONTEND СТРАНИЦИ

| Страница | Описание |
|----------|----------|
| LogisticsPage.tsx | Заявки, Поръчки, Доставки, Доставчици, Шаблони |
| FleetPage.tsx | Списък автомобили |
| VehicleProfilePage.tsx | Профил с всички данни |
| VehicleTripsPage.tsx | Маршрути |
| VehicleInspectionsPage.tsx | Инспекции преди път |
| VehicleSchedulesPage.tsx | График поддръжка |
| FleetReportsPage.tsx | Експорт на справки |

---

## 7. DASHBOARD WIDGETS

```
┌────────────────────────────────────────┐
│  🚗 Автопарк - Общо: 15              │
│  ────────────────────────────────────  │
│  ✅ Активни: 12  🔧 В ремонт: 2       │
│  ⛔ Извън експлоатация: 1             │
├────────────────────────────────────────┤
│  ⚠️ Под внимание:                     │
│  ────────────────────────────────────  │
│  🚗 CA1234BB - ГТП изтича след 5 дни  │
│  🚗 E5678AB - Застраховка изтича 12 д │
│  🚗 AB9999CC - Винетка изтича 3 дни   │
└────────────────────────────────────────┘
```

---

## 8. СЧЕТОВОДСТВО

### Разходи → Счетоводни операции

| Разход | Дебит | Кредит |
|--------|-------|--------|
| Гориво | 6021 (Гориво и смазочни материали) | 501 (Каса) / 502 (Банка) |
| Ремонт | 6022 (Ремонти и поддръжка) | 501 / 502 |
| Застраховка | 6023 (Застраховки и данъци) | 501 / 502 |
| ГТП | 6022 (Ремонти и поддръжка) | 501 / 502 |
| Винетки/Тол | 6024 (Други разходи) | 501 / 502 |

### AccountingEntry връзки
- reference_id → VehicleExpense.id
- description → "Разход за Vehicle: {registration_number}"

---

## 9. РАЗРЕШЕНИЯ (RBAC)

### Logistics Permissions
```python
LOGISTICS_PERMISSIONS = [
    "logistics:suppliers:read",
    "logistics:suppliers:create",
    "logistics:suppliers:edit",
    "logistics:suppliers:delete",
    "logistics:templates:read",
    "logistics:templates:create",
    "logistics:templates:edit",
    "logistics:templates:delete",
    "logistics:requests:read",
    "logistics:requests:create",
    "logistics:requests:edit",
    "logistics:requests:approve",      # За одобрение
    "logistics:requests:delete",
    "logistics:orders:read",
    "logistics:orders:create",
    "logistics:orders:edit",
    "logistics:orders:delete",
    "logistics:deliveries:read",
    "logistics:deliveries:create",
    "logistics:deliveries:edit",
    "logistics:deliveries:delete",
]
```

### Fleet Permissions
```python
FLEET_PERMISSIONS = [
    "fleet:vehicles:read",
    "fleet:vehicles:create",
    "fleet:vehicles:edit",
    "fleet:vehicles:delete",
    "fleet:vehicles:status",           # Промяна на статут
    "fleet:documents:read",
    "fleet:documents:create",
    "fleet:documents:edit",
    "fleet:documents:delete",
    "fleet:fuel_cards:read",
    "fleet:fuel_cards:create",
    "fleet:fuel_cards:edit",
    "fleet:fuel_cards:delete",
    "fleet:vignettes:read",
    "fleet:vignettes:create",
    "fleet:vignettes:edit",
    "fleet:vignettes:delete",
    "fleet:tolls:read",
    "fleet:tolls:create",
    "fleet:tolls:edit",
    "fleet:mileage:read",
    "fleet:mileage:create",
    "fleet:mileage:edit",
    "fleet:fuel:read",
    "fleet:fuel:create",
    "fleet:fuel:edit",
    "fleet:repairs:read",
    "fleet:repairs:create",
    "fleet:repairs:edit",
    "fleet:repairs:delete",
    "fleet:schedules:read",
    "fleet:schedules:create",
    "fleet:schedules:edit",
    "fleet:schedules:delete",
    "fleet:insurances:read",
    "fleet:insurances:create",
    "fleet:insurances:edit",
    "fleet:insurances:delete",
    "fleet:inspections:read",
    "fleet:inspections:create",
    "fleet:inspections:edit",
    "fleet:inspections:delete",
    "fleet:pretrip:read",
    "fleet:pretrip:create",
    "fleet:pretrip:edit",
    "fleet:drivers:read",
    "fleet:drivers:create",
    "fleet:drivers:edit",
    "fleet:trips:read",
    "fleet:trips:create",
    "fleet:trips:edit",
    "fleet:trips:delete",
    "fleet:expenses:read",
    "fleet:expenses:create",
    "fleet:expenses:edit",
    "fleet:costcenters:read",
    "fleet:costcenters:create",
    "fleet:costcenters:edit",
    "fleet:reports:read",             # Експорт
    "fleet:reports:export",
]
```

---

## 10. СТЪПКИ ЗА РЕАЛИЗАЦИЯ

### 10.1 Миграции
1. Нови таблици за всички модели
2. Промени по Ingredient (min_quantity, reorder_quantity, is_auto_reorder, preferred_supplier_id)
3. Миграция за новите сметкопланни сметки (6021-6024)

### 10.2 Backend
1. SQLAlchemy модели
2. CRUD операции
3. GraphQL типове и mutations
4. Background jobs (inventory check, notifications)
5. Accounting интеграция

### 10.3 Frontend
1. GraphQL заявки
2. Компоненти и страници
3. Dashboard widgets
4. Редактори (modals/forms)

### 10.4 Тестване
1. Unit тестове
2. Интеграционни тестове
3. E2E тестове

### 10.5 Deployment
1. Docker compose update
2. Nginx конфигурация
3. Environment variables

---

## Дати
- **Създаден**: 2026-03-10
- **Версия**: 1.0
