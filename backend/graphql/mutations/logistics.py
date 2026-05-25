import datetime
import logging

import strawberry
from sqlalchemy import select

from backend.crud.repositories import payroll_repo
from backend.exceptions import (
    InvalidOperationException,
    NotFoundException,
    PermissionDeniedException,
    ValidationException,
)
from backend.graphql import types, inputs

logger = logging.getLogger(__name__)


@strawberry.type
class LogisticsMutation:
    @strawberry.mutation
    async def approve_business_trip(
        self,
        trip_id: int,
        approved: bool,
        notes: str | None = None,
        info: strawberry.Info | None = None,
    ) -> types.BusinessTrip:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")

        from backend.database.models import BusinessTrip, sofia_now

        trip = await db.get(BusinessTrip, trip_id)
        if not trip:
            raise NotFoundException.resource("Business Trip")

        trip.status = "approved" if approved else "rejected"
        trip.approved_by_id = current_user.id
        trip.approved_at = sofia_now()
        trip.approved_notes = notes

        await db.commit()
        await db.refresh(trip)
        return types.BusinessTrip.from_instance(trip)

    @strawberry.mutation
    async def create_supplier(self, input: inputs.SupplierInput, info: strawberry.Info) -> types.Supplier:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin", "Warehouse_Manager"]:
            raise PermissionDeniedException.for_action("manage")
        target_company_id = input.company_id if current_user.role.name == "super_admin" else current_user.company_id
        if not target_company_id:
            raise ValidationException.required_field("Company ID")
        from backend.database.models import Company
        stmt = select(Company).where(Company.id == target_company_id)
        res = await db.execute(stmt)
        if not res.scalar_one_or_none():
            raise NotFoundException.resource("Фирма", target_company_id)
        from backend.database.models import Supplier
        supplier = Supplier(
            name=input.name,
            eik=input.eik,
            vat_number=input.vat_number,
            address=input.address,
            contact_person=input.contact_person,
            phone=input.phone,
            email=input.email,
            company_id=target_company_id
        )
        db.add(supplier)
        await db.commit()
        await db.refresh(supplier)
        return types.Supplier.from_instance(supplier)

    @strawberry.mutation
    async def update_supplier(self, input: inputs.UpdateSupplierInput, info: strawberry.Info) -> types.Supplier:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin", "Warehouse_Manager"]:
            raise PermissionDeniedException.for_action("manage")
        from backend.database.models import Supplier
        stmt = select(Supplier).where(Supplier.id == input.id)
        res = await db.execute(stmt)
        supplier = res.scalar_one_or_none()
        if not supplier:
            raise NotFoundException.resource("Доставчик")
        if current_user.role.name not in ["super_admin"] and supplier.company_id != current_user.company_id:
            raise PermissionDeniedException.for_resource("доставчик", "access")
        supplier.name = input.name
        supplier.eik = input.eik
        supplier.vat_number = input.vat_number
        supplier.address = input.address
        supplier.contact_person = input.contact_person
        supplier.phone = input.phone
        supplier.email = input.email
        await db.commit()
        await db.refresh(supplier)
        return types.Supplier.from_instance(supplier)

    @strawberry.mutation
    async def create_service_loan(
            self,
            user_id: int,
            total_amount: float,
            installments_count: int,
            start_date: datetime.date,
            description: str,
            info: strawberry.Info | None = None
    ) -> types.ServiceLoan:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        loan = await payroll_repo.create_service_loan(
            db, user_id=user_id, amount=total_amount, months=installments_count
        )
        return types.ServiceLoan.from_instance(loan)
