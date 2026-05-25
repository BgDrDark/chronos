import datetime
import enum

import strawberry
from strawberry.experimental import pydantic as sp

from backend import schemas
from backend.utils.json_type import JSONScalar


@strawberry.enum
class VehicleStatus(enum.StrEnum):
    ACTIVE = "active"
    IN_REPAIR = "in_repair"
    OUT_OF_SERVICE = "out_of_service"
    SOLD = "sold"


@strawberry.enum
class FuelType(enum.StrEnum):
    BENZIN = "benzin"
    DIZEL = "dizel"
    ELECTRIC = "electric"
    HYBRID = "hybrid"
    LNG = "lng"
    CNG = "cng"


@strawberry.enum
class VehicleDocumentType(enum.StrEnum):
    INVOICE = "invoice"
    POLICY = "policy"
    INSPECTION = "inspection"
    CONTRACT = "contract"
    OTHER = "other"


@strawberry.enum
class InsuranceType(enum.StrEnum):
    CIVIL = "civil"
    KASKO = "kasko"
    BORDER = "border"


@strawberry.enum
class InspectionResult(enum.StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    PENDING = "pending"


@strawberry.enum
class PreTripStatus(enum.StrEnum):
    PASSED = "passed"
    FAILED = "failed"


@strawberry.enum
class ExpenseType(enum.StrEnum):
    FUEL = "fuel"
    REPAIR = "repair"
    INSURANCE = "insurance"
    INSPECTION = "inspection"
    VIGNETTE = "vignette"
    TOLL = "toll"
    TAX = "tax"
    OTHER = "other"


@sp.type(schemas.VehicleType)
class VehicleType:
    id: strawberry.auto
    name: strawberry.auto
    code: strawberry.auto


@sp.type(schemas.VehicleDocument)
class VehicleDocument:
    id: strawberry.auto
    vehicle_id: strawberry.auto
    document_type: VehicleDocumentType
    title: strawberry.auto
    file_url: strawberry.auto
    issue_date: strawberry.auto
    expiry_date: strawberry.auto
    notes: strawberry.auto
    created_at: strawberry.auto


@sp.type(schemas.VehicleFuelCard)
class VehicleFuelCard:
    id: strawberry.auto
    vehicle_id: strawberry.auto
    card_number: strawberry.auto
    provider: strawberry.auto
    pin: strawberry.auto
    limit: strawberry.auto
    is_active: strawberry.auto
    expiry_date: strawberry.auto
    created_at: strawberry.auto


@sp.type(schemas.VehicleVignette)
class VehicleVignette:
    id: strawberry.auto
    vehicle_id: strawberry.auto
    vignette_type: strawberry.auto
    purchase_date: strawberry.auto
    valid_from: strawberry.auto
    valid_until: strawberry.auto
    price: strawberry.auto
    provider: strawberry.auto
    document_url: strawberry.auto
    created_at: strawberry.auto


@sp.type(schemas.VehicleToll)
class VehicleToll:
    id: strawberry.auto
    vehicle_id: strawberry.auto
    route: strawberry.auto
    toll_amount: strawberry.auto
    toll_date: strawberry.auto
    section: strawberry.auto
    document_url: strawberry.auto
    created_at: strawberry.auto


@sp.type(schemas.VehicleMileage)
class VehicleMileage:
    id: strawberry.auto
    vehicle_id: strawberry.auto
    date: strawberry.auto
    mileage: strawberry.auto
    source: strawberry.auto
    notes: strawberry.auto
    created_at: strawberry.auto


@sp.type(schemas.VehicleFuel)
class VehicleFuel:
    id: strawberry.auto
    vehicle_id: strawberry.auto
    date: strawberry.auto
    fuel_type: strawberry.auto
    quantity: strawberry.auto
    price_per_liter: strawberry.auto
    total_amount: strawberry.auto
    mileage: strawberry.auto
    location: strawberry.auto
    invoice_number: strawberry.auto
    fuel_card_id: strawberry.auto
    driver_id: strawberry.auto
    created_at: strawberry.auto


@sp.type(schemas.VehicleService)
class VehicleService:
    id: strawberry.auto
    name: strawberry.auto
    address: strawberry.auto
    phone: strawberry.auto
    email: strawberry.auto
    contact_person: strawberry.auto
    notes: strawberry.auto
    created_at: strawberry.auto


@sp.type(schemas.VehicleRepair)
class VehicleRepair:
    id: strawberry.auto
    vehicle_id: strawberry.auto
    repair_date: strawberry.auto
    repair_type: strawberry.auto
    description: strawberry.auto
    parts: JSONScalar | None = None
    labor_hours: strawberry.auto
    labor_cost: strawberry.auto
    parts_cost: strawberry.auto
    total_cost: strawberry.auto
    mileage: strawberry.auto
    vehicle_service_id: strawberry.auto
    warranty_months: strawberry.auto
    next_service_km: strawberry.auto
    notes: strawberry.auto
    created_at: strawberry.auto


@sp.type(schemas.VehicleSchedule)
class VehicleSchedule:
    id: strawberry.auto
    vehicle_id: strawberry.auto
    schedule_type: strawberry.auto
    interval_km: strawberry.auto
    interval_months: strawberry.auto
    last_service_date: strawberry.auto
    last_service_km: strawberry.auto
    next_service_date: strawberry.auto
    next_service_km: strawberry.auto
    vehicle_service_id: strawberry.auto
    notes: strawberry.auto
    created_at: strawberry.auto
    updated_at: strawberry.auto


@sp.type(schemas.VehicleInsurance)
class VehicleInsurance:
    id: strawberry.auto
    vehicle_id: strawberry.auto
    insurance_type: InsuranceType
    policy_number: strawberry.auto
    insurance_company: strawberry.auto
    start_date: strawberry.auto
    end_date: strawberry.auto
    premium: strawberry.auto
    coverage_amount: strawberry.auto
    payment_type: strawberry.auto
    document_url: strawberry.auto
    notes: strawberry.auto
    created_at: strawberry.auto


@sp.type(schemas.VehicleInspection)
class VehicleInspection:
    id: strawberry.auto
    vehicle_id: strawberry.auto
    inspection_date: strawberry.auto
    valid_until: strawberry.auto
    result: InspectionResult
    mileage: strawberry.auto
    inspector: strawberry.auto
    certificate_number: strawberry.auto
    next_inspection_date: strawberry.auto
    notes: strawberry.auto
    created_at: strawberry.auto


@sp.type(schemas.VehiclePreTripInspection)
class VehiclePreTripInspection:
    id: strawberry.auto
    vehicle_id: strawberry.auto
    driver_id: strawberry.auto
    inspection_date: strawberry.auto
    tires_condition: strawberry.auto
    tires_pressure: strawberry.auto
    tires_tread: strawberry.auto
    brakes_condition: strawberry.auto
    brakes_parking: strawberry.auto
    lights_headlights: strawberry.auto
    lights_brake: strawberry.auto
    lights_turn: strawberry.auto
    lights_warning: strawberry.auto
    fluids_oil: strawberry.auto
    fluids_coolant: strawberry.auto
    fluids_washer: strawberry.auto
    fluids_brake: strawberry.auto
    mirrors: strawberry.auto
    wipers: strawberry.auto
    horn: strawberry.auto
    seatbelts: strawberry.auto
    first_aid_kit: strawberry.auto
    fire_extinguisher: strawberry.auto
    warning_triangle: strawberry.auto
    overall_status: PreTripStatus
    notes: strawberry.auto
    photos: JSONScalar | None = None
    created_at: strawberry.auto


@sp.type(schemas.VehicleDriver)
class VehicleDriver:
    id: strawberry.auto
    vehicle_id: strawberry.auto
    user_id: strawberry.auto
    assigned_from: strawberry.auto
    assigned_to: strawberry.auto
    is_primary: strawberry.auto
    created_at: strawberry.auto


@sp.type(schemas.VehicleTrip)
class VehicleTrip:
    id: strawberry.auto
    vehicle_id: strawberry.auto
    driver_id: strawberry.auto
    delivery_id: strawberry.auto
    start_address: strawberry.auto
    end_address: strawberry.auto
    start_time: strawberry.auto
    end_time: strawberry.auto
    distance_km: strawberry.auto
    purpose: strawberry.auto
    expenses: strawberry.auto
    notes: strawberry.auto
    created_at: strawberry.auto
    updated_at: strawberry.auto


@sp.type(schemas.VehicleExpense)
class VehicleExpense:
    id: strawberry.auto
    vehicle_id: strawberry.auto
    expense_type: ExpenseType
    expense_date: strawberry.auto
    amount: strawberry.auto
    vat_amount: strawberry.auto
    total_amount: strawberry.auto
    description: strawberry.auto
    reference_id: strawberry.auto
    reference_type: strawberry.auto
    is_deductible: strawberry.auto
    cost_center_id: strawberry.auto
    company_id: strawberry.auto
    created_at: strawberry.auto


@sp.type(schemas.Vehicle)
class Vehicle:
    id: strawberry.auto
    registration_number: strawberry.auto
    vin: strawberry.auto
    make: strawberry.auto
    model: strawberry.auto
    year: strawberry.auto
    vehicle_type_id: strawberry.auto
    fuel_type: FuelType
    engine_number: strawberry.auto
    chassis_number: strawberry.auto
    color: strawberry.auto
    initial_mileage: strawberry.auto
    is_company: strawberry.auto
    owner_name: strawberry.auto
    status: VehicleStatus
    notes: strawberry.auto
    company_id: strawberry.auto
    created_at: strawberry.auto
    updated_at: strawberry.auto

    @strawberry.field
    async def type(self, info: strawberry.Info) -> VehicleType | None:
        if not self.vehicle_type_id:
            return None
        db = info.context["db"]
        from backend.database.models import VehicleType as DbVehicleType
        res = await db.get(DbVehicleType, self.vehicle_type_id)
        return VehicleType.from_pydantic(res) if res else None

    @strawberry.field
    async def documents(self, info: strawberry.Info) -> list[VehicleDocument] | None:
        db = info.context["db"]
        from sqlalchemy import select
        from backend.database.models import VehicleDocument as DbModel
        stmt = select(DbModel).where(DbModel.vehicle_id == self.id)
        res = await db.execute(stmt)
        return [VehicleDocument.from_pydantic(d) for d in res.scalars().all()]

    @strawberry.field
    async def fuel_cards(self, info: strawberry.Info) -> list[VehicleFuelCard] | None:
        db = info.context["db"]
        from sqlalchemy import select
        from backend.database.models import VehicleFuelCard as DbModel
        stmt = select(DbModel).where(DbModel.vehicle_id == self.id)
        res = await db.execute(stmt)
        return [VehicleFuelCard.from_pydantic(d) for d in res.scalars().all()]

    @strawberry.field
    async def vignettes(self, info: strawberry.Info) -> list[VehicleVignette] | None:
        db = info.context["db"]
        from sqlalchemy import select
        from backend.database.models import VehicleVignette as DbModel
        stmt = select(DbModel).where(DbModel.vehicle_id == self.id)
        res = await db.execute(stmt)
        return [VehicleVignette.from_pydantic(d) for d in res.scalars().all()]

    @strawberry.field
    async def tolls(self, info: strawberry.Info) -> list[VehicleToll]:
        db = info.context["db"]
        from sqlalchemy import select
        from backend.database.models import VehicleToll as DbModel
        stmt = select(DbModel).where(DbModel.vehicle_id == self.id)
        res = await db.execute(stmt)
        return [VehicleToll.from_pydantic(d) for d in res.scalars().all()]

    @strawberry.field
    async def mileages(self, info: strawberry.Info) -> list[VehicleMileage]:
        db = info.context["db"]
        from sqlalchemy import select
        from backend.database.models import VehicleMileage as DbModel
        stmt = select(DbModel).where(DbModel.vehicle_id == self.id)
        res = await db.execute(stmt)
        return [VehicleMileage.from_pydantic(d) for d in res.scalars().all()]

    @strawberry.field
    async def fuel_records(self, info: strawberry.Info) -> list[VehicleFuel]:
        db = info.context["db"]
        from sqlalchemy import select
        from backend.database.models import VehicleFuel as DbModel
        stmt = select(DbModel).where(DbModel.vehicle_id == self.id)
        res = await db.execute(stmt)
        return [VehicleFuel.from_pydantic(d) for d in res.scalars().all()]

    @strawberry.field
    async def repairs(self, info: strawberry.Info) -> list[VehicleRepair]:
        db = info.context["db"]
        from sqlalchemy import select
        from backend.database.models import VehicleRepair as DbModel
        stmt = select(DbModel).where(DbModel.vehicle_id == self.id)
        res = await db.execute(stmt)
        return [VehicleRepair.from_pydantic(d) for d in res.scalars().all()]

    @strawberry.field
    async def schedules(self, info: strawberry.Info) -> list[VehicleSchedule]:
        db = info.context["db"]
        from sqlalchemy import select
        from backend.database.models import VehicleSchedule as DbModel
        stmt = select(DbModel).where(DbModel.vehicle_id == self.id)
        res = await db.execute(stmt)
        return [VehicleSchedule.from_pydantic(d) for d in res.scalars().all()]

    @strawberry.field
    async def inspections(self, info: strawberry.Info) -> list[VehicleInspection]:
        db = info.context["db"]
        from sqlalchemy import select
        from backend.database.models import VehicleInspection as DbModel
        stmt = select(DbModel).where(DbModel.vehicle_id == self.id)
        res = await db.execute(stmt)
        return [VehicleInspection.from_pydantic(d) for d in res.scalars().all()]

    @strawberry.field
    async def pre_trip_inspections(self, info: strawberry.Info) -> list[VehiclePreTripInspection]:
        db = info.context["db"]
        from sqlalchemy import select
        from backend.database.models import VehiclePreTripInspection as DbModel
        stmt = select(DbModel).where(DbModel.vehicle_id == self.id)
        res = await db.execute(stmt)
        return [VehiclePreTripInspection.from_pydantic(d) for d in res.scalars().all()]

    @strawberry.field
    async def drivers(self, info: strawberry.Info) -> list[VehicleDriver]:
        db = info.context["db"]
        from sqlalchemy import select
        from backend.database.models import VehicleDriver as DbModel
        stmt = select(DbModel).where(DbModel.vehicle_id == self.id)
        res = await db.execute(stmt)
        return [VehicleDriver.from_pydantic(d) for d in res.scalars().all()]

    @strawberry.field
    async def trips(self, info: strawberry.Info) -> list[VehicleTrip]:
        db = info.context["db"]
        from sqlalchemy import select
        from backend.database.models import VehicleTrip as DbModel
        stmt = select(DbModel).where(DbModel.vehicle_id == self.id)
        res = await db.execute(stmt)
        return [VehicleTrip.from_pydantic(d) for d in res.scalars().all()]

    @strawberry.field
    async def expenses(self, info: strawberry.Info) -> list[VehicleExpense]:
        db = info.context["db"]
        from sqlalchemy import select
        from backend.database.models import VehicleExpense as DbModel
        stmt = select(DbModel).where(DbModel.vehicle_id == self.id)
        res = await db.execute(stmt)
        return [VehicleExpense.from_pydantic(d) for d in res.scalars().all()]


__all__ = [
    "ExpenseType",
    "FuelType",
    "InspectionResult",
    "InsuranceType",
    "PreTripStatus",
    "Vehicle",
    "VehicleDocument",
    "VehicleDocumentType",
    "VehicleDriver",
    "VehicleExpense",
    "VehicleFuel",
    "VehicleFuelCard",
    "VehicleInspection",
    "VehicleInsurance",
    "VehicleMileage",
    "VehiclePreTripInspection",
    "VehicleRepair",
    "VehicleSchedule",
    "VehicleService",
    "VehicleStatus",
    "VehicleToll",
    "VehicleTrip",
    "VehicleType",
    "VehicleVignette",
]
