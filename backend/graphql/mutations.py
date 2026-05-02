import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*strawberry.scalar.*")
warnings.filterwarnings("ignore", message=".*Extension.*")
warnings.filterwarnings("ignore", message=".*Pydantic.*")

import strawberry
from strawberry.file_uploads import Upload
from typing import Optional, List
import datetime
import json
from decimal import Decimal
from sqlalchemy import select
from datetime import time as dt_time
from backend.graphql import types, inputs
from backend.utils.json_type import JSONScalar
from backend import crud, schemas
from backend.crud.repositories import time_repo, settings_repo, user_repo, company_repo, vehicle_repo, payroll_repo
from backend.services.shift_swap_service import shift_swap_service
from backend.services.leave_service import leave_service
from backend.services.time_tracking_service import time_tracking_service
from backend.services.notification_service import notification_service
from backend.services.auth_service import auth_service, regenerate_user_qr_token, force_password_change_for_all_users
from backend.services.schedule_template_service import schedule_template_service
from backend.services.payroll_service import payroll_service
from backend.services.settings_service import settings_service
from backend.auth.permission_helper import check_permission, require_role, require_permission_or_role
from backend.database.transaction_manager import atomic_transaction, atomic_with_savepoint
from backend.exceptions import (
    PermissionDeniedException,
    NotFoundException,
    ValidationException,
    DatabaseException,
    AuthenticationException,
    DuplicateException,
    InvalidOperationException,
)
from backend.utils.error_handling import handle_db_error
from backend.graphql.inputs import (
    UserCreateInput, RoleCreateInput, UpdateUserInput,
    LeaveRequestInput, UpdateLeaveRequestStatusInput,
    CompanyCreateInput, CompanyUpdateInput, CompanyAccountingSettingsInput,
    DepartmentCreateInput, DepartmentUpdateInput, PositionCreateInput,
    SmtpSettingsInput, BonusCreateInput, MonthlyWorkDaysInput,
    PasswordSettingsInput, VehicleCreateInput, VehicleUpdateInput,
    VehicleMileageInput, VehicleFuelInput, VehicleRepairInput,
    VehicleInsuranceInput, VehicleInspectionInput, VehicleDriverInput, VehicleTripInput,
    VehicleMileageUpdateInput, VehicleFuelUpdateInput, VehicleRepairUpdateInput,
    VehicleInsuranceUpdateInput, VehicleInspectionUpdateInput, VehicleDriverUpdateInput, VehicleTripUpdateInput,
    CostCenterInput, UpdateCostCenterInput,
)
from backend.services.holiday_service import fetch_and_store_holidays
from backend.services.orthodox_holiday_service import fetch_and_store_orthodox_holidays
from backend.database.models import LeaveRequest, AccessZone, AccessDoor, AccessCode, Gateway, NightWorkBonus, OvertimeWork, WorkOnHoliday, PublicHoliday, Shift, WorkSchedule
from backend.auth.security import verify_password, hash_password, validate_password_complexity
from backend.auth.module_guard import verify_module_enabled


authenticate_msg = "Трябва да се автентикирате"
async def create_trz_records_on_clock_out(
    db,
    user_id: int,
    clock_in: datetime.datetime,
    clock_out: datetime.datetime
):
    """
    Автоматично създава NightWorkBonus, OvertimeWork и WorkOnHoliday записи при clock-out.
    
    Логика:
    1. Ако работата е в нощен период (22:00 - 06:00) -> NightWorkBonus
    2. Ако работеното време е над 8 часа -> OvertimeWork
    3. Ако денят е празничен -> WorkOnHoliday
    """
    
    from backend import crud
    
    # Провери дали автоматизацията е активирана
    auto_night = await settings_repo.get_setting(db, "payroll_auto_night_work")
    auto_overtime = await settings_repo.get_setting(db, "payroll_auto_overtime")
    auto_holiday = await settings_repo.get_setting(db, "payroll_auto_holiday")
    
    auto_night = auto_night.lower() == "true" if auto_night else False
    auto_overtime = auto_overtime.lower() == "true" if auto_overtime else False
    auto_holiday = auto_holiday.lower() == "true" if auto_holiday else False
    
    if not (auto_night or auto_overtime or auto_holiday):
        return  # Автоматизацията е изключена
    
    # Вземи настройките
    night_supplement_str = await settings_repo.get_setting(db, "payroll_night_hourly_supplement")
    overtime_rate_str = await settings_repo.get_setting(db, "payroll_overtime_rate")
    holiday_rate_str = await settings_repo.get_setting(db, "payroll_holiday_rate")
    night_supplement = Decimal(night_supplement_str) if night_supplement_str else Decimal("0.15")
    overtime_rate = Decimal(overtime_rate_str) if overtime_rate_str else Decimal("50")
    holiday_rate = Decimal(holiday_rate_str) if holiday_rate_str else Decimal("100")
    
    # Провери за празничен ден
    work_date = clock_in.date()
    result = await db.execute(
        select(PublicHoliday).where(PublicHoliday.date == work_date)
    )
    holiday = result.scalars().first()
    is_holiday = holiday is not None
    
    # Изчисли работеното време
    duration = clock_out - clock_in
    total_hours = Decimal(str(duration.total_seconds() / 3600))
    
    # Вземи заплатата на служителя (за опростенение - използваме мин заплата)
    # В реална имплементация - от employment_contract
    min_wage_str = await settings_repo.get_setting(db, "payroll_min_wage")
    hourly_rate = Decimal(min_wage_str) if min_wage_str else Decimal("1213")
    hourly_rate = hourly_rate / Decimal("8")  # Дневна / 8 часа
    
    created_records = []
    
    # 1. Нощен труд (22:00 - 06:00)
    if auto_night:
        night_hours = Decimal("0")
        
        # Провери дали clock-in е в нощен период
        if clock_in.time() >= dt_time(22, 0) or clock_in.time() < dt_time(6, 0):
            # Цялата смяна е нощна
            night_hours = total_hours
        elif clock_out.time() >= dt_time(22, 0):
            # Частично нощна работа
            night_start = datetime.datetime.combine(work_date, dt_time(22, 0))
            if clock_in.time() < dt_time(22, 0):
                night_hours = Decimal(str((clock_out - night_start).total_seconds() / 3600))
        
        if night_hours > 0:
            night_amount = night_hours * night_supplement
            night_bonus = NightWorkBonus(
                user_id=user_id,
                date=work_date,
                hours=night_hours,
                hourly_rate=night_supplement,
                amount=night_amount,
                is_paid=False,
                notes="Автоматично създаден при clock-out"
            )
            db.add(night_bonus)
            created_records.append(f"NightWorkBonus: {night_hours}h")
    
    # 2. Извънреден труд (над 8 часа)
    if auto_overtime and total_hours > Decimal("8"):
        overtime_hours = total_hours - Decimal("8")
        base_hourly = hourly_rate
        overtime_amount = overtime_hours * base_hourly * (overtime_rate / Decimal("100"))
        
        overtime = OvertimeWork(
            user_id=user_id,
            date=work_date,
            hours=overtime_hours,
            hourly_rate=base_hourly,
            multiplier=overtime_rate / Decimal("100"),
            amount=overtime_amount,
            is_paid=False,
            notes="Автоматично създаден при clock-out"
        )
        db.add(overtime)
        created_records.append(f"OvertimeWork: {overtime_hours}h")
    
    # 3. Празничен труд
    if auto_holiday and is_holiday:
        base_hourly = hourly_rate
        holiday_amount = total_hours * base_hourly * (holiday_rate / Decimal("100"))
        
        holiday_work = WorkOnHoliday(
            user_id=user_id,
            date=work_date,
            hours=total_hours,
            hourly_rate=base_hourly,
            multiplier=holiday_rate / Decimal("100"),
            amount=holiday_amount,
            is_paid=False,
            notes="Автоматично създаден при clock-out"
        )
        db.add(holiday_work)
        created_records.append(f"WorkOnHoliday: {total_hours}h")
    
    return created_records


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def attach_leave_document(
            self,
            request_id: int,
            file: Upload,
            info: strawberry.Info
    ) -> types.LeaveRequest:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        await verify_module_enabled("integrations", db)

        # Read file content
        # Upload type from strawberry has read() and filename but type hints are missing
        content = await file.read()  # type: ignore
        filename = file.filename  # type: ignore

        # Perform OCR
        from backend.services.ocr_service import extract_text_from_file
        ocr_text = extract_text_from_file(content, filename)

        stmt = select(LeaveRequest).where(LeaveRequest.id == request_id)
        res = await db.execute(stmt)
        req = res.scalars().first()
    
        if not req:
            raise NotFoundException.request()

        if req.user_id != current_user.id and current_user.role.name not in ["admin", "super_admin"]:
            raise AuthenticationException(detail="Нямате права за това действие")

        # Append text
        original_reason = req.reason or ""
        # Add timestamp to OCR data
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        new_reason = f"{original_reason}\n\n[OCR DATA - {filename} - {timestamp}]:\n{ocr_text}"
        req.reason = new_reason

        db.add(req)
        await db.commit()
        await db.refresh(req)

        return types.LeaveRequest.from_instance(req)

    @strawberry.mutation
    async def update_smtp_settings(
            self,
            settings: SmtpSettingsInput,
            info: strawberry.Info
    ) -> types.SmtpSettings:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        if not settings.smtp_server or not settings.sender_email:
            raise ValidationException.required_field("Server and Sender Email")

        await settings_repo.set_setting(db, "smtp_server", settings.smtp_server)
        await settings_repo.set_setting(db, "smtp_port", str(settings.smtp_port))
        await settings_repo.set_setting(db, "smtp_username", settings.smtp_username)
        await settings_repo.set_setting(db, "smtp_password", settings.smtp_password)
        await settings_repo.set_setting(db, "sender_email", settings.sender_email)
        await settings_repo.set_setting(db, "use_tls", str(settings.use_tls))

        return types.SmtpSettings(
            smtp_server=settings.smtp_server,
            smtp_port=settings.smtp_port,
            smtp_username=settings.smtp_username,
            smtp_password=settings.smtp_password,
            sender_email=settings.sender_email,
            use_tls=settings.use_tls
        )

    @strawberry.mutation
    async def save_notification_setting(
            self,
            setting_data: inputs.NotificationSettingInput,
            info: strawberry.Info
    ) -> types.NotificationSetting:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        import json
        from backend.database.models import NotificationSetting
        from sqlalchemy import select

        # Check if setting exists
        stmt = select(NotificationSetting).where(
            NotificationSetting.event_type == setting_data.event_type,
            NotificationSetting.company_id == setting_data.company_id
        )
        res = await db.execute(stmt)
        existing = res.scalars().first()

        recipients = None
        if setting_data.recipients:
            try:
                recipients = json.loads(setting_data.recipients)
            except:
                recipients = []

        if existing:
            existing.email_enabled = setting_data.email_enabled
            existing.push_enabled = setting_data.push_enabled
            existing.email_template = setting_data.email_template
            existing.recipients = recipients
            existing.interval_minutes = setting_data.interval_minutes
            existing.enabled = setting_data.enabled
            await db.commit()
            await db.refresh(existing)
            return types.NotificationSetting.from_instance(existing)
        else:
            new_setting = NotificationSetting(
                company_id=setting_data.company_id,
                event_type=setting_data.event_type,
                email_enabled=setting_data.email_enabled,
                push_enabled=setting_data.push_enabled,
                email_template=setting_data.email_template,
                recipients=recipients,
                interval_minutes=setting_data.interval_minutes,
                enabled=setting_data.enabled
            )
            db.add(new_setting)
            await db.commit()
            await db.refresh(new_setting)
            return types.NotificationSetting.from_instance(new_setting)

    @strawberry.mutation
    async def test_notification(
            self,
            event_type: str,
            info: strawberry.Info
    ) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        # TODO: Implement actual email sending
        # For now, just return success
        return True

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
            info: strawberry.Info
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

        return types.PayrollLegalSettings(
            max_insurance_base=max_insurance_base,
            employee_insurance_rate=employee_insurance_rate,
            income_tax_rate=income_tax_rate,
            civil_contract_costs_rate=civil_contract_costs_rate,
            noi_compensation_percent=noi_compensation_percent,
            employer_paid_sick_days=employer_paid_sick_days,
            default_tax_resident=default_tax_resident,
            trz_compliance_strict_mode=trz_compliance_strict_mode
        )

    @strawberry.mutation
    async def create_user(self, userInput: UserCreateInput, info: strawberry.Info) -> types.User:
        db = info.context["db"]
        current_user = info.context["current_user"]
        
        await require_permission_or_role(
            current_user,
            "users:create",
            db,
            ["admin", "super_admin"]
        )

        user_data = schemas.UserCreate(**userInput.model_dump())

        db_user = await user_repo.create_user(db=db, user_data=user_data, role_id=userInput.role_id)
        return types.User.from_instance(db_user)

    @strawberry.mutation
    async def update_user(self, userInput: UpdateUserInput, info: strawberry.Info) -> types.User:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None:
            raise AuthenticationException(detail=authenticate_msg)

        if current_user.id != userInput.id:
            await require_permission_or_role(
                current_user,
                "users:update",
                db,
                ["admin", "super_admin"]
            )

        # Build update data - exclude None values to preserve existing data
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

        # Filter out None values for contract-related fields
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

        # Also add surname to update_data
        if userInput.surname is not None:
            update_data["surname"] = userInput.surname

        # Convert dict to UserUpdate Pydantic model
        user_in = schemas.UserUpdate(**update_data)
        db_user = await user_repo.update_user(db, user_id=userInput.id, user_in=user_in)
        
        # Update or create EmploymentContract with TRZ fields
        if userInput.contract_type or userInput.base_salary:
            from backend.database.models import EmploymentContract
            from sqlalchemy import select
            
            stmt = select(EmploymentContract).where(
                EmploymentContract.user_id == userInput.id,
                EmploymentContract.is_active == True
            )
            result = await db.execute(stmt)
            contract = result.scalar_one_or_none()
            
            if contract:
                # Update existing contract
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
                # ТРЗ полета
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
                # Create new contract
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
                    # ТРЗ разширение
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
        current_user = info.context["current_user"]
        
        await require_permission_or_role(
            current_user,
            "users:delete",
            db,
            ["admin", "super_admin"]
        )
        
        return await user_repo.delete_user(db, id)

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
            vat_number=input.vat_number,
            address=input.address,
            city=input.city,
            country=input.country,
            phone=input.phone,
            website=input.web_site,
            logo_url=input.logo_url
        )
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
        return types.Company.from_instance(company)

    @strawberry.mutation
    async def update_company_accounting_settings(
        self, input: CompanyAccountingSettingsInput, info: strawberry.Info
    ) -> types.Company:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        company = await company_repo.update_company(
            db,
            company_id=input.company_id,
            default_sales_account_id=input.default_sales_account_id,
            default_expense_account_id=input.default_expense_account_id,
            default_vat_account_id=input.default_vat_account_id,
            default_customer_account_id=input.default_customer_account_id,
            default_supplier_account_id=input.default_supplier_account_id,
            default_cash_account_id=input.default_cash_account_id,
            default_bank_account_id=input.default_bank_account_id,
        )
        return types.Company.from_instance(company)

    @strawberry.mutation
    async def create_department(self, input: DepartmentCreateInput, info: strawberry.Info) -> types.Department:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        dept = await company_repo.create_department(db, name=input.name, company_id=input.company_id,
                                            manager_id=input.manager_id)
        return types.Department.from_instance(dept)

    @strawberry.mutation
    async def update_department(self, input: DepartmentUpdateInput, info: strawberry.Info) -> types.Department:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        dept = await company_repo.update_department(db, department_id=input.id, name=input.name, manager_id=input.manager_id)
        return types.Department.from_instance(dept)

    @strawberry.mutation
    async def create_position(self, title: str, department_id: int, info: strawberry.Info) -> types.Position:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        pos = await company_repo.create_position(db, title, department_id)
        return types.Position.from_instance(pos)

    @strawberry.mutation
    async def update_position(self, id: int, title: str, department_id: int, info: strawberry.Info) -> types.Position:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        pos = await company_repo.update_position(db, position_id=id, title=title, department_id=department_id)
        return types.Position.from_instance(pos)

    @strawberry.mutation
    async def delete_position(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")
        return await company_repo.delete_position(db, id)

    @strawberry.mutation
    async def create_vehicle(self, input: VehicleCreateInput, info: strawberry.Info) -> types.Vehicle:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin", "fleet_manager"]:
            raise PermissionDeniedException.for_action("manage")

        # Get company_id from current user if not provided
        company_id = input.company_id or current_user.company_id

        vehicle = await vehicle_repo.create_vehicle(
            db,
            registration_number=input.registration_number,
            vin=input.vin,
            make=input.make,
            model=input.model,
            year=input.year,
            vehicle_type=input.vehicle_type,
            fuel_type=input.fuel_type,
            status=input.status,
            color=input.color,
            initial_mileage=input.initial_mileage,
            is_company_vehicle=input.is_company_vehicle,
            notes=input.notes,
            company_id=company_id,
        )
        return types.Vehicle.from_instance(vehicle)

    @strawberry.mutation
    async def update_vehicle(self, id: int, input: VehicleUpdateInput, info: strawberry.Info) -> types.Vehicle:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin", "fleet_manager"]:
            raise PermissionDeniedException.for_action("manage")

        vehicle = await vehicle_repo.update_vehicle(
            db,
            vehicle_id=id,
            registration_number=input.registration_number,
            vin=input.vin,
            make=input.make,
            model=input.model,
            year=input.year,
            vehicle_type=input.vehicle_type,
            fuel_type=input.fuel_type,
            status=input.status,
            color=input.color,
            initial_mileage=input.initial_mileage,
            is_company_vehicle=input.is_company_vehicle,
            notes=input.notes,
        )
        if not vehicle:
            raise NotFoundException.vehicle()
        return types.Vehicle.from_instance(vehicle)

    @strawberry.mutation
    async def delete_vehicle(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin", "fleet_manager"]:
            raise PermissionDeniedException.for_action("manage")

        success = await vehicle_repo.delete_vehicle(db, vehicle_id=id)
        if not success:
            raise NotFoundException.vehicle()
        return True

    @strawberry.mutation
    async def create_vehicle_mileage(self, input: VehicleMileageInput, info: strawberry.Info) -> types.VehicleMileage:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin", "fleet_manager", "driver"]:
            raise PermissionDeniedException.for_action("manage")

        record = await vehicle_repo.create_vehicle_mileage(
            db,
            vehicle_id=input.vehicle_id,
            date=input.date.date() if hasattr(input.date, 'date') else input.date,
            mileage=input.mileage,
            notes=input.notes,
        )
        return types.VehicleMileage.from_instance(record)

    @strawberry.mutation
    async def create_vehicle_fuel(self, input: VehicleFuelInput, info: strawberry.Info) -> types.VehicleFuel:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin", "fleet_manager", "driver"]:
            raise PermissionDeniedException.for_action("manage")

        record = await vehicle_repo.create_vehicle_fuel(
            db,
            vehicle_id=input.vehicle_id,
            date=input.date.date() if hasattr(input.date, 'date') else input.date,
            liters=input.liters,
            price=input.price,
            total=input.total,
            fuel_type=input.fuel_type,
            notes=input.notes,
        )
        return types.VehicleFuel.from_instance(record)

    @strawberry.mutation
    async def create_vehicle_repair(self, input: VehicleRepairInput, info: strawberry.Info) -> types.VehicleRepair:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin", "fleet_manager"]:
            raise PermissionDeniedException.for_action("manage")

        record = await vehicle_repo.create_vehicle_repair(
            db,
            vehicle_id=input.vehicle_id,
            date=input.date.date() if hasattr(input.date, 'date') else input.date,
            description=input.description,
            cost=input.cost,
            notes=input.notes,
        )
        return types.VehicleRepair.from_instance(record)

    @strawberry.mutation
    async def create_vehicle_insurance(self, input: VehicleInsuranceInput, info: strawberry.Info) -> types.VehicleInsurance:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin", "fleet_manager"]:
            raise PermissionDeniedException.for_action("manage")

        record = await vehicle_repo.create_vehicle_insurance(
            db,
            vehicle_id=input.vehicle_id,
            provider=input.provider,
            policy_number=input.policy_number,
            start_date=input.start_date.date() if hasattr(input.start_date, 'date') else input.start_date,
            end_date=input.end_date.date() if hasattr(input.end_date, 'date') else input.end_date,
            premium=input.premium,
            notes=input.notes,
        )
        return types.VehicleInsurance.from_instance(record)

    @strawberry.mutation
    async def create_vehicle_inspection(self, input: VehicleInspectionInput, info: strawberry.Info) -> types.VehicleInspection:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin", "fleet_manager"]:
            raise PermissionDeniedException.for_action("manage")

        record = await vehicle_repo.create_vehicle_inspection(
            db,
            vehicle_id=input.vehicle_id,
            inspection_type=input.inspection_type,
            date=input.date.date() if hasattr(input.date, 'date') else input.date,
            result=input.result,
            next_inspection_date=input.next_inspection_date.date() if hasattr(input.next_inspection_date, 'date') else input.next_inspection_date,
            cost=input.cost,
            notes=input.notes,
        )
        return types.VehicleInspection.from_instance(record)

    @strawberry.mutation
    async def create_vehicle_driver(self, input: VehicleDriverInput, info: strawberry.Info) -> types.VehicleDriver:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin", "fleet_manager"]:
            raise PermissionDeniedException.for_action("manage")

        record = await vehicle_repo.create_vehicle_driver(
            db,
            vehicle_id=input.vehicle_id,
            user_id=input.user_id,
            start_date=input.start_date.date() if hasattr(input.start_date, 'date') else input.start_date,
            end_date=input.end_date.date() if hasattr(input.end_date, 'date') else input.end_date,
            is_primary=input.is_primary,
            notes=input.notes,
        )
        return types.VehicleDriver.from_instance(record)

    @strawberry.mutation
    async def create_vehicle_trip(self, input: VehicleTripInput, info: strawberry.Info) -> types.VehicleTrip:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin", "fleet_manager", "driver"]:
            raise PermissionDeniedException.for_action("manage")

        record = await vehicle_repo.create_vehicle_trip(
            db,
            vehicle_id=input.vehicle_id,
            user_id=input.user_id,
            start_time=input.start_time,
            end_time=input.end_time,
            start_location=input.start_location,
            end_location=input.end_location,
            distance=input.distance,
            notes=input.notes,
        )
        return types.VehicleTrip.from_instance(record)

    @strawberry.mutation
    async def delete_vehicle_mileage(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin", "fleet_manager"]:
            raise PermissionDeniedException.for_action("manage")
        success = await vehicle_repo.delete_vehicle_mileage(db, id)
        if not success:
            raise NotFoundException.record("Запис")
        return True

    @strawberry.mutation
    async def delete_vehicle_fuel(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin", "fleet_manager"]:
            raise PermissionDeniedException.for_action("manage")
        success = await vehicle_repo.delete_vehicle_fuel(db, id)
        if not success:
            raise NotFoundException.record("Запис")
        return True

    @strawberry.mutation
    async def delete_vehicle_repair(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin", "fleet_manager"]:
            raise PermissionDeniedException.for_action("manage")
        success = await vehicle_repo.delete_vehicle_repair(db, id)
        if not success:
            raise NotFoundException.record("Запис")
        return True

    @strawberry.mutation
    async def delete_vehicle_insurance(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin", "fleet_manager"]:
            raise PermissionDeniedException.for_action("manage")
        success = await vehicle_repo.delete_vehicle_insurance(db, id)
        if not success:
            raise NotFoundException.record("Запис")
        return True

    @strawberry.mutation
    async def delete_vehicle_inspection(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin", "fleet_manager"]:
            raise PermissionDeniedException.for_action("manage")
        success = await vehicle_repo.delete_vehicle_inspection(db, id)
        if not success:
            raise NotFoundException.record("Запис")
        return True

    @strawberry.mutation
    async def delete_vehicle_driver(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin", "fleet_manager"]:
            raise PermissionDeniedException.for_action("manage")
        success = await vehicle_repo.delete_vehicle_driver(db, id)
        if not success:
            raise NotFoundException.record("Запис")
        return True

    @strawberry.mutation
    async def delete_vehicle_trip(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin", "fleet_manager"]:
            raise PermissionDeniedException.for_action("manage")
        success = await vehicle_repo.delete_vehicle_trip(db, id)
        if not success:
            raise NotFoundException.record("Запис")
        return True

    @strawberry.mutation
    async def update_vehicle_mileage(self, id: int, input: VehicleMileageUpdateInput, info: strawberry.Info) -> types.VehicleMileage:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin", "fleet_manager", "driver"]:
            raise PermissionDeniedException.for_action("manage")
        record = await vehicle_repo.update_vehicle_mileage(
            db, id,
            date=input.date.date() if input.date else None,
            mileage=input.mileage,
            notes=input.notes,
        )
        if not record:
            raise NotFoundException.record("Запис")
        return types.VehicleMileage.from_instance(record)

    @strawberry.mutation
    async def update_vehicle_fuel(self, id: int, input: VehicleFuelUpdateInput, info: strawberry.Info) -> types.VehicleFuel:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin", "fleet_manager", "driver"]:
            raise PermissionDeniedException.for_action("manage")
        record = await vehicle_repo.update_vehicle_fuel(
            db, id,
            date=input.date.date() if input.date else None,
            liters=input.liters,
            price=input.price,
            total=input.total,
            fuel_type=input.fuel_type,
            notes=input.notes,
        )
        if not record:
            raise NotFoundException.record("Запис")
        return types.VehicleFuel.from_instance(record)

    @strawberry.mutation
    async def update_vehicle_repair(self, id: int, input: VehicleRepairUpdateInput, info: strawberry.Info) -> types.VehicleRepair:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin", "fleet_manager"]:
            raise PermissionDeniedException.for_action("manage")
        record = await vehicle_repo.update_vehicle_repair(
            db, id,
            date=input.date.date() if input.date else None,
            description=input.description,
            cost=input.cost,
            repair_type=input.repair_type,
            notes=input.notes,
        )
        if not record:
            raise NotFoundException.record("Запис")
        return types.VehicleRepair.from_instance(record)

    @strawberry.mutation
    async def update_vehicle_insurance(self, id: int, input: VehicleInsuranceUpdateInput, info: strawberry.Info) -> types.VehicleInsurance:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin", "fleet_manager"]:
            raise PermissionDeniedException.for_action("manage")
        record = await vehicle_repo.update_vehicle_insurance(
            db, id,
            provider=input.provider,
            policy_number=input.policy_number,
            start_date=input.start_date.date() if input.start_date else None,
            end_date=input.end_date.date() if input.end_date else None,
            premium=input.premium,
            insurance_type=input.insurance_type,
            notes=input.notes,
        )
        if not record:
            raise NotFoundException.record("Запис")
        return types.VehicleInsurance.from_instance(record)

    @strawberry.mutation
    async def update_vehicle_inspection(self, id: int, input: VehicleInspectionUpdateInput, info: strawberry.Info) -> types.VehicleInspection:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin", "fleet_manager"]:
            raise PermissionDeniedException.for_action("manage")
        record = await vehicle_repo.update_vehicle_inspection(
            db, id,
            date=input.date.date() if input.date else None,
            next_date=input.next_date.date() if input.next_date else None,
            cost=input.cost,
            result=input.result,
            protocol_number=input.protocol_number,
            notes=input.notes,
        )
        if not record:
            raise NotFoundException.record("Запис")
        return types.VehicleInspection.from_instance(record)

    @strawberry.mutation
    async def update_vehicle_driver(self, id: int, input: VehicleDriverUpdateInput, info: strawberry.Info) -> types.VehicleDriver:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin", "fleet_manager"]:
            raise PermissionDeniedException.for_action("manage")
        record = await vehicle_repo.update_vehicle_driver(
            db, id,
            license_number=input.license_number,
            license_expiry=input.license_expiry.date() if input.license_expiry else None,
            phone=input.phone,
            category=input.category,
            is_primary=input.is_primary,
            notes=input.notes,
        )
        if not record:
            raise NotFoundException.record("Запис")
        return types.VehicleDriver.from_instance(record)

    @strawberry.mutation
    async def update_vehicle_trip(self, id: int, input: VehicleTripUpdateInput, info: strawberry.Info) -> types.VehicleTrip:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin", "fleet_manager", "driver"]:
            raise PermissionDeniedException.for_action("manage")
        record = await vehicle_repo.update_vehicle_trip(
            db, id,
            start_date=input.start_date,
            end_date=input.end_date,
            start_location=input.start_location,
            end_location=input.end_location,
            distance=input.distance,
            trip_type=input.trip_type,
            notes=input.notes,
        )
        if not record:
            raise NotFoundException.record("Запис")
        return types.VehicleTrip.from_instance(record)

    @strawberry.mutation
    async def create_shift(self, name: str, start_time: datetime.time, end_time: datetime.time,
                           info: strawberry.Info) -> types.Shift:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        s = await time_repo.create_shift(db, name, start_time, end_time)
        return types.Shift.from_instance(s)

    @strawberry.mutation
    async def update_shift(
            self, id: int, name: str, start_time: datetime.time, end_time: datetime.time,
            tolerance_minutes: Optional[int] = None, break_duration_minutes: Optional[int] = None,
            pay_multiplier: Optional[Decimal] = None, shift_type: Optional[str] = None,
            info: Optional[strawberry.Info] = None
    ) -> types.Shift:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        s = await time_repo.update_shift(
            db, shift_id=id, name=name, start_time=start_time, end_time=end_time,
            tolerance_minutes=tolerance_minutes, break_duration_minutes=break_duration_minutes, pay_multiplier=pay_multiplier, shift_type=shift_type
        )
        return types.Shift.from_instance(s)

    @strawberry.mutation
    async def delete_shift(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")
        return await time_repo.delete_shift(db, id)

    @strawberry.mutation
    async def create_role(self, input: RoleCreateInput, info: strawberry.Info) -> types.Role:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        role = await time_repo.create_role(db, schemas.RoleCreate(name=input.name, description=input.description))
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
        return types.Role.from_instance(role)

    @strawberry.mutation
    async def delete_role(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")
        return await time_repo.delete_role(db, id)

    @strawberry.mutation
    async def assign_role_to_user(self, user_id: int, company_id: int, role_id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        from backend.auth.rbac_service import PermissionService
        perm_service = PermissionService(db)
        await perm_service.assign_role_to_user(user_id, company_id, role_id, current_user.id)
        return True

    @strawberry.mutation
    async def set_global_setting(self, key: str, value: str, info: strawberry.Info) -> types.GlobalSetting:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name != "super_admin":
            raise PermissionDeniedException.for_action("manage")

        setting = await settings_repo.set_setting(db, key, value)
        return types.GlobalSetting.from_instance(setting)

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
            info: strawberry.Info
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
            has_health_insurance=has_health_insurance
        )
        await settings_repo.set_setting(db, "qr_token_regen_minutes", str(qr_regen_interval_minutes))

        # Re-fetch the updated config with the new QR setting
        config = await payroll_svc.get_global_config()
        qr_setting = await settings_repo.get_setting(db, "qr_token_regen_minutes")
        return types.GlobalPayrollConfig(
            id="global",
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
            qr_regen_interval_minutes=int(qr_setting) if qr_setting else 60
        )

    @strawberry.mutation(name="requestLeave")
    async def create_leave_request(self, leave_input: LeaveRequestInput, info: strawberry.Info) -> types.LeaveRequest:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        # Create leave request directly with the model
        from backend.database.models import LeaveRequest
        leave_request = LeaveRequest(
            user_id=current_user.id,
            start_date=leave_input.start_date,
            end_date=leave_input.end_date,
            leave_type=leave_input.leave_type,
            reason=leave_input.reason,
            status="pending"
        )
        db.add(leave_request)
        await db.commit()
        await db.refresh(leave_request)
        return types.LeaveRequest.from_instance(leave_request)

    @strawberry.mutation
    async def update_leave_request_status(self, input: UpdateLeaveRequestStatusInput,
                                          info: strawberry.Info) -> types.LeaveRequest:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        service = leave_service(db)
        if input.status == "approved":
            req = await service.approve_request(
                request_id=input.request_id,
                admin_comment=input.admin_comment,
                admin_user_id=current_user.id,
                employer_top_up=input.employer_top_up
            )
        else:
            req = await service.reject_request(
                request_id=input.request_id,
                admin_comment=input.admin_comment,
                admin_user_id=current_user.id
            )
        return types.LeaveRequest.from_instance(req)

    @strawberry.mutation(name="approveLeave")
    async def approve_leave(self, info: strawberry.Info, request_id: int, admin_comment: str = None, employer_top_up: bool = False) -> types.LeaveRequest:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        service = leave_service(db)
        async with atomic_with_savepoint(db, "leave_approved"):
            req = await service.approve_request(
                request_id=request_id,
                admin_comment=admin_comment,
                admin_user_id=current_user.id,
                employer_top_up=employer_top_up
            )
        return types.LeaveRequest.from_instance(req)

    @strawberry.mutation(name="rejectLeave")
    async def reject_leave(self, info: strawberry.Info, request_id: int, admin_comment: str = None) -> types.LeaveRequest:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        service = leave_service(db)
        async with atomic_with_savepoint(db, "leave_rejected"):
            req = await service.reject_request(
                request_id=request_id,
                admin_comment=admin_comment,
                admin_user_id=current_user.id
            )
        return types.LeaveRequest.from_instance(req)

    @strawberry.mutation
    async def delete_leave_request(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")
        is_admin = current_user.role.name in ["admin", "super_admin"]
        return await time_repo.delete_leave_request(db, id, current_user.id, is_admin)

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

        return types.OfficeLocation(
            latitude=latitude,
            longitude=longitude,
            radius=radius,
            entry_enabled=entry_enabled,
            exit_enabled=exit_enabled
        )

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

        # Re-fetch user from DB to access hashed_password (not present in Pydantic schema)
        from backend.database.models import User
        stmt = select(User).where(User.id == current_user.id)
        result = await db.execute(stmt)
        db_user = result.scalars().first()

        if not db_user:
            raise NotFoundException.user()

        if not verify_password(old_password, db_user.hashed_password):
            raise ValidationException.field("password", "Неправилна стара парола")

        await validate_password_complexity(db, new_password)

        db_user.hashed_password = hash_password(new_password)
        db_user.password_force_change = False  # Reset the flag after successful change
        db.add(db_user)
        await db.commit()
        return True

    @strawberry.mutation
    async def invalidate_user_session(self, sessionId: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        # Check if the session belongs to the user trying to invalidate (if not admin)
        session_to_invalidate = await user_repo.get_user_session_by_id(db, sessionId)
        if not session_to_invalidate:
            raise NotFoundException.session()

        if session_to_invalidate.user_id != current_user.id and current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("invalidate session")

        return await user_repo.invalidate_user_session(db, session_to_invalidate.refresh_token_jti)

    @strawberry.mutation
    async def update_security_config(
            self,
            max_login_attempts: int,
            lockout_minutes: int,
            info: strawberry.Info
    ) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        await settings_repo.set_setting(db, "max_login_attempts", str(max_login_attempts))
        await settings_repo.set_setting(db, "lockout_minutes", str(lockout_minutes))
        await db.commit()
        return True

    @strawberry.mutation
    async def update_kiosk_security_settings(
            self,
            require_gps: bool,
            require_same_network: bool,
            info: strawberry.Info
    ) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        await settings_repo.set_setting(db, "kiosk_require_gps", "true" if require_gps else "false")
        await settings_repo.set_setting(db, "kiosk_require_same_network", "true" if require_same_network else "false")
        await db.commit()
        return True

    @strawberry.mutation
    async def disconnect_google_calendar(self, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        await crud.disconnect_google_calendar(db, current_user.id)
        return True

    @strawberry.mutation
    async def update_google_calendar_settings(
            self,
            sync_work_schedules: bool,
            sync_time_logs: bool,
            sync_leave_requests: bool,
            sync_public_holidays: bool,
            privacy_level: str,
            info: strawberry.Info
    ) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        await crud.update_google_calendar_sync_settings(
            db,
            user_id=current_user.id,
            sync_work_schedules=sync_work_schedules,
            sync_time_logs=sync_time_logs,
            sync_leave_requests=sync_leave_requests,
            sync_public_holidays=sync_public_holidays,
            privacy_level=privacy_level
        )
        return True

    @strawberry.mutation
    async def generate_my_payslip(
            self,
            start_date: datetime.date,
            end_date: datetime.date,
            info: strawberry.Info
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
            generated_at=crud.sofia_now()
        )
        db.add(db_payslip)
        await db.commit()
        await db.refresh(db_payslip)

        return types.Payslip.from_instance(db_payslip)

    @strawberry.mutation
    async def generate_payslip(
            self,
            user_id: int,
            start_date: datetime.date,
            end_date: datetime.date,
            info: strawberry.Info
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
            generated_at=crud.sofia_now()
        )
        db.add(db_payslip)
        await db.commit()
        await db.refresh(db_payslip)

        return types.Payslip.from_instance(db_payslip)

    @strawberry.mutation
    async def create_time_log(
            self,
            user_id: int,
            start_time: datetime.datetime,
            end_time: Optional[datetime.datetime] = None,
            is_manual: bool = False,
            break_duration_minutes: int = 0,
            notes: Optional[str] = None,
            info: Optional[strawberry.Info] = None
    ) -> types.TimeLog:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = info.context["current_user"]

        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        if not end_time:
            raise ValidationException(detail="Краен час е задължителен за ръчно въвеждане")

        # Pre-validation: check for overlaps BEFORE creating
        time_svc = time_tracking_service(db)
        has_overlap = await time_svc.check_time_overlap(user_id, start_time, end_time)
        if has_overlap:
            raise ValidationException(detail="Записът се застъпва с друг запис за този период")

        log = await time_repo.create_manual_time_log(
            db, user_id, start_time, end_time, break_duration_minutes or 0, notes, is_manual=is_manual
        )
        return types.TimeLog.from_instance(log)

    @strawberry.mutation
    async def update_time_log(
            self, id: int, start_time: datetime.datetime, end_time: Optional[datetime.datetime] = None,
            is_manual: bool = False, break_duration_minutes: int = 0, notes: Optional[str] = None,
            info: Optional[strawberry.Info] = None
    ) -> types.TimeLog:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = info.context["current_user"]

        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        log = await time_repo.update_time_log(
            db, log_id=id, start_time=start_time, end_time=end_time, is_manual=is_manual, break_duration_minutes=break_duration_minutes, notes=notes
        )
        return types.TimeLog.from_instance(log)

    @strawberry.mutation
    async def delete_time_log(self, id: int, info: Optional[strawberry.Info]) -> bool:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")
        return await time_repo.delete_time_log(db, log_id=id)

    @strawberry.mutation
    async def clock_in(
            self,
            info: strawberry.Info,
            latitude: Optional[float] = None,
            longitude: Optional[float] = None
    ) -> types.TimeLog:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail="Not authenticated")

        await verify_module_enabled("shifts", db)

        service = time_tracking_service(db)
        async with atomic_transaction(db):
            log = await service.clock_in(current_user.id, latitude, longitude)
            async with atomic_with_savepoint(db, "clock_in_complete"):
                pass
            return types.TimeLog.from_instance(log)

    @strawberry.mutation
    async def clock_out(
            self,
            info: strawberry.Info,
            notes: Optional[str] = None,
            latitude: Optional[float] = None,
            longitude: Optional[float] = None
    ) -> types.TimeLog:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail="Not authenticated")

        await verify_module_enabled("shifts", db)

        service = time_tracking_service(db)
        active_log = await service.get_active_timelog(current_user.id)

        if not active_log:
            raise InvalidOperationException.cannot_complete("No active time log found")

        log = await service.clock_out(current_user.id, latitude, longitude, notes=notes)

        await create_trz_records_on_clock_out(
            db=db,
            user_id=current_user.id,
            clock_in=active_log.start_time,
            clock_out=log.end_time
        )

        async with atomic_with_savepoint(db, "clock_out_complete"):
            pass

        return types.TimeLog.from_instance(log)

    @strawberry.mutation(name="adminClockIn")
    async def admin_clock_in(
            self,
            user_id: int,
            info: strawberry.Info,
            custom_time: Optional[datetime.datetime] = None
    ) -> types.TimeLog:
        db = info.context["db"]
        current_user = info.context["current_user"]
        
        if current_user is None or current_user.role is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")
        
        await verify_module_enabled("shifts", db)
        
        service = time_tracking_service(db)
        active_log = await service.get_active_timelog(user_id)
        if active_log:
            raise InvalidOperationException.cannot_complete("User already has an active time log")
        
        log = await service.clock_in(user_id, custom_time=custom_time)
        
        return types.TimeLog.from_instance(log)

    @strawberry.mutation(name="adminClockOut")
    async def admin_clock_out(
            self,
            user_id: int,
            info: strawberry.Info,
            notes: Optional[str] = None,
            custom_time: Optional[datetime.datetime] = None
    ) -> types.TimeLog:
        db = info.context["db"]
        current_user = info.context["current_user"]
        
        if current_user is None or current_user.role is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")
        
        await verify_module_enabled("shifts", db)
        
        service = time_tracking_service(db)
        active_log = await service.get_active_timelog(user_id)
        
        if not active_log:
            raise InvalidOperationException.cannot_complete("No active time log found")
        
        log = await service.clock_out(user_id, custom_time=custom_time, notes=notes)
        
        await create_trz_records_on_clock_out(
            db=db,
            user_id=user_id,
            clock_in=active_log.start_time,
            clock_out=log.end_time,
        )
        
        return types.TimeLog.from_instance(log)

    @strawberry.mutation
    async def create_schedule_template(self, name: str, description: Optional[str],
                                       items: List[inputs.ScheduleTemplateItemInput],
                                       info: strawberry.Info) -> types.ScheduleTemplate:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        await verify_module_enabled("shifts", db)

        # Convert Strawberry Input items to dicts manually
        items_dicts = []
        for item in items:
            items_dicts.append({
                "day_index": item.day_of_week,
                "shift_id": getattr(item, 'shift_id', None)
            })
        template = await time_repo.create_schedule_template(db, name, current_user.company_id, description, items_dicts)
        return types.ScheduleTemplate.from_instance(template)

    @strawberry.mutation
    async def delete_schedule_template(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        await verify_module_enabled("shifts", db)
        result = await time_repo.delete_schedule_template(db, id, company_id=current_user.company_id)
        if not result:
            raise NotFoundException.resource("ScheduleTemplate", id)
        return True

    @strawberry.mutation
    async def apply_schedule_template(
            self,
            template_id: int,
            user_ids: List[int],
            start_date: datetime.date,
            end_date: datetime.date,
            info: strawberry.Info
    ) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        await verify_module_enabled("shifts", db)

        # Apply template to each user
        for user_id in user_ids:
            await time_repo.apply_schedule_template(
                db, template_id, user_id, start_date, end_date, current_user.id
            )
            async with atomic_with_savepoint(db, f"schedule_applied_{user_id}"):
                pass  # Reserved for future notifications
        return True

    @strawberry.mutation
    async def update_password_settings(
            self,
            settings: PasswordSettingsInput,
            info: strawberry.Info
    ) -> types.PasswordSettings:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name != "super_admin":
            raise PermissionDeniedException.for_action("manage")

        await settings_repo.set_setting(db, "pwd_min_length", str(settings.min_length))
        await settings_repo.set_setting(db, "pwd_max_length", str(settings.max_length))
        await settings_repo.set_setting(db, "pwd_require_upper", "true" if settings.require_upper else "false")
        await settings_repo.set_setting(db, "pwd_require_lower", "true" if settings.require_lower else "false")
        await settings_repo.set_setting(db, "pwd_require_digit", "true" if settings.require_digit else "false")
        await settings_repo.set_setting(db, "pwd_require_special", "true" if settings.require_special else "false")

        # Increment password settings version
        current_version = int(await settings_repo.get_setting(db, "password_settings_version") or "0")
        await settings_repo.set_setting(db, "password_settings_version", str(current_version + 1))

        # Set password_force_change to True for all users
        await force_password_change_for_all_users(db)

        await db.commit()
        return types.PasswordSettings(
            min_length=settings.min_length,
            max_length=settings.max_length,
            require_upper=settings.require_upper,
            require_lower=settings.require_lower,
            require_digit=settings.require_digit,
            require_special=settings.require_special
        )

    @strawberry.mutation
    async def sync_holidays(self, year: int, info: strawberry.Info) -> int:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        return await fetch_and_store_holidays(db, year)

    @strawberry.mutation
    async def sync_orthodox_holidays(self, year: int, info: strawberry.Info) -> int:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        try:
            return await fetch_and_store_orthodox_holidays(db, year)
        except Exception as e:
            await db.rollback()
            if "duplicate key" in str(e).lower():
                from datetime import date
                from sqlalchemy import select
                from backend.database.models import OrthodoxHoliday
                try:
                    start_date = date(year, 1, 1)
                    end_date = date(year, 12, 31)
                    result = await db.execute(
                        select(OrthodoxHoliday.date).where(OrthodoxHoliday.date >= start_date).where(
                            OrthodoxHoliday.date <= end_date))
                    existing = result.scalars().all()
                    return len(existing)
                except:
                    pass
            raise DatabaseException(detail=f"Failed to sync holidays: {str(e)}")

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
            description=input.description
        )
        async with atomic_with_savepoint(db, "bonus_created"):
            pass  # Reserved for future notifications
        await db.commit()
        return types.Bonus.from_instance(bonus)

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
    async def regenerate_my_qr_code(self, info: strawberry.Info) -> str:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        return await regenerate_user_qr_token(db, current_user.id)

    @strawberry.mutation
    async def create_advance_payment(
            self,
            user_id: int,
            amount: float,
            payment_date: datetime.date,
            description: Optional[str] = None,
            info: Optional[strawberry.Info] = None
    ) -> types.AdvancePayment:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        advance = await payroll_repo.create_advance_payment(
            db, user_id=user_id, amount=amount, request_date=payment_date
        )
        return types.AdvancePayment.from_instance(advance)

    @strawberry.mutation
    async def create_service_loan(
            self,
            user_id: int,
            total_amount: float,
            installments_count: int,
            start_date: datetime.date,
            description: str,
            info: Optional[strawberry.Info] = None
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

    @strawberry.mutation
    async def set_monthly_work_days(self, input: MonthlyWorkDaysInput, info: strawberry.Info) -> types.MonthlyWorkDays:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        payroll_svc = payroll_service(db)
        res = await payroll_svc.set_monthly_work_days(input.year, input.month, input.days_count)
        return types.MonthlyWorkDays.from_instance(res)

    @strawberry.mutation
    async def create_manual_time_log(
            self,
            user_id: int,
            start_time: datetime.datetime,
            end_time: datetime.datetime,
            break_duration_minutes: int = 0,
            notes: Optional[str] = None,
            info: Optional[strawberry.Info] = None
    ) -> types.TimeLog:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        # Pre-validation: check for overlaps BEFORE creating
        time_svc = time_tracking_service(db)
        has_overlap = await time_svc.check_time_overlap(user_id, start_time, end_time)
        if has_overlap:
            raise ValidationException(detail="Записът се застъпва с друг запис за този период")

        log = await time_repo.create_manual_time_log(
            db, user_id, start_time, end_time, break_duration_minutes, notes
        )
        async with atomic_with_savepoint(db, "manual_timelog_created"):
            pass  # Reserved for future notifications
        return types.TimeLog.from_instance(log)

    @strawberry.mutation
    async def delete_work_schedule(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        return await time_repo.delete_schedule(db, id)

    @strawberry.mutation
    async def set_work_schedule(self, user_id: int, shift_id: int, date: datetime.date,
                                info: strawberry.Info) -> types.WorkSchedule:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        res = await time_repo.create_or_update_schedule(db, user_id, shift_id, date)
        return types.WorkSchedule.from_instance(res)

    @strawberry.mutation
    async def bulk_set_schedule(self, user_ids: List[int], shift_id: int, start_date: datetime.date,
                                end_date: datetime.date, days_of_week: List[int], info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        return await time_repo.create_bulk_schedules(db, user_ids, shift_id, start_date, end_date, days_of_week)

    @strawberry.mutation
    async def respond_to_swap(self, swap_id: int, accept: bool, info: strawberry.Info) -> types.ShiftSwapRequest:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        new_status = "accepted" if accept else "rejected"
        service = shift_swap_service(db)
        res = await service.update_status(swap_id, new_status)
        return types.ShiftSwapRequest.from_instance(res)

    @strawberry.mutation
    async def approve_swap(self, swap_id: int, approve: bool, info: strawberry.Info) -> types.ShiftSwapRequest:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        new_status = "approved" if approve else "rejected"
        service = shift_swap_service(db)
        async with atomic_with_savepoint(db, "swap_approved"):
            res = await service.update_status(swap_id, new_status, admin_user_id=current_user.id)
        return types.ShiftSwapRequest.from_instance(res)

    @strawberry.mutation
    async def create_swap_request(self, requestor_schedule_id: int, target_user_id: int, target_schedule_id: int,
                                  info: strawberry.Info) -> types.ShiftSwapRequest:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        service = shift_swap_service(db)
        async with atomic_with_savepoint(db, "swap_created"):
            res = await service.create_request(current_user.id, requestor_schedule_id, target_user_id, target_schedule_id)
        return types.ShiftSwapRequest.from_instance(res)

    # --- Confectionery Module Mutations ---

    @strawberry.mutation
    async def create_storage_zone(self, input: inputs.StorageZoneInput, info: strawberry.Info) -> types.StorageZone:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        target_company_id = input.company_id if current_user.role.name == "super_admin" else current_user.company_id
        if not target_company_id:
            raise ValidationException.required_field("Company ID")

        # Validate company exists
        from backend.database.models import Company
        stmt = select(Company).where(Company.id == target_company_id)
        res = await db.execute(stmt)
        if not res.scalar_one_or_none():
            raise NotFoundException.resource("Фирма", target_company_id)

        from backend.database.models import StorageZone
        zone = StorageZone(
            name=input.name,
            temp_min=input.temp_min,
            temp_max=input.temp_max,
            description=input.description,
            is_active=input.is_active if input.is_active is not None else True,
            asset_type=input.asset_type or "KMA",
            zone_type=input.zone_type or "food",
            company_id=target_company_id
        )
        db.add(zone)
        await db.commit()
        await db.refresh(zone)
        return types.StorageZone.from_instance(zone)
    @strawberry.mutation
    async def update_storage_zone(self, input: inputs.UpdateStorageZoneInput,
                                info: strawberry.Info) -> types.StorageZone:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin", "Warehouse_Manager"]:
            raise PermissionDeniedException.for_action("manage")
        from backend.database.models import StorageZone
        from sqlalchemy import select
        stmt = select(StorageZone).where(StorageZone.id == input.id)
        res = await db.execute(stmt)
        zone = res.scalar_one_or_none()
        if not zone:
            raise NotFoundException.resource("Зона")
        if current_user.role.name not in ["super_admin"] and zone.company_id != current_user.company_id:
            raise PermissionDeniedException.for_resource("zone", "access")
        zone.name = input.name
        zone.temp_min = input.temp_min
        zone.temp_max = input.temp_max
        zone.description = input.description
        zone.is_active = input.is_active if input.is_active is not None else True
        zone.asset_type = input.asset_type or "KMA"
        zone.zone_type = input.zone_type or "food"
        await db.commit()
        await db.refresh(zone)
        return types.StorageZone.from_instance(zone)
    
    @strawberry.mutation
    async def create_cost_center(self, input: inputs.CostCenterInput, info: strawberry.Info) -> types.VehicleCostCenter:
        """Създай разходен център"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")
        
        target_company_id = input.company_id if current_user.role.name == "super_admin" else current_user.company_id
        if not target_company_id:
            raise ValidationException.required_field("company_id")
        
        from backend.database.models import VehicleCostCenter, Company
        stmt = select(Company).where(Company.id == target_company_id)
        res = await db.execute(stmt)
        if not res.scalar_one_or_none():
            raise NotFoundException.resource("Company", target_company_id)
        
        cost_center = VehicleCostCenter(
            name=input.name,
            department_id=input.department_id,
            is_active=input.is_active if input.is_active is not None else True,
            company_id=target_company_id
        )
        db.add(cost_center)
        await db.commit()
        await db.refresh(cost_center)
        return types.VehicleCostCenter.from_instance(cost_center)
    
    @strawberry.mutation
    async def update_cost_center(self, input: inputs.UpdateCostCenterInput, info: strawberry.Info) -> types.VehicleCostCenter:
        """Обнови разходен център"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")
        
        from backend.database.models import VehicleCostCenter
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
        return types.VehicleCostCenter.from_instance(cost_center)
    
    @strawberry.mutation
    async def delete_cost_center(self, id: int, info: strawberry.Info) -> bool:
        """Изтрий разходен център"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")
        
        from backend.database.models import VehicleCostCenter
        cost_center = await db.get(VehicleCostCenter, id)
        if not cost_center:
            raise NotFoundException.record("CostCenter")
        
        # Soft delete - mark as inactive
        cost_center.is_active = False
        await db.commit()
        return True
    
    @strawberry.mutation
    async def create_supplier(self, input: inputs.SupplierInput, info: strawberry.Info) -> types.Supplier:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin", "Warehouse_Manager"]:
            raise PermissionDeniedException.for_action("manage")
        target_company_id = input.company_id if current_user.role.name == "super_admin" else current_user.company_id
        if not target_company_id:
            raise ValidationException.required_field("Company ID")
        # Validate company exists
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
        from sqlalchemy import select
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
    async def create_ingredient(self, input: inputs.IngredientInput, info: strawberry.Info) -> types.Ingredient:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin", "Warehouse_Manager"]:
            raise PermissionDeniedException.for_action("manage")
        target_company_id = input.company_id if current_user.role.name == "super_admin" else current_user.company_id
        if not target_company_id:
            raise ValidationException.required_field("Company ID")
        # Validate company exists
        from backend.database.models import Company
        stmt = select(Company).where(Company.id == target_company_id)
        res = await db.execute(stmt)
        if not res.scalar_one_or_none():
            raise NotFoundException.resource("Фирма", target_company_id)
        from backend.database.models import Ingredient
        ingredient = Ingredient(
            name=input.name,
            unit=input.unit,
            barcode=input.barcode,
            baseline_min_stock=input.baseline_min_stock,
            current_price=input.current_price,
            storage_zone_id=input.storage_zone_id,
            is_perishable=input.is_perishable,
            expiry_warning_days=input.expiry_warning_days,
            allergens=input.allergens,
            company_id=target_company_id
        )
        db.add(ingredient)
        await db.commit()
        await db.refresh(ingredient)
        return types.Ingredient.from_instance(ingredient)

    @strawberry.mutation
    async def update_ingredient(self, input: inputs.IngredientInput, info: strawberry.Info) -> types.Ingredient:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin", "Warehouse_Manager"]:
            raise PermissionDeniedException.for_action("manage")

        from backend.database.models import Ingredient
        ingredient = await db.get(Ingredient, input.id)
        if not ingredient:
            raise NotFoundException.ingredient()

        if current_user.role.name != "super_admin" and ingredient.company_id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage")

        ingredient.name = input.name
        ingredient.unit = input.unit
        ingredient.barcode = input.barcode
        ingredient.baseline_min_stock = input.baseline_min_stock
        ingredient.current_price = input.current_price
        ingredient.storage_zone_id = input.storage_zone_id
        ingredient.is_perishable = input.is_perishable
        ingredient.expiry_warning_days = input.expiry_warning_days
        ingredient.allergens = input.allergens
        ingredient.product_type = input.product_type

        await db.commit()
        await db.refresh(ingredient)
        return types.Ingredient.from_instance(ingredient)

    @strawberry.mutation
    async def add_batch(self, input: inputs.BatchInput, info: strawberry.Info) -> types.Batch:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin", "Warehouse_Manager"]:
            raise PermissionDeniedException.for_action("manage")

        from backend.database.models import Batch, Ingredient
        # Verify ingredient belongs to company
        res = await db.get(Ingredient, input.ingredient_id)
        if not res or (current_user.role.name != "super_admin" and res.company_id != current_user.company_id):
            raise PermissionDeniedException.for_resource("ingredient", "manage")

        batch = Batch(
            ingredient_id=input.ingredient_id,
            batch_number=input.batch_number,
            quantity=input.quantity,
            expiry_date=input.expiry_date,
            supplier_id=input.supplier_id,
            invoice_number=input.invoice_number,
            storage_zone_id=input.storage_zone_id,
            status="active"
        )
        db.add(batch)
        await db.commit()
        await db.refresh(batch)
        return types.Batch.from_instance(batch)

    @strawberry.mutation
    async def update_batch_status(self, id: int, status: str, info: strawberry.Info) -> types.Batch:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin", "Warehouse_Manager"]:
            raise PermissionDeniedException.for_action("manage")

        from backend.database.models import Batch, Ingredient
        batch = await db.get(Batch, id)
        if not batch: raise NotFoundException.record("Batch")

        ingredient = await db.get(Ingredient, batch.ingredient_id)
        if current_user.role.name != "super_admin" and ingredient.company_id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage")

        batch.status = status
        await db.commit()
        await db.refresh(batch)
        return types.Batch.from_instance(batch)

    @strawberry.mutation
    async def update_batch(self, input: inputs.BatchInput, info: strawberry.Info) -> types.Batch:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin", "Warehouse_Manager"]:
            raise PermissionDeniedException.for_action("manage")

        from backend.database.models import Batch, Ingredient
        batch = await db.get(Batch, input.id)
        if not batch:
            raise NotFoundException.record("Batch")

        ingredient = await db.get(Ingredient, batch.ingredient_id)
        if current_user.role.name != "super_admin" and ingredient.company_id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage")

        batch.ingredient_id = input.ingredient_id
        batch.batch_number = input.batch_number
        batch.quantity = input.quantity
        batch.expiry_date = input.expiry_date
        batch.supplier_id = input.supplier_id
        batch.invoice_number = input.invoice_number
        batch.storage_zone_id = input.storage_zone_id

        await db.commit()
        await db.refresh(batch)
        return types.Batch.from_instance(batch)

    @strawberry.mutation
    async def consume_from_batch(
        self,
        batch_id: int,
        quantity: Decimal,
        reason: str,
        info: strawberry.Info,
        notes: Optional[str] = None,
    ) -> types.Batch:
        """Ръчно изразходване от конкретна партида"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException()

        from backend.database.models import Batch, StockConsumptionLog
        
        batch = await db.get(Batch, batch_id)
        if not batch: raise NotFoundException.record("Партида")
        
        if batch.quantity < quantity:
            raise ValidationException.field("quantity", f"Недостатъчно количество (Налично: {batch.quantity})")

        # 1. Намали количеството на партидата
        batch.quantity -= quantity
        if batch.quantity == 0:
            batch.status = "depleted"

        # 2. Създай лог
        log = StockConsumptionLog(
            ingredient_id=batch.ingredient_id,
            batch_id=batch.id,
            quantity=quantity,
            reason=reason,
            notes=notes,
            created_by=current_user.id
        )
        db.add(log)
        
        try:
            await db.commit()
            await db.refresh(batch)
            return types.Batch.from_instance(batch)
        except Exception as e:
            await db.rollback()
            raise handle_db_error(e)

    @strawberry.mutation
    async def auto_consume_fefo(
        self,
        ingredient_id: int,
        quantity: Decimal,
        reason: str,
        info: strawberry.Info,
        notes: Optional[str] = None,
    ) -> List[types.StockConsumptionLog]:
        """Автоматично изразходване по FEFO (First Expired, First Out)"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException()

        from backend.database.models import Batch, StockConsumptionLog
        from sqlalchemy import select

        # Вземи активни партиди, подредени по срок на годност
        stmt = select(Batch).where(
            Batch.ingredient_id == ingredient_id,
            Batch.status == "active",
            Batch.quantity > 0
        ).order_by(Batch.expiry_date.asc())
        
        result = await db.execute(stmt)
        batches = result.scalars().all()
        
        total_available = sum(b.quantity for b in batches)
        if total_available < quantity:
            raise ValidationException.field("quantity", f"Недостатъчна наличност (Общо: {total_available})")

        remaining_to_consume = quantity
        logs = []

        for batch in batches:
            if remaining_to_consume <= 0:
                break
            
            consume_qty = min(batch.quantity, remaining_to_consume)
            
            # Намали партидата
            batch.quantity -= consume_qty
            if batch.quantity == 0:
                batch.status = "depleted"
            
            # Лог
            log = StockConsumptionLog(
                ingredient_id=ingredient_id,
                batch_id=batch.id,
                quantity=consume_qty,
                reason=reason,
                notes=notes,
                created_by=current_user.id
            )
            db.add(log)
            logs.append(log)
            
            remaining_to_consume -= consume_qty

        try:
            await db.commit()
            return [types.StockConsumptionLog.from_instance(l) for l in logs]
        except Exception as e:
            await db.rollback()
            raise handle_db_error(e)

    @strawberry.mutation
    async def create_recipe(self, input: inputs.RecipeInput, info: strawberry.Info) -> types.Recipe:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        target_company_id = input.company_id if current_user.role.name == "super_admin" else current_user.company_id
        if not target_company_id:
            raise ValidationException.required_field("Company ID")

        # Validate company exists
        from backend.database.models import Company
        stmt = select(Company).where(Company.id == target_company_id)
        res = await db.execute(stmt)
        if not res.scalar_one_or_none():
            raise NotFoundException.resource("Фирма", target_company_id)

        from backend.database.models import Recipe, RecipeSection, RecipeIngredient, RecipeStep

        recipe = Recipe(
            name=input.name,
            description=input.description,
            yield_quantity=input.yield_quantity,
            yield_unit=input.yield_unit,
            shelf_life_days=input.shelf_life_days,
            shelf_life_frozen_days=input.shelf_life_frozen_days or 30,
            default_pieces=input.default_pieces or 12,
            production_time_days=input.production_time_days or 1,
            standard_quantity=input.standard_quantity or Decimal("1.0"),
            instructions=input.instructions,
            company_id=target_company_id
        )
        db.add(recipe)
        await db.flush()  # Get recipe ID

        # Create sections (3 parts: dough, cream, decoration)
        for section_input in input.sections:
            section = RecipeSection(
                recipe_id=recipe.id,
                section_type=section_input.section_type,
                name=section_input.name,
                shelf_life_days=section_input.shelf_life_days,
                waste_percentage=section_input.waste_percentage or Decimal("0"),
                section_order=section_input.section_order or 0
            )
            db.add(section)
            await db.flush()

            # Create ingredients for this section
            for ing in section_input.ingredients:
                ri = RecipeIngredient(
                    section_id=section.id,
                    ingredient_id=ing.ingredient_id,
                    quantity_gross=ing.quantity_gross,
                    quantity_net=ing.quantity_net or ing.quantity_gross,
                    waste_percentage=ing.waste_percentage or section_input.waste_percentage or Decimal("0"),
                    workstation_id=ing.workstation_id
                )
                db.add(ri)

            # Create steps for this section
            for step in section_input.steps:
                rs = RecipeStep(
                    section_id=section.id,
                    workstation_id=step.workstation_id,
                    name=step.name,
                    step_order=step.step_order or 0,
                    estimated_duration_minutes=step.estimated_duration_minutes
                )
                db.add(rs)

        await db.commit()
        await db.refresh(recipe)
        return types.Recipe.from_instance(recipe)

    @strawberry.mutation
    async def delete_recipe(self, id: int, info: strawberry.Info) -> bool:
        """Изтрий рецепта"""
        from backend.database.models import Recipe
        
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException()
        
        recipe = await db.get(Recipe, id)
        if not recipe:
            raise NotFoundException.recipe()
        
        if recipe.company_id != current_user.company_id:
            raise PermissionDeniedException()
        
        await db.delete(recipe)
        await db.commit()
        return True

    @strawberry.mutation
    async def update_recipe_price(
        self,
        recipe_id: int,
        input: inputs.RecipePriceUpdateInput,
        info: strawberry.Info
    ) -> types.Recipe:
        """Обнови цена на рецепта"""
        from backend.database import models
        from backend.database.models import sofia_now
        from backend.services.recipe_cost_calculator import RecipeCostCalculator
        
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)
        
        recipe = await db.get(models.Recipe, recipe_id)
        if not recipe:
            raise NotFoundException.recipe()
        
        if recipe.company_id != current_user.company_id:
            raise PermissionDeniedException()
        
        # Запиши в историята
        history = models.PriceHistory(
            recipe_id=recipe_id,
            old_price=recipe.selling_price or Decimal("0"),
            old_cost=recipe.cost_price or Decimal("0"),
            old_markup=recipe.markup_percentage or Decimal("0"),
            old_premium=recipe.premium_amount or Decimal("0"),
            new_markup=input.markup_percentage or Decimal("0"),
            new_premium=input.premium_amount or Decimal("0"),
            changed_by=current_user.id,
            reason=input.reason
        )
        
        # Актуализирай рецептата
        if input.markup_percentage is not None:
            recipe.markup_percentage = input.markup_percentage
        
        if input.premium_amount is not None:
            recipe.premium_amount = input.premium_amount
        
        if input.portions is not None:
            recipe.portions = input.portions
        
        # Изчислени новата продажна цена
        cost = recipe.cost_price or Decimal("0")
        recipe.selling_price = RecipeCostCalculator.calculate_final_price(
            cost,
            recipe.markup_percentage,
            recipe.premium_amount
        )
        recipe.last_price_update = sofia_now()
        
        # Update new price in history
        history.new_price = recipe.selling_price
        history.new_cost = recipe.cost_price
        
        db.add(history)
        await db.commit()
        await db.refresh(recipe)
        
        return types.Recipe.from_instance(recipe)

    @strawberry.mutation
    async def calculate_recipe_cost(
        self,
        recipe_id: int,
        info: strawberry.Info
    ) -> types.RecipeCostResult:
        """Изчисли себестойността на рецепта"""
        from backend.database import models
        from backend.database.models import sofia_now
        from backend.services.recipe_cost_calculator import RecipeCostCalculator
        
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)
        
        recipe = await db.get(models.Recipe, recipe_id)
        if not recipe:
            raise NotFoundException.recipe()
        
        if recipe.company_id != current_user.company_id:
            raise PermissionDeniedException()
        
        cost = await RecipeCostCalculator.calculate_recipe_cost(db, recipe_id)
        
        final_price = RecipeCostCalculator.calculate_final_price(
            cost,
            recipe.markup_percentage,
            recipe.premium_amount
        )
        
        markup_amount = RecipeCostCalculator.calculate_markup_amount(
            cost,
            recipe.markup_percentage
        )
        
        # Обнови себестойността в рецептата
        recipe.cost_price = cost
        recipe.price_calculated_at = sofia_now()
        recipe.selling_price = final_price
        recipe.last_price_update = sofia_now()
        
        await db.commit()
        await db.refresh(recipe)
        
        portion_price = Decimal("0")
        if recipe.default_pieces and recipe.default_pieces > 0:
            portion_price = final_price / recipe.default_pieces
        
        return types.RecipeCostResult(
            recipe_id=recipe_id,
            recipe_name=recipe.name,
            cost_price=cost,
            markup_amount=markup_amount,
            premium_amount=recipe.premium_amount or Decimal("0"),
            final_price=final_price,
            portion_price=portion_price
        )

    @strawberry.mutation
    async def recalculate_all_recipe_costs(
        self,
        info: strawberry.Info
    ) -> List[types.RecalculateResult]:
        """Преизчисли себестойността на всички рецепти"""
        from backend.database import models
        from backend.database.models import sofia_now
        from sqlalchemy import select
        from backend.services.recipe_cost_calculator import RecipeCostCalculator
        
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)
        
        stmt = select(models.Recipe).where(
            models.Recipe.company_id == current_user.company_id
        )
        res = await db.execute(stmt)
        
        results: List[types.RecalculateResult] = []
        
        for recipe in res.scalars().all():
            cost = await RecipeCostCalculator.calculate_recipe_cost(db, recipe.id)
            recipe.cost_price = cost
            recipe.price_calculated_at = sofia_now()
            
            markup_amount = Decimal("0")
            final_price = Decimal("0")
            portion_price = Decimal("0")
            
            if recipe.markup_percentage or recipe.premium_amount:
                markup_amount = RecipeCostCalculator.calculate_markup_amount(cost, recipe.markup_percentage)
                final_price = RecipeCostCalculator.calculate_final_price(
                    cost,
                    recipe.markup_percentage,
                    recipe.premium_amount
                )
                portions = recipe.portions or 1
                portion_price = final_price / portions if portions > 0 else final_price
                recipe.selling_price = final_price
                recipe.last_price_update = sofia_now()
            
            results.append(types.RecalculateResult(
                recipe_id=recipe.id,
                recipe_name=recipe.name,
                cost_price=cost,
                markup_amount=markup_amount,
                final_price=final_price,
                portion_price=portion_price
            ))
        
        await db.commit()
        return results

    @strawberry.mutation
    async def create_workstation(self, name: str, description: Optional[str], company_id: int,
                                 info: strawberry.Info) -> types.Workstation:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        target_company_id = company_id if current_user.role.name == "super_admin" else current_user.company_id
        if not target_company_id:
            raise ValidationException.required_field("Company ID")

        # Validate company exists
        from backend.database.models import Company
        stmt = select(Company).where(Company.id == target_company_id)
        res = await db.execute(stmt)
        if not res.scalar_one_or_none():
            raise NotFoundException.resource("Фирма", target_company_id)

        from backend.database.models import Workstation
        ws = Workstation(
            name=name,
            description=description,
            company_id=target_company_id
        )
        db.add(ws)
        await db.commit()
        await db.refresh(ws)
        return types.Workstation.from_instance(ws)

    @strawberry.mutation
    async def create_production_order(self, input: inputs.ProductionOrderInput,
                                      info: strawberry.Info) -> types.ProductionOrder:
        from backend.database.transaction_manager import atomic_transaction
        
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        target_company_id = input.company_id if current_user.role.name == "super_admin" else current_user.company_id
        if not target_company_id:
            raise ValidationException.required_field("Company ID")

        async with atomic_transaction(db) as tx:
            # Validate company exists
            from backend.database.models import Company
            stmt = select(Company).where(Company.id == target_company_id)
            res = await tx.execute(stmt)
            if not res.scalar_one_or_none():
                raise NotFoundException.resource("Фирма", target_company_id)

            from backend.database.models import ProductionOrder, Recipe, ProductionTask, Batch, sofia_now
            from datetime import timedelta
            from sqlalchemy.orm import selectinload

            # Convert due_date to naive datetime if it has timezone info
            due_date = input.due_date
            if due_date.tzinfo is not None:
                due_date = due_date.replace(tzinfo=None)
            
            # Calculate production_deadline
            production_deadline = None
            stmt = select(Recipe).where(Recipe.id == input.recipe_id).options(
                selectinload(Recipe.ingredients),
                selectinload(Recipe.steps)
            )
            recipe = (await tx.execute(stmt)).scalar_one_or_none()
            
            if not recipe:
                raise NotFoundException.recipe()

            if recipe.production_deadline_days and recipe.shelf_life_days:
                pd_days = recipe.production_deadline_days
                if pd_days:
                    production_deadline = due_date - timedelta(days=pd_days)
                    if production_deadline.tzinfo is not None:
                        production_deadline = production_deadline.replace(tzinfo=None)

            # 1. Create Order
            order = ProductionOrder(
                recipe_id=input.recipe_id,
                quantity=input.quantity,
                due_date=due_date,
                production_deadline=production_deadline,
                notes=input.notes,
                created_by=current_user.id,
                company_id=target_company_id,
                status="awaiting_stock"  # Initial status
            )

            # 2. Check stock availability (Simple version)
            all_available = True
            for ri in recipe.ingredients:
                required = ri.quantity_gross * input.quantity
                # Check batches for this ingredient
                stmt = select(Batch).where(Batch.ingredient_id == ri.ingredient_id, Batch.status == "active")
                res = await tx.execute(stmt)
                available = sum((b.quantity for b in res.scalars().all()), Decimal("0"))
                if available < required:
                    all_available = False
                    break

            if all_available:
                order.status = "ready"

            tx.add(order)
            await tx.flush()

            # 3. Create initial tasks from recipe steps
            for step in recipe.steps:
                task = ProductionTask(
                    order_id=order.id,
                    workstation_id=step.workstation_id,
                    step_id=step.id,
                    name=step.name,
                    status="pending"
                )
                tx.add(task)

            await tx.refresh(order)
            return types.ProductionOrder.from_instance(order)

    @strawberry.mutation
    async def update_production_order_status(self, id: int, status: str,
                                             info: strawberry.Info) -> types.ProductionOrder:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import ProductionOrder
        order = await db.get(ProductionOrder, id)
        if not order: raise NotFoundException.order()

        if current_user.role.name != "super_admin" and order.company_id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage")

        order.status = status
        await db.commit()
        await db.refresh(order)
        return types.ProductionOrder.from_instance(order)

    @strawberry.mutation
    async def confirm_production_order(self, id: int, info: strawberry.Info) -> types.ProductionOrder:
        """Department head confirms order is ready for transport"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import (
            ProductionOrder, ProductionTask, ProductionRecord,
            ProductionRecordIngredient, ProductionRecordWorker,
            Recipe, Batch, sofia_now
        )
        from sqlalchemy import select
        from datetime import timedelta

        order = await db.get(ProductionOrder, id)
        if not order: raise NotFoundException.order()

        if current_user.role.name != "super_admin" and order.company_id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage")

        if order.status != "ready":
            raise ValidationException.field("Order status", "Трябва да е 'ready' за потвърждение")

        from sqlalchemy.orm import selectinload

        # Get recipe for shelf_life_days and its ingredients
        stmt = select(Recipe).where(Recipe.id == order.recipe_id).options(
            selectinload(Recipe.ingredients).selectinload(RecipeIngredient.ingredient)
        )
        recipe = (await db.execute(stmt)).scalar_one_or_none()
        
        shelf_life_days = recipe.shelf_life_days if recipe else 7
        expiry_date = sofia_now().date() + timedelta(days=shelf_life_days)

        order.status = "confirmed"
        order.confirmed_at = sofia_now()
        order.confirmed_by = current_user.id

        # Create production record for traceability
        record = ProductionRecord(
            order_id=order.id,
            confirmed_by=current_user.id,
            confirmed_at=sofia_now(),
            expiry_date=expiry_date
        )
        db.add(record)
        await db.flush()

        # Get all tasks and their workers (regardless of status - record who worked on it)
        stmt = select(ProductionTask).where(ProductionTask.order_id == order.id)
        res = await db.execute(stmt)
        tasks = res.scalars().all()

        for task in tasks:
            if task.assigned_user_id:
                worker = ProductionRecordWorker(
                    record_id=record.id,
                    user_id=task.assigned_user_id,
                    workstation_id=task.workstation_id,
                    task_id=task.id,
                    started_at=task.started_at,
                    completed_at=task.completed_at
                )
                db.add(worker)

        # Get recipe ingredients with batch info
        if recipe:
            for ri in recipe.ingredients:
                # Get the earliest expiry batch for this ingredient
                stmt = select(Batch).where(
                    Batch.ingredient_id == ri.ingredient_id,
                    Batch.status == "active",
                    Batch.quantity > 0
                ).order_by(Batch.expiry_date.asc())
                res = await db.execute(stmt)
                batches = res.scalars().all()

                if batches:
                    batch = batches[0]  # Use FIFO - earliest expiry
                    record_ing = ProductionRecordIngredient(
                        record_id=record.id,
                        ingredient_id=ri.ingredient_id,
                        batch_number=batch.batch_number or f"BATCH-{batch.id}",
                        expiry_date=batch.expiry_date,
                        quantity_used=ri.quantity_gross * order.quantity,
                        unit=ri.ingredient.unit if ri.ingredient else None
                    )
                    db.add(record_ing)
                else:
                    # No batch found - record without batch number
                    record_ing = ProductionRecordIngredient(
                        record_id=record.id,
                        ingredient_id=ri.ingredient_id,
                        batch_number="N/A",
                        expiry_date=None,
                        quantity_used=ri.quantity_gross * order.quantity,
                        unit=ri.ingredient.unit if ri.ingredient else None
                    )
                    db.add(record_ing)

        await db.commit()
        await db.refresh(order)
        return types.ProductionOrder.from_instance(order)

    @strawberry.mutation
    async def mark_task_scrap(self, id: int, info: strawberry.Info) -> types.ProductionTask:
        """Mark a task as scrap - deducts all ingredients for that task"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import ProductionTask, ProductionOrder, Recipe, RecipeIngredient, Batch, \
            RecipeStep, sofia_now
        from sqlalchemy import select

        task = await db.get(ProductionTask, id)
        if not task: raise NotFoundException.resource("Task")

        order = await db.get(ProductionOrder, task.order_id)
        if current_user.role.name != "super_admin" and order.company_id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage")

        # Mark task as scrap
        task.is_scrap = True
        task.status = "completed"
        task.completed_at = sofia_now()

        from sqlalchemy.orm import selectinload
        # Get recipe and step to determine which ingredients to deduct
        stmt_recipe = select(Recipe).where(Recipe.id == order.recipe_id).options(
            selectinload(Recipe.ingredients)
        )
        recipe = (await db.execute(stmt_recipe)).scalar_one_or_none()

        # Deduct all ingredients for this task (full quantity)
        if recipe:
            for ri in recipe.ingredients:
                needed = ri.quantity_gross * order.quantity
                stmt_batches = select(Batch).where(
                    Batch.ingredient_id == ri.ingredient_id,
                    Batch.status == "active"
                ).order_by(Batch.expiry_date.asc())

                batches = (await db.execute(stmt_batches)).scalars().all()
                for batch in batches:
                    if needed <= 0: break

                    if batch.quantity >= needed:
                        batch.quantity -= needed
                        needed = 0
                    else:
                        needed -= batch.quantity
                        batch.quantity = 0
                        batch.status = "depleted"

        await db.commit()
        await db.refresh(task)
        return types.ProductionTask.from_instance(task)

    @strawberry.mutation
    async def scrap_task(self, input: inputs.ScrapTaskInput, info: strawberry.Info) -> types.ProductionTask:
        """Scrap part of a task quantity - logs the scrap and reduces the order quantity"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import ProductionTask, ProductionOrder, ProductionScrapLog, sofia_now

        task = await db.get(ProductionTask, input.task_id)
        if not task: raise NotFoundException.resource("Task")

        order = await db.get(ProductionOrder, task.order_id)
        if current_user.role.name != "super_admin" and order.company_id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage")

        # Validate quantity
        if input.quantity <= 0:
            raise ValidationException.field("Quantity", "Трябва да е положително")

        if input.quantity > float(order.quantity):
            raise ValidationException.field("Quantity", "Не може да надвишава количеството на поръчката")

        # Create scrap log
        scrap_log = ProductionScrapLog(
            task_id=task.id,
            user_id=current_user.id,
            quantity=input.quantity,
            reason=input.reason,
        )
        db.add(scrap_log)

        # Reduce order quantity
        order.quantity = Decimal(str(float(order.quantity) - input.quantity))

        await db.commit()
        await db.refresh(task)
        await db.refresh(order)
        return types.ProductionTask.from_instance(task)

    @strawberry.mutation
    async def get_scrap_logs(self, task_id: int, info: strawberry.Info) -> List[types.ProductionScrapLog]:
        """Get scrap logs for a task"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import ProductionScrapLog, ProductionTask, ProductionOrder
        from sqlalchemy import select

        task = await db.get(ProductionTask, task_id)
        if not task: raise NotFoundException.resource("Task")

        order = await db.get(ProductionOrder, task.order_id)
        if current_user.role.name != "super_admin" and order.company_id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage")

        stmt = select(ProductionScrapLog).where(ProductionScrapLog.task_id == task_id).order_by(
            ProductionScrapLog.created_at.desc())
        res = await db.execute(stmt)
        return [types.ProductionScrapLog.from_instance(s) for s in res.scalars().all()]

    @strawberry.mutation
    async def update_production_task_status(self, id: int, status: str, info: strawberry.Info) -> types.ProductionTask:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import ProductionTask, ProductionOrder, sofia_now
        task = await db.get(ProductionTask, id)
        if not task: raise NotFoundException.resource("Task")

        # Verify ownership
        order = await db.get(ProductionOrder, task.order_id)
        if current_user.role.name != "super_admin" and order.company_id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage")

        task.status = status
        if status == "in_progress" and not task.started_at:
            task.started_at = sofia_now()
            task.assigned_user_id = current_user.id
            # Also update order status if it's the first task
            if order.status == "ready":
                order.status = "in_progress"
        elif status == "completed":
            task.completed_at = sofia_now()

            # --- AUTO CREATE SEMI-FINISHED PRODUCT ---
            from backend.database.models import Recipe, RecipeStep, Ingredient, Batch
            recipe = await db.get(Recipe, order.recipe_id)

            if recipe:
                # Get the step that was completed
                step = await db.get(RecipeStep, task.step_id) if task.step_id else None

                # Create semi-finished product name
                semi_name = f"{recipe.name}"
                if step:
                    semi_name = f"{recipe.name} - {step.name}"

                # Check if semi-finished ingredient already exists
                stmt_semi = select(Ingredient).where(
                    Ingredient.company_id == order.company_id,
                    Ingredient.name == semi_name,
                    Ingredient.product_type == "semi_finished"
                )
                res_semi = await db.execute(stmt_semi)
                semi_ingredient = res_semi.scalars().first()

                if not semi_ingredient:
                    # Create new semi-finished ingredient
                    semi_ingredient = Ingredient(
                        name=semi_name,
                        unit=recipe.yield_unit,
                        product_type="semi_finished",
                        company_id=order.company_id,
                        shelf_life_days=recipe.shelf_life_days
                    )
                    db.add(semi_ingredient)
                    await db.flush()

                # Create batch for semi-finished product
                expiry_days = recipe.shelf_life_days or 7
                from datetime import timedelta
                expiry_date = sofia_now().date() + timedelta(days=expiry_days)

                semi_batch = Batch(
                    ingredient_id=semi_ingredient.id,
                    batch_number=f"SEMI-{order.id}-{task.id}",
                    quantity=order.quantity,
                    status="active",
                    expiry_date=expiry_date
                )
                db.add(semi_batch)
            # ---------------------------------------

            # Check if all tasks for this order are completed
            stmt = select(ProductionTask).where(ProductionTask.order_id == order.id)
            res = await db.execute(stmt)
            all_tasks = res.scalars().all()
            if all(t.status == "completed" or t.id == id for t in all_tasks):
                order.status = "completed"

                # --- AUTO STOCK DEDUCTION (FEFO) ---
                from backend.database.models import Recipe as RecipeModel, RecipeIngredient, Batch as BatchModel, StockConsumptionLog, sofia_now
                from decimal import Decimal
                
                recipe = await db.get(RecipeModel, order.recipe_id)
                stmt_ings = select(RecipeIngredient).where(RecipeIngredient.recipe_id == recipe.id)
                recipe_ings = (await db.execute(stmt_ings)).scalars().all()
                
                total_cost = Decimal("0")

                for ri in recipe_ings:
                    needed = ri.quantity_gross * order.quantity
                    # Fetch active batches for this ingredient, ordered by expiry_date (FEFO)
                    stmt_batches = select(BatchModel).where(
                        BatchModel.ingredient_id == ri.ingredient_id,
                        BatchModel.status == "active"
                    ).order_by(BatchModel.expiry_date.asc())

                    batches = (await db.execute(stmt_batches)).scalars().all()
                    for batch in batches:
                        if needed <= 0: break

                        consumed_qty = min(needed, batch.quantity)
                        
                        # Calculate price from batch
                        batch_price = batch.price_no_vat or batch.price_with_vat or 0
                        consumed_value = consumed_qty * batch_price
                        total_cost += Decimal(str(consumed_value))

                        # Update batch quantity
                        batch.quantity -= consumed_qty
                        needed -= consumed_qty
                        
                        if batch.quantity <= 0:
                            batch.status = "depleted"
                        
                        # Log consumption with price
                        log = StockConsumptionLog(
                            ingredient_id=ri.ingredient_id,
                            batch_id=batch.id,
                            quantity=Decimal(str(consumed_qty)),
                            price_per_unit=batch_price,
                            total_price=consumed_value,
                            reason="production",
                            production_order_id=order.id,
                            created_by=current_user.id
                        )
                        db.add(log)
                # ----------------------------------
                
                # Update recipe cost price
                if recipe:
                    recipe.cost_price = total_cost
                    recipe.price_calculated_at = sofia_now()

        await db.commit()
        await db.refresh(task)
        return types.ProductionTask.from_instance(task)

    @strawberry.mutation
    async def start_inventory_session(self, info: strawberry.Info) -> types.InventorySession:
        """Start a new inventory session"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import InventorySession, sofia_now

        session = InventorySession(
            company_id=current_user.company_id,
            started_by=current_user.id,
            started_at=sofia_now(),
            status="active"
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return types.InventorySession.from_instance(session)

    @strawberry.mutation
    async def add_inventory_item(
            self,
            session_id: int,
            ingredient_id: int,
            found_quantity: float,
            info: strawberry.Info
    ) -> types.InventoryItem:
        """Add or update an item in the inventory session"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import InventorySession, InventoryItem, Ingredient, Batch
        from sqlalchemy import func, select

        # Verify session exists and belongs to company
        session = await db.get(InventorySession, session_id)
        if not session: raise NotFoundException.session()
        if session.company_id != current_user.company_id and current_user.role.name != "super_admin":
            raise PermissionDeniedException.for_action("manage")
        if session.status != "active":
            raise ValidationException.field("Session", "Не е активна")

        # Get ingredient
        ingredient = await db.get(Ingredient, ingredient_id)
        if not ingredient: raise NotFoundException.ingredient()

        # Calculate system quantity (sum of all active batches)
        stmt = select(func.coalesce(func.sum(Batch.quantity), 0)).where(
            Batch.ingredient_id == ingredient_id,
            Batch.status == "active"
        )
        res = await db.execute(stmt)
        system_qty = res.scalar() or 0

        # Calculate difference
        difference = found_quantity - float(system_qty)

        # Check if item already exists in session
        stmt = select(InventoryItem).where(
            InventoryItem.session_id == session_id,
            InventoryItem.ingredient_id == ingredient_id
        )
        res = await db.execute(stmt)
        item = res.scalars().first()

        if item:
            # Update existing item
            item.found_quantity = found_quantity
            item.system_quantity = system_qty
            item.difference = difference
        else:
            # Create new item
            item = InventoryItem(
                session_id=session_id,
                ingredient_id=ingredient_id,
                found_quantity=found_quantity,
                system_quantity=system_qty,
                difference=difference
            )
            db.add(item)

        await db.commit()
        await db.refresh(item)
        return types.InventoryItem.from_instance(item)

    @strawberry.mutation
    async def complete_inventory_session(self, session_id: int, info: strawberry.Info) -> types.InventorySession:
        """Complete inventory session and adjust quantities"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import InventorySession, InventoryItem, Batch, sofia_now
        from sqlalchemy import select
        import uuid

        # Verify session
        session = await db.get(InventorySession, session_id)
        if not session: raise NotFoundException.session()
        if session.company_id != current_user.company_id and current_user.role.name != "super_admin":
            raise PermissionDeniedException.for_action("manage")
        if session.status != "active":
            raise ValidationException.field("Session", "Не е активна")

        # Get all items
        stmt = select(InventoryItem).where(InventoryItem.session_id == session_id)
        res = await db.execute(stmt)
        items = res.scalars().all()

        # Generate protocol number
        protocol_number = f"INV-{sofia_now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"

        # Adjust quantities in batches
        for item in items:
            if item.found_quantity is None:
                continue

            # Get all batches for this ingredient
            stmt = select(Batch).where(
                Batch.ingredient_id == item.ingredient_id,
                Batch.status == "active"
            ).order_by(Batch.expiry_date.asc())
            res = await db.execute(stmt)
            batches = res.scalars().all()

            # Calculate target quantity
            target_qty = float(item.found_quantity)
            current_qty = sum(float(b.quantity) for b in batches)
            diff = target_qty - current_qty

            if abs(diff) < 0.001:  # Already correct
                item.adjusted = True
                continue

            if diff > 0:
                # Need more - create new batch
                new_batch = Batch(
                    ingredient_id=item.ingredient_id,
                    batch_number=f"ADJ-{protocol_number}",
                    quantity=diff,
                    status="active",
                    expiry_date=None
                )
                db.add(new_batch)
            else:
                # Need less - reduce from batches (FEFO)
                remaining = abs(diff)
                for batch in batches:
                    if remaining <= 0:
                        break
                    if batch.quantity >= remaining:
                        batch.quantity -= remaining
                        remaining = 0
                    else:
                        remaining -= batch.quantity
                        batch.quantity = 0
                        batch.status = "depleted"

            item.adjusted = True

        # Complete session
        session.status = "completed"
        session.completed_at = sofia_now()
        session.protocol_number = protocol_number

        await db.commit()
        await db.refresh(session)
        return types.InventorySession.from_instance(session)

    @strawberry.mutation
    async def create_invoice(
            self,
            invoice_data: inputs.InvoiceInput,
            info: strawberry.Info
    ) -> types.Invoice:
        """Create a new invoice with items"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database.transaction_manager import atomic_transaction
        from backend.database import models
        from decimal import Decimal

        async with atomic_transaction(db) as tx:
            # Generate invoice number
            year = invoice_data.date.year
            prefix = "ВХ" if invoice_data.type == "incoming" else "ИЗХ"

            stmt = select(models.Invoice).where(
                models.Invoice.number.like(f"{prefix}-{year}-%")
            ).order_by(models.Invoice.number.desc())
            res = await tx.execute(stmt)
            last_invoice = res.scalars().first()

            if last_invoice:
                last_num = int(last_invoice.number.split("-")[-1])
                new_num = last_num + 1
            else:
                new_num = 1

            invoice_number = f"{prefix}-{year}-{new_num:04d}"

            # Calculate totals
            subtotal = Decimal("0")
            for item in invoice_data.items:
                item_total = item.quantity * item.unit_price
                item_discount = item_total * (item.discount_percent / 100)
                item_total = item_total - item_discount
                subtotal += item_total

            discount_amount = subtotal * (invoice_data.discount_percent / 100)
            subtotal_after_discount = subtotal - discount_amount
            vat_amount = subtotal_after_discount * (invoice_data.vat_rate / 100)
            total = subtotal_after_discount + vat_amount

            # Create invoice
            invoice = models.Invoice(
                number=invoice_number,
                type=invoice_data.type,
                document_type=invoice_data.document_type,
                griff=invoice_data.griff,
                description=invoice_data.description,
                date=invoice_data.date,
                supplier_id=invoice_data.supplier_id,
                batch_id=invoice_data.batch_id,
                client_name=invoice_data.client_name,
                client_eik=invoice_data.client_eik,
                client_address=invoice_data.client_address,
                subtotal=subtotal,
                discount_percent=invoice_data.discount_percent,
                discount_amount=discount_amount,
                vat_rate=invoice_data.vat_rate,
                vat_amount=vat_amount,
                total=total,
                payment_method=invoice_data.payment_method,
                delivery_method=invoice_data.delivery_method,
                due_date=invoice_data.due_date,
                payment_date=invoice_data.payment_date,
                status=invoice_data.status,
                notes=invoice_data.notes,
                company_id=invoice_data.company_id,
                created_by=current_user.id
            )

            tx.add(invoice)
            await tx.flush()

            # Create invoice items
            for item in invoice_data.items:
                item_total = item.quantity * item.unit_price
                item_discount = item_total * (item.discount_percent / 100)
                item_total = item_total - item_discount

                invoice_item = models.InvoiceItem(
                    invoice_id=invoice.id,
                    ingredient_id=item.ingredient_id,
                    batch_id=item.batch_id,
                    name=item.name,
                    quantity=item.quantity,
                    unit=item.unit,
                    unit_price=item.unit_price,
                    unit_price_with_vat=item.unit_price_with_vat,
                    discount_percent=item.discount_percent,
                    total=item_total,
                    expiration_date=datetime.datetime.strptime(item.expiration_date, '%Y-%m-%d').date() if item.expiration_date else None,
                    batch_number=item.batch_number
                )
                tx.add(invoice_item)
                
                # Обнови цената на партидата от фактурата
                if item.batch_id:
                    batch = await tx.get(models.Batch, item.batch_id)
                    if batch:
                        batch.price_no_vat = float(item.unit_price)
                        batch.price_with_vat = float(item.unit_price_with_vat or item.unit_price * Decimal("1.2"))

            return types.Invoice.from_instance(invoice, tx)

        # Log the operation
        log_entry = models.OperationLog(
            operation="create",
            entity_type="invoice",
            entity_id=invoice.id,
            user_id=current_user.id,
            changes={"number": invoice.number, "type": invoice.type, "total": str(total), "status": invoice_data.status}
        )
        db.add(log_entry)

        # Auto-create cash journal entry if paid in cash
        if invoice_data.payment_method == "cash" and invoice_data.status == "paid":
            cash_entry = models.CashJournalEntry(
                date=invoice_data.payment_date or invoice_data.date,
                operation_type="expense" if invoice_data.type == "incoming" else "income",
                amount=total,
                description=f"Фактура {invoice.number}",
                reference_type="invoice",
                reference_id=invoice.id,
                company_id=invoice.company_id,
                created_by=current_user.id
            )
            db.add(cash_entry)

        # Auto-create accounting entries
        company = await db.get(models.Company, invoice.company_id)
        if company and invoice_data.status in ["paid", "sent"]:
            from backend.services.accounting_service import AccountingService
            accounting_service = AccountingService(db)
            entries = await accounting_service.create_invoice_entries(invoice, company, current_user)
            if entries:
                for entry in entries:
                    db.add(entry)

        await db.commit()
        return types.Invoice.from_instance(invoice)

    @strawberry.mutation
    async def update_invoice(
            self,
            id: int,
            invoice_data: inputs.InvoiceInput,
            info: strawberry.Info
    ) -> types.Invoice:
        """Update an existing invoice"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database import models
        from decimal import Decimal

        invoice = await db.get(models.Invoice, id)
        if not invoice:
            raise NotFoundException.record("Invoice")

        if current_user.role.name != "super_admin" and invoice.company_id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage")

        # READONLY check: paid, cancelled, and corrected invoices cannot be edited
        readonly_statuses = ['paid', 'cancelled', 'corrected']
        if invoice.status in readonly_statuses:
            raise ValidationException(
                detail=f"Фактура с статус '{invoice.status}' е в READONLY режим и не може да се редактира. Платена/анулирана/коригирана фактура не може да се променя."
            )

        # Validate status transition
        current_status = invoice.status
        new_status = invoice_data.status

        ALLOWED_TRANSITIONS = {
            'draft': ['sent', 'paid', 'cancelled'],
            'sent': ['paid', 'cancelled'],
            'overdue': ['paid', 'cancelled'],
            'corrected': []  # No transitions from corrected
        }
        # NOTE: 'paid' and 'cancelled' are handled by the READONLY check above

        if new_status != current_status:
            allowed = ALLOWED_TRANSITIONS.get(current_status, [])
            if new_status not in allowed:
                allowed_text = ', '.join([f"'{s}'" for s in allowed]) if allowed else 'няма'
                raise ValidationException.field(
                    "status", 
                    f"Не може да промените статуса от '{current_status}' на '{new_status}'. Позволени: {allowed_text}"
                )

            # Special protection: accountant, head_accountant, and super_admin can cancel paid invoices
            if current_status == 'paid' and new_status == 'cancelled':
                if current_user.role.name not in ["super_admin", "head_accountant", "accountant"]:
                    raise PermissionDeniedException(
                        detail="Нямате права да анулирате платена фактура. За това действие са необходими права на счетоводител или по-високи."
                    )
                # Log the cancellation of paid invoice
                log_entry = models.OperationLog(
                    operation="cancel_paid",
                    entity_type="invoice",
                    entity_id=invoice.id,
                    user_id=current_user.id,
                    company_id=current_user.company_id,
                    changes={
                        "number": invoice.number,
                        "previous_status": "paid",
                        "new_status": "cancelled",
                        "amount": str(invoice.total),
                        "role": current_user.role.name
                    }
                )
                db.add(log_entry)

        # Update basic fields
        invoice.type = invoice_data.type
        invoice.document_type = invoice_data.document_type
        invoice.griff = invoice_data.griff
        invoice.description = invoice_data.description
        invoice.date = invoice_data.date
        invoice.supplier_id = invoice_data.supplier_id
        invoice.batch_id = invoice_data.batch_id
        invoice.client_name = invoice_data.client_name
        invoice.client_eik = invoice_data.client_eik
        invoice.client_address = invoice_data.client_address
        invoice.discount_percent = invoice_data.discount_percent
        invoice.vat_rate = invoice_data.vat_rate
        invoice.payment_method = invoice_data.payment_method
        invoice.delivery_method = invoice_data.delivery_method
        invoice.due_date = invoice_data.due_date
        invoice.payment_date = invoice_data.payment_date
        invoice.status = invoice_data.status
        invoice.notes = invoice_data.notes

        # Calculate totals
        subtotal = Decimal("0")
        for item in invoice_data.items:
            item_total = item.quantity * item.unit_price
            item_discount = item_total * (item.discount_percent / 100)
            item_total = item_total - item_discount
            subtotal += item_total

        discount_amount = subtotal * (invoice_data.discount_percent / 100)
        subtotal_after_discount = subtotal - discount_amount
        vat_amount = subtotal_after_discount * (invoice_data.vat_rate / 100)
        total = subtotal_after_discount + vat_amount

        invoice.subtotal = subtotal
        invoice.discount_amount = discount_amount
        invoice.vat_amount = vat_amount
        invoice.total = total

        # Update items: delete old and create new (simpler approach)
        from sqlalchemy import delete
        await db.execute(delete(models.InvoiceItem).where(models.InvoiceItem.invoice_id == id))

        for item in invoice_data.items:
            item_total = item.quantity * item.unit_price
            item_discount = item_total * (item.discount_percent / 100)
            item_total = item_total - item_discount

            invoice_item = models.InvoiceItem(
                invoice_id=invoice.id,
                ingredient_id=item.ingredient_id,
                batch_id=item.batch_id,
                name=item.name,
                quantity=item.quantity,
                unit=item.unit,
                unit_price=item.unit_price,
                unit_price_with_vat=item.unit_price_with_vat,
                discount_percent=item.discount_percent,
                total=item_total,
                expiration_date=datetime.datetime.strptime(item.expiration_date, '%Y-%m-%d').date() if item.expiration_date else None,
                batch_number=item.batch_number
            )
            db.add(invoice_item)

        # Log the operation
        log_entry = models.OperationLog(
            operation="update",
            entity_type="invoice",
            entity_id=invoice.id,
            user_id=current_user.id,
            changes={"number": invoice.number, "total": str(total), "status": invoice_data.status}
        )
        db.add(log_entry)

        # Handle cash journal entry
        if invoice_data.payment_method == "cash" and invoice_data.status == "paid":
            existing_entry = await db.execute(
                select(models.CashJournalEntry).where(
                    models.CashJournalEntry.reference_type == "invoice",
                    models.CashJournalEntry.reference_id == invoice.id
                )
            )
            existing = existing_entry.scalars().first()

            if not existing:
                cash_entry = models.CashJournalEntry(
                    date=invoice_data.payment_date or invoice_data.date,
                    operation_type="expense" if invoice_data.type == "incoming" else "income",
                    amount=total,
                    description=f"Фактура {invoice.number}",
                    reference_type="invoice",
                    reference_id=invoice.id,
                    company_id=invoice.company_id,
                    created_by=current_user.id
                )
                db.add(cash_entry)
            else:
                # Update existing cash entry
                existing.amount = total
                existing.date = invoice_data.payment_date or invoice_data.date
                db.add(existing)

        # Auto-create accounting entries when status changes to paid/sent
        company = await db.get(models.Company, invoice.company_id)
        if company and invoice_data.status in ["paid", "sent"]:
            # Check if entries already exist
            existing_accounting = await db.execute(
                select(models.AccountingEntry).where(
                    models.AccountingEntry.invoice_id == invoice.id
                )
            )
            existing_acct_entries = existing_accounting.scalars().all()
            
            if not existing_acct_entries:
                from backend.services.accounting_service import AccountingService
                accounting_service = AccountingService(db)
                entries = await accounting_service.create_invoice_entries(invoice, company, current_user)
                if entries:
                    for entry in entries:
                        db.add(entry)

        await db.commit()
        await db.refresh(invoice)
        return types.Invoice.from_instance(invoice)

    @strawberry.mutation
    async def delete_invoice(
            self,
            id: int,
            info: strawberry.Info
    ) -> bool:
        """Delete an invoice - ALWAYS BLOCKED"""
        raise ValidationException(
            detail="Създадена фактура не може да се изтрие. Може само да се анулира."
        )

    @strawberry.mutation
    async def create_invoice_from_batch(
            self,
            batch_id: int,
            info: strawberry.Info
    ) -> types.Invoice:
        """Create an incoming invoice from a received batch"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database import models
        from decimal import Decimal

        batch = await db.get(models.Batch, batch_id)
        if not batch:
            raise NotFoundException.record("Batch")

        if current_user.role.name != "super_admin" and batch.ingredient.company_id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage")

        # Get ingredient price
        ingredient = await db.get(models.Ingredient, batch.ingredient_id)
        unit_price = ingredient.current_price or Decimal("0")

        # Generate invoice number
        today = datetime.date.today()
        year = today.year
        prefix = "ВХ"

        stmt = select(models.Invoice).where(
            models.Invoice.number.like(f"{prefix}-{year}-%")
        ).order_by(models.Invoice.number.desc())
        res = await db.execute(stmt)
        last_invoice = res.scalars().first()

        if last_invoice:
            last_num = int(last_invoice.number.split("-")[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        invoice_number = f"{prefix}-{year}-{new_num:04d}"

        # Calculate totals
        subtotal = batch.quantity * unit_price
        vat_rate = Decimal("20.0")
        vat_amount = subtotal * (vat_rate / 100)
        total = subtotal + vat_amount

        # Create invoice
        invoice = models.Invoice(
            number=invoice_number,
            type="incoming",
            date=today,
            supplier_id=batch.supplier_id,
            batch_id=batch.id,
            subtotal=subtotal,
            discount_percent=Decimal("0"),
            discount_amount=Decimal("0"),
            vat_rate=vat_rate,
            vat_amount=vat_amount,
            total=total,
            status="draft",
            company_id=batch.ingredient.company_id,
            created_by=current_user.id
        )

        db.add(invoice)
        await db.flush()

        # Create invoice item
        invoice_item = models.InvoiceItem(
            invoice_id=invoice.id,
            ingredient_id=batch.ingredient_id,
            batch_id=batch.id,
            name=ingredient.name,
            quantity=batch.quantity,
            unit=ingredient.unit,
            unit_price=unit_price,
            unit_price_with_vat=batch.price_with_vat,
            discount_percent=Decimal("0"),
            total=subtotal,
            expiration_date=batch.expiry_date,
            batch_number=batch.batch_number
        )
        db.add(invoice_item)
        
        # Обнови цената на партидата от фактурата
        batch.price_no_vat = float(unit_price)
        batch.price_with_vat = float(batch.price_with_vat or unit_price * Decimal("1.2"))

        await db.commit()
        await db.refresh(invoice)
        return types.Invoice.from_instance(invoice)

    @strawberry.mutation
    async def bulk_add_batches(
            self,
            invoice_number: str,
            supplier_id: int,
            date: datetime.date,
            items: List[inputs.BatchInput],
            create_invoice: bool,
            info: strawberry.Info
    ) -> List[types.Batch]:
        """Bulk add batches from a single delivery and optionally create an invoice"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database import models
        from decimal import Decimal

        batches = []
        invoice_items_data = []
        total_subtotal = Decimal("0")

        # 1. Create Batches
        for idx, item_input in enumerate(items):
            ingredient = await db.get(models.Ingredient, item_input.ingredient_id)
            if not ingredient:
                continue

            # Auto-generate batch number if not provided
            batch_number = item_input.batch_number
            if not batch_number:
                batch_number = f"{date.strftime('%Y%m%d')}-{idx + 1:03d}"

            new_batch = models.Batch(
                ingredient_id=item_input.ingredient_id,
                batch_number=batch_number,
                quantity=item_input.quantity,
                expiry_date=item_input.expiry_date,
                supplier_id=supplier_id,
                invoice_number=invoice_number,
                invoice_date=date,
                storage_zone_id=item_input.storage_zone_id or ingredient.storage_zone_id,
                status="active",
                is_stock_receipt=True
            )
            db.add(new_batch)
            await db.flush()
            batches.append(new_batch)

            if create_invoice:
                unit_price = ingredient.current_price or Decimal("0")
                item_total = item_input.quantity * unit_price
                total_subtotal += item_total
                invoice_items_data.append({
                    "ingredient_id": ingredient.id,
                    "batch_id": new_batch.id,
                    "name": ingredient.name,
                    "quantity": item_input.quantity,
                    "unit": ingredient.unit,
                    "unit_price": unit_price,
                    "total": item_total,
                    "batch_number": batch_number,
                    "expiration_date": item_input.expiry_date
                })

        # 2. Optionally Create Invoice
        if create_invoice and batches:
            vat_rate = Decimal("20.0")
            vat_amount = total_subtotal * (vat_rate / 100)
            total = total_subtotal + vat_amount

            invoice = models.Invoice(
                number=invoice_number,
                type="incoming",
                date=date,
                supplier_id=supplier_id,
                subtotal=total_subtotal,
                discount_percent=Decimal("0"),
                discount_amount=Decimal("0"),
                vat_rate=vat_rate,
                vat_amount=vat_amount,
                total=total,
                status="draft",
                company_id=current_user.company_id,
                created_by=current_user.id
            )
            db.add(invoice)
            await db.flush()

            for item_data in invoice_items_data:
                inv_item = models.InvoiceItem(
                    invoice_id=invoice.id,
                    ingredient_id=item_data["ingredient_id"],
                    batch_id=item_data["batch_id"],
                    name=item_data["name"],
                    quantity=item_data["quantity"],
                    unit=item_data["unit"],
                    unit_price=item_data["unit_price"],
                    discount_percent=Decimal("0"),
                    total=item_data["total"],
                    batch_number=item_data.get("batch_number"),
                    expiration_date=item_data.get("expiration_date")
                )
                db.add(inv_item)
                await db.flush()
                
                # Обнови партидата с цената от фактурата
                if item_data.get("batch_id"):
                    batch = await db.get(models.Batch, item_data["batch_id"])
                    if batch:
                        batch.price_no_vat = float(item_data["unit_price"])
                        batch.price_with_vat = float(item_data["unit_price"]) * 1.2  # 20% ДДС

        await db.commit()
        for b in batches:
            await db.refresh(b)

        return [types.Batch.from_instance(b) for b in batches]

    @strawberry.mutation
    async def create_cash_journal_entry(
            self,
            input: inputs.CashJournalEntryInput,
            info: strawberry.Info
    ) -> types.CashJournalEntryType:
        """Create a cash journal entry"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database import models

        entry = models.CashJournalEntry(
            date=input.date,
            operation_type=input.operation_type,
            amount=input.amount,
            description=input.description,
            reference_type=input.reference_type,
            reference_id=input.reference_id,
            company_id=input.company_id,
            created_by=current_user.id
        )
        db.add(entry)

        # Log the operation
        log_entry = models.OperationLog(
            operation="create",
            entity_type="cash_journal",
            entity_id=0,  # Will be updated after flush
            user_id=current_user.id,
            changes={"amount": str(input.amount), "operation_type": input.operation_type}
        )
        db.add(log_entry)

        await db.commit()
        await db.refresh(entry)

        # Update log with actual ID
        log_entry.entity_id = entry.id
        await db.commit()

        return types.CashJournalEntryType.from_instance(entry)

    @strawberry.mutation
    async def delete_cash_journal_entry(
            self,
            id: int,
            info: strawberry.Info
    ) -> bool:
        """Delete a cash journal entry (soft delete via log)"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database import models

        entry = await db.get(models.CashJournalEntry, id)
        if not entry:
            raise NotFoundException.record("Entry")

        if current_user.role.name != "super_admin" and entry.company_id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage")

        # Проверка за законовия срок за съхранение (10 години)
        from datetime import datetime
        MIN_RETENTION_YEARS = 10
        age_in_days = (datetime.utcnow() - entry.created_at).days
        if age_in_days < MIN_RETENTION_YEARS * 365:
            raise ValidationException(
                detail=f"Записът не може да бъде изтрит. Законовият срок за съхранение е {MIN_RETENTION_YEARS} години."
            )

        # Log the deletion (soft delete)
        log_entry = models.OperationLog(
            operation="delete",
            entity_type="cash_journal",
            entity_id=id,
            user_id=current_user.id,
            changes={"amount": str(entry.amount), "operation_type": entry.operation_type}
        )
        db.add(log_entry)

        # Actually delete the entry
        await db.delete(entry)
        await db.commit()

        return True

    @strawberry.mutation
    async def generate_daily_summary(
            self,
            date: str,
            info: strawberry.Info
    ) -> types.DailySummaryType:
        """Generate daily summary for a specific date"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database import models
        import datetime
        from decimal import Decimal

        target_date = datetime.date.fromisoformat(date)

        if current_user.role.name != "super_admin":
            company_id = current_user.company_id
        else:
            raise AuthenticationException(detail=authenticate_msg)

        # Get invoices for the date
        invoices_stmt = select(models.Invoice).where(
            models.Invoice.date == target_date,
            models.Invoice.company_id == company_id
        )
        invoices_result = await db.execute(invoices_stmt)
        invoices = invoices_result.scalars().all()

        # Get cash journal entries for the date
        cash_stmt = select(models.CashJournalEntry).where(
            models.CashJournalEntry.date == target_date,
            models.CashJournalEntry.company_id == company_id
        )
        cash_result = await db.execute(cash_stmt)
        cash_entries = cash_result.scalars().all()

        # Calculate summaries
        invoices_count = len(invoices)
        incoming_invoices_count = sum(1 for i in invoices if i.type == "incoming")
        outgoing_invoices_count = sum(1 for i in invoices if i.type == "outgoing")

        invoices_total = sum(float(i.total or 0) for i in invoices)
        incoming_invoices_total = sum(float(i.total or 0) for i in invoices if i.type == "incoming")
        outgoing_invoices_total = sum(float(i.total or 0) for i in invoices if i.type == "outgoing")

        cash_income = sum(float(c.amount or 0) for c in cash_entries if c.operation_type == "income")
        cash_expense = sum(float(c.amount or 0) for c in cash_entries if c.operation_type == "expense")
        cash_balance = cash_income - cash_expense

        vat_collected = sum(float(i.vat_amount or 0) for i in invoices if i.type == "outgoing")
        vat_paid = sum(float(i.vat_amount or 0) for i in invoices if i.type == "incoming")

        paid_invoices_count = sum(1 for i in invoices if i.status == "paid")
        unpaid_invoices_count = sum(1 for i in invoices if i.status in ["draft", "sent"])
        overdue_invoices_count = sum(1 for i in invoices if i.status == "overdue")

        # Check if summary exists
        existing_stmt = select(models.DailySummary).where(
            models.DailySummary.date == target_date,
            models.DailySummary.company_id == company_id
        )
        existing_result = await db.execute(existing_stmt)
        existing = existing_result.scalars().first()

        if existing:
            # Update existing
            existing.invoices_count = invoices_count
            existing.incoming_invoices_count = incoming_invoices_count
            existing.outgoing_invoices_count = outgoing_invoices_count
            existing.invoices_total = Decimal(str(invoices_total))
            existing.incoming_invoices_total = Decimal(str(incoming_invoices_total))
            existing.outgoing_invoices_total = Decimal(str(outgoing_invoices_total))
            existing.cash_income = Decimal(str(cash_income))
            existing.cash_expense = Decimal(str(cash_expense))
            existing.cash_balance = Decimal(str(cash_balance))
            existing.vat_collected = Decimal(str(vat_collected))
            existing.vat_paid = Decimal(str(vat_paid))
            existing.paid_invoices_count = paid_invoices_count
            existing.unpaid_invoices_count = unpaid_invoices_count
            existing.overdue_invoices_count = overdue_invoices_count
            summary = existing
        else:
            # Create new
            summary = models.DailySummary(
                date=target_date,
                invoices_count=invoices_count,
                incoming_invoices_count=incoming_invoices_count,
                outgoing_invoices_count=outgoing_invoices_count,
                invoices_total=Decimal(str(invoices_total)),
                incoming_invoices_total=Decimal(str(incoming_invoices_total)),
                outgoing_invoices_total=Decimal(str(outgoing_invoices_total)),
                cash_income=Decimal(str(cash_income)),
                cash_expense=Decimal(str(cash_expense)),
                cash_balance=Decimal(str(cash_balance)),
                vat_collected=Decimal(str(vat_collected)),
                vat_paid=Decimal(str(vat_paid)),
                paid_invoices_count=paid_invoices_count,
                unpaid_invoices_count=unpaid_invoices_count,
                overdue_invoices_count=overdue_invoices_count,
                company_id=company_id
            )
            db.add(summary)

        await db.commit()
        await db.refresh(summary)
        return types.DailySummaryType.from_instance(summary)

    @strawberry.mutation
    async def generate_monthly_summary(
            self,
            year: int,
            month: int,
            info: strawberry.Info
    ) -> types.MonthlySummaryType:
        """Generate monthly summary for a specific year and month"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database import models
        import datetime
        from decimal import Decimal
        from sqlalchemy import func

        if current_user.role.name != "super_admin":
            company_id = current_user.company_id
        else:
            raise AuthenticationException(detail=authenticate_msg)

        start_date = datetime.date(year, month, 1)
        if month == 12:
            end_date = datetime.date(year + 1, 1, 1) - datetime.timedelta(days=1)
        else:
            end_date = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)

        invoices_stmt = select(models.Invoice).where(
            models.Invoice.date >= start_date,
            models.Invoice.date <= end_date,
            models.Invoice.company_id == company_id
        )
        invoices_result = await db.execute(invoices_stmt)
        invoices = invoices_result.scalars().all()

        cash_stmt = select(models.CashJournalEntry).where(
            models.CashJournalEntry.date >= start_date,
            models.CashJournalEntry.date <= end_date,
            models.CashJournalEntry.company_id == company_id
        )
        cash_result = await db.execute(cash_stmt)
        cash_entries = cash_result.scalars().all()

        invoices_count = len(invoices)
        incoming_invoices_count = sum(1 for i in invoices if i.type == "incoming")
        outgoing_invoices_count = sum(1 for i in invoices if i.type == "outgoing")

        invoices_total = sum(float(i.total or 0) for i in invoices)
        incoming_invoices_total = sum(float(i.total or 0) for i in invoices if i.type == "incoming")
        outgoing_invoices_total = sum(float(i.total or 0) for i in invoices if i.type == "outgoing")

        cash_income = sum(float(c.amount or 0) for c in cash_entries if c.operation_type == "income")
        cash_expense = sum(float(c.amount or 0) for c in cash_entries if c.operation_type == "expense")
        cash_balance = cash_income - cash_expense

        vat_collected = sum(float(i.vat_amount or 0) for i in invoices if i.type == "outgoing")
        vat_paid = sum(float(i.vat_amount or 0) for i in invoices if i.type == "incoming")

        paid_invoices_count = sum(1 for i in invoices if i.status == "paid")
        unpaid_invoices_count = sum(1 for i in invoices if i.status in ["draft", "sent"])
        overdue_invoices_count = sum(1 for i in invoices if i.status == "overdue")

        existing_stmt = select(models.MonthlySummary).where(
            models.MonthlySummary.year == year,
            models.MonthlySummary.month == month,
            models.MonthlySummary.company_id == company_id
        )
        existing_result = await db.execute(existing_stmt)
        existing = existing_result.scalars().first()

        if existing:
            existing.invoices_count = invoices_count
            existing.incoming_invoices_count = incoming_invoices_count
            existing.outgoing_invoices_count = outgoing_invoices_count
            existing.invoices_total = Decimal(str(invoices_total))
            existing.incoming_invoices_total = Decimal(str(incoming_invoices_total))
            existing.outgoing_invoices_total = Decimal(str(outgoing_invoices_total))
            existing.cash_income = Decimal(str(cash_income))
            existing.cash_expense = Decimal(str(cash_expense))
            existing.cash_balance = Decimal(str(cash_balance))
            existing.vat_collected = Decimal(str(vat_collected))
            existing.vat_paid = Decimal(str(vat_paid))
            existing.paid_invoices_count = paid_invoices_count
            existing.unpaid_invoices_count = unpaid_invoices_count
            existing.overdue_invoices_count = overdue_invoices_count
            summary = existing
        else:
            summary = models.MonthlySummary(
                year=year,
                month=month,
                invoices_count=invoices_count,
                incoming_invoices_count=incoming_invoices_count,
                outgoing_invoices_count=outgoing_invoices_count,
                invoices_total=Decimal(str(invoices_total)),
                incoming_invoices_total=Decimal(str(incoming_invoices_total)),
                outgoing_invoices_total=Decimal(str(outgoing_invoices_total)),
                cash_income=Decimal(str(cash_income)),
                cash_expense=Decimal(str(cash_expense)),
                cash_balance=Decimal(str(cash_balance)),
                vat_collected=Decimal(str(vat_collected)),
                vat_paid=Decimal(str(vat_paid)),
                paid_invoices_count=paid_invoices_count,
                unpaid_invoices_count=unpaid_invoices_count,
                overdue_invoices_count=overdue_invoices_count,
                company_id=company_id
            )
            db.add(summary)

        await db.commit()
        await db.refresh(summary)
        return types.MonthlySummaryType.from_instance(summary)

    @strawberry.mutation
    async def generate_yearly_summary(
            self,
            year: int,
            info: strawberry.Info
    ) -> types.YearlySummaryType:
        """Generate yearly summary for a specific year"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database import models
        import datetime
        from decimal import Decimal

        if current_user.role.name != "super_admin":
            company_id = current_user.company_id
        else:
            raise AuthenticationException(detail=authenticate_msg)

        start_date = datetime.date(year, 1, 1)
        end_date = datetime.date(year, 12, 31)

        invoices_stmt = select(models.Invoice).where(
            models.Invoice.date >= start_date,
            models.Invoice.date <= end_date,
            models.Invoice.company_id == company_id
        )
        invoices_result = await db.execute(invoices_stmt)
        invoices = invoices_result.scalars().all()

        cash_stmt = select(models.CashJournalEntry).where(
            models.CashJournalEntry.date >= start_date,
            models.CashJournalEntry.date <= end_date,
            models.CashJournalEntry.company_id == company_id
        )
        cash_result = await db.execute(cash_stmt)
        cash_entries = cash_result.scalars().all()

        invoices_count = len(invoices)
        incoming_invoices_count = sum(1 for i in invoices if i.type == "incoming")
        outgoing_invoices_count = sum(1 for i in invoices if i.type == "outgoing")

        invoices_total = sum(float(i.total or 0) for i in invoices)
        incoming_invoices_total = sum(float(i.total or 0) for i in invoices if i.type == "incoming")
        outgoing_invoices_total = sum(float(i.total or 0) for i in invoices if i.type == "outgoing")

        cash_income = sum(float(c.amount or 0) for c in cash_entries if c.operation_type == "income")
        cash_expense = sum(float(c.amount or 0) for c in cash_entries if c.operation_type == "expense")
        cash_balance = cash_income - cash_expense

        vat_collected = sum(float(i.vat_amount or 0) for i in invoices if i.type == "outgoing")
        vat_paid = sum(float(i.vat_amount or 0) for i in invoices if i.type == "incoming")

        paid_invoices_count = sum(1 for i in invoices if i.status == "paid")
        unpaid_invoices_count = sum(1 for i in invoices if i.status in ["draft", "sent"])
        overdue_invoices_count = sum(1 for i in invoices if i.status == "overdue")

        existing_stmt = select(models.YearlySummary).where(
            models.YearlySummary.year == year,
            models.YearlySummary.company_id == company_id
        )
        existing_result = await db.execute(existing_stmt)
        existing = existing_result.scalars().first()

        if existing:
            existing.invoices_count = invoices_count
            existing.incoming_invoices_count = incoming_invoices_count
            existing.outgoing_invoices_count = outgoing_invoices_count
            existing.invoices_total = Decimal(str(invoices_total))
            existing.incoming_invoices_total = Decimal(str(incoming_invoices_total))
            existing.outgoing_invoices_total = Decimal(str(outgoing_invoices_total))
            existing.cash_income = Decimal(str(cash_income))
            existing.cash_expense = Decimal(str(cash_expense))
            existing.cash_balance = Decimal(str(cash_balance))
            existing.vat_collected = Decimal(str(vat_collected))
            existing.vat_paid = Decimal(str(vat_paid))
            existing.paid_invoices_count = paid_invoices_count
            existing.unpaid_invoices_count = unpaid_invoices_count
            existing.overdue_invoices_count = overdue_invoices_count
            summary = existing
        else:
            summary = models.YearlySummary(
                year=year,
                invoices_count=invoices_count,
                incoming_invoices_count=incoming_invoices_count,
                outgoing_invoices_count=outgoing_invoices_count,
                invoices_total=Decimal(str(invoices_total)),
                incoming_invoices_total=Decimal(str(incoming_invoices_total)),
                outgoing_invoices_total=Decimal(str(outgoing_invoices_total)),
                cash_income=Decimal(str(cash_income)),
                cash_expense=Decimal(str(cash_expense)),
                cash_balance=Decimal(str(cash_balance)),
                vat_collected=Decimal(str(vat_collected)),
                vat_paid=Decimal(str(vat_paid)),
                paid_invoices_count=paid_invoices_count,
                unpaid_invoices_count=unpaid_invoices_count,
                overdue_invoices_count=overdue_invoices_count,
                company_id=company_id
            )
            db.add(summary)

        await db.commit()
        await db.refresh(summary)
        return types.YearlySummaryType.from_instance(summary)

    # ============== SAF-T MUTATIONS ==============

    @strawberry.mutation
    async def generate_saft_file(
            self,
            info: strawberry.Info,
            company_id: int,
            year: int,
            month: int,
            saft_type: Optional[str] = "monthly"
    ) -> types.SAFTFileResult:
        """
        Generate SAF-T XML file for Bulgarian NRA.

        Args:
            company_id: Company ID
            year: Year (e.g., 2026)
            month: Month (1-12)
            saft_type: 'monthly', 'annual', or 'on_demand'

        Returns:
            SAFTFileResult with XML content and validation results
        """
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        # Import SAF-T generator
        from backend.services.saft_generator import generate_saft_file as saft_generator

        try:
            result = await saft_generator(
                db=db,
                company_id=company_id,
                year=year,
                month=month,
                saft_type=saft_type
            )

            return types.SAFTFileResult(
                xml_content=result['xml_content'],
                validation_result=types.SAFTValidationResult(
                    status=result['validation_result']['status'],
                    errors=result['validation_result'].get('errors', []),
                    warnings=result['validation_result'].get('warnings', []),
                    is_valid=result['validation_result'].get('is_valid', False)
                ),
                period_start=result['period_start'],
                period_end=result['period_end'],
                file_size=result['file_size'],
                file_name=result['file_name']
            )
        except Exception as e:
            raise internal_server_error(f"Error generating SAF-T file: {str(e)}")

    @strawberry.mutation
    async def validate_saft_xml(
            self,
            xml_content: str,
            info: strawberry.Info
    ) -> types.SAFTValidationResult:
        """Validate SAF-T XML content"""
        from backend.services.saft_generator import SAFTValidator

        validator = SAFTValidator()
        result = validator.validate(xml_content)

        return types.SAFTValidationResult(
            status=result['status'],
            errors=result.get('errors', []),
            warnings=result.get('warnings', []),
            is_valid=result.get('is_valid', False)
        )

    @strawberry.mutation
    async def create_proforma_invoice(
            self,
            client_name: str,
            client_eik: Optional[str],
            client_address: Optional[str],
            date: datetime.date,
            items: List[inputs.InvoiceItemInput],
            vat_rate: float,
            discount_percent: float,
            notes: Optional[str],
            info: strawberry.Info
    ) -> types.ProformaInvoice:
        """Create a proforma invoice"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database import models

        # Generate proforma number
        year = date.year
        prefix = "ПРОФОРМА"

        stmt = select(models.Invoice).where(
            models.Invoice.number.like(f"{prefix}-{year}-%")
        ).order_by(models.Invoice.number.desc())
        res = await db.execute(stmt)
        last_invoice = res.scalars().first()

        if last_invoice:
            last_num = int(last_invoice.number.split("-")[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        invoice_number = f"{prefix}-{year}-{new_num:04d}"

        # Calculate totals
        subtotal = sum(Decimal(str(item.quantity)) * Decimal(str(item.unit_price)) for item in items)
        discount_amount = subtotal * Decimal(str(discount_percent / 100))
        subtotal_after_discount = subtotal - discount_amount
        vat_amount = subtotal_after_discount * Decimal(str(vat_rate / 100))
        total = subtotal_after_discount + vat_amount

        # Create invoice
        invoice = models.Invoice(
            number=invoice_number,
            type="proforma",
            date=date,
            client_name=client_name,
            client_eik=client_eik,
            client_address=client_address,
            subtotal=subtotal,
            discount_percent=Decimal(str(discount_percent)),
            discount_amount=discount_amount,
            vat_rate=Decimal(str(vat_rate)),
            vat_amount=vat_amount,
            total=total,
            status="draft",
            notes=notes,
            company_id=current_user.company_id,
            created_by=current_user.id
        )

        db.add(invoice)
        await db.flush()

        # Create invoice items
        for idx, item in enumerate(items, 1):
            item_total = Decimal(str(item.quantity)) * Decimal(str(item.unit_price))
            db_item = models.InvoiceItem(
                invoice_id=invoice.id,
                name=item.name,
                quantity=Decimal(str(item.quantity)),
                unit=item.unit,
                unit_price=Decimal(str(item.unit_price)),
                unit_price_with_vat=item.unit_price_with_vat,
                discount_percent=item.discount_percent or Decimal("0"),
                total=item_total,
                expiration_date=datetime.datetime.strptime(item.expiration_date, '%Y-%m-%d').date() if item.expiration_date else None,
                batch_number=item.batch_number
            )
            db.add(db_item)

        await db.commit()
        await db.refresh(invoice)
        return types.ProformaInvoice.from_instance(invoice)

    @strawberry.mutation
    async def convert_proforma_to_invoice(
            self,
            proforma_id: int,
            invoice_type: str,
            info: strawberry.Info
    ) -> types.Invoice:
        """Convert proforma invoice to regular invoice"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database import models

        proforma = await db.get(models.Invoice, proforma_id)
        if not proforma or proforma.type != "proforma":
            raise NotFoundException.record("Proforma Invoice")

        # Generate new invoice number
        today = datetime.date.today()
        year = today.year
        prefix = "ИЗХ" if invoice_type == "outgoing" else "ВХ"

        stmt = select(models.Invoice).where(
            models.Invoice.number.like(f"{prefix}-{year}-%")
        ).order_by(models.Invoice.number.desc())
        res = await db.execute(stmt)
        last_invoice = res.scalars().first()

        if last_invoice:
            last_num = int(last_invoice.number.split("-")[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        invoice_number = f"{prefix}-{year}-{new_num:04d}"

        # Create new invoice
        invoice = models.Invoice(
            number=invoice_number,
            type=invoice_type,
            date=today,
            client_name=proforma.client_name,
            client_eik=proforma.client_eik,
            client_address=proforma.client_address,
            subtotal=proforma.subtotal,
            discount_percent=proforma.discount_percent,
            discount_amount=proforma.discount_amount,
            vat_rate=proforma.vat_rate,
            vat_amount=proforma.vat_amount,
            total=proforma.total,
            status="draft",
            notes=proforma.notes,
            company_id=proforma.company_id,
            created_by=current_user.id
        )

        db.add(invoice)
        await db.flush()

        # Copy items
        stmt_items = select(models.InvoiceItem).where(
            models.InvoiceItem.invoice_id == proforma_id
        )
        res_items = await db.execute(stmt_items)
        proforma_items = res_items.scalars().all()

        for item in proforma_items:
            new_item = models.InvoiceItem(
                invoice_id=invoice.id,
                name=item.name,
                quantity=item.quantity,
                unit=item.unit,
                unit_price=item.unit_price,
                unit_price_with_vat=item.unit_price_with_vat,
                discount_percent=item.discount_percent,
                total=item.total,
                expiration_date=item.expiration_date,
                batch_number=item.batch_number
            )
            db.add(new_item)

        # Mark proforma as converted
        proforma.status = "converted"

        await db.commit()
        await db.refresh(invoice)
        return types.Invoice.from_instance(invoice)

    @strawberry.mutation
    async def create_invoice_correction(
            self,
            original_invoice_id: int,
            correction_type: str,
            reason: str,
            correction_date: datetime.date,
            info: strawberry.Info,
            create_new_invoice: bool = False,
    ) -> types.InvoiceCorrection:
        """Create a credit or debit note for an invoice"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        # Permission check: accountant, head_accountant, super_admin
        allowed_roles = ["super_admin", "head_accountant", "accountant"]
        if current_user.role.name not in allowed_roles:
            raise PermissionDeniedException(
                detail="Нямате права да създавате корекции. За това действие са необходими права на счетоводител или по-високи."
            )

        from backend.database import models
        from sqlalchemy import func

        original_invoice = await db.get(models.Invoice, original_invoice_id)
        if not original_invoice:
            raise NotFoundException.record("Original Invoice")

        # Validate invoice can be corrected
        if original_invoice.status == 'cancelled':
            raise ValidationException(
                detail="Не можете да коригирате тази фактура. Тя е анулирана."
            )
        if original_invoice.status == 'corrected':
            raise ValidationException(
                detail="Не можете да коригирате тази фактура. Тя вече е коригирана."
            )
        if original_invoice.status == 'paid':
            raise ValidationException(
                detail="Платена фактура не може да се коригира."
            )

        # Validate correction type
        if correction_type not in ['credit', 'debit']:
            raise ValidationException(
                detail="Типът на корекцията трябва да бъде 'credit' или 'debit'."
            )

        # Generate correction number: КР-{YEAR}-{NNN}
        year = correction_date.year
        last_correction = await db.execute(
            select(models.InvoiceCorrection)
            .where(
                models.InvoiceCorrection.company_id == current_user.company_id,
                func.extract('year', models.InvoiceCorrection.correction_date) == year
            )
            .order_by(models.InvoiceCorrection.id.desc())
            .limit(1)
        )
        last_num = last_correction.scalar()
        next_num = 1 if not last_num else int(last_num.number.split('-')[-1]) + 1
        correction_number = f"КР-{year}-{next_num:04d}"

        # Calculate amounts based on correction type
        if correction_type == 'credit':
            amount_diff = -original_invoice.subtotal
            vat_diff = -original_invoice.vat_amount
        else:  # debit
            amount_diff = original_invoice.subtotal
            vat_diff = original_invoice.vat_amount

        # Create correction
        correction = models.InvoiceCorrection(
            number=correction_number,
            original_invoice_id=original_invoice_id,
            type=correction_type,
            correction_type=correction_type,
            reason=reason,
            amount_diff=amount_diff,
            vat_diff=vat_diff,
            correction_date=correction_date,
            company_id=current_user.company_id,
            created_by=current_user.id
        )

        db.add(correction)

        # Optionally create new invoice
        if create_new_invoice:
            # Generate invoice number
            prefix = "ИЗХ" if original_invoice.type == 'outgoing' else "ВХ"
            year_inv = correction_date.year
            last_invoice = await db.execute(
                select(models.Invoice)
                .where(
                    models.Invoice.company_id == current_user.company_id,
                    models.Invoice.number.like(f"{prefix}-{year_inv}-%")
                )
                .order_by(models.Invoice.id.desc())
                .limit(1)
            )
            last_inv_num = last_invoice.scalar()
            next_inv_num = 1 if not last_inv_num else int(last_inv_num.number.split('-')[-1]) + 1
            new_invoice_number = f"{prefix}-{year_inv}-{next_inv_num:04d}"

            new_invoice = models.Invoice(
                number=new_invoice_number,
                type=original_invoice.type,
                document_type=original_invoice.document_type,
                date=correction_date,
                client_name=original_invoice.client_name,
                client_eik=original_invoice.client_eik,
                client_address=original_invoice.client_address,
                subtotal=original_invoice.subtotal + amount_diff,
                vat_amount=original_invoice.vat_amount + vat_diff,
                total=(original_invoice.subtotal + amount_diff) + (original_invoice.vat_amount + vat_diff),
                vat_rate=original_invoice.vat_rate,
                status='draft',
                company_id=current_user.company_id,
                created_by=current_user.id
            )
            db.add(new_invoice)
            correction.new_invoice = new_invoice

        # Mark original as corrected
        original_invoice.status = "corrected"

        # Create reverse accounting entries
        from backend.services.accounting_service import AccountingService
        company = await db.get(models.Company, current_user.company_id)
        correction_entries = []
        if company:
            accounting_service = AccountingService(db)
            correction_entries = await accounting_service.create_correction_entries(
                correction=correction,
                invoice=original_invoice,
                company=company,
                created_by=current_user
            )
            for entry in correction_entries:
                db.add(entry)

        # Log the operation
        log_entry = models.OperationLog(
            operation="create_correction",
            entity_type="correction",
            entity_id=correction.id,
            user_id=current_user.id,
            company_id=current_user.company_id,
            changes={
                "number": correction_number,
                "type": correction_type,
                "original_invoice_id": original_invoice_id,
                "original_invoice_number": original_invoice.number,
                "amount_diff": float(amount_diff),
                "vat_diff": float(vat_diff),
                "reason": reason,
                "create_new_invoice": create_new_invoice,
                "accounting_entries_created": len(correction_entries)
            }
        )
        db.add(log_entry)

        await db.commit()
        await db.refresh(correction, ["original_invoice"])
        return types.InvoiceCorrection.from_instance(correction)

    @strawberry.mutation
    async def create_credit_note(
            self,
            original_invoice_id: int,
            reason: str,
            correction_date: datetime.date,
            info: strawberry.Info
    ) -> types.InvoiceCorrection:
        """Create a credit note for an invoice"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database import models

        original_invoice = await db.get(models.Invoice, original_invoice_id)
        if not original_invoice:
            raise NotFoundException.record("Original Invoice")

        # Create correction
        correction = models.InvoiceCorrection(
            original_invoice_id=original_invoice_id,
            correction_type="credit",
            reason=reason,
            amount_diff=-original_invoice.subtotal,
            vat_diff=-original_invoice.vat_amount,
            correction_date=correction_date,
            company_id=current_user.company_id,
            created_by=current_user.id
        )

        db.add(correction)

        # Mark original as corrected
        original_invoice.status = "corrected"

        await db.commit()
        await db.refresh(correction, ["original_invoice"])
        return types.InvoiceCorrection.from_instance(correction)

    @strawberry.mutation
    async def create_cash_receipt(
            self,
            input: inputs.CashReceiptInput,
            info: strawberry.Info
    ) -> types.CashReceipt:
        """Create a cash receipt"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database import models

        receipt = models.CashReceipt(
            receipt_number=input.receipt_number,
            date=input.date,
            payment_type=input.payment_type,
            amount=input.amount,
            vat_amount=input.vat_amount,
            items_json=input.items_json,
            fiscal_printer_id=input.fiscal_printer_id,
            company_id=input.company_id,
            created_by=current_user.id
        )
        db.add(receipt)
        await db.commit()
        await db.refresh(receipt)
        return types.CashReceipt.from_instance(receipt)

    @strawberry.mutation
    async def update_cash_receipt(
            self,
            id: int,
            input: inputs.CashReceiptUpdateInput,
            info: strawberry.Info
    ) -> Optional[types.CashReceipt]:
        """Update a cash receipt"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database import models

        receipt = await db.get(models.CashReceipt, id)
        if not receipt:
            raise NotFoundException.record("Cash Receipt")

        if receipt.company_id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage")

        if input.receipt_number is not None:
            receipt.receipt_number = input.receipt_number
        if input.date is not None:
            receipt.date = input.date
        if input.payment_type is not None:
            receipt.payment_type = input.payment_type
        if input.amount is not None:
            receipt.amount = input.amount
        if input.vat_amount is not None:
            receipt.vat_amount = input.vat_amount
        if input.items_json is not None:
            receipt.items_json = input.items_json
        if input.fiscal_printer_id is not None:
            receipt.fiscal_printer_id = input.fiscal_printer_id

        await db.commit()
        await db.refresh(receipt)
        return types.CashReceipt.from_instance(receipt)

    @strawberry.mutation
    async def delete_cash_receipt(
            self,
            id: int,
            info: strawberry.Info
    ) -> bool:
        """Delete a cash receipt"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database import models

        receipt = await db.get(models.CashReceipt, id)
        if not receipt:
            raise NotFoundException.record("Cash Receipt")

        if receipt.company_id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage")

        # Проверка за законовия срок за съхранение (10 години)
        from datetime import datetime
        MIN_RETENTION_YEARS = 10
        age_in_days = (datetime.utcnow() - receipt.created_at).days
        if age_in_days < MIN_RETENTION_YEARS * 365:
            raise ValidationException(
                detail=f"Касовата бележка не може да бъде изтрита. Законовият срок за съхранение е {MIN_RETENTION_YEARS} години."
            )

        await db.delete(receipt)
        await db.commit()
        return True

    @strawberry.mutation
    async def create_bank_account(
            self,
            input: inputs.BankAccountInput,
            info: strawberry.Info
    ) -> types.BankAccount:
        """Create a bank account"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database import models

        if input.is_default:
            existing = await db.execute(
                select(models.BankAccount).where(
                    models.BankAccount.company_id == input.company_id,
                    models.BankAccount.is_default == True
                )
            )
            for acc in existing.scalars():
                acc.is_default = False

        account = models.BankAccount(
            iban=input.iban,
            bic=input.bic,
            bank_name=input.bank_name,
            account_type=input.account_type,
            is_default=input.is_default,
            currency=input.currency,
            is_active=input.is_active,
            company_id=input.company_id,
            created_by=current_user.id
        )
        db.add(account)
        await db.commit()
        await db.refresh(account)
        return types.BankAccount.from_instance(account)

    @strawberry.mutation
    async def update_bank_account(
            self,
            id: int,
            input: inputs.BankAccountUpdateInput,
            info: strawberry.Info
    ) -> Optional[types.BankAccount]:
        """Update a bank account"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database import models

        account = await db.get(models.BankAccount, id)
        if not account:
            raise NotFoundException.record("Bank Account")

        if account.company_id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage")

        if input.is_default and not account.is_default:
            existing = await db.execute(
                select(models.BankAccount).where(
                    models.BankAccount.company_id == account.company_id,
                    models.BankAccount.is_default == True,
                    models.BankAccount.id != id
                )
            )
            for acc in existing.scalars():
                acc.is_default = False

        if input.iban is not None:
            account.iban = input.iban
        if input.bic is not None:
            account.bic = input.bic
        if input.bank_name is not None:
            account.bank_name = input.bank_name
        if input.account_type is not None:
            account.account_type = input.account_type
        if input.is_default is not None:
            account.is_default = input.is_default
        if input.currency is not None:
            account.currency = input.currency
        if input.is_active is not None:
            account.is_active = input.is_active

        await db.commit()
        await db.refresh(account)
        return types.BankAccount.from_instance(account)

    @strawberry.mutation
    async def delete_bank_account(
            self,
            id: int,
            info: strawberry.Info
    ) -> bool:
        """Delete a bank account"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database import models

        account = await db.get(models.BankAccount, id)
        if not account:
            raise NotFoundException.record("Bank Account")

        if account.company_id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage")

        await db.delete(account)
        await db.commit()
        return True

    @strawberry.mutation
    async def create_bank_transaction(
            self,
            input: inputs.BankTransactionInput,
            info: strawberry.Info
    ) -> types.BankTransaction:
        """Create a bank transaction"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database import models

        transaction = models.BankTransaction(
            bank_account_id=input.bank_account_id,
            date=input.date,
            amount=input.amount,
            type=input.type,
            description=input.description,
            reference=input.reference,
            invoice_id=input.invoice_id,
            matched=input.invoice_id is not None,
            company_id=input.company_id,
            created_by=current_user.id
        )
        db.add(transaction)
        
        # Log the operation
        log_entry = models.OperationLog(
            operation="create",
            entity_type="bank_transaction",
            entity_id=transaction.id,
            user_id=current_user.id,
            company_id=current_user.company_id,
            changes={
                "amount": float(input.amount),
                "type": input.type,
                "description": input.description,
                "reference": input.reference,
                "invoice_id": input.invoice_id
            }
        )
        db.add(log_entry)
        
        await db.commit()
        await db.refresh(transaction)
        return types.BankTransaction.from_instance(transaction)

    @strawberry.mutation
    async def update_bank_transaction(
            self,
            id: int,
            input: inputs.BankTransactionUpdateInput,
            info: strawberry.Info
    ) -> Optional[types.BankTransaction]:
        """Update a bank transaction"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database import models

        transaction = await db.get(models.BankTransaction, id)
        if not transaction:
            raise NotFoundException.record("Bank Transaction")

        if transaction.company_id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage")

        if input.date is not None:
            transaction.date = input.date
        if input.amount is not None:
            transaction.amount = input.amount
        if input.type is not None:
            transaction.type = input.type
        if input.description is not None:
            transaction.description = input.description
        if input.reference is not None:
            transaction.reference = input.reference
        if input.invoice_id is not None:
            transaction.invoice_id = input.invoice_id
            transaction.matched = True
        if input.matched is not None:
            transaction.matched = input.matched

        # Log the update
        log_entry = models.OperationLog(
            operation="update",
            entity_type="bank_transaction",
            entity_id=transaction.id,
            user_id=current_user.id,
            company_id=current_user.company_id,
            changes={
                "amount": float(transaction.amount),
                "type": transaction.type,
                "description": transaction.description,
                "reference": transaction.reference,
                "invoice_id": transaction.invoice_id,
                "matched": transaction.matched
            }
        )
        db.add(log_entry)

        await db.commit()
        await db.refresh(transaction)
        return types.BankTransaction.from_instance(transaction)

    @strawberry.mutation
    async def delete_bank_transaction(
            self,
            id: int,
            info: strawberry.Info
    ) -> bool:
        """Delete a bank transaction"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database import models

        transaction = await db.get(models.BankTransaction, id)
        if not transaction:
            raise NotFoundException.record("Bank Transaction")

        if transaction.company_id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage")

        # Проверка за законовия срок за съхранение (10 години)
        from datetime import datetime
        MIN_RETENTION_YEARS = 10
        age_in_days = (datetime.utcnow() - transaction.created_at).days
        if age_in_days < MIN_RETENTION_YEARS * 365:
            raise ValidationException(
                detail=f"Банковата транзакция не може да бъде изтрита. Законовият срок за съхранение е {MIN_RETENTION_YEARS} години."
            )

        # Log the deletion
        log_entry = models.OperationLog(
            operation="delete",
            entity_type="bank_transaction",
            entity_id=transaction.id,
            user_id=current_user.id,
            company_id=current_user.company_id,
            changes={
                "amount": float(transaction.amount),
                "type": transaction.type,
                "description": transaction.description
            }
        )
        db.add(log_entry)

        await db.delete(transaction)
        await db.commit()
        return True

    @strawberry.mutation
    async def match_bank_transaction(
            self,
            transaction_id: int,
            invoice_id: int,
            info: strawberry.Info
    ) -> Optional[types.BankTransaction]:
        """Match a bank transaction to an invoice"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database import models

        transaction = await db.get(models.BankTransaction, transaction_id)
        if not transaction:
            raise NotFoundException.record("Bank Transaction")

        invoice = await db.get(models.Invoice, invoice_id)
        if not invoice:
            raise NotFoundException.record("Invoice")

        if transaction.company_id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage")

        transaction.invoice_id = invoice_id
        transaction.matched = True

        await db.commit()
        await db.refresh(transaction)
        return types.BankTransaction.from_instance(transaction)

    @strawberry.mutation
    async def unmatch_bank_transaction(
            self,
            transaction_id: int,
            info: strawberry.Info
    ) -> Optional[types.BankTransaction]:
        """Unmatch a bank transaction from an invoice"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database import models

        transaction = await db.get(models.BankTransaction, transaction_id)
        if not transaction:
            raise NotFoundException.record("Банкова транзакция")

        if transaction.company_id != current_user.company_id:
            raise PermissionDeniedException()

        transaction.invoice_id = None
        transaction.matched = False

        await db.commit()
        await db.refresh(transaction)
        return types.BankTransaction.from_instance(transaction)

    @strawberry.mutation
    async def auto_match_bank_transactions(
            self,
            bank_account_id: int,
            info: strawberry.Info
    ) -> types.AutoMatchResult:
        """Automatically match bank transactions to invoices based on amount and reference"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database import models
        from sqlalchemy import select

        bank_account = await db.get(models.BankAccount, bank_account_id)
        if not bank_account:
            raise NotFoundException.record("Банкова сметка")

        if bank_account.company_id != current_user.company_id:
            raise PermissionDeniedException()

        unmatched_transactions = await db.execute(
            select(models.BankTransaction).where(
                models.BankTransaction.bank_account_id == bank_account_id,
                models.BankTransaction.matched == False,
                models.BankTransaction.invoice_id.is_(None)
            )
        )
        transactions = unmatched_transactions.scalars().all()

        unpaid_invoices = await db.execute(
            select(models.Invoice).where(
                models.Invoice.company_id == current_user.company_id,
                models.Invoice.status.in_(["sent", "paid"])
            )
        )
        invoices = unpaid_invoices.scalars().all()

        matched_count = 0
        for tx in transactions:
            for inv in invoices:
                if (tx.type == "credit" and Decimal(tx.amount) == Decimal(inv.total)) or \
                   (tx.type == "debit" and Decimal(tx.amount) == Decimal(inv.total)):
                    if not inv.bank_transactions:
                        tx.invoice_id = inv.id
                        tx.matched = True
                        matched_count += 1
                        break

        await db.commit()

        unmatched_count = len(transactions) - matched_count
        return types.AutoMatchResult(matched_count=matched_count, unmatched_count=unmatched_count)

    @strawberry.mutation
    async def create_account(
            self,
            input: inputs.AccountInput,
            info: strawberry.Info
    ) -> types.Account:
        """Create an account in the chart of accounts"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database import models

        account = models.Account(
            code=input.code,
            name=input.name,
            type=input.type,
            parent_id=input.parent_id,
            company_id=input.company_id,
            opening_balance=input.opening_balance,
            closing_balance=input.opening_balance
        )
        db.add(account)
        await db.commit()
        await db.refresh(account)
        return types.Account.from_instance(account)

    @strawberry.mutation
    async def update_account(
            self,
            id: int,
            input: inputs.AccountUpdateInput,
            info: strawberry.Info
    ) -> Optional[types.Account]:
        """Update an account"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database import models

        account = await db.get(models.Account, id)
        if not account:
            raise NotFoundException.record("Account")

        if account.company_id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage")

        if input.code is not None:
            account.code = input.code
        if input.name is not None:
            account.name = input.name
        if input.type is not None:
            account.type = input.type
        if input.parent_id is not None:
            account.parent_id = input.parent_id
        if input.opening_balance is not None:
            account.opening_balance = input.opening_balance

        await db.commit()
        await db.refresh(account)
        return types.Account.from_instance(account)

    @strawberry.mutation
    async def delete_account(
            self,
            id: int,
            info: strawberry.Info
    ) -> bool:
        """Delete an account"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database import models

        account = await db.get(models.Account, id)
        if not account:
            raise NotFoundException.record("Account")

        if account.company_id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage")

        await db.delete(account)
        await db.commit()
        return True

    @strawberry.mutation
    async def create_accounting_entry(
            self,
            input: inputs.AccountingEntryInput,
            info: strawberry.Info
    ) -> types.AccountingEntry:
        """Create an accounting entry"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database import models

        entry = models.AccountingEntry(
            date=input.date,
            entry_number=input.entry_number,
            description=input.description,
            debit_account_id=input.debit_account_id,
            credit_account_id=input.credit_account_id,
            amount=input.amount,
            vat_amount=input.vat_amount,
            invoice_id=input.invoice_id,
            bank_transaction_id=input.bank_transaction_id,
            cash_journal_id=input.cash_journal_id,
            company_id=input.company_id,
            created_by=current_user.id
        )
        db.add(entry)

        # Log the operation
        log_entry = models.OperationLog(
            operation="create",
            entity_type="accounting_entry",
            entity_id=entry.id,
            user_id=current_user.id,
            company_id=current_user.company_id,
            changes={
                "entry_number": input.entry_number,
                "description": input.description,
                "debit_account_id": input.debit_account_id,
                "credit_account_id": input.credit_account_id,
                "amount": float(input.amount),
                "vat_amount": float(input.vat_amount),
                "invoice_id": input.invoice_id
            }
        )
        db.add(log_entry)

        await db.commit()
        await db.refresh(entry)
        return types.AccountingEntry.from_instance(entry)

    @strawberry.mutation
    async def delete_accounting_entry(
            self,
            id: int,
            info: strawberry.Info
    ) -> bool:
        """Delete an accounting entry"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database import models

        entry = await db.get(models.AccountingEntry, id)
        if not entry:
            raise NotFoundException.record("Accounting Entry")

        if entry.company_id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage")

        # Log the deletion
        log_entry = models.OperationLog(
            operation="delete",
            entity_type="accounting_entry",
            entity_id=entry.id,
            user_id=current_user.id,
            company_id=current_user.company_id,
            changes={
                "entry_number": entry.entry_number,
                "description": entry.description,
                "amount": float(entry.amount)
            }
        )
        db.add(log_entry)

        await db.delete(entry)
        await db.commit()
        return True

    @strawberry.mutation
    async def generate_vat_register(
            self,
            input: inputs.VATRegisterInput,
            info: strawberry.Info
    ) -> types.VATRegister:
        """Generate VAT register for a period"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database import models

        existing = await db.execute(
            select(models.VATRegister).where(
                models.VATRegister.company_id == input.company_id,
                models.VATRegister.period_month == input.period_month,
                models.VATRegister.period_year == input.period_year
            )
        )
        existing_reg = existing.scalars().first()
        if existing_reg:
            await db.delete(existing_reg)
            await db.commit()

        from datetime import date
        start_date = date(input.period_year, input.period_month, 1)
        if input.period_month == 12:
            end_date = date(input.period_year + 1, 1, 1)
        else:
            end_date = date(input.period_year, input.period_month + 1, 1)

        outgoing = await db.execute(
            select(models.Invoice).where(
                models.Invoice.company_id == input.company_id,
                models.Invoice.type == "outgoing",
                models.Invoice.date >= start_date,
                models.Invoice.date < end_date,
                models.Invoice.status == "paid"
            )
        )
        incoming = await db.execute(
            select(models.Invoice).where(
                models.Invoice.company_id == input.company_id,
                models.Invoice.type == "incoming",
                models.Invoice.date >= start_date,
                models.Invoice.date < end_date,
                models.Invoice.status == "paid"
            )
        )

        vat_collected_20 = Decimal("0")
        vat_collected_9 = Decimal("0")
        vat_collected_0 = Decimal("0")
        for inv in outgoing.scalars():
            if inv.vat_rate == Decimal("20"):
                vat_collected_20 += inv.vat_amount or Decimal("0")
            elif inv.vat_rate == Decimal("9"):
                vat_collected_9 += inv.vat_amount or Decimal("0")
            else:
                vat_collected_0 += inv.vat_amount or Decimal("0")

        vat_paid_20 = Decimal("0")
        vat_paid_9 = Decimal("0")
        vat_paid_0 = Decimal("0")
        for inv in incoming.scalars():
            if inv.vat_rate == Decimal("20"):
                vat_paid_20 += inv.vat_amount or Decimal("0")
            elif inv.vat_rate == Decimal("9"):
                vat_paid_9 += inv.vat_amount or Decimal("0")
            else:
                vat_paid_0 += inv.vat_amount or Decimal("0")

        vat_due = max(Decimal("0"), (vat_collected_20 + vat_collected_9) - (vat_paid_20 + vat_paid_9))
        vat_credit = max(Decimal("0"), (vat_paid_20 + vat_paid_9) - (vat_collected_20 + vat_collected_9))

        vat_register = models.VATRegister(
            company_id=input.company_id,
            period_month=input.period_month,
            period_year=input.period_year,
            vat_collected_20=vat_collected_20,
            vat_collected_9=vat_collected_9,
            vat_collected_0=vat_collected_0,
            vat_paid_20=vat_paid_20,
            vat_paid_9=vat_paid_9,
            vat_paid_0=vat_paid_0,
            vat_adjustment=Decimal("0"),
            vat_due=vat_due,
            vat_credit=vat_credit
        )
        db.add(vat_register)
        await db.commit()
        await db.refresh(vat_register)
        return types.VATRegister.from_instance(vat_register)

    # ========== PRODUCTION CONTROL TABLET MUTATIONS ==========

    @strawberry.mutation
    async def reassign_task_workstation(
            self,
            task_id: int,
            new_workstation_id: int,
            info: strawberry.Info
    ) -> types.ProductionTask:
        """Reassign a production task to a different workstation"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import ProductionTask, ProductionOrder

        task = await db.get(ProductionTask, task_id)
        if not task: raise NotFoundException.resource("Task")

        order = await db.get(ProductionOrder, task.order_id)
        if current_user.role.name != "super_admin" and order.company_id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage")

        task.workstation_id = new_workstation_id
        await db.commit()
        await db.refresh(task)
        return types.ProductionTask.from_instance(task)

    @strawberry.mutation
    async def recalculate_production_deadline(
            self,
            order_id: int,
            info: strawberry.Info
    ) -> types.ProductionOrder:
        """Recalculate production_deadline for an order based on recipe"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import ProductionOrder, Recipe, sofia_now
        from datetime import timedelta

        order = await db.get(ProductionOrder, order_id)
        if not order: raise NotFoundException.order()

        if current_user.role.name != "super_admin" and order.company_id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage")

        recipe = await db.get(Recipe, order.recipe_id)
        if recipe and recipe.production_deadline_days and order.due_date:
            order.production_deadline = order.due_date - timedelta(days=recipe.production_deadline_days)
            if order.production_deadline and order.production_deadline.tzinfo is not None:
                order.production_deadline = order.production_deadline.replace(tzinfo=None)

        await db.commit()
        await db.refresh(order)
        return types.ProductionOrder.from_instance(order)

    @strawberry.mutation
    async def update_production_order_quantity(
            self,
            order_id: int,
            quantity: float,
            info: strawberry.Info
    ) -> types.ProductionOrder:
        """Update production order quantity"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import ProductionOrder
        from decimal import Decimal

        order = await db.get(ProductionOrder, order_id)
        if not order: raise NotFoundException.order()

        if current_user.role.name != "super_admin" and order.company_id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage")

        if quantity <= 0:
            raise ValidationException.field("Quantity", "Трябва да е положително")

        order.quantity = Decimal(str(quantity))
        await db.commit()
        await db.refresh(order)
        return types.ProductionOrder.from_instance(order)

    @strawberry.mutation
    async def generate_label(self, order_id: int, info: strawberry.Info) -> types.LabelData:
        """Generate label for a production order"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import ProductionOrder, Recipe, sofia_now
        
        order = await db.get(ProductionOrder, order_id)
        if not order: raise NotFoundException.order()
        
        if current_user.role.name != "super_admin" and order.company_id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage")
        
        recipe = await db.get(Recipe, order.recipe_id)
        if not recipe: raise not_found("Recipe not found")
        
        now = sofia_now()
        expiry = now.date() + datetime.timedelta(days=recipe.shelf_life_days)
        
        # Batch number logic: ORDER-ID-DATE
        batch_num = f"PRD-{order.id}-{now.strftime('%y%m%d')}"
        
        # Collect allergens from ingredients
        from backend.database.models import RecipeIngredient, Ingredient
        from sqlalchemy import select
        
        # Get all unique allergens from all ingredients in this recipe
        allergen_stmt = select(Ingredient.allergens).join(
            RecipeIngredient, RecipeIngredient.ingredient_id == Ingredient.id
        ).where(RecipeIngredient.recipe_id == recipe.id)
        
        res = await db.execute(allergen_stmt)
        all_allergens = set()
        for row in res.scalars().all():
            if row:
                for a in row:
                    all_allergens.add(a)
        
        allergens_list = list(all_allergens) if all_allergens else ["Виж документацията на рецептата"]
        
        return types.LabelData(
            product_name=recipe.name,
            batch_number=batch_num,
            production_date=now,
            expiry_date=expiry,
            allergens=allergens_list,
            storage_conditions="Съхранение от 2°C до 6°C",
            qr_code_content=f"BATCH:{batch_num}|PROD:{recipe.name}",
            quantity=f"{order.quantity} {recipe.yield_unit}"
        )

    @strawberry.mutation
    async def create_quick_sale(self, input: inputs.QuickSaleInput, info: strawberry.Info) -> types.ProductionOrder:
        """Създава бърза продажба и я записва като приход в касовия дневник"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        target_company_id = input.company_id if current_user.role.name == "super_admin" else current_user.company_id
        if not target_company_id:
            raise ValidationException.required_field("Company ID")

        from backend.database.models import ProductionOrder, Recipe, sofia_now, Company
        from datetime import timedelta

        # Get recipe
        recipe = await db.get(Recipe, input.recipe_id)
        if not recipe:
            raise NotFoundException.recipe()

        # Create production order with completed status (direct sale)
        now = sofia_now()
        order = ProductionOrder(
            recipe_id=input.recipe_id,
            quantity=Decimal(str(input.quantity)),
            due_date=now,
            production_deadline=now,
            status="completed",
            notes=f"Бърза продажба - {input.payment_method}" + (f" - {input.client_name}" if input.client_name else ""),
            company_id=target_company_id,
            created_by=current_user.id
        )
        db.add(order)
        await db.flush()

        # Create cash journal entry (приход)
        from backend.database.models import CashJournalEntry
        cash_entry = CashJournalEntry(
            date=now.date() if hasattr(now, 'date') else now,
            operation_type="income",
            amount=Decimal(str(input.price)) if input.price else Decimal("0"),
            description=f"Продажба: {recipe.name} x {input.quantity}" + (f" - {input.client_name}" if input.client_name else ""),
            reference_type="quick_sale",
            payment_method=input.payment_method,
            company_id=target_company_id,
            created_by=current_user.id
        )
        db.add(cash_entry)

        await db.commit()
        await db.refresh(order)
        return types.ProductionOrder.from_instance(order)

    # --- Access Control (KD) Mutations ---

    @strawberry.mutation
    async def trigger_door_remote(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")
        
        from backend.database.models import AccessDoor, Gateway
        door = await db.get(AccessDoor, id)
        if not door: raise NotFoundException.resource("Door")
        
        gateway = await db.get(Gateway, door.gateway_id)
        if not gateway or not gateway.ip_address: raise InvalidOperationException.cannot_complete("Gateway offline or unreachable")
        
        import aiohttp
        url = f"http://{gateway.ip_address}:{gateway.terminal_port}/access/doors/{door.door_id}/trigger"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    return response.status == 200
        except:
            return False

    @strawberry.mutation
    async def create_access_zone(self, input: inputs.AccessZoneInput, info: strawberry.Info) -> types.AccessZone:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")
        
        from backend.database.models import AccessZone
        new_zone = AccessZone(
            zone_id=input.zone_id,
            name=input.name,
            level=input.level,
            depends_on=input.depends_on,
            required_hours_start=input.required_hours_start,
            required_hours_end=input.required_hours_end,
            anti_passback_enabled=input.anti_passback_enabled,
            anti_passback_type=input.anti_passback_type,
            anti_passback_timeout=input.anti_passback_timeout,
            description=input.description,
            company_id=current_user.company_id
        )
        db.add(new_zone)
        await db.commit()
        await db.refresh(new_zone)
        return types.AccessZone.from_instance(new_zone)

    @strawberry.mutation
    async def update_access_zone(self, id: int, input: inputs.AccessZoneInput, info: strawberry.Info) -> types.AccessZone:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")
            
        from backend.database.models import AccessZone
        zone = await db.get(AccessZone, id)
        if not zone:
            raise NotFoundException.resource("Zone")
            
        # Update fields
        zone.zone_id = input.zone_id
        zone.name = input.name
        zone.level = input.level
        zone.depends_on = input.depends_on
        zone.required_hours_start = input.required_hours_start
        zone.required_hours_end = input.required_hours_end
        zone.anti_passback_enabled = input.anti_passback_enabled
        zone.anti_passback_type = input.anti_passback_type
        zone.anti_passback_timeout = input.anti_passback_timeout
        zone.description = input.description
        
        await db.commit()
        await db.refresh(zone)
        return types.AccessZone.from_instance(zone)

    @strawberry.mutation
    async def delete_access_zone(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")
        
        from backend.database.models import AccessZone
        zone = await db.get(AccessZone, id)
        if zone:
            await db.delete(zone)
            await db.commit()
            return True
        return False

    @strawberry.mutation
    async def open_door(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")
            
        from backend.database.models import AccessDoor, Gateway
        door = await db.get(AccessDoor, id)
        if not door: raise NotFoundException.resource("Door")
        
        gw = await db.get(Gateway, door.gateway_id)
        if not gw or not gw.ip_address: raise InvalidOperationException.cannot_complete("Gateway offline or no IP")

        import aiohttp
        # Gateway internal endpoint: /access/doors/{door_id}/trigger
        url = f"http://{gw.ip_address}:{gw.web_port}/access/doors/{door.door_id}/trigger"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, timeout=aiohttp.ClientTimeout(total=5)) as r:
                    if r.status == 200:
                        return True
                    try:
                        data = await r.json()
                        msg = data.get("message", "Gateway error")
                    except:
                        msg = f"Gateway returned {r.status}"
                    raise InvalidOperationException(detail=msg)
        except Exception as e:
            raise InvalidOperationException(detail=f"Connection error: {str(e)}")

    @strawberry.mutation
    async def create_access_door(self, input: inputs.AccessDoorInput, info: strawberry.Info) -> types.AccessDoor:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")
        
        from backend.database.models import AccessDoor
        new_door = AccessDoor(
            door_id=input.door_id,
            name=input.name,
            zone_db_id=input.zone_db_id,
            gateway_id=input.gateway_id,
            device_id=input.device_id,
            relay_number=input.relay_number,
            terminal_id=input.terminal_id,
            description=input.description
        )
        db.add(new_door)
        await db.commit()
        await db.refresh(new_door)
        return types.AccessDoor.from_instance(new_door)

    @strawberry.mutation
    async def delete_access_door(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")
        
        from backend.database.models import AccessDoor
        door = await db.get(AccessDoor, id)
        if door:
            await db.delete(door)
            await db.commit()
            return True
        return False

    @strawberry.mutation
    async def update_door_terminal(
        self,
        id: int,
        terminal_id: Optional[str],
        terminal_mode: Optional[str],
        info: strawberry.Info
    ) -> types.AccessDoor:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")
        
        from backend.database.models import AccessDoor, Terminal
        from sqlalchemy import update
        
        door = await db.get(AccessDoor, id)
        if not door:
            raise NotFoundException.resource("Door")
        
        # 1. Ако задаваме нов терминал на тази врата, първо разкачаме този терминал от ВСИЧКИ други врати
        if terminal_id:
            await db.execute(
                update(AccessDoor)
                .where(AccessDoor.terminal_id == terminal_id)
                .where(AccessDoor.id != id)
                .values(terminal_id=None)
            )
            
            # Обновяваме режима и на самия терминал за синхрон
            res = await db.execute(select(Terminal).where(Terminal.hardware_uuid == terminal_id))
            terminal = res.scalar_one_or_none()
            if terminal and terminal_mode:
                terminal.mode = terminal_mode
        
        # 2. Обновяваме вратата
        door.terminal_id = terminal_id
        if terminal_mode is not None:
            door.terminal_mode = terminal_mode
        
        await db.commit()
        await db.refresh(door)
        return types.AccessDoor.from_instance(door)

    @strawberry.mutation
    async def update_terminal(
        self,
        id: int,
        alias: Optional[str] = None,
        mode: Optional[str] = None,
        is_active: Optional[bool] = None,
        info: Optional[strawberry.Info] = None
    ) -> types.Terminal:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")
            
        from backend.database.models import Terminal
        terminal = await db.get(Terminal, id)
        if not terminal:
            raise NotFoundException.resource("Terminal") 
        if alias is not None:
            terminal.alias = alias
        if mode is not None:
            terminal.mode = mode
        if is_active is not None:
            terminal.is_active = is_active
            
        await db.commit()
        await db.refresh(terminal)
        return types.Terminal.from_instance(terminal)

    @strawberry.mutation
    async def create_access_code(self, input: inputs.AccessCodeInput, info: strawberry.Info) -> types.AccessCode:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")
        
        import secrets
        from backend.database.models import AccessCode
        code = input.code or secrets.token_hex(4).upper()
        expires_at = None
        if input.expires_hours:
            expires_at = datetime.datetime.now() + datetime.timedelta(hours=input.expires_hours)
        
        new_code = AccessCode(
            code=code,
            code_type=input.code_type,
            zones=input.zones,
            uses_remaining=input.uses_remaining,
            expires_at=expires_at,
            created_by=current_user.id,
            gateway_id=input.gateway_id
        )
        db.add(new_code)
        await db.commit()
        await db.refresh(new_code)
        return types.AccessCode.from_instance(new_code)

    @strawberry.mutation
    async def revoke_access_code(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")
        
        from backend.database.models import AccessCode
        code = await db.get(AccessCode, id)
        if code:
            code.is_active = False
            await db.commit()
            return True
        return False

    @strawberry.mutation
    async def sync_gateway_config(self, id: int, direction: str, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail="Not authenticated")
        
        from backend.database.models import Gateway
        gw = await db.get(Gateway, id)
        raise NotFoundException.resource("Gateway")
        if not gw.ip_address: raise InvalidOperationException.cannot_complete("Gateway offline or no IP")

        import aiohttp
        # Map push/pull to gateway's internal endpoints
        # gateway has /sync/push and /sync/pull
        url = f"http://{gw.ip_address}:{gw.web_port}/sync/{direction}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, timeout=aiohttp.ClientTimeout(total=10)) as r:
                    if r.status == 200:
                        return True
                    try:
                        data = await r.json()
                        msg = data.get("message", "Gateway error")
                    except:
                        msg = f"Gateway returned {r.status}"
                    raise InvalidOperationException(detail=msg)
        except Exception as e:
            raise InvalidOperationException(detail=f"Connection error: {str(e)}")

    @strawberry.mutation
    async def delete_access_code(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")
        
        from backend.database.models import AccessCode
        code = await db.get(AccessCode, id)
        if code:
            await db.delete(code)
            await db.commit()
            return True
        return False

    @strawberry.mutation
    async def assign_zone_to_user(self, user_id: int, zone_id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")
        
        from backend.database.models import User, AccessZone, user_access_zones
        from sqlalchemy import insert
        
        # Check if already assigned
        stmt = select(user_access_zones).where(
            user_access_zones.c.user_id == user_id,
            user_access_zones.c.zone_id == zone_id
        )
        res = await db.execute(stmt)
        if res.first(): return True
        
        await db.execute(insert(user_access_zones).values(user_id=user_id, zone_id=zone_id))
        await db.commit()
        return True

    @strawberry.mutation
    async def remove_zone_from_user(self, user_id: int, zone_id: int, info: strawberry.Info) -> bool:

        from backend.database.models import user_access_zones
        from sqlalchemy import delete 

        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")
 
        await db.execute(delete(user_access_zones).where(
            user_access_zones.c.user_id == user_id,
            user_access_zones.c.zone_id == zone_id
        ))
        await db.commit()
        return True

    @strawberry.mutation
    async def bulk_update_user_access(self, user_ids: List[int], zone_ids: List[int], action: str, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")
        
        from backend.database.models import user_access_zones
        from sqlalchemy import insert, delete, and_
        
        if action == "add":
            for uid in user_ids:
                for zid in zone_ids:
                    # Проверка за съществуващ запис
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

    @strawberry.mutation
    async def bulk_emergency_action(self, action: str, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")
        
        from backend.database.models import Gateway, AuditLog
        from sqlalchemy import update
        
        # 1. Update all gateways
        await db.execute(
            update(Gateway)
            .where(Gateway.company_id == current_user.company_id)
            .values(system_mode=action)
        )
        
        # 2. Log
        log = AuditLog(
            user_id=current_user.id,
            action=f"EMERGENCY_{action.upper()}",
            target_type="System",
            details=f"Групово действие: {action}"
        )
        db.add(log)
        await db.commit()
        return True

    @strawberry.mutation
    async def delete_terminal(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")
            
        from backend.database.models import Terminal
        terminal = await db.get(Terminal, id)
        if terminal:
            await db.delete(terminal)
            await db.commit()
            return True
        return False

    @strawberry.mutation
    async def update_gateway(
        self, 
        id: int, 
        alias: Optional[str] = None, 
        company_id: Optional[int] = None,
        info: Optional[strawberry.Info] = None
    ) -> types.Gateway:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")

        from backend.database.models import Gateway
        gateway = await db.get(Gateway, id)
        if not gateway:
            raise NotFoundException.resource("Gateway")

        if alias is not None:
            gateway.alias = alias
        if company_id is not None:
            gateway.company_id = company_id

        await db.commit()
        await db.refresh(gateway)
        return types.Gateway.from_instance(gateway)

    # ==================== ТРЗ Mutations ====================

    @strawberry.mutation
    async def create_night_work_bonus(
        self,
        user_id: int,
        date: datetime.date,
        hours: float,
        hourly_rate: float,
        period_id: Optional[int] = None,
        notes: Optional[str] = None,
        info: Optional[strawberry.Info] = None
    ) -> types.NightWorkBonus:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")

        from backend.database.models import NightWorkBonus
        from decimal import Decimal

        amount = Decimal(str(hours)) * Decimal(str(hourly_rate)) * Decimal("1.5")  # 50% надбавка

        night_work = NightWorkBonus(
            user_id=user_id,
            period_id=period_id,
            date=date,
            hours=Decimal(str(hours)),
            hourly_rate=Decimal(str(hourly_rate)),
            amount=amount,
            is_paid=False,
            notes=notes
        )
        db.add(night_work)
        await db.commit()
        await db.refresh(night_work)
        return types.NightWorkBonus.from_instance(night_work)

    @strawberry.mutation
    async def create_overtime_work(
        self,
        user_id: int,
        date: datetime.date,
        hours: float,
        hourly_rate: float,
        multiplier: float = 1.5,
        period_id: Optional[int] = None,
        notes: Optional[str] = None,
        info: Optional[strawberry.Info] = None
    ) -> types.OvertimeWork:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")

        from backend.database.models import OvertimeWork
        from decimal import Decimal

        amount = Decimal(str(hours)) * Decimal(str(hourly_rate)) * Decimal(str(multiplier))

        overtime = OvertimeWork(
            user_id=user_id,
            period_id=period_id,
            date=date,
            hours=Decimal(str(hours)),
            hourly_rate=Decimal(str(hourly_rate)),
            multiplier=Decimal(str(multiplier)),
            amount=amount,
            is_paid=False,
            notes=notes
        )
        db.add(overtime)
        await db.commit()
        await db.refresh(overtime)
        return types.OvertimeWork.from_instance(overtime)

    @strawberry.mutation
    async def create_business_trip(
        self,
        user_id: int,
        destination: str,
        start_date: datetime.date,
        end_date: datetime.date,
        daily_allowance: float = 40.00,
        accommodation: float = 0,
        transport: float = 0,
        other_expenses: float = 0,
        department_id: Optional[int] = None,
        period_id: Optional[int] = None,
        notes: Optional[str] = None,
        info: Optional[strawberry.Info] = None
    ) -> types.BusinessTrip:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise PermissionDeniedException.for_action("access")

        from backend.database.models import BusinessTrip
        from decimal import Decimal

        days = (end_date - start_date).days + 1
        total_amount = Decimal(str(daily_allowance)) * Decimal(str(days)) + \
                      Decimal(str(accommodation)) + Decimal(str(transport)) + Decimal(str(other_expenses))

        trip = BusinessTrip(
            user_id=user_id,
            period_id=period_id,
            department_id=department_id,
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            daily_allowance=Decimal(str(daily_allowance)),
            accommodation=Decimal(str(accommodation)),
            transport=Decimal(str(transport)),
            other_expenses=Decimal(str(other_expenses)),
            total_amount=total_amount,
            status="pending",
            notes=notes
        )
        db.add(trip)
        await db.commit()
        await db.refresh(trip)
        return types.BusinessTrip.from_instance(trip)

    @strawberry.mutation
    async def approve_business_trip(
        self,
        trip_id: int,
        approved: bool,
        notes: Optional[str] = None,
        info: Optional[strawberry.Info] = None
    ) -> types.BusinessTrip:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")

        from backend.database.models import BusinessTrip
        from backend.database.models import sofia_now

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
    async def create_work_experience(
        self,
        user_id: int,
        company_name: str,
        start_date: datetime.date,
        end_date: Optional[datetime.date] = None,
        position: Optional[str] = None,
        years: int = 0,
        months: int = 0,
        class_level: Optional[str] = None,
        is_current: bool = False,
        notes: Optional[str] = None,
        info: Optional[strawberry.Info] = None
    ) -> types.WorkExperience:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")

        from backend.database.models import WorkExperience

        experience = WorkExperience(
            user_id=user_id,
            company_id=current_user.company_id,
            company_name=company_name,
            position=position,
            start_date=start_date,
            end_date=end_date,
            years=years,
            months=months,
            class_level=class_level,
            is_current=is_current,
            notes=notes
        )
        db.add(experience)
        await db.commit()
        await db.refresh(experience)
        return types.WorkExperience.from_instance(experience)

    @strawberry.mutation
    async def mark_payslip_as_paid(
        self,
        payslip_id: int,
        payment_date: Optional[datetime.datetime] = None,
        payment_method: str = "bank",
        info: Optional[strawberry.Info] = None
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
            message=f"Заплата за период {payslip.period_start.strftime('%d.%m.%Y')} - {payslip.period_end.strftime('%d.%m.%Y')} е маркирана като платена."
        )
        await db.commit()
        
        return types.Payslip.from_instance(payslip)

    @strawberry.mutation
    async def bulk_mark_payslips_as_paid(
        self,
        payslip_ids: List[int],
        payment_date: Optional[datetime.datetime] = None,
        payment_method: str = "bank",
        info: Optional[strawberry.Info] = None
    ) -> List[types.Payslip]:
        """
        Bulk mark multiple payslips as paid.
        Used for batch payment processing.
        """
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        from backend.database.models import Payslip
        
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
        return [types.Payslip.from_instance(p) for p in updated_payslips]

    @strawberry.mutation
    async def generate_sepa_xml(
        self,
        company_id: int,
        period_start: datetime.date,
        period_end: datetime.date,
        execution_date: Optional[datetime.date] = None,
        info: Optional[strawberry.Info] = None
    ) -> str:
        """
        Generate SEPA XML file for payroll payments.
        """
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        from backend.database.models import Payslip, User, EmploymentContract
        from backend.services.sepa_generator import SEPAGenerator
        from sqlalchemy import select, and_
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
                    Payslip.payment_status == "paid"
                )
            )
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
                        EmploymentContract.is_active == True
                    )
                )
                emp = emp_result.scalars().first()
                
                payments.append({
                    "name": f"{user.firstName or ''} {user.lastName or ''}".strip(),
                    "iban": user.iban,
                    "amount": float(payslip.total_amount),
                    "reference": f"SAL-{payslip.id}",
                    "description": f"Заплата {period_start.strftime('%m/%Y')}"
                })
        
        # Generate SEPA XML
        generator = SEPAGenerator(
            sender_name=company_name,
            sender_iban=company_iban,
            sender_bic=company_bic
        )
        
        validation = generator.validate_payments(payments)
        if not validation["valid"]:
            raise ValidationException(detail=f"Invalid payments: {', '.join(validation['errors'])}")
        
        return generator.generate_payment_xml(
            payments=payments,
            batch_name=f"Payroll {period_start.strftime('%m/%Y')}",
            execution_date=execution_date.strftime("%Y-%m-%d") if execution_date else None
        )

    @strawberry.mutation
    async def create_contract_annex(
        self,
        contract_id: int,
        effective_date: datetime.date,
        annex_number: Optional[str] = None,
        base_salary: Optional[Decimal] = None,
        position_id: Optional[int] = None,
        work_hours_per_week: Optional[int] = None,
        night_work_rate: Optional[float] = None,
        overtime_rate: Optional[float] = None,
        holiday_rate: Optional[float] = None,
        info: Optional[strawberry.Info] = None
    ) -> types.ContractAnnex:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")

        from backend.database.models import ContractAnnex
        
        annex = ContractAnnex(
            contract_id=contract_id,
            annex_number=annex_number,
            effective_date=effective_date,
            base_salary=base_salary,
            position_id=position_id,
            work_hours_per_week=work_hours_per_week,
            night_work_rate=Decimal(str(night_work_rate)) if night_work_rate is not None else None,
            overtime_rate=Decimal(str(overtime_rate)) if overtime_rate is not None else None,
            holiday_rate=Decimal(str(holiday_rate)) if holiday_rate is not None else None,
            is_signed=False
        )
        db.add(annex)
        await db.commit()
        await db.refresh(annex)
        return types.ContractAnnex.from_instance(annex)

    # === Contract Templates ===

    @strawberry.mutation
    async def create_contract_template(
        self,
        name: str,
        description: Optional[str],
        contract_type: str,
        work_hours_per_week: int,
        probation_months: int,
        salary_calculation_type: str,
        payment_day: int,
        night_work_rate: float,
        overtime_rate: float,
        holiday_rate: float,
        work_class: Optional[str],
        position_id: Optional[int] = None,
        department_id: Optional[int] = None,
        base_salary: Optional[float] = None,
        clause_ids: Optional[str] = None,  # JSON string like "[1,2,3]"
        info: Optional[strawberry.Info] = None
    ) -> types.ContractTemplate:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")

        from backend.database.models import ContractTemplate, ContractTemplateVersion, ContractTemplateSection, ContractTemplateClause
        from backend.database.models import sofia_now
        from decimal import Decimal
        import json

        template = ContractTemplate(
            company_id=current_user.company_id,
            name=name,
            description=description,
            contract_type=contract_type,
            work_hours_per_week=work_hours_per_week,
            probation_months=probation_months,
            salary_calculation_type=salary_calculation_type,
            payment_day=payment_day,
            night_work_rate=Decimal(str(night_work_rate)),
            overtime_rate=Decimal(str(overtime_rate)),
            holiday_rate=Decimal(str(holiday_rate)),
            work_class=work_class,
            position_id=position_id,
            department_id=department_id,
            base_salary=Decimal(str(base_salary)) if base_salary else None,
            is_active=True,
        )
        db.add(template)
        await db.flush()

        # Добавяне на клаузи
        if clause_ids:
            try:
                clause_id_list = json.loads(clause_ids)
                for idx, clause_id in enumerate(clause_id_list):
                    clause_assoc = ContractTemplateClause(
                        template_id=template.id,
                        clause_id=clause_id,
                        order_index=idx
                    )
                    db.add(clause_assoc)
            except:
                pass

        version = ContractTemplateVersion(
            template_id=template.id,
            version=1,
            contract_type=contract_type,
            work_hours_per_week=work_hours_per_week,
            probation_months=probation_months,
            salary_calculation_type=salary_calculation_type,
            payment_day=payment_day,
            night_work_rate=Decimal(str(night_work_rate)),
            overtime_rate=Decimal(str(overtime_rate)),
            holiday_rate=Decimal(str(holiday_rate)),
            work_class=work_class,
            position_id=position_id,
            department_id=department_id,
            base_salary=Decimal(str(base_salary)) if base_salary else None,
            is_current=True,
            created_by=f"{current_user.first_name} {current_user.last_name}" if current_user.first_name else current_user.email,
            change_note="Първоначална версия"
        )
        db.add(version)
        await db.flush()

        default_sections = [
            {"title": "Предмет на договора", "content": "Работодателят предоставя на Работника работата на длъжността.", "order_index": 0, "is_required": True},
            {"title": "Работно време и почивки", "content": f"Работникът изпълнява работата си в рамките на {work_hours_per_week} часа седмично.", "order_index": 1, "is_required": True},
            {"title": "Права и задължения на работодателя", "content": "Работодателят е длъжен да осигури на Работника работата и необходимите условия.", "order_index": 2, "is_required": True},
            {"title": "Права и задължения на работника", "content": "Работникът е длъжен да изпълнява работата лично и да спазва реда в предприятието.", "order_index": 3, "is_required": True},
            {"title": "Заплащане", "content": "За извършената работа Работодателят заплаща трудовото възнаграждение.", "order_index": 4, "is_required": True},
            {"title": "Конфиденциалност", "content": "Работникът се задължава да не разкрива на трети лица информация, станала му известна.", "order_index": 5, "is_required": False},
        ]

        for section_data in default_sections:
            section = ContractTemplateSection(
                template_id=template.id,
                version_id=version.id,
                title=section_data["title"],
                content=section_data["content"],
                order_index=section_data["order_index"],
                is_required=section_data["is_required"],
            )
            db.add(section)

        await db.commit()
        await db.refresh(template)
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

    @strawberry.mutation
    async def update_contract_template(
        self,
        id: int,
        name: str,
        description: Optional[str],
        contract_type: str,
        work_hours_per_week: int,
        probation_months: int,
        salary_calculation_type: str,
        payment_day: int,
        night_work_rate: float,
        overtime_rate: float,
        holiday_rate: float,
        work_class: Optional[str],
        change_note: str,
        info: Optional[strawberry.Info] = None
    ) -> types.ContractTemplate:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")

        from backend.database.models import ContractTemplate, ContractTemplateVersion
        from decimal import Decimal

        template = await db.get(ContractTemplate, id)
        if not template:
            raise NotFoundException.resource("Template")

        template.name = name
        template.description = description
        template.contract_type = contract_type
        template.work_hours_per_week = work_hours_per_week
        template.probation_months = probation_months
        template.salary_calculation_type = salary_calculation_type
        template.payment_day = payment_day
        template.night_work_rate = Decimal(str(night_work_rate))
        template.overtime_rate = Decimal(str(overtime_rate))
        template.holiday_rate = Decimal(str(holiday_rate))
        template.work_class = work_class

        stmt = select(ContractTemplateVersion).where(
            ContractTemplateVersion.template_id == id,
            ContractTemplateVersion.is_current == True
        )
        result = await db.execute(stmt)
        current_version = result.scalar_one_or_none()

        if current_version:
            current_version.is_current = False

        new_version = ContractTemplateVersion(
            template_id=template.id,
            version=current_version.version + 1 if current_version else 1,
            contract_type=contract_type,
            work_hours_per_week=work_hours_per_week,
            probation_months=probation_months,
            salary_calculation_type=salary_calculation_type,
            payment_day=payment_day,
            night_work_rate=Decimal(str(night_work_rate)),
            overtime_rate=Decimal(str(overtime_rate)),
            holiday_rate=Decimal(str(holiday_rate)),
            work_class=work_class,
            is_current=True,
            created_by=f"{current_user.first_name} {current_user.last_name}" if current_user.first_name else current_user.email,
            change_note=change_note
        )
        db.add(new_version)

        await db.commit()
        await db.refresh(template)
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

    @strawberry.mutation
    async def delete_contract_template(
        self,
        id: int,
        info: Optional[strawberry.Info] = None
    ) -> bool:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")

        from backend.database.models import ContractTemplate

        template = await db.get(ContractTemplate, id)
        if not template:
            raise NotFoundException.resource("Template")

        template.is_active = False
        await db.commit()
        return True

    @strawberry.mutation
    async def restore_contract_template_version(
        self,
        version_id: int,
        info: Optional[strawberry.Info] = None
    ) -> types.ContractTemplate:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")

        from backend.database.models import ContractTemplate, ContractTemplateVersion
        from decimal import Decimal

        version = await db.get(ContractTemplateVersion, version_id)
        if not version:
            raise NotFoundException.resource("Version")

        template = await db.get(ContractTemplate, version.template_id)
        if not template:
            raise NotFoundException.resource("Template")

        stmt = select(ContractTemplateVersion).where(
            ContractTemplateVersion.template_id == template.id,
            ContractTemplateVersion.is_current == True
        )
        result = await db.execute(stmt)
        current = result.scalar_one_or_none()
        if current:
            current.is_current = False

        version.is_current = True

        template.contract_type = version.contract_type
        template.work_hours_per_week = version.work_hours_per_week
        template.probation_months = version.probation_months
        template.salary_calculation_type = version.salary_calculation_type
        template.payment_day = version.payment_day
        template.night_work_rate = version.night_work_rate
        template.overtime_rate = version.overtime_rate
        template.holiday_rate = version.holiday_rate
        template.work_class = version.work_class

        await db.commit()
        await db.refresh(template)
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

    # === Annex Templates ===

    @strawberry.mutation
    async def create_annex_template(
        self,
        name: str,
        description: Optional[str],
        change_type: str,
        new_base_salary: Optional[float],
        new_work_hours_per_week: Optional[int],
        new_night_work_rate: Optional[float],
        new_overtime_rate: Optional[float],
        new_holiday_rate: Optional[float],
        info: Optional[strawberry.Info] = None
    ) -> types.AnnexTemplate:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")

        from backend.database.models import AnnexTemplate, AnnexTemplateVersion, AnnexTemplateSection
        from decimal import Decimal

        template = AnnexTemplate(
            company_id=current_user.company_id,
            name=name,
            description=description,
            change_type=change_type,
            new_base_salary=Decimal(str(new_base_salary)) if new_base_salary else None,
            new_work_hours_per_week=new_work_hours_per_week,
            new_night_work_rate=Decimal(str(new_night_work_rate)) if new_night_work_rate else None,
            new_overtime_rate=Decimal(str(new_overtime_rate)) if new_overtime_rate else None,
            new_holiday_rate=Decimal(str(new_holiday_rate)) if new_holiday_rate else None,
            is_active=True,
        )
        db.add(template)
        await db.flush()

        version = AnnexTemplateVersion(
            template_id=template.id,
            version=1,
            change_type=change_type,
            new_base_salary=Decimal(str(new_base_salary)) if new_base_salary else None,
            new_work_hours_per_week=new_work_hours_per_week,
            new_night_work_rate=Decimal(str(new_night_work_rate)) if new_night_work_rate else None,
            new_overtime_rate=Decimal(str(new_overtime_rate)) if new_overtime_rate else None,
            new_holiday_rate=Decimal(str(new_holiday_rate)) if new_holiday_rate else None,
            is_current=True,
            created_by=f"{current_user.first_name} {current_user.last_name}" if current_user.first_name else current_user.email,
            change_note="Първоначална версия"
        )
        db.add(version)
        await db.flush()

        default_sections = [
            {"title": "Описание на промените", "content": "С настоящето споразумение се променят следните условия от трудовия договор:", "order_index": 0, "is_required": True},
            {"title": "Основание", "content": "Настоящето споразумение се сключва на основание чл. 119, ал. 1 от Кодекса на труда.", "order_index": 1, "is_required": False},
        ]

        for section_data in default_sections:
            section = AnnexTemplateSection(
                template_id=template.id,
                version_id=version.id,
                title=section_data["title"],
                content=section_data["content"],
                order_index=section_data["order_index"],
                is_required=section_data["is_required"],
            )
            db.add(section)

        await db.commit()
        await db.refresh(template)
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

    @strawberry.mutation
    async def delete_annex_template(
        self,
        id: int,
        info: Optional[strawberry.Info] = None
    ) -> bool:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")

        from backend.database.models import AnnexTemplate

        template = await db.get(AnnexTemplate, id)
        if not template:
            raise NotFoundException.resource("Template")

        template.is_active = False
        await db.commit()
        return True

    # === Clause Templates ===

    @strawberry.mutation
    async def create_clause_template(
        self,
        title: str,
        content: str,
        category: str,
        info: Optional[strawberry.Info] = None
    ) -> types.ClauseTemplate:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")

        from backend.database.models import ClauseTemplate

        clause = ClauseTemplate(
            company_id=current_user.company_id,
            title=title,
            content=content,
            category=category,
            is_active=True,
        )
        db.add(clause)
        await db.commit()
        await db.refresh(clause)
        return types.ClauseTemplate(
            id=clause.id,
            company_id=clause.company_id,
            title=clause.title,
            content=clause.content,
            category=clause.category,
            is_active=clause.is_active,
            created_at=clause.created_at
        )

    @strawberry.mutation
    async def update_clause_template(
        self,
        id: int,
        title: str,
        content: str,
        category: str,
        info: Optional[strawberry.Info] = None
    ) -> types.ClauseTemplate:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")

        from backend.database.models import ClauseTemplate

        clause = await db.get(ClauseTemplate, id)
        if not clause:
            raise NotFoundException.resource("Clause")

        clause.title = title
        clause.content = content
        clause.category = category

        await db.commit()
        await db.refresh(clause)
        return types.ClauseTemplate(
            id=clause.id,
            company_id=clause.company_id,
            title=clause.title,
            content=clause.content,
            category=clause.category,
            is_active=clause.is_active,
            created_at=clause.created_at
        )

    @strawberry.mutation
    async def delete_clause_template(
        self,
        id: int,
        info: Optional[strawberry.Info] = None
    ) -> bool:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")

        from backend.database.models import ClauseTemplate

        clause = await db.get(ClauseTemplate, id)
        if not clause:
            raise NotFoundException.resource("Clause")

        clause.is_active = False
        await db.commit()
        return True

    # ============ Contract Template Section CRUD ============

    @strawberry.mutation
    async def add_section_to_contract_template(
        self,
        template_id: int,
        section: inputs.ContractTemplateSectionInput,
        info: Optional[strawberry.Info] = None
    ) -> types.ContractTemplateSection:
        """Добавя секция към шаблон за договор"""
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")

        from backend.database.models import ContractTemplate, ContractTemplateSection, ContractTemplateVersion
        
        template = await db.get(ContractTemplate, template_id)
        if not template:
            raise NotFoundException.resource("Template")
        
        # Намираме текущата версия
        stmt = select(ContractTemplateVersion).where(
            ContractTemplateVersion.template_id == template_id,
            ContractTemplateVersion.is_current == True
        )
        result = await db.execute(stmt)
        current_version = result.scalar_one_or_none()
        
        if not current_version:
            raise NotFoundException.resource("Version")
        
        # Създаваме секцията
        new_section = ContractTemplateSection(
            template_id=template_id,
            version_id=current_version.id,
            title=section.title,
            content=section.content,
            order_index=section.order_index,
            is_required=section.is_required
        )
        db.add(new_section)
        await db.commit()
        await db.refresh(new_section)
        
        return types.ContractTemplateSection(
            id=new_section.id,
            template_id=new_section.template_id,
            version_id=new_section.version_id,
            title=new_section.title,
            content=new_section.content,
            order_index=new_section.order_index,
            is_required=new_section.is_required
        )

    @strawberry.mutation
    async def update_section_in_contract_template(
        self,
        section_id: int,
        section: inputs.ContractTemplateSectionUpdateInput,
        info: Optional[strawberry.Info] = None
    ) -> types.ContractTemplateSection:
        """Обновява секция в шаблон за договор"""
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")

        from backend.database.models import ContractTemplateSection
        
        db_section = await db.get(ContractTemplateSection, section_id)
        if not db_section:
            raise NotFoundException.resource("Section")
        
        if section.title is not None:
            db_section.title = section.title
        if section.content is not None:
            db_section.content = section.content
        if section.order_index is not None:
            db_section.order_index = section.order_index
        if section.is_required is not None:
            db_section.is_required = section.is_required
        
        await db.commit()
        await db.refresh(db_section)
        
        return types.ContractTemplateSection(
            id=db_section.id,
            template_id=db_section.template_id,
            version_id=db_section.version_id,
            title=db_section.title,
            content=db_section.content,
            order_index=db_section.order_index,
            is_required=db_section.is_required
        )

    @strawberry.mutation
    async def delete_section_from_contract_template(
        self,
        section_id: int,
        info: Optional[strawberry.Info] = None
    ) -> bool:
        """Изтрива секция от шаблон за договор"""
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")

        from backend.database.models import ContractTemplateSection
        
        db_section = await db.get(ContractTemplateSection, section_id)
        if not db_section:
            raise NotFoundException.resource("Section")
        
        await db.delete(db_section)
        await db.commit()
        return True

    # ============ Annex Template Section CRUD ============

    @strawberry.mutation
    async def add_section_to_annex_template(
        self,
        template_id: int,
        section: inputs.AnnexTemplateSectionInput,
        info: Optional[strawberry.Info] = None
    ) -> types.AnnexTemplateSection:
        """Добавя секция към шаблон за анекс"""
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")

        from backend.database.models import AnnexTemplate, AnnexTemplateSection, AnnexTemplateVersion
        
        template = await db.get(AnnexTemplate, template_id)
        if not template:
            raise NotFoundException.resource("Template")
        
        # Намираме текущата версия
        stmt = select(AnnexTemplateVersion).where(
            AnnexTemplateVersion.template_id == template_id,
            AnnexTemplateVersion.is_current == True
        )
        result = await db.execute(stmt)
        current_version = result.scalar_one_or_none()
        
        if not current_version:
            raise NotFoundException.resource("Version")
        
        # Създаваме секцията
        new_section = AnnexTemplateSection(
            template_id=template_id,
            version_id=current_version.id,
            title=section.title,
            content=section.content,
            order_index=section.order_index,
            is_required=section.is_required
        )
        db.add(new_section)
        await db.commit()
        await db.refresh(new_section)
        
        return types.AnnexTemplateSection(
            id=new_section.id,
            template_id=new_section.template_id,
            version_id=new_section.version_id,
            title=new_section.title,
            content=new_section.content,
            order_index=new_section.order_index,
            is_required=new_section.is_required
        )

    @strawberry.mutation
    async def update_section_in_annex_template(
        self,
        section_id: int,
        section: inputs.AnnexTemplateSectionUpdateInput,
        info: Optional[strawberry.Info] = None
    ) -> types.AnnexTemplateSection:
        """Обновява секция в шаблон за анекс"""
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")

        from backend.database.models import AnnexTemplateSection
        
        db_section = await db.get(AnnexTemplateSection, section_id)
        if not db_section:
            raise NotFoundException.resource("Section")
        
        if section.title is not None:
            db_section.title = section.title
        if section.content is not None:
            db_section.content = section.content
        if section.order_index is not None:
            db_section.order_index = section.order_index
        if section.is_required is not None:
            db_section.is_required = section.is_required
        
        await db.commit()
        await db.refresh(db_section)
        
        return types.AnnexTemplateSection(
            id=db_section.id,
            template_id=db_section.template_id,
            version_id=db_section.version_id,
            title=db_section.title,
            content=db_section.content,
            order_index=db_section.order_index,
            is_required=db_section.is_required
        )

    @strawberry.mutation
    async def delete_section_from_annex_template(
        self,
        section_id: int,
        info: Optional[strawberry.Info] = None
    ) -> bool:
        """Изтрива секция от шаблон за анекс"""
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")

        from backend.database.models import AnnexTemplateSection
        
        db_section = await db.get(AnnexTemplateSection, section_id)
        if not db_section:
            raise NotFoundException.resource("Section")
        
        await db.delete(db_section)
        await db.commit()
        return True

    # === Sign Annex (updated) ===

    @strawberry.mutation
    async def sign_contract_annex(
        self,
        annex_id: int,
        role: str = "employer",
        info: Optional[strawberry.Info] = None
    ) -> types.ContractAnnex:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")

        from backend.database.models import ContractAnnex, EmploymentContract, sofia_now
        
        annex = await db.get(ContractAnnex, annex_id)
        if not annex:
            raise NotFoundException.resource("Annex")
        
        now = sofia_now()
        
        if role == "employer":
            annex.signed_by_employer = True
            annex.signed_by_employer_at = now
        elif role == "employee":
            annex.signed_by_employee = True
            annex.signed_by_employee_at = now
        
        if annex.signed_by_employer and annex.signed_by_employee:
            annex.is_signed = True
            annex.signed_at = now
            annex.status = "signed"
            
            if annex.effective_date <= datetime.date.today():
                contract = await db.get(EmploymentContract, annex.contract_id)
                if contract:
                    if annex.base_salary is not None:
                        contract.base_salary = annex.base_salary
                    if annex.position_id is not None:
                        contract.position_id = annex.position_id
                    if annex.work_hours_per_week is not None:
                        contract.work_hours_per_week = annex.work_hours_per_week
                    if annex.night_work_rate is not None:
                        contract.night_work_rate = annex.night_work_rate
                    if annex.overtime_rate is not None:
                        contract.overtime_rate = annex.overtime_rate
                    if annex.holiday_rate is not None:
                        contract.holiday_rate = annex.holiday_rate
        else:
            annex.status = "pending"
        
        await db.commit()
        await db.refresh(annex)
        return types.ContractAnnex.from_instance(annex)

    @strawberry.mutation
    async def reject_contract_annex(
        self,
        annex_id: int,
        reason: str,
        info: Optional[strawberry.Info] = None
    ) -> types.ContractAnnex:
        """Отхвърля анекс"""
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin", "employee"]:
            raise PermissionDeniedException.for_action("access")

        from backend.database.models import ContractAnnex
        
        annex = await db.get(ContractAnnex, annex_id)
        if not annex:
            raise NotFoundException.resource("Annex")
        
        annex.status = "rejected"
        annex.rejection_reason = reason
        
        await db.commit()
        await db.refresh(annex)
        return types.ContractAnnex.from_instance(annex)

    # === NAP Reports (Фаза 7) ===
    
    @strawberry.mutation
    async def generate_annual_insurance_report(
        self,
        company_id: int,
        year: int,
        info: Optional[strawberry.Info] = None
    ) -> JSONScalar:
        """Генерира годишна справка за осигурени лица"""
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")
        
        from backend.services.nap_reports import NAPReportsGenerator
        
        generator = NAPReportsGenerator(db, company_id, year)
        return await generator.generate_annual_insurance_report()
    
    @strawberry.mutation
    async def generate_income_report_by_type(
        self,
        company_id: int,
        year: int,
        info: Optional[strawberry.Info] = None
    ) -> JSONScalar:
        """Генерира справка по чл. 73, ал. 6 ЗДДФЛ"""
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")
        
        from backend.services.nap_reports import NAPReportsGenerator
        
        generator = NAPReportsGenerator(db, company_id, year)
        return await generator.generate_income_report_by_type()
    
    @strawberry.mutation
    async def generate_service_book_export(
        self,
        company_id: int,
        year: int,
        info: Optional[strawberry.Info] = None
    ) -> JSONScalar:
        """Генерира експорт за електронната трудова книжка"""
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")
        
        from backend.services.nap_reports import NAPReportsGenerator
        
        generator = NAPReportsGenerator(db, company_id, year)
        return await generator.generate_service_book_export()
    
    @strawberry.mutation
    async def generate_monthly_declaration(
        self,
        company_id: int,
        year: int,
        month: int,
        info: Optional[strawberry.Info] = None
    ) -> JSONScalar:
        """Генерира месечна декларация за НАП"""
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")
        
        from backend.services.nap_reports import NAPReportsGenerator
        
        generator = NAPReportsGenerator(db, company_id, year)
        return await generator.generate_monthly_declaration(month)

    @strawberry.mutation
    async def create_employment_contract(
        self,
        input: inputs.EmploymentContractCreateInput,
        info: strawberry.Info
    ) -> types.EmploymentContract:
        """Създава нов трудов договор"""
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = info.context["current_user"]
        
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")
        
        from backend.database.models import EmploymentContract, ContractTemplate
        
        company_id = input.company_id
        if not company_id and current_user.company_id:
            company_id = current_user.company_id
        
        if not company_id:
            raise ValidationException.required_field("ID на фирмата")
        
        # Ако е избран шаблон, зареждаме данните от него
        template = None
        template_clauses = []
        if input.template_id:
            template = await db.get(ContractTemplate, input.template_id)
            # Зареждаме клаузите от шаблона
            if template:
                from backend.database.models import ContractTemplateClause
                clauses_result = await db.execute(
                    select(ContractTemplateClause).where(ContractTemplateClause.template_id == input.template_id)
                )
                template_clauses = [c.clause_id for c in clauses_result.scalars().all()]
        
        # Определяме clause_ids - от input или от шаблон
        final_clause_ids = input.clause_ids
        if not final_clause_ids and template_clauses:
            final_clause_ids = json.dumps(template_clauses) if template_clauses else None
        
        contract = EmploymentContract(
            employee_name=input.employee_name,
            employee_egn=input.employee_egn,
            company_id=company_id,
            department_id=input.department_id,
            position_id=input.position_id,
            template_id=input.template_id,
            user_id=None,
            contract_type=input.contract_type,
            contract_number=input.contract_number,
            start_date=input.start_date,
            end_date=input.end_date,
            base_salary=input.base_salary,
            work_hours_per_week=input.work_hours_per_week,
            job_description=input.job_description,
            status="draft",
            clause_ids=final_clause_ids,
            # TRZ полета - от шаблон или от input
            probation_months=input.probation_months if input.probation_months is not None else (template.probation_months if template else None),
            salary_calculation_type=input.salary_calculation_type or (template.salary_calculation_type if template else 'gross'),
            payment_day=input.payment_day if input.payment_day is not None else (template.payment_day if template else 25),
            night_work_rate=input.night_work_rate if input.night_work_rate is not None else (template.night_work_rate if template else 0.5),
            overtime_rate=input.overtime_rate if input.overtime_rate is not None else (template.overtime_rate if template else 1.5),
            holiday_rate=input.holiday_rate if input.holiday_rate is not None else (template.holiday_rate if template else 2.0),
            work_class=input.work_class or (template.work_class if template else None),
        )
        
        db.add(contract)
        await db.commit()
        await db.refresh(contract, ["company", "position", "department"])
        
        return types.EmploymentContract.from_instance(contract)

    @strawberry.mutation
    async def sign_employment_contract(
        self,
        id: int,
        info: strawberry.Info
    ) -> types.EmploymentContract:
        """Маркира трудов договор като подписан"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")
        
        from backend.database.models import EmploymentContract
        from datetime import datetime as dt
        
        contract = await db.get(EmploymentContract, id)
        if not contract:
            raise NotFoundException.record("Договор")
        
        if contract.status == "signed":
            raise ValidationException.field("Договор", "Вече е подписан")
        
        contract.status = "signed"
        contract.signed_at = dt.now()
        
        await db.commit()
        await db.refresh(contract, ["company", "position", "department"])
        
        return types.EmploymentContract.from_instance(contract)

    @strawberry.mutation
    async def link_employment_contract_to_user(
        self,
        contract_id: int,
        user_id: int,
        info: strawberry.Info
    ) -> types.EmploymentContract:
        """Свързва трудов договор с потребител"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")
        
        from backend.database.models import EmploymentContract, User
        
        contract = await db.get(EmploymentContract, contract_id)
        if not contract:
            raise NotFoundException.record("Договор")
        
        user = await db.get(User, user_id)
        if not user:
            raise NotFoundException.user()
        
        if contract.status != "signed":
            raise ValidationException.field("Договор", "Трябва първо да бъде подписан")
        
        contract.user_id = user_id
        contract.status = "linked"
        
        await db.commit()
        await db.refresh(contract, ["company", "position", "department"])
        
        return types.EmploymentContract.from_instance(contract)

    @strawberry.mutation
    async def generate_contract_number(
        self,
        company_id: int,
        info: strawberry.Info
    ) -> str:
        """Генерира уникален номер на трудов договор"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        
        if current_user is None or current_user.role is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")
        
        from backend.database.models import EmploymentContract, Company
        
        company = await db.get(Company, company_id)
        if not company:
            raise NotFoundException.resource("Фирма")
        
        current_year = datetime.datetime.now().year
        
        result = await db.execute(
            select(EmploymentContract).where(
                EmploymentContract.company_id == company_id
            )
        )
        all_contracts = result.scalars().all()
        
        year_contracts = [c for c in all_contracts if c.created_at and c.created_at.year == current_year]
        sequence = len(year_contracts) + 1
        
        company_code = company.eik if company.eik else str(company_id)
        contract_number = f"TRZ-{company_code}-{current_year}-{sequence:04d}"
        
        return contract_number

    @strawberry.mutation
    async def get_contract_pdf_url(
        self,
        contract_id: int,
        info: strawberry.Info
    ) -> str:
        """Връща URL за изтегляне на PDF на трудов договор"""
        from backend.config import settings
        
        db = info.context["db"]
        current_user = info.context["current_user"]
        
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")
        
        from backend.database.models import EmploymentContract
        
        contract = await db.get(EmploymentContract, contract_id)
        if not contract:
            raise NotFoundException.record("Договор")
        
        base_url = getattr(settings, 'API_URL', 'https://dev.oblak24.org')
        return f"{base_url}/export/contract/{contract_id}/pdf"

    @strawberry.mutation
    async def get_annex_pdf_url(
        self,
        annex_id: int,
        info: strawberry.Info
    ) -> str:
        """Връща URL за изтегляне на PDF на допълнително споразумение"""
        from backend.config import settings
        
        db = info.context["db"]
        current_user = info.context["current_user"]
        
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")
        
        from backend.database.models import ContractAnnex
        
        annex = await db.get(ContractAnnex, annex_id)
        if not annex:
            raise NotFoundException.record("Споразумение")
        
        base_url = getattr(settings, 'API_URL', 'https://dev.oblak24.org')
        return f"{base_url}/export/annex/{annex_id}/pdf"

    @strawberry.mutation
    async def get_invoice_pdf_url(
        self,
        invoice_id: int,
        info: strawberry.Info
    ) -> str:
        """Връща URL за изтегляне на PDF на фактура"""
        from backend.config import settings
        
        db = info.context["db"]
        current_user = info.context["current_user"]
        
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)
        
        from backend.database.models import Invoice
        
        invoice = await db.get(Invoice, invoice_id)
        if not invoice:
            raise NotFoundException.record("Фактура")
        
        if invoice.company_id != current_user.company_id:
            raise PermissionDeniedException.for_resource("фактура", "access")
        
        base_url = getattr(settings, 'API_URL', 'https://dev.oblak24.org')
        return f"{base_url}/export/invoice/{invoice_id}/pdf"

