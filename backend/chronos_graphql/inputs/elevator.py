import strawberry


@strawberry.input
class ElevatorGroupInput:
    name: str
    gateway_id: int
    terminal_id: str
    controller_type: str = "sr201"


@strawberry.input
class ElevatorGroupUpdateInput:
    name: str | None = None
    terminal_id: str | None = None
    controller_type: str | None = None
    is_active: bool | None = None


@strawberry.input
class ElevatorFloorInput:
    elevator_group_id: int
    floor_number: int
    name: str | None = None
    zone_id: int | None = None
    relay_device_id: str
    relay_number: int
    order: int = 0


@strawberry.input
class ElevatorFloorUpdateInput:
    floor_number: int | None = None
    name: str | None = None
    zone_id: int | None = None
    relay_device_id: str | None = None
    relay_number: int | None = None
    order: int | None = None
    is_active: bool | None = None
