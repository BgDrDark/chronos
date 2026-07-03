import logging

import strawberry
from sqlalchemy import select

from backend import schemas
from backend.exceptions import (
    AuthenticationException,
    NotFoundException,
    ValidationException,
)
from backend.chronos_graphql import inputs, types
from backend.chronos_graphql.utils.permission_checker import (
    check_company_access,
    get_current_user,
)

logger = logging.getLogger(__name__)
authenticate_msg = "Трябва да се автентикирате"


@strawberry.type
class FloorPlanMutation:

    @strawberry.mutation
    async def create_floor_plan(
        self, input: inputs.FloorPlanInput, info: strawberry.Info
    ) -> types.FloorPlan:
        db = info.context["db"]
        current_user = get_current_user(info)

        from backend.database.models import FloorPlan as DbFloorPlan

        target_company_id = (
            input.company_id
            if current_user.role.name == "super_admin"
            else current_user.company_id
        )
        if not target_company_id:
            raise ValidationException(detail="company_id е задължителен")

        fp = DbFloorPlan(
            company_id=target_company_id,
            name=input.name,
            image_path=input.image_path,
            svg_content=input.svg_content,
            background_image=input.background_image,
            width=input.width or 1000,
            height=input.height or 800,
            is_active=input.is_active if input.is_active is not None else True,
        )
        db.add(fp)
        await db.commit()
        await db.refresh(fp)
        return types.FloorPlan.from_pydantic(schemas.FloorPlan.model_validate(fp))

    @strawberry.mutation
    async def update_floor_plan(
        self, input: inputs.UpdateFloorPlanInput, info: strawberry.Info
    ) -> types.FloorPlan:
        db = info.context["db"]
        current_user = get_current_user(info)

        from backend.database.models import FloorPlan as DbFloorPlan

        fp = await db.get(DbFloorPlan, input.id)
        if not fp:
            raise NotFoundException.resource("FloorPlan")
        check_company_access(db, current_user, "FloorPlan", input.id)

        if input.name is not None:
            fp.name = input.name
        if input.image_path is not None:
            fp.image_path = input.image_path
        if input.svg_content is not None:
            fp.svg_content = input.svg_content
        if input.background_image is not None:
            fp.background_image = input.background_image
        if input.width is not None:
            fp.width = input.width
        if input.height is not None:
            fp.height = input.height
        if input.is_active is not None:
            fp.is_active = input.is_active

        await db.commit()
        await db.refresh(fp)
        return types.FloorPlan.from_pydantic(schemas.FloorPlan.model_validate(fp))

    @strawberry.mutation
    async def delete_floor_plan(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        get_current_user(info)

        from backend.database.models import FloorPlan as DbFloorPlan

        fp = await db.get(DbFloorPlan, id)
        if not fp:
            raise NotFoundException.resource("FloorPlan")
        await check_company_access(db, info.context["current_user"], "FloorPlan", id)

        await db.delete(fp)
        await db.commit()
        return True

    @strawberry.mutation
    async def add_door_to_floor_plan(
        self, input: inputs.FloorPlanDoorInput, info: strawberry.Info
    ) -> types.FloorPlanDoor:
        db = info.context["db"]
        get_current_user(info)

        from backend.database.models import FloorPlanDoor as DbFloorPlanDoor

        door = DbFloorPlanDoor(
            floor_plan_id=input.floor_plan_id,
            door_id=input.door_id,
            x=input.x,
            y=input.y,
            width=input.width or 20,
            height=input.height or 5,
            rotation=input.rotation or 0,
            label=input.label,
        )
        db.add(door)
        await db.commit()
        await db.refresh(door)
        return types.FloorPlanDoor.from_pydantic(
            schemas.FloorPlanDoor.model_validate(door)
        )

    @strawberry.mutation
    async def update_door_on_floor_plan(
        self, input: inputs.UpdateFloorPlanDoorInput, info: strawberry.Info
    ) -> types.FloorPlanDoor:
        db = info.context["db"]
        get_current_user(info)

        from backend.database.models import FloorPlanDoor as DbFloorPlanDoor

        door = await db.get(DbFloorPlanDoor, input.id)
        if not door:
            raise NotFoundException.resource("FloorPlanDoor")

        if input.x is not None:
            door.x = input.x
        if input.y is not None:
            door.y = input.y
        if input.width is not None:
            door.width = input.width
        if input.height is not None:
            door.height = input.height
        if input.rotation is not None:
            door.rotation = input.rotation
        if input.label is not None:
            door.label = input.label

        await db.commit()
        await db.refresh(door)
        return types.FloorPlanDoor.from_pydantic(
            schemas.FloorPlanDoor.model_validate(door)
        )

    @strawberry.mutation
    async def remove_door_from_floor_plan(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        get_current_user(info)

        from backend.database.models import FloorPlanDoor as DbFloorPlanDoor

        door = await db.get(DbFloorPlanDoor, id)
        if not door:
            raise NotFoundException.resource("FloorPlanDoor")

        await db.delete(door)
        await db.commit()
        return True
