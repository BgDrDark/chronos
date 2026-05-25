import logging
from typing import Optional

import strawberry

from backend import schemas
from backend.crud.repositories import company_repo, time_repo, settings_repo
from backend.exceptions import PermissionDeniedException, InvalidOperationException
from backend.graphql import types
from backend.graphql.inputs import (
    CompanyCreateInput,
    CompanyUpdateInput,
    DepartmentCreateInput,
    DepartmentUpdateInput,
    RoleCreateInput,
)

logger = logging.getLogger(__name__)


@strawberry.type
class CompanyMutation:
    @strawberry.mutation
    async def create_company(self, input: CompanyCreateInput, info: strawberry.Info) -> types.Company:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name != "super_admin":
            raise PermissionDeniedException.for_action("manage")

        company = await company_repo.create_company(
            db,
            name=input.name,
            eik=input.eik,
            bulstat=input.bulstat,
            vat_number=input.vat_number,
            address=input.address,
            mol_name=input.mol_name,
        )
        await db.commit()
        await db.refresh(company)
        return types.Company.from_instance(company)

    @strawberry.mutation
    async def update_company(self, input: CompanyUpdateInput, info: strawberry.Info) -> types.Company:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name != "super_admin":
            raise PermissionDeniedException.for_action("manage")

        company = await company_repo.update_company(
            db,
            company_id=input.id,
            name=input.name,
            eik=input.eik,
            bulstat=input.bulstat,
            vat_number=input.vat_number,
            address=input.address,
            mol_name=input.mol_name,
            default_sales_account_id=input.default_sales_account_id,
            default_expense_account_id=input.default_expense_account_id,
            default_vat_account_id=input.default_vat_account_id,
            default_customer_account_id=input.default_customer_account_id,
            default_supplier_account_id=input.default_supplier_account_id,
            default_cash_account_id=input.default_cash_account_id,
            default_bank_account_id=input.default_bank_account_id,
        )
        await db.commit()
        await db.refresh(company)
        return types.Company.from_instance(company)

    @strawberry.mutation
    async def create_department(self, input: DepartmentCreateInput, info: strawberry.Info) -> types.Department:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        dept = await company_repo.create_department(db, name=input.name, company_id=input.company_id,
                                            manager_id=input.manager_id)
        await db.commit()
        await db.refresh(dept)
        return types.Department.from_instance(dept)

    @strawberry.mutation
    async def update_department(self, input: DepartmentUpdateInput, info: strawberry.Info) -> types.Department:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        dept = await company_repo.update_department(db, department_id=input.id, name=input.name, manager_id=input.manager_id)
        await db.commit()
        await db.refresh(dept)
        return types.Department.from_instance(dept)

    @strawberry.mutation
    async def create_position(self, title: str, department_id: Optional[int] = None, info: Optional[strawberry.Info] = None) -> types.Position:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        pos = await company_repo.create_position(db, title, department_id)
        await db.commit()
        await db.refresh(pos)
        return types.Position.from_instance(pos)

    @strawberry.mutation
    async def update_position(self, id: int, title: str, department_id: int, info: strawberry.Info) -> types.Position:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        pos = await company_repo.update_position(db, position_id=id, title=title, department_id=department_id)
        await db.commit()
        await db.refresh(pos)
        return types.Position.from_instance(pos)

    @strawberry.mutation
    async def delete_position(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")
        result = await company_repo.delete_position(db, id)
        await db.commit()
        return result

    @strawberry.mutation
    async def create_role(self, input: RoleCreateInput, info: strawberry.Info) -> types.Role:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        role = await time_repo.create_role(db, schemas.RoleCreate(name=input.name, description=input.description))
        await db.commit()
        await db.refresh(role)
        return types.Role.from_instance(role)

    @strawberry.mutation
    async def update_role(self, id: int, name: Optional[str] = None, description: Optional[str] = None,
                          info: Optional[strawberry.Info] = None) -> types.Role:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        role = await time_repo.update_role(db, role_id=id, name=name, description=description)
        await db.commit()
        await db.refresh(role)
        return types.Role.from_instance(role)

    @strawberry.mutation
    async def delete_role(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")
        result = await time_repo.delete_role(db, id)
        await db.commit()
        return result

    @strawberry.mutation
    async def update_office_location(
            self,
            latitude: float,
            longitude: float,
            radius: int,
            entry_enabled: bool,
            exit_enabled: bool,
            info: strawberry.Info
    ) -> types.OfficeLocation:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        await settings_repo.set_setting(db, "office_latitude", str(latitude))
        await settings_repo.set_setting(db, "office_longitude", str(longitude))
        await settings_repo.set_setting(db, "office_radius", str(radius))
        await settings_repo.set_setting(db, "geofencing_entry_enabled", str(entry_enabled))
        await settings_repo.set_setting(db, "geofencing_exit_enabled", str(exit_enabled))
        await db.commit()

        return types.OfficeLocation(
            latitude=latitude,
            longitude=longitude,
            radius=radius,
            entry_enabled=entry_enabled,
            exit_enabled=exit_enabled
        )
