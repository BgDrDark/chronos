
import strawberry


@strawberry.input
class AccessZoneInput:
    zone_id: str
    name: str
    level: int = 1
    depends_on: list[str] = strawberry.field(default_factory=list)
    required_hours_start: str = "00:00"
    required_hours_end: str = "23:59"
    anti_passback_enabled: bool = False
    anti_passback_type: str = "soft"
    anti_passback_timeout: int = 5
    description: str | None = None
    parent_zone_id: int | None = None
    inherit_permissions: bool = True
    required_auth_factors: list[int] = strawberry.field(default_factory=list)
    interlock_enabled: bool = False
    interlock_timeout: int = 30
    dual_auth_enabled: bool = False
    dual_auth_timeout: int = 30


@strawberry.input
class AccessDoorInput:
    door_id: str
    name: str
    zone_db_id: int
    gateway_id: int
    device_id: str
    relay_number: int = 1
    terminal_id: str | None = None
    description: str | None = None


@strawberry.input
class AccessCodeInput:
    code: str | None = None
    code_type: str = "one_time"
    zones: list[str] = strawberry.field(default_factory=list)
    uses_remaining: int = 1
    expires_hours: int | None = 24
    gateway_id: int | None = None
