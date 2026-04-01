import datetime
from decimal import Decimal
from typing import List, Optional
import strawberry
from sqlalchemy import select, Time, desc
from backend import crud
from backend.config import settings
from backend.exceptions import (
    AuthenticationException,
    PermissionDeniedException,
    NotFoundException,
)
from backend.graphql import types
from backend.services.payroll_calculator import PayrollCalculator

authenticate_msg = "Трябва да се автентикирате"
@strawberry.type
class Query:
    @strawberry.field
    async def hello(self) -> str:
        return "Hello World"

    @strawberry.field
    async def me(self, info: strawberry.Info) -> Optional[types.User]:
        current_user = info.context["current_user"]
        if current_user:
            return types.User.from_instance(current_user)
        return None

    @strawberry.field
    async def employment_contracts(
        self,
        info: strawberry.Info,
        company_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> List[types.EmploymentContract]:
        """Връща списък с трудови договори"""
        from sqlalchemy import select
        from backend.database.models import EmploymentContract
        db = info.context["db"]
        current_user = info.context["current_user"]
        
        if current_user.role.name not in ["admin", "super_admin"]:
            raise AuthenticationException(detail="Трябва да сте администратор за достъп до договорите")
        
        from sqlalchemy.orm import selectinload
        stmt = select(EmploymentContract).options(
            selectinload(EmploymentContract.company),
            selectinload(EmploymentContract.position),
            selectinload(EmploymentContract.department)
        )
        
        # Filter by company
        if company_id:
            stmt = stmt.where(EmploymentContract.company_id == company_id)
        elif current_user.role.name != "super_admin":
            stmt = stmt.where(EmploymentContract.company_id == current_user.company_id)
        
        # Filter by status
        if status:
            stmt = stmt.where(EmploymentContract.status == status)
        
        stmt = stmt.order_by(EmploymentContract.created_at.desc())
        
        result = await db.execute(stmt)
        contracts = result.scalars().all()
        return [types.EmploymentContract.from_instance(c) for c in contracts]

    @strawberry.field
    async def employment_contract(
        self,
        info: strawberry.Info,
        id: int
    ) -> Optional[types.EmploymentContract]:
        """Връща конкретен трудов договор"""
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from backend.database.models import EmploymentContract
        db = info.context["db"]
        
        stmt = select(EmploymentContract).options(
            selectinload(EmploymentContract.company),
            selectinload(EmploymentContract.position),
            selectinload(EmploymentContract.department)
        ).where(EmploymentContract.id == id)
        result = await db.execute(stmt)
        contract = result.scalar_one_or_none()
        
        if contract:
            return types.EmploymentContract.from_instance(contract)
        return None

    @strawberry.field
    async def active_time_log(self, info: strawberry.Info) -> Optional[types.TimeLog]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            return None
        db_log = await crud.get_active_time_log(db, current_user.id)
        if db_log:
            return types.TimeLog.from_instance(db_log)
        return None

    @strawberry.field
    async def users(
        self, 
        info: strawberry.Info, 
        skip: int = 0, 
        limit: int = 10, 
        search: Optional[str] = None, 
        sort_by: str = "id", 
        sort_order: str = "asc"
    ) -> types.PaginatedUsers:
        db = info.context["db"]
        current_user = info.context["current_user"]
        # Allow admin, super_admin, accountant, and manager
        allowed_roles = ["admin", "super_admin", "accountant", "manager"]
        if current_user is None or current_user.role.name not in allowed_roles:
            raise PermissionDeniedException()
        
        # Isolation: Non-super_admin sees only their company
        company_id = None
        if current_user.role.name != "super_admin":
            company_id = current_user.company_id

        db_users = await crud.get_users(db, skip=skip, limit=limit, search=search, sort_by=sort_by, sort_order=sort_order, company_id=company_id)
        total_count = await crud.count_users(db, search=search, company_id=company_id)
        
        return types.PaginatedUsers(
            users=[types.User.from_instance(user) for user in db_users],
            total_count=total_count or 0
        )

    @strawberry.field
    async def all_users(
        self, 
        info: strawberry.Info,
        search: Optional[str] = None
    ) -> List[types.User]:
        """Връща всички потребители като плосък списък (за старите компоненти)"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin", "accountant", "manager"]:
            raise PermissionDeniedException.for_action("view records")
            
        company_id = current_user.company_id if current_user.role.name != "super_admin" else None
        db_users = await crud.get_users(db, skip=0, limit=1000, search=search, company_id=company_id)
        return [types.User.from_instance(u) for u in db_users]

    @strawberry.field
    async def user(self, info: strawberry.Info, id: Optional[int] = None) -> Optional[types.User]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None:
            raise AuthenticationException()
            
        target_id = id if id is not None else current_user.id
        
        if current_user.role.name not in ["admin", "super_admin"] and current_user.id != target_id:
            raise PermissionDeniedException.for_action("access")
            
        db_user = await crud.get_user_by_id(db, target_id)
        if db_user:
            return types.User.from_instance(db_user)
        return None

    @strawberry.field
    async def roles(self, info: strawberry.Info) -> List[types.Role]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        allowed_roles = ["admin", "super_admin", "accountant", "manager"]
        if current_user is None or current_user.role.name not in allowed_roles:
            raise PermissionDeniedException.for_action("access roles")
        db_roles = await crud.get_roles(db)
        return [types.Role.from_instance(role) for role in db_roles]
    
    @strawberry.field
    async def kiosk_security_settings(self, info: strawberry.Info) -> types.KioskSecuritySettings:
        db = info.context["db"]
        current_user = info.context["current_user"]
        
        # Access check
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
             raise PermissionDeniedException.for_action("access")
             
        gps = await crud.get_global_setting(db, "kiosk_require_gps") != "false"
        net = await crud.get_global_setting(db, "kiosk_require_same_network") != "false"
        
        return types.KioskSecuritySettings(
            require_gps=gps,
            require_same_network=net
        )

    @strawberry.field
    async def google_calendar_account(self, info: strawberry.Info) -> Optional[types.GoogleCalendarAccount]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            return None
            
        from backend.database.models import GoogleCalendarAccount
        stmt = select(GoogleCalendarAccount).where(GoogleCalendarAccount.user_id == current_user.id)
        result = await db.execute(stmt)
        account = result.scalars().first()
        
        if account:
            return types.GoogleCalendarAccount(
                id=account.id,
                email=account.email,
                is_active=account.is_active,
                sync_settings=types.GoogleCalendarSyncSettings(
                    id=account.sync_settings.id,
                    calendar_id=account.sync_settings.calendar_id,
                    sync_work_schedules=account.sync_settings.sync_work_schedules,
                    sync_time_logs=account.sync_settings.sync_time_logs,
                    sync_leave_requests=account.sync_settings.sync_leave_requests,
                    sync_public_holidays=account.sync_settings.sync_public_holidays,
                    sync_direction=account.sync_settings.sync_direction,
                    sync_frequency_minutes=account.sync_settings.sync_frequency_minutes,
                    privacy_level=account.sync_settings.privacy_level
                ) if account.sync_settings else None
            )
        return None

    @strawberry.field
    async def payroll_legal_settings(self, info: strawberry.Info) -> types.PayrollLegalSettings:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
             raise PermissionDeniedException.for_action("access")
             
        max_ins = await crud.get_global_setting(db, "payroll_max_insurance_base")
        ins_rate = await crud.get_global_setting(db, "payroll_employee_insurance_rate")
        tax_rate = await crud.get_global_setting(db, "payroll_income_tax_rate")
        civil_costs = await crud.get_global_setting(db, "payroll_civil_contract_costs_rate")
        noi_perc = await crud.get_global_setting(db, "payroll_noi_compensation_percent")
        sick_days = await crud.get_global_setting(db, "payroll_employer_paid_sick_days")
        tax_res = await crud.get_global_setting(db, "payroll_default_tax_resident")
        strict_mode = await crud.get_global_setting(db, "trz_compliance_strict_mode")

        return types.PayrollLegalSettings(
            max_insurance_base=float(max_ins) if max_ins else 3750.0,
            employee_insurance_rate=float(ins_rate) if ins_rate else 13.78,
            income_tax_rate=float(tax_rate) if tax_rate else 10.0,
            civil_contract_costs_rate=float(civil_costs) if civil_costs else 25.0,
            noi_compensation_percent=float(noi_perc) if noi_perc else 80.0,
            employer_paid_sick_days=int(sick_days) if sick_days else 2,
            default_tax_resident=(tax_res.lower() == "true") if tax_res else True,
            trz_compliance_strict_mode=(strict_mode.lower() == "true") if strict_mode else False
        )

    @strawberry.field
    async def contract_templates(self, info: strawberry.Info) -> List[types.ContractTemplate]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")
        
        company_id = current_user.company_id if current_user.role.name != "super_admin" else None
        
        from backend.database.models import ContractTemplate
        stmt = select(ContractTemplate)
        if company_id:
            stmt = stmt.where(ContractTemplate.company_id == company_id)
        stmt = stmt.where(ContractTemplate.is_active == True).order_by(ContractTemplate.name)
        
        result = await db.execute(stmt)
        templates = result.scalars().all()
        return [types.ContractTemplate(
            id=t.id,
            company_id=t.company_id,
            name=t.name,
            description=t.description,
            contract_type=t.contract_type,
            work_hours_per_week=t.work_hours_per_week,
            probation_months=t.probation_months,
            salary_calculation_type=t.salary_calculation_type,
            payment_day=t.payment_day,
            night_work_rate=float(t.night_work_rate),
            overtime_rate=float(t.overtime_rate),
            holiday_rate=float(t.holiday_rate),
            work_class=t.work_class,
            is_active=t.is_active,
            created_at=t.created_at
        ) for t in templates]

    @strawberry.field
    async def contract_template(self, info: strawberry.Info, id: int) -> Optional[types.ContractTemplate]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")
        
        from backend.database.models import ContractTemplate
        template = await db.get(ContractTemplate, id)
        if not template:
            return None
        return types.ContractTemplate(
            id=template.id,
            company_id=template.company_id,
            name=template.name,
            description=template.description,
            contract_type=template.contract_type,
            work_hours_per_week=template.work_hours_per_week,
            probation_months=template.probation_months,
            salary_calculation_type=template.salary_calculation_type,
            payment_day=template.payment_day,
            night_work_rate=float(template.night_work_rate),
            overtime_rate=float(template.overtime_rate),
            holiday_rate=float(template.holiday_rate),
            work_class=template.work_class,
            is_active=template.is_active,
            created_at=template.created_at
        )

    @strawberry.field
    async def contract_template_versions(self, info: strawberry.Info, template_id: int) -> List[types.ContractTemplateVersion]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")
        
        from backend.database.models import ContractTemplateVersion
        stmt = select(ContractTemplateVersion).where(
            ContractTemplateVersion.template_id == template_id
        ).order_by(ContractTemplateVersion.version.desc())
        
        result = await db.execute(stmt)
        versions = result.scalars().all()
        return [types.ContractTemplateVersion(
            id=v.id,
            template_id=v.template_id,
            version=v.version,
            contract_type=v.contract_type,
            work_hours_per_week=v.work_hours_per_week,
            probation_months=v.probation_months,
            salary_calculation_type=v.salary_calculation_type,
            payment_day=v.payment_day,
            night_work_rate=float(v.night_work_rate),
            overtime_rate=float(v.overtime_rate),
            holiday_rate=float(v.holiday_rate),
            work_class=v.work_class,
            is_current=v.is_current,
            created_by=v.created_by,
            created_at=v.created_at,
            change_note=v.change_note
        ) for v in versions]

    @strawberry.field
    async def annex_templates(self, info: strawberry.Info) -> List[types.AnnexTemplate]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")
        
        company_id = current_user.company_id if current_user.role.name != "super_admin" else None
        
        from backend.database.models import AnnexTemplate
        stmt = select(AnnexTemplate)
        if company_id:
            stmt = stmt.where(AnnexTemplate.company_id == company_id)
        stmt = stmt.where(AnnexTemplate.is_active == True).order_by(AnnexTemplate.name)
        
        result = await db.execute(stmt)
        templates = result.scalars().all()
        return [types.AnnexTemplate(
            id=t.id,
            company_id=t.company_id,
            name=t.name,
            description=t.description,
            change_type=t.change_type,
            new_base_salary=float(t.new_base_salary) if t.new_base_salary else None,
            new_work_hours_per_week=t.new_work_hours_per_week,
            new_night_work_rate=float(t.new_night_work_rate) if t.new_night_work_rate else None,
            new_overtime_rate=float(t.new_overtime_rate) if t.new_overtime_rate else None,
            new_holiday_rate=float(t.new_holiday_rate) if t.new_holiday_rate else None,
            is_active=t.is_active,
            created_at=t.created_at
        ) for t in templates]

    @strawberry.field
    async def annex_template(self, info: strawberry.Info, id: int) -> Optional[types.AnnexTemplate]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise AuthenticationException(detail=authenticate_msg)
        
        from backend.database.models import AnnexTemplate
        template = await db.get(AnnexTemplate, id)
        if not template:
            return None
        return types.AnnexTemplate(
            id=template.id,
            company_id=template.company_id,
            name=template.name,
            description=template.description,
            change_type=template.change_type,
            new_base_salary=float(template.new_base_salary) if template.new_base_salary else None,
            new_work_hours_per_week=template.new_work_hours_per_week,
            new_night_work_rate=float(template.new_night_work_rate) if template.new_night_work_rate else None,
            new_overtime_rate=float(template.new_overtime_rate) if template.new_overtime_rate else None,
            new_holiday_rate=float(template.new_holiday_rate) if template.new_holiday_rate else None,
            is_active=template.is_active,
            created_at=template.created_at
        )

    @strawberry.field
    async def annex_template_versions(self, info: strawberry.Info, template_id: int) -> List[types.AnnexTemplateVersion]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise AuthenticationException(detail=authenticate_msg)
        
        from backend.database.models import AnnexTemplateVersion
        stmt = select(AnnexTemplateVersion).where(
            AnnexTemplateVersion.template_id == template_id
        ).order_by(AnnexTemplateVersion.version.desc())
        
        result = await db.execute(stmt)
        versions = result.scalars().all()
        return [types.AnnexTemplateVersion(
            id=v.id,
            template_id=v.template_id,
            version=v.version,
            change_type=v.change_type,
            new_base_salary=float(v.new_base_salary) if v.new_base_salary else None,
            new_work_hours_per_week=v.new_work_hours_per_week,
            new_night_work_rate=float(v.new_night_work_rate) if v.new_night_work_rate else None,
            new_overtime_rate=float(v.new_overtime_rate) if v.new_overtime_rate else None,
            new_holiday_rate=float(v.new_holiday_rate) if v.new_holiday_rate else None,
            is_current=v.is_current,
            created_by=v.created_by,
            created_at=v.created_at,
            change_note=v.change_note
        ) for v in versions]

    @strawberry.field
    async def clause_templates(self, info: strawberry.Info, category: Optional[str] = None) -> List[types.ClauseTemplate]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise AuthenticationException(detail=authenticate_msg)
        
        company_id = current_user.company_id if current_user.role.name != "super_admin" else None
        
        from backend.database.models import ClauseTemplate
        stmt = select(ClauseTemplate)
        if company_id:
            stmt = stmt.where(ClauseTemplate.company_id == company_id)
        if category:
            stmt = stmt.where(ClauseTemplate.category == category)
        stmt = stmt.where(ClauseTemplate.is_active == True).order_by(ClauseTemplate.title)
        
        result = await db.execute(stmt)
        templates = result.scalars().all()
        return [types.ClauseTemplate(
            id=t.id,
            company_id=t.company_id,
            title=t.title,
            content=t.content,
            category=t.category,
            is_active=t.is_active,
            created_at=t.created_at
        ) for t in templates]

    @strawberry.field
    async def annexes(self, info: strawberry.Info, status: Optional[str] = None) -> List[types.ContractAnnex]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise AuthenticationException(detail=authenticate_msg)
        
        from backend.database.models import ContractAnnex, EmploymentContract, User
        stmt = select(ContractAnnex).join(EmploymentContract).join(User)
        
        if current_user.role.name != "super_admin":
            stmt = stmt.where(User.company_id == current_user.company_id)
        
        if status:
            stmt = stmt.where(ContractAnnex.status == status)
        
        stmt = stmt.order_by(ContractAnnex.effective_date.desc())
        
        result = await db.execute(stmt)
        annexes = result.scalars().all()
        return [types.ContractAnnex.from_instance(a) for a in annexes]

    @strawberry.field
    async def payroll_summary(
        self, 
        info: strawberry.Info, 
        start_date: datetime.date, 
        end_date: datetime.date,
        user_ids: Optional[List[int]] = None
    ) -> List[types.PayrollSummaryItem]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("view records")
            
        from backend.database.models import (
            User, EmploymentContract, PayrollDeduction, SickLeaveRecord, 
            NOIPaymentDays, AdvancePayment, ServiceLoan, PayrollPaymentSchedule
        )
        from backend.services.enhanced_payroll_calculator import EnhancedPayrollCalculator
        
        # 1. Fetch Users
        stmt = select(User).where(User.is_active == True)
        
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
        schedule_stmt = select(PayrollPaymentSchedule).where(PayrollPaymentSchedule.active == True)
        deductions_stmt = select(PayrollDeduction).where(PayrollDeduction.is_active == True)
        
        if company_id:
            schedule_stmt = schedule_stmt.where(PayrollPaymentSchedule.company_id == company_id)
            deductions_stmt = deductions_stmt.where(PayrollDeduction.company_id == company_id)
        
        # B) User-specific records
        from sqlalchemy.orm import selectinload
        contracts_stmt = select(EmploymentContract).options(
            selectinload(EmploymentContract.user)
        ).where(EmploymentContract.user_id.in_(target_ids), EmploymentContract.is_active == True)
        sick_stmt = select(SickLeaveRecord).where(SickLeaveRecord.user_id.in_(target_ids), SickLeaveRecord.start_date >= start_date, SickLeaveRecord.end_date <= end_date)
        advances_stmt = select(AdvancePayment).where(AdvancePayment.user_id.in_(target_ids), AdvancePayment.payment_date >= start_date, AdvancePayment.payment_date <= end_date, AdvancePayment.is_processed == False)
        loans_stmt = select(ServiceLoan).where(ServiceLoan.user_id.in_(target_ids), ServiceLoan.is_active == True, ServiceLoan.remaining_amount > 0)
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
            'payment_schedule': schedule_res,
            'deductions': deductions,
            'contracts': contracts,
            'sick_records': sick_records,
            'advances': advances,
            'loans': loans,
            'noi_days': noi_days
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
                    gross_amount=data['gross_amount'],
                    net_amount=data['net_amount'],
                    tax_amount=data['tax_amount'],
                    insurance_amount=data['insurance_amount'],
                    bonus_amount=data['bonus_amount'],
                    advances=data['advances'],
                    loan_deductions=data['loan_deductions'],
                    total_deductions=data['total_deductions'],
                    net_payable=data['net_payable'],
                    contract_type=data['contract_type'],
                    installments=types.SalaryInstallments(
                        count=data['installments']['count'],
                        amount_per_installment=data['installments']['amount_per_installment']
                    )
                ))
            except Exception as e:
                print(f"Error calculating payroll for user {user.id}: {e}")
                continue
                
        return summary

    @strawberry.field
    async def role(self, id: int, info: strawberry.Info) -> Optional[types.Role]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("view records")
        db_role = await crud.get_role_by_id(db, id)
        if db_role:
            return types.Role.from_instance(db_role)
        return None

    @strawberry.field
    async def shifts(self, info: strawberry.Info) -> List[types.Shift]:
        db = info.context["db"]
        db_shifts = await crud.get_shifts(db)
        return [types.Shift.from_instance(s) for s in db_shifts]

    @strawberry.field
    async def my_schedules(
        self,
        start_date: datetime.date,
        end_date: datetime.date,
        info: strawberry.Info
    ) -> List[types.WorkSchedule]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            return []
        
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from backend.database.models import WorkSchedule
        
        result = await db.execute(
            select(WorkSchedule)
            .where(WorkSchedule.user_id == current_user.id)
            .where(WorkSchedule.date >= start_date)
            .where(WorkSchedule.date <= end_date)
            .options(selectinload(WorkSchedule.shift))
        )
        return [types.WorkSchedule.from_instance(s) for s in result.scalars().all()]

    @strawberry.field
    async def work_schedules(
        self, 
        info: strawberry.Info, 
        start_date: datetime.date, 
        end_date: datetime.date, 
    ) -> List[types.WorkSchedule]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        
        company_id = None
        if current_user and current_user.role.name != "super_admin":
            company_id = current_user.company_id
            
        res = await crud.get_schedules_by_period(db, start_date, end_date, company_id=company_id)
        return [types.WorkSchedule.from_instance(s) for s in res]

    @strawberry.field
    async def time_logs(
        self,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
        info: strawberry.Info
    ) -> List[types.TimeLog]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("view records")
        
        # Convert aware to naive UTC to match DB TIMESTAMP WITHOUT TIME ZONE
        query_start = start_date
        if query_start.tzinfo is not None:
            query_start = query_start.astimezone(datetime.timezone.utc).replace(tzinfo=None)
            
        query_end = end_date
        if query_end.tzinfo is not None:
            query_end = query_end.astimezone(datetime.timezone.utc).replace(tzinfo=None)
        
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from backend.database.models import TimeLog, User
        
        stmt = select(TimeLog).where(TimeLog.start_time >= query_start).where(TimeLog.start_time <= query_end)
        
        # Isolation: Non-super_admin sees only their company's logs
        if current_user.role.name != "super_admin":
            stmt = stmt.join(User).where(User.company_id == current_user.company_id)
            
        result = await db.execute(stmt.options(selectinload(TimeLog.user)))
        logs = result.scalars().all()
        return [types.TimeLog.from_instance(l) for l in logs]

    @strawberry.field
    async def my_leave_requests(self, info: strawberry.Info) -> List[types.LeaveRequest]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            return []
        
        reqs = await crud.get_leave_requests(db, user_id=current_user.id)
        return [types.LeaveRequest.from_instance(r) for r in reqs]

    @strawberry.field
    async def pending_leave_requests(self, info: strawberry.Info) -> List[types.LeaveRequest]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("view records")
            
        reqs = await crud.get_leave_requests(db, status="pending")
        return [types.LeaveRequest.from_instance(r) for r in reqs]

    @strawberry.field
    async def all_leave_requests(self, info: strawberry.Info, status: Optional[str] = None) -> List[types.LeaveRequest]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("view records")
            
        reqs = await crud.get_leave_requests(db, status=status)
        return [types.LeaveRequest.from_instance(r) for r in reqs]

    @strawberry.field
    async def leave_balance(self, user_id: int, year: int, info: strawberry.Info) -> types.LeaveBalance:
        db = info.context["db"]
        current_user = info.context["current_user"]
        
        if current_user is None:
             raise AuthenticationException(detail=authenticate_msg)
             
        if current_user.id != user_id and current_user.role.name not in ["admin", "super_admin"]:
             raise PermissionDeniedException.for_action("view records")
             
        balance = await crud.get_leave_balance(db, user_id, year)
        return types.LeaveBalance.from_instance(balance)

    @strawberry.field
    async def companies(self, info: strawberry.Info) -> List[types.Company]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)
        
        res = await crud.get_companies(db)
        return [types.Company.from_instance(c) for c in res]

    @strawberry.field
    async def departments(self, info: strawberry.Info, company_id: Optional[int] = None) -> List[types.Department]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)
            
        res = await crud.get_departments(db, company_id)
        return [types.Department.from_instance(d) for d in res]

    @strawberry.field
    async def positions(self, info: strawberry.Info, department_id: Optional[int] = None) -> List[types.Position]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)
            
        res = await crud.get_positions(db, department_id)
        return [types.Position.from_instance(p) for p in res]

    @strawberry.field
    async def public_holidays(self, info: strawberry.Info, year: Optional[int] = None) -> List[types.PublicHoliday]:
        db = info.context["db"]
        from sqlalchemy import select, extract
        from backend.database.models import PublicHoliday
        
        stmt = select(PublicHoliday)
        if year:
            stmt = stmt.where(extract('year', PublicHoliday.date) == year)
        
        result = await db.execute(stmt)
        return [types.PublicHoliday.from_instance(h) for h in result.scalars().all()]

    @strawberry.field
    async def orthodox_holidays(self, info: strawberry.Info, year: Optional[int] = None) -> List[types.OrthodoxHoliday]:
        db = info.context["db"]
        from sqlalchemy import select, extract
        from backend.database.models import OrthodoxHoliday
        
        stmt = select(OrthodoxHoliday)
        if year:
            stmt = stmt.where(extract('year', OrthodoxHoliday.date) == year)
        
        result = await db.execute(stmt)
        return [types.OrthodoxHoliday.from_instance(h) for h in result.scalars().all()]

    @strawberry.field
    async def user_presences(
        self,
        info: strawberry.Info,
        date: datetime.date,
        status: Optional[types.PresenceStatus] = None
    ) -> List[types.UserPresence]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("view records")

        from sqlalchemy import select, and_
        from sqlalchemy.orm import selectinload
        from backend.database.models import User, TimeLog, WorkSchedule, LeaveRequest, sofia_now
        
        # 1. Fetch all active users from the current company only
        users_result = await db.execute(
            select(User).where(
                User.is_active == True,
                User.company_id == current_user.company_id
            )
        )
        users = users_result.scalars().all()
        
        # 2. Fetch all schedules for the date
        schedules_result = await db.execute(
            select(WorkSchedule)
            .where(WorkSchedule.date == date)
            .options(selectinload(WorkSchedule.shift))
        )
        schedules_map = {s.user_id: s for s in schedules_result.scalars().all()}
        
        # 3. Fetch logs
        start_dt = datetime.datetime.combine(date, datetime.time.min)
        end_dt = datetime.datetime.combine(date, datetime.time.max)
        
        logs_result = await db.execute(
            select(TimeLog)
            .where(and_(TimeLog.start_time >= start_dt, TimeLog.start_time <= end_dt))
            .order_by(TimeLog.start_time.asc())
        )
        user_logs = {}
        for log in logs_result.scalars().all():
            if log.user_id not in user_logs: user_logs[log.user_id] = []
            user_logs[log.user_id].append(log)

        # 4. Fetch Approved Leaves for the date
        leaves_result = await db.execute(
            select(LeaveRequest)
            .where(LeaveRequest.status == "approved")
            .where(LeaveRequest.start_date <= date)
            .where(LeaveRequest.end_date >= date)
        )
        leaves_map = {l.user_id: l for l in leaves_result.scalars().all()}

        results = []
        now = sofia_now()
        is_today = (date == now.date())
        current_time = now.time() if is_today else datetime.time(23, 59, 59)

        for u in users:
            schedule = schedules_map.get(u.id)
            logs = user_logs.get(u.id, [])
            leave = leaves_map.get(u.id)

            shift_start = None
            shift_end = None
            
            # --- Determine Status ---
            p_status = types.PresenceStatus.OFF_DUTY # Default
            
            # 1. Determine Shift Times (needed for UI even if logs exist)
            if schedule and schedule.shift:
                shift_start = schedule.shift.start_time
                shift_end = schedule.shift.end_time

            # 2. Check Active Presence (Highest Priority)
            is_present = False
            has_logs = bool(logs)
            
            if has_logs:
                last_log = logs[-1]
                if last_log.end_time is None:
                    p_status = types.PresenceStatus.ON_DUTY
                    is_present = True
                else:
                    p_status = types.PresenceStatus.OFF_DUTY # Finished work

            # 3. Check Leave (If NOT present)
            # We assume if someone comes to work, they are ON_DUTY even if they had a leave booked (overtime/emergency)
            if not is_present and leave:
                if leave.leave_type == "sick_leave":
                    p_status = types.PresenceStatus.SICK_LEAVE
                else:
                    # Covers paid_leave and others for now
                    p_status = types.PresenceStatus.PAID_LEAVE
            
            # 4. Check Schedule Logic (If NOT present and NOT on leave)
            if not is_present and not leave:
                if schedule and schedule.shift:
                    if is_today and shift_start and shift_end:
                        if current_time < shift_start:
                             p_status = types.PresenceStatus.OFF_DUTY # Waiting for start
                        elif current_time >= shift_start and current_time <= shift_end:
                             # Shift started, user not here -> LATE
                             # Requirement: Activate immediately after start if not marked for entry
                             p_status = types.PresenceStatus.LATE
                        elif current_time > shift_end:
                             # Shift ended, user never came -> ABSENT
                             # Requirement: Status ABSENT stays if shift exists but not marked for entry
                             # Requirement: Add status 'not at work' (OFF_DUTY) if it is after end of working day? 
                             # Interpretation: If they missed the WHOLE shift, it's ABSENT. 
                             # If they worked and left, it's OFF_DUTY (handled in step 2).
                             p_status = types.PresenceStatus.ABSENT
                    else:
                        # Past date
                        # If shift existed and no logs -> ABSENT
                        p_status = types.PresenceStatus.ABSENT
                else:
                    # No schedule, no logs, no leave
                    p_status = types.PresenceStatus.OFF_DUTY

            # Map Data
            first_log = logs[0] if logs else None
            last_log = logs[-1] if logs else None
            actual_arrival = first_log.start_time if first_log else None
            actual_departure = last_log.end_time if last_log else None
            is_on_duty = bool(last_log and last_log.end_time is None)

            if status and p_status != status:
                continue
                
            results.append(types.UserPresence(
                user=types.User.from_instance(u),
                shift_start=shift_start,
                shift_end=shift_end,
                actual_arrival=actual_arrival,
                actual_departure=actual_departure,
                status=p_status,
                is_on_duty=is_on_duty
            ))
            
        return results

    @strawberry.field
    async def smtp_settings(self, info: strawberry.Info) -> Optional[types.SmtpSettings]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
             raise PermissionDeniedException.for_action("view records")

        server = await crud.get_global_setting(db, "smtp_server")
        port = await crud.get_global_setting(db, "smtp_port")
        username = await crud.get_global_setting(db, "smtp_username")
        # Don't return the real password for security, or return it if necessary for editing
        # Usually better to leave blank and only update if provided.
        # But for this simple app, we might return it or a placeholder.
        password = await crud.get_global_setting(db, "smtp_password") 
        sender = await crud.get_global_setting(db, "sender_email")
        tls = await crud.get_global_setting(db, "use_tls")

        if not server:
            return None

        return types.SmtpSettings(
            smtp_server=server,
            smtp_port=int(port) if port else 587,
            smtp_username=username or "",
            smtp_password=password or "",
            sender_email=sender or "",
            use_tls=tls == "True"
        )

    @strawberry.field
    async def notification_settings(self, info: strawberry.Info, company_id: int) -> List[types.NotificationSetting]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("view records")

        from backend.database.models import NotificationSetting
        stmt = select(NotificationSetting).where(NotificationSetting.company_id == company_id)
        res = await db.execute(stmt)
        return [types.NotificationSetting.from_instance(s) for s in res.scalars().all()]

    @strawberry.field
    async def notification_setting(self, info: strawberry.Info, event_type: str, company_id: int) -> Optional[types.NotificationSetting]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("view records")

        from backend.database.models import NotificationSetting
        stmt = select(NotificationSetting).where(
            NotificationSetting.event_type == event_type,
            NotificationSetting.company_id == company_id
        )
        res = await db.execute(stmt)
        setting = res.scalars().first()
        return types.NotificationSetting.from_instance(setting) if setting else None

    @strawberry.field
    async def user_daily_stats(
        self,
        info: strawberry.Info,
        user_id: int,
        start_date: datetime.date,
        end_date: datetime.date
    ) -> List[types.DailyStat]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
             raise PermissionDeniedException.for_action("view records")

        from backend.services.payroll_calculator import PayrollCalculator
        calculator = PayrollCalculator(db)
        
        stats = await calculator.get_daily_stats(user_id, start_date, end_date)
        
        return [
            types.DailyStat(
                date=s["date"],
                total_worked_hours=s["total_worked_hours"],
                regular_hours=s["regular_hours"],
                overtime_hours=s["overtime_hours"],
                is_work_day=s["is_work_day"],
                shift_name=s["shift_name"],
                actual_arrival=s.get("actual_arrival"),
                actual_departure=s.get("actual_departure")
            )
            for s in stats
        ]

    @strawberry.field
    async def my_daily_stats(
        self,
        info: strawberry.Info,
        start_date: datetime.date,
        end_date: datetime.date
    ) -> List[types.DailyStat]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
             return []

        from backend.services.payroll_calculator import PayrollCalculator
        calculator = PayrollCalculator(db)
        
        stats = await calculator.get_daily_stats(current_user.id, start_date, end_date)
        
        return [
            types.DailyStat(
                date=s["date"],
                total_worked_hours=s["total_worked_hours"],
                regular_hours=s["regular_hours"],
                overtime_hours=s["overtime_hours"],
                is_work_day=s["is_work_day"],
                shift_name=s["shift_name"],
                actual_arrival=s.get("actual_arrival"),
                actual_departure=s.get("actual_departure")
            )
            for s in stats
        ]

    @strawberry.field
    async def office_location(self, info: strawberry.Info) -> Optional[types.OfficeLocation]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        # Allow any user to see office location (needed for client-side checks if we want)
        # But usually client just sends coords and backend validates.
        # Let's restrict to admin for editing, but maybe exposure is fine?
        # For now, let's keep it open or at least for authenticated users.
        if not current_user:
             return None

        lat = await crud.get_global_setting(db, "office_latitude")
        lon = await crud.get_global_setting(db, "office_longitude")
        rad = await crud.get_global_setting(db, "office_radius")
        entry_enabled = await crud.get_global_setting(db, "geofencing_entry_enabled")
        exit_enabled = await crud.get_global_setting(db, "geofencing_exit_enabled")
        
        if not lat or not lon:
            return None
            
        return types.OfficeLocation(
            latitude=float(lat),
            longitude=float(lon),
            radius=int(rad) if rad else 100,
            entry_enabled=(entry_enabled == "True"),
            exit_enabled=(exit_enabled == "True")
        )

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
            qr_regen_interval_minutes=settings.QR_TOKEN_REGEN_MINUTES
        )

    @strawberry.field
    async def weekly_summary(
        self, 
        info: strawberry.Info, 
        date: Optional[datetime.date] = None,
        user_id: Optional[int] = None
    ) -> Optional[types.WeeklySummary]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
             return None
        
        target_user_id = current_user.id
        if user_id:
            if current_user.role.name not in ["admin", "super_admin"] and current_user.id != user_id:
                raise PermissionDeniedException.for_action("view weekly summary")
            target_user_id = user_id
            
        ref_date = date if date else datetime.datetime.now().date()
        
        from backend.services.payroll_calculator import PayrollCalculator
        calculator = PayrollCalculator(db)
        
        config = await crud.get_payroll_config(db, target_user_id)
        # Calculate weekly target based on daily standard hours * 5 (work week)
        # If no config, default to 8 hours/day * 5 = 40
        daily_hours = config.standard_hours_per_day if config and config.standard_hours_per_day else 8
        target = float(daily_hours * 5)
        
        summary = await calculator.get_weekly_summary(target_user_id, ref_date, target)
        
        return types.WeeklySummary(
            start_date=summary["start_date"],
            end_date=summary["end_date"],
            total_regular_hours=Decimal(str(summary["total_regular_hours"])),
            total_overtime_hours=Decimal(str(summary["total_overtime_hours"])),
            target_hours=Decimal(str(summary["target_hours"])),
            debt_hours=Decimal(str(summary["debt_hours"])),
            surplus_hours=Decimal(str(summary["surplus_hours"])),
            status_message=summary["status_message"]
        )

    @strawberry.field
    async def monthly_work_days(
        self,
        info: strawberry.Info,
        year: int,
        month: int
    ) -> Optional[types.MonthlyWorkDays]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
             return None
        
        # Any authenticated user should be able to see work days to calculate their own salary expectations
        # But for editing, only admin (handled in mutation)
        
        res = await crud.get_monthly_work_days(db, year, month)
        if res:
            return types.MonthlyWorkDays.from_instance(res)
        return None

    @strawberry.field
    async def active_sessions(self, info: strawberry.Info, skip: int = 0, limit: int = 100) -> List[types.UserSession]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("view active sessions")
        
        sessions = await crud.get_active_sessions(db, skip=skip, limit=limit)
        return [types.UserSession.from_instance(s) for s in sessions]

    @strawberry.field
    async def audit_logs(
        self, 
        info: strawberry.Info, 
        skip: int = 0, 
        limit: int = 100,
        action: Optional[str] = None
    ) -> List[types.AuditLog]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("view audit logs")
        
        from sqlalchemy import select, desc
        from backend.database.models import AuditLog as DbAuditLog, User
        
        stmt = select(DbAuditLog).join(User, DbAuditLog.user_id == User.id).order_by(desc(DbAuditLog.created_at))
        stmt = stmt.where(User.company_id == current_user.company_id)
        if action:
            stmt = stmt.where(DbAuditLog.action == action)
            
        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        return [types.AuditLog.from_instance(log) for log in result.scalars().all()]

    @strawberry.field
    async def my_swap_requests(self, info: strawberry.Info) -> List[types.ShiftSwapRequest]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
             return []
        res = await crud.get_my_swap_requests(db, current_user.id)
        return [types.ShiftSwapRequest.from_instance(s) for s in res]

    @strawberry.field
    async def pending_admin_swaps(self, info: strawberry.Info) -> List[types.ShiftSwapRequest]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("view swap requests")
        res = await crud.get_all_pending_swaps(db)
        return [types.ShiftSwapRequest.from_instance(s) for s in res]

    @strawberry.field
    async def management_stats(self, info: strawberry.Info) -> types.ManagementStats:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("view management stats")   

        from sqlalchemy import func
        from backend.database.models import Payslip, TimeLog, WorkSchedule, Shift, User
        
        # 1. Overtime by Month (last 12 months)
        # We group payslips by year and month
        stmt_ot = select(
            func.to_char(Payslip.period_start, 'YYYY-MM').label('month'),
            func.sum(Payslip.overtime_amount).label('total_ot')
        ).group_by('month').order_by('month').limit(12)
        
        res_ot = await db.execute(stmt_ot)
        overtime_data = [
            types.OvertimeStat(month=row[0], amount=Decimal(str(row[1])))
            for row in res_ot.all()
        ]

        # 2. Lateness by User (Top 10)
        # Logic: start_time > shift.start_time (with tolerance)
        # For simplicity, we'll look at the last 30 days
        cutoff = datetime.datetime.now() - datetime.timedelta(days=30)
        
        stmt_late = select(
            User.first_name,
            User.last_name,
            func.count(TimeLog.id).label('late_count')
        ).join(TimeLog, User.id == TimeLog.user_id).join(
            WorkSchedule, (User.id == WorkSchedule.user_id) & (func.date(TimeLog.start_time) == WorkSchedule.date)
        ).join(
            Shift, WorkSchedule.shift_id == Shift.id
        ).where(
            TimeLog.start_time > cutoff,
            # Extract time and compare. This is DB specific, using func for postgres
            func.cast(TimeLog.start_time, Time) > Shift.start_time
        ).group_by(User.id).order_by(desc('late_count')).limit(10)

        res_late = await db.execute(stmt_late)
        lateness_data = [
            types.LatenessStat(user_name=f"{row[0]} {row[1]}", count=row[2])
            for row in res_late.all()
        ]

        return types.ManagementStats(
            overtime_by_month=overtime_data,
            lateness_by_user=lateness_data
        )

    @strawberry.field
    async def schedule_templates(self, info: strawberry.Info) -> List[types.ScheduleTemplate]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("view schedule templates")
        res = await crud.get_schedule_templates(db, company_id=current_user.company_id)
        return [types.ScheduleTemplate.from_instance(t) for t in res]

    @strawberry.field
    async def schedule_template(self, info: strawberry.Info, id: int) -> Optional[types.ScheduleTemplate]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("view schedule template")
        res = await crud.get_schedule_template(db, id, company_id=current_user.company_id)
        if res and res.company_id != current_user.company_id:
            return None
        return types.ScheduleTemplate.from_instance(res) if res else None

    @strawberry.field
    async def vapid_public_key(self, info: strawberry.Info) -> Optional[str]:
        db = info.context["db"]
        if not info.context["current_user"]:
             return None
        return await crud.get_global_setting(db, "vapid_public_key")

    @strawberry.field
    async def payroll_forecast(self, info: strawberry.Info, year: int, month: int) -> types.PayrollForecast:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("view payroll forecast")
        
        # 1. Get All Active Users
        users = await crud.get_users(db, limit=1000)
        
        total = 0.0
        dept_map = {}
        
        calc = PayrollCalculator(db)
        
        for u in users:
            if not u.is_active: continue
            
            amount = await calc.calculate_forecast(u.id, year, month)
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
    async def api_keys(self, info: strawberry.Info) -> List[types.APIKey]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("view API keys")
        
        res = await crud.get_api_keys(db)
        return [types.APIKey.from_instance(k) for k in res]

    @strawberry.field
    async def webhooks(self, info: strawberry.Info) -> List[types.Webhook]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("view webhooks")   
        
        res = await crud.get_webhooks(db)
        return [types.Webhook.from_instance(w) for w in res]

    @strawberry.field
    async def modules(self, info: strawberry.Info) -> List[types.Module]:
        db = info.context["db"]
        # Public query - no auth required (used for login page to show module status)
        from backend.services.module_service import ModuleService
        res = await ModuleService.get_all_modules(db)
        return [types.Module.from_instance(m) for m in res]

    @strawberry.field
    async def password_settings(self, info: strawberry.Info) -> types.PasswordSettings:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name != "super_admin":
            raise PermissionDeniedException.for_action("view password settings")
            
        return types.PasswordSettings(
            min_length=int(await crud.get_global_setting(db, "pwd_min_length") or "8"),
            max_length=int(await crud.get_global_setting(db, "pwd_max_length") or "32"),
            require_upper=(await crud.get_global_setting(db, "pwd_require_upper")) == "true",
            require_lower=(await crud.get_global_setting(db, "pwd_require_lower")) == "true",
            require_digit=(await crud.get_global_setting(db, "pwd_require_digit")) == "true",
            require_special=(await crud.get_global_setting(db, "pwd_require_special")) == "true"
        )

    # --- Confectionery Module Queries ---

    @strawberry.field
    async def storage_zones(self, info: strawberry.Info) -> List[types.StorageZone]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)
        
        from backend.database.models import StorageZone
        stmt = select(StorageZone)
        if current_user.role.name != "super_admin":
            stmt = stmt.where(StorageZone.company_id == current_user.company_id)
        
        res = await db.execute(stmt)
        return [types.StorageZone.from_instance(z) for z in res.scalars().all()]

    @strawberry.field
    async def suppliers(self, info: strawberry.Info) -> List[types.Supplier]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)
        
        from backend.database.models import Supplier
        stmt = select(Supplier)
        if current_user.role.name != "super_admin":
            stmt = stmt.where(Supplier.company_id == current_user.company_id)
        
        res = await db.execute(stmt)
        return [types.Supplier.from_instance(s) for s in res.scalars().all()]

    @strawberry.field
    async def ingredients(self, info: strawberry.Info, search: Optional[str] = None) -> List[types.Ingredient]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)
        
        from backend.database.models import Ingredient
        stmt = select(Ingredient)
        if current_user.role.name != "super_admin":
            stmt = stmt.where(Ingredient.company_id == current_user.company_id)
        
        if search:
            stmt = stmt.where(Ingredient.name.ilike(f"%{search}%"))
            
        res = await db.execute(stmt)
        return [types.Ingredient.from_instance(i) for i in res.scalars().all()]

    @strawberry.field
    async def batches(
        self, 
        info: strawberry.Info, 
        ingredient_id: Optional[int] = None,
        status: Optional[str] = "active"
    ) -> List[types.Batch]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)
        
        from backend.database.models import Batch, Ingredient
        stmt = select(Batch).join(Ingredient)
        
        if current_user.role.name != "super_admin":
            stmt = stmt.where(Ingredient.company_id == current_user.company_id)
            
        if ingredient_id:
            stmt = stmt.where(Batch.ingredient_id == ingredient_id)
        if status:
            stmt = stmt.where(Batch.status == status)
        stmt = stmt.order_by(Batch.expiry_date.asc()) # FEFO logic
        res = await db.execute(stmt)
        return [types.Batch.from_instance(b) for b in res.scalars().all()]

    @strawberry.field
    async def get_fefo_suggestion(
        self,
        ingredient_id: int,
        quantity: Decimal,
        info: strawberry.Info
    ) -> List[types.FefoSuggestion]:
        """Предложение за изразходване по FEFO"""
        db = info.context["db"]
        from backend.database.models import Batch
        from sqlalchemy import select
        import datetime

        stmt = select(Batch).where(
            Batch.ingredient_id == ingredient_id,
            Batch.status == "active",
            Batch.quantity > 0
        ).order_by(Batch.expiry_date.asc())
        
        result = await db.execute(stmt)
        batches = result.scalars().all()
        
        suggestions = []
        remaining = quantity
        today = datetime.date.today()

        for batch in batches:
            if remaining <= 0: break
            
            to_take = min(batch.quantity, remaining)
            suggestions.append(types.FefoSuggestion(
                batch_id=batch.id,
                batch_number=batch.batch_number or f"ID-{batch.id}",
                available_quantity=batch.quantity,
                quantity_to_take=to_take,
                expiry_date=batch.expiry_date,
                days_until_expiry=(batch.expiry_date - today).days
            ))
            remaining -= to_take
            
        return suggestions

    @strawberry.field
    async def stock_consumption_logs(
        self,
        info: strawberry.Info,
        ingredient_id: Optional[int] = None,
        batch_id: Optional[int] = None,
        start_date: Optional[datetime.date] = None,
        end_date: Optional[datetime.date] = None
    ) -> List[types.StockConsumptionLog]:
        """История на изразходването на стока"""
        db = info.context["db"]
        from backend.database.models import StockConsumptionLog
        from sqlalchemy import select, desc
        stmt = select(StockConsumptionLog)
        
        if ingredient_id:
            stmt = stmt.where(StockConsumptionLog.ingredient_id == ingredient_id)
        if batch_id:
            stmt = stmt.where(StockConsumptionLog.batch_id == batch_id)
        if start_date:
            stmt = stmt.where(StockConsumptionLog.created_at >= start_date)
        if end_date:
            stmt = stmt.where(StockConsumptionLog.created_at <= end_date)
        stmt = stmt.order_by(desc(StockConsumptionLog.created_at))
        result = await db.execute(stmt)
        logs = result.scalars().all()
        return [types.StockConsumptionLog.from_instance(l) for l in logs]

    @strawberry.field
    async def ingredient_batches_with_stock(
        self,
        info: strawberry.Info,
        ingredient_id: int
    ) -> List[types.Batch]:
        """Get active batches with available stock for a specific ingredient"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)
        
        from backend.database.models import Batch, Ingredient
        stmt = select(Batch).join(Ingredient).where(
            Batch.ingredient_id == ingredient_id,
            Batch.status == "active",
            Batch.quantity > 0
        )
        
        if current_user.role.name != "super_admin":
            stmt = stmt.where(Ingredient.company_id == current_user.company_id)
        
        stmt = stmt.order_by(Batch.expiry_date.asc())  # FEFO - earliest expiry first
        
        res = await db.execute(stmt)
        return [types.Batch.from_instance(b) for b in res.scalars().all()]

    @strawberry.field
    async def recipes(self, info: strawberry.Info) -> List[types.Recipe]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)
        
        from backend.database.models import Recipe
        stmt = select(Recipe)
        if current_user.role.name != "super_admin":
            stmt = stmt.where(Recipe.company_id == current_user.company_id)
            
        res = await db.execute(stmt)
        return [types.Recipe.from_instance(r) for r in res.scalars().all()]

    @strawberry.field
    async def recipes_with_prices(
        self,
        info: strawberry.Info,
        category_id: Optional[int] = None
    ) -> List[types.Recipe]:
        """Всички рецепти с цени"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)
        
        from backend.database.models import Recipe
        stmt = select(Recipe)
        if current_user.role.name != "super_admin":
            stmt = stmt.where(Recipe.company_id == current_user.company_id)
        
        if category_id:
            stmt = stmt.where(Recipe.category_id == category_id)
        
        res = await db.execute(stmt)
        return [types.Recipe.from_instance(r) for r in res.scalars().all()]

    @strawberry.field
    async def price_history(
        self,
        info: strawberry.Info,
        recipe_id: int,
        limit: int = 20
    ) -> List[types.PriceHistory]:
        """История на промените на цената"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)
        
        from backend.database.models import PriceHistory, Recipe
        from sqlalchemy import desc
        
        recipe = await db.get(Recipe, recipe_id)
        if not recipe or recipe.company_id != current_user.company_id:
            raise NotFoundException.record("Recipe")
        
        stmt = select(PriceHistory).where(
            PriceHistory.recipe_id == recipe_id
        ).order_by(desc(PriceHistory.changed_at)).limit(limit)
        
        res = await db.execute(stmt)
        return [types.PriceHistory.from_instance(h) for h in res.scalars().all()]

    @strawberry.field
    async def workstations(self, info: strawberry.Info) -> List[types.Workstation]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)
        
        from backend.database.models import Workstation
        stmt = select(Workstation)
        if current_user.role.name != "super_admin":
            stmt = stmt.where(Workstation.company_id == current_user.company_id)
            
        res = await db.execute(stmt)
        return [types.Workstation.from_instance(w) for w in res.scalars().all()]

    @strawberry.field
    async def production_orders(self, info: strawberry.Info, status: Optional[str] = None) -> List[types.ProductionOrder]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)
        
        from backend.database.models import ProductionOrder
        stmt = select(ProductionOrder)
        if current_user.role.name != "super_admin":
            stmt = stmt.where(ProductionOrder.company_id == current_user.company_id)
            
        if status:
            stmt = stmt.where(ProductionOrder.status == status)
            
        stmt = stmt.order_by(ProductionOrder.due_date.asc())
        
        res = await db.execute(stmt)
        return [types.ProductionOrder.from_instance(o) for o in res.scalars().all()]

    @strawberry.field
    async def terminal_orders(self, info: strawberry.Info, workstation_id: int) -> List[types.TerminalOrder]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)
        
        from backend.database.models import ProductionOrder, ProductionTask, Recipe
        stmt = select(ProductionOrder).where(
            ProductionOrder.status.in_(["in_progress", "ready", "pending"])
        )
        
        if current_user.role.name != "super_admin":
            stmt = stmt.where(ProductionOrder.company_id == current_user.company_id)
        
        stmt = stmt.order_by(ProductionOrder.created_at.desc()).limit(50)
        
        res = await db.execute(stmt)
        orders = []
        
        for order in res.scalars().all():
            recipe = await db.get(Recipe, order.recipe_id) if order.recipe_id else None
            
            task_stmt = select(ProductionTask).where(
                ProductionTask.order_id == order.id,
                ProductionTask.workstation_id == workstation_id,
                ProductionTask.status.in_(["pending", "in_progress"])
            )
            task_res = await db.execute(task_stmt)
            order_qty = int(order.quantity) if order.quantity else 0
            tasks = [types.TerminalTask.from_instance(t, order_qty) for t in task_res.scalars().all()]
            
            if tasks:
                orders.append(types.TerminalOrder.from_instance(
                    order,
                    recipe_name=recipe.name if recipe else "Unknown",
                    instructions=recipe.instructions if recipe else None,
                    tasks=tasks
                ))
        
        return orders

    @strawberry.field
    async def production_records(self, info: strawberry.Info, order_id: Optional[int] = None) -> List[types.ProductionRecord]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)
        
        from backend.database.models import ProductionRecord
        stmt = select(ProductionRecord)
        if current_user.role.name != "super_admin":
            # Join with ProductionOrder to filter by company
            from backend.database.models import ProductionOrder
            stmt = stmt.join(ProductionOrder).where(ProductionOrder.company_id == current_user.company_id)
            
        if order_id:
            stmt = stmt.where(ProductionRecord.order_id == order_id)
        
        stmt = stmt.order_by(ProductionRecord.confirmed_at.desc())
        
        res = await db.execute(stmt)
        return [types.ProductionRecord.from_instance(r) for r in res.scalars().all()]

    @strawberry.field
    async def production_record_by_order(self, order_id: int, info: strawberry.Info) -> Optional[types.ProductionRecord]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)
        
        from backend.database.models import ProductionRecord, ProductionOrder
        stmt = select(ProductionRecord).where(ProductionRecord.order_id == order_id)
        
        if current_user.role.name != "super_admin":
            stmt = stmt.join(ProductionOrder).where(ProductionOrder.company_id == current_user.company_id)
        
        res = await db.execute(stmt)
        record = res.scalars().first()
        if not record:
            return None
        return types.ProductionRecord.from_instance(record)

    @strawberry.field
    async def inventory_sessions(self, info: strawberry.Info, status: Optional[str] = None) -> List[types.InventorySession]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)
        
        from backend.database.models import InventorySession
        stmt = select(InventorySession)
        if current_user.role.name != "super_admin":
            stmt = stmt.where(InventorySession.company_id == current_user.company_id)
        
        if status:
            stmt = stmt.where(InventorySession.status == status)
        
        stmt = stmt.order_by(InventorySession.started_at.desc())
        
        res = await db.execute(stmt)
        return [types.InventorySession.from_instance(s) for s in res.scalars().all()]

    @strawberry.field
    async def inventory_session_items(self, session_id: int, info: strawberry.Info) -> List[types.InventoryItem]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)
        
        from backend.database.models import InventorySession, InventoryItem
        
        session = await db.get(InventorySession, session_id)
        if not session: return []
        if current_user.role.name != "super_admin" and session.company_id != current_user.company_id:
            return []
        
        stmt = select(InventoryItem).where(InventoryItem.session_id == session_id)
        res = await db.execute(stmt)
        return [types.InventoryItem.from_instance(i) for i in res.scalars().all()]

    @strawberry.field
    async def inventory_by_barcode(self, barcode: str, info: strawberry.Info) -> Optional[types.InventoryItem]:
        """Get ingredient by barcode for inventory scanning"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)
        
        from backend.database.models import Ingredient, Batch
        from sqlalchemy import select, func
        
        # Find ingredient by barcode
        stmt = select(Ingredient).where(Ingredient.barcode == barcode)
        res = await db.execute(stmt)
        ingredient = res.scalars().first()
        if not ingredient:
            return None
        
        # Calculate total system quantity
        stmt = select(func.coalesce(func.sum(Batch.quantity), 0)).where(
            Batch.ingredient_id == ingredient.id,
            Batch.status == "active"
        )
        res = await db.execute(stmt)
        system_qty = Decimal(res.scalar() or 0)

        # Return a simple object with the info
        return types.InventoryItem(
            id=0,
            session_id=0,
            ingredient_id=ingredient.id,
            ingredient_name=ingredient.name,
            ingredient_unit=ingredient.unit,
            found_quantity=None,
            system_quantity=system_qty,
            difference=None,
            adjusted=False
        )

    @strawberry.field
    async def invoices(
        self,
        info: strawberry.Info,
        type: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[types.Invoice]:
        """Get all invoices, optionally filtered by type and status"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import Invoice
        stmt = select(Invoice)

        if current_user.role.name != "super_admin":
            stmt = stmt.where(Invoice.company_id == current_user.company_id)

        if type:
            stmt = stmt.where(Invoice.type == type)
        if status:
            stmt = stmt.where(Invoice.status == status)
        if search:
            stmt = stmt.where(
                (Invoice.number.ilike(f"%{search}%")) |
                (Invoice.client_name.ilike(f"%{search}%"))
            )

        stmt = stmt.order_by(Invoice.date.desc(), Invoice.id.desc())

        res = await db.execute(stmt)
        return [types.Invoice.from_instance(i) for i in res.scalars().all()]

    @strawberry.field
    async def invoice(self, info: strawberry.Info, id: int) -> Optional[types.Invoice]:
        """Get a single invoice by ID"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import Invoice
        invoice = await db.get(Invoice, id)
        if not invoice:
            return None

        if current_user.role.name != "super_admin" and invoice.company_id != current_user.company_id:
            return None

        return types.Invoice.from_instance(invoice)

    @strawberry.field
    async def invoice_by_number(self, info: strawberry.Info, number: str) -> Optional[types.Invoice]:
        """Get a single invoice by number"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import Invoice
        stmt = select(Invoice).where(Invoice.number == number)
        res = await db.execute(stmt)
        invoice = res.scalars().first()
        if not invoice:
            return None

        if current_user.role.name != "super_admin" and invoice.company_id != current_user.company_id:
            return None

        return types.Invoice.from_instance(invoice)


    @strawberry.field
    async def cash_journal_entries(
        self,
        info: strawberry.Info,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        operation_type: Optional[str] = None,
    ) -> List[types.CashJournalEntryType]:
        """Get cash journal entries, optionally filtered"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import CashJournalEntry
        import datetime
        stmt = select(CashJournalEntry)

        if current_user.role.name != "super_admin":
            stmt = stmt.where(CashJournalEntry.company_id == current_user.company_id)

        if start_date:
            stmt = stmt.where(CashJournalEntry.date >= datetime.date.fromisoformat(start_date))
        if end_date:
            stmt = stmt.where(CashJournalEntry.date <= datetime.date.fromisoformat(end_date))
        if operation_type:
            stmt = stmt.where(CashJournalEntry.operation_type == operation_type)

        stmt = stmt.order_by(CashJournalEntry.date.desc(), CashJournalEntry.id.desc())

        res = await db.execute(stmt)
        return [types.CashJournalEntryType.from_instance(i) for i in res.scalars().all()]

    @strawberry.field
    async def operation_logs(
        self,
        info: strawberry.Info,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        operation: Optional[str] = None,
        entity_type: Optional[str] = None,
    ) -> List[types.OperationLogType]:
        """Get operation logs, optionally filtered"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import OperationLog
        import datetime
        stmt = select(OperationLog)

        if start_date:
            start_dt = datetime.datetime.fromisoformat(start_date)
            stmt = stmt.where(OperationLog.timestamp >= start_dt)
        if end_date:
            end_dt = datetime.datetime.fromisoformat(end_date)
            stmt = stmt.where(OperationLog.timestamp <= end_dt)
        if operation:
            stmt = stmt.where(OperationLog.operation == operation)
        if entity_type:
            stmt = stmt.where(OperationLog.entity_type == entity_type)

        stmt = stmt.order_by(OperationLog.timestamp.desc())

        res = await db.execute(stmt)
        return [types.OperationLogType.from_instance(i) for i in res.scalars().all()]

    @strawberry.field
    async def daily_summaries(
        self,
        info: strawberry.Info,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[types.DailySummaryType]:
        """Get daily summaries, optionally filtered by date range"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import DailySummary
        import datetime
        stmt = select(DailySummary)

        if current_user.role.name != "super_admin":
            stmt = stmt.where(DailySummary.company_id == current_user.company_id)

        if start_date:
            stmt = stmt.where(DailySummary.date >= datetime.date.fromisoformat(start_date))
        if end_date:
            stmt = stmt.where(DailySummary.date <= datetime.date.fromisoformat(end_date))

        stmt = stmt.order_by(DailySummary.date.desc())

        res = await db.execute(stmt)
        return [types.DailySummaryType.from_instance(i) for i in res.scalars().all()]

    @strawberry.field
    async def monthly_summaries(
        self,
        info: strawberry.Info,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
    ) -> List[types.MonthlySummaryType]:
        """Get monthly summaries, optionally filtered by year range"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import MonthlySummary
        stmt = select(MonthlySummary)

        if current_user.role.name != "super_admin":
            stmt = stmt.where(MonthlySummary.company_id == current_user.company_id)

        if start_year:
            stmt = stmt.where(MonthlySummary.year >= start_year)
        if end_year:
            stmt = stmt.where(MonthlySummary.year <= end_year)

        stmt = stmt.order_by(MonthlySummary.year.desc(), MonthlySummary.month.desc())

        res = await db.execute(stmt)
        return [types.MonthlySummaryType.from_instance(i) for i in res.scalars().all()]

    @strawberry.field
    async def yearly_summaries(
        self,
        info: strawberry.Info,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
    ) -> List[types.YearlySummaryType]:
        """Get yearly summaries, optionally filtered by year range"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import YearlySummary
        stmt = select(YearlySummary)

        if current_user.role.name != "super_admin":
            stmt = stmt.where(YearlySummary.company_id == current_user.company_id)

        if start_year:
            stmt = stmt.where(YearlySummary.year >= start_year)
        if end_year:
            stmt = stmt.where(YearlySummary.year <= end_year)

        stmt = stmt.order_by(YearlySummary.year.desc())

        res = await db.execute(stmt)
        return [types.YearlySummaryType.from_instance(i) for i in res.scalars().all()]

    @strawberry.field
    async def proforma_invoices(
        self,
        info: strawberry.Info,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[types.ProformaInvoice]:
        """Get all proforma invoices"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import Invoice
        stmt = select(Invoice).where(Invoice.type == "proforma")

        if current_user.role.name != "super_admin":
            stmt = stmt.where(Invoice.company_id == current_user.company_id)

        if status:
            stmt = stmt.where(Invoice.status == status)
        if search:
            stmt = stmt.where(
                (Invoice.number.ilike(f"%{search}%")) |
                (Invoice.client_name.ilike(f"%{search}%"))
            )

        stmt = stmt.order_by(Invoice.date.desc(), Invoice.id.desc())

        res = await db.execute(stmt)
        return [types.ProformaInvoice.from_instance(i) for i in res.scalars().all()]

    @strawberry.field
    async def invoice_corrections(
        self,
        info: strawberry.Info,
        type: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[types.InvoiceCorrection]:
        """Get all invoice corrections (credit/debit notes)"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import InvoiceCorrection
        from sqlalchemy.orm import selectinload
        stmt = select(InvoiceCorrection).options(selectinload(InvoiceCorrection.original_invoice))

        if current_user.role.name != "super_admin":
            stmt = stmt.where(InvoiceCorrection.company_id == current_user.company_id)

        if type:
            stmt = stmt.where(InvoiceCorrection.type == type)
        if status:
            stmt = stmt.where(InvoiceCorrection.status == status)

        stmt = stmt.order_by(InvoiceCorrection.correction_date.desc(), InvoiceCorrection.id.desc())

        res = await db.execute(stmt)
        return [types.InvoiceCorrection.from_instance(i) for i in res.scalars().all()]

    @strawberry.field
    async def invoice_correction(self, info: strawberry.Info, id: int) -> Optional[types.InvoiceCorrection]:
        """Get a single invoice correction by ID"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import InvoiceCorrection
        from sqlalchemy.orm import selectinload
        stmt = select(InvoiceCorrection).options(
            selectinload(InvoiceCorrection.original_invoice)
        ).where(InvoiceCorrection.id == id)
        res = await db.execute(stmt)
        correction = res.scalar_one_or_none()
        
        if not correction:
            return None

        if current_user.role.name != "super_admin" and correction.company_id != current_user.company_id:
            return None

        return types.InvoiceCorrection.from_instance(correction)

    @strawberry.field
    async def cash_receipts(
        self,
        info: strawberry.Info,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[types.CashReceipt]:
        """Get all cash receipts"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import CashReceipt
        stmt = select(CashReceipt)

        if current_user.role.name != "super_admin":
            stmt = stmt.where(CashReceipt.company_id == current_user.company_id)

        if start_date:
            stmt = stmt.where(CashReceipt.date >= datetime.date.fromisoformat(start_date))
        if end_date:
            stmt = stmt.where(CashReceipt.date <= datetime.date.fromisoformat(end_date))
        if search:
            stmt = stmt.where(CashReceipt.receipt_number.ilike(f"%{search}%"))

        stmt = stmt.order_by(CashReceipt.date.desc(), CashReceipt.id.desc())

        res = await db.execute(stmt)
        return [types.CashReceipt.from_instance(i) for i in res.scalars().all()]

    @strawberry.field
    async def cash_receipt(self, info: strawberry.Info, id: int) -> Optional[types.CashReceipt]:
        """Get a single cash receipt by ID"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import CashReceipt
        receipt = await db.get(CashReceipt, id)
        if not receipt:
            return None

        if current_user.role.name != "super_admin" and receipt.company_id != current_user.company_id:
            return None

        return types.CashReceipt.from_instance(receipt)

    @strawberry.field
    async def bank_accounts(
        self,
        info: strawberry.Info,
        is_active: Optional[bool] = None
    ) -> List[types.BankAccount]:
        """Get all bank accounts"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import BankAccount
        stmt = select(BankAccount)

        if current_user.role.name != "super_admin":
            stmt = stmt.where(BankAccount.company_id == current_user.company_id)

        if is_active is not None:
            stmt = stmt.where(BankAccount.is_active == is_active)

        stmt = stmt.order_by(BankAccount.bank_name.asc())

        res = await db.execute(stmt)
        return [types.BankAccount.from_instance(i) for i in res.scalars().all()]

    @strawberry.field
    async def bank_account(self, info: strawberry.Info, id: int) -> Optional[types.BankAccount]:
        """Get a single bank account by ID"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import BankAccount
        account = await db.get(BankAccount, id)
        if not account:
            return None

        if current_user.role.name != "super_admin" and account.company_id != current_user.company_id:
            return None

        return types.BankAccount.from_instance(account)

    @strawberry.field
    async def bank_transactions(
        self,
        info: strawberry.Info,
        bank_account_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        matched: Optional[bool] = None
    ) -> List[types.BankTransaction]:
        """Get all bank transactions"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import BankTransaction
        stmt = select(BankTransaction)

        if current_user.role.name != "super_admin":
            stmt = stmt.where(BankTransaction.company_id == current_user.company_id)

        if bank_account_id:
            stmt = stmt.where(BankTransaction.bank_account_id == bank_account_id)
        if start_date:
            stmt = stmt.where(BankTransaction.date >= datetime.date.fromisoformat(start_date))
        if end_date:
            stmt = stmt.where(BankTransaction.date <= datetime.date.fromisoformat(end_date))
        if matched is not None:
            stmt = stmt.where(BankTransaction.matched == matched)

        stmt = stmt.order_by(BankTransaction.date.desc(), BankTransaction.id.desc())

        res = await db.execute(stmt)
        return [types.BankTransaction.from_instance(i) for i in res.scalars().all()]

    @strawberry.field
    async def bank_transaction(self, info: strawberry.Info, id: int) -> Optional[types.BankTransaction]:
        """Get a single bank transaction by ID"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import BankTransaction
        transaction = await db.get(BankTransaction, id)
        if not transaction:
            return None

        if current_user.role.name != "super_admin" and transaction.company_id != current_user.company_id:
            return None

        return types.BankTransaction.from_instance(transaction)

    @strawberry.field
    async def accounts(
        self,
        info: strawberry.Info,
        type: Optional[str] = None,
        parent_id: Optional[int] = None
    ) -> List[types.Account]:
        """Get all accounts (chart of accounts)"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import Account
        stmt = select(Account)

        if current_user.role.name != "super_admin":
            stmt = stmt.where(Account.company_id == current_user.company_id)

        if type:
            stmt = stmt.where(Account.type == type)
        if parent_id is not None:
            stmt = stmt.where(Account.parent_id == parent_id)

        stmt = stmt.order_by(Account.code.asc())

        res = await db.execute(stmt)
        return [types.Account.from_instance(i) for i in res.scalars().all()]

    @strawberry.field
    async def account(self, info: strawberry.Info, id: int) -> Optional[types.Account]:
        """Get a single account by ID"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import Account
        account = await db.get(Account, id)
        if not account:
            return None

        if current_user.role.name != "super_admin" and account.company_id != current_user.company_id:
            return None

        return types.Account.from_instance(account)

    @strawberry.field
    async def account_by_code(self, info: strawberry.Info, code: str) -> Optional[types.Account]:
        """Get a single account by code"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import Account
        stmt = select(Account).where(Account.code == code)
        res = await db.execute(stmt)
        account = res.scalars().first()
        if not account:
            return None

        if current_user.role.name != "super_admin" and account.company_id != current_user.company_id:
            return None

        return types.Account.from_instance(account)

    @strawberry.field
    async def accounting_entries(
        self,
        info: strawberry.Info,
        account_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[types.AccountingEntry]:
        """Get all accounting entries"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import AccountingEntry
        stmt = select(AccountingEntry)

        if current_user.role.name != "super_admin":
            stmt = stmt.where(AccountingEntry.company_id == current_user.company_id)

        if account_id:
            stmt = stmt.where(
                (AccountingEntry.debit_account_id == account_id) |
                (AccountingEntry.credit_account_id == account_id)
            )
        if start_date:
            stmt = stmt.where(AccountingEntry.date >= datetime.date.fromisoformat(start_date))
        if end_date:
            stmt = stmt.where(AccountingEntry.date <= datetime.date.fromisoformat(end_date))
        if search:
            stmt = stmt.where(AccountingEntry.description.ilike(f"%{search}%"))

        stmt = stmt.order_by(AccountingEntry.date.desc(), AccountingEntry.id.desc())

        res = await db.execute(stmt)
        return [types.AccountingEntry.from_instance(i) for i in res.scalars().all()]

    @strawberry.field
    async def accounting_entry(self, info: strawberry.Info, id: int) -> Optional[types.AccountingEntry]:
        """Get a single accounting entry by ID"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import AccountingEntry
        entry = await db.get(AccountingEntry, id)
        if not entry:
            return None

        if current_user.role.name != "super_admin" and entry.company_id != current_user.company_id:
            return None

        return types.AccountingEntry.from_instance(entry)

    @strawberry.field
    async def vat_registers(
        self,
        info: strawberry.Info,
        year: Optional[int] = None,
        month: Optional[int] = None
    ) -> List[types.VATRegister]:
        """Get all VAT registers"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import VATRegister
        stmt = select(VATRegister)

        if current_user.role.name != "super_admin":
            stmt = stmt.where(VATRegister.company_id == current_user.company_id)

        if year:
            stmt = stmt.where(VATRegister.period_year == year)
        if month:
            stmt = stmt.where(VATRegister.period_month == month)

        stmt = stmt.order_by(VATRegister.period_year.desc(), VATRegister.period_month.desc())

        res = await db.execute(stmt)
        return [types.VATRegister.from_instance(i) for i in res.scalars().all()]

    @strawberry.field
    async def vat_register(self, info: strawberry.Info, id: int) -> Optional[types.VATRegister]:
        """Get a single VAT register by ID"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import VATRegister
        vat_register = await db.get(VATRegister, id)
        if not vat_register:
            return None

        if current_user.role.name != "super_admin" and vat_register.company_id != current_user.company_id:
            return None

        return types.VATRegister.from_instance(vat_register)

    @strawberry.field
    async def gateways(self, info: strawberry.Info, is_active: Optional[bool] = None) -> List[types.Gateway]:
        """Get all gateways"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import Gateway
        stmt = select(Gateway)
        
        if current_user.role.name != "super_admin":
            stmt = stmt.where(Gateway.company_id == current_user.company_id)

        if is_active is not None:
            stmt = stmt.where(Gateway.is_active == is_active)

        stmt = stmt.order_by(Gateway.registered_at.desc())

        res = await db.execute(stmt)
        return [types.Gateway.from_instance(i) for i in res.scalars().all()]

    @strawberry.field
    async def gateway(self, info: strawberry.Info, id: int) -> Optional[types.Gateway]:
        """Get a single gateway by ID"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import Gateway
        gateway = await db.get(Gateway, id)
        if not gateway:
            return None

        return types.Gateway.from_instance(gateway)

    @strawberry.field
    async def terminals(
        self, 
        info: strawberry.Info, 
        gateway_id: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> List[types.Terminal]:
        """Get all terminals"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import Terminal, Gateway
        stmt = select(Terminal)
        
        # Filter by company via Gateway, but ALWAYS allow terminals without gateway
        if current_user.role.name != "super_admin":
            from sqlalchemy import or_
            stmt = stmt.outerjoin(Gateway).where(
                or_(Gateway.company_id == current_user.company_id, Terminal.gateway_id == None)
            )

        if gateway_id is not None:
            stmt = stmt.where(Terminal.gateway_id == gateway_id)
        if is_active is not None:
            stmt = stmt.where(Terminal.is_active == is_active)

        stmt = stmt.order_by(Terminal.last_seen.desc())

        res = await db.execute(stmt)
        return [types.Terminal.from_instance(i) for i in res.scalars().all()]

    @strawberry.field
    async def terminal(self, info: strawberry.Info, id: int) -> Optional[types.Terminal]:
        """Get a single terminal by ID"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import Terminal
        terminal = await db.get(Terminal, id)
        if not terminal:
            return None

        return types.Terminal.from_instance(terminal)

    @strawberry.field
    async def printers(self, info: strawberry.Info, gateway_id: int) -> List[types.Printer]:
        """Get all printers for a gateway"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import Printer
        stmt = select(Printer).where(Printer.gateway_id == gateway_id)
        stmt = stmt.order_by(Printer.is_default.desc(), Printer.name)

        res = await db.execute(stmt)
        return [types.Printer.from_instance(i) for i in res.scalars().all()]

    @strawberry.field
    async def gateway_stats(self, info: strawberry.Info) -> types.GatewayStats:
        """Get gateway statistics"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)
        if current_user.role.name != "super_admin":
            raise AuthenticationException

        from backend.database.models import Gateway, Terminal, Printer
        from sqlalchemy import func

        total_gateways = await db.scalar(select(func.count(Gateway.id)))
        active_gateways = await db.scalar(select(func.count(Gateway.id)).where(Gateway.is_active == True))
        inactive_gateways = await db.scalar(select(func.count(Gateway.id)).where(Gateway.is_active == False))

        total_terminals = await db.scalar(select(func.count(Terminal.id)))
        active_terminals = await db.scalar(select(func.count(Terminal.id)).where(Terminal.is_active == True))

        total_printers = await db.scalar(select(func.count(Printer.id)))
        active_printers = await db.scalar(select(func.count(Printer.id)).where(Printer.is_active == True))

        return types.GatewayStats(
            total_gateways=total_gateways or 0,
            active_gateways=active_gateways or 0,
            inactive_gateways=inactive_gateways or 0,
            total_terminals=total_terminals or 0,
            active_terminals=active_terminals or 0,
            total_printers=total_printers or 0,
            active_printers=active_printers or 0
        )

    @strawberry.field
    async def access_zones(self, info: strawberry.Info) -> List[types.AccessZone]:
        db = info.context["db"]
        from backend.database import models
        user = info.context["current_user"]
        if not user: raise AuthenticationException
        
        stmt = select(models.AccessZone)
        if user.role.name != "super_admin":
            stmt = stmt.where(models.AccessZone.company_id == user.company_id)
            
        result = await db.execute(stmt)
        return [types.AccessZone.from_instance(z) for z in result.scalars().all()]

    @strawberry.field
    async def access_doors(self, info: strawberry.Info, gateway_id: Optional[int] = None) -> List[types.AccessDoor]:
        db = info.context["db"]
        from backend.database import models
        user = info.context["current_user"]
        if not user: raise AuthenticationException()
        
        query = select(models.AccessDoor).join(models.AccessZone)
        if user.role.name != "super_admin":
            query = query.where(models.AccessZone.company_id == user.company_id)
            
        if gateway_id:
            query = query.where(models.AccessDoor.gateway_id == gateway_id)
        result = await db.execute(query)
        return [types.AccessDoor.from_instance(d) for d in result.scalars().all()]

    @strawberry.field
    async def access_codes(self, info: strawberry.Info, gateway_id: Optional[int] = None) -> List[types.AccessCode]:
        db = info.context["db"]
        from backend.database import models
        user = info.context["current_user"]
        if not user: raise AuthenticationException()
        
        query = select(models.AccessCode)
        if user.role.name != "super_admin":
            from sqlalchemy import or_
            from backend.database.models import Gateway
            query = query.outerjoin(Gateway).where(
                or_(Gateway.company_id == user.company_id, models.AccessCode.gateway_id == None)
            )
            
        if gateway_id:
            query = query.where(models.AccessCode.gateway_id == gateway_id)
        result = await db.execute(query)
        return [types.AccessCode.from_instance(c) for c in result.scalars().all()]

    @strawberry.field
    async def access_logs(self, info: strawberry.Info, gateway_id: Optional[int] = None, limit: int = 100) -> List[types.AccessLog]:
        db = info.context["db"]
        from backend.database import models
        user = info.context["current_user"]
        if not user: raise AuthenticationException()
        
        query = select(models.AccessLog).order_by(models.AccessLog.timestamp.desc()).limit(limit)
        if user.role.name != "super_admin":
            from backend.database.models import Gateway
            query = query.join(Gateway).where(Gateway.company_id == user.company_id)
            
        if gateway_id:
            query = query.where(models.AccessLog.gateway_id == gateway_id)
        result = await db.execute(query)
        return [types.AccessLog.from_instance(l) for l in result.scalars().all()]

    # ========== PRODUCTION CONTROL QUERIES ==========

    @strawberry.field
    async def production_orders_for_day(
        self, 
        info: strawberry.Info, 
        date: Optional[str] = None
    ) -> List[types.ProductionOrder]:
        """Get production orders for a specific day (by production_deadline)"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException()
        
        from backend.database.models import ProductionOrder
        from datetime import datetime

        target_date = datetime.now().date()
        if date:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
        
        start_of_day = datetime.combine(target_date, datetime.min.time())
        end_of_day = datetime.combine(target_date, datetime.max.time())
        
        stmt = select(ProductionOrder).where(
            ProductionOrder.production_deadline >= start_of_day,
            ProductionOrder.production_deadline <= end_of_day,
            ProductionOrder.status.in_(["ready", "in_progress", "pending"])
        )
        
        if current_user.role.name != "super_admin":
            stmt = stmt.where(ProductionOrder.company_id == current_user.company_id)
        
        stmt = stmt.order_by(ProductionOrder.production_deadline.asc())
        
        res = await db.execute(stmt)
        return [types.ProductionOrder.from_instance(o) for o in res.scalars().all()]

    @strawberry.field
    async def overdue_production_orders(
        self, 
        info: strawberry.Info
    ) -> List[types.ProductionOrder]:
        """Get overdue production orders (production_deadline < now)"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException()
        
        from backend.database.models import ProductionOrder
        from datetime import datetime
        
        now = datetime.now()
        
        stmt = select(ProductionOrder).where(
            ProductionOrder.production_deadline < now,
            ProductionOrder.status.in_(["ready", "in_progress", "pending"])
        )
        
        if current_user.role.name != "super_admin":
            stmt = stmt.where(ProductionOrder.company_id == current_user.company_id)
        
        stmt = stmt.order_by(ProductionOrder.production_deadline.asc())
        
        res = await db.execute(stmt)
        return [types.ProductionOrder.from_instance(o) for o in res.scalars().all()]

    # ========== FLEET MANAGEMENT QUERIES ==========

    @strawberry.field
    async def vehicles(self, info: strawberry.Info, company_id: Optional[int] = None) -> List[types.Vehicle]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException()
        
        from backend.database.models import Vehicle
        stmt = select(Vehicle)
        
        if company_id:
            stmt = stmt.where(Vehicle.company_id == company_id)
        elif current_user.role.name != "super_admin":
            stmt = stmt.where(Vehicle.company_id == current_user.company_id)
            
        res = await db.execute(stmt)
        return [types.Vehicle.from_instance(v) for v in res.scalars().all()]

    @strawberry.field
    async def vehicle(self, info: strawberry.Info, id: int) -> Optional[types.Vehicle]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException()
        
        from backend.database.models import Vehicle
        vehicle = await db.get(Vehicle, id)
        
        if vehicle and current_user.role.name != "super_admin":
            if vehicle.company_id != current_user.company_id:
                return None
                
        return types.Vehicle.from_instance(vehicle) if vehicle else None

    @strawberry.field
    async def vehicle_types(self, info: strawberry.Info) -> List[types.VehicleType]:
        db = info.context["db"]
        from backend.database.models import VehicleType
        res = await db.execute(select(VehicleType))
        return [types.VehicleType.from_instance(vt) for vt in res.scalars().all()]

    @strawberry.field
    async def vehicle_documents(self, info: strawberry.Info, vehicle_id: int) -> List[types.VehicleDocument]:
        db = info.context["db"]
        from backend.database.models import VehicleDocument
        stmt = select(VehicleDocument).where(VehicleDocument.vehicle_id == vehicle_id)
        res = await db.execute(stmt)
        return [types.VehicleDocument.from_instance(d) for d in res.scalars().all()]

    @strawberry.field
    async def vehicle_mileage(self, info: strawberry.Info, vehicle_id: int) -> List[types.VehicleMileage]:
        db = info.context["db"]
        from backend.database.models import VehicleMileage
        stmt = select(VehicleMileage).where(VehicleMileage.vehicle_id == vehicle_id).order_by(VehicleMileage.date.desc())
        res = await db.execute(stmt)
        return [types.VehicleMileage.from_instance(m) for m in res.scalars().all()]

    @strawberry.field
    async def vehicle_fuel_logs(self, info: strawberry.Info, vehicle_id: int) -> List[types.VehicleFuel]:
        db = info.context["db"]
        from backend.database.models import VehicleFuel
        stmt = select(VehicleFuel).where(VehicleFuel.vehicle_id == vehicle_id).order_by(VehicleFuel.date.desc())
        res = await db.execute(stmt)
        return [types.VehicleFuel.from_instance(f) for f in res.scalars().all()]

    @strawberry.field
    async def vehicle_repairs(self, info: strawberry.Info, vehicle_id: int) -> List[types.VehicleRepair]:
        db = info.context["db"]
        from backend.database.models import VehicleRepair
        stmt = select(VehicleRepair).where(VehicleRepair.vehicle_id == vehicle_id).order_by(VehicleRepair.repair_date.desc())
        res = await db.execute(stmt)
        return [types.VehicleRepair.from_instance(r) for r in res.scalars().all()] if hasattr(res, "scalars") else []

    @strawberry.field
    async def vehicle_insurances(self, info: strawberry.Info, vehicle_id: int) -> List[types.VehicleInsurance]:
        db = info.context["db"]
        from backend.database.models import VehicleInsurance
        stmt = select(VehicleInsurance).where(VehicleInsurance.vehicle_id == vehicle_id).order_by(VehicleInsurance.start_date.desc())
        res = await db.execute(stmt)
        return [types.VehicleInsurance.from_instance(i) for i in res.scalars().all()]

    @strawberry.field
    async def vehicle_inspections(self, info: strawberry.Info, vehicle_id: int) -> List[types.VehicleInspection]:
        db = info.context["db"]
        from backend.database.models import VehicleInspection
        stmt = select(VehicleInspection).where(VehicleInspection.vehicle_id == vehicle_id).order_by(VehicleInspection.inspection_date.desc())
        res = await db.execute(stmt)
        return [types.VehicleInspection.from_instance(i) for i in res.scalars().all()]

    @strawberry.field
    async def vehicle_drivers(self, info: strawberry.Info, vehicle_id: int) -> List[types.VehicleDriver]:
        db = info.context["db"]
        from backend.database.models import VehicleDriver
        stmt = select(VehicleDriver).where(VehicleDriver.vehicle_id == vehicle_id).order_by(VehicleDriver.assigned_from.desc())
        res = await db.execute(stmt)
        return [types.VehicleDriver.from_instance(d) for d in res.scalars().all()]

    @strawberry.field
    async def vehicle_trips(self, info: strawberry.Info, vehicle_id: int) -> List[types.VehicleTrip]:
        db = info.context["db"]
        from backend.database.models import VehicleTrip
        stmt = select(VehicleTrip).where(VehicleTrip.vehicle_id == vehicle_id).order_by(VehicleTrip.start_time.desc())
        res = await db.execute(stmt)
        return [types.VehicleTrip.from_instance(t) for t in res.scalars().all()]
