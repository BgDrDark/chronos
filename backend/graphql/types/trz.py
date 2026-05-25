import enum
from typing import Optional

import strawberry
from strawberry.experimental import pydantic as sp

from backend import schemas
from backend.graphql.types import User


@strawberry.enum
class BusinessTripStatus(enum.StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"


@sp.type(schemas.NightWorkBonus)
class NightWorkBonus:
    id: strawberry.auto
    user_id: strawberry.auto
    period_id: strawberry.auto
    date: strawberry.auto
    hours: strawberry.auto
    hourly_rate: strawberry.auto
    amount: strawberry.auto
    is_paid: strawberry.auto
    notes: strawberry.auto
    created_at: strawberry.auto
    updated_at: strawberry.auto

    @strawberry.field
    async def user(self, info: strawberry.Info) -> "User":
        return await info.context["dataloaders"]["user_by_id"].load(self.user_id)


@sp.type(schemas.OvertimeWork)
class OvertimeWork:
    id: strawberry.auto
    user_id: strawberry.auto
    period_id: strawberry.auto
    date: strawberry.auto
    hours: strawberry.auto
    hourly_rate: strawberry.auto
    multiplier: strawberry.auto
    amount: strawberry.auto
    is_paid: strawberry.auto
    notes: strawberry.auto
    created_at: strawberry.auto
    updated_at: strawberry.auto

    @strawberry.field
    async def user(self, info: strawberry.Info) -> "User":
        return await info.context["dataloaders"]["user_by_id"].load(self.user_id)


@sp.type(schemas.BusinessTrip)
class BusinessTrip:
    id: strawberry.auto
    user_id: strawberry.auto
    period_id: strawberry.auto
    department_id: strawberry.auto
    destination: strawberry.auto
    start_date: strawberry.auto
    end_date: strawberry.auto
    daily_allowance: strawberry.auto
    accommodation: strawberry.auto
    transport: strawberry.auto
    other_expenses: strawberry.auto
    total_amount: strawberry.auto
    status: strawberry.auto
    approved_by_id: strawberry.auto
    approved_at: strawberry.auto
    approved_notes: strawberry.auto
    notes: strawberry.auto
    created_at: strawberry.auto
    updated_at: strawberry.auto

    @strawberry.field
    async def user(self, info: strawberry.Info) -> "User":
        return await info.context["dataloaders"]["user_by_id"].load(self.user_id)

    @strawberry.field
    async def approved_by(self, info: strawberry.Info) -> Optional["User"]:
        if self.approved_by_id:
            return await info.context["dataloaders"]["user_by_id"].load(self.approved_by_id)
        return None


@sp.type(schemas.WorkExperience)
class WorkExperience:
    id: strawberry.auto
    user_id: strawberry.auto
    company_id: strawberry.auto
    company_name: strawberry.auto
    position: strawberry.auto
    start_date: strawberry.auto
    end_date: strawberry.auto
    years: strawberry.auto
    months: strawberry.auto
    class_level: strawberry.auto
    is_current: strawberry.auto
    notes: strawberry.auto
    created_at: strawberry.auto
    updated_at: strawberry.auto

    @strawberry.field
    async def user(self, info: strawberry.Info) -> "User":
        return await info.context["dataloaders"]["user_by_id"].load(self.user_id)
