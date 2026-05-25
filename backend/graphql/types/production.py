import datetime
from decimal import Decimal
from typing import Optional

import strawberry
from strawberry.experimental import pydantic as sp
from sqlalchemy import select

from backend import schemas
from backend.database import models
from backend.graphql.types import User
from backend.graphql.types.logistics import Ingredient


@sp.type(schemas.Workstation)
class Workstation:
    id: strawberry.auto
    name: strawberry.auto
    description: strawberry.auto
    company_id: strawberry.auto


@sp.type(schemas.RecipeIngredient)
class RecipeIngredient:
    id: strawberry.auto
    recipe_id: strawberry.auto
    section_id: strawberry.auto
    ingredient_id: strawberry.auto
    workstation_id: strawberry.auto
    quantity_gross: strawberry.auto
    quantity_net: strawberry.auto
    waste_percentage: strawberry.auto

    @strawberry.field
    async def ingredient(self, info: strawberry.Info) -> Ingredient:
        result = await info.context["dataloaders"]["ingredient_by_id"].load(self.ingredient_id)
        return Ingredient.from_pydantic(result)

    @strawberry.field
    async def workstation(self, info: strawberry.Info) -> Optional[Workstation]:
        if not self.workstation_id:
            return None
        result = await info.context["dataloaders"]["workstation_by_id"].load(self.workstation_id)
        return Workstation.from_pydantic(result) if result else None


@sp.type(schemas.RecipeStep)
class RecipeStep:
    id: strawberry.auto
    section_id: strawberry.auto
    recipe_id: strawberry.auto
    workstation_id: strawberry.auto
    name: strawberry.auto
    step_order: strawberry.auto
    estimated_duration_minutes: strawberry.auto

    @strawberry.field
    async def workstation(self, info: strawberry.Info) -> Workstation:
        result = await info.context["dataloaders"]["workstation_by_id"].load(self.workstation_id)
        return Workstation.from_pydantic(result)


@sp.type(schemas.RecipeSection)
class RecipeSection:
    id: strawberry.auto
    recipe_id: strawberry.auto
    section_type: strawberry.auto
    name: strawberry.auto
    shelf_life_days: strawberry.auto
    waste_percentage: strawberry.auto
    section_order: strawberry.auto

    @strawberry.field
    async def ingredients(self, info: strawberry.Info) -> list[RecipeIngredient]:
        try:
            results = await info.context["dataloaders"]["recipe_ingredients_by_section_id"].load(self.id)
            return [RecipeIngredient.from_pydantic(i) for i in results]
        except Exception as e:
            print(f"Error loading ingredients for section {self.id}: {e}")
            return []

    @strawberry.field
    async def steps(self, info: strawberry.Info) -> list[RecipeStep]:
        results = await info.context["dataloaders"]["recipe_steps_by_section_id"].load(self.id)
        return [RecipeStep.from_pydantic(s) for s in results]


@sp.type(schemas.Recipe)
class Recipe:
    id: strawberry.auto
    name: strawberry.auto
    category: strawberry.auto
    description: strawberry.auto
    yield_quantity: strawberry.auto
    yield_unit: strawberry.auto
    shelf_life_days: strawberry.auto
    shelf_life_frozen_days: strawberry.auto
    default_pieces: strawberry.auto
    production_time_days: strawberry.auto
    production_deadline_days: strawberry.auto
    standard_quantity: strawberry.auto
    instructions: strawberry.auto
    company_id: strawberry.auto
    selling_price: strawberry.auto
    cost_price: strawberry.auto
    markup_percentage: strawberry.auto
    premium_amount: strawberry.auto
    portions: strawberry.auto
    last_price_update: strawberry.auto
    price_calculated_at: strawberry.auto

    @strawberry.field
    def markup_amount(self) -> Decimal:
        if not self.cost_price or not self.markup_percentage or self.markup_percentage == 0:
            return Decimal(0)
        return self.cost_price * self.markup_percentage / 100

    @strawberry.field
    def final_price(self) -> Decimal:
        base = self.cost_price or Decimal(0)
        markup = Decimal(0)
        if self.cost_price and self.markup_percentage and self.markup_percentage != 0:
            markup = self.cost_price * self.markup_percentage / 100
        premium = self.premium_amount or Decimal(0)
        return base + markup + premium

    @strawberry.field
    def portion_price(self) -> Decimal | None:
        if not self.default_pieces or self.default_pieces <= 0:
            return None
        base = self.cost_price or Decimal(0)
        markup = Decimal(0)
        if self.cost_price and self.markup_percentage and self.markup_percentage != 0:
            markup = self.cost_price * self.markup_percentage / 100
        premium = self.premium_amount or Decimal(0)
        return (base + markup + premium) / self.default_pieces if self.default_pieces and self.default_pieces > 0 else None

    @strawberry.field
    async def sections(self, info: strawberry.Info) -> list[RecipeSection]:
        results = await info.context["dataloaders"]["recipe_sections_by_recipe_id"].load(self.id)
        return [RecipeSection.from_pydantic(s) for s in results]

    @strawberry.field
    async def ingredients(self, info: strawberry.Info) -> list[RecipeIngredient]:
        results = await info.context["dataloaders"]["recipe_ingredients_by_recipe_id"].load(self.id)
        return [RecipeIngredient.from_pydantic(i) for i in results]

    @strawberry.field
    async def steps(self, info: strawberry.Info) -> list[RecipeStep]:
        results = await info.context["dataloaders"]["recipe_steps_by_recipe_id"].load(self.id)
        return [RecipeStep.from_pydantic(s) for s in results]


@sp.type(schemas.PriceHistory)
class PriceHistory:
    id: strawberry.auto
    recipe_id: strawberry.auto
    old_price: strawberry.auto
    new_price: strawberry.auto
    old_cost: strawberry.auto
    new_cost: strawberry.auto
    old_markup: strawberry.auto
    new_markup: strawberry.auto
    old_premium: strawberry.auto
    new_premium: strawberry.auto
    changed_by: strawberry.auto
    changed_at: strawberry.auto
    reason: strawberry.auto

    @strawberry.field
    async def recipe(self, info: strawberry.Info) -> Recipe | None:
        result = await info.context["dataloaders"]["recipe_by_id"].load(self.recipe_id)
        return Recipe.from_pydantic(result) if result else None

    @strawberry.field
    async def user(self, info: strawberry.Info) -> User | None:
        result = await info.context["dataloaders"]["user_by_id"].load(self.changed_by)
        return User.from_pydantic(result) if result else None


@strawberry.type
class RecipeCostResult:
    recipe_id: int
    recipe_name: str
    cost_price: Decimal
    markup_amount: Decimal
    premium_amount: Decimal
    final_price: Decimal
    portion_price: Decimal


@strawberry.type
class RecalculateResult:
    recipe_id: int
    recipe_name: str
    cost_price: Decimal
    markup_amount: Decimal
    final_price: Decimal
    portion_price: Decimal


@sp.type(schemas.ProductionTask)
class ProductionTask:
    id: strawberry.auto
    order_id: strawberry.auto
    workstation_id: strawberry.auto
    step_id: strawberry.auto
    name: strawberry.auto
    status: strawberry.auto
    started_at: strawberry.auto
    completed_at: strawberry.auto
    assigned_user_id: strawberry.auto

    @strawberry.field
    async def workstation(self, info: strawberry.Info) -> Workstation:
        result = await info.context["dataloaders"]["workstation_by_id"].load(self.workstation_id)
        return Workstation.from_pydantic(result)

    @strawberry.field
    async def assigned_user(self, info: strawberry.Info) -> User | None:
        if not self.assigned_user_id: return None
        return await info.context["dataloaders"]["user_by_id"].load(self.assigned_user_id)


@sp.type(schemas.ProductionScrapLog)
class ProductionScrapLog:
    id: strawberry.auto
    task_id: strawberry.auto
    user_id: strawberry.auto
    quantity: strawberry.auto
    reason: strawberry.auto
    created_at: strawberry.auto


@strawberry.type
class TerminalTask:
    id: int
    name: str
    quantity: int
    status: str

    @classmethod
    def from_instance(cls, instance: models.ProductionTask, order_quantity: int) -> "TerminalTask":
        return cls(
            id=instance.id,
            name=instance.name,
            quantity=order_quantity,
            status=instance.status,
        )


@strawberry.type
class TerminalOrder:
    id: int
    order_number: str
    product_name: str
    quantity: int
    status: str
    recipe_name: str
    instructions: str | None
    tasks: list[TerminalTask]

    @classmethod
    def from_instance(cls, instance: models.ProductionOrder, recipe_name: str, instructions: str | None, tasks: list[TerminalTask]) -> "TerminalOrder":
        return cls(
            id=instance.id,
            order_number=str(instance.id),
            product_name=recipe_name,
            quantity=int(instance.quantity) if instance.quantity else 0,
            status=instance.status,
            recipe_name=recipe_name,
            instructions=instructions,
            tasks=tasks,
        )


@sp.type(schemas.ProductionOrder)
class ProductionOrder:
    id: strawberry.auto
    recipe_id: strawberry.auto
    quantity: strawberry.auto
    due_date: strawberry.auto
    production_deadline: strawberry.auto
    status: strawberry.auto
    notes: strawberry.auto
    created_at: strawberry.auto
    created_by: strawberry.auto
    company_id: strawberry.auto
    confirmed_at: strawberry.auto
    confirmed_by: strawberry.auto

    @strawberry.field
    async def recipe(self, info: strawberry.Info) -> Recipe:
        result = await info.context["dataloaders"]["recipe_by_id"].load(self.recipe_id)
        return Recipe.from_pydantic(result)

    @strawberry.field
    async def tasks(self, info: strawberry.Info) -> list[ProductionTask]:
        results = await info.context["dataloaders"]["production_tasks_by_order_id"].load(self.id)
        return [ProductionTask.from_pydantic(t) for t in results]


@strawberry.type
class LabelData:
    product_name: str
    batch_number: str
    production_date: datetime.datetime
    expiry_date: datetime.date
    allergens: list[str]
    storage_conditions: str | None
    qr_code_content: str
    quantity: str


@sp.type(schemas.ProductionRecordIngredient)
class ProductionRecordIngredient:
    id: strawberry.auto
    ingredient_id: strawberry.auto
    batch_number: strawberry.auto
    expiry_date: strawberry.auto
    quantity_used: strawberry.auto
    unit: strawberry.auto


@sp.type(schemas.ProductionRecordWorker)
class ProductionRecordWorker:
    id: strawberry.auto
    user_id: strawberry.auto
    workstation_id: strawberry.auto
    started_at: strawberry.auto
    completed_at: strawberry.auto


@sp.type(schemas.ProductionRecord)
class ProductionRecord:
    id: strawberry.auto
    order_id: strawberry.auto
    confirmed_by: strawberry.auto
    confirmed_at: strawberry.auto
    expiry_date: strawberry.auto
    notes: strawberry.auto
    created_at: strawberry.auto

    @strawberry.field
    async def ingredients(self, info: strawberry.Info) -> list[ProductionRecordIngredient]:
        results = await info.context["dataloaders"]["production_record_ingredients_by_record_id"].load(self.id)
        return [ProductionRecordIngredient.from_pydantic(i) for i in results]

    @strawberry.field
    async def workers(self, info: strawberry.Info) -> list[ProductionRecordWorker]:
        results = await info.context["dataloaders"]["production_record_workers_by_record_id"].load(self.id)
        return [ProductionRecordWorker.from_pydantic(t) for t in results]


__all__ = [
    "LabelData",
    "PriceHistory",
    "ProductionOrder",
    "ProductionRecord",
    "ProductionRecordIngredient",
    "ProductionRecordWorker",
    "ProductionScrapLog",
    "ProductionTask",
    "RecalculateResult",
    "Recipe",
    "RecipeCostResult",
    "RecipeIngredient",
    "RecipeSection",
    "RecipeStep",
    "TerminalOrder",
    "TerminalTask",
    "Workstation",
]
