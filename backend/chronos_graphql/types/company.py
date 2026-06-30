from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

import strawberry
from sqlalchemy import select
from strawberry.experimental import pydantic as sp

from backend import schemas

if TYPE_CHECKING:
    from backend.chronos_graphql.types.accounting import Account
    from backend.chronos_graphql.types.payroll import Payroll
    from backend.chronos_graphql.types.user import User



@sp.type(schemas.Role)
class Role:
    id: strawberry.auto
    name: strawberry.auto
    description: strawberry.auto


@sp.type(schemas.Company)
class Company:
    id: strawberry.auto
    name: strawberry.auto
    eik: strawberry.auto
    bulstat: strawberry.auto
    vat_number: strawberry.auto
    address: strawberry.auto
    mol_name: strawberry.auto
    default_sales_account_id: strawberry.auto
    default_expense_account_id: strawberry.auto
    default_vat_account_id: strawberry.auto
    default_customer_account_id: strawberry.auto
    default_supplier_account_id: strawberry.auto
    default_cash_account_id: strawberry.auto
    default_bank_account_id: strawberry.auto

    @strawberry.field
    async def default_sales_account(self, info: strawberry.Info) -> Annotated[Account, strawberry.lazy("backend.chronos_graphql.types.accounting")] | None:
        if not self.default_sales_account_id:
            return None
        result = await info.context["dataloaders"]["account_by_id"].load(self.default_sales_account_id)
        from backend.chronos_graphql.types.accounting import Account
        return Account.from_pydantic(result) if result else None

    @strawberry.field
    async def default_expense_account(self, info: strawberry.Info) -> Annotated[Account, strawberry.lazy("backend.chronos_graphql.types.accounting")] | None:
        if not self.default_expense_account_id:
            return None
        result = await info.context["dataloaders"]["account_by_id"].load(self.default_expense_account_id)
        from backend.chronos_graphql.types.accounting import Account
        return Account.from_pydantic(result) if result else None

    @strawberry.field
    async def default_vat_account(self, info: strawberry.Info) -> Annotated[Account, strawberry.lazy("backend.chronos_graphql.types.accounting")] | None:
        if not self.default_vat_account_id:
            return None
        result = await info.context["dataloaders"]["account_by_id"].load(self.default_vat_account_id)
        from backend.chronos_graphql.types.accounting import Account
        return Account.from_pydantic(result) if result else None

    @strawberry.field
    async def default_customer_account(self, info: strawberry.Info) -> Annotated[Account, strawberry.lazy("backend.chronos_graphql.types.accounting")] | None:
        if not self.default_customer_account_id:
            return None
        result = await info.context["dataloaders"]["account_by_id"].load(self.default_customer_account_id)
        from backend.chronos_graphql.types.accounting import Account
        return Account.from_pydantic(result) if result else None

    @strawberry.field
    async def default_supplier_account(self, info: strawberry.Info) -> Annotated[Account, strawberry.lazy("backend.chronos_graphql.types.accounting")] | None:
        if not self.default_supplier_account_id:
            return None
        result = await info.context["dataloaders"]["account_by_id"].load(self.default_supplier_account_id)
        from backend.chronos_graphql.types.accounting import Account
        return Account.from_pydantic(result) if result else None

    @strawberry.field
    async def default_cash_account(self, info: strawberry.Info) -> Annotated[Account, strawberry.lazy("backend.chronos_graphql.types.accounting")] | None:
        if not self.default_cash_account_id:
            return None
        result = await info.context["dataloaders"]["account_by_id"].load(self.default_cash_account_id)
        from backend.chronos_graphql.types.accounting import Account
        return Account.from_pydantic(result) if result else None

    @strawberry.field
    async def default_bank_account(self, info: strawberry.Info) -> Annotated[Account, strawberry.lazy("backend.chronos_graphql.types.accounting")] | None:
        if not self.default_bank_account_id:
            return None
        result = await info.context["dataloaders"]["account_by_id"].load(self.default_bank_account_id)
        from backend.chronos_graphql.types.accounting import Account
        return Account.from_pydantic(result) if result else None


@sp.type(schemas.Department)
class Department:
    id: strawberry.auto
    name: strawberry.auto
    company_id: strawberry.auto
    manager_id: strawberry.auto

    @strawberry.field
    async def company(self, info: strawberry.Info) -> Company | None:
        if not self.company_id: return None
        db = info.context["db"]
        from backend.database.models import Company as DbCompany
        res = await db.get(DbCompany, self.company_id)
        return Company.from_pydantic(res) if res else None

    @strawberry.field
    async def manager(self, info: strawberry.Info) -> Annotated[User, strawberry.lazy("backend.chronos_graphql.types.user")] | None:
        if not self.manager_id: return None
        return await info.context["dataloaders"]["user_by_id"].load(self.manager_id)


@sp.type(schemas.Position)
class Position:
    id: strawberry.auto
    title: strawberry.auto
    department_id: strawberry.auto

    @strawberry.field
    async def department(self, info: strawberry.Info) -> Department | None:
        if not self.department_id: return None
        db = info.context["db"]
        from backend.database.models import Department as DbDepartment
        res = await db.get(DbDepartment, self.department_id)
        return Department.from_pydantic(res) if res else None

    @strawberry.field
    async def payrolls(self, info: strawberry.Info) -> list[Annotated[Payroll, strawberry.lazy("backend.chronos_graphql.types.payroll")]]:
        db = info.context["db"]
        from backend.database.models import Payroll as DbPayroll
        result = await db.execute(
            select(DbPayroll).where(DbPayroll.position_id == self.id),
        )
        rows = result.scalars().all()
        return [Payroll.from_pydantic(r) for r in rows]
