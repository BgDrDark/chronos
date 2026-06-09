from __future__ import annotations

import datetime
import re

import strawberry

from backend.crud.repositories import vehicle_repo
from backend.exceptions import NotFoundException, ValidationException
from backend.graphql import types
from backend.graphql.inputs.vehicle import (
    VehicleCreateInput,
    VehicleDriverInput,
    VehicleDriverUpdateInput,
    VehicleFuelInput,
    VehicleFuelUpdateInput,
    VehicleInspectionInput,
    VehicleInspectionUpdateInput,
    VehicleInsuranceInput,
    VehicleInsuranceUpdateInput,
    VehicleMileageInput,
    VehicleMileageUpdateInput,
    VehicleRepairInput,
    VehicleRepairUpdateInput,
    VehicleTripInput,
    VehicleTripUpdateInput,
    VehicleUpdateInput,
)
from backend.graphql.utils.permission_checker import check_company_access


@strawberry.type
class VehicleMutation:
    @strawberry.mutation
    async def create_vehicle(self, input: VehicleCreateInput, info: strawberry.Info) -> types.Vehicle:
        db = info.context["db"]
        current_user = info.context["current_user"]

        company_id = input.company_id or current_user.company_id

        # VIN Validation
        if input.vin:
            if not re.match(r'^[A-HJ-NPR-Z0-9]{17}$', input.vin.upper()):
                raise ValidationException.detail("VIN трябва да е точно 17 символа (без I, O, Q)")
            input.vin = input.vin.upper()

        # Year Validation
        current_year = datetime.datetime.now().year
        if input.year and (input.year < 1900 or input.year > current_year + 1):
            raise ValidationException.detail(f"Годината трябва да е между 1900 и {current_year + 1}")

        # Initial Mileage Validation
        if input.initial_mileage is not None and input.initial_mileage < 0:
            raise ValidationException.detail("Началният пробег не може да бъде отрицателен")

        vehicle_type_obj = None
        if input.vehicle_type:
            from sqlalchemy import select

            from backend.database.models import VehicleType
            vt_result = await db.execute(select(VehicleType).where(VehicleType.code == input.vehicle_type))
            vehicle_type_obj = vt_result.scalar_one_or_none()

        vehicle = await vehicle_repo.create_vehicle(
            db,
            registration_number=input.registration_number,
            vin=input.vin,
            make=input.make,
            model=input.model,
            year=input.year,
            vehicle_type=vehicle_type_obj,
            fuel_type=input.fuel_type,
            status=input.status,
            color=input.color,
            initial_mileage=input.initial_mileage,
            is_company=input.is_company_vehicle,
            notes=input.notes,
            company_id=company_id,
        )
        await db.commit()
        await db.refresh(vehicle)
        return types.Vehicle.from_pydantic(vehicle)

    @strawberry.mutation
    async def update_vehicle(self, id: int, input: VehicleUpdateInput, info: strawberry.Info) -> types.Vehicle:
        db = info.context["db"]
        current_user = info.context["current_user"]
        check_company_access(db, current_user, "Vehicle", id)

        # VIN Validation
        if input.vin:
            if not re.match(r'^[A-HJ-NPR-Z0-9]{17}$', input.vin.upper()):
                raise ValidationException.detail("VIN трябва да е точно 17 символа (без I, O, Q)")
            input.vin = input.vin.upper()

        # Year Validation
        current_year = datetime.datetime.now().year
        if input.year and (input.year < 1900 or input.year > current_year + 1):
            raise ValidationException.detail(f"Годината трябва да е между 1900 и {current_year + 1}")

        # Initial Mileage Validation
        if input.initial_mileage is not None and input.initial_mileage < 0:
            raise ValidationException.detail("Началният пробег не може да бъде отрицателен")

        update_data = {
            "registration_number": input.registration_number,
            "vin": input.vin,
            "make": input.make,
            "model": input.model,
            "year": input.year,
            "fuel_type": input.fuel_type,
            "status": input.status,
            "color": input.color,
            "initial_mileage": input.initial_mileage,
            "is_company": input.is_company_vehicle,
            "notes": input.notes,
        }

        if input.vehicle_type:
            from sqlalchemy import select

            from backend.database.models import VehicleType
            vt_result = await db.execute(select(VehicleType).where(VehicleType.code == input.vehicle_type))
            vt_obj = vt_result.scalar_one_or_none()
            update_data["vehicle_type"] = vt_obj

        vehicle = await vehicle_repo.update_vehicle(db, vehicle_id=id, **update_data)
        if not vehicle:
            raise NotFoundException.vehicle()
        await db.commit()
        await db.refresh(vehicle)
        return types.Vehicle.from_pydantic(vehicle)

    @strawberry.mutation
    async def delete_vehicle(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        check_company_access(db, current_user, "Vehicle", id)

        success = await vehicle_repo.delete_vehicle(db, vehicle_id=id)
        if not success:
            raise NotFoundException.vehicle()
        await db.commit()
        return True

    @strawberry.mutation
    async def create_vehicle_mileage(self, input: VehicleMileageInput, info: strawberry.Info) -> types.VehicleMileage:
        db = info.context["db"]
        current_user = info.context["current_user"]
        check_company_access(db, current_user, "Vehicle", input.vehicle_id)

        # Validate mileage is not less than the last recorded mileage
        from sqlalchemy import select
        from backend.database.models import VehicleMileage
        last_mileage_stmt = select(VehicleMileage).where(
            VehicleMileage.vehicle_id == input.vehicle_id
        ).order_by(VehicleMileage.date.desc(), VehicleMileage.id.desc()).limit(1)
        last_mileage_res = await db.execute(last_mileage_stmt)
        last_mileage_record = last_mileage_res.scalars().first()

        if last_mileage_record and input.mileage < last_mileage_record.mileage:
            raise ValidationException.detail(f"Пробегът не може да бъде по-малък от последния запис ({last_mileage_record.mileage} км)")

        record = await vehicle_repo.create_vehicle_mileage(
            db,
            vehicle_id=input.vehicle_id,
            date=input.date.date() if hasattr(input.date, "date") else input.date,
            mileage=input.mileage,
            notes=input.notes,
        )
        await db.commit()
        await db.refresh(record)
        return types.VehicleMileage.from_pydantic(record)

    @strawberry.mutation
    async def create_vehicle_fuel(self, input: VehicleFuelInput, info: strawberry.Info) -> types.VehicleFuel:
        db = info.context["db"]
        current_user = info.context["current_user"]
        check_company_access(db, current_user, "Vehicle", input.vehicle_id)

        record = await vehicle_repo.create_vehicle_fuel(
            db,
            vehicle_id=input.vehicle_id,
            date=input.date.date() if hasattr(input.date, "date") else input.date,
            liters=input.liters,
            price=input.price,
            total=input.total,
            fuel_type=input.fuel_type,
            notes=input.notes,
        )
        await db.commit()
        await db.refresh(record)
        return types.VehicleFuel.from_pydantic(record)

    @strawberry.mutation
    async def create_vehicle_repair(self, input: VehicleRepairInput, info: strawberry.Info) -> types.VehicleRepair:
        db = info.context["db"]
        current_user = info.context["current_user"]
        check_company_access(db, current_user, "Vehicle", input.vehicle_id)

        record = await vehicle_repo.create_vehicle_repair(
            db,
            vehicle_id=input.vehicle_id,
            date=input.date.date() if hasattr(input.date, "date") else input.date,
            description=input.description,
            cost=input.cost,
            notes=input.notes,
        )
        await db.commit()
        await db.refresh(record)
        return types.VehicleRepair.from_pydantic(record)

    @strawberry.mutation
    async def create_vehicle_insurance(self, input: VehicleInsuranceInput, info: strawberry.Info) -> types.VehicleInsurance:
        db = info.context["db"]
        current_user = info.context["current_user"]
        check_company_access(db, current_user, "Vehicle", input.vehicle_id)

        record = await vehicle_repo.create_vehicle_insurance(
            db,
            vehicle_id=input.vehicle_id,
            provider=input.provider,
            policy_number=input.policy_number,
            start_date=input.start_date.date() if hasattr(input.start_date, "date") else input.start_date,
            end_date=input.end_date.date() if hasattr(input.end_date, "date") else input.end_date,
            premium=input.premium,
            notes=input.notes,
        )
        await db.commit()
        await db.refresh(record)
        return types.VehicleInsurance.from_pydantic(record)

    @strawberry.mutation
    async def create_vehicle_inspection(self, input: VehicleInspectionInput, info: strawberry.Info) -> types.VehicleInspection:
        db = info.context["db"]
        current_user = info.context["current_user"]
        check_company_access(db, current_user, "Vehicle", input.vehicle_id)

        record = await vehicle_repo.create_vehicle_inspection(
            db,
            vehicle_id=input.vehicle_id,
            inspection_type=input.inspection_type,
            date=input.date.date() if hasattr(input.date, "date") else input.date,
            result=input.result,
            next_inspection_date=input.next_inspection_date.date() if input.next_inspection_date is not None and hasattr(input.next_inspection_date, "date") else input.next_inspection_date,
            cost=input.cost,
            notes=input.notes,
        )
        await db.commit()
        await db.refresh(record)
        return types.VehicleInspection.from_pydantic(record)

    @strawberry.mutation
    async def create_vehicle_driver(self, input: VehicleDriverInput, info: strawberry.Info) -> types.VehicleDriver:
        db = info.context["db"]
        current_user = info.context["current_user"]
        check_company_access(db, current_user, "Vehicle", input.vehicle_id)

        record = await vehicle_repo.create_vehicle_driver(
            db,
            vehicle_id=input.vehicle_id,
            user_id=input.user_id,
            start_date=input.start_date.date() if input.start_date is not None and hasattr(input.start_date, "date") else input.start_date,
            end_date=input.end_date.date() if input.end_date is not None and hasattr(input.end_date, "date") else input.end_date,
            is_primary=input.is_primary,
            notes=input.notes,
        )
        await db.commit()
        await db.refresh(record)
        return types.VehicleDriver.from_pydantic(record)

    @strawberry.mutation
    async def create_vehicle_trip(self, input: VehicleTripInput, info: strawberry.Info) -> types.VehicleTrip:
        db = info.context["db"]
        current_user = info.context["current_user"]
        check_company_access(db, current_user, "Vehicle", input.vehicle_id)

        record = await vehicle_repo.create_vehicle_trip(
            db,
            vehicle_id=input.vehicle_id,
            driver_id=input.user_id,
            start_time=input.start_date,
            end_time=input.end_date,
            start_address=input.start_location,
            end_address=input.end_location,
            distance_km=input.distance,
            purpose=input.trip_type,
            notes=input.notes,
        )
        await db.commit()
        await db.refresh(record)
        return types.VehicleTrip.from_pydantic(record)

    @strawberry.mutation
    async def delete_vehicle_mileage(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        success = await vehicle_repo.delete_vehicle_mileage(db, id)
        if not success:
            raise NotFoundException.record("Запис")
        await db.commit()
        return True

    @strawberry.mutation
    async def delete_vehicle_fuel(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        success = await vehicle_repo.delete_vehicle_fuel(db, id)
        if not success:
            raise NotFoundException.record("Запис")
        await db.commit()
        return True

    @strawberry.mutation
    async def delete_vehicle_repair(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        success = await vehicle_repo.delete_vehicle_repair(db, id)
        if not success:
            raise NotFoundException.record("Запис")
        await db.commit()
        return True

    @strawberry.mutation
    async def delete_vehicle_insurance(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        success = await vehicle_repo.delete_vehicle_insurance(db, id)
        if not success:
            raise NotFoundException.record("Запис")
        await db.commit()
        return True

    @strawberry.mutation
    async def delete_vehicle_inspection(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        success = await vehicle_repo.delete_vehicle_inspection(db, id)
        if not success:
            raise NotFoundException.record("Запис")
        await db.commit()
        return True

    @strawberry.mutation
    async def delete_vehicle_driver(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        success = await vehicle_repo.delete_vehicle_driver(db, id)
        if not success:
            raise NotFoundException.record("Запис")
        await db.commit()
        return True

    @strawberry.mutation
    async def delete_vehicle_trip(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        success = await vehicle_repo.delete_vehicle_trip(db, id)
        if not success:
            raise NotFoundException.record("Запис")
        await db.commit()
        return True

    @strawberry.mutation
    async def update_vehicle_mileage(self, id: int, input: VehicleMileageUpdateInput, info: strawberry.Info) -> types.VehicleMileage:
        db = info.context["db"]
        record = await vehicle_repo.update_vehicle_mileage(
            db, id,
            date=input.date.date() if input.date else None,
            mileage=input.mileage,
            notes=input.notes,
        )
        if not record:
            raise NotFoundException.record("Запис")
        await db.commit()
        await db.refresh(record)
        return types.VehicleMileage.from_pydantic(record)

    @strawberry.mutation
    async def update_vehicle_fuel(self, id: int, input: VehicleFuelUpdateInput, info: strawberry.Info) -> types.VehicleFuel:
        db = info.context["db"]
        record = await vehicle_repo.update_vehicle_fuel(
            db, id,
            date=input.date.date() if input.date else None,
            liters=input.liters,
            price=input.price,
            total=input.total,
            fuel_type=input.fuel_type,
            notes=input.notes,
        )
        if not record:
            raise NotFoundException.record("Запис")
        await db.commit()
        await db.refresh(record)
        return types.VehicleFuel.from_pydantic(record)

    @strawberry.mutation
    async def update_vehicle_repair(self, id: int, input: VehicleRepairUpdateInput, info: strawberry.Info) -> types.VehicleRepair:
        db = info.context["db"]
        record = await vehicle_repo.update_vehicle_repair(
            db, id,
            date=input.date.date() if input.date else None,
            description=input.description,
            cost=input.cost,
            repair_type=input.repair_type,
            notes=input.notes,
        )
        if not record:
            raise NotFoundException.record("Запис")
        await db.commit()
        await db.refresh(record)
        return types.VehicleRepair.from_pydantic(record)

    @strawberry.mutation
    async def update_vehicle_insurance(self, id: int, input: VehicleInsuranceUpdateInput, info: strawberry.Info) -> types.VehicleInsurance:
        db = info.context["db"]
        record = await vehicle_repo.update_vehicle_insurance(
            db, id,
            provider=input.provider,
            policy_number=input.policy_number,
            start_date=input.start_date.date() if input.start_date else None,
            end_date=input.end_date.date() if input.end_date else None,
            premium=input.premium,
            insurance_type=input.insurance_type,
            notes=input.notes,
        )
        if not record:
            raise NotFoundException.record("Запис")
        await db.commit()
        await db.refresh(record)
        return types.VehicleInsurance.from_pydantic(record)

    @strawberry.mutation
    async def update_vehicle_inspection(self, id: int, input: VehicleInspectionUpdateInput, info: strawberry.Info) -> types.VehicleInspection:
        db = info.context["db"]
        record = await vehicle_repo.update_vehicle_inspection(
            db, id,
            date=input.date.date() if input.date else None,
            next_date=input.next_date.date() if input.next_date else None,
            cost=input.cost,
            result=input.result,
            protocol_number=input.protocol_number,
            notes=input.notes,
        )
        if not record:
            raise NotFoundException.record("Запис")
        await db.commit()
        await db.refresh(record)
        return types.VehicleInspection.from_pydantic(record)

    @strawberry.mutation
    async def update_vehicle_driver(self, id: int, input: VehicleDriverUpdateInput, info: strawberry.Info) -> types.VehicleDriver:
        db = info.context["db"]
        record = await vehicle_repo.update_vehicle_driver(
            db, id,
            license_number=input.license_number,
            license_expiry=input.license_expiry.date() if input.license_expiry else None,
            phone=input.phone,
            category=input.category,
            is_primary=input.is_primary,
            notes=input.notes,
        )
        if not record:
            raise NotFoundException.record("Запис")
        await db.commit()
        await db.refresh(record)
        return types.VehicleDriver.from_pydantic(record)

    @strawberry.mutation
    async def update_vehicle_trip(self, id: int, input: VehicleTripUpdateInput, info: strawberry.Info) -> types.VehicleTrip:
        db = info.context["db"]
        record = await vehicle_repo.update_vehicle_trip(
            db, id,
            start_time=input.start_date,
            end_time=input.end_date,
            start_address=input.start_location,
            end_address=input.end_location,
            distance_km=input.distance,
            purpose=input.trip_type,
            notes=input.notes,
        )
        if not record:
            raise NotFoundException.record("Запис")
        await db.commit()
        await db.refresh(record)
        return types.VehicleTrip.from_pydantic(record)


