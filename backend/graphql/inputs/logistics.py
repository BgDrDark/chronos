import datetime
from decimal import Decimal

import strawberry


@strawberry.input
class SupplierInput:
    name: str
    eik: str | None = None
    vat_number: str | None = None
    address: str | None = None
    contact_person: str | None = None
    phone: str | None = None
    email: str | None = None
    company_id: int


@strawberry.input
class UpdateSupplierInput:
    id: int
    name: str
    eik: str | None = None
    vat_number: str | None = None
    address: str | None = None
    contact_person: str | None = None
    phone: str | None = None
    email: str | None = None


@strawberry.input
class StorageZoneInput:
    name: str
    temp_min: float | None = None
    temp_max: float | None = None
    description: str | None = None
    is_active: bool | None = True
    asset_type: str | None = "KMA"
    zone_type: str | None = "food"
    company_id: int


@strawberry.input
class UpdateStorageZoneInput:
    id: int
    name: str
    temp_min: float | None = None
    temp_max: float | None = None
    description: str | None = None
    is_active: bool | None = True
    asset_type: str | None = "KMA"
    zone_type: str | None = "food"
    manager_id: int | None = None


@strawberry.input
class IngredientInput:
    id: int | None = None
    name: str
    unit: str
    barcode: str | None = None
    baseline_min_stock: Decimal = Decimal(0)
    current_price: Decimal | None = None
    storage_zone_id: int | None = None
    is_perishable: bool = True
    expiry_warning_days: int = 3
    allergens: list[str] = strawberry.field(default_factory=list)
    product_type: str = "raw"
    company_id: int


@strawberry.input
class BatchInput:
    id: int | None = None
    ingredient_id: int
    batch_number: str | None = None
    quantity: Decimal
    expiry_date: datetime.date
    supplier_id: int | None = None
    invoice_number: str | None = None
    invoice_date: datetime.date | None = None
    storage_zone_id: int | None = None
