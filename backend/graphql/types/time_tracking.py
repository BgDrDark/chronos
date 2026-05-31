
import strawberry
from strawberry.experimental import pydantic as sp

from backend import schemas
from backend.graphql.types import User


@sp.type(schemas.TimeLog)
class TimeLog:
    id: strawberry.auto
    start_time: strawberry.auto
    end_time: strawberry.auto
    is_manual: strawberry.auto
    break_duration_minutes: strawberry.auto
    type: strawberry.auto
    notes: strawberry.auto
    latitude: strawberry.auto
    longitude: strawberry.auto
    user_id: strawberry.auto

    @strawberry.field
    async def user(self, info: strawberry.Info) -> User | None:
        if not self.user_id:
            return None
        return await info.context["dataloaders"]["user_by_id"].load(self.user_id)
