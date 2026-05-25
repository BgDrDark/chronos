from datetime import date, datetime, timedelta

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import (
    Vehicle,
    VehicleCostCenter,
    VehicleDocument,
    VehicleDriver,
    VehicleExpense,
    VehicleFuel,
    VehicleFuelCard,
    VehicleInspection,
    VehicleInsurance,
    VehicleMileage,
    VehiclePreTripInspection,
    VehicleRepair,
    VehicleSchedule,
    VehicleToll,
    VehicleTrip,
    VehicleVignette,
)

from .base import BaseRepository


class VehicleRepository(BaseRepository):
    """Repository за превозни средства"""

    model = Vehicle

    async def create_vehicle(self, db: AsyncSession, **kwargs) -> Vehicle:
        """Създава превозно средство"""
        vehicle = Vehicle(**kwargs)
        db.add(vehicle)
        await db.flush()
        await db.refresh(vehicle)
        return vehicle

    async def update_vehicle(self, db: AsyncSession, vehicle_id: int, **kwargs) -> Vehicle | None:
        """Обновява превозно средство"""
        vehicle = await db.get(Vehicle, vehicle_id)
        if vehicle:
            for key, value in kwargs.items():
                if value is not None:
                    setattr(vehicle, key, value)
            await db.flush()
            await db.refresh(vehicle)
        return vehicle

    async def delete_vehicle(self, db: AsyncSession, vehicle_id: int) -> bool:
        """Изтрива превозно средство"""
        vehicle = await db.get(Vehicle, vehicle_id)
        if vehicle:
            await db.delete(vehicle)
            await db.flush()
            return True
        return False

    async def create_vehicle_mileage(self, db: AsyncSession, **kwargs) -> VehicleMileage:
        """Създава запис за километри"""
        record = VehicleMileage(**kwargs)
        db.add(record)
        await db.flush()
        await db.refresh(record)
        return record

    async def update_vehicle_mileage(self, db: AsyncSession, id: int, **kwargs) -> VehicleMileage | None:
        """Обновява запис за километри"""
        record = await db.get(VehicleMileage, id)
        if record:
            for key, value in kwargs.items():
                if value is not None:
                    setattr(record, key, value)
            await db.flush()
            await db.refresh(record)
        return record

    async def delete_vehicle_mileage(self, db: AsyncSession, id: int) -> bool:
        """Изтрива запис за километри"""
        record = await db.get(VehicleMileage, id)
        if record:
            await db.delete(record)
            await db.flush()
            return True
        return False

    async def create_vehicle_fuel(self, db: AsyncSession, **kwargs) -> VehicleFuel:
        """Създава запис за гориво"""
        record = VehicleFuel(**kwargs)
        db.add(record)
        await db.flush()
        await db.refresh(record)
        return record

    async def update_vehicle_fuel(self, db: AsyncSession, id: int, **kwargs) -> VehicleFuel | None:
        """Обновява запис за гориво"""
        record = await db.get(VehicleFuel, id)
        if record:
            for key, value in kwargs.items():
                if value is not None:
                    setattr(record, key, value)
            await db.flush()
            await db.refresh(record)
        return record

    async def delete_vehicle_fuel(self, db: AsyncSession, id: int) -> bool:
        """Изтрива запис за гориво"""
        record = await db.get(VehicleFuel, id)
        if record:
            await db.delete(record)
            await db.flush()
            return True
        return False

    async def create_vehicle_repair(self, db: AsyncSession, **kwargs) -> VehicleRepair:
        """Създава запис за ремонт"""
        record = VehicleRepair(**kwargs)
        db.add(record)
        await db.flush()
        await db.refresh(record)
        return record

    async def update_vehicle_repair(self, db: AsyncSession, id: int, **kwargs) -> VehicleRepair | None:
        """Обновява запис за ремонт"""
        record = await db.get(VehicleRepair, id)
        if record:
            for key, value in kwargs.items():
                if value is not None:
                    setattr(record, key, value)
            await db.flush()
            await db.refresh(record)
        return record

    async def delete_vehicle_repair(self, db: AsyncSession, id: int) -> bool:
        """Изтрива запис за ремонт"""
        record = await db.get(VehicleRepair, id)
        if record:
            await db.delete(record)
            await db.flush()
            return True
        return False

    async def create_vehicle_insurance(self, db: AsyncSession, **kwargs) -> VehicleInsurance:
        """Създава запис за застраховка"""
        record = VehicleInsurance(**kwargs)
        db.add(record)
        await db.flush()
        await db.refresh(record)
        return record

    async def update_vehicle_insurance(self, db: AsyncSession, id: int, **kwargs) -> VehicleInsurance | None:
        """Обновява запис за застраховка"""
        record = await db.get(VehicleInsurance, id)
        if record:
            for key, value in kwargs.items():
                if value is not None:
                    setattr(record, key, value)
            await db.flush()
            await db.refresh(record)
        return record

    async def delete_vehicle_insurance(self, db: AsyncSession, id: int) -> bool:
        """Изтрива запис за застраховка"""
        record = await db.get(VehicleInsurance, id)
        if record:
            await db.delete(record)
            await db.flush()
            return True
        return False

    async def create_vehicle_inspection(self, db: AsyncSession, **kwargs) -> VehicleInspection:
        """Създава запис за преглед"""
        record = VehicleInspection(**kwargs)
        db.add(record)
        await db.flush()
        await db.refresh(record)
        return record

    async def update_vehicle_inspection(self, db: AsyncSession, id: int, **kwargs) -> VehicleInspection | None:
        """Обновява запис за преглед"""
        record = await db.get(VehicleInspection, id)
        if record:
            for key, value in kwargs.items():
                if value is not None:
                    setattr(record, key, value)
            await db.flush()
            await db.refresh(record)
        return record

    async def delete_vehicle_inspection(self, db: AsyncSession, id: int) -> bool:
        """Изтрива запис за преглед"""
        record = await db.get(VehicleInspection, id)
        if record:
            await db.delete(record)
            await db.flush()
            return True
        return False

    async def create_vehicle_driver(self, db: AsyncSession, **kwargs) -> VehicleDriver:
        """Създава запис за шофьор"""
        record = VehicleDriver(**kwargs)
        db.add(record)
        await db.flush()
        await db.refresh(record)
        return record

    async def update_vehicle_driver(self, db: AsyncSession, id: int, **kwargs) -> VehicleDriver | None:
        """Обновява запис за шофьор"""
        record = await db.get(VehicleDriver, id)
        if record:
            for key, value in kwargs.items():
                if value is not None:
                    setattr(record, key, value)
            await db.flush()
            await db.refresh(record)
        return record

    async def delete_vehicle_driver(self, db: AsyncSession, id: int) -> bool:
        """Изтрива запис за шофьор"""
        record = await db.get(VehicleDriver, id)
        if record:
            await db.delete(record)
            await db.flush()
            return True
        return False

    async def create_vehicle_trip(self, db: AsyncSession, **kwargs) -> VehicleTrip:
        """Създава запис за пътуване"""
        record = VehicleTrip(**kwargs)
        db.add(record)
        await db.flush()
        await db.refresh(record)
        return record

    async def update_vehicle_trip(self, db: AsyncSession, id: int, **kwargs) -> VehicleTrip | None:
        """Обновява запис за пътуване"""
        record = await db.get(VehicleTrip, id)
        if record:
            for key, value in kwargs.items():
                if value is not None:
                    setattr(record, key, value)
            await db.flush()
            await db.refresh(record)
        return record

    async def delete_vehicle_trip(self, db: AsyncSession, id: int) -> bool:
        """Изтрива запис за пътуване"""
        record = await db.get(VehicleTrip, id)
        if record:
            await db.delete(record)
            await db.flush()
            return True
        return False

    # ─── VehicleDocument methods ────────────────────────────────────────

    async def create_vehicle_document(self, db: AsyncSession, **kwargs) -> VehicleDocument:
        """Създава документ на автомобил"""
        instance = VehicleDocument(**kwargs)
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
        return instance

    async def update_vehicle_document(self, db: AsyncSession, id: int, **kwargs) -> VehicleDocument | None:
        """Обновява документ на автомобил"""
        instance = await db.get(VehicleDocument, id)
        if instance:
            for key, value in kwargs.items():
                if value is not None:
                    setattr(instance, key, value)
            await db.flush()
            await db.refresh(instance)
        return instance

    async def delete_vehicle_document(self, db: AsyncSession, id: int) -> bool:
        """Изтрива документ на автомобил"""
        instance = await db.get(VehicleDocument, id)
        if instance:
            await db.delete(instance)
            await db.flush()
            return True
        return False

    async def get_vehicle_documents(self, db: AsyncSession, vehicle_id: int) -> list[VehicleDocument]:
        """Връща всички документи за автомобил"""
        result = await db.execute(
            select(VehicleDocument).where(VehicleDocument.vehicle_id == vehicle_id),
        )
        return list(result.scalars().all())

    async def get_vehicle_document_by_id(self, db: AsyncSession, id: int) -> VehicleDocument | None:
        """Връща документ по ID"""
        result = await db.execute(
            select(VehicleDocument).where(VehicleDocument.id == id),
        )
        return result.scalar_one_or_none()

    # ─── VehicleFuelCard methods ────────────────────────────────────────

    async def create_vehicle_fuel_card(self, db: AsyncSession, **kwargs) -> VehicleFuelCard:
        """Създава горивна карта"""
        instance = VehicleFuelCard(**kwargs)
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
        return instance

    async def update_vehicle_fuel_card(self, db: AsyncSession, id: int, **kwargs) -> VehicleFuelCard | None:
        """Обновява горивна карта"""
        instance = await db.get(VehicleFuelCard, id)
        if instance:
            for key, value in kwargs.items():
                if value is not None:
                    setattr(instance, key, value)
            await db.flush()
            await db.refresh(instance)
        return instance

    async def delete_vehicle_fuel_card(self, db: AsyncSession, id: int) -> bool:
        """Изтрива горивна карта"""
        instance = await db.get(VehicleFuelCard, id)
        if instance:
            await db.delete(instance)
            await db.flush()
            return True
        return False

    async def get_vehicle_fuel_cards(self, db: AsyncSession, vehicle_id: int) -> list[VehicleFuelCard]:
        """Връща всички горивни карти за автомобил"""
        result = await db.execute(
            select(VehicleFuelCard).where(VehicleFuelCard.vehicle_id == vehicle_id),
        )
        return list(result.scalars().all())

    # ─── VehicleVignette methods ────────────────────────────────────────

    async def create_vehicle_vignette(self, db: AsyncSession, **kwargs) -> VehicleVignette:
        """Създава е-винетка"""
        instance = VehicleVignette(**kwargs)
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
        return instance

    async def update_vehicle_vignette(self, db: AsyncSession, id: int, **kwargs) -> VehicleVignette | None:
        """Обновява е-винетка"""
        instance = await db.get(VehicleVignette, id)
        if instance:
            for key, value in kwargs.items():
                if value is not None:
                    setattr(instance, key, value)
            await db.flush()
            await db.refresh(instance)
        return instance

    async def delete_vehicle_vignette(self, db: AsyncSession, id: int) -> bool:
        """Изтрива е-винетка"""
        instance = await db.get(VehicleVignette, id)
        if instance:
            await db.delete(instance)
            await db.flush()
            return True
        return False

    async def get_vehicle_vignettes(self, db: AsyncSession, vehicle_id: int) -> list[VehicleVignette]:
        """Връща всички е-винетки за автомобил"""
        result = await db.execute(
            select(VehicleVignette).where(VehicleVignette.vehicle_id == vehicle_id),
        )
        return list(result.scalars().all())

    async def get_expiring_vignettes(self, db: AsyncSession, company_id: int, days: int) -> list[VehicleVignette]:
        """Връща е-винетки, изтичащи в рамките на N дни"""
        today = date.today()
        expire_end = today + timedelta(days=days)
        result = await db.execute(
            select(VehicleVignette)
            .join(Vehicle, VehicleVignette.vehicle_id == Vehicle.id)
            .where(
                and_(
                    Vehicle.company_id == company_id,
                    VehicleVignette.valid_until >= today,
                    VehicleVignette.valid_until <= expire_end,
                ),
            ),
        )
        return list(result.scalars().all())

    # ─── VehicleToll methods ────────────────────────────────────────────

    async def create_vehicle_toll(self, db: AsyncSession, **kwargs) -> VehicleToll:
        """Създава тол такса"""
        instance = VehicleToll(**kwargs)
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
        return instance

    async def get_vehicle_tolls(
        self,
        db: AsyncSession,
        vehicle_id: int,
        start_date: datetime = None,
        end_date: datetime = None,
    ) -> list[VehicleToll]:
        """Връща тол такси за автомобил с опционален период"""
        query = select(VehicleToll).where(VehicleToll.vehicle_id == vehicle_id)
        if start_date:
            query = query.where(VehicleToll.toll_date >= start_date)
        if end_date:
            query = query.where(VehicleToll.toll_date <= end_date)
        result = await db.execute(query)
        return list(result.scalars().all())

    # ─── VehicleSchedule methods ────────────────────────────────────────

    async def create_vehicle_schedule(self, db: AsyncSession, **kwargs) -> VehicleSchedule:
        """Създава график за поддръжка"""
        instance = VehicleSchedule(**kwargs)
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
        return instance

    async def update_vehicle_schedule(self, db: AsyncSession, id: int, **kwargs) -> VehicleSchedule | None:
        """Обновява график за поддръжка"""
        instance = await db.get(VehicleSchedule, id)
        if instance:
            for key, value in kwargs.items():
                if value is not None:
                    setattr(instance, key, value)
            await db.flush()
            await db.refresh(instance)
        return instance

    async def delete_vehicle_schedule(self, db: AsyncSession, id: int) -> bool:
        """Изтрива график за поддръжка"""
        instance = await db.get(VehicleSchedule, id)
        if instance:
            await db.delete(instance)
            await db.flush()
            return True
        return False

    async def get_vehicle_schedules(
        self,
        db: AsyncSession,
        vehicle_id: int,
        date_from: date = None,
        date_to: date = None,
    ) -> list[VehicleSchedule]:
        """Връща графици за поддръжка за автомобил"""
        query = select(VehicleSchedule).where(VehicleSchedule.vehicle_id == vehicle_id)
        if date_from:
            query = query.where(VehicleSchedule.next_service_date >= date_from)
        if date_to:
            query = query.where(VehicleSchedule.next_service_date <= date_to)
        result = await db.execute(query)
        return list(result.scalars().all())

    # ─── VehiclePreTripInspection methods ───────────────────────────────

    async def create_pre_trip_inspection(self, db: AsyncSession, **kwargs) -> VehiclePreTripInspection:
        """Създава инспекция преди път"""
        instance = VehiclePreTripInspection(**kwargs)
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
        return instance

    async def update_pre_trip_inspection(self, db: AsyncSession, id: int, **kwargs) -> VehiclePreTripInspection | None:
        """Обновява инспекция преди път"""
        instance = await db.get(VehiclePreTripInspection, id)
        if instance:
            for key, value in kwargs.items():
                if value is not None:
                    setattr(instance, key, value)
            await db.flush()
            await db.refresh(instance)
        return instance

    async def get_pre_trip_inspections(
        self,
        db: AsyncSession,
        vehicle_id: int,
        date_from: datetime = None,
        date_to: datetime = None,
    ) -> list[VehiclePreTripInspection]:
        """Връща инспекции преди път за автомобил"""
        query = select(VehiclePreTripInspection).where(VehiclePreTripInspection.vehicle_id == vehicle_id)
        if date_from:
            query = query.where(VehiclePreTripInspection.inspection_date >= date_from)
        if date_to:
            query = query.where(VehiclePreTripInspection.inspection_date <= date_to)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_pre_trip_inspection_by_id(self, db: AsyncSession, id: int) -> VehiclePreTripInspection | None:
        """Връща инспекция преди път по ID"""
        result = await db.execute(
            select(VehiclePreTripInspection).where(VehiclePreTripInspection.id == id),
        )
        return result.scalar_one_or_none()

    # ─── VehicleCostCenter methods ──────────────────────────────────────

    async def create_vehicle_cost_center(self, db: AsyncSession, **kwargs) -> VehicleCostCenter:
        """Създава разходен център"""
        instance = VehicleCostCenter(**kwargs)
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
        return instance

    async def update_vehicle_cost_center(self, db: AsyncSession, id: int, **kwargs) -> VehicleCostCenter | None:
        """Обновява разходен център"""
        instance = await db.get(VehicleCostCenter, id)
        if instance:
            for key, value in kwargs.items():
                if value is not None:
                    setattr(instance, key, value)
            await db.flush()
            await db.refresh(instance)
        return instance

    async def delete_vehicle_cost_center(self, db: AsyncSession, id: int) -> bool:
        """Изтрива разходен център"""
        instance = await db.get(VehicleCostCenter, id)
        if instance:
            await db.delete(instance)
            await db.flush()
            return True
        return False

    async def get_vehicle_cost_centers(self, db: AsyncSession, company_id: int) -> list[VehicleCostCenter]:
        """Връща разходни центрове за компания"""
        result = await db.execute(
            select(VehicleCostCenter).where(VehicleCostCenter.company_id == company_id),
        )
        return list(result.scalars().all())

    # ─── VehicleExpense methods ─────────────────────────────────────────

    async def create_vehicle_expense(self, db: AsyncSession, **kwargs) -> VehicleExpense:
        """Създава разход за автомобил"""
        instance = VehicleExpense(**kwargs)
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
        return instance

    async def update_vehicle_expense(self, db: AsyncSession, id: int, **kwargs) -> VehicleExpense | None:
        """Обновява разход за автомобил"""
        instance = await db.get(VehicleExpense, id)
        if instance:
            for key, value in kwargs.items():
                if value is not None:
                    setattr(instance, key, value)
            await db.flush()
            await db.refresh(instance)
        return instance

    async def delete_vehicle_expense(self, db: AsyncSession, id: int) -> bool:
        """Изтрива разход за автомобил"""
        instance = await db.get(VehicleExpense, id)
        if instance:
            await db.delete(instance)
            await db.flush()
            return True
        return False

    async def get_vehicle_expenses(
        self,
        db: AsyncSession,
        vehicle_id: int,
        start_date: date = None,
        end_date: date = None,
    ) -> list[VehicleExpense]:
        """Връща разходи за автомобил с опционален период"""
        query = select(VehicleExpense).where(VehicleExpense.vehicle_id == vehicle_id)
        if start_date:
            query = query.where(VehicleExpense.expense_date >= start_date)
        if end_date:
            query = query.where(VehicleExpense.expense_date <= end_date)
        result = await db.execute(query)
        return list(result.scalars().all())


vehicle_repo = VehicleRepository()
