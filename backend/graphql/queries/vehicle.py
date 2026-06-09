
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

    @strawberry.field
    async def vehicle_schedules(self, info: strawberry.Info, vehicle_id: int) -> list[types.VehicleSchedule]:
        db = info.context["db"]
        from backend.database.models import VehicleSchedule
        stmt = select(VehicleSchedule).where(VehicleSchedule.vehicle_id == vehicle_id).order_by(VehicleSchedule.next_service_date.asc())
        res = await db.execute(stmt)
        return [types.VehicleSchedule.from_pydantic(s) for s in res.scalars().all()]

    @strawberry.field
    async def vehicle_accidents(self, info: strawberry.Info, vehicle_id: int) -> list[types.VehicleAccident]:
        db = info.context["db"]
        from backend.database.models import VehicleAccident
        stmt = select(VehicleAccident).where(VehicleAccident.vehicle_id == vehicle_id).order_by(VehicleAccident.date.desc())
        res = await db.execute(stmt)
        return [types.VehicleAccident.from_pydantic(a) for a in res.scalars().all()]

    @strawberry.field
    async def vehicle_cost_summary(
        self,
        info: strawberry.Info,
        vehicle_id: int,
        year: int | None = None,
    ) -> types.VehicleCostSummary:
        """Calculate cost summary for a vehicle"""
        db = info.context["db"]
        from sqlalchemy import func

        # Base filters
        base_filters = [VehicleFuel.vehicle_id == vehicle_id]
        if year:
            base_filters.append(func.extract('year', VehicleFuel.date) == year)

        # Fuel costs
        fuel_stmt = select(func.coalesce(func.sum(VehicleFuel.total), 0)).where(*base_filters)
        total_fuel = float((await db.execute(fuel_stmt)).scalar())

        # Repair costs
        repair_filters = [VehicleRepair.vehicle_id == vehicle_id]
        if year:
            repair_filters.append(func.extract('year', VehicleRepair.repair_date) == year)
        repair_stmt = select(func.coalesce(func.sum(VehicleRepair.cost), 0)).where(*repair_filters)
        total_repairs = float((await db.execute(repair_stmt)).scalar())

        # Inspection costs
        insp_filters = [VehicleInspection.vehicle_id == vehicle_id]
        if year:
            insp_filters.append(func.extract('year', VehicleInspection.inspection_date) == year)
        insp_stmt = select(func.coalesce(func.sum(VehicleInspection.cost), 0)).where(*insp_filters)
        total_inspections = float((await db.execute(insp_stmt)).scalar())

        # Insurance premiums
        ins_filters = [VehicleInsurance.vehicle_id == vehicle_id]
        if year:
            ins_filters.append(func.extract('year', VehicleInsurance.start_date) == year)
        ins_stmt = select(func.coalesce(func.sum(VehicleInsurance.premium), 0)).where(*ins_filters)
        total_insurances = float((await db.execute(ins_stmt)).scalar())

        # Vignette costs (if table exists)
        try:
            from backend.database.models import VehicleVignette
            vig_filters = [VehicleVignette.vehicle_id == vehicle_id]
            if year:
                vig_filters.append(func.extract('year', VehicleVignette.start_date) == year)
            vig_stmt = select(func.coalesce(func.sum(VehicleVignette.cost), 0)).where(*vig_filters)
            total_vignettes = float((await db.execute(vig_stmt)).scalar())
        except Exception:
            total_vignettes = 0

        # Toll costs (if table exists)
        try:
            from backend.database.models import VehicleToll
            toll_filters = [VehicleToll.vehicle_id == vehicle_id]
            if year:
                toll_filters.append(func.extract('year', VehicleToll.date) == year)
            toll_stmt = select(func.coalesce(func.sum(VehicleToll.cost), 0)).where(*toll_filters)
            total_tolls = float((await db.execute(toll_stmt)).scalar())
        except Exception:
            total_tolls = 0

        grand_total = total_fuel + total_repairs + total_inspections + total_insurances + total_vignettes + total_tolls

        # Calculate depreciation
        vehicle_res = await db.execute(select(Vehicle).where(Vehicle.id == vehicle_id))
        vehicle = vehicle_res.scalars().first()
        depreciation = 0
        if vehicle and vehicle.purchase_price and vehicle.purchase_date and vehicle.useful_life_years:
            from datetime import date
            today = date.today()
            years_passed = (today - vehicle.purchase_date).days / 365.25
            if years_passed < vehicle.useful_life_years:
                salvage = vehicle.salvage_value or 0
                annual_dep = (vehicle.purchase_price - salvage) / vehicle.useful_life_years
                depreciation = annual_dep * years_passed

        # Calculate cost per km
        mileage_stmt = select(func.max(VehicleMileage.mileage)).where(VehicleMileage.vehicle_id == vehicle_id)
        current_mileage = (await db.execute(mileage_stmt)).scalar() or 0
        initial_mileage_stmt = select(Vehicle.initial_mileage).where(Vehicle.id == vehicle_id)
        initial_mileage = (await db.execute(initial_mileage_stmt)).scalar() or 0
        distance = current_mileage - initial_mileage
        cost_per_km = (grand_total / distance) if distance > 0 and grand_total > 0 else None

        return types.VehicleCostSummary(
            total_fuel=total_fuel,
            total_repairs=total_repairs,
            total_inspections=total_inspections,
            total_insurances=total_insurances,
            total_vignettes=total_vignettes,
            total_tolls=total_tolls,
            grand_total=grand_total + depreciation,
            cost_per_km=cost_per_km,
        )
