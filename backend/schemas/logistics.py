from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import ConfigDict, model_validator

from backend.schemas.base import CustomBaseModel


class StorageZoneBase(CustomBaseModel):

    name: str
    temp_min: Decimal | None = None
    temp_max: Decimal | None = None
    description: str | None = None
    company_id: int
    is_active: bool = True
    asset_type: str = "KMA"
    zone_type: str = "food"


class StorageZoneCreate(StorageZoneBase):
    pass


class StorageZone(StorageZoneBase):
    id: int


class IngredientBase(CustomBaseModel):
    name: str
    unit: str = "kg"
    barcode: str | None = None
    baseline_min_stock: Decimal = Decimal(0)
    current_price: Decimal | None = None
    storage_zone_id: int | None = None
    is_perishable: bool = True
    expiry_warning_days: int = 3
    allergens: list[Any] = []
    company_id: int


class IngredientCreate(IngredientBase):
    pass


class Ingredient(IngredientBase):
    id: int


class BatchBase(CustomBaseModel):

    ingredient_id: int
    batch_number: str | None = None
    quantity: Decimal
    unit_value: Decimal | None = None
    production_date: date | None = None
    expiry_date: date
    price_no_vat: Decimal | None = None
    vat_percent: Decimal | None = 20
    price_with_vat: Decimal | None = None
    supplier_id: int | None = None
    is_stock_receipt: bool = False
    invoice_number: str | None = None
    invoice_date: date | None = None
    storage_zone_id: int | None = None


class BatchCreate(BatchBase):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @model_validator(mode="after")
    def check_production_fields(self) -> "BatchCreate":
        if (self.batch_number or self.production_date) and not (self.batch_number and self.production_date):
            raise ValueError("Партиден номер и дата на производство трябва да бъдат въведени заедно.")
        return self


class Batch(BatchBase):
    id: int
    received_by: int | None = None
    status: str
    received_at: datetime


class SupplierBase(CustomBaseModel):
    name: str
    eik: str | None = None
    vat_number: str | None = None
    address: str | None = None
    contact_person: str | None = None
    phone: str | None = None
    email: str | None = None
    company_id: int


class Supplier(SupplierBase):
    id: int
