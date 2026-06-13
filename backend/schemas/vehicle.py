from datetime import date, datetime
from decimal import Decimal
from typing import Any

from backend.schemas.base import CustomBaseModel


class VehicleType(CustomBaseModel):
    id: int
    name: str
    code: str | None = None


class Vehicle(CustomBaseModel):
    id: int
    registration_number: str
    vin: str | None = None
    make: str
    model: str
    year: int | None = None
    vehicle_type_id: int | None = None
    fuel_type: str = "dizel"
    engine_number: str | None = None
    chassis_number: str | None = None
    color: str | None = None
    initial_mileage: int | None = None
    is_company: bool | None = None
    owner_name: str | None = None
    status: str = "active"
    notes: str | None = None
    company_id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None


class VehicleDocument(CustomBaseModel):
    id: int
    vehicle_id: int
    document_type: str
    title: str
    file_url: str | None = None
    issue_date: date | None = None
    expiry_date: date | None = None
    notes: str | None = None
    created_at: datetime | None = None


class VehicleFuelCard(CustomBaseModel):
    id: int
    vehicle_id: int
    card_number: str
    provider: str | None = None
    pin: str | None = None
    limit: Decimal | None = None
    is_active: bool | None = None
    expiry_date: date | None = None
    created_at: datetime | None = None


class VehicleVignette(CustomBaseModel):
    id: int
    vehicle_id: int
    vignette_type: str
    purchase_date: date | None = None
    valid_from: date | None = None
    valid_until: date | None = None
    price: Decimal | None = None
    provider: str | None = None
    document_url: str | None = None
    created_at: datetime | None = None


class VehicleToll(CustomBaseModel):
    id: int
    vehicle_id: int
    route: str | None = None
    toll_amount: Decimal
    toll_date: datetime | None = None
    section: str | None = None
    document_url: str | None = None
    created_at: datetime | None = None


class VehicleMileage(CustomBaseModel):
    id: int
    vehicle_id: int
    date: date
    mileage: int
    source: str | None = None
    notes: str | None = None
    created_at: datetime | None = None


class VehicleFuel(CustomBaseModel):
    id: int
    vehicle_id: int
    date: datetime
    fuel_type: str | None = None
    quantity: Decimal
    price_per_liter: Decimal
    total_amount: Decimal
    mileage: int | None = None
    location: str | None = None
    invoice_number: str | None = None
    fuel_card_id: int | None = None
    driver_id: int | None = None
    efficiency_l_per_100km: float | None = None
    is_anomaly: bool = False
    created_at: datetime | None = None


class VehicleService(CustomBaseModel):
    id: int
    name: str
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    contact_person: str | None = None
    notes: str | None = None
    created_at: datetime | None = None


class VehicleRepair(CustomBaseModel):
    id: int
    vehicle_id: int
    repair_date: datetime
    repair_type: str | None = None
    description: str | None = None
    parts: Any = None
    labor_hours: Decimal | None = None
    labor_cost: Decimal | None = None
    parts_cost: Decimal | None = None
    total_cost: Decimal | None = None
    mileage: int | None = None
    vehicle_service_id: int | None = None
    warranty_months: int | None = None
    next_service_km: int | None = None
    notes: str | None = None
    created_at: datetime | None = None


class VehicleSchedule(CustomBaseModel):
    id: int
    vehicle_id: int
    schedule_type: str
    interval_km: int | None = None
    interval_months: int | None = None
    last_service_date: date | None = None
    last_service_km: int | None = None
    next_service_date: date | None = None
    next_service_km: int | None = None
    vehicle_service_id: int | None = None
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class VehicleInsurance(CustomBaseModel):
    id: int
    vehicle_id: int
    insurance_type: str
    policy_number: str
    insurance_company: str | None = None
    start_date: date
    end_date: date
    premium: Decimal | None = None
    coverage_amount: Decimal | None = None
    payment_type: str | None = None
    document_url: str | None = None
    notes: str | None = None
    created_at: datetime | None = None


class VehicleInspection(CustomBaseModel):
    id: int
    vehicle_id: int
    inspection_date: date
    valid_until: date
    result: str = "pending"
    mileage: int | None = None
    inspector: str | None = None
    certificate_number: str | None = None
    next_inspection_date: date | None = None
    notes: str | None = None
    created_at: datetime | None = None


class VehiclePreTripInspection(CustomBaseModel):
    id: int
    vehicle_id: int
    driver_id: int
    inspection_date: datetime | None = None
    tires_condition: bool | None = None
    tires_pressure: bool | None = None
    tires_tread: bool | None = None
    brakes_condition: bool | None = None
    brakes_parking: bool | None = None
    lights_headlights: bool | None = None
    lights_brake: bool | None = None
    lights_turn: bool | None = None
    lights_warning: bool | None = None
    fluids_oil: bool | None = None
    fluids_coolant: bool | None = None
    fluids_washer: bool | None = None
    fluids_brake: bool | None = None
    mirrors: bool | None = None
    wipers: bool | None = None
    horn: bool | None = None
    seatbelts: bool | None = None
    first_aid_kit: bool | None = None
    fire_extinguisher: bool | None = None
    warning_triangle: bool | None = None
    overall_status: str = "failed"
    notes: str | None = None
    photos: Any = None
    created_at: datetime | None = None


class VehicleDriver(CustomBaseModel):
    id: int
    vehicle_id: int
    user_id: int
    assigned_from: date
    assigned_to: date | None = None
    is_primary: bool | None = None
    created_at: datetime | None = None


class VehicleTrip(CustomBaseModel):
    id: int
    vehicle_id: int
    driver_id: int
    delivery_id: int | None = None
    start_address: str | None = None
    end_address: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    distance_km: int | None = None
    purpose: str | None = None
    expenses: Decimal | None = None
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class VehicleExpense(CustomBaseModel):
    id: int
    vehicle_id: int
    expense_type: str
    expense_date: date
    amount: Decimal | None = None
    vat_amount: Decimal | None = None
    total_amount: Decimal | None = None
    description: str | None = None
    reference_id: int | None = None
    reference_type: str | None = None
    is_deductible: bool | None = None
    cost_center_id: int | None = None
    company_id: int
    created_at: datetime | None = None


class VehicleAccident(CustomBaseModel):
    id: int
    vehicle_id: int
    date: date
    location: str | None = None
    description: str
    severity: str = "minor"
    estimated_cost: Decimal = Decimal(0)
    actual_cost: Decimal = Decimal(0)
    third_party_name: str | None = None
    third_party_insurance: str | None = None
    police_report_number: str | None = None
    photos: dict | None = None
    downtime_days: int = 0
    status: str = "reported"
    created_at: datetime | None = None
