import strawberry


@strawberry.input
class AccessLevelInput:
    name: str
    description: str | None = None
    is_active: bool = True


@strawberry.input
class AccessLevelUpdateInput:
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


@strawberry.input
class AccessScheduleInput:
    name: str
    timezone: str = "Europe/Sofia"
    config: strawberry.scalars.JSON = strawberry.field(default_factory=dict)
    holiday_override_auto: bool = True
    is_active: bool = True


@strawberry.input
class AccessScheduleUpdateInput:
    name: str | None = None
    timezone: str | None = None
    config: strawberry.scalars.JSON | None = None
    holiday_override_auto: bool | None = None
    is_active: bool | None = None


@strawberry.input
class AssignLevelToZoneInput:
    access_level_id: int
    zone_id: int
    schedule_id: int | None = None
    out_of_hours_behavior: str = "deny"
    priority: int = 0


@strawberry.input
class AssignAccessLevelToUserInput:
    user_id: int
    access_level_id: int | None = None
