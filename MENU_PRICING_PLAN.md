# 🍰 ПЪЛЕН ПЛАН: MENU/PRICING СИСТЕМА

**Версия:** 1.0  
**Дата:** 21.03.2026  
**Статус:** Планиране завършено

---

## 1. АНАЛИЗ НА СЪЩЕСТВУВАЩОТО СЪСТОЯНИЕ

### 1.1 Съществуваща архитектура

```
┌────────────────────────────────────────────────────────────────┐
│ ПРИЕМ НА СТОКА                                                  │
│ Supplier Invoice → Batch (с цена) → Ingredient.current_price   │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│ РЕЦЕПТА                                                        │
│ Recipe                                                         │
│  ├── sections[]                                                 │
│  │     └── ingredients[]                                        │
│  │           └── quantity_gross × current_price = COST        │
│  └── waste_percentage (фира %)                                 │
└────────────────────────────────────────────────────────────────┘
```

### 1.2 Липсващи функционалности

| # | Проблем | Статус |
|---|---------|--------|
| 1 | Няма калкулатор на себестойност | ❌ Липсва |
| 2 | Няма поле за продажна цена | ❌ Липсва |
| 3 | Няма марж % | ❌ Липсва |
| 4 | Няма надценка | ❌ Липсва |
| 5 | Цената се въвежда ръчно при продажба | ❌ Липсва |

---

## 2. ОСНОВНИ РЕШЕНИЯ

### 2.1 Формула за крайна цена

```
Продажна цена = Себестойност + Марж + Надценка

Където:
  - Себестойност = Σ (количество_neto × единична цена)
  - количество_neto = количество_gross × (1 - фира% / 100)
  - единична цена = Ingredient.current_price

Пример:
  Себестойност: 8.59 лв
  Марж (26%):   2.23 лв
  Надценка:     1.00 лв
  ───────────────────────────
  Продажна:    11.82 лв
```

### 2.2 Полета в Recipe модела

| Поле | Тип | Описание |
|------|-----|----------|
| `selling_price` | Decimal | Продажна цена |
| `cost_price` | Decimal | Себестойност (изчислена) |
| `markup_percentage` | Decimal | Марж % |
| `premium_amount` | Decimal | Надценка (лв) |
| `portions` | Integer | Брой порции |
| `last_price_update` | DateTime | Кога е обновена цената |
| `price_calculated_at` | DateTime | Кога е изчислена себестойността |

### 2.3 Вариянти за въвеждане

| Поле | Вариянт 1 | Вариянт 2 |
|------|-----------|-----------|
| Марж % | Въвежда се (%) | Изчислява се от лв |
| Надценка | Въвежда се (лв) | Изчислява се от % |

**Подразбиране:** Марж % (вторият 1)

### 2.4 Ако Марж % е 0 или празно

```
Продажна цена = Себестойност + Надценка
```

---

## 3. ПЪЛЕН ПЛАН ЗА ИМПЛЕМЕНТАЦИЯ

### ФАЗА 1: ОСНОВНИ ПОЛЕТА В МОДЕЛА 🔴

#### 3.1 Промяна на Recipe модела

**Файл:** `backend/database/models.py`

```python
class Recipe(Base):
    # ... съществуващи полета ...
    
    # НОВИ ПОЛЕТА ЗА PRICING
    selling_price = Column(Numeric(10, 2), nullable=True)
    cost_price = Column(Numeric(10, 2), nullable=True)
    markup_percentage = Column(Numeric(5, 2), default=0)
    premium_amount = Column(Numeric(10, 2), default=0)
    portions = Column(Integer, default=1)
    last_price_update = Column(DateTime, nullable=True)
    price_calculated_at = Column(DateTime, nullable=True)
```

#### 3.2 Нова таблица: PriceHistory

```python
class PriceHistory(Base):
    """История на промените на цените"""
    id = Column(Integer, primary_key=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    old_price = Column(Numeric(10, 2))
    new_price = Column(Numeric(10, 2))
    old_cost = Column(Numeric(10, 2))
    new_cost = Column(Numeric(10, 2))
    old_markup = Column(Numeric(5, 2))
    new_markup = Column(Numeric(5, 2))
    old_premium = Column(Numeric(10, 2))
    new_premium = Column(Numeric(10, 2))
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    changed_at = Column(DateTime, default=datetime.utcnow)
    reason = Column(String(255))
```

#### 3.3 GraphQL Types

**Файл:** `backend/graphql/types.py`

```python
@strawberry.type
class Recipe:
    # ... съществуващи полета ...
    
    # PRICING
    selling_price: Optional[Decimal]
    cost_price: Optional[Decimal]
    markup_percentage: Decimal
    premium_amount: Decimal
    portions: int
    
    @strawberry.field
    def markup_amount(self) -> Decimal:
        """Изчислена стойност на маржа в лв"""
        if not self.cost_price or not self.markup_percentage:
            return Decimal("0")
        return self.cost_price * self.markup_percentage / 100
    
    @strawberry.field
    def final_price(self) -> Decimal:
        """Крайна продажна цена"""
        base = self.cost_price or Decimal("0")
        markup = self.markup_amount
        premium = self.premium_amount or Decimal("0")
        return base + markup + premium
    
    @strawberry.field
    def portion_price(self) -> Optional[Decimal]:
        """Цена за 1 порция"""
        if self.portions and self.portions > 0:
            return self.final_price / self.portions
        return None
```

#### 3.4 GraphQL Input

**Файл:** `backend/graphql/inputs.py`

```python
@strawberry.input
class RecipePriceInput:
    selling_price: Optional[Decimal] = None
    cost_price: Optional[Decimal] = None
    markup_percentage: Optional[Decimal] = None
    premium_amount: Optional[Decimal] = None
    portions: Optional[int] = None
    reason: Optional[str] = None

@strawberry.input
class RecipePriceUpdateInput:
    markup_percentage: Optional[Decimal] = None
    premium_amount: Optional[Decimal] = None
    portions: Optional[int] = None
    reason: str
```

---

### ФАЗА 2: КАЛКУЛАТОР НА СЕБЕСТОЙНОСТ 🔴

#### 3.5 Нова услуга

**Файл:** `backend/services/recipe_cost_calculator.py`

```python
from decimal import Decimal
from typing import Optional

class RecipeCostCalculator:
    """Калкулатор за себестойност на рецепти"""
    
    @staticmethod
    def calculate_recipe_cost(db, recipe_id: int) -> Decimal:
        """
        Изчислява себестойността на рецепта
        
        Формула:
          себестойност = Σ (количество_neto × единична цена)
        """
        from backend.database.models import Recipe, RecipeSection, RecipeIngredient
        
        recipe = db.get(Recipe, recipe_id)
        if not recipe:
            raise ValueError("Рецепта не е намерена")
        
        total_cost = Decimal("0")
        
        for section in recipe.sections:
            section_cost = Decimal("0")
            
            for ri in section.ingredients:
                ingredient = ri.ingredient
                if not ingredient or not ingredient.current_price:
                    continue
                
                # Бруто количество
                gross_qty = Decimal(str(ri.quantity_gross or 0))
                
                # Нето количество (след фира)
                waste_pct = Decimal(str(section.waste_percentage or 0))
                net_qty = gross_qty * (1 - waste_pct / 100)
                
                # Цена за това количество
                cost = net_qty * Decimal(str(ingredient.current_price))
                section_cost += cost
            
            total_cost += section_cost
        
        return total_cost
    
    @staticmethod
    def calculate_final_price(
        cost_price: Decimal,
        markup_percentage: Optional[Decimal] = None,
        premium_amount: Optional[Decimal] = None
    ) -> Decimal:
        """
        Изчислява крайната продажна цена
        
        Формула:
          продажна = себестойност + марж + надценка
        """
        markup = Decimal("0")
        if markup_percentage and markup_percentage > 0:
            markup = cost_price * markup_percentage / 100
        
        premium = premium_amount or Decimal("0")
        
        return cost_price + markup + premium
```

---

### ФАЗА 3: GRAPHQL MUTATIONS 🔴

#### 3.6 Mutations за цени

**Файл:** `backend/graphql/mutations.py`

```python
@strawberry.mutation
async def update_recipe_price(
    self,
    recipe_id: int,
    input: RecipePriceUpdateInput,
    info: strawberry.Info
) -> types.Recipe:
    """Обнови цена на рецепта"""
    db = info.context["db"]
    current_user = info.context["current_user"]
    
    recipe = await db.get(models.Recipe, recipe_id)
    if not recipe:
        raise not_found("Рецепта не е намерена")
    
    # Запиши в историята
    history = models.PriceHistory(
        recipe_id=recipe_id,
        old_price=recipe.selling_price,
        old_cost=recipe.cost_price,
        old_markup=recipe.markup_percentage,
        old_premium=recipe.premium_amount,
        new_markup=input.markup_percentage,
        new_premium=input.premium_amount,
        changed_by=current_user.id,
        reason=input.reason
    )
    
    # Актуализирай рецептата
    if input.markup_percentage is not None:
        recipe.markup_percentage = input.markup_percentage
    
    if input.premium_amount is not None:
        recipe.premium_amount = input.premium_amount
    
    if input.portions is not None:
        recipe.portions = input.portions
    
    # Изчислени новата продажна цена
    cost = recipe.cost_price or Decimal("0")
    recipe.selling_price = RecipeCostCalculator.calculate_final_price(
        cost,
        recipe.markup_percentage,
        recipe.premium_amount
    )
    recipe.last_price_update = datetime.utcnow()
    
    db.add(history)
    await db.commit()
    await db.refresh(recipe)
    
    return types.Recipe.from_instance(recipe)

@strawberry.mutation
async def calculate_recipe_cost(
    self,
    recipe_id: int,
    info: strawberry.Info
) -> types.RecipeCostResult:
    """Изчисли себестойността на рецепта"""
    db = info.context["db"]
    
    cost = RecipeCostCalculator.calculate_recipe_cost(db, recipe_id)
    
    recipe = await db.get(models.Recipe, recipe_id)
    final_price = RecipeCostCalculator.calculate_final_price(
        cost,
        recipe.markup_percentage if recipe else None,
        recipe.premium_amount if recipe else None
    )
    
    markup_amount = Decimal("0")
    if recipe and recipe.markup_percentage and recipe.markup_percentage > 0:
        markup_amount = cost * recipe.markup_percentage / 100
    
    return types.RecipeCostResult(
        recipe_id=recipe_id,
        cost_price=cost,
        markup_amount=markup_amount,
        premium_amount=recipe.premium_amount if recipe else Decimal("0"),
        final_price=final_price
    )

@strawberry.mutation
async def recalculate_all_recipe_costs(
    self,
    info: strawberry.Info
) -> int:
    """Преизчисли себестойността на всички рецепти"""
    db = info.context["db"]
    current_user = info.context["current_user"]
    
    recipes = await db.execute(
        select(models.Recipe).where(models.Recipe.company_id == current_user.company_id)
    )
    
    count = 0
    for recipe in recipes.scalars().all():
        cost = RecipeCostCalculator.calculate_recipe_cost(db, recipe.id)
        recipe.cost_price = cost
        recipe.price_calculated_at = datetime.utcnow()
        
        if recipe.markup_percentage or recipe.premium_amount:
            recipe.selling_price = RecipeCostCalculator.calculate_final_price(
                cost,
                recipe.markup_percentage,
                recipe.premium_amount
            )
        
        count += 1
    
    await db.commit()
    return count
```

#### 3.7 GraphQL Types за резултат

```python
@strawberry.type
class RecipeCostResult:
    recipe_id: int
    cost_price: Decimal
    markup_amount: Decimal
    premium_amount: Decimal
    final_price: Decimal
```

---

### ФАЗА 4: GRAPHQL QUERIES 🟡

#### 3.8 Queries

**Файл:** `backend/graphql/queries.py`

```python
@strawberry.field
async def recipes_with_prices(
    self,
    info: strawberry.Info,
    category_id: Optional[int] = None
) -> List[types.Recipe]:
    """Всички рецепти с цени"""
    db = info.context["db"]
    current_user = info.context["current_user"]
    
    stmt = select(models.Recipe).where(
        models.Recipe.company_id == current_user.company_id
    )
    
    if category_id:
        stmt = stmt.where(models.Recipe.category_id == category_id)
    
    res = await db.execute(stmt)
    return [types.Recipe.from_instance(r) for r in res.scalars().all()]

@strawberry.field
async def price_history(
    self,
    info: strawberry.Info,
    recipe_id: int,
    limit: int = 20
) -> List[types.PriceHistory]:
    """История на промените на цената"""
    db = info.context["db"]
    
    stmt = select(models.PriceHistory).where(
        models.PriceHistory.recipe_id == recipe_id
    ).order_by(desc(models.PriceHistory.changed_at)).limit(limit)
    
    res = await db.execute(stmt)
    return [types.PriceHistory.from_instance(h) for h in res.scalars().all()]
```

---

### ФАЗА 5: FRONTEND - ЦЕНИ РЕЦЕПТИ 🟡

#### 3.9 Нова страница

**Файл:** `frontend/src/pages/MenuPricingPage.tsx`

```tsx
function MenuPricingPage() {
  // ... state за рецепти, цени, филтри ...

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h5">Цени Рецепти</Typography>
        <Button startIcon={<RefreshIcon />} onClick={handleRecalculate}>
          Преизчисли всички
        </Button>
      </Box>

      {/* Филтри */}
      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid size={{ xs: 12, md: 4 }}>
          <TextField
            fullWidth
            size="small"
            placeholder="Търси рецепта..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </Grid>
      </Grid>

      {/* Таблица с рецепти */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Рецепта</TableCell>
              <TableCell align="right">Себестойност</TableCell>
              <TableCell align="right">Марж %</TableCell>
              <TableCell align="right">Надценка</TableCell>
              <TableCell align="right">Продажна</TableCell>
              <TableCell>Действия</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredRecipes.map((recipe) => (
              <TableRow key={recipe.id}>
                <TableCell>{recipe.name}</TableCell>
                <TableCell align="right">
                  {recipe.costPrice?.toFixed(2)} лв
                </TableCell>
                <TableCell align="right">
                  {recipe.markupPercentage > 0 
                    ? `${recipe.markupPercentage}%` 
                    : '-'}
                </TableCell>
                <TableCell align="right">
                  {recipe.premiumAmount > 0 
                    ? `${recipe.premiumAmount} лв` 
                    : '-'}
                </TableCell>
                <TableCell align="right" sx={{ fontWeight: 'bold' }}>
                  {recipe.sellingPrice?.toFixed(2)} лв
                </TableCell>
                <TableCell>
                  <IconButton onClick={() => openEditDialog(recipe)}>
                    <EditIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Диалог за редакция */}
      <RecipePriceDialog
        open={dialogOpen}
        recipe={selectedRecipe}
        onClose={() => setDialogOpen(false)}
        onSave={handleSavePrice}
      />
    </Box>
  );
}
```

#### 3.10 Диалог за редакция на цена

**Файл:** `frontend/src/components/RecipePriceDialog.tsx`

```tsx
interface RecipePriceDialogProps {
  open: boolean;
  recipe: Recipe | null;
  onClose: () => void;
  onSave: (data: RecipePriceData) => void;
}

function RecipePriceDialog({ open, recipe, onClose, onSave }: RecipePriceDialogProps) {
  const [markupPercent, setMarkupPercent] = useState('');
  const [premiumAmount, setPremiumAmount] = useState('');
  const [reason, setReason] = useState('');

  // При отваряне - зареди стойностите
  useEffect(() => {
    if (recipe) {
      setMarkupPercent(recipe.markupPercentage?.toString() || '');
      setPremiumAmount(recipe.premiumAmount?.toString() || '');
    }
  }, [recipe]);

  // Изчисление на крайната цена
  const calculateFinalPrice = () => {
    if (!recipe?.costPrice) return 0;
    
    const cost = Number(recipe.costPrice);
    const markup = Number(markupPercent || 0);
    const premium = Number(premiumAmount || 0);
    
    const markupAmount = cost * (markup / 100);
    return cost + markupAmount + premium;
  };

  const finalPrice = calculateFinalPrice();
  const markupAmount = recipe?.costPrice 
    ? Number(recipe.costPrice) * (Number(markupPercent || 0) / 100) 
    : 0;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Цена: {recipe?.name}</DialogTitle>
      <DialogContent>
        <Grid container spacing={2}>
          <Grid size={{ xs: 12 }}>
            <Typography variant="body2" color="text.secondary">
              Себестойност: {recipe?.costPrice?.toFixed(2)} лв
            </Typography>
          </Grid>

          <Grid size={{ xs: 6 }}>
            <TextField
              fullWidth
              label="Марж %"
              type="number"
              value={markupPercent}
              onChange={(e) => setMarkupPercent(e.target.value)}
              inputProps={{ min: 0, max: 100 }}
            />
            {markupAmount > 0 && (
              <Typography variant="caption" color="text.secondary">
                = {markupAmount.toFixed(2)} лв
              </Typography>
            )}
          </Grid>

          <Grid size={{ xs: 6 }}>
            <TextField
              fullWidth
              label="Надценка (лв)"
              type="number"
              value={premiumAmount}
              onChange={(e) => setPremiumAmount(e.target.value)}
              inputProps={{ min: 0 }}
            />
          </Grid>

          <Grid size={{ xs: 12 }}>
            <Divider />
            <Box sx={{ mt: 2 }}>
              <Typography variant="h6" align="center">
                Продажна цена: {finalPrice.toFixed(2)} лв
              </Typography>
              {markupAmount > 0 && premiumAmount > 0 && (
                <Typography variant="caption" align="center" display="block">
                  Марж: {markupAmount.toFixed(2)} лв ({markupPercent}%) + 
                  Надценка: {premiumAmount} лв
                </Typography>
              )}
            </Box>
          </Grid>

          <Grid size={{ xs: 12 }}>
            <TextField
              fullWidth
              label="Причина за промяната"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              required
            />
          </Grid>
        </Grid>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Отказ</Button>
        <Button 
          variant="contained" 
          onClick={() => onSave({ markupPercent, premiumAmount, reason })}
          disabled={!reason}
        >
          Запази
        </Button>
      </DialogActions>
    </Dialog>
  );
}
```

---

### ФАЗА 6: ИНТЕГРАЦИЯ ВЪВ ФРОНТЕНДА 🟢

#### 3.11 Бързи Продажби (OrdersPage.tsx)

**Промяна:** Показване на име, количество, единична цена, общо

```tsx
// При избор на рецепта
const handleRecipeSelect = (recipeId: string) => {
  const recipe = recipes.find(r => r.id === recipeId);
  if (recipe) {
    addToSale({
      recipeId,
      name: recipe.name,
      quantity: 1,
      unitPrice: recipe.sellingPrice || 0,
      total: recipe.sellingPrice || 0,
    });
  }
};
```

**UI:**
```
┌─────────────────────────────────────────────────────────────────┐
│  [+ Добави артикул]                                            │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ 1. Торта Наполеон ................... × 2 = 23.20 лв │  │
│  │ 2. Чийзкейк ........................ × 1 =  8.50 лв │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│  Общо: 31.70 лв                                              │
│                                                                 │
│                                      [Приеми Плащане]           │
└─────────────────────────────────────────────────────────────────┘
```

#### 3.12 Приемане на Поръчка

**UI:**
```
┌─────────────────────────────────────────────────────────────────┐
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ 1. Торта Наполеон .................. 11.60 лв × 2    │  │
│  │ 2. Чийзкейк ....................... 8.50 лв × 1    │  │
│  │    ─────────────────────────────────────────────────── │  │
│  │    Общо: 32.70 лв                                     │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                       [Приеми Поръчка]         │
└─────────────────────────────────────────────────────────────────┘
```

#### 3.13 Поръчки за Производство

**UI:**
```
┌─────────────────────────────────────────────────────────────────┐
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ 🍰 Торта Наполеон - 5 бр                                 │  │
│  │    Доставка: 23.03.2026                                 │  │
│  │    ─────────────────────────────────────────────────────  │  │
│  │    Цена: 58.00 лв                                       │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

### ФАЗА 7: МИГРАЦИЯ НА БАЗАТА ДАННИ 🟡

#### 3.14 SQL Миграция

**Файл:** `backend/init_db.py`

```python
# Добави полета към recipes
await conn.execute(text("ALTER TABLE recipes ADD COLUMN IF NOT EXISTS selling_price NUMERIC(10, 2)"))
await conn.execute(text("ALTER TABLE recipes ADD COLUMN IF NOT EXISTS cost_price NUMERIC(10, 2)"))
await conn.execute(text("ALTER TABLE recipes ADD COLUMN IF NOT EXISTS markup_percentage NUMERIC(5, 2) DEFAULT 0"))
await conn.execute(text("ALTER TABLE recipes ADD COLUMN IF NOT EXISTS premium_amount NUMERIC(10, 2) DEFAULT 0"))
await conn.execute(text("ALTER TABLE recipes ADD COLUMN IF NOT EXISTS portions INTEGER DEFAULT 1"))
await conn.execute(text("ALTER TABLE recipes ADD COLUMN IF NOT EXISTS last_price_update TIMESTAMP"))
await conn.execute(text("ALTER TABLE recipes ADD COLUMN IF NOT EXISTS price_calculated_at TIMESTAMP"))

# Нова таблица price_history
await conn.execute(text("""
    CREATE TABLE IF NOT EXISTS price_history (
        id SERIAL PRIMARY KEY,
        recipe_id INTEGER NOT NULL REFERENCES recipes(id),
        old_price NUMERIC(10, 2),
        new_price NUMERIC(10, 2),
        old_cost NUMERIC(10, 2),
        new_cost NUMERIC(10, 2),
        old_markup NUMERIC(5, 2),
        new_markup NUMERIC(5, 2),
        old_premium NUMERIC(10, 2),
        new_premium NUMERIC(10, 2),
        changed_by INTEGER NOT NULL REFERENCES users(id),
        changed_at TIMESTAMP DEFAULT NOW(),
        reason VARCHAR(255)
    )
"""))

# Индекси
await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_price_history_recipe ON price_history(recipe_id)"))
await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_price_history_date ON price_history(changed_at)"))
```

---

### ФАЗА 8: НАВИГАЦИЯ 🟢

#### 3.15 MainLayout

**Файл:** `frontend/src/components/MainLayout.tsx`

```tsx
// В секция "Склад"
{
  text: 'Цени Рецепти',
  path: '/admin/warehouse/pricing',
  visible: hasModule('confectionery'),
  icon: <ReceiptIcon />,
},
```

---

## 4. ТЕХНИЧЕСКИ ЗАВИСИМОСТИ

```
┌─────────────────────────────────────────────────────────────────┐
│                    ЗАВИСИМОСТИ                                 │
└─────────────────────────────────────────────────────────────────┘

     ┌─────────────────┐
     │  1. ОСНОВНИ    │
     │     ПОЛЕТА     │
     └────────┬────────┘
              │
              ├──────────────────────────────┐
              │                              │
              ▼                              ▼
     ┌─────────────────┐         ┌─────────────────┐
     │  2. КАЛКУЛАТОР  │         │  3. MUTATIONS   │
     │  (себестойност)  │         │  (обновяне)    │
     └────────┬────────┘         └────────┬────────┘
              │                              │
              └──────────────┬───────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  4. FRONTEND    │
                    │  (показване)    │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
     ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
     │ Бързи       │ │ Приемане    │ │ Производ-   │
     │ Продажби    │ │ на Поръчка │ │ ство        │
     └─────────────┘ └─────────────┘ └─────────────┘
```

---

## 5. ПОДРЕДБА ЗА ИМПЛЕМЕНТАЦИЯ

| # | Фаза | Описание | Време | Зависимости |
|---|------|---------|--------|-------------|
| 1 | Основни полета | selling_price, cost_price, markup, premium | 1 ден | Няма |
| 2 | PriceHistory | История на промените | 1 ден | 1 |
| 3 | Калкулатор | RecipeCostCalculator | 2 дни | 1 |
| 4 | Mutations | update_recipe_price, calculate_recipe_cost | 1 ден | 2, 3 |
| 5 | Queries | recipes_with_prices, price_history | 1 ден | 1, 3 |
| 6 | Frontend - Цени | MenuPricingPage | 2 дни | 1, 3, 4 |
| 7 | Frontend - Интеграции | Бързи Продажби, Поръчки | 2 дни | 1, 3 |
| 8 | Миграция | SQL за нови колони | 1 ден | Няма |
| **ОБЩО** | | | **~11 дни** | |

---

## 6. ФАЙЛОВЕ ЗА ПРОМЯНА

### 6.1 Нов файлове

| Файл | Описание |
|------|----------|
| `backend/services/recipe_cost_calculator.py` | Калкулатор за себестойност |
| `frontend/src/pages/MenuPricingPage.tsx` | Страница "Цени Рецепти" |
| `frontend/src/components/RecipePriceDialog.tsx` | Диалог за редакция на цена |

### 6.2 Модифицирани файлове

| Файл | Промени |
|------|---------|
| `backend/database/models.py` | +selling_price, cost_price, markup_percentage, premium_amount, portions |
| `backend/graphql/inputs.py` | +RecipePriceInput, RecipePriceUpdateInput |
| `backend/graphql/types.py` | +RecipeCostResult, markup_amount, final_price, portion_price |
| `backend/graphql/mutations.py` | +update_recipe_price, calculate_recipe_cost, recalculate_all_recipe_costs |
| `backend/graphql/queries.py` | +recipes_with_prices, price_history |
| `backend/init_db.py` | +SQL миграция |
| `frontend/src/types.ts` | +RecipePriceResult тип |
| `frontend/src/pages/OrdersPage.tsx` | +показване на цени |
| `frontend/src/components/MainLayout.tsx` | +навигация "Цени Рецепти" |

---

## 7. SQL МИГРАЦИЯ

```sql
-- Добави полета към recipes
ALTER TABLE recipes ADD COLUMN IF NOT EXISTS selling_price NUMERIC(10, 2);
ALTER TABLE recipes ADD COLUMN IF NOT EXISTS cost_price NUMERIC(10, 2);
ALTER TABLE recipes ADD COLUMN IF NOT EXISTS markup_percentage NUMERIC(5, 2) DEFAULT 0;
ALTER TABLE recipes ADD COLUMN IF NOT EXISTS premium_amount NUMERIC(10, 2) DEFAULT 0;
ALTER TABLE recipes ADD COLUMN IF NOT EXISTS portions INTEGER DEFAULT 1;
ALTER TABLE recipes ADD COLUMN IF NOT EXISTS last_price_update TIMESTAMP;
ALTER TABLE recipes ADD COLUMN IF NOT EXISTS price_calculated_at TIMESTAMP;

-- Нова таблица price_history
CREATE TABLE IF NOT EXISTS price_history (
    id SERIAL PRIMARY KEY,
    recipe_id INTEGER NOT NULL REFERENCES recipes(id),
    old_price NUMERIC(10, 2),
    new_price NUMERIC(10, 2),
    old_cost NUMERIC(10, 2),
    new_cost NUMERIC(10, 2),
    old_markup NUMERIC(5, 2),
    new_markup NUMERIC(5, 2),
    old_premium NUMERIC(10, 2),
    new_premium NUMERIC(10, 2),
    changed_by INTEGER NOT NULL REFERENCES users(id),
    changed_at TIMESTAMP DEFAULT NOW(),
    reason VARCHAR(255)
);

CREATE INDEX IF NOT EXISTS idx_price_history_recipe ON price_history(recipe_id);
CREATE INDEX IF NOT EXISTS idx_price_history_date ON price_history(changed_at);
```

---

## 8. UI ДИЗАЙН - РЕЗЮМЕ

### 8.1 Цени Рецепти (основна страница)

```
┌─────────────────────────────────────────────────────────────────┐
│  Цени Рецепти                            [Преизчисли всички]   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Рецепта              │ Себестойност │ Марж │ Надцен │ Продажна │
│  ─────────────────────────────────────────────────────────────  │
│  Торта Наполеон       │ 8.59 лв     │ 26%  │ 1.00 лв│ 11.82 лв │
│  Чийзкейк            │ 5.20 лв     │ 30%  │ -       │ 6.76 лв  │
│  Торта Захара         │ 6.80 лв     │ 25%  │ 0.50 лв│ 9.00 лв  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 Диалог за редакция

```
┌─────────────────────────────────────────────────────────────────┐
│  Цена: Торта Наполеон                           [✕]           │
├─────────────────────────────────────────────────────────────────┤
│  Себестойност: 8.59 лв                                        │
│                                                                 │
│  Марж %: [ 26 ] %                                             │
│           = 2.23 лв                                           │
│                                                                 │
│  Надценка (лв): [ 1.00 ]                                     │
│                                                                 │
│  ════════════════════════════════════════════════════════════   │
│  Продажна цена: 11.82 лв                                     │
│  Марж: 2.23 лв (26%) + Надценка: 1.00 лв                    │
│  ─────────────────────────────────────────────────────────────  │
│  Причина: [___]                                                │
│                                        [Отказ] [Запази]        │
└─────────────────────────────────────────────────────────────────┘
```

### 8.3 Бързи Продажби

```
┌─────────────────────────────────────────────────────────────────┐
│  Бързи Продажби                                               │
├─────────────────────────────────────────────────────────────────┤
│  [+ Добави артикул]                                            │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ 1. Торта Наполеон ................... × 2 = 23.20 лв │  │
│  │ 2. Чийзкейк ........................ × 1 =  8.50 лв │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│  Общо: 31.70 лв                                               │
│                                       [Приеми Плащане]         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 9. ФОРМУЛИ - ОБОБЩЕНИЕ

### 9.1 Себестойност
```
себестойност = Σ (количество_neto × единична цена)

количество_neto = количество_gross × (1 - фира% / 100)
единична цена = Ingredient.current_price
```

### 9.2 Крайна цена
```
продажна_цена = себестойност + марж + надценка

където:
  марж = себестойност × (марж% / 100)
```

### 9.3 Пример
```
Себестойност: 8.59 лв
Марж (26%):   8.59 × 0.26 = 2.23 лв
Надценка:     1.00 лв
───────────────────────────
Продажна:    11.82 лв
```

---

## 10. РЕШЕНИЯ ПРИЕТИ

| # | Решение | Стойност |
|---|--------|----------|
| 1 | Подразбиране за марж | Марж % (не лв) |
| 2 | Ако марж% е 0/празно | Продажна = Себестойност + Надценка |
| 3 | Показване на марж в Бързи Продажби | НЕ |
| 4 | Печалба (труд, наем, ток) | Оставя се за по-късно |
| 5 | Надценка | ДА, отделно поле |

---

## 11. СТАТУС

| # | Фаза | Статус |
|---|------|--------|
| 1 | Основни полета | 📋 Планирана |
| 2 | PriceHistory | 📋 Планирана |
| 3 | Калкулатор | 📋 Планирана |
| 4 | Mutations | 📋 Планирана |
| 5 | Queries | 📋 Планирана |
| 6 | Frontend - Цени | 📋 Планирана |
| 7 | Frontend - Интеграции | 📋 Планирана |
| 8 | Миграция | 📋 Планирана |

---

*Създаден на: 21.03.2026*
*Базиран на: Анализ на pricing потоци*
*Версия: 1.0*
