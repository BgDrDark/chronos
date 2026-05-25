import dataclasses
import datetime
from decimal import Decimal

import strawberry
from strawberry.experimental import pydantic as sp
from sqlalchemy import select

from backend import schemas
from backend.database import models
from backend.graphql.types import User


@sp.type(schemas.StorageZone)
class StorageZone:
    id: strawberry.auto
    name: strawberry.auto
    temp_min: float | None = None
    temp_max: float | None = None
    description: strawberry.auto
    company_id: strawberry.auto
    is_active: strawberry.auto
    asset_type: strawberry.auto
    zone_type: strawberry.auto


@sp.type(schemas.Supplier)
class Supplier:
    id: strawberry.auto
    name: strawberry.auto
    eik: strawberry.auto
    vat_number: strawberry.auto
    address: strawberry.auto
    contact_person: strawberry.auto
    phone: strawberry.auto
    email: strawberry.auto
    company_id: strawberry.auto


@sp.type(schemas.Ingredient)
class Ingredient:
    id: strawberry.auto
    name: strawberry.auto
    unit: strawberry.auto
    barcode: strawberry.auto
    baseline_min_stock: strawberry.auto
    current_price: strawberry.auto
    storage_zone_id: strawberry.auto
    is_perishable: strawberry.auto
    expiry_warning_days: strawberry.auto
    allergens: list[str] = dataclasses.field(default_factory=list)
    company_id: strawberry.auto
    product_type: str = "raw"

    @strawberry.field
    async def storage_zone(self, info: strawberry.Info) -> StorageZone | None:
        if not self.storage_zone_id: return None
        result = await info.context["dataloaders"]["storage_zone_by_id"].load(self.storage_zone_id)
        return StorageZone.from_pydantic(result) if result else None

    @strawberry.field
    async def current_stock(self, info: strawberry.Info) -> Decimal:
        db = info.context["db"]
        stmt = select(models.Batch).where(
            models.Batch.ingredient_id == self.id,
            models.Batch.status == "active",
        )
        res = await db.execute(stmt)
        batches = res.scalars().all()
        return sum((b.quantity for b in batches), Decimal(0))


@sp.type(schemas.Batch)
class Batch:
    id: strawberry.auto
    ingredient_id: strawberry.auto
    batch_number: strawberry.auto
    quantity: strawberry.auto
    expiry_date: strawberry.auto
    status: strawberry.auto
    received_at: strawberry.auto
    supplier_id: strawberry.auto
    invoice_number: strawberry.auto
    storage_zone_id: strawberry.auto

    @strawberry.field
    def available_stock(self) -> Decimal:
        if self.status == "active" and self.quantity > 0:
            return self.quantity
        return Decimal(0)

    @strawberry.field
    def is_expired(self) -> bool:
        return datetime.date.today() > self.expiry_date

    @strawberry.field
    def days_until_expiry(self) -> int:
        delta = self.expiry_date - datetime.date.today()
        return delta.days

    @strawberry.field
    async def ingredient(self, info: strawberry.Info) -> Ingredient:
        result = await info.context["dataloaders"]["ingredient_by_id"].load(self.ingredient_id)
        return Ingredient.from_pydantic(result)

    @strawberry.field
    async def supplier(self, info: strawberry.Info) -> Supplier | None:
        if not self.supplier_id: return None
        result = await info.context["dataloaders"]["supplier_by_id"].load(self.supplier_id)
        return Supplier.from_pydantic(result) if result else None

    @strawberry.field
    async def storage_zone(self, info: strawberry.Info) -> StorageZone | None:
        if not self.storage_zone_id: return None
        result = await info.context["dataloaders"]["storage_zone_by_id"].load(self.storage_zone_id)
        return StorageZone.from_pydantic(result) if result else None


@strawberry.type
class StockConsumptionLog:
    id: int
    ingredient_id: int
    batch_id: int
    quantity: Decimal
    reason: str
    production_order_id: int | None
    notes: str | None
    created_by: int
    created_at: datetime.datetime

    @strawberry.field
    async def ingredient(self, info: strawberry.Info) -> Ingredient:
        result = await info.context["dataloaders"]["ingredient_by_id"].load(self.ingredient_id)
        return Ingredient.from_pydantic(result)

    @strawberry.field
    async def batch(self, info: strawberry.Info) -> Batch:
        result = await info.context["dataloaders"]["batch_by_id"].load(self.batch_id)
        return Batch.from_pydantic(result)

    @strawberry.field
    async def creator(self, info: strawberry.Info) -> User:
        result = await info.context["dataloaders"]["user_by_id"].load(self.created_by)
        return User.from_pydantic(result)

    @classmethod
    def from_instance(cls, instance: models.StockConsumptionLog) -> "StockConsumptionLog":
        return cls(
            id=instance.id,
            ingredient_id=instance.ingredient_id,
            batch_id=instance.batch_id,
            quantity=instance.quantity,
            reason=instance.reason,
            production_order_id=instance.production_order_id,
            notes=instance.notes,
            created_by=instance.created_by,
            created_at=instance.created_at,
        )


@strawberry.type
class FefoSuggestion:
    batch_id: int
    batch_number: str
    available_quantity: Decimal
    quantity_to_take: Decimal
    expiry_date: datetime.date
    days_until_expiry: int


@strawberry.type
class InventoryItem:
    id: int
    session_id: int
    ingredient_id: int
    ingredient_name: str | None
    ingredient_unit: str | None
    found_quantity: Decimal | None
    system_quantity: Decimal | None
    difference: Decimal | None
    adjusted: bool

    @classmethod
    def from_instance(cls, instance: models.InventoryItem) -> "InventoryItem":
        return cls(
            id=instance.id,
            session_id=instance.session_id,
            ingredient_id=instance.ingredient_id,
            ingredient_name=instance.ingredient.name if instance.ingredient else None,
            ingredient_unit=instance.ingredient.unit if instance.ingredient else None,
            found_quantity=instance.found_quantity,
            system_quantity=instance.system_quantity,
            difference=instance.difference,
            adjusted=instance.adjusted,
        )


@strawberry.type
class InventorySession:
    id: int
    company_id: int
    started_by: int | None
    started_at: datetime.datetime
    completed_at: datetime.datetime | None
    status: str
    protocol_number: str | None
    notes: str | None

    @strawberry.field
    async def items(self, info: strawberry.Info) -> list[InventoryItem]:
        from sqlalchemy.orm import selectinload
        db = info.context["db"]
        stmt = select(models.InventoryItem).options(
            selectinload(models.InventoryItem.ingredient),
        ).where(models.InventoryItem.session_id == self.id)
        res = await db.execute(stmt)
        return [InventoryItem.from_instance(t) for t in res.scalars().all()]

    @classmethod
    def from_instance(cls, instance: models.InventorySession) -> "InventorySession":
        return cls(
            id=instance.id,
            company_id=instance.company_id,
            started_by=instance.started_by,
            started_at=instance.started_at,
            completed_at=instance.completed_at,
            status=instance.status,
            protocol_number=instance.protocol_number,
            notes=instance.notes,
        )
