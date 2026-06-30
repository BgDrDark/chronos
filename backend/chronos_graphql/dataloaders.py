from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from strawberry.dataloader import DataLoader

from backend import schemas
from backend.database.models import (
    AccessZone,
    Account,
    Batch,
    Company,
    Department,
    EmploymentContract,
    Gateway,
    Ingredient,
    Invoice,
    InvoiceItem,
    Position,
    ProductionRecordIngredient,
    ProductionRecordWorker,
    ProductionTask,
    Recipe,
    RecipeIngredient,
    RecipeSection,
    RecipeStep,
    Role,
    Shift,
    StorageZone,
    Supplier,
    User as DbUser,
    VehicleDocument,
    VehicleDriver,
    VehicleExpense,
    VehicleFuel,
    VehicleFuelCard,
    VehicleInspection,
    VehicleMileage,
    VehiclePreTripInspection,
    VehicleRepair,
    VehicleSchedule,
    VehicleToll,
    VehicleTrip,
    VehicleType,
    VehicleVignette,
    WorkSchedule,
    Workstation,
)


async def load_users(db: AsyncSession, keys: Sequence[int]) -> list:
    from sqlalchemy.orm import joinedload
    from backend.chronos_graphql.types.user import User as GqlUser
    stmt = select(DbUser).where(DbUser.id.in_(keys)).options(joinedload(DbUser.role))
    res = await db.execute(stmt)
    users = {}
    for u in res.scalars().unique().all():
        users[u.id] = GqlUser.from_pydantic(schemas.User.model_validate(u))
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

async def load_workstations(db: AsyncSession, keys: Sequence[int]) -> list[Workstation]:
    stmt = select(Workstation).where(Workstation.id.in_(keys))
    res = await db.execute(stmt)
    workstations = {w.id: w for w in res.scalars().all()}
    return [workstations.get(key) for key in keys]

async def load_work_schedules(db: AsyncSession, keys: Sequence[int]) -> list[WorkSchedule]:
    stmt = select(WorkSchedule).where(WorkSchedule.id.in_(keys))
    res = await db.execute(stmt)
    schedules = {s.id: s for s in res.scalars().all()}
    return [schedules.get(key) for key in keys]

async def load_invoices(db: AsyncSession, keys: Sequence[int]) -> list[Invoice]:
    stmt = select(Invoice).where(Invoice.id.in_(keys))
    res = await db.execute(stmt)
    invoices = {i.id: i for i in res.scalars().all()}
    return [invoices.get(key) for key in keys]

async def load_vehicle_types(db: AsyncSession, keys: Sequence[int]) -> list[VehicleType]:
    stmt = select(VehicleType).where(VehicleType.id.in_(keys))
    res = await db.execute(stmt)
    types = {t.id: t for t in res.scalars().all()}
    return [types.get(key) for key in keys]

async def load_access_zones(db: AsyncSession, keys: Sequence[int]) -> list[AccessZone]:
    stmt = select(AccessZone).where(AccessZone.id.in_(keys))
    res = await db.execute(stmt)
    zones = {z.id: z for z in res.scalars().all()}
    return [zones.get(key) for key in keys]

async def load_gateways(db: AsyncSession, keys: Sequence[int]) -> list[Gateway]:
    stmt = select(Gateway).where(Gateway.id.in_(keys))
    res = await db.execute(stmt)
    gateways = {g.id: g for g in res.scalars().all()}
    return [gateways.get(key) for key in keys]

async def load_vehicle_documents(db: AsyncSession, keys: Sequence[int]) -> list[list[VehicleDocument]]:
    stmt = select(VehicleDocument).where(VehicleDocument.vehicle_id.in_(keys))
    res = await db.execute(stmt)
    docs_by_vehicle = {}
    for doc in res.scalars().all():
        docs_by_vehicle.setdefault(doc.vehicle_id, []).append(doc)
    return [docs_by_vehicle.get(key, []) for key in keys]

async def load_vehicle_fuel_cards(db: AsyncSession, keys: Sequence[int]) -> list[list[VehicleFuelCard]]:
    stmt = select(VehicleFuelCard).where(VehicleFuelCard.vehicle_id.in_(keys))
    res = await db.execute(stmt)
    cards_by_vehicle = {}
    for card in res.scalars().all():
        cards_by_vehicle.setdefault(card.vehicle_id, []).append(card)
    return [cards_by_vehicle.get(key, []) for key in keys]

async def load_vehicle_vignettes(db: AsyncSession, keys: Sequence[int]) -> list[list[VehicleVignette]]:
    stmt = select(VehicleVignette).where(VehicleVignette.vehicle_id.in_(keys))
    res = await db.execute(stmt)
    vignettes_by_vehicle = {}
    for vignette in res.scalars().all():
        vignettes_by_vehicle.setdefault(vignette.vehicle_id, []).append(vignette)
    return [vignettes_by_vehicle.get(key, []) for key in keys]

async def load_vehicle_tolls(db: AsyncSession, keys: Sequence[int]) -> list[list[VehicleToll]]:
    stmt = select(VehicleToll).where(VehicleToll.vehicle_id.in_(keys))
    res = await db.execute(stmt)
    tolls_by_vehicle = {}
    for toll in res.scalars().all():
        tolls_by_vehicle.setdefault(toll.vehicle_id, []).append(toll)
    return [tolls_by_vehicle.get(key, []) for key in keys]

async def load_vehicle_mileages(db: AsyncSession, keys: Sequence[int]) -> list[list[VehicleMileage]]:
    stmt = select(VehicleMileage).where(VehicleMileage.vehicle_id.in_(keys))
    res = await db.execute(stmt)
    mileages_by_vehicle = {}
    for mileage in res.scalars().all():
        mileages_by_vehicle.setdefault(mileage.vehicle_id, []).append(mileage)
    return [mileages_by_vehicle.get(key, []) for key in keys]

async def load_vehicle_fuel_records(db: AsyncSession, keys: Sequence[int]) -> list[list[VehicleFuel]]:
    stmt = select(VehicleFuel).where(VehicleFuel.vehicle_id.in_(keys))
    res = await db.execute(stmt)
    fuel_by_vehicle = {}
    for fuel in res.scalars().all():
        fuel_by_vehicle.setdefault(fuel.vehicle_id, []).append(fuel)
    return [fuel_by_vehicle.get(key, []) for key in keys]

async def load_vehicle_repairs(db: AsyncSession, keys: Sequence[int]) -> list[list[VehicleRepair]]:
    stmt = select(VehicleRepair).where(VehicleRepair.vehicle_id.in_(keys))
    res = await db.execute(stmt)
    repairs_by_vehicle = {}
    for repair in res.scalars().all():
        repairs_by_vehicle.setdefault(repair.vehicle_id, []).append(repair)
    return [repairs_by_vehicle.get(key, []) for key in keys]

async def load_vehicle_schedules(db: AsyncSession, keys: Sequence[int]) -> list[list[VehicleSchedule]]:
    stmt = select(VehicleSchedule).where(VehicleSchedule.vehicle_id.in_(keys))
    res = await db.execute(stmt)
    schedules_by_vehicle = {}
    for schedule in res.scalars().all():
        schedules_by_vehicle.setdefault(schedule.vehicle_id, []).append(schedule)
    return [schedules_by_vehicle.get(key, []) for key in keys]

async def load_vehicle_inspections(db: AsyncSession, keys: Sequence[int]) -> list[list[VehicleInspection]]:
    stmt = select(VehicleInspection).where(VehicleInspection.vehicle_id.in_(keys))
    res = await db.execute(stmt)
    inspections_by_vehicle = {}
    for inspection in res.scalars().all():
        inspections_by_vehicle.setdefault(inspection.vehicle_id, []).append(inspection)
    return [inspections_by_vehicle.get(key, []) for key in keys]

async def load_vehicle_pre_trip_inspections(db: AsyncSession, keys: Sequence[int]) -> list[list[VehiclePreTripInspection]]:
    stmt = select(VehiclePreTripInspection).where(VehiclePreTripInspection.vehicle_id.in_(keys))
    res = await db.execute(stmt)
    inspections_by_vehicle = {}
    for inspection in res.scalars().all():
        inspections_by_vehicle.setdefault(inspection.vehicle_id, []).append(inspection)
    return [inspections_by_vehicle.get(key, []) for key in keys]

async def load_vehicle_drivers(db: AsyncSession, keys: Sequence[int]) -> list[list[VehicleDriver]]:
    stmt = select(VehicleDriver).where(VehicleDriver.vehicle_id.in_(keys))
    res = await db.execute(stmt)
    drivers_by_vehicle = {}
    for driver in res.scalars().all():
        drivers_by_vehicle.setdefault(driver.vehicle_id, []).append(driver)
    return [drivers_by_vehicle.get(key, []) for key in keys]

async def load_vehicle_trips(db: AsyncSession, keys: Sequence[int]) -> list[list[VehicleTrip]]:
    stmt = select(VehicleTrip).where(VehicleTrip.vehicle_id.in_(keys))
    res = await db.execute(stmt)
    trips_by_vehicle = {}
    for trip in res.scalars().all():
        trips_by_vehicle.setdefault(trip.vehicle_id, []).append(trip)
    return [trips_by_vehicle.get(key, []) for key in keys]

async def load_vehicle_expenses(db: AsyncSession, keys: Sequence[int]) -> list[list[VehicleExpense]]:
    stmt = select(VehicleExpense).where(VehicleExpense.vehicle_id.in_(keys))
    res = await db.execute(stmt)
    expenses_by_vehicle = {}
    for expense in res.scalars().all():
        expenses_by_vehicle.setdefault(expense.vehicle_id, []).append(expense)
    return [expenses_by_vehicle.get(key, []) for key in keys]

async def load_recipe_ingredients_by_section(db: AsyncSession, keys: Sequence[int]) -> list[list[RecipeIngredient]]:
    stmt = select(RecipeIngredient).where(RecipeIngredient.section_id.in_(keys))
    res = await db.execute(stmt)
    ingredients_by_section = {}
    for ingredient in res.scalars().all():
        ingredients_by_section.setdefault(ingredient.section_id, []).append(ingredient)
    return [ingredients_by_section.get(key, []) for key in keys]

async def load_recipe_steps_by_section(db: AsyncSession, keys: Sequence[int]) -> list[list[RecipeStep]]:
    stmt = select(RecipeStep).where(RecipeStep.section_id.in_(keys)).order_by(RecipeStep.step_order)
    res = await db.execute(stmt)
    steps_by_section = {}
    for step in res.scalars().all():
        steps_by_section.setdefault(step.section_id, []).append(step)
    return [steps_by_section.get(key, []) for key in keys]

async def load_recipe_ingredients_by_recipe(db: AsyncSession, keys: Sequence[int]) -> list[list[RecipeIngredient]]:
    stmt = select(RecipeIngredient).where(RecipeIngredient.recipe_id.in_(keys))
    res = await db.execute(stmt)
    ingredients_by_recipe = {}
    for ingredient in res.scalars().all():
        ingredients_by_recipe.setdefault(ingredient.recipe_id, []).append(ingredient)
    return [ingredients_by_recipe.get(key, []) for key in keys]

async def load_recipe_steps_by_recipe(db: AsyncSession, keys: Sequence[int]) -> list[list[RecipeStep]]:
    stmt = select(RecipeStep).where(RecipeStep.recipe_id.in_(keys)).order_by(RecipeStep.step_order)
    res = await db.execute(stmt)
    steps_by_recipe = {}
    for step in res.scalars().all():
        steps_by_recipe.setdefault(step.recipe_id, []).append(step)
    return [steps_by_recipe.get(key, []) for key in keys]

async def load_production_tasks_by_order(db: AsyncSession, keys: Sequence[int]) -> list[list[ProductionTask]]:
    stmt = select(ProductionTask).where(ProductionTask.order_id.in_(keys))
    res = await db.execute(stmt)
    tasks_by_order = {}
    for task in res.scalars().all():
        tasks_by_order.setdefault(task.order_id, []).append(task)
    return [tasks_by_order.get(key, []) for key in keys]

async def load_production_record_ingredients(db: AsyncSession, keys: Sequence[int]) -> list[list[ProductionRecordIngredient]]:
    stmt = select(ProductionRecordIngredient).where(ProductionRecordIngredient.record_id.in_(keys))
    res = await db.execute(stmt)
    ingredients_by_record = {}
    for ingredient in res.scalars().all():
        ingredients_by_record.setdefault(ingredient.record_id, []).append(ingredient)
    return [ingredients_by_record.get(key, []) for key in keys]

async def load_production_record_workers(db: AsyncSession, keys: Sequence[int]) -> list[list[ProductionRecordWorker]]:
    stmt = select(ProductionRecordWorker).where(ProductionRecordWorker.record_id.in_(keys))
    res = await db.execute(stmt)
    workers_by_record = {}
    for worker in res.scalars().all():
        workers_by_record.setdefault(worker.record_id, []).append(worker)
    return [workers_by_record.get(key, []) for key in keys]

def create_dataloaders(db: AsyncSession):
    return {
        "user_by_id": DataLoader(load_fn=lambda keys: load_users(db, keys)),
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
        "workstation_by_id": DataLoader[int, Workstation](load_fn=lambda keys: load_workstations(db, keys)),
        "work_schedule_by_id": DataLoader[int, WorkSchedule](load_fn=lambda keys: load_work_schedules(db, keys)),
        "invoice_by_id": DataLoader[int, Invoice](load_fn=lambda keys: load_invoices(db, keys)),
        "vehicle_type_by_id": DataLoader[int, VehicleType](load_fn=lambda keys: load_vehicle_types(db, keys)),
        "access_zone_by_id": DataLoader[int, AccessZone](load_fn=lambda keys: load_access_zones(db, keys)),
        "gateway_by_id": DataLoader[int, Gateway](load_fn=lambda keys: load_gateways(db, keys)),
        "vehicle_documents_by_vehicle_id": DataLoader[int, list](load_fn=lambda keys: load_vehicle_documents(db, keys)),
        "vehicle_fuel_cards_by_vehicle_id": DataLoader[int, list](load_fn=lambda keys: load_vehicle_fuel_cards(db, keys)),
        "vehicle_vignettes_by_vehicle_id": DataLoader[int, list](load_fn=lambda keys: load_vehicle_vignettes(db, keys)),
        "vehicle_tolls_by_vehicle_id": DataLoader[int, list](load_fn=lambda keys: load_vehicle_tolls(db, keys)),
        "vehicle_mileages_by_vehicle_id": DataLoader[int, list](load_fn=lambda keys: load_vehicle_mileages(db, keys)),
        "vehicle_fuel_records_by_vehicle_id": DataLoader[int, list](load_fn=lambda keys: load_vehicle_fuel_records(db, keys)),
        "vehicle_repairs_by_vehicle_id": DataLoader[int, list](load_fn=lambda keys: load_vehicle_repairs(db, keys)),
        "vehicle_schedules_by_vehicle_id": DataLoader[int, list](load_fn=lambda keys: load_vehicle_schedules(db, keys)),
        "vehicle_inspections_by_vehicle_id": DataLoader[int, list](load_fn=lambda keys: load_vehicle_inspections(db, keys)),
        "vehicle_pre_trip_inspections_by_vehicle_id": DataLoader[int, list](load_fn=lambda keys: load_vehicle_pre_trip_inspections(db, keys)),
        "vehicle_drivers_by_vehicle_id": DataLoader[int, list](load_fn=lambda keys: load_vehicle_drivers(db, keys)),
        "vehicle_trips_by_vehicle_id": DataLoader[int, list](load_fn=lambda keys: load_vehicle_trips(db, keys)),
        "vehicle_expenses_by_vehicle_id": DataLoader[int, list](load_fn=lambda keys: load_vehicle_expenses(db, keys)),
        "recipe_ingredients_by_section_id": DataLoader[int, list](load_fn=lambda keys: load_recipe_ingredients_by_section(db, keys)),
        "recipe_steps_by_section_id": DataLoader[int, list](load_fn=lambda keys: load_recipe_steps_by_section(db, keys)),
        "recipe_ingredients_by_recipe_id": DataLoader[int, list](load_fn=lambda keys: load_recipe_ingredients_by_recipe(db, keys)),
        "recipe_steps_by_recipe_id": DataLoader[int, list](load_fn=lambda keys: load_recipe_steps_by_recipe(db, keys)),
        "production_tasks_by_order_id": DataLoader[int, list](load_fn=lambda keys: load_production_tasks_by_order(db, keys)),
        "production_record_ingredients_by_record_id": DataLoader[int, list](load_fn=lambda keys: load_production_record_ingredients(db, keys)),
        "production_record_workers_by_record_id": DataLoader[int, list](load_fn=lambda keys: load_production_record_workers(db, keys)),
    }
