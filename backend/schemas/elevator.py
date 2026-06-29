from datetime import datetime

from backend.schemas.base import CustomBaseModel


class ElevatorGroup(CustomBaseModel):
    id: int
    name: str
    gateway_id: int
    terminal_id: str
    controller_type: str = "sr201"
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ElevatorFloor(CustomBaseModel):
    id: int
    elevator_group_id: int
    floor_number: int
    name: str | None = None
    zone_id: int | None = None
    relay_device_id: str
    relay_number: int
    order: int = 0
    is_active: bool = True


class ElevatorGroupCreate(CustomBaseModel):
    name: str
    gateway_id: int
    terminal_id: str
    controller_type: str = "sr201"


class ElevatorGroupUpdate(CustomBaseModel):
    name: str | None = None
    terminal_id: str | None = None
    controller_type: str | None = None
    is_active: bool | None = None


class ElevatorFloorCreate(CustomBaseModel):
    elevator_group_id: int
    floor_number: int
    name: str | None = None
    zone_id: int | None = None
    relay_device_id: str
    relay_number: int
    order: int = 0


class ElevatorFloorUpdate(CustomBaseModel):
    floor_number: int | None = None
    name: str | None = None
    zone_id: int | None = None
    relay_device_id: str | None = None
    relay_number: int | None = None
    order: int | None = None
    is_active: bool | None = None
