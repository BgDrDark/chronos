from datetime import date, datetime
from decimal import Decimal

from pydantic import model_validator

from backend.schemas.base import CustomBaseModel


class RecipeIngredient(CustomBaseModel):
    id: int
    section_id: int | None = None
    recipe_id: int | None = None
    ingredient_id: int
    workstation_id: int | None = None
    quantity_gross: Decimal
    quantity_net: Decimal = Decimal(0)
    waste_percentage: Decimal = Decimal(0)


class RecipeSection(CustomBaseModel):
    id: int
    recipe_id: int
    section_type: str
    name: str
    shelf_life_days: int | None = None
    waste_percentage: Decimal = Decimal(0)
    section_order: int = 0


class RecipeStep(CustomBaseModel):
    id: int
    section_id: int | None = None
    recipe_id: int | None = None
    workstation_id: int
    name: str
    step_order: int = 0
    estimated_duration_minutes: int | None = None


class RecipeBase(CustomBaseModel):

    name: str
    category: str | None = None
    description: str | None = None
    yield_quantity: Decimal = Decimal("1.0")
    yield_unit: str = "br"
    shelf_life_days: int = 7
    shelf_life_frozen_days: int = 30
    default_pieces: int = 12
    production_time_days: int = 1
    production_deadline_days: int | None = None
    standard_quantity: Decimal = Decimal("1.0")
    instructions: str | None = None
    company_id: int
    selling_price: Decimal | None = None
    cost_price: Decimal | None = None
    markup_percentage: Decimal = Decimal(0)
    premium_amount: Decimal = Decimal(0)
    portions: int = 1
    last_price_update: datetime | None = None
    price_calculated_at: datetime | None = None


class RecipeCreate(RecipeBase):
    pass


class Recipe(RecipeBase):
    id: int


class ProductionOrderBase(CustomBaseModel):

    recipe_id: int
    quantity: Decimal
    due_date: datetime
    status: str = "pending"
    notes: str | None = None
    company_id: int


class ProductionOrderCreate(ProductionOrderBase):
    pass


class ProductionOrderUpdate(CustomBaseModel):

    status: str | None = None
    notes: str | None = None
    completed_by: int | None = None


class ProductionOrder(ProductionOrderBase):

    id: int
    created_at: datetime
    production_deadline: datetime | None = None
    created_by: int | None = None
    completed_at: datetime | None = None
    completed_by: int | None = None
    confirmed_at: datetime | None = None
    confirmed_by: int | None = None


class PriceHistory(CustomBaseModel):
    id: int
    recipe_id: int
    old_price: Decimal
    new_price: Decimal
    old_cost: Decimal
    new_cost: Decimal
    old_markup: Decimal
    new_markup: Decimal
    old_premium: Decimal
    new_premium: Decimal
    changed_by: int
    changed_at: datetime
    reason: str | None = None


class Workstation(CustomBaseModel):
    id: int
    name: str
    description: str | None = None
    company_id: int


class ProductionTask(CustomBaseModel):
    id: int
    order_id: int
    workstation_id: int
    step_id: int | None = None
    name: str
    status: str = "pending"
    started_at: datetime | None = None
    completed_at: datetime | None = None
    assigned_user_id: int | None = None


class ProductionScrapLog(CustomBaseModel):
    id: int
    task_id: int
    user_id: int
    quantity: Decimal
    reason: str | None = None
    created_at: datetime


class ProductionRecord(CustomBaseModel):
    id: int
    order_id: int
    confirmed_by: int | None = None
    confirmed_at: datetime | None = None
    expiry_date: date | None = None
    notes: str | None = None
    created_at: datetime


class ProductionRecordIngredient(CustomBaseModel):
    id: int
    record_id: int
    ingredient_id: int
    batch_number: str
    expiry_date: date | None = None
    quantity_used: Decimal
    unit: str | None = None


class ProductionRecordWorker(CustomBaseModel):
    id: int
    record_id: int
    user_id: int
    workstation_id: int | None = None
    task_id: int | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
