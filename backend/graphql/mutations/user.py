import datetime
import logging
from decimal import Decimal

import strawberry
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy import and_, delete, insert, select
from sqlalchemy.orm import selectinload

from backend import schemas
from backend.auth.rbac_service import PermissionService
from backend.auth.security import (
    hash_password,
    validate_password_complexity,
    verify_password,
)
from backend.crud.repositories import user_repo
from backend.database.models import AuditLog, EmploymentContract, user_access_zones
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
from backend.utils.pin_utils import decrypt_pin

logger = logging.getLogger(__name__)
authenticate_msg = "Трябва да се автентикирате"


def _handle_pydantic_error(e: PydanticValidationError) -> None:
    """Convert Pydantic ValidationError to user-friendly ValidationException."""
    for error in e.errors():
        field = error.get("loc", ("unknown",))[-1]
        field_name = str(field)
        msg = error.get("msg", "Невалидна стойност")
        # Remove Pydantic URL suffix
        msg = msg.split(" For further information")[0]
        field_labels = {
            "phone_number": "Телефонен номер",
            "email": "Имейл",
            "egn": "ЕГН",
            "iban": "IBAN",
            "password": "Парола",
            "username": "Потребителско име",
            "first_name": "Име",
            "surname": "Презиме",
            "last_name": "Фамилия",
        }
        label = field_labels.get(field_name, field_name)
        raise ValidationException.field(label, msg)
    raise ValidationException.field("данни", "Невалидни входни данни")


@strawberry.type
class UserMutation:
    @strawberry.mutation
    async def create_user(self, userInput: UserCreateInput, info: strawberry.Info) -> types.User:
        db = info.context["db"]
        info.context["current_user"]
        
        await check_company_access(info, userInput.company_id)

        import dataclasses
        user_input_dict = dataclasses.asdict(userInput)
        user_input_dict.pop("pin_code", None)
        try:
            user_data = schemas.UserCreate(**user_input_dict)
        except PydanticValidationError as e:
            _handle_pydantic_error(e)
            raise AssertionError("unreachable")  # _handle_pydantic_error always raises

        db_user = await user_repo.create_user(db=db, user_data=user_data, role_id=userInput.role_id)

        if userInput.pin_code:
            if not await user_repo.check_pin_unique(db, userInput.pin_code):
                raise ValidationException.field("pin_code", "Този PIN вече се използва")
            await user_repo.set_pin_code(db, db_user.id, userInput.pin_code)

        has_contract_data = any([
            userInput.contract_type is not None,
            userInput.base_salary is not None,
            userInput.contract_start_date is not None,
        ])
        if has_contract_data:
            contract = EmploymentContract(
                user_id=db_user.id,
                company_id=userInput.company_id,
                contract_type=userInput.contract_type or 'full_time',
                start_date=userInput.contract_start_date or datetime.date.today(),
                base_salary=userInput.base_salary,
                work_hours_per_week=userInput.work_hours_per_week or 40,
                contract_number=userInput.contract_number,
                end_date=userInput.contract_end_date,
                probation_months=userInput.probation_months or 0,
                salary_calculation_type=userInput.salary_calculation_type or 'gross',
                salary_installments_count=userInput.salary_installments_count or 1,
                monthly_advance_amount=userInput.monthly_advance_amount or Decimal(0),
                tax_resident=userInput.tax_resident if userInput.tax_resident is not None else True,
                insurance_contributor=userInput.insurance_contributor if userInput.insurance_contributor is not None else True,
                has_income_tax=userInput.has_income_tax if userInput.has_income_tax is not None else True,
                payment_day=userInput.payment_day or 25,
                experience_start_date=userInput.experience_start_date,
                night_work_rate=userInput.night_work_rate or Decimal('0.50'),
                overtime_rate=userInput.overtime_rate or Decimal('1.50'),
                holiday_rate=userInput.holiday_rate or Decimal('2.00'),
                work_class=userInput.work_class,
                dangerous_work=userInput.dangerous_work or False,
                status='draft',
                is_active=False,
            )
            db.add(contract)

        await db.commit()
        stmt = select(DbUser).where(DbUser.id == db_user.id).options(selectinload(DbUser.role))
        result = await db.execute(stmt)
        db_user = result.scalar_one()
        return types.User.from_pydantic(schemas.User.model_validate(db_user))

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
        if userInput.pin_code is not None:
            if not await user_repo.check_pin_unique(db, userInput.pin_code, exclude_user_id=userInput.id):
                raise ValidationException.field("pin_code", "Този PIN вече се използва")
            await user_repo.set_pin_code(db, userInput.id, userInput.pin_code)

        user_in = schemas.UserUpdate(**update_data)
        db_user = await user_repo.update_user(db, user_id=userInput.id, user_in=user_in)

        has_contract_data = any([
            userInput.contract_type is not None,
            userInput.base_salary is not None,
            userInput.contract_start_date is not None,
        ])
        if has_contract_data:
            stmt = select(EmploymentContract).where(
                EmploymentContract.user_id == userInput.id,
                EmploymentContract.status.in_(["draft", "signed", "linked"]),
            ).order_by(EmploymentContract.created_at.desc())
            result = await db.execute(stmt)
            existing_contract = result.scalar_one_or_none()

            if existing_contract and existing_contract.status in ("signed", "linked"):
                raise ValidationException.field(
                    "Договор",
                    "Потребителят има подписан или линкнат договор. Промени се правят само чрез анекс."
                )

            if existing_contract and existing_contract.status == "draft":
                if userInput.contract_type is not None:
                    existing_contract.contract_type = userInput.contract_type
                if userInput.contract_number is not None:
                    existing_contract.contract_number = userInput.contract_number
                if userInput.contract_start_date is not None:
                    existing_contract.start_date = userInput.contract_start_date
                if userInput.contract_end_date is not None:
                    existing_contract.end_date = userInput.contract_end_date
                if userInput.base_salary is not None:
                    existing_contract.base_salary = userInput.base_salary
                if userInput.work_hours_per_week is not None:
                    existing_contract.work_hours_per_week = userInput.work_hours_per_week
                if userInput.probation_months is not None:
                    existing_contract.probation_months = userInput.probation_months
                if userInput.salary_calculation_type is not None:
                    existing_contract.salary_calculation_type = userInput.salary_calculation_type
                if userInput.salary_installments_count is not None:
                    existing_contract.salary_installments_count = userInput.salary_installments_count
                if userInput.monthly_advance_amount is not None:
                    existing_contract.monthly_advance_amount = userInput.monthly_advance_amount
                if userInput.tax_resident is not None:
                    existing_contract.tax_resident = userInput.tax_resident
                if userInput.insurance_contributor is not None:
                    existing_contract.insurance_contributor = userInput.insurance_contributor
                if userInput.has_income_tax is not None:
                    existing_contract.has_income_tax = userInput.has_income_tax
                if userInput.payment_day is not None:
                    existing_contract.payment_day = userInput.payment_day
                if userInput.experience_start_date is not None:
                    existing_contract.experience_start_date = userInput.experience_start_date
                if userInput.night_work_rate is not None:
                    existing_contract.night_work_rate = userInput.night_work_rate
                if userInput.overtime_rate is not None:
                    existing_contract.overtime_rate = userInput.overtime_rate
                if userInput.holiday_rate is not None:
                    existing_contract.holiday_rate = userInput.holiday_rate
                if userInput.work_class is not None:
                    existing_contract.work_class = userInput.work_class
                if userInput.dangerous_work is not None:
                    existing_contract.dangerous_work = userInput.dangerous_work
                db.add(existing_contract)
            elif not existing_contract:
                contract = EmploymentContract(
                    user_id=userInput.id,
                    company_id=userInput.company_id or (db_user.company_id if db_user else None),
                    contract_type=userInput.contract_type or 'full_time',
                    start_date=userInput.contract_start_date or datetime.date.today(),
                    base_salary=userInput.base_salary,
                    work_hours_per_week=userInput.work_hours_per_week or 40,
                    contract_number=userInput.contract_number,
                    end_date=userInput.contract_end_date,
                    probation_months=userInput.probation_months or 0,
                    salary_calculation_type=userInput.salary_calculation_type or 'gross',
                    salary_installments_count=userInput.salary_installments_count or 1,
                    monthly_advance_amount=userInput.monthly_advance_amount or Decimal(0),
                    tax_resident=userInput.tax_resident if userInput.tax_resident is not None else True,
                    insurance_contributor=userInput.insurance_contributor if userInput.insurance_contributor is not None else True,
                    has_income_tax=userInput.has_income_tax if userInput.has_income_tax is not None else True,
                    payment_day=userInput.payment_day or 25,
                    experience_start_date=userInput.experience_start_date,
                    night_work_rate=userInput.night_work_rate or Decimal('0.50'),
                    overtime_rate=userInput.overtime_rate or Decimal('1.50'),
                    holiday_rate=userInput.holiday_rate or Decimal('2.00'),
                    work_class=userInput.work_class,
                    dangerous_work=userInput.dangerous_work or False,
                    status='draft',
                    is_active=False,
                )
                db.add(contract)

        stmt = select(DbUser).where(DbUser.id == db_user.id).options(selectinload(DbUser.role))
        result = await db.execute(stmt)
        db_user = result.scalar_one()
        return types.User.from_pydantic(schemas.User.model_validate(db_user))

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
    async def generate_pin(self, user_id: int, info: strawberry.Info) -> str:
        """Генерира 8-цифрен PIN за потребител. Връща го веднъж (само при генериране)."""
        import secrets
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None:
            raise AuthenticationException(detail=authenticate_msg)

        if current_user.id != user_id:
            await require_permission(info, "users:manage_access")

        for _ in range(10):
            pin = "".join(secrets.choice("0123456789") for _ in range(8))
            if await user_repo.check_pin_unique(db, pin, exclude_user_id=user_id):
                break
        else:
            raise ValidationException("Не може да се генерира уникален PIN")

        await user_repo.set_pin_code(db, user_id, pin)

        log = AuditLog(
            user_id=current_user.id,
            action="GENERATE_PIN",
            target_type="User",
            target_id=user_id,
            details="Генериран е PIN код за достъп",
        )
        db.add(log)

        await db.commit()
        return pin

    @strawberry.mutation
    async def reissue_pin(self, user_id: int, info: strawberry.Info) -> str:
        """Преиздава 8-цифрен PIN (заменя стария). Връща го веднъж."""
        import secrets
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None:
            raise AuthenticationException(detail=authenticate_msg)

        if current_user.id != user_id:
            await require_permission(info, "users:manage_access")

        for _ in range(10):
            pin = "".join(secrets.choice("0123456789") for _ in range(8))
            if await user_repo.check_pin_unique(db, pin, exclude_user_id=user_id):
                break
        else:
            raise ValidationException("Не може да се генерира уникален PIN")

        await user_repo.set_pin_code(db, user_id, pin)

        log = AuditLog(
            user_id=current_user.id,
            action="REISSUE_PIN",
            target_type="User",
            target_id=user_id,
            details="Преиздаден е PIN код за достъп",
        )
        db.add(log)

        await db.commit()
        return pin

    @strawberry.mutation
    async def reveal_pin(self, info: strawberry.Info, password: str) -> str | None:
        """Разкрива PIN кода след въвеждане на парола."""
        db = info.context["db"]
        current_user_schema = info.context["current_user"]
        if current_user_schema is None:
            raise AuthenticationException(detail=authenticate_msg)

        from sqlalchemy import select

        result = await db.execute(
            select(DbUser).where(DbUser.id == current_user_schema.id)
        )
        db_user = result.scalar_one_or_none()
        if not db_user:
            raise AuthenticationException(detail=authenticate_msg)

        if not verify_password(password, db_user.hashed_password):
            raise ValidationException.field("password", "Неправилна парола")

        if not db_user.pin_encrypted:
            return None

        return decrypt_pin(db_user.pin_encrypted)

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
