import strawberry


@strawberry.input
class EmergencyTriggerInput:
    event_type: str
    scope: str = "all"
    gateway_id: int | None = None
    zone_id: int | None = None
    notes: str | None = None
