from datetime import datetime

from backend.schemas.base import CustomBaseModel


class FloorPlan(CustomBaseModel):
    id: int
    company_id: int
    name: str
    image_path: str | None = None
    svg_content: str | None = None
    background_image: str | None = None
    width: int = 1000
    height: int = 800
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None


class FloorPlanDoor(CustomBaseModel):
    id: int
    floor_plan_id: int
    door_id: int
    x: float
    y: float
    width: float = 20
    height: float = 5
    rotation: float = 0
    label: str | None = None
