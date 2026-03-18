# ПЛАН: Разширяване на ТРЗ Договори в CHRONOS

## Преглед

Този документ описва подробния план за имплементация на нова функционалност за управление на трудови договори в системата CHRONOS.

### Поток на работа

1. **Първо** - генерираш PDF на трудовия договор
2. **Подписваш** го (физически) със служителя
3. **След това** - създаваш акаунт в системата
4. **Свързваш** договора с потребителя

---

## 1. Database Models

### Съществуващи модели (използвани):
- `EmploymentContract` - съществуващ трудов договор в системата
- `AnnexTemplate`, `AnnexTemplateVersion`, `AnnexTemplateSection` - шаблони за анекси
- `ClauseTemplate` - библиотека от клаузи

### Нови модели:

#### LaborContract
```python
class LaborContract(Base):
    """Трудов договор - преди създаване на потребител"""
    __tablename__ = "labor_contracts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_name: Mapped[str] = mapped_column(String(200), nullable=False)  # ЗАДЪЛЖИТЕЛНО
    employee_egn: Mapped[str] = mapped_column(String(10), nullable=False)    # ЗАДЪЛЖИТЕЛНО
    
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"))
    position: Mapped[str] = mapped_column(String(200), nullable=True)
    job_description: Mapped[str] = mapped_column(Text, nullable=False)       # ЗАДЪЛЖИТЕЛНО
    
    contract_type: Mapped[str] = mapped_column(String(20))  # permanent/temporary/seasonal/internship
    base_salary: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    work_hours_per_week: Mapped[int] = mapped_column(Integer, default=40)
    
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date, nullable=True)
    
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft/signed/linked
    signed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    employment_contract_id: Mapped[int] = mapped_column(Integer, ForeignKey("employment_contracts.id"), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=sofia_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    company = relationship("Company")
    user = relationship("User")
```

#### LaborContractTemplate
```python
class LaborContractTemplate(Base):
    """Шаблон за трудов договор"""
    __tablename__ = "labor_contract_templates"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"))
    name: Mapped[str] = mapped_column(String(200))
    contract_type: Mapped[str] = mapped_column(String(20))  # permanent/temporary/seasonal/internship
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    job_description_template: Mapped[str] = mapped_column(Text, nullable=True)
    clauses_template: Mapped[str] = mapped_column(JSON)  # JSON с клаузи
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=sofia_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    company = relationship("Company", backref="labor_contract_templates")
```

#### LaborContractClause
```python
class LaborContractClause(Base):
    """Клаузи за трудов договор"""
    __tablename__ = "labor_contract_clauses"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    contract_id: Mapped[int] = mapped_column(Integer, ForeignKey("labor_contracts.id"))
    
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    
    contract = relationship("LaborContract", backref="clauses")
```

---

## 2. GraphQL Types

### Файл: `backend/graphql/types.py`

```python
@strawberry.type
class LaborContract:
    id: int
    employee_name: str
    employee_egn: str
    company_id: int
    position: Optional[str]
    job_description: str
    contract_type: str
    base_salary: Optional[float]
    work_hours_per_week: int
    start_date: date
    end_date: Optional[date]
    status: str
    signed_at: Optional[datetime]
    user_id: Optional[int]
    employment_contract_id: Optional[int]
    created_at: datetime
    
    # Relationships
    company: "Company"
    user: Optional["User"]

@strawberry.type
class LaborContractTemplate:
    id: int
    company_id: int
    name: str
    contract_type: str
    is_active: bool
    job_description_template: Optional[str]
    clauses_template: Optional[dict]
    created_at: datetime
    
    company: "Company"

@strawberry.type
class LaborContractClause:
    id: int
    contract_id: int
    title: str
    content: str
    order_index: int
```

---

## 3. GraphQL Mutations

### Файл: `backend/graphql/mutations.py`

```python
# Labor Contract Mutations
@strawberry.mutation
async def create_labor_contract(
    input: LaborContractCreateInput,
    info: strawberry.Info
) -> LaborContract: ...

@strawberry.mutation
async def update_labor_contract(
    id: int,
    input: LaborContractUpdateInput,
    info: strawberry.Info
) -> LaborContract: ...

@strawberry.mutation
async def sign_labor_contract(
    id: int,
    info: strawberry.Info
) -> LaborContract: ...

@strawberry.mutation
async def link_labor_contract_to_user(
    contract_id: int,
    user_id: int,
    employment_contract_id: int,
    info: strawberry.Info
) -> LaborContract: ...

@strawberry.mutation
async def delete_labor_contract(
    id: int,
    info: strawberry.Info
) -> bool: ...

# Template Mutations
@strawberry.mutation
async def create_labor_contract_template(
    input: LaborContractTemplateInput,
    info: strawberry.Info
) -> LaborContractTemplate: ...

@strawberry.mutation
async def update_labor_contract_template(
    id: int,
    input: LaborContractTemplateInput,
    info: strawberry.Info
) -> LaborContractTemplate: ...

@strawberry.mutation
async def delete_labor_contract_template(
    id: int,
    info: strawberry.Info
) -> bool: ...
```

---

## 4. GraphQL Queries

### Файл: `backend/graphql/queries.py`

```python
@strawberry.type
class Query:
    @strawberry.field
    async def labor_contracts(
        self,
        info: strawberry.Info,
        company_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> List[LaborContract]: ...
    
    @strawberry.field
    async def labor_contract(
        self,
        info: strawberry.Info,
        id: int
    ) -> Optional[LaborContract]: ...
    
    @strawberry.field
    async def labor_contract_templates(
        self,
        info: strawberry.Info,
        company_id: Optional[int] = None,
        contract_type: Optional[str] = None
    ) -> List[LaborContractTemplate]: ...
    
    @strawberry.field
    async def labor_contract_template(
        self,
        info: strawberry.Info,
        id: int
    ) -> Optional[LaborContractTemplate]: ...
```

---

## 5. GraphQL Inputs

### Файл: `backend/graphql/inputs.py`

```python
@strawberry.input
class LaborContractCreateInput:
    employee_name: str
    employee_egn: str
    company_id: int
    position: Optional[str] = None
    job_description: str
    contract_type: str  # permanent/temporary/seasonal/internship
    base_salary: Optional[float] = None
    work_hours_per_week: int = 40
    start_date: date
    end_date: Optional[date] = None

@strawberry.input
class LaborContractUpdateInput:
    employee_name: Optional[str] = None
    employee_egn: Optional[str] = None
    position: Optional[str] = None
    job_description: Optional[str] = None
    contract_type: Optional[str] = None
    base_salary: Optional[float] = None
    work_hours_per_week: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

@strawberry.input
class LaborContractTemplateInput:
    company_id: int
    name: str
    contract_type: str
    job_description_template: Optional[str] = None
    clauses_template: Optional[dict] = None
```

---

## 6. PDF Generation

### Файл: `backend/routers/trz_export.py`

```python
@router.get("/labor-contract/{contract_id}/pdf")
async def generate_labor_contract_pdf(contract_id: int, ...):
    """
    Генерира PDF на трудов договор
    
    Включва:
    - Данни за служителя (име, ЕГН)
    - Данни за фирмата
    - Длъжност
    - Трудова характеристика (job_description)
    - Вид на договора
    - Заплащане
    - Работно време
    - Клаузи
    """
```

---

## 7. Frontend - TypeScript Types

### Файл: `frontend/src/types.ts`

```typescript
export interface LaborContract {
  id: number;
  employeeName: string;
  employeeEgn: string;
  companyId: number;
  company?: Company;
  position: string | null;
  jobDescription: string;
  contractType: 'permanent' | 'temporary' | 'seasonal' | 'internship';
  baseSalary: number | null;
  workHoursPerWeek: number;
  startDate: string;
  endDate: string | null;
  status: 'draft' | 'signed' | 'linked';
  signedAt: string | null;
  userId: number | null;
  employmentContractId: number | null;
  user?: User;
  createdAt: string;
}

export interface LaborContractTemplate {
  id: number;
  companyId: number;
  name: string;
  contractType: 'permanent' | 'temporary' | 'seasonal' | 'internship';
  isActive: boolean;
  jobDescriptionTemplate: string | null;
  clausesTemplate: Record<string, any> | null;
  createdAt: string;
}

export interface LaborContractClause {
  id: number;
  contractId: number;
  title: string;
  content: string;
  orderIndex: number;
}
```

---

## 8. Frontend - GraphQL Operations

### Файл: `frontend/src/graphql/operations.ts`

```typescript
// Queries
export const GET_LABOR_CONTRACTS = gql`
  query GetLaborContracts($companyId: Int, $status: String) {
    laborContracts(companyId: $companyId, status: $status) {
      id
      employeeName
      employeeEgn
      company { id name }
      position
      jobDescription
      contractType
      baseSalary
      workHoursPerWeek
      startDate
      endDate
      status
      signedAt
      userId
      user { id firstName lastName }
      employmentContractId
      createdAt
    }
  }
`;

export const GET_LABOR_CONTRACT_TEMPLATES = gql`
  query GetLaborContractTemplates($companyId: Int, $contractType: String) {
    laborContractTemplates(companyId: $companyId, contractType: $contractType) {
      id
      name
      contractType
      jobDescriptionTemplate
      clausesTemplate
    }
  }
`;

// Mutations
export const CREATE_LABOR_CONTRACT = gql`
  mutation CreateLaborContract($input: LaborContractCreateInput!) {
    createLaborContract(input: $input) {
      id
      status
    }
  }
`;

export const SIGN_LABOR_CONTRACT = gql`
  mutation SignLaborContract($id: Int!) {
    signLaborContract(id: $id) {
      id
      status
      signedAt
    }
  }
`;

export const LINK_CONTRACT_TO_USER = gql`
  mutation LinkContractToUser($contractId: Int!, $userId: Int!, $employmentContractId: Int!) {
    linkLaborContractToUser(contractId: $contractId, userId: $userId, employmentContractId: $employmentContractId) {
      id
      status
      userId
      employmentContractId
    }
  }
`;
```

---

## 9. Frontend - UI Components

### Структура на компонентите:

```
frontend/src/
├── components/
│   ├── LaborContractsList.tsx      # Списък с договори
│   ├── LaborContractDialog.tsx     # Форма за създаване/редактиране
│   ├── LaborContractCard.tsx       # Карта на един договор
│   ├── LaborContractTemplates.tsx  # Управление на шаблони
│   └── LinkUserDialog.tsx          # Диалог за свързване с потребител
```

### LaborContractsList.tsx
- Списък с всички договори
- Филтриране по статус (draft/signed/linked)
- Действия за всеки договор

### LaborContractDialog.tsx
- Избор на шаблон
- Попълване на данни
- Задължителни полета:
  - employee_name
  - employee_egn
  - job_description
- Избор на contract_type

### LaborContractCard.tsx
- Показва данните на договора
- Бутон "Генерирай PDF"
- Бутон "Принтирай"
- Бутон "Маркирай като подписан" (само за draft)
- Бутон "Свържи с потребител" (само за signed)

### LinkUserDialog.tsx
- Търсене на потребител
- Избор на employment_contract
- Бутон "Свържи"

---

## 10. PayrollPage Integration

### Нова секция в PayrollPage:

```typescript
// Секция "Трудови договори"
const LaborContractsTab = () => {
  // 1. Листване на договори
  // 2. Бутон "Нов договор"
  // 3. Филтри по статус
};
```

---

## 11. Database Migrations

### Миграции:

1. `labor_contracts_table.py` - Създава таблица labor_contracts
2. `labor_contract_templates_table.py` - Създава таблица labor_contract_templates
3. `labor_contract_clauses_table.py` - Създава таблица labor_contract_clauses

---

## 12. Implementation Order (Стъпка по Стъпка)

### Backend:
1. ➤ Database models + migrations
2. ➤ GraphQL inputs
3. ➤ GraphQL types
4. ➤ GraphQL queries
5. ➤ GraphQL mutations
6. ➤ PDF generation endpoint

### Frontend:
7. ➤ TypeScript types
8. ➤ GraphQL operations (queries + mutations)
9. ➤ LaborContractDialog component
10. ➤ LaborContractsList component  
11. ➤ LinkUserDialog component
12. ➤ Integration in PayrollPage
13. ➤ Testing

---

## 13. Status Flow

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│  draft  │────▶│ signed  │────▶│ linked  │
└─────────┘     └─────────┘     └─────────┘
    │               │               │
    │ PDF           │ Подпис        │ Свързване
    ▼               ▼               ▼
Генерирай      Маркирай         Свържи с
PDF            като подписан    потребител
```

---

## 14. Примерни SQL заявки

```sql
-- Всички договори на дадена фирма
SELECT * FROM labor_contracts WHERE company_id = 1;

-- Договори чакащи подпис
SELECT * FROM labor_contracts WHERE status = 'draft';

-- Свързани договори
SELECT lc.*, u.first_name, u.last_name 
FROM labor_contracts lc
LEFT JOIN users u ON lc.user_id = u.id
WHERE lc.status = 'linked';
```
