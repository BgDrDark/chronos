import strawberry
from sqlalchemy import select

from backend.database.models import Company, VehicleCostCenter
from backend.exceptions import (
    NotFoundException,
    ValidationException,
)
from backend.chronos_graphql import types
from backend.chronos_graphql.inputs.cost_center import CostCenterInput, UpdateCostCenterInput
from backend.chronos_graphql.utils.permission_checker import get_current_user


@strawberry.type
class CostCenterMutation:
    @strawberry.mutation
    async def create_cost_center(self, input: CostCenterInput, info: strawberry.Info) -> types.VehicleCostCenter:
        db = info.context["db"]
        current_user = get_current_user(info)

        target_company_id = input.company_id if current_user.role.name == "super_admin" else current_user.company_id
        if not target_company_id:
            raise ValidationException.required_field("company_id")

        stmt = select(Company).where(Company.id == target_company_id)
        res = await db.execute(stmt)
        if not res.scalar_one_or_none():
            raise NotFoundException.resource("Company", target_company_id)

        cost_center = VehicleCostCenter(
            name=input.name,
            department_id=input.department_id,
            is_active=input.is_active if input.is_active is not None else True,
            company_id=target_company_id,
        )
        db.add(cost_center)
        await db.commit()
        await db.refresh(cost_center)
        return types.VehicleCostCenter.from_pydantic(cost_center)

    @strawberry.mutation
    async def update_cost_center(self, input: UpdateCostCenterInput, info: strawberry.Info) -> types.VehicleCostCenter:
        db = info.context["db"]
        get_current_user(info)

        cost_center = await db.get(VehicleCostCenter, input.id)
        if not cost_center:
            raise NotFoundException.record("CostCenter")

        if input.name is not None:
            cost_center.name = input.name
        if input.department_id is not None:
            cost_center.department_id = input.department_id
        if input.is_active is not None:
            cost_center.is_active = input.is_active

        await db.commit()
        await db.refresh(cost_center)
        return types.VehicleCostCenter.from_pydantic(cost_center)

    @strawberry.mutation
    async def delete_cost_center(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        get_current_user(info)

        cost_center = await db.get(VehicleCostCenter, id)
        if not cost_center:
            raise NotFoundException.record("CostCenter")

        cost_center.is_active = False
        await db.commit()
        return True
