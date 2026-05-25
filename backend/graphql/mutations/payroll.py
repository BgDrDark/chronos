import datetime
import logging
from decimal import Decimal

import strawberry
from sqlalchemy import select

from backend import crud
from backend.auth.module_guard import verify_module_enabled
from backend.crud.repositories import payroll_repo, settings_repo
from backend.database.transaction_manager import (
    atomic_with_savepoint,
)
from backend.exceptions import (
    AuthenticationException,
    InvalidOperationException,
    NotFoundException,
    PermissionDeniedException,
    ValidationException,
)
from backend.graphql import types
from backend.graphql.inputs import BonusCreateInput
from backend.services.notification_service import notification_service
from backend.services.payroll_service import payroll_service

logger = logging.getLogger(__name__)
authenticate_msg = "Трябва да се автентикирате"


@strawberry.type
class PayrollMutation:

    @strawberry.mutation
    async def update_payroll_legal_settings(
            self,
            max_insurance_base: float,
            employee_insurance_rate: float,
            income_tax_rate: float,
            civil_contract_costs_rate: float,
            noi_compensation_percent: float,
            employer_paid_sick_days: int,
            default_tax_resident: bool,
            trz_compliance_strict_mode: bool,
            info: strawberry.Info,
    ) -> types.PayrollLegalSettings:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        # Само super_admin може да променя строгия режим на съответствие
        if trz_compliance_strict_mode is not None and current_user.role.name == "super_admin":
            await settings_repo.set_setting(db, "trz_compliance_strict_mode", str(trz_compliance_strict_mode).lower())

        await settings_repo.set_setting(db, "payroll_max_insurance_base", str(max_insurance_base))
        await settings_repo.set_setting(db, "payroll_employee_insurance_rate", str(employee_insurance_rate))
        await settings_repo.set_setting(db, "payroll_income_tax_rate", str(income_tax_rate))
        await settings_repo.set_setting(db, "payroll_civil_contract_costs_rate", str(civil_contract_costs_rate))
        await settings_repo.set_setting(db, "payroll_noi_compensation_percent", str(noi_compensation_percent))
        await settings_repo.set_setting(db, "payroll_employer_paid_sick_days", str(employer_paid_sick_days))
        await settings_repo.set_setting(db, "payroll_default_tax_resident", str(default_tax_resident))
        await db.commit()

        return types.PayrollLegalSettings(
            max_insurance_base=max_insurance_base,
            employee_insurance_rate=employee_insurance_rate,
            income_tax_rate=income_tax_rate,
            civil_contract_costs_rate=civil_contract_costs_rate,
            noi_compensation_percent=noi_compensation_percent,
            employer_paid_sick_days=employer_paid_sick_days,
            default_tax_resident=default_tax_resident,
            trz_compliance_strict_mode=trz_compliance_strict_mode,
        )

    @strawberry.mutation
    async def update_global_payroll_config(
            self,
            hourly_rate: Decimal,
            monthly_salary: Decimal,
            overtime_multiplier: Decimal,
            standard_hours_per_day: int,
            currency: str,
            annual_leave_days: int,
            tax_percent: Decimal,
            health_insurance_percent: Decimal,
            has_tax_deduction: bool,
            has_health_insurance: bool,
            qr_regen_interval_minutes: int,
            info: strawberry.Info,
    ) -> types.GlobalPayrollConfig:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        config_data = {
            "hourly_rate": hourly_rate,
            "monthly_salary": monthly_salary,
            "overtime_multiplier": overtime_multiplier,
            "standard_hours_per_day": standard_hours_per_day,
            "currency": currency,
            "annual_leave_days": annual_leave_days,
            "tax_percent": tax_percent,
            "health_insurance_percent": health_insurance_percent,
            "has_tax_deduction": has_tax_deduction,
            "has_health_insurance": has_health_insurance,
        }
        payroll_svc = payroll_service(db)
        await payroll_svc.update_global_config(
            hourly_rate=config_data.get("hourly_rate", 0),
            overtime_multiplier=config_data.get("overtime_multiplier", 0),
            standard_hours_per_day=config_data.get("standard_hours_per_day", 0),
            monthly_salary=config_data.get("monthly_salary", 0),
            currency=currency,
            annual_leave_days=annual_leave_days,
            tax_percent=tax_percent,
            health_insurance_percent=health_insurance_percent,
            has_tax_deduction=has_tax_deduction,
            has_health_insurance=has_health_insurance,
        )
        await settings_repo.set_setting(db, "qr_token_regen_minutes", str(qr_regen_interval_minutes))
        await db.commit()

        # Re-fetch the updated config with the new QR setting
        config = await payroll_svc.get_global_config()
        qr_setting = await settings_repo.get_setting(db, "qr_token_regen_minutes")
        return types.GlobalPayrollConfig(
            id="global",
            hourly_rate=Decimal(str(config["hourly_rate"])),
            monthly_salary=Decimal(str(config["monthly_salary"])),
            overtime_multiplier=Decimal(str(config["overtime_multiplier"])),
            standard_hours_per_day=config["standard_hours_per_day"],
            currency=config["currency"],
            annual_leave_days=config["annual_leave_days"],
            tax_percent=Decimal(str(config["tax_percent"])),
            health_insurance_percent=Decimal(str(config["health_insurance_percent"])),
            has_tax_deduction=config["has_tax_deduction"],
            has_health_insurance=config["has_health_insurance"],
            qr_regen_interval_minutes=int(qr_setting) if qr_setting else 60,
        )

    @strawberry.mutation
    async def generate_my_payslip(
            self,
            start_date: datetime.date,
            end_date: datetime.date,
            info: strawberry.Info,
    ) -> types.Payslip:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        await verify_module_enabled("salaries", db)

        # Convert date to datetime for PayrollCalculator
        start_dt = datetime.datetime.combine(start_date, datetime.time.min)
        end_dt = datetime.datetime.combine(end_date, datetime.time.max)
        calculator = crud.PayrollCalculator(db)
        res = await calculator.calculate(current_user.id, start_dt, end_dt)

        # Save to DB
        db_payslip = crud.Payslip(
            user_id=current_user.id,
            period_start=start_date,
            period_end=end_date,
            total_regular_hours=res["total_regular_hours"],
            total_overtime_hours=res["total_overtime_hours"],
            regular_amount=res["regular_amount"],
            overtime_amount=res["overtime_amount"],
            bonus_amount=res["bonus_amount"],
            tax_amount=res["tax_amount"],
            insurance_amount=res["insurance_amount"],
            sick_days=res["sick_days"],
            leave_days=res["leave_days"],
            total_amount=res["total_amount"],
            generated_at=crud.sofia_now(),
        )
        db.add(db_payslip)
        await db.commit()
        await db.refresh(db_payslip)

        return types.Payslip.from_pydantic(db_payslip)

    @strawberry.mutation
    async def generate_payslip(
            self,
            user_id: int,
            start_date: datetime.date,
            end_date: datetime.date,
            info: strawberry.Info,
    ) -> types.Payslip:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        await verify_module_enabled("salaries", db)

        # Convert date to datetime for PayrollCalculator
        start_dt = datetime.datetime.combine(start_date, datetime.time.min)
        end_dt = datetime.datetime.combine(end_date, datetime.time.max)

        calculator = crud.PayrollCalculator(db)
        res = await calculator.calculate(user_id, start_dt, end_dt)

        # Save to DB
        db_payslip = crud.Payslip(
            user_id=user_id,
            period_start=start_date,
            period_end=end_date,
            total_regular_hours=res["total_regular_hours"],
            total_overtime_hours=res["total_overtime_hours"],
            regular_amount=res["regular_amount"],
            overtime_amount=res["overtime_amount"],
            bonus_amount=res["bonus_amount"],
            tax_amount=res["tax_amount"],
            insurance_amount=res["insurance_amount"],
            sick_days=res["sick_days"],
            leave_days=res["leave_days"],
            total_amount=res["total_amount"],
            generated_at=crud.sofia_now(),
        )
        db.add(db_payslip)
        await db.commit()
        await db.refresh(db_payslip)

        return types.Payslip.from_pydantic(db_payslip)

    @strawberry.mutation
    async def add_bonus(self, input: BonusCreateInput, info: strawberry.Info) -> types.Bonus:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        bonus = await payroll_repo.create_bonus(
            db,
            user_id=input.user_id,
            amount=input.amount,
            date=input.date,
            description=input.description,
        )
        async with atomic_with_savepoint(db, "bonus_created"):
            pass  # Reserved for future notifications
        await db.commit()
        return types.Bonus.from_pydantic(bonus)

    @strawberry.mutation
    async def remove_bonus(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        await payroll_repo.delete_bonus(db, id)
        await db.commit()
        return True

    @strawberry.mutation
    async def create_advance_payment(
            self,
            user_id: int,
            amount: float,
            payment_date: datetime.date,
            description: str | None = None,
            info: strawberry.Info = None,
    ) -> types.AdvancePayment:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        advance = await payroll_repo.create_advance_payment(
            db, user_id=user_id, amount=amount, request_date=payment_date,
        )
        return types.AdvancePayment.from_pydantic(advance)

    @strawberry.mutation
    async def create_service_loan(
            self,
            user_id: int,
            total_amount: float,
            installments_count: int,
            start_date: datetime.date,
            description: str,
            info: strawberry.Info = None,
    ) -> types.ServiceLoan:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        loan = await payroll_repo.create_service_loan(
            db, user_id=user_id, amount=total_amount, months=installments_count,
        )
        return types.ServiceLoan.from_pydantic(loan)

    @strawberry.mutation
    async def mark_payslip_as_paid(
        self,
        payslip_id: int,
        payment_date: datetime.datetime | None = None,
        payment_method: str = "bank",
        info: strawberry.Info = None,
    ) -> types.Payslip:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")

        from backend.database.models import Payslip, sofia_now

        payslip = await db.get(Payslip, payslip_id)
        if not payslip:
            raise NotFoundException.resource("Payslip")

        payslip.payment_status = "paid"
        payslip.actual_payment_date = payment_date or sofia_now()
        payslip.payment_method = payment_method

        await db.commit()
        await db.refresh(payslip)

        # Notify user
        await notification_service.create_notification(
            db,
            user_id=payslip.user_id,
            message=f"Заплата за период {payslip.period_start.strftime('%d.%m.%Y')} - {payslip.period_end.strftime('%d.%m.%Y')} е маркирана като платена.",
        )
        await db.commit()

        return types.Payslip.from_pydantic(payslip)

    @strawberry.mutation
    async def bulk_mark_payslips_as_paid(
        self,
        payslip_ids: list[int],
        payment_date: datetime.datetime | None = None,
        payment_method: str = "bank",
        info: strawberry.Info = None,
    ) -> list[types.Payslip]:
        """Bulk mark multiple payslips as paid.
        Used for batch payment processing.
        """
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        from backend.database.models import Payslip, sofia_now

        updated_payslips = []

        for payslip_id in payslip_ids:
            payslip = await db.get(Payslip, payslip_id)
            if payslip and payslip.payment_status != "paid":
                payslip.payment_status = "paid"
                payslip.actual_payment_date = payment_date or sofia_now()
                payslip.payment_method = payment_method
                await db.refresh(payslip)
                updated_payslips.append(payslip)

        await db.commit()
        return [types.Payslip.from_pydantic(p) for p in updated_payslips]

    @strawberry.mutation
    async def generate_sepa_xml(
        self,
        company_id: int,
        period_start: datetime.date,
        period_end: datetime.date,
        execution_date: datetime.date | None = None,
        info: strawberry.Info = None,
    ) -> str:
        """Generate SEPA XML file for payroll payments.
        """
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        from sqlalchemy import and_

        from backend.database.models import EmploymentContract, Payslip, User
        from backend.services.sepa_generator import SEPAGenerator
        # Get company settings
        company_name = await settings_repo.get_setting(db, f"company_{company_id}_name") or "Company"
        company_iban = await settings_repo.get_setting(db, f"company_{company_id}_iban") or ""
        company_bic = await settings_repo.get_setting(db, f"company_{company_id}_bic") or ""

        if not company_iban:
            raise ValidationException(detail="Company IBAN not configured")

        # Get paid payslips for the period
        result = await db.execute(
            select(Payslip).where(
                and_(
                    Payslip.period_start >= period_start,
                    Payslip.period_end <= period_end,
                    Payslip.payment_status == "paid",
                ),
            ),
        )
        payslips = result.scalars().all()

        # Build payments list
        payments = []
        for payslip in payslips:
            user = await db.get(User, payslip.user_id)
            if user and user.iban:
                # Try to get bank details from employment contract
                emp_result = await db.execute(
                    select(EmploymentContract).where(
                        EmploymentContract.user_id == user.id,
                        EmploymentContract.is_active,
                    ),
                )
                emp_result.scalars().first()

                payments.append({
                    "name": f"{user.firstName or ''} {user.lastName or ''}".strip(),
                    "iban": user.iban,
                    "amount": float(payslip.total_amount),
                    "reference": f"SAL-{payslip.id}",
                    "description": f"Заплата {period_start.strftime('%m/%Y')}",
                })

        # Generate SEPA XML
        generator = SEPAGenerator(
            sender_name=company_name,
            sender_iban=company_iban,
            sender_bic=company_bic,
        )

        validation = generator.validate_payments(payments)
        if not validation["valid"]:
            raise ValidationException(detail=f"Invalid payments: {', '.join(validation['errors'])}")

        return generator.generate_payment_xml(
            payments=payments,
            batch_name=f"Payroll {period_start.strftime('%m/%Y')}",
            execution_date=execution_date.strftime("%Y-%m-%d") if execution_date else None,
        )
