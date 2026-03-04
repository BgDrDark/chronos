from typing import List, Dict
from strawberry.dataloader import DataLoader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models import Role, Position, Department, EmploymentContract, User
from backend.database.models import Supplier, Ingredient, Batch, StorageZone, Recipe, RecipeSection

async def load_users(db: AsyncSession, keys: List[int]) -> List[User]:
    stmt = select(User).where(User.id.in_(keys))
    res = await db.execute(stmt)
    users = {u.id: u for u in res.scalars().all()}
    return [users.get(key) for key in keys]

async def load_roles(db: AsyncSession, keys: List[int]) -> List[Role]:
    stmt = select(Role).where(Role.id.in_(keys))
    res = await db.execute(stmt)
    roles = {r.id: r for r in res.scalars().all()}
    return [roles.get(key) for key in keys]

async def load_positions(db: AsyncSession, keys: List[int]) -> List[Position]:
    stmt = select(Position).where(Position.id.in_(keys))
    res = await db.execute(stmt)
    positions = {p.id: p for p in res.scalars().all()}
    return [positions.get(key) for key in keys]

async def load_contracts(db: AsyncSession, keys: List[int]) -> List[EmploymentContract]:
    # Returns the active contract for each user_id
    stmt = select(EmploymentContract).where(
        EmploymentContract.user_id.in_(keys),
        EmploymentContract.is_active == True
    )
    res = await db.execute(stmt)
    contracts = {c.user_id: c for c in res.scalars().all()}
    return [contracts.get(key) for key in keys]

async def load_suppliers(db: AsyncSession, keys: List[int]) -> List[Supplier]:
    stmt = select(Supplier).where(Supplier.id.in_(keys))
    res = await db.execute(stmt)
    suppliers = {s.id: s for s in res.scalars().all()}
    return [suppliers.get(key) for key in keys]

async def load_ingredients(db: AsyncSession, keys: List[int]) -> List[Ingredient]:
    stmt = select(Ingredient).where(Ingredient.id.in_(keys))
    res = await db.execute(stmt)
    ingredients = {i.id: i for i in res.scalars().all()}
    return [ingredients.get(key) for key in keys]

async def load_batches(db: AsyncSession, keys: List[int]) -> List[Batch]:
    stmt = select(Batch).where(Batch.id.in_(keys))
    res = await db.execute(stmt)
    batches = {b.id: b for b in res.scalars().all()}
    return [batches.get(key) for key in keys]

async def load_storage_zones(db: AsyncSession, keys: List[int]) -> List[StorageZone]:
    stmt = select(StorageZone).where(StorageZone.id.in_(keys))
    res = await db.execute(stmt)
    zones = {z.id: z for z in res.scalars().all()}
    return [zones.get(key) for key in keys]

async def load_recipes(db: AsyncSession, keys: List[int]) -> List[Recipe]:
    stmt = select(Recipe).where(Recipe.id.in_(keys))
    res = await db.execute(stmt)
    recipes = {r.id: r for r in res.scalars().all()}
    return [recipes.get(key) for key in keys]

async def load_recipe_sections(db: AsyncSession, keys: List[int]) -> List[RecipeSection]:
    stmt = select(RecipeSection).where(RecipeSection.id.in_(keys))
    res = await db.execute(stmt)
    sections = {s.id: s for s in res.scalars().all()}
    return [sections.get(key) for key in keys]

async def load_invoice_items(db: AsyncSession, keys: List[int]) -> List:
    from backend.database.models import InvoiceItem
    stmt = select(InvoiceItem).where(InvoiceItem.invoice_id.in_(keys))
    res = await db.execute(stmt)
    items_by_invoice = {}
    for item in res.scalars().all():
        items_by_invoice.setdefault(item.invoice_id, []).append(item)
    return [items_by_invoice.get(key, []) for key in keys]

def create_dataloaders(db: AsyncSession):
    return {
        "user_by_id": DataLoader(load_fn=lambda keys: load_users(db, keys)),
        "role_by_id": DataLoader(load_fn=lambda keys: load_roles(db, keys)),
        "position_by_id": DataLoader(load_fn=lambda keys: load_positions(db, keys)),
        "contract_by_user_id": DataLoader(load_fn=lambda keys: load_contracts(db, keys)),
        "supplier_by_id": DataLoader(load_fn=lambda keys: load_suppliers(db, keys)),
        "ingredient_by_id": DataLoader(load_fn=lambda keys: load_ingredients(db, keys)),
        "batch_by_id": DataLoader(load_fn=lambda keys: load_batches(db, keys)),
        "storage_zone_by_id": DataLoader(load_fn=lambda keys: load_storage_zones(db, keys)),
        "recipe_by_id": DataLoader(load_fn=lambda keys: load_recipes(db, keys)),
        "recipe_sections_by_recipe_id": DataLoader(load_fn=lambda keys: load_recipe_sections(db, keys)),
        "invoice_items_by_invoice_id": DataLoader(load_fn=lambda keys: load_invoice_items(db, keys)),
    }