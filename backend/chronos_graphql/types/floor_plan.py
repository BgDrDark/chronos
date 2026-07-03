import strawberry
from strawberry.experimental import pydantic as sp

from backend import schemas


@sp.type(schemas.FloorPlan)
class FloorPlan:
    id: strawberry.auto
    company_id: strawberry.auto
    name: strawberry.auto
    image_path: strawberry.auto
    svg_content: strawberry.auto
    background_image: strawberry.auto
    width: strawberry.auto
    height: strawberry.auto
    is_active: strawberry.auto
    created_at: strawberry.auto
    updated_at: strawberry.auto


@sp.type(schemas.FloorPlanDoor)
class FloorPlanDoor:
    id: strawberry.auto
    floor_plan_id: strawberry.auto
    door_id: strawberry.auto
    x: strawberry.auto
    y: strawberry.auto
    width: strawberry.auto
    height: strawberry.auto
    rotation: strawberry.auto
    label: strawberry.auto
