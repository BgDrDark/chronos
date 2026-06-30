
import strawberry
from sqlalchemy import select

from backend.database.models import VehicleCostCenter
from backend.exceptions import (
    AuthenticationException,
    NotFoundException,
    PermissionDeniedException,
)
from backend.chronos_graphql import types

authenticate_msg = "Трябва да се автентикирате"


@strawberry.type
class CostCenterQuery:
    @strawberry.field
    async def cost_centers(self, info: strawberry.Info, company_id: int | None = None) -> list[types.VehicleCostCenter]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        stmt = select(VehicleCostCenter)

        if current_user.role.name != "super_admin":
            stmt = stmt.where(VehicleCostCenter.company_id == current_user.company_id)
        elif company_id:
            stmt = stmt.where(VehicleCostCenter.company_id == company_id)

        stmt = stmt.where(VehicleCostCenter.is_active)

        res = await db.execute(stmt)
        return [types.VehicleCostCenter.from_pydantic(c) for c in res.scalars().all()]

    @strawberry.field
    async def cost_center(self, id: int, info: strawberry.Info) -> types.VehicleCostCenter | None:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        result = await db.get(VehicleCostCenter, id)

        if not result:
            raise NotFoundException.record("CostCenter")

        if current_user.role.name != "super_admin" and result.company_id != current_user.company_id:
            raise PermissionDeniedException.for_action("view")

        return types.VehicleCostCenter.from_pydantic(result)
