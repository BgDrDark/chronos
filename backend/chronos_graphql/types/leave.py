from typing import TYPE_CHECKING, Annotated

import strawberry
from strawberry.experimental import pydantic as sp

from backend import schemas

if TYPE_CHECKING:
    from backend.chronos_graphql.types.user import User


@sp.type(schemas.LeaveRequest)
class LeaveRequest:
    id: strawberry.auto
    user_id: strawberry.auto
    start_date: strawberry.auto
    end_date: strawberry.auto
    leave_type: strawberry.auto
    reason: strawberry.auto
    status: strawberry.auto
    created_at: strawberry.auto
    admin_comment: strawberry.auto
    employer_top_up: strawberry.auto

    @strawberry.field
    async def user(self, info: strawberry.Info) -> Annotated["User", strawberry.lazy("backend.chronos_graphql.types.user")] | None:
        if not self.user_id: return None
        return await info.context["dataloaders"]["user_by_id"].load(self.user_id)


@sp.type(schemas.LeaveBalance)
class LeaveBalance:
    id: strawberry.auto
    user_id: strawberry.auto
    year: strawberry.auto
    total_days: strawberry.auto
    used_days: strawberry.auto
