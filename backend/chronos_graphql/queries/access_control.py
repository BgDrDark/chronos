
import strawberry
from sqlalchemy import select

from backend.exceptions import (
    AuthenticationException,
)
from backend.chronos_graphql import types

authenticate_msg = "Трябва да се автентикирате"


@strawberry.type
class AccessControlQuery:

    @strawberry.field
    async def access_zones(self, info: strawberry.Info) -> list[types.AccessZone]:
        db = info.context["db"]
        from backend.database import models
        user = info.context["current_user"]
        if not user: raise AuthenticationException

        stmt = select(models.AccessZone)
        if user.role.name != "super_admin":
            stmt = stmt.where(models.AccessZone.company_id == user.company_id)

        result = await db.execute(stmt)
        return [types.AccessZone.from_pydantic(z) for z in result.scalars().all()]

    @strawberry.field
    async def access_doors(self, info: strawberry.Info, gateway_id: int | None = None) -> list[types.AccessDoor]:
        db = info.context["db"]
        from backend.database import models
        user = info.context["current_user"]
        if not user: raise AuthenticationException()

        query = select(models.AccessDoor).join(models.AccessZone)
        if user.role.name != "super_admin":
            query = query.where(models.AccessZone.company_id == user.company_id)

        if gateway_id:
            query = query.where(models.AccessDoor.gateway_id == gateway_id)
        result = await db.execute(query)
        return [types.AccessDoor.from_pydantic(d) for d in result.scalars().all()]

    @strawberry.field
    async def access_codes(self, info: strawberry.Info, gateway_id: int | None = None) -> list[types.AccessCode]:
        db = info.context["db"]
        from backend.database import models
        user = info.context["current_user"]
        if not user: raise AuthenticationException()

        query = select(models.AccessCode)
        if user.role.name != "super_admin":
            from sqlalchemy import or_

            from backend.database.models import Gateway
            query = query.outerjoin(Gateway).where(
                or_(Gateway.company_id == user.company_id, models.AccessCode.gateway_id is None),
            )

        if gateway_id:
            query = query.where(models.AccessCode.gateway_id == gateway_id)
        result = await db.execute(query)
        return [types.AccessCode.from_pydantic(c) for c in result.scalars().all()]

    @strawberry.field
    async def access_logs(self, info: strawberry.Info, gateway_id: int | None = None, limit: int = 100) -> list[types.AccessLog]:
        db = info.context["db"]
        from backend.database import models
        user = info.context["current_user"]
        if not user: raise AuthenticationException()

        query = select(models.AccessLog).order_by(models.AccessLog.timestamp.desc()).limit(limit)
        if user.role.name != "super_admin":
            from backend.database.models import Gateway
            query = query.join(Gateway).where(Gateway.company_id == user.company_id)

        if gateway_id:
            query = query.where(models.AccessLog.gateway_id == gateway_id)
        result = await db.execute(query)
        return [types.AccessLog.from_pydantic(item) for item in result.scalars().all()]
