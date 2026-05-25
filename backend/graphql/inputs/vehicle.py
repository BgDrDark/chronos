import datetime

import strawberry


@strawberry.input
class VehicleCreateInput:
    registration_number: str
    vin: str | None = None
    make: str
    model: str | None = None
    year: int | None = None
    vehicle_type: str | None = "car"
    fuel_type: str | None = "dizel"
    status: str | None = "active"
    color: str | None = None
    initial_mileage: int | None = 0
    is_company_vehicle: bool | None = True
    notes: str | None = None
    company_id: int | None = None


@strawberry.input
class VehicleUpdateInput:
    registration_number: str | None = None
    vin: str | None = None
    make: str | None = None
    model: str | None = None
    year: int | None = None
    vehicle_type: str | None = None
    fuel_type: str | None = None
    status: str | None = None
    color: str | None = None
    initial_mileage: int | None = None
    is_company_vehicle: bool | None = None
    notes: str | None = None


@strawberry.input
class VehicleMileageInput:
    vehicle_id: int
    date: datetime.datetime
    mileage: int
    notes: str | None = None


@strawberry.input
class VehicleFuelInput:
    vehicle_id: int
    date: datetime.datetime
    liters: float
    price: float
    total: float
    fuel_type: str | None = "dizel"
    notes: str | None = None


@strawberry.input
class VehicleRepairInput:
    vehicle_id: int
    date: datetime.datetime
    description: str
    cost: float | None = 0
    repair_type: str | None = "maintenance"
    notes: str | None = None


@strawberry.input
class VehicleInsuranceInput:
    vehicle_id: int
    provider: str
    policy_number: str
    start_date: datetime.datetime
    end_date: datetime.datetime
    premium: float | None = 0
    insurance_type: str | None = "grazhdanska"
    notes: str | None = None


@strawberry.input
class VehicleInspectionInput:
    vehicle_id: int
    date: datetime.datetime
    next_date: datetime.datetime | None = None
    cost: float | None = 0
    result: str | None = "passed"
    protocol_number: str | None = None
    notes: str | None = None
    inspection_type: str | None = "periodic"
    next_inspection_date: datetime.datetime | None = None



@strawberry.input
class VehicleDriverInput:
    vehicle_id: int
    user_id: int
    license_number: str
    license_expiry: datetime.datetime
    phone: str | None = None
    category: str | None = "B"
    is_primary: bool | None = False
    notes: str | None = None
    start_date: datetime.datetime | None = None
    end_date: datetime.datetime | None = None



@strawberry.input
class VehicleTripInput:
    vehicle_id: int
    user_id: int
    start_date: datetime.datetime
    end_date: datetime.datetime | None = None
    start_location: str | None = None
    end_location: str | None = None
    distance: float | None = 0
    trip_type: str | None = "business"
    notes: str | None = None


@strawberry.input
class VehicleMileageUpdateInput:
    date: datetime.datetime | None = None
    mileage: int | None = None
    notes: str | None = None


@strawberry.input
class VehicleFuelUpdateInput:
    date: datetime.datetime | None = None
    liters: float | None = None
    price: float | None = None
    total: float | None = None
    fuel_type: str | None = None
    notes: str | None = None


@strawberry.input
class VehicleRepairUpdateInput:
    date: datetime.datetime | None = None
    description: str | None = None
    cost: float | None = None
    repair_type: str | None = None
    notes: str | None = None


@strawberry.input
class VehicleInsuranceUpdateInput:
    provider: str | None = None
    policy_number: str | None = None
    start_date: datetime.datetime | None = None
    end_date: datetime.datetime | None = None
    premium: float | None = None
    insurance_type: str | None = None
    notes: str | None = None


@strawberry.input
class VehicleInspectionUpdateInput:
    date: datetime.datetime | None = None
    next_date: datetime.datetime | None = None
    cost: float | None = None
    result: str | None = None
    protocol_number: str | None = None
    notes: str | None = None


@strawberry.input
class VehicleDriverUpdateInput:
    license_number: str | None = None
    license_expiry: datetime.datetime | None = None
    phone: str | None = None
    category: str | None = None
    is_primary: bool | None = None
    notes: str | None = None


@strawberry.input
class VehicleTripUpdateInput:
    start_date: datetime.datetime | None = None
    end_date: datetime.datetime | None = None
    start_location: str | None = None
    end_location: str | None = None
    distance: float | None = None
    trip_type: str | None = None
    notes: str | None = None
