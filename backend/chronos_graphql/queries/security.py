import strawberry
from sqlalchemy import select

from backend.chronos_graphql import types


@strawberry.type
class SecurityQueries:

    @strawberry.field
    async def emergency_events(self, info: strawberry.Info, is_active: bool | None = None) -> list[types.EmergencyEvent]:
        db = info.context["db"]
        from backend.database import models
        user = info.context["current_user"]
        if not user:
            from backend.exceptions import AuthenticationException
            raise AuthenticationException()

        stmt = select(models.EmergencyEvent).order_by(models.EmergencyEvent.triggered_at.desc())
        if is_active is not None:
            stmt = stmt.where(models.EmergencyEvent.is_active == is_active)
        result = await db.execute(stmt)
        return [types.EmergencyEvent.from_pydantic(e) for e in result.scalars().all()]
