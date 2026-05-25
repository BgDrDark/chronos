from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from strawberry.dataloader import DataLoader

from backend.database.models import (
    Account,
    Batch,
    Company,
    Department,
    EmploymentContract,
    Ingredient,
    InvoiceItem,
    Position,
    Recipe,
    RecipeSection,
    Role,
    Shift,
    StorageZone,
    Supplier,
    User,
)


async def load_users(db: AsyncSession, keys: Sequence[int]) -> list[User]:
    stmt = select(User).where(User.id.in_(keys))
    res = await db.execute(stmt)
    users = {u.id: u for u in res.scalars().all()}
    return [users.get(key) for key in keys]

async def load_roles(db: AsyncSession, keys: Sequence[int]) -> list[Role]:
    stmt = select(Role).where(Role.id.in_(keys))
    res = await db.execute(stmt)
    roles = {r.id: r for r in res.scalars().all()}
    return [roles.get(key) for key in keys]

async def load_positions(db: AsyncSession, keys: Sequence[int]) -> list[Position]:
    stmt = select(Position).where(Position.id.in_(keys))
    res = await db.execute(stmt)
    positions = {p.id: p for p in res.scalars().all()}
    return [positions.get(key) for key in keys]

async def load_departments(db: AsyncSession, keys: Sequence[int]) -> list[Department]:
    stmt = select(Department).where(Department.id.in_(keys))
    res = await db.execute(stmt)
    departments = {d.id: d for d in res.scalars().all()}
    return [departments.get(key) for key in keys]

async def load_contracts(db: AsyncSession, keys: Sequence[int]) -> list[EmploymentContract]:
    # Returns the active contract for each user_id
    from sqlalchemy.orm import selectinload
    stmt = select(EmploymentContract).options(
        selectinload(EmploymentContract.company),
        selectinload(EmploymentContract.position),
        selectinload(EmploymentContract.department),
    ).where(
        EmploymentContract.user_id.in_(keys),
        EmploymentContract.is_active,
    )
    res = await db.execute(stmt)
    contracts = {c.user_id: c for c in res.scalars().all()}
    return [contracts.get(key) for key in keys]

async def load_suppliers(db: AsyncSession, keys: Sequence[int]) -> list[Supplier]:
    stmt = select(Supplier).where(Supplier.id.in_(keys))
    res = await db.execute(stmt)
    suppliers = {s.id: s for s in res.scalars().all()}
    return [suppliers.get(key) for key in keys]

async def load_companies(db: AsyncSession, keys: Sequence[int]) -> list[Company]:
    stmt = select(Company).where(Company.id.in_(keys))
    res = await db.execute(stmt)
    companies = {c.id: c for c in res.scalars().all()}
    return [companies.get(key) for key in keys]

async def load_ingredients(db: AsyncSession, keys: Sequence[int]) -> list[Ingredient]:
    stmt = select(Ingredient).where(Ingredient.id.in_(keys))
    res = await db.execute(stmt)
    ingredients = {i.id: i for i in res.scalars().all()}
    return [ingredients.get(key) for key in keys]

async def load_batches(db: AsyncSession, keys: Sequence[int]) -> list[Batch]:
    stmt = select(Batch).where(Batch.id.in_(keys))
    res = await db.execute(stmt)
    batches = {b.id: b for b in res.scalars().all()}
    return [batches.get(key) for key in keys]

async def load_storage_zones(db: AsyncSession, keys: Sequence[int]) -> list[StorageZone]:
    stmt = select(StorageZone).where(StorageZone.id.in_(keys))
    res = await db.execute(stmt)
    zones = {z.id: z for z in res.scalars().all()}
    return [zones.get(key) for key in keys]

async def load_recipes(db: AsyncSession, keys: Sequence[int]) -> list[Recipe]:
    stmt = select(Recipe).where(Recipe.id.in_(keys))
    res = await db.execute(stmt)
    recipes = {r.id: r for r in res.scalars().all()}
    return [recipes.get(key) for key in keys]

async def load_recipe_sections(db: AsyncSession, keys: Sequence[int]) -> list[RecipeSection]:
    stmt = select(RecipeSection).where(RecipeSection.id.in_(keys))
    res = await db.execute(stmt)
    sections = {s.id: s for s in res.scalars().all()}
    return [sections.get(key) for key in keys]

async def load_accounts(db: AsyncSession, keys: Sequence[int]) -> list[Account]:
    stmt = select(Account).where(Account.id.in_(keys))
    res = await db.execute(stmt)
    accounts = {a.id: a for a in res.scalars().all()}
    return [accounts.get(key) for key in keys]

async def load_shifts(db: AsyncSession, keys: Sequence[int]) -> list[Shift]:
    stmt = select(Shift).where(Shift.id.in_(keys))
    res = await db.execute(stmt)
    shifts = {s.id: s for s in res.scalars().all()}
    return [shifts.get(key) for key in keys]

async def load_invoice_items(db: AsyncSession, keys: Sequence[int]) -> list[InvoiceItem]:
    stmt = select(InvoiceItem).where(InvoiceItem.invoice_id.in_(keys))
    res = await db.execute(stmt)
    items_by_invoice = {}
    for item in res.scalars().all():
        items_by_invoice.setdefault(item.invoice_id, []).append(item)
    return [items_by_invoice.get(key, []) for key in keys]

def create_dataloaders(db: AsyncSession):
    return {
        "user_by_id": DataLoader[int, User](load_fn=lambda keys: load_users(db, keys)),
        "role_by_id": DataLoader[int, Role](load_fn=lambda keys: load_roles(db, keys)),
        "position_by_id": DataLoader[int, Position](load_fn=lambda keys: load_positions(db, keys)),
        "department_by_id": DataLoader[int, Department](load_fn=lambda keys: load_departments(db, keys)),
        "contract_by_user_id": DataLoader[int, EmploymentContract](load_fn=lambda keys: load_contracts(db, keys)),
        "supplier_by_id": DataLoader[int, Supplier](load_fn=lambda keys: load_suppliers(db, keys)),
        "company_by_id": DataLoader[int, Company](load_fn=lambda keys: load_companies(db, keys)),
        "ingredient_by_id": DataLoader[int, Ingredient](load_fn=lambda keys: load_ingredients(db, keys)),
        "batch_by_id": DataLoader[int, Batch](load_fn=lambda keys: load_batches(db, keys)),
        "storage_zone_by_id": DataLoader[int, StorageZone](load_fn=lambda keys: load_storage_zones(db, keys)),
        "recipe_by_id": DataLoader[int, Recipe](load_fn=lambda keys: load_recipes(db, keys)),
        "recipe_sections_by_recipe_id": DataLoader[int, RecipeSection](load_fn=lambda keys: load_recipe_sections(db, keys)),
        "invoice_items_by_invoice_id": DataLoader[int, list](load_fn=lambda keys: load_invoice_items(db, keys)),
        "account_by_id": DataLoader[int, Account](load_fn=lambda keys: load_accounts(db, keys)),
        "shift_by_id": DataLoader[int, Shift](load_fn=lambda keys: load_shifts(db, keys)),
    }
