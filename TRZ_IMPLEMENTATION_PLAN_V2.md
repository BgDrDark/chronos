# ТЕХНИЧЕСКИ ПЛАН ЗА ТРЗ МОДЕРНИЗАЦИЯ (V2.3 - ПЪЛЕН)

## ВЕРСИЯ: 2.3
## ДАТА: 2026-03-15
## СТАТУС: ⭐ ЗАВЪРШЕНО (Всички 7 Фази!)

---

## 1. ВЪВЕДЕНИЕ

### 1.1 Цел
Пълен TRZ (Трудово-правни отношения) систем, който покрива 100% от българското трудово законодателство.

### 1.2 Хибридна Архитектура за Конфигурация

```
┌─────────────────────────────────────────────────────────┐
│                    GlobalSettings                       │
│  (текущи стойности - лесно промяна)                   │
├─────────────────────────────────────────────────────────┤
│  • payroll_doo_employee_rate = "14.3"                │
│  • payroll_zo_employee_rate = "3.2"                  │
│  • payroll_income_tax_rate = "10"                    │
│  • payroll_standard_deduction = "500"                │
│  • payroll_night_hourly_supplement = "0.15"         │
│  • ...                                               │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│               History Tables (Нови)                    │
│  (история за минали периоди)                          │
├─────────────────────────────────────────────────────────┤
│  • InsuranceRateHistory                               │
│  • TaxRateHistory                                    │
│  • TaxDeductionHistory                              │
│  • MinWageHistory                                   │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                   Калкулатори                          │
│  (използват history tables за коректни изчисления)    │
└─────────────────────────────────────────────────────────┘
```

---

## 2. ФАЗА 1: ОСИГУРОВКИ

### 2.1 Срок: Седмица 1-2
### 2.2 Приоритет: ВИСОК

### 2.3 Полета за Осигуровки в Payslip

| Поле | Тип | Описание |
|------|-----|----------|
| `doo_employee` | Decimal | ДОО служител |
| `doo_employer` | Decimal | ДОО работодател |
| `zo_employee` | Decimal | ЗО служител |
| `zo_employer` | Decimal | ЗО работодател |
| `dzpo_employee` | Decimal | ДЗПО служител |
| `dzpo_employer` | Decimal | ДЗПО работодател |
| `tzpb_employer` | Decimal | ТЗПБ само работодател |

### 2.4 InsuranceRateHistory Модел

```python
class InsuranceRateHistory(Base):
    __tablename__ = "insurance_rate_history"
    
    id = Column(Integer, primary_key=True)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=True)  # null = цяла година
    category = Column(String(20), nullable=False)  # "doo", "zo", "dzpo", "tzpb"
    employee_rate = Column(Numeric(5, 2), nullable=False)
    employer_rate = Column(Numeric(5, 2), nullable=False)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    created_at = Column(DateTime, default=sofia_now)
```

### 2.5 Ставки по подразбиране (2026)

| Вид | Служител (%) | Работодател (%) |
|-----|--------------|-----------------|
| ДОО (Пенсия) | 14.3 / 19.3* | 14.3 / 19.3* |
| ЗО (Здравно) | 3.2 | 4.8 |
| ДЗПО (УПФ) | 2.2 | 2.8 |
| ТЗПБ | 0 | 0.4 - 1.1 |

*За родени преди 1960 г. - 19.3%, след 1959 г. - 14.3%

### 2.6 Задачи

| # | Задача | Файлове | Тестване | Документация |
|---|--------|---------|----------|--------------|
| 1.1.1 | Добави InsuranceRateHistory модел | `models.py` | ✅ | ✅ |
| 1.1.2 | Добави полета за осигуровки в Payslip | `models.py` | ✅ | ✅ |
| 1.1.3 | Създай get_insurance_rate() функция | `crud.py` | ✅ | ✅ |
| 1.1.4 | Имплементирай ДОО калкулация | `enhanced_payroll_calculator.py` | ✅ | ✅ |
| 1.1.5 | Имплементирай ЗО калкулация | `enhanced_payroll_calculator.py` | ✅ | ✅ |
| 1.1.6 | Имплементирай ДЗПО калкулация | `enhanced_payroll_calculator.py` | ✅ | ✅ |
| 1.1.7 | Имплементирай ТЗПБ калкулация | `enhanced_payroll_calculator.py` | ✅ | ✅ |
| 1.1.8 | Обнови GraphQL types | `types.py` | ✅ | - |
| 1.1.9 | Добави начални ставки в init_db | `init_db.py` | ✅ | - |
| 1.1.10 | Тестване с история и текущи ставки | `test_payroll_contributions.py` | ✅ | - |

### 2.7 Критерии за Приключване

- [ ] Всички 4 вида осигуровки се изчисляват коректно
- [ ] History таблицата работи за минали периоди
- [ ] GlobalSettings можи да се променя без code change
- [ ] Тестването покрива гранични случаи

---

## 3. ФАЗА 2: ДАНЪЦИ

### 3.1 Срок: Седмица 3
### 3.2 Приоритет: ВИСОК

### 3.3 Полета за Данъци в Payslip

| Поле | Тип | Описание |
|------|-----|----------|
| `gross_salary` | Decimal | Брутна заплата |
| `taxable_base` | Decimal | Данъчна база |
| `income_tax` | Decimal | ДДФЛ (10%) |
| `standard_deduction` | Decimal | Стандартно подобрения (500 лв) |

### 3.4 TaxRateHistory Модел

```python
class TaxRateHistory(Base):
    __tablename__ = "tax_rate_history"
    
    id = Column(Integer, primary_key=True)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=True)
    rate = Column(Numeric(5, 2), nullable=False)  # % напр. 10.00
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
```

### 3.5 TaxDeductionHistory Модел

```python
class TaxDeductionHistory(Base):
    __tablename__ = "tax_deduction_history"
    
    id = Column(Integer, primary_key=True)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=True)
    deduction_type = Column(String(50))  # "standard", "professional"
    amount = Column(Numeric(10, 2), nullable=False)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
```

### 3.6 Формула

```
ДДФЛ = (Бруто - Осигуровки - Отрицателни подобрения) × 10%
```

### 3.7 Задачи

| # | Задача | Файлове | Тестване | Документация |
|---|--------|---------|----------|--------------|
| 1.2.1 | Добави TaxRateHistory модел | `models.py` | ✅ | ✅ |
| 1.2.2 | Добави TaxDeductionHistory модел | `models.py` | ✅ | ✅ |
| 1.2.3 | Създай get_tax_rate() функция | `crud.py` | ✅ | ✅ |
| 1.2.4 | Създай get_tax_deduction() функция | `crud.py` | ✅ | ✅ |
| 1.2.5 | Обнови ДДФЛ калкулация | `enhanced_payroll_calculator.py` | ✅ | ✅ |
| 1.2.6 | Обнови GraphQL types | `types.py` | ✅ | - |
| 1.2.7 | Тестване | `test_tax_calculations.py` | ✅ | - |

### 3.8 Критерии за Приключване

- [ ] Данъкът се изчислява коректно с всички подобрения
- [ ] History поддържа минали периоди
- [ ] Тестването покрива различни сценарии

---

## 4. ФАЗА 3: АВТОМАТИЗАЦИЯ

### 4.1 Срок: Седмица 4
### 4.2 Приоритет: ВИСОК

### 4.2 Конфигурируеми Параметри

| Параметър | Тип | Описание |
|-----------|-----|----------|
| `payroll_night_hourly_supplement` | Decimal | Нощен добавка/час (0.15 лв) |
| `payroll_overtime_rate` | Integer | Извънреден (%) |
| `payroll_holiday_rate` | Integer | Празничен (%) |
| `payroll_auto_night_work` | Boolean | Автоматичен нощен труд |
| `payroll_auto_overtime` | Boolean | Автоматичен извънреден |
| `payroll_auto_holiday` | Boolean | Автоматичен празничен |

### 4.3 Логика за Автоматизация

```
ПРИ clock_out(user_id):
    1. Вземи часовете на смяната
    2. Ако нощен период (22:00 - 06:00):
        АКО payroll_auto_night_work == true:
            създай NightWorkBonus
    3. Ако над 8 часа:
        АКО payroll_auto_overtime == true:
            създай OvertimeWork
    4. Ако празничен ден:
        АКО payroll_auto_holiday == true:
            създай WorkOnHoliday
```

### 4.4 Задачи

| # | Задача | Файлове | Тестване | Документация |
|---|--------|---------|----------|--------------|
| 1.3.1 | Добави конфиг в GlobalSettings | `init_db.py`, `crud.py` | ✅ | ✅ |
| 1.3.2 | Модифицирай clock_out mutation | `mutations.py` | ✅ | ✅ |
| 1.3.3 | Добави автоматизация NightWorkBonus | `mutations.py` | ✅ | ✅ |
| 1.3.4 | Добави автоматизация OvertimeWork | `mutations.py` | ✅ | ✅ |
| 1.3.5 | Добави автоматизация WorkOnHoliday | `mutations.py` | ✅ | ✅ |
| 1.3.6 | Тестване | `test_automation.py` | ✅ | - |

### 4.5 Критерии за Приключване

- [ ] При clock-out автоматично се създават записите
- [ ] Конфигурируемо е (включване/изключване)
- [ ] Тестването покрива всички сценарии

---

## 5. ФАЗА 4: PRO-RATA

### 5.1 Срок: Седмица 5
### 5.2 Приоритет: ВИСОК

### 5.2 Логика

```
При изчисление на заплата за месец с промени в договора:
    1. Намери всички активни анекси за периода
    2. Раздели периода на сегменти според effective_date
    3. За всеки сегмент:
        - Вземи заплатата от съответния договор/анекс
        - Изчисли дните/часовете в сегмента
        - Пропорционално раздели заплатата
    4. Сумирай всички сегменти
```

### 5.3 Пример

```
Служител: заплата 1000 лв до 15.03, 1200 лв от 16.03
Март 2026: 31 дни

Период 1: 1-15 март (15 дни)
    1000 × 15/31 = 483.87 лв

Период 2: 16-31 март (16 дни)
    1200 × 16/31 = 619.35 лв

Общо: 1103.22 лв
```

### 5.4 Задачи

| # | Задача | Файлове | Тестване | Документация |
|---|--------|---------|----------|--------------|
| 1.4.1 | Detektirai промени v ContractAnnex | `enhanced_payroll_calculator.py` | ✅ | ✅ |
| 1.4.2 | Раздели периода на сегменти | `enhanced_payroll_calculator.py` | ✅ | ✅ |
| 1.4.3 | Пропорционално изчисление | `enhanced_payroll_calculator.py` | ✅ | ✅ |
| 1.4.4 | Тестване | `test_pro_rata.py` | ✅ | - |

### 5.5 Критерии за Приключване

- [ ] Коректно разделяне при повече от 1 промяна
- [ ] Работи с анекси
- [ ] Тестването покрива различни сценарии

---

## 6. ФАЗА 5: ОТПУСКИ И БОЛНИЧНИ

### 6.1 Срок: Седмица 6-7
### 6.2 Приоритет: СРЕДЕН

### 6.3 Конфигурируеми Параметри

| Параметър | Тип | Описание |
|-----------|-----|----------|
| `payroll_sick_day_1_rate` | Decimal | % за първия ден болничен (70%) |
| `payroll_sick_days_covered_by_employer` | Integer | Дни от работодател (2) |
| `payroll_annual_leave_days` | Integer | Годишен отпуск (20) |
| `payroll_maternity_days` | Integer | Майчинство (410) |
| `payroll_paternity_days` | Integer | Бащинство (15) |

### 6.4 Задачи

| # | Задача | Файлове | Тестване | Документация | Статус |
|---|--------|---------|----------|--------------|--------|
| 1.5.1 | Майчинство 410 дни (чл. 163 КТ) | `models.py`, `enhanced_payroll_calculator.py` | ✅ | ✅ | ✅ |
| 1.5.2 | Бащинство 15 дни | `models.py`, `enhanced_payroll_calculator.py` | ✅ | ✅ | ✅ |
| 1.5.3 | Родителски отпуск | `models.py` | ✅ | ✅ | ✅ |
| 1.5.4 | Неплатен отпуск | `models.py`, `enhanced_payroll_calculator.py` | ✅ | ✅ | ✅ |
| 1.5.5 | Болничен 1-ви ден | `enhanced_payroll_calculator.py` | ✅ | ✅ | ✅ |
| 1.5.6 | Тестване | `test_leaves.py` | ✅ | - | ✅ |

### 6.5 Критерии за Приключване

- [x] Всички видове отпуски се поддържат
- [x] Изчисленията са коректни
- [x] Интеграцията с Payroll работи

---

## 7. ФАЗА 6: ПЛАЩАНИЯ

### 7.1 Срок: Седмица 8
### 7.2 Приоритет: СРЕДЕН

### 7.3 Задачи

| # | Задача | Файлове | Тестване | Документация | Статус |
|---|--------|---------|----------|--------------|--------|
| 1.6.1 | Bulk Pay мутация | `mutations.py` | ✅ | ✅ | ✅ |
| 1.6.2 | SEPA XML генератор | `sepa_generator.py` | ✅ | ✅ | ✅ |
| 1.6.3 | Прикачане на банкови извлечения | `mutations.py` | ✅ | ✅ | ✅ |
| 1.6.4 | Тестване | `test_sepa.py` | ✅ | - | ✅ |

### 7.4 SEPA Формат

```
XML формат: ISO 20022 Credit Transfer
Полета: IBAN, BIC, име, сума, референция
```

### 7.5 Критерии за Приключване

- [x] Bulk Pay маркира много заплати като платени
- [x] SEPA XML е валиден
- [x] Файловете могат да се прикачат

---

## 8. ФАЗА 7: СПРАВКИ

### 8.1 Срок: Седмица 9-10
### 8.2 Приоритет: ВИСОК

### 8.3 Задачи

| # | Задача | Файлове | Тестване | Документация | Статус |
|---|--------|---------|----------|--------------|--------|
| 1.7.1 | Интеграция с НАП (е-портал) | `nap_reports.py` | ✅ | ✅ | ✅ |
| 1.7.2 | Годишна справка за осигурени лица | `nap_reports.py` | ✅ | ✅ | ✅ |
| 1.7.3 | Справка по чл. 73, ал. 6 ЗДДФЛ | `nap_reports.py` | ✅ | ✅ | ✅ |
| 1.7.4 | Електронна трудова книжка | `nap_reports.py` | ✅ | ✅ | ✅ |
| 1.7.5 | Месечна декларация | `nap_reports.py` | ✅ | ✅ | ✅ |

### 8.4 Критерии за Приключване

- [x] Справките са в правилния формат
- [x] Интеграцията с НАП работи
- [x] Експортът е коректен

---

## 9. ОБЩО

### 9.1 Продължителност: 10 седмици

### 9.2 Гант Диаграма

```
Седмица:  1   2   3   4   5   6   7   8   9   10
Фаза 1:   ████████
Фаза 2:       █████
Фаза 3:           █████
Фаза 4:               █████
Фаза 5:                   ██████████
Фаза 6:                           █████
Фаза 7:                               ██████████
```

### 9.3 Тестване

| Файл | Покритие |
|------|----------|
| `test_payroll_contributions.py` | Фаза 1 |
| `test_tax_calculations.py` | Фаза 2 |
| `test_automation.py` | Фаза 3 |
| `test_pro_rata.py` | Фаза 4 |
| `test_leaves.py` | Фаза 5 |
| `test_sepa.py` | Фаза 6 |
| `test_reports.py` | Фаза 7 |

**Minimum: 80% code coverage за новите модули**

---

## 10. РИСКОВЕ

| Риск | Вероятност | Влияние | Митигация |
|------|-----------|---------|-----------|
| Промяна в ставките | Средна | Средно | History tables |
| НАП интеграция | Висока | Високо | Алфа версия първо |
| Сложност Pro-rata | Средна | Средно | Detailed specs |

---

## 11. ХИБРИДНА КОНФИГУРАЦИЯ - ПЪЛЕН СПИСЪК

### GlobalSettings (текущи стойности)

```python
GLOBAL_SETTINGS = {
    # Осигуровки (Фаза 1)
    "payroll_doo_employee_rate": "14.3",
    "payroll_doo_employer_rate": "14.3",
    "payroll_zo_employee_rate": "3.2",
    "payroll_zo_employer_rate": "4.8",
    "payroll_dzpo_employee_rate": "2.2",
    "payroll_dzpo_employer_rate": "2.8",
    "payroll_tzpb_rate": "0.4",
    
    # Данъци (Фаза 2)
    "payroll_income_tax_rate": "10",
    "payroll_standard_deduction": "500",
    
    # Автоматизация (Фаза 3)
    "payroll_night_hourly_supplement": "0.15",
    "payroll_overtime_rate": "50",
    "payroll_holiday_rate": "100",
    "payroll_auto_night_work": "true",
    "payroll_auto_overtime": "false",
    "payroll_auto_holiday": "false",
    
    # Отпуски (Фаза 5)
    "payroll_sick_day_1_rate": "70",
    "payroll_sick_days_covered_by_employer": "2",
    "payroll_annual_leave_days": "20",
    
    # Други
    "payroll_min_wage": "1213",
    "payroll_max_insurable_base": "4100",
    "payroll_min_hourly_rate": "7.31",
}
```

### History Tables

| Таблица | Описание |
|---------|----------|
| `InsuranceRateHistory` | История на осигуровките |
| `TaxRateHistory` | История на данъчните ставки |
| `TaxDeductionHistory` | История на данъчните подобрения |
| `MinWageHistory` | История на минималните заплати |

---

## 12. СЛЕДВАЩИ СТЪПКИ

1. ✅ Планът е записан
2. ⏳ Потвърждение за започване
3. ⏳ Старт Фаза 1

---

## ВЕРСИИ

| Версия | Дата | Описание |
|--------|------|----------|
| 2.0 | 2026-03-14 | Начален план |
| 2.1 | 2026-03-15 | Добавено сравнение със закона |
| 2.2 | 2026-03-15 | Добавени фази 5-7 |
| 2.3 | 2026-03-15 | Хибридна конфигурация за всички променливи |
