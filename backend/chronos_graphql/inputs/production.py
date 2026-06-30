import datetime
from decimal import Decimal

import strawberry


@strawberry.input
class RecipeIngredientInput:
    ingredient_id: int
    quantity_gross: Decimal
    quantity_net: Decimal | None = Decimal(0)
    waste_percentage: Decimal | None = Decimal(0)
    workstation_id: int | None = None


@strawberry.input
class RecipeStepInput:
    workstation_id: int
    name: str
    step_order: int = 0
    estimated_duration_minutes: int | None = None


@strawberry.input
class RecipeSectionInput:
    section_type: str
    name: str
    shelf_life_days: int | None = None
    waste_percentage: Decimal = Decimal(0)
    section_order: int = 0
    ingredients: list[RecipeIngredientInput]
    steps: list[RecipeStepInput]
    brutto_g: float | None = None
    net_g: float | None = None


@strawberry.input
class RecipeInput:
    name: str
    description: str | None = None
    yield_quantity: Decimal = Decimal("1.0")
    yield_unit: str = "br"
    shelf_life_days: int = 7
    shelf_life_frozen_days: int = 30
    default_pieces: int = 12
    production_time_days: int = 1
    standard_quantity: Decimal = Decimal("1.0")
    instructions: str | None = None
    company_id: int
    sections: list[RecipeSectionInput]
    ingredients: list[RecipeIngredientInput] = strawberry.field(default_factory=list)
    steps: list[RecipeStepInput] = strawberry.field(default_factory=list)


@strawberry.input
class RecipePriceUpdateInput:
    markup_percentage: Decimal | None = None
    premium_amount: Decimal | None = None
    portions: int | None = None
    reason: str | None = None


@strawberry.input
class RecipePriceInput:
    recipe_id: int
    markup_percentage: Decimal | None = None
    premium_amount: Decimal | None = None


@strawberry.input
class ProductionOrderInput:
    recipe_id: int
    quantity: Decimal
    due_date: datetime.datetime
    notes: str | None = None
    company_id: int


@strawberry.input
class ScrapTaskInput:
    task_id: int
    quantity: float
    reason: str | None = None


@strawberry.input
class QuickSaleInput:
    recipe_id: int
    quantity: Decimal
    client_name: str | None = None
    client_phone: str | None = None
    payment_method: str = "В брой"
    price: Decimal | None = None
    notes: str | None = None
    company_id: int


__all__ = [
    "ProductionOrderInput",
    "QuickSaleInput",
    "RecipeIngredientInput",
    "RecipeInput",
    "RecipePriceInput",
    "RecipePriceUpdateInput",
    "RecipeSectionInput",
    "RecipeStepInput",
    "ScrapTaskInput",
]
