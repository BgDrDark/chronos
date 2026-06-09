
import strawberry
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.database.models import (
    Vehicle,
    VehicleDocument,
    VehicleDriver,
    VehicleFuel,
    VehicleInspection,
    VehicleInsurance,
    VehicleMileage,
    VehicleRepair,
    VehicleTrip,
    VehicleType,
)
from backend.exceptions import (
    AuthenticationException,
)
from backend.graphql import types

authenticate_msg = "Трябва да се автентикирате"


@strawberry.type
class VehicleQuery:
    @strawberry.field
    async def vehicles(
        self, 
        info: strawberry.Info, 
        company_id: int | None = None,
        search: str | None = None,
        status: str | None = None,
        fuel_type: str | None = None,
        vehicle_type: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> types.VehiclePage:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException()

        from sqlalchemy import func, or_

        stmt = select(Vehicle).options(
            selectinload(Vehicle.vehicle_type),
        )

        # Company filter
        if company_id:
            stmt = stmt.where(Vehicle.company_id == company_id)
        elif current_user.role.name != "super_admin":
            stmt = stmt.where(Vehicle.company_id == current_user.company_id)

        # Search filter
        if search:
            search_term = f"%{search.lower()}%"
            stmt = stmt.where(
                or_(
                    Vehicle.registration_number.ilike(search_term),
                    Vehicle.make.ilike(search_term),
                    Vehicle.model.ilike(search_term),
                    Vehicle.vin.ilike(search_term),
                )
            )

        # Status filter
        if status:
            stmt = stmt.where(Vehicle.status == status)

        # Fuel type filter
        if fuel_type:
            stmt = stmt.where(Vehicle.fuel_type == fuel_type)

        # Vehicle type filter
        if vehicle_type:
            stmt = stmt.join(VehicleType, Vehicle.vehicle_type_id == VehicleType.id).where(VehicleType.code == vehicle_type)

        # Count total
        count_stmt = select(func.count(Vehicle.id)).select_from(Vehicle)
        if company_id:
            count_stmt = count_stmt.where(Vehicle.company_id == company_id)
        elif current_user.role.name != "super_admin":
            count_stmt = count_stmt.where(Vehicle.company_id == current_user.company_id)
        
        if search:
            search_term = f"%{search.lower()}%"
            count_stmt = count_stmt.where(
                or_(
                    Vehicle.registration_number.ilike(search_term),
                    Vehicle.make.ilike(search_term),
                    Vehicle.model.ilike(search_term),
                    Vehicle.vin.ilike(search_term),
                )
            )
        if status:
            count_stmt = count_stmt.where(Vehicle.status == status)
        if fuel_type:
            count_stmt = count_stmt.where(Vehicle.fuel_type == fuel_type)
        if vehicle_type:
            count_stmt = count_stmt.join(VehicleType, Vehicle.vehicle_type_id == VehicleType.id).where(VehicleType.code == vehicle_type)
        
        total_count = (await db.execute(count_stmt)).scalar() or 0

        # Apply pagination
        stmt = stmt.offset(skip).limit(limit)
        res = await db.execute(stmt)
        
        return types.VehiclePage(
            vehicles=[types.Vehicle.from_pydantic(v) for v in res.scalars().all()],
            total_count=total_count
        )

    @strawberry.field
    async def vehicle(self, info: strawberry.Info, id: int) -> types.Vehicle | None:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException()

        vehicle = await db.get(Vehicle, id)

        if vehicle and current_user.role.name != "super_admin" and vehicle.company_id != current_user.company_id:
            return None

        return types.Vehicle.from_pydantic(vehicle) if vehicle else None

    @strawberry.field
    async def vehicle_types(self, info: strawberry.Info) -> list[types.VehicleType]:
        db = info.context["db"]
        res = await db.execute(select(VehicleType))
        return [types.VehicleType.from_pydantic(vt) for vt in res.scalars().all()]

    @strawberry.field
    async def vehicle_documents(self, info: strawberry.Info, vehicle_id: int) -> list[types.VehicleDocument]:
        db = info.context["db"]
        stmt = select(VehicleDocument).where(VehicleDocument.vehicle_id == vehicle_id)
        res = await db.execute(stmt)
        return [types.VehicleDocument.from_pydantic(d) for d in res.scalars().all()]

    @strawberry.field
    async def vehicle_mileage(self, info: strawberry.Info, vehicle_id: int) -> list[types.VehicleMileage]:
        db = info.context["db"]
        stmt = select(VehicleMileage).where(VehicleMileage.vehicle_id == vehicle_id).order_by(VehicleMileage.date.desc())
        res = await db.execute(stmt)
        return [types.VehicleMileage.from_pydantic(m) for m in res.scalars().all()]

    @strawberry.field
    async def vehicle_fuel_logs(self, info: strawberry.Info, vehicle_id: int) -> list[types.VehicleFuel]:
        db = info.context["db"]
        stmt = select(VehicleFuel).where(VehicleFuel.vehicle_id == vehicle_id).order_by(VehicleFuel.date.desc())
        res = await db.execute(stmt)
        return [types.VehicleFuel.from_pydantic(f) for f in res.scalars().all()]

    @strawberry.field
    async def vehicle_repairs(self, info: strawberry.Info, vehicle_id: int) -> list[types.VehicleRepair]:
        db = info.context["db"]
        stmt = select(VehicleRepair).where(VehicleRepair.vehicle_id == vehicle_id).order_by(VehicleRepair.repair_date.desc())
        res = await db.execute(stmt)
        return [types.VehicleRepair.from_pydantic(r) for r in res.scalars().all()] if hasattr(res, "scalars") else []

    @strawberry.field
    async def vehicle_insurances(self, info: strawberry.Info, vehicle_id: int) -> list[types.VehicleInsurance]:
        db = info.context["db"]
        stmt = select(VehicleInsurance).where(VehicleInsurance.vehicle_id == vehicle_id).order_by(VehicleInsurance.start_date.desc())
        res = await db.execute(stmt)
        return [types.VehicleInsurance.from_pydantic(i) for i in res.scalars().all()]

    @strawberry.field
    async def vehicle_inspections(self, info: strawberry.Info, vehicle_id: int) -> list[types.VehicleInspection]:
        db = info.context["db"]
        stmt = select(VehicleInspection).where(VehicleInspection.vehicle_id == vehicle_id).order_by(VehicleInspection.inspection_date.desc())
        res = await db.execute(stmt)
        return [types.VehicleInspection.from_pydantic(i) for i in res.scalars().all()]

    @strawberry.field
    async def vehicle_drivers(self, info: strawberry.Info, vehicle_id: int) -> list[types.VehicleDriver]:
        db = info.context["db"]
        stmt = select(VehicleDriver).where(VehicleDriver.vehicle_id == vehicle_id).order_by(VehicleDriver.assigned_from.desc())
        res = await db.execute(stmt)
        return [types.VehicleDriver.from_pydantic(d) for d in res.scalars().all()]

    @strawberry.field
    async def vehicle_trips(self, info: strawberry.Info, vehicle_id: int) -> list[types.VehicleTrip]:
        db = info.context["db"]
        stmt = select(VehicleTrip).where(VehicleTrip.vehicle_id == vehicle_id).order_by(VehicleTrip.start_time.desc())
        res = await db.execute(stmt)
        return [types.VehicleTrip.from_pydantic(t) for t in res.scalars().all()]
