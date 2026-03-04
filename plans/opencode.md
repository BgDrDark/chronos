# OpenCode - Хронос Проект Документация

## Последна активност

### 16.02.2026 - Склад и Редакции

#### Направени промени:

**Backend:**
1. Добавено поле `id` в `BatchInput` за редакция на партиди
2. Добавена мутация `update_ingredient` в mutations.py
3. Добавена мутация `update_batch` в mutations.py
4. Добавено поле `product_type` в `IngredientInput` (raw/semi_finished/finished)

**Frontend (WarehousePage.tsx):**
1. Добавени бутони за редакция:
   - Продукти (бутон в таблицата)
   - Партиди (нова колона "Действия")
   - Зони за съхранение (бутон в картите)
2. Добавени модални форми за редакция:
   - Продукт: име, мерна единица, мин. наличност, зона, баркод, вид (суров/заготовка/готов), развалаем, дни за предупреждение
   - Партида: продукт, количество, срок на годност, доставчик, фактура, партиден номер, зона
3. Показване на вида и типа на зоните в картите (КМА/ДМА, Хранителен/Нехранителен)

---

# РЕЦЕПТИ - 3-ЧАСТОВА СТРУКТУРА

## Финален План за Имплементация

### Дата: 16.02.2026

---

## 1. Структура на Данните

### Database Models

#### Recipe (обновен)
```python
class Recipe(Base):
    __tablename__ = "recipes"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)           # "Торта Шоколад"
    description = Column(String, nullable=True)
    yield_quantity = Column(Numeric(12, 2), default=1.0) # Добив (брой парчета)
    yield_unit = Column(String(20), default="br")
    shelf_life_days = Column(Integer, default=7)          # Срок в хладилник
    shelf_life_frozen_days = Column(Integer, default=30)  # Срок замразена
    default_pieces = Column(Integer, default=12)          # Първоначален брой парчета
    standard_quantity = Column(Numeric(12, 2), default=1.0)
    instructions = Column(Text, nullable=True)
    company_id = Column(Integer, ForeignKey("companies.id"))
    
    # Relationships
    sections = relationship("RecipeSection", back_populates="recipe", cascade="all, delete-orphan")
```

#### RecipeSection (НОВА ТАБЛИЦА)
```python
class RecipeSection(Base):
    __tablename__ = "recipe_sections"
    id = Column(Integer, primary_key=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id", ondelete="CASCADE"))
    section_type = Column(String(20))  # "dough", "cream", "decoration"
    name = Column(String(255))           # "Блат - Торта Шоколад"
    shelf_life_days = Column(Integer, nullable=True)  # Срок на заготовката
    waste_percentage = Column(Numeric(5, 2), default=0.0)  # Фира %
    section_order = Column(Integer, default=0)  # 1, 2, 3
    
    # Relationships
    recipe = relationship("Recipe", back_populates="sections")
    ingredients = relationship("RecipeIngredient", back_populates="section")
    steps = relationship("RecipeStep", back_populates="section")
```

#### RecipeIngredient
```python
class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"
    id = Column(Integer, primary_key=True)
    section_id = Column(Integer, ForeignKey("recipe_sections.id", ondelete="CASCADE"))
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"))
    quantity_gross = Column(Numeric(12, 3))  # Количество (бруто)
    # quantity_net и waste_percentage се изчисляват автоматично
    
    # Relationships
    section = relationship("RecipeSection", back_populates="ingredients")
    ingredient = relationship("Ingredient")
```

#### RecipeStep
```python
class RecipeStep(Base):
    __tablename__ = "recipe_steps"
    id = Column(Integer, primary_key=True)
    section_id = Column(Integer, ForeignKey("recipe_sections.id", ondelete="CASCADE"))
    workstation_id = Column(Integer, ForeignKey("workstations.id"))
    name = Column(String(255), nullable=False)
    step_order = Column(Integer, default=0)
    estimated_duration_minutes = Column(Integer, nullable=True)
    
    # Relationships
    section = relationship("RecipeSection", back_populates="steps")
    workstation = relationship("Workstation")
```

---

## 2. GraphQL Schema

### Inputs

#### RecipeSectionInput
```python
class RecipeSectionInput:
    section_type: str  # "dough" | "cream" | "decoration"
    name: str
    shelf_life_days: Optional[int] = None
    waste_percentage: Decimal = Decimal("0")
    section_order: int = 0
    ingredients: List[RecipeIngredientInput]
    steps: List[RecipeStepInput]
```

#### RecipeIngredientInput
```python
class RecipeIngredientInput:
    ingredient_id: int
    quantity_gross: Decimal  # Само бруто
    # НЕТО се изчислява автоматично
```

#### RecipeInput (обновен)
```python
class RecipeInput:
    name: str
    description: Optional[str] = None
    yield_quantity: Decimal = Decimal("1.0")
    yield_unit: str = "br"
    shelf_life_days: int = 7
    shelf_life_frozen_days: int = 30
    default_pieces: int = 12
    standard_quantity: Decimal = Decimal("1.0")
    instructions: Optional[str] = None
    company_id: int
    sections: List[RecipeSectionInput]  # 3-те части
```

### Types

#### RecipeSectionType
```python
class RecipeSectionType:
    id: int
    section_type: str
    name: str
    shelf_life_days: Optional[int]
    waste_percentage: float
    section_order: int
    total_gross: float        # Изчислено автоматично
    total_net: float          # Изчислено автоматично
    ingredients: List[RecipeIngredientType]
    steps: List[RecipeStepType]
```

#### RecipeType (обновен)
```python
class RecipeType:
    id: int
    name: str
    default_pieces: int
    shelf_life_days: int
    shelf_life_frozen_days: int
    sections: List[RecipeSectionType]
```

---

## 3. Frontend - RecipesPage

### State
```typescript
const [recipeForm, setRecipeForm] = useState({
  name: '',                           // "Торта Шоколад"
  defaultPieces: 12,                  // Първоначален брой
  currentPieces: 12,                  // Текущ брой (за манипулация)
  shelfLifeFridgeDays: 7,             // Срок в хладилник
  shelfLifeFrozenDays: 30,            // Срок замразена
  
  sections: [
    { 
      type: 'dough', 
      name: 'Блат - ', 
      shelfLifeDays: null,
      wastePercentage: 10,
      ingredients: [], 
      steps: [] 
    },
    { 
      type: 'cream', 
      name: 'Крем - ', 
      shelfLifeDays: null,
      wastePercentage: 5,
      ingredients: [], 
      steps: [] 
    },
    { 
      type: 'decoration', 
      name: 'Декор - ', 
      shelfLifeDays: null,
      wastePercentage: 15,
      ingredients: [], 
      steps: [] 
    }
  ]
});
```

### UI Структура

```
┌─────────────────────────────────────────────────────────────┐
│  СЪЗДАВАНЕ НА РЕЦЕПТА                                       │
├─────────────────────────────────────────────────────────────┤
│  Име на продукта: [Торта Шоколад______________________]   │
│                                                             │
│  Бр. парчета: [12]  [-]  (Default)  [+]                   │
│  Срок (хладилник): [7] дни  Срок (замразена): [30] дни   │
└─────────────────────────────────────────────────────────────┘

▼ ЧАСТ 1: ПЕКАРНА - Блат - Торта Шоколад
  ┌────────────────────────────────────────────────┐
  │ Срок на заготовката: [____] дни                 │
  │ Фира: [10]%                                   │
  │                                                │
  │ СЪСТАВКИ:                                     │
  │ [+ Добави съставка]                            │
  │                                                │
  │ 1. Брашно    [300] g                         │
  │ 2. Захар     [150] g                         │
  │                                                │
  │────────────────────────────────────────────────│
  │ ОБЩО: 650g                                   │
  │ НЕТО: 585g                                   │
  │                                                │
  │ СТЪПКИ:                                        │
  │ [+ Добави стъпка]                              │
  │   1. Разбъркване                               │
  └────────────────────────────────────────────────┘

▼ ЧАСТ 2: КРЕМОВЕ - Крем - Торта Шоколад
  ...

▼ ЧАСТ 3: ДЕКОРАЦИЯ - Декор - Торта Шоколад
  ...
```

### Функционалности

1. **+/- бутони** - променят `currentPieces` и преизчисляват всички количества
   ```
   Ново количество = (Старо количество / oldPieces) * newPieces
   ```

2. **Default бутон** - връща `currentPieces` = `defaultPieces`

3. **Generate name** - при промяна на `name`, обновява имената на секциите:
   - "Блат - {recipeName}"
   - "Крем - {recipeName}"
   - "Декор - {recipeName}"

4. **+ за съставки** - добавя нова съставка в секцията

5. **+ за стъпки** - добавя нова стъпка (първата е задължителна)

6. **Сгъване/разгъване** на секциите

7. **Автоматично изчисление**:
   - ОБЩО = сума от всички quantity_gross
   - НЕТО = ОБЩО - (ОБЩО × waste_percentage / 100)

---

## 4. Имплементация - Стъпки

### Backend:
1. [ ] Добавяне на нови колони в Recipe модел
2. [ ] Създаване на RecipeSection модел
3. [ ] Обновяване на RecipeIngredient и RecipeStep модели
4. [ ] Обновяване на GraphQL Types
5. [ ] Обновяване на GraphQL Inputs
6. [ ] Обновяване на Mutations (create/update recipe)

### Frontend:
1. [ ] Обновяване на State структура
2. [ ] Създаване на UI за хедъра (име, брой парчета, срокове)
3. [ ] Създаване на 3-те секции (Accordion)
4. [ ] Имплементация на +/- и Default бутони
5. [ ] Имплементация на калкулацията
6. [ ] Имплементация на добавяне на съставки и стъпки
7. [ ] Обновяване на записа

---

## 5. За бъдеще (V2)

- **Независими заготовки** - отделни обекти, които могат да се използват в различни рецепти
- Пример: "Блат Шоколадов" може да се използва в "Торта Шоколад" и в "Торта Червено бархат"

---

## Docker Services

- **chronos-backend** - Python/FastAPI/Strawberry GraphQL
- **chronos-frontend** - React/Vite/PWA
- **chronos-DB** - PostgreSQL

---

## Команди

```bash
# Билд на бекенд
docker compose build backend

# Билд на фронтенд
docker compose build frontend

# Рестарт на услугите
docker compose up -d backend
docker compose up -d frontend

# Логове
docker compose logs -f backend
docker compose logs -f frontend
```


Какво е направено до момента:
Backend:
1. ✅ Обновени модели (models.py):
   - Recipe - добавени: shelf_life_frozen_days, default_pieces
   - Нова таблица RecipeSection - за 3-те части (dough/cream/decoration)
   - RecipeIngredient - добавено section_id, премахнати quantity_net, waste_percentage
   - RecipeStep - добавено section_id
2. ✅ Обновени GraphQL Types (types.py):
   - RecipeSection - нов тип
   - RecipeIngredient - премахнати quantity_net, waste_percentage
   - RecipeStep - премахнати brutto_g, net_g
   - Recipe - добавени нови полета и sections
3. ✅ Обновени GraphQL Inputs (inputs.py):
   - RecipeSectionInput - нов input
   - RecipeIngredientInput - само ingredient_id, quantity_gross
   - RecipeInput - добавени sections, shelf_life_frozen_days, default_pieces
4. ✅ Обновена мутация create_recipe - създава секции и техните съставки/стъпки
Frontend:
1. ✅ Обновена GraphQL заявка - връща sections вместо ingredients/steps
2. ✅ Добавени нови компоненти (Accordion, AccordionSummary, AccordionDetails, ExpandMoreIcon)
3. ✅ Ново състояние на формата (recipeForm) - с 3-те секции
4. ✅ Нови функции:
   - handlePiecesChange - +- преизчислява количества
   - handleResetPieces - връща на default
   - handleNameChange - обновява имената на секциите
   - handleAddIngredient/RemoveIngredient - за всяка секция
   - handleAddStep/RemoveStep - за всяка секция
   - calculateSectionTotals - ОБЩО и НЕТО
5. ✅ Обновен handleAddRecipe - записва със секции

---
анализирай RecipesPage.tsx как сме направил компонент `ValidatedTextField` с Тултипи при hover, добавена валидация червена/зелена рамка


### 17.02.2026 - Валидация и Тултипи

**Frontend (RecipesPage.tsx):**

1. ✅ Добавен компонент `ValidatedTextField` с:
   - Тултипи при hover
   - Червена рамка при грешка
   - Зелена рамка при валидна стойност

2. ✅ Добавена валидация:
   - Име на рецепта (мин. 2 символа)
   - Добив (> 0)
   - Срок в хладилник (1-365 дни)
   - Срок замразена (1-730 дни)
   - Име на секцията
   - Съставки (задължителни: избор + количество > 0)

3. ✅ Валидацията се стартира при "Запази Рецепта" и показва грешки

4. ✅ Почистени неизползвани променливи и функции

**Database:**
- Добавени колони в recipes: shelf_life_frozen_days, default_pieces
- Създадена таблица recipe_sections
- Добавени section_id в recipe_ingredients и recipe_steps

---

### 17.02.2026 - Дневник (Journal) + Месечен/Годишен отчет

#### Направени промени:

**Backend:**

1. ✅ **Нови модели** (models.py):
   - `CashJournalEntry` - касов дневник (приходи/разходи в брой)
   - `OperationLog` - дневник на операциите (create/update/delete на фактури)
   - `DailySummary` - дневен отчет
   - `MonthlySummary` - месечен отчет
   - `YearlySummary` - годишен отчет

2. ✅ **Нови GraphQL типове** (types.py):
   - `CashJournalEntryType`
   - `OperationLogType`
   - `DailySummaryType`
   - `MonthlySummaryType`
   - `YearlySummaryType`

3. ✅ **Нови GraphQL заявки** (queries.py):
   - `cash_journal_entries` - с филтри по дата и тип операция
   - `operation_logs` - с филтри по дата и тип операция
   - `daily_summaries` - с филтри по период
   - `monthly_summaries` - с филтри по диапазон от години
   - `yearly_summaries` - с филтри по диапазон от години

4. ✅ **Нови мутации** (mutations.py):
   - `create_cash_journal_entry` - ръчно добавяне на касова операция
   - `delete_cash_journal_entry` - изтриване (само меки, 10 год. запазване)
   - `generate_daily_summary` - генериране на дневен отчет
   - `generate_monthly_summary` - генериране на месечен отчет
   - `generate_yearly_summary` - генериране на годишен отчет

5. ✅ **Автоматизация**:
   - При плащане на фактура в брой (paymentMethod='cash' + status='paid') -> автоматично създава касов запис
   - Всички create/update/delete операции на фактури -> записват се в operation_logs

**Frontend (AccountingPage.tsx):**

1. ✅ **Нови табове**:
   - 💰 **Касов дневник** - приходи/разходи в брой
     - Филтри: дата от/до, тип операция
     - Таблица със зелени редове за приходи, червени за разходи
     - Бутон за ръчно добавяне
     - Изтриване
   - 📋 **Операции** - дневник на всички операции
     - Филтри: дата от/до, тип операция
     - Таблица с timestamp, операция, обект, потребител
   - 📊 **Дневен отчет** - автоматични дневни суми
     - Филтри: дата от/до
     - Бутон "Генерирай" за конкретна дата
     - Колони: дата, брой фактури, обща сума, приход каса, разход каса, баланс, ДДС събран, ДДС платен
   - 📅 **Месечен отчет** - агрегирани месечни данни
     - Филтри: от година, до година
     - Бутон "Генерирай" за конкретна година и месец
     - Колони: период, брой фактури, входящи, изходящи, сума, приход, разход, баланс, ДДС
   - 📆 **Годишен отчет** - агрегирани годишни данни
     - Филтри: от година, до година
     - Бутон "Генерирай" за конкретна година
     - Колони: година, брой фактури, входящи, изходящи, сума, приход, разход, баланс, ДДС

2. ✅ **GraphQL заявки и мутации**:
   - GET_CASH_JOURNAL_ENTRIES
   - CREATE_CASH_JOURNAL_ENTRY
   - DELETE_CASH_JOURNAL_ENTRY
   - GET_OPERATION_LOGS
   - GET_DAILY_SUMMARIES
   - GENERATE_DAILY_SUMMARY
   - GET_MONTHLY_SUMMARIES
   - GENERATE_MONTHLY_SUMMARY
   - GET_YEARLY_SUMMARIES
   - GENERATE_YEARLY_SUMMARY

**Бази данни:**
- Създадени таблици: cash_journal_entries, operation_logs, daily_summaries, monthly_summaries, yearly_summaries
- Индекси за бързо търсене по дата

---

### 17.02.2026 - N+1 Оптимизация с DataLoaders

**Проблем:**
- N+1 заявки при зареждане на свързани обекти (supplier, batch, ingredient, storage_zone)
- Пример: 10 фактури с по 5 артикула = 10 + 10*5 = 60 заявки вместо 1-2

**Решение - DataLoader патърн:**

1. ✅ **Нови DataLoader функции** (dataloaders.py):
   - `load_suppliers` - зарежда multiple suppliers
   - `load_ingredients` - зарежда multiple ingredients
   - `load_batches` - зарежда multiple batches
   - `load_storage_zones` - зарежда multiple storage zones
   - `load_recipes` - зарежда multiple recipes
   - `load_invoice_items` - зарежда артикули по invoice_id

2. ✅ **Регистрирани в create_dataloaders**:
   - supplier_by_id
   - ingredient_by_id
   - batch_by_id
   - storage_zone_by_id
   - recipe_by_id
   - invoice_items_by_invoice_id

3. ✅ **Обновени типове да използват DataLoaders**:
   - Invoice: supplier, batch, items
   - InvoiceItem: ingredient, batch
   - Ingredient: storage_zone
   - Batch: ingredient, supplier, storage_zone
   - RecipeIngredient: ingredient

**Резултат:**
- Преди: 1 + N заявки (N = брой свързани обекти)
- Сега: 1 (основна) + 1 (batch loader) = 2 заявки

---

# План за подобрена сигурност

## Цел

Имплементация на подобрена сигурност за Chronos приложението чрез:
1. HttpOnly Cookie за CSRF токен
2. Secure Cookie
3. SameSite=Strict
4. Bearer Token в HttpOnly Cookie
5. CSRF за всички mutations

---

## Текущо състояние

| Компонент | Текуща стойност | Нова стойност |
|-----------|-----------------|---------------|
| CSRF Cookie | `HttpOnly=false`, `Secure=false`, `SameSite=lax` | `HttpOnly=true`, `Secure=true`, `SameSite=Strict` |
| Auth Token | localStorage | HttpOnly Cookie |
| CSRF Protected URLs | Само `/admin/*` | Всички mutations |

---

## Стъпки за имплементация

### Стъпка 1: Бекенд - Конфигурация на CSRF Middleware

**Файл:** `backend/main.py`

```python
import re
app.add_middleware(
    CSRFMiddleware,
    secret=settings.CSRF_SECRET_KEY,
    cookie_name="csrf_token",
    cookie_path="/",
    cookie_domain=None,
    cookie_secure=True,          # HTTPS only
    cookie_httponly=True,       # Недостъпен за JS
    cookie_samesite="strict",   # Strict same-site policy
    required_urls=[
        re.compile(r".*"),       # Всички URL-ове
    ],
    safe_methods={"GET", "HEAD", "OPTIONS", "TRACE"},
)
```

### Стъпка 2: Бекенд - Auth Token в HttpOnly Cookie

**Файл:** `backend/main.py`

Добави нов endpoint за login който връща token в HttpOnly cookie:

```python
@app.post("/auth/login")
async def login(response: Response, form_data: OAuth2PasswordRequestForm = Depends()):
    # ... валидация ...
    
    # Създай access token
    access_token = create_access_token(data={"sub": user.email})
    
    # Запази в HttpOnly cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,        # Недостъпен за JS
        secure=True,          # HTTPS only  
        samesite="strict",   # Strict
        path="/",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    return {"access_token": access_token, "token_type": "bearer"}
```

### Стъпка 3: Бекенд - Валидация на Token от Cookie

**Файл:** `backend/auth.py`

Актуализирай `get_current_user` да чете от cookie:

```python
async def get_current_user(request: Request):
    # Първо опитай от cookie
    token = request.cookies.get("access_token")
    
    # Ако няма в cookie, опитай от header (за backward compatibility)
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Валидирай token...
```

### Стъпка 4: Бекенд - Logout

**Файл:** `backend/main.py`

```python
@app.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie(
        key="access_token",
        path="/",
        secure=True,
        samesite="strict"
    )
    response.delete_cookie(
        key="csrf_token", 
        path="/",
        secure=True,
        samesite="strict"
    )
    return {"message": "Logged out"}
```

### Стъпка 5: Фронтенд - Премахване на localStorage

**Файл:** `frontend/src/apolloClient.ts`

```typescript
// Премахни localStorage.getItem('token')
// Използвай credentials: 'include' за всички заявки
```

### Стъпка 6: Фронтенд - CSRF от HttpOnly Cookie

**Файл:** `frontend/src/apolloClient.ts`

```typescript
// Тъй като CSRF cookie е HttpOnly, НЕ можем да го четем с JS
// Вместо това - използвай Double Submit Cookie автоматично от браузъра
```

### Стъпка 7: Фронтенд - Login/Logout

**Файл:** `frontend/src/pages/LoginPage.tsx`

```typescript
// Премахни localStorage.setItem('token', ...)
// Използвай credentials: 'include' 
```

**Файл:** `frontend/src/components/MainLayout.tsx`

```typescript
// Премахни localStorage.removeItem('token')
```

---

## Файлове за промяна

| Файл | Промяна |
|------|---------|
| `backend/main.py` | CSRF конфигурация, login/logout endpoints |
| `backend/auth.py` | Token validation от cookie |
| `frontend/src/apolloClient.ts` | Премахни localStorage, използвай credentials |
| `frontend/src/pages/LoginPage.tsx` | Cookie-based login |
| `frontend/src/components/MainLayout.tsx` | Cookie-based logout |

---

## Тестване

1. **Login** - след login, token е в HttpOnly cookie
2. **CSRF** - можем да направим mutation само от правилния origin
3. **XSS** - крадци не могат да откраднат token (HttpOnly)
4. **Logout** - cookie се изтрива коректно
5. **GraphQL** - всички mutations работят с новата автентикация

---

## Рискове и миграция

| Риск | Решение |
|------|---------|
| Breaking changes за съществуващи клиенти | Backward compatibility - поддържай и header auth |
| Third-party интеграции | Добави exception за API endpoints |
| Проблеми с browser cookies | Тествай в различни браузъри |

---

## Приоритет на имплементация

1. **Фаза 1:** CSRF конфигурация (secure, httponly, samesite=strict)
2. **Фаза 2:** Login връща token в cookie
3. **Фаза 3:** Backend чете token от cookie
4. **Фаза 4:** Frontend използва credentials: 'include'
5. **Фаза 5:** Тестване и фиксове

---

##.2026 - 18.02 Подобрена сигурност (Session Management)

### Направени промени:

**Backend:**
1. ✅ CSRF конфигурация с `Secure=True`, `SameSite=Strict`
2. ✅ Auth token в HttpOnly cookie (Secure, SameSite=Strict)
3. ✅ Refresh token в HttpOnly cookie
4. ✅ CSRF protected всички URL-ове освен `/auth/*`, `/graphql`, `/google/*`

**Frontend:**
1. ✅ Премахнато localStorage за token
2. ✅ Използва `credentials: 'include'` за всички заявки
3. ✅ CSRF token от cookie (double-submit pattern)

---

## 18.02.2026 - Автоматичен Session Lock (Без парола)

### Проблем:
- При изтичане на session потребителят се пренасочва директно към /login
- Ако потребителят редактира нещо - губи работата си

### Решение:
- Автоматичен session refresh при активност
- Redirect to login само след X минути неактивност

### Направени промени:

**Frontend:**
1. ✅ Нов hook `frontend/src/hooks/useSessionActivity.ts`:
   - Следи активността на потребителя (mousemove, keydown, click, scroll, touchstart)
   - Auto-refresh на session при активност
   - Redirect to /login след 15 минути неактивност

2. ✅ Модифициран `frontend/src/components/MainLayout.tsx`:
   - Интегриран `useSessionActivity` hook
   - При неактивност > 15 мин → redirect to /login

### Конфигурация:
- **Idle timeout**: 15 минути (15 * 60 * 1000 ms)
- **Refresh before**: 5 минути преди изтичане

### Как работи:
1. Докато потребителят е активен → session се поддържа alive
2. След 15 мин неактивност → redirect to /login
3. Няма нужда от парола (вече си логнат)
4. Няма бутони - всичко е автоматично