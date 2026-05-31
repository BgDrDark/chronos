import datetime
import logging

import strawberry
from sqlalchemy import and_, delete, insert, select

from backend import schemas
from backend.auth.rbac_service import PermissionService
from backend.auth.security import (
    hash_password,
    validate_password_complexity,
    verify_password,
)
from backend.crud.repositories import user_repo
from backend.database.models import EmploymentContract, user_access_zones
from backend.database.models import User as DbUser
from backend.exceptions import (
    AuthenticationException,
    NotFoundException,
    ValidationException,
)
from backend.graphql import types
from backend.graphql.inputs import UpdateUserInput, UserCreateInput
from backend.graphql.utils.permission_checker import (
    check_company_access,
    require_permission,
)
from backend.services.auth_service import regenerate_user_qr_token

logger = logging.getLogger(__name__)
authenticate_msg = "Трябва да се автентикирате"


@strawberry.type
class UserMutation:
    @strawberry.mutation
    async def create_user(self, userInput: UserCreateInput, info: strawberry.Info) -> types.User:
        db = info.context["db"]
        info.context["current_user"]
        
        await check_company_access(info, userInput.company_id)

        import dataclasses
        user_input_dict = dataclasses.asdict(userInput)
        user_data = schemas.UserCreate(**user_input_dict)

        db_user = await user_repo.create_user(db=db, user_data=user_data, role_id=userInput.role_id)
        await db.commit()
        await db.refresh(db_user)
        return types.User.from_instance(db_user)

    @strawberry.mutation
    async def update_user(self, userInput: UpdateUserInput, info: strawberry.Info) -> types.User:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None:
            raise AuthenticationException(detail=authenticate_msg)

        if current_user.id != userInput.id:
            await require_permission(info, "users:update", company_id=userInput.company_id)
        else:
            await require_permission(info, "users:update_own")

        update_data = {}
        if userInput.first_name is not None:
            update_data["first_name"] = userInput.first_name
        if userInput.surname is not None:
            update_data["surname"] = userInput.surname
        if userInput.last_name is not None:
            update_data["last_name"] = userInput.last_name
        if userInput.phone_number is not None:
            update_data["phone_number"] = userInput.phone_number
        if userInput.address is not None:
            update_data["address"] = userInput.address
        if userInput.egn is not None:
            update_data["egn"] = userInput.egn
        if userInput.birth_date is not None:
            update_data["birth_date"] = userInput.birth_date
        if userInput.iban is not None:
            update_data["iban"] = userInput.iban
        if userInput.is_active is not None:
            update_data["is_active"] = userInput.is_active
        if userInput.password_force_change is not None:
            update_data["password_force_change"] = userInput.password_force_change
        if userInput.company_id is not None:
            update_data["company_id"] = userInput.company_id
        if userInput.department_id is not None:
            update_data["department_id"] = userInput.department_id
        if userInput.position_id is not None:
            update_data["position_id"] = userInput.position_id
        if userInput.role_id is not None:
            update_data["role_id"] = userInput.role_id
        if userInput.password is not None and userInput.password != '':
            update_data["password"] = userInput.password

        update_data["base_salary"] = userInput.base_salary
        update_data["contract_type"] = userInput.contract_type
        update_data["contract_number"] = userInput.contract_number
        update_data["contract_start_date"] = userInput.contract_start_date
        update_data["contract_end_date"] = userInput.contract_end_date
        update_data["work_hours_per_week"] = userInput.work_hours_per_week
        update_data["probation_months"] = userInput.probation_months
        update_data["salary_calculation_type"] = userInput.salary_calculation_type
        update_data["salary_installments_count"] = userInput.salary_installments_count
        update_data["monthly_advance_amount"] = userInput.monthly_advance_amount
        update_data["tax_resident"] = userInput.tax_resident
        update_data["insurance_contributor"] = userInput.insurance_contributor
        update_data["has_income_tax"] = userInput.has_income_tax
        update_data["payment_day"] = userInput.payment_day
        update_data["experience_start_date"] = userInput.experience_start_date
        update_data["night_work_rate"] = userInput.night_work_rate
        update_data["overtime_rate"] = userInput.overtime_rate
        update_data["holiday_rate"] = userInput.holiday_rate
        update_data["work_class"] = userInput.work_class
        update_data["dangerous_work"] = userInput.dangerous_work

        contract_fields = [
            'base_salary', 'contract_type', 'contract_number', 'contract_start_date', 
            'contract_end_date', 'work_hours_per_week', 'probation_months', 
            'salary_calculation_type', 'salary_installments_count', 'monthly_advance_amount',
            'tax_resident', 'insurance_contributor', 'has_income_tax', 'payment_day',
            'experience_start_date', 'night_work_rate', 'overtime_rate', 'holiday_rate',
            'work_class', 'dangerous_work'
        ]
        for field in contract_fields:
            if field in update_data and update_data[field] is None:
                del update_data[field]

        if userInput.surname is not None:
            update_data["surname"] = userInput.surname

        user_in = schemas.UserUpdate(**update_data)
        db_user = await user_repo.update_user(db, user_id=userInput.id, user_in=user_in)
        
        if userInput.contract_type or userInput.base_salary:
            stmt = select(EmploymentContract).where(
                EmploymentContract.user_id == userInput.id,
                EmploymentContract.is_active
            )
            result = await db.execute(stmt)
            contract = result.scalar_one_or_none()
            
            if contract:
                if userInput.contract_type:
                    contract.contract_type = userInput.contract_type
                if userInput.base_salary is not None:
                    contract.base_salary = userInput.base_salary
                if userInput.contract_start_date:
                    contract.start_date = userInput.contract_start_date
                if userInput.contract_end_date:
                    contract.end_date = userInput.contract_end_date
                if userInput.salary_installments_count:
                    contract.salary_installments_count = userInput.salary_installments_count
                if userInput.monthly_advance_amount is not None:
                    contract.monthly_advance_amount = userInput.monthly_advance_amount
                if userInput.tax_resident is not None:
                    contract.tax_resident = userInput.tax_resident
                if userInput.has_income_tax is not None:
                    contract.has_income_tax = userInput.has_income_tax
                if userInput.insurance_contributor is not None:
                    contract.insurance_contributor = userInput.insurance_contributor
                if userInput.work_hours_per_week is not None:
                    contract.work_hours_per_week = userInput.work_hours_per_week
                if userInput.probation_months is not None:
                    contract.probation_months = userInput.probation_months
                if userInput.salary_calculation_type:
                    contract.salary_calculation_type = userInput.salary_calculation_type
                if userInput.payment_day is not None:
                    contract.payment_day = userInput.payment_day
                if userInput.experience_start_date:
                    contract.experience_start_date = userInput.experience_start_date
                if userInput.night_work_rate is not None:
                    contract.night_work_rate = userInput.night_work_rate
                if userInput.overtime_rate is not None:
                    contract.overtime_rate = userInput.overtime_rate
                if userInput.holiday_rate is not None:
                    contract.holiday_rate = userInput.holiday_rate
                if userInput.work_class:
                    contract.work_class = userInput.work_class
                if userInput.dangerous_work is not None:
                    contract.dangerous_work = userInput.dangerous_work
            else:
                contract = EmploymentContract(
                    user_id=userInput.id,
                    company_id=userInput.company_id or (db_user.company_id if db_user else None),
                    contract_type=userInput.contract_type or 'full_time',
                    start_date=userInput.contract_start_date or datetime.date.today(),
                    base_salary=userInput.base_salary,
                    work_hours_per_week=userInput.work_hours_per_week or 40,
                    probation_months=userInput.probation_months or 0,
                    salary_calculation_type=userInput.salary_calculation_type or 'gross',
                    is_active=True,
                    salary_installments_count=userInput.salary_installments_count or 1,
                    monthly_advance_amount=userInput.monthly_advance_amount or 0,
                    tax_resident=userInput.tax_resident if userInput.tax_resident is not None else True,
                    insurance_contributor=userInput.insurance_contributor if userInput.insurance_contributor is not None else True,
                    has_income_tax=userInput.has_income_tax if userInput.has_income_tax is not None else True,
                    payment_day=userInput.payment_day or 25,
                    experience_start_date=userInput.experience_start_date,
                    night_work_rate=userInput.night_work_rate or 0.5,
                    overtime_rate=userInput.overtime_rate or 1.5,
                    holiday_rate=userInput.holiday_rate or 2.0,
                    work_class=userInput.work_class,
                    dangerous_work=userInput.dangerous_work or False
                )
                db.add(contract)
            
            await db.commit()
        
        return types.User.from_instance(db_user)

    @strawberry.mutation
    async def delete_user(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        
        result = await user_repo.delete_user(db, id)
        await db.commit()
        return result

    @strawberry.mutation
    async def change_password(
            self,
            old_password: str,
            new_password: str,
            info: strawberry.Info
    ) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        stmt = select(DbUser).where(DbUser.id == current_user.id)
        result = await db.execute(stmt)
        db_user = result.scalars().first()

        if not db_user:
            raise NotFoundException.user()

        if not verify_password(old_password, db_user.hashed_password):
            raise ValidationException.field("password", "Неправилна стара парола")

        await validate_password_complexity(db, new_password)

        db_user.hashed_password = hash_password(new_password)
        db_user.password_force_change = False
        db.add(db_user)
        await db.commit()
        return True

    @strawberry.mutation
    async def regenerate_my_qr_code(self, info: strawberry.Info) -> str:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        user = await regenerate_user_qr_token(db, current_user.id)
        await db.commit()
        return user.qr_token

    @strawberry.mutation
    async def invalidate_user_session(self, sessionId: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        
        await require_permission(info, "users:manage_sessions")

        session_to_invalidate = await user_repo.get_user_session_by_id(db, sessionId)
        if not session_to_invalidate:
            raise NotFoundException.session()

        if session_to_invalidate.user_id != current_user.id:
            await check_company_access(info, None)

        return await user_repo.invalidate_user_session(db, session_to_invalidate.refresh_token_jti)

    @strawberry.mutation
    async def assign_role_to_user(self, user_id: int, company_id: int, role_id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        
        await require_permission(info, "users:manage_roles", company_id=company_id)
        await check_company_access(info, company_id)

        perm_service = PermissionService(db)
        await perm_service.assign_role_to_user(user_id, company_id, role_id, current_user.id)
        await db.commit()
        return True

    @strawberry.mutation
    async def bulk_update_user_access(self, user_ids: list[int], zone_ids: list[int], action: str, info: strawberry.Info) -> bool:
        db = info.context["db"]
        
        await require_permission(info, "users:manage_access")
        
        if action == "add":
            for uid in user_ids:
                for zid in zone_ids:
                    stmt = select(user_access_zones).where(
                        user_access_zones.c.user_id == uid,
                        user_access_zones.c.zone_id == zid
                    )
                    res = await db.execute(stmt)
                    if not res.first():
                        await db.execute(insert(user_access_zones).values(user_id=uid, zone_id=zid))
        
        elif action == "remove":
            await db.execute(delete(user_access_zones).where(
                and_(
                    user_access_zones.c.user_id.in_(user_ids),
                    user_access_zones.c.zone_id.in_(zone_ids)
                )
            ))
        
        await db.commit()
        return True
