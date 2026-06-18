import datetime
import logging

import strawberry
from sqlalchemy import select

from backend import schemas
from backend.crud.repositories import payroll_repo
from backend.exceptions import (
    InvalidOperationException,
    NotFoundException,
    ValidationException,
)
from backend.graphql import inputs, types
from backend.graphql.utils.permission_checker import (
    check_company_access,
    get_current_user,
)

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
        current_user = get_current_user(info)

        from backend.database.models import BusinessTrip, sofia_now

        trip = await db.get(BusinessTrip, trip_id)
        if not trip:
            raise NotFoundException.resource("Business Trip")

        check_company_access(db, current_user, "BusinessTrip", trip_id)

        trip.status = "approved" if approved else "rejected"
        trip.approved_by_id = current_user.id
        trip.approved_at = sofia_now()
        trip.approved_notes = notes

        await db.commit()
        await db.refresh(trip)
        return types.BusinessTrip.from_pydantic(schemas.BusinessTrip.model_validate(trip))

    @strawberry.mutation
    async def create_supplier(self, input: inputs.SupplierInput, info: strawberry.Info) -> types.Supplier:
        db = info.context["db"]
        current_user = get_current_user(info)
        target_company_id = input.company_id if current_user.role.name == "super_admin" else current_user.company_id
        if not target_company_id:
            raise ValidationException.required_field("Company ID")
        from backend.database.models import Company
        stmt = select(Company).where(Company.id == target_company_id)
        res = await db.execute(stmt)
        if not res.scalar_one_or_none():
            raise NotFoundException.resource("Фирма", target_company_id)
        check_company_access(db, current_user, "Company", target_company_id)
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
        return types.Supplier.from_pydantic(schemas.Supplier.model_validate(supplier))

    @strawberry.mutation
    async def update_supplier(self, input: inputs.UpdateSupplierInput, info: strawberry.Info) -> types.Supplier:
        db = info.context["db"]
        current_user = get_current_user(info)
        from backend.database.models import Supplier
        stmt = select(Supplier).where(Supplier.id == input.id)
        res = await db.execute(stmt)
        supplier = res.scalar_one_or_none()
        if not supplier:
            raise NotFoundException.resource("Доставчик")
        check_company_access(db, current_user, "Supplier", input.id)
        supplier.name = input.name
        supplier.eik = input.eik
        supplier.vat_number = input.vat_number
        supplier.address = input.address
        supplier.contact_person = input.contact_person
        supplier.phone = input.phone
        supplier.email = input.email
        await db.commit()
        await db.refresh(supplier)
        return types.Supplier.from_pydantic(schemas.Supplier.model_validate(supplier))

    @strawberry.mutation
    async def create_service_loan(
            self,
            info: strawberry.Info,
            user_id: int,
            total_amount: float,
            installments_count: int,
            start_date: datetime.date,
            description: str | None = None,
    ) -> types.ServiceLoan:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = get_current_user(info)
        await check_company_access(db, current_user, "User", user_id)

        loan = await payroll_repo.create_service_loan(
            db, user_id=user_id, amount=total_amount, months=installments_count, start_date=start_date
        )
        return types.ServiceLoan.from_pydantic(schemas.ServiceLoan.model_validate(loan))
