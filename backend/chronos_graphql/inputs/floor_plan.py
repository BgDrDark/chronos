import strawberry


@strawberry.input
class FloorPlanInput:
    name: str
    image_path: str | None = None
    svg_content: str | None = None
    background_image: str | None = None
    width: int | None = 1000
    height: int | None = 800
    is_active: bool | None = True
    company_id: int


@strawberry.input
class UpdateFloorPlanInput:
    id: int
    name: str | None = None
    image_path: str | None = None
    svg_content: str | None = None
    background_image: str | None = None
    width: int | None = None
    height: int | None = None
    is_active: bool | None = None


@strawberry.input
class FloorPlanDoorInput:
    floor_plan_id: int
    door_id: int
    x: float
    y: float
    width: float | None = 20
    height: float | None = 5
    rotation: float | None = 0
    label: str | None = None


@strawberry.input
class UpdateFloorPlanDoorInput:
    id: int
    x: float | None = None
    y: float | None = None
    width: float | None = None
    height: float | None = None
    rotation: float | None = None
    label: str | None = None
