import strawberry
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend import schemas
from backend.exceptions import AuthenticationException
from backend.chronos_graphql import types

authenticate_msg = "Трябва да се автентикирате"


@strawberry.type
class FloorPlanQuery:

    @strawberry.field
    async def floor_plans(self, info: strawberry.Info) -> list[types.FloorPlan]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import FloorPlan as DbFloorPlan

        stmt = select(DbFloorPlan)
        if current_user.role.name != "super_admin":
            stmt = stmt.where(DbFloorPlan.company_id == current_user.company_id)
        stmt = stmt.order_by(DbFloorPlan.name)

        res = await db.execute(stmt)
        return [types.FloorPlan.from_pydantic(schemas.FloorPlan.model_validate(fp)) for fp in res.scalars().all()]

    @strawberry.field
    async def floor_plan(self, id: int, info: strawberry.Info) -> types.FloorPlan | None:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import FloorPlan as DbFloorPlan

        fp = await db.get(DbFloorPlan, id)
        if not fp:
            return None
        if current_user.role.name != "super_admin" and fp.company_id != current_user.company_id:
            return None
        return types.FloorPlan.from_pydantic(schemas.FloorPlan.model_validate(fp))

    @strawberry.field
    async def floor_plan_doors(
        self, floor_plan_id: int, info: strawberry.Info
    ) -> list[types.FloorPlanDoor]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import FloorPlanDoor as DbFloorPlanDoor

        stmt = (
            select(DbFloorPlanDoor)
            .where(DbFloorPlanDoor.floor_plan_id == floor_plan_id)
            .order_by(DbFloorPlanDoor.id)
        )
        res = await db.execute(stmt)
        return [
            types.FloorPlanDoor.from_pydantic(schemas.FloorPlanDoor.model_validate(d))
            for d in res.scalars().all()
        ]
