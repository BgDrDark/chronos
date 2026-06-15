import datetime
from decimal import Decimal

import strawberry
from sqlalchemy import select

from backend import crud
from backend.config import settings
from backend.crud.repositories import settings_repo, user_repo
from backend.exceptions import PermissionDeniedException
from backend.graphql import types
from backend.graphql.utils.permission_checker import (
    get_current_user,
    require_permission,
)
from backend.services.payroll_calculator import PayrollCalculator

authenticate_msg = "Трябва да се автентикирате"

@strawberry.type
class PayrollQuery:

    @strawberry.field
    async def payroll_legal_settings(self, info: strawberry.Info) -> types.PayrollLegalSettings:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
             raise PermissionDeniedException.for_action("access")

        max_ins = await settings_repo.get_setting(db, "payroll_max_insurance_base")
        ins_rate = await settings_repo.get_setting(db, "payroll_employee_insurance_rate")
        tax_rate = await settings_repo.get_setting(db, "payroll_income_tax_rate")
        civil_costs = await settings_repo.get_setting(db, "payroll_civil_contract_costs_rate")
        noi_perc = await settings_repo.get_setting(db, "payroll_noi_compensation_percent")
        sick_days = await settings_repo.get_setting(db, "payroll_employer_paid_sick_days")
        tax_res = await settings_repo.get_setting(db, "payroll_default_tax_resident")
        strict_mode = await settings_repo.get_setting(db, "trz_compliance_strict_mode")

        return types.PayrollLegalSettings(
            max_insurance_base=float(max_ins) if max_ins else 3750.0,
            employee_insurance_rate=float(ins_rate) if ins_rate else 13.78,
            income_tax_rate=float(tax_rate) if tax_rate else 10.0,
            civil_contract_costs_rate=float(civil_costs) if civil_costs else 25.0,
            noi_compensation_percent=float(noi_perc) if noi_perc else 80.0,
            employer_paid_sick_days=int(sick_days) if sick_days else 2,
            default_tax_resident=(tax_res.lower() == "true") if tax_res else True,
            trz_compliance_strict_mode=(strict_mode.lower() == "true") if strict_mode else False,
        )

    @strawberry.field
    async def payroll_summary(
        self,
        info: strawberry.Info,
        start_date: datetime.date,
        end_date: datetime.date,
        user_ids: list[int] | None = None,
    ) -> list[types.PayrollSummaryItem]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("view records")

        from backend.database.models import (
            AdvancePayment,
            EmploymentContract,
            NOIPaymentDays,
            PayrollDeduction,
            PayrollPaymentSchedule,
            ServiceLoan,
            SickLeaveRecord,
            User,
        )
        from backend.services.enhanced_payroll_calculator import (
            EnhancedPayrollCalculator,
        )

        # 1. Fetch Users
        stmt = select(User).where(User.is_active)

        # Isolation: Non-super_admin sees only their company
        if current_user.role.name != "super_admin":
            stmt = stmt.where(User.company_id == current_user.company_id)

        if user_ids:
            stmt = stmt.where(User.id.in_(user_ids))
        result = await db.execute(stmt)
        users = result.scalars().all()
        target_ids = [u.id for u in users]
        if not target_ids: return []

        # 2. BULK LOAD everything in parallel queries
        # Isolation: Filter settings by company_id if not super_admin
        company_id = current_user.company_id if current_user.role.name != "super_admin" else None
        schedule_stmt = select(PayrollPaymentSchedule).where(PayrollPaymentSchedule.active)
        deductions_stmt = select(PayrollDeduction).where(PayrollDeduction.is_active)

        if company_id:
            schedule_stmt = schedule_stmt.where(PayrollPaymentSchedule.company_id == company_id)
            deductions_stmt = deductions_stmt.where(PayrollDeduction.company_id == company_id)

        # B) User-specific records
        from sqlalchemy.orm import selectinload
        contracts_stmt = select(EmploymentContract).options(
            selectinload(EmploymentContract.user),
        ).where(EmploymentContract.user_id.in_(target_ids), EmploymentContract.is_active)
        sick_stmt = select(SickLeaveRecord).where(SickLeaveRecord.user_id.in_(target_ids), SickLeaveRecord.start_date >= start_date, SickLeaveRecord.end_date <= end_date)
        advances_stmt = select(AdvancePayment).where(AdvancePayment.user_id.in_(target_ids), AdvancePayment.payment_date >= start_date, AdvancePayment.payment_date <= end_date, not AdvancePayment.is_processed)
        loans_stmt = select(ServiceLoan).where(ServiceLoan.user_id.in_(target_ids), ServiceLoan.is_active, ServiceLoan.remaining_amount > 0)
        noi_stmt = select(NOIPaymentDays).where(NOIPaymentDays.user_id.in_(target_ids), NOIPaymentDays.year == start_date.year)

        # Execute all (Simplified execution for clarity)
        schedule_res = (await db.execute(schedule_stmt)).scalar_one_or_none()
        deductions = (await db.execute(deductions_stmt)).scalars().all()

        contracts = {c.user_id: c for c in (await db.execute(contracts_stmt)).scalars().all()}

        # Group lists by user_id
        def group_by_user(items):
            d = {}
            for item in items:
                d.setdefault(item.user_id, []).append(item)
            return d

        sick_records = group_by_user((await db.execute(sick_stmt)).scalars().all())
        advances = group_by_user((await db.execute(advances_stmt)).scalars().all())
        loans = group_by_user((await db.execute(loans_stmt)).scalars().all())
        noi_days = {n.user_id: n for n in (await db.execute(noi_stmt)).scalars().all()}

        # 3. Compile preloaded data packet
        preloaded = {
            "payment_schedule": schedule_res,
            "deductions": deductions,
            "contracts": contracts,
            "sick_records": sick_records,
            "advances": advances,
            "loans": loans,
            "noi_days": noi_days,
        }

        summary = []
        period = {"start_date": start_date, "end_date": end_date}

        for user in users:
            # Use calculator with PRELOADED data (No extra DB calls inside)
            calc = EnhancedPayrollCalculator(db, user.company_id or 1, user.id, period, preloaded_data=preloaded)
            try:
                data = await calc.calculate_enhanced_payroll()
                summary.append(types.PayrollSummaryItem(
                    user_id=user.id,
                    email=user.email,
                    full_name=f"{user.first_name} {user.last_name}",
                    gross_amount=data["gross_amount"],
                    net_amount=data["net_amount"],
                    tax_amount=data["tax_amount"],
                    insurance_amount=data["insurance_amount"],
                    bonus_amount=data["bonus_amount"],
                    advances=data["advances"],
                    loan_deductions=data["loan_deductions"],
                    total_deductions=data["total_deductions"],
                    net_payable=data["net_payable"],
                    contract_type=data["contract_type"],
                    installments=types.SalaryInstallments(
                        count=data["installments"]["count"],
                        amount_per_installment=data["installments"]["amount_per_installment"],
                    ),
                ))
            except Exception as e:
                print(f"Error calculating payroll for user {user.id}: {e}")
                continue

        return summary

    @strawberry.field
    async def global_payroll_config(self, info: strawberry.Info) -> types.GlobalPayrollConfig:
        db = info.context["db"]
        # Make this public so frontend can fetch currency even when not logged in
        config = await crud.get_global_payroll_config(db)

        return types.GlobalPayrollConfig(
            hourly_rate=Decimal(str(config.hourly_rate)),
            monthly_salary=Decimal(str(config.monthly_salary)),
            overtime_multiplier=Decimal(str(config.overtime_multiplier)),
            standard_hours_per_day=config.standard_hours_per_day,
            currency=config.currency,
            annual_leave_days=config.annual_leave_days,
            tax_percent=Decimal(str(config.tax_percent)),
            health_insurance_percent=Decimal(str(config.health_insurance_percent)),
            has_tax_deduction=config.has_tax_deduction,
            has_health_insurance=config.has_health_insurance,
            qr_regen_interval_minutes=settings.QR_TOKEN_REGEN_MINUTES,
        )

    @strawberry.field
    async def payroll_forecast(self, info: strawberry.Info, year: int, month: int) -> types.PayrollForecast:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("view payroll forecast")

        # 1. Get All Active Users
        users = await user_repo.get_users(db, limit=1000)

        total = 0.0
        dept_map = {}

        calc = PayrollCalculator(db)

        # Optimized: Use asyncio.gather for parallel queries instead of sequential loop
        async def calc_user_amount(u):
            if not u.is_active:
                return 0.0
            return await calc.calculate_forecast(u.id, year, month)

        # Run all calculations in parallel
        import asyncio
        amounts = await asyncio.gather(*[calc_user_amount(u) for u in users])

        for u, amount in zip(users, amounts, strict=False):
            total += amount

            # Use new department relation if available, else string fallback
            dept_name = "Без отдел"
            if u.department:
                dept_name = u.department

            if dept_name not in dept_map: dept_map[dept_name] = 0.0
            dept_map[dept_name] += amount

        by_dept = [
            types.DepartmentForecast(department_name=k, amount=round(v, 2))
            for k, v in dept_map.items()
        ]

        return types.PayrollForecast(total_amount=round(total, 2), by_department=by_dept)

    @strawberry.field
    async def payment_batches(
        self,
        info: strawberry.Info,
        company_id: int | None = None,
        status: str | None = None,
        period_start: datetime.date | None = None,
        period_end: datetime.date | None = None,
    ) -> list[types.SalaryPaymentBatchType]:
        from backend.crud.repositories.salary_payment_repo import salary_payment_repo
        db = info.context["db"]
        get_current_user(info)
        await require_permission(info, "payroll:read")

        batches = await salary_payment_repo.list_batches(
            db,
            company_id=company_id,
            status=status,
            period_start=period_start,
            period_end=period_end,
        )
        return [types.SalaryPaymentBatchType(
            id=b.id, company_id=b.company_id,
            period_start=b.period_start, period_end=b.period_end,
            payment_date=b.payment_date, total_amount=float(b.total_amount),
            status=b.status, payment_method=b.payment_method,
            payment_reference=b.payment_reference, notes=b.notes,
            created_at=b.created_at, paid_by=b.paid_by,
        ) for b in batches]

    @strawberry.field
    async def payment_batch(
        self,
        info: strawberry.Info,
        id: int,
    ) -> types.SalaryPaymentBatchType | None:
        from backend.crud.repositories.salary_payment_repo import salary_payment_repo
        db = info.context["db"]
        get_current_user(info)
        await require_permission(info, "payroll:read")

        batch = await salary_payment_repo.get_batch(db, id)
        if not batch:
            return None
        return types.SalaryPaymentBatchType(
            id=batch.id, company_id=batch.company_id,
            period_start=batch.period_start, period_end=batch.period_end,
            payment_date=batch.payment_date, total_amount=float(batch.total_amount),
            status=batch.status, payment_method=batch.payment_method,
            payment_reference=batch.payment_reference, notes=batch.notes,
            created_at=batch.created_at,
        )

    @strawberry.field
    async def my_payment_history(
        self,
        info: strawberry.Info,
        year: int | None = None,
    ) -> list[types.SalaryPaymentItemType]:
        from backend.crud.repositories.salary_payment_repo import salary_payment_repo
        db = info.context["db"]
        user = get_current_user(info)

        items = await salary_payment_repo.list_items_by_user(db, user.id, year)
        return [types.SalaryPaymentItemType(
            id=item.id, batch_id=item.batch_id,
            payslip_id=item.payslip_id, user_id=item.user_id,
            amount=float(item.amount), paid_at=item.paid_at,
        ) for item in items]

    @strawberry.field
    async def payment_statistics(
        self,
        info: strawberry.Info,
        company_id: int,
        year: int,
        month: int | None = None,
    ) -> types.PaymentStatisticsType | None:
        from backend.services.salary_payment_service import SalaryPaymentService
        db = info.context["db"]
        get_current_user(info)
        await require_permission(info, "payroll:read")

        service = SalaryPaymentService(db)
        stats = await service.get_statistics(company_id, year, month)
        return types.PaymentStatisticsType(**stats)

    @strawberry.field
    async def user_payment_history(
        self,
        info: strawberry.Info,
        user_id: int,
        year: int | None = None,
    ) -> list[types.SalaryPaymentItemType]:
        from backend.crud.repositories.salary_payment_repo import salary_payment_repo
        db = info.context["db"]
        get_current_user(info)
        await require_permission(info, "payroll:read")

        items = await salary_payment_repo.list_items_by_user(db, user_id, year)
        return [types.SalaryPaymentItemType(
            id=item.id, batch_id=item.batch_id,
            payslip_id=item.payslip_id, user_id=item.user_id,
            amount=float(item.amount), paid_at=item.paid_at,
        ) for item in items]
