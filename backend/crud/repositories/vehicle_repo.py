from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.database.models import Vehicle, VehicleMileage, VehicleFuel, VehicleRepair, VehicleInsurance, VehicleInspection, VehicleDriver, VehicleTrip
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
    
    async def update_vehicle(self, db: AsyncSession, vehicle_id: int, **kwargs) -> Optional[Vehicle]:
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
    
    async def update_vehicle_mileage(self, db: AsyncSession, id: int, **kwargs) -> Optional[VehicleMileage]:
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
    
    async def update_vehicle_fuel(self, db: AsyncSession, id: int, **kwargs) -> Optional[VehicleFuel]:
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
    
    async def update_vehicle_repair(self, db: AsyncSession, id: int, **kwargs) -> Optional[VehicleRepair]:
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
    
    async def update_vehicle_insurance(self, db: AsyncSession, id: int, **kwargs) -> Optional[VehicleInsurance]:
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
    
    async def update_vehicle_inspection(self, db: AsyncSession, id: int, **kwargs) -> Optional[VehicleInspection]:
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
    
    async def update_vehicle_driver(self, db: AsyncSession, id: int, **kwargs) -> Optional[VehicleDriver]:
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
    
    async def update_vehicle_trip(self, db: AsyncSession, id: int, **kwargs) -> Optional[VehicleTrip]:
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


vehicle_repo = VehicleRepository()
