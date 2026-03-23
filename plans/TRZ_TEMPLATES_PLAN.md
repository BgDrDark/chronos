# TRZ Шаблони и Допълнителни Споразумения - План за имплементация

**Версия:** 1.0
**Дата:** 2026-03-15
**Статус:** За имплементация

---

## 1. Преглед

Този документ описва пълния план за имплементация на:
1. Шаблони за трудови договори с версионност и секции
2. Шаблони за допълнителни споразумения с версионност и секции
3. Библиотека от преизползваеми клаузи
4. PDF генерация
5. E-signature (маркиране като подписано)
6. Email известия (опционално)

---

## 2. Модели (Database)

### 2.1 ContractTemplate - Шаблон за договор

```python
class ContractTemplate(Base):
    """Шаблон за трудов договор"""
    __tablename__ = "contract_templates"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"))
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Шаблонни стойности
    contract_type: Mapped[str] = mapped_column(String(50))
    work_hours_per_week: Mapped[int] = mapped_column(Integer, default=40)
    probation_months: Mapped[int] = mapped_column(Integer, default=6)
    salary_calculation_type: Mapped[str] = mapped_column(String(20), default='gross')
    payment_day: Mapped[int] = mapped_column(Integer, default=25)
    night_work_rate: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=0.5)
    overtime_rate: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=1.5)
    holiday_rate: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=2.0)
    work_class: Mapped[str] = mapped_column(String(10), nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True)
```

### 2.2 ContractTemplateVersion - Версия на шаблон

```python
class ContractTemplateVersion(Base):
    """Версия на шаблон за договор"""
    __tablename__ = "contract_template_versions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_id: Mapped[int] = mapped_column(Integer, ForeignKey("contract_templates.id", ondelete="CASCADE"))
    version: Mapped[int] = mapped_column(Integer)
    
    # Стойности на версията
    contract_type: Mapped[str] = mapped_column(String(50))
    work_hours_per_week: Mapped[int] = mapped_column(Integer)
    probation_months: Mapped[int] = mapped_column(Integer)
    salary_calculation_type: Mapped[str] = mapped_column(String(20))
    payment_day: Mapped[int] = mapped_column(Integer)
    night_work_rate: Mapped[Decimal] = mapped_column(Numeric(4, 2))
    overtime_rate: Mapped[Decimal] = mapped_column(Numeric(4, 2))
    holiday_rate: Mapped[Decimal] = mapped_column(Numeric(4, 2))
    work_class: Mapped[str] = mapped_column(String(10), nullable=True)
    
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    change_note: Mapped[str] = mapped_column(String(500), nullable=True)
```

### 2.3 ContractTemplateSection - Секция в шаблон

```python
class ContractTemplateSection(Base):
    """Секция/клауза в шаблон за договор"""
    __tablename__ = "contract_template_sections"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_id: Mapped[int] = mapped_column(Integer, ForeignKey("contract_templates.id", ondelete="CASCADE"))
    version_id: Mapped[int] = mapped_column(Integer, ForeignKey("contract_template_versions.id", ondelete="CASCADE"))
    
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)  # Rich text (HTML)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    is_required: Mapped[bool] = mapped_column(Boolean, default=False)
```

### 2.4 AnnexTemplate - Шаблон за анекс

```python
class AnnexTemplate(Base):
    """Шаблон за допълнително споразумение"""
    __tablename__ = "annex_templates"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"))
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, nullable=True)
    
    change_type: Mapped[str] = mapped_column(String(50))  # "salary", "position", "hours", "rate", "other"
    
    # Шаблонни стойности (nullable)
    new_base_salary: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=True)
    new_work_hours_per_week: Mapped[int] = mapped_column(Integer, nullable=True)
    new_night_work_rate: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=True)
    new_overtime_rate: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=True)
    new_holiday_rate: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True)
```

### 2.5 AnnexTemplateVersion - Версия на анекс шаблон

```python
class AnnexTemplateVersion(Base):
    """Версия на шаблон за анекс"""
    __tablename__ = "annex_template_versions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_id: Mapped[int] = mapped_column(Integer, ForeignKey("annex_templates.id", ondelete="CASCADE"))
    version: Mapped[int] = mapped_column(Integer)
    
    change_type: Mapped[str] = mapped_column(String(50))
    new_base_salary: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=True)
    new_work_hours_per_week: Mapped[int] = mapped_column(Integer, nullable=True)
    new_night_work_rate: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=True)
    new_overtime_rate: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=True)
    new_holiday_rate: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=True)
    
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    change_note: Mapped[str] = mapped_column(String(500), nullable=True)
```

### 2.6 AnnexTemplateSection - Секция в анекс шаблон

```python
class AnnexTemplateSection(Base):
    """Секция/клауза в шаблон за анекс"""
    __tablename__ = "annex_template_sections"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_id: Mapped[int] = mapped_column(Integer, ForeignKey("annex_templates.id", ondelete="CASCADE"))
    version_id: Mapped[int] = mapped_column(Integer, ForeignKey("annex_template_versions.id", ondelete="CASCADE"))
    
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    is_required: Mapped[bool] = mapped_column(Boolean, default=False)
```

### 2.7 ClauseTemplate - Библиотека от клаузи

```python
class ClauseTemplate(Base):
    """Библиотека от преизползваеми клаузи"""
    __tablename__ = "clause_templates"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"))
    
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)  # Rich text
    category: Mapped[str] = mapped_column(String(50))  # "rights", "duties", "confidentiality", etc.
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True)
```

### 2.8 Разширение на ContractAnnex

```python
class ContractAnnex(Base):
    # ... съществуващи полета ...
    
    # Нови полета
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft, pending, signed, rejected
    template_id: Mapped[int] = mapped_column(Integer, ForeignKey("annex_templates.id", ondelete="SET NULL"), nullable=True)
    
    change_type: Mapped[str] = mapped_column(String(50), nullable=True)
    change_description: Mapped[str] = mapped_column(Text, nullable=True)
    
    signature_requested_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True)
    signed_by_employee: Mapped[bool] = mapped_column(Boolean, default=False)
    signed_by_employee_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True)
    signed_by_employer: Mapped[bool] = mapped_column(Boolean, default=False)
    signed_by_employer_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True)
    rejection_reason: Mapped[str] = mapped_column(Text, nullable=True)
```

### 2.9 Разширение на EmploymentContract

```python
class EmploymentContract(Base):
    # ... съществуващи полета ...
    
    # Нова връзка към шаблон
    template_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("contract_templates.id", ondelete="SET NULL"),
        nullable=True
    )
```

---

## 3. Global Settings

```python
# Email известия
"payroll_annex_email_notifications": "false"  # Опционално
```

---

## 4. Default Seed Data

### 4.1 Договорни шаблони

```python
CONTRACT_TEMPLATES = [
    {
        "name": "Трудов договор - пълно работно време",
        "contract_type": "full_time",
        "work_hours_per_week": 40,
        "probation_months": 6,
    },
    {
        "name": "Трудов договор - непълно работно време",
        "contract_type": "part_time",
        "work_hours_per_week": 20,
        "probation_months": 6,
    },
    {
        "name": "Граждански договор",
        "contract_type": "contractor",
        "work_hours_per_week": 0,
        "probation_months": 0,
    },
]
```

### 4.2 Секции по подразбиране

```python
DEFAULT_CONTRACT_SECTIONS = [
    {"title": "Предмет на договора", "order": 0, "required": True},
    {"title": "Работно време и почивки", "order": 1, "required": True},
    {"title": "Права и задължения на работодателя", "order": 2, "required": True},
    {"title": "Права и задължения на работника", "order": 3, "required": True},
    {"title": "Заплащане", "order": 4, "required": True},
    {"title": "Конфиденциалност", "order": 5, "required": False},
]

DEFAULT_ANNEX_SECTIONS = [
    {"title": "Описание на промените", "order": 0, "required": True},
    {"title": "Основание", "order": 1, "required": False},
]
```

### 4.3 Шаблони за анекси

```python
ANNEX_TEMPLATES = [
    {"name": "Повишение на заплатата", "change_type": "salary"},
    {"name": "Промяна на длъжността", "change_type": "position"},
    {"name": "Промяна на работното време", "change_type": "hours"},
    {"name": "Промяна на надбавки", "change_type": "rate"},
    {"name": "Сключване на допълнително споразумение", "change_type": "other"},
]
```

### 4.4 Категории за клаузи

```python
CLAUSE_CATEGORIES = [
    "rights_employer",
    "rights_employee", 
    "work_schedule",
    "salary",
    "confidentiality",
    "business_trip",
    "termination",
    "other",
]
```

---

## 5. GraphQL API

### 5.1 Queries

| Query | Описание |
|-------|----------|
| `contract_templates` | Списък шаблони за договори |
| `contract_template(id)` | Детайли за шаблон |
| `contract_template_versions(template_id)` | Версии на шаблон |
| `annex_templates` | Списък шаблони за анекси |
| `annex_template(id)` | Детайли за шаблон |
| `annex_template_versions(template_id)` | Версии на шаблон |
| `clause_templates(category)` | Клаузи по категория |
| `annexes(filter)` | Списък анекси |
| `annex(id)` | Детайли за анекс |

### 5.2 Mutations

| Mutation | Описание |
|----------|----------|
| `create_contract_template(input)` | Създава шаблон + версия 1 |
| `update_contract_template(id, input, note)` | Създава нова версия |
| `delete_contract_template(id)` | Изтрива шаблон |
| `restore_contract_template_version(version_id)` | Въстановява версия |
| `add_section_to_template(template_id, section)` | Добавя секция |
| `update_section(section_id, content)` | Редактира секция |
| `delete_section(section_id)` | Изтрива секция |
| `create_clause_template(input)` | Създава клауза |
| `update_clause_template(id, input)` | Редактира клауза |
| `delete_clause_template(id)` | Изтрива клауза |
| `create_annex_template(input)` | Създава шаблон за анекс |
| `update_annex_template(id, input, note)` | Създава нова версия |
| `create_annex(contract_id, template_id, data)` | Създава анекс |
| `sign_annex(annex_id, role)` | Подписва анекс |
| `reject_annex(annex_id, reason)` | Отхвърля анекс |
| `generate_annex_pdf(annex_id)` | Генерира PDF |

---

## 6. Frontend Страници

### 6.1 Меню структура

```
Отдел ТРЗ
├── ТРЗ Настройки
├── Настройки
├── История
├── Шаблони
│   ├── Договори
│   ├── Анекси
│   └── Клаузи
├── Допълнителни споразумения
│   ├── Списък
│   ├── Създай договор
│   └── Създай анекс
├── Плащания
├── Празници
└── Справки
```

### 6.2 Routes

| Route | Описание |
|-------|----------|
| `/admin/payroll/templates/contracts` | Списък договорни шаблони |
| `/admin/payroll/templates/contracts/:id` | Редактиране на шаблон |
| `/admin/payroll/templates/annexes` | Списък анекс шаблони |
| `/admin/payroll/templates/annexes/:id` | Редактиране на шаблон |
| `/admin/payroll/templates/clauses` | Библиотека от клаузи |
| `/admin/payroll/contracts` | Списък договори |
| `/admin/payroll/contracts/new` | Създаване на договор |
| `/admin/payroll/contracts/:id` | Детайли за договор |
| `/admin/payroll/annexes` | Списък анекси |
| `/admin/payroll/annexes/new` | Създаване на анекс |
| `/admin/payroll/annexes/:id` | Детайли за анекс + подписване + PDF |

---

## 7. PDF Генерация

### 7.1 Структура на PDF

```
┌─────────────────────────────────────────┐
│           [ФИРМЕН ЛОГО]                 │
│         ИМЕ НА ФИРМАТА                  │
│    ЕИК: xxxxxxxxxxx                     │
├─────────────────────────────────────────┤
│                                         │
│     ДОПЪЛНИТЕЛНО СПОРАЗУМЕНИЕ          │
│     № 001/2026                          │
│                                         │
│     към Трудов договор № 001/2025       │
│                                         │
│     Днес: 15.03.2026 г.                │
│                                         │
├─────────────────────────────────────────┤
│   СТРАНИ:                               │
│   1. РАБОТОДАТЕЛ: [име]                │
│   2. РАБОТНИК: [име]                   │
│                                         │
├─────────────────────────────────────────┤
│   ПРЕДМЕТ:                              │
│   [Секции от шаблона]                   │
│                                         │
├─────────────────────────────────────────┤
│   ПОДПИСИ:                              │
│   _______________          ____________  │
│   ЗА РАБОТОДАТЕЛЯ        ЗА РАБОТНИКА  │
│                                         │
├─────────────────────────────────────────┤
│   Дата на влизане в сила: 01.04.2026   │
└─────────────────────────────────────────┘
```

### 7.2 Print бутон

```tsx
<Button 
  startIcon={<PrintIcon />}
  onClick={() => window.open(pdfUrl, '_blank')?.print()}
>
  Принтирай
</Button>
```

---

## 8. Приоритети за имплементация

| Приоритет | Стъпка |
|-----------|--------|
| 1 | Модели: ContractTemplate, AnnexTemplate |
| 2 | Модели: Version, Section |
| 3 | Модели: ClauseTemplate |
| 4 | GraphQL: CRUD + версионност |
| 5 | Frontend: Страница "Шаблони" |
| 6 | Frontend: Редактиране на секции |
| 7 | Frontend: Библиотека "Клаузи" |
| 8 | Frontend: Създаване на договор/анекс |
| 9 | PDF Generator |
| 10 | Подписване + Print бутон |
| 11 | Email известия |

---

## 9. Забележки

- Payroll калкулаторът винаги взима данните от `EmploymentContract`, не от шаблоните
- Шаблоните са само за улеснение при създаване и документиране
- При подписване на анекс, данните автоматично се обновяват в `EmploymentContract`
- Email известията са опционални (контролират се от global setting)
- Rich text editor: TinyMCE или Quill
