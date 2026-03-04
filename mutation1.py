import strawberry
from strawberry.file_uploads import Upload
from typing import Optional, List
import datetime
from decimal import Decimal
from sqlalchemy import select

from fastapi import HTTPException, status

from backend.graphql import types, inputs
from backend import crud, schemas
from backend.graphql.inputs import (
    UserCreateInput, RoleCreateInput, UpdateUserInput,
    LeaveRequestInput, UpdateLeaveRequestStatusInput,
    CompanyCreateInput, CompanyUpdateInput, DepartmentCreateInput, DepartmentUpdateInput, PositionCreateInput,
    SmtpSettingsInput, BonusCreateInput, MonthlyWorkDaysInput,
    PasswordSettingsInput
)
from backend.services.holiday_service import fetch_and_store_holidays
from backend.services.orthodox_holiday_service import fetch_and_store_orthodox_holidays
from backend.database.models import LeaveRequest
from backend.auth.security import verify_password, hash_password, validate_password_complexity
from backend.auth.module_guard import verify_module_enabled


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
            raise HTTPException(status_code=401, detail="Not authenticated")

        await verify_module_enabled("integrations", db)

        # Read file content
        content = await file.read()
        filename = file.filename

        # Perform OCR
        from backend.services.ocr_service import extract_text_from_file
        ocr_text = extract_text_from_file(content, filename)

        stmt = select(LeaveRequest).where(LeaveRequest.id == request_id)
        res = await db.execute(stmt)
        req = res.scalars().first()

        if not req:
            raise HTTPException(status_code=404, detail="Request not found")

        if req.user_id != current_user.id and current_user.role.name not in ["admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Not authorized")

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
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")

        # Basic Validation
        if not settings.smtp_server or not settings.sender_email:
            raise HTTPException(status_code=400, detail="Server and Sender Email are required")

        await crud.set_global_setting(db, "smtp_server", settings.smtp_server)
        await crud.set_global_setting(db, "smtp_port", str(settings.smtp_port))
        await crud.set_global_setting(db, "smtp_username", settings.smtp_username)
        await crud.set_global_setting(db, "smtp_password", settings.smtp_password)
        await crud.set_global_setting(db, "sender_email", settings.sender_email)
        await crud.set_global_setting(db, "use_tls", str(settings.use_tls))

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
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")

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
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")

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
            info: strawberry.Info
    ) -> types.PayrollLegalSettings:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")

        await crud.set_global_setting(db, "payroll_max_insurance_base", str(max_insurance_base))
        await crud.set_global_setting(db, "payroll_employee_insurance_rate", str(employee_insurance_rate))
        await crud.set_global_setting(db, "payroll_income_tax_rate", str(income_tax_rate))
        await crud.set_global_setting(db, "payroll_civil_contract_costs_rate", str(civil_contract_costs_rate))
        await crud.set_global_setting(db, "payroll_noi_compensation_percent", str(noi_compensation_percent))
        await crud.set_global_setting(db, "payroll_employer_paid_sick_days", str(employer_paid_sick_days))
        await crud.set_global_setting(db, "payroll_default_tax_resident", str(default_tax_resident))

        return types.PayrollLegalSettings(
            max_insurance_base=max_insurance_base,
            employee_insurance_rate=employee_insurance_rate,
            income_tax_rate=income_tax_rate,
            civil_contract_costs_rate=civil_contract_costs_rate,
            noi_compensation_percent=noi_compensation_percent,
            employer_paid_sick_days=employer_paid_sick_days,
            default_tax_resident=default_tax_resident
        )

    @strawberry.mutation
    async def create_user(self, userInput: UserCreateInput, info: strawberry.Info) -> types.User:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")

        user_data = schemas.UserCreate(
            email=userInput.email,
            username=userInput.username,
            password=userInput.password,
            first_name=userInput.first_name,
            last_name=userInput.last_name,
            phone_number=userInput.phone_number,
            address=userInput.address,
            egn=userInput.egn,
            birth_date=userInput.birth_date,
            iban=userInput.iban,
            company_id=userInput.company_id,
            department_id=userInput.department_id,
            position_id=userInput.position_id,
            password_force_change=userInput.password_force_change,
            contract_type=userInput.contract_type,
            contract_start_date=userInput.contract_start_date,
            contract_end_date=userInput.contract_end_date,
            base_salary=userInput.base_salary,
            work_hours_per_week=userInput.work_hours_per_week,
            probation_months=userInput.probation_months,
            salary_calculation_type=userInput.salary_calculation_type,
            salary_installments_count=userInput.salary_installments_count,
            monthly_advance_amount=userInput.monthly_advance_amount,
            tax_resident=userInput.tax_resident,
            insurance_contributor=userInput.insurance_contributor,
            has_income_tax=userInput.has_income_tax,
        )

        db_user = await crud.create_user(db=db, user=user_data, role_id=userInput.role_id)
        return types.User.from_instance(db_user)

    @strawberry.mutation
    async def update_user(self, userInput: UpdateUserInput, info: strawberry.Info) -> types.User:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

        if current_user.id != userInput.id and current_user.role.name not in ["admin", "super_admin"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")

        update_data = schemas.UserUpdate(
            email=userInput.email,
            username=userInput.username,
            password=userInput.password,
            first_name=userInput.first_name,
            last_name=userInput.last_name,
            phone_number=userInput.phone_number,
            address=userInput.address,
            egn=userInput.egn,
            birth_date=userInput.birth_date,
            iban=userInput.iban,
            is_active=userInput.is_active,
            role_id=userInput.role_id,
            password_force_change=userInput.password_force_change,
            company_id=userInput.company_id,
            department_id=userInput.department_id,
            position_id=userInput.position_id,
            base_salary=userInput.base_salary,  # Passed for payroll linkage
        )
        db_user = await crud.update_user(db, user_id=userInput.id, user_in=update_data)
        return types.User.from_instance(db_user)

    @strawberry.mutation
    async def delete_user(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")
        return await crud.delete_user(db, id)

    @strawberry.mutation
    async def create_company(self, input: CompanyCreateInput, info: strawberry.Info) -> types.Company:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name != "super_admin":
            raise HTTPException(status_code=403, detail="Operation not permitted")

        company = await crud.create_company(
            db,
            name=input.name,
            eik=input.eik,
            bulstat=input.bulstat,
            vat_number=input.vat_number,
            address=input.address,
            mol_name=input.mol_name
        )
        return types.Company.from_instance(company)

    @strawberry.mutation
    async def update_company(self, input: CompanyUpdateInput, info: strawberry.Info) -> types.Company:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name != "super_admin":
            raise HTTPException(status_code=403, detail="Operation not permitted")

        company = await crud.update_company(
            db,
            company_id=input.id,
            name=input.name,
            eik=input.eik,
            bulstat=input.bulstat,
            vat_number=input.vat_number,
            address=input.address,
            mol_name=input.mol_name
        )
        return types.Company.from_instance(company)

    @strawberry.mutation
    async def create_department(self, input: DepartmentCreateInput, info: strawberry.Info) -> types.Department:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Operation not permitted")

        dept = await crud.create_department(db, name=input.name, company_id=input.company_id,
                                            manager_id=input.manager_id)
        return types.Department.from_instance(dept)

    @strawberry.mutation
    async def update_department(self, input: DepartmentUpdateInput, info: strawberry.Info) -> types.Department:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Operation not permitted")

        dept = await crud.update_department(db, department_id=input.id, name=input.name, manager_id=input.manager_id)
        return types.Department.from_instance(dept)

    @strawberry.mutation
    async def create_position(self, title: str, department_id: int, info: strawberry.Info) -> types.Position:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")

        pos = await crud.create_position(db, title, department_id)
        return types.Position.from_instance(pos)

    @strawberry.mutation
    async def update_position(self, id: int, title: str, department_id: int, info: strawberry.Info) -> types.Position:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")

        pos = await crud.update_position(db, id, title, department_id)
        return types.Position.from_instance(pos)

    @strawberry.mutation
    async def delete_position(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")
        return await crud.delete_position(db, id)

    @strawberry.mutation
    async def create_shift(self, name: str, start_time: datetime.time, end_time: datetime.time,
                           info: strawberry.Info) -> types.Shift:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")

        s = await crud.create_shift(db, name, start_time, end_time)
        return types.Shift.from_instance(s)

    @strawberry.mutation
    async def update_shift(
            self, id: int, name: str, start_time: datetime.time, end_time: datetime.time,
            tolerance_minutes: Optional[int] = None, break_duration_minutes: Optional[int] = None,
            pay_multiplier: Optional[Decimal] = None, shift_type: Optional[str] = None,
            info: strawberry.Info = None
    ) -> types.Shift:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")

        s = await crud.update_shift(
            db, id, name, start_time, end_time,
            tolerance_minutes, break_duration_minutes, pay_multiplier, shift_type
        )
        return types.Shift.from_instance(s)

    @strawberry.mutation
    async def delete_shift(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")
        return await crud.delete_shift(db, id)

    @strawberry.mutation
    async def create_role(self, input: RoleCreateInput, info: strawberry.Info) -> types.Role:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")

        role = await crud.create_role(db, schemas.RoleCreate(name=input.name, description=input.description))
        return types.Role.from_instance(role)

    @strawberry.mutation
    async def update_role(self, id: int, name: Optional[str] = None, description: Optional[str] = None,
                          info: strawberry.Info = None) -> types.Role:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")

        role = await crud.update_role(db, id, name, description)
        return types.Role.from_instance(role)

    @strawberry.mutation
    async def delete_role(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")
        return await crud.delete_role(db, id)

    @strawberry.mutation
    async def assign_role_to_user(self, user_id: int, company_id: int, role_id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")

        from backend.auth.rbac_service import PermissionService
        perm_service = PermissionService(db)
        await perm_service.assign_role_to_user(user_id, company_id, role_id, current_user.id)
        return True

    @strawberry.mutation
    async def set_global_setting(self, key: str, value: str, info: strawberry.Info) -> types.GlobalSetting:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name != "super_admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")

        setting = await crud.set_global_setting(db, key, value)
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
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")

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
        await crud.update_global_payroll_config(db, **config_data)
        await crud.set_global_setting(db, "qr_token_regen_minutes", str(qr_regen_interval_minutes))

        # Re-fetch the updated config with the new QR setting
        return await crud.get_global_payroll_config(db)

    @strawberry.mutation
    async def create_leave_request(self, input: LeaveRequestInput, info: strawberry.Info) -> types.LeaveRequest:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

        # Override user_id from input to ensure self-submission
        req_data = schemas.LeaveRequestCreate(**input.dict(), user_id=current_user.id)
        req = await crud.create_leave_request(db, req_data)
        return types.LeaveRequest.from_instance(req)

    @strawberry.mutation
    async def update_leave_request_status(self, input: UpdateLeaveRequestStatusInput,
                                          info: strawberry.Info) -> types.LeaveRequest:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")

        req = await crud.update_leave_request_status(
            db,
            input.request_id,
            input.status,
            input.admin_comment,
            admin_user_id=current_user.id,
            employer_top_up=input.employer_top_up
        )
        return types.LeaveRequest.from_instance(req)

    @strawberry.mutation
    async def delete_leave_request(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")
        return await crud.delete_leave_request(db, id)

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
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")

        await crud.set_global_setting(db, "office_latitude", str(latitude))
        await crud.set_global_setting(db, "office_longitude", str(longitude))
        await crud.set_global_setting(db, "office_radius", str(radius))
        await crud.set_global_setting(db, "geofencing_entry_enabled", str(entry_enabled))
        await crud.set_global_setting(db, "geofencing_exit_enabled", str(exit_enabled))

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
            raise HTTPException(status_code=401, detail="Not authenticated")

        # Re-fetch user from DB to access hashed_password (not present in Pydantic schema)
        from backend.database.models import User
        stmt = select(User).where(User.id == current_user.id)
        result = await db.execute(stmt)
        db_user = result.scalars().first()

        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")

        if not verify_password(old_password, db_user.hashed_password):
            raise HTTPException(status_code=400, detail="Incorrect old password")

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
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")

        # Check if the session belongs to the user trying to invalidate (if not admin)
        session_to_invalidate = await crud.get_user_session_by_id(db, sessionId)
        if not session_to_invalidate:
            raise HTTPException(status_code=404, detail="Session not found")

        if session_to_invalidate.user_id != current_user.id and current_user.role.name not in ["admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Not authorized to invalidate this session")

        return await crud.invalidate_user_session(db, session_to_invalidate.refresh_token_jti)

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
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")

        await crud.set_global_setting(db, "max_login_attempts", str(max_login_attempts))
        await crud.set_global_setting(db, "lockout_minutes", str(lockout_minutes))
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
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")

        await crud.set_global_setting(db, "kiosk_require_gps", "true" if require_gps else "false")
        await crud.set_global_setting(db, "kiosk_require_same_network", "true" if require_same_network else "false")
        await db.commit()
        return True

    @strawberry.mutation
    async def disconnect_google_calendar(self, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

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
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

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
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

        await verify_module_enabled("salaries", db)

        calculator = crud.PayrollCalculator(db)
        res = await calculator.calculate(current_user.id, start_date, end_date)

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
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")

        await verify_module_enabled("salaries", db)

        calculator = crud.PayrollCalculator(db)
        res = await calculator.calculate(user_id, start_date, end_date)

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
            info: strawberry.Info = None
    ) -> types.TimeLog:
        db = info.context["db"]
        current_user = info.context["current_user"]

        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")

        log = await crud.create_time_log(
            db, user_id, start_time, end_time, is_manual, break_duration_minutes, notes
        )
        return types.TimeLog.from_instance(log)

    @strawberry.mutation
    async def update_time_log(
            self, id: int, start_time: datetime.datetime, end_time: Optional[datetime.datetime] = None,
            is_manual: bool = False, break_duration_minutes: int = 0, notes: Optional[str] = None,
            info: strawberry.Info = None
    ) -> types.TimeLog:
        db = info.context["db"]
        current_user = info.context["current_user"]

        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")

        log = await crud.update_time_log(
            db, id, start_time, end_time, is_manual, break_duration_minutes, notes
        )
        return types.TimeLog.from_instance(log)

    @strawberry.mutation
    async def delete_time_log(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")
        return await crud.delete_time_log(db, id)

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
            raise Exception("Not authenticated")

        await verify_module_enabled("shifts", db)

        # Check for active log
        active_log = await crud.get_active_time_log(db, current_user.id)
        if active_log:
            raise Exception("User already has an active time log")

        log = await crud.start_time_log(db, current_user.id)
        await db.commit()
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
            raise Exception("Not authenticated")

        await verify_module_enabled("shifts", db)

        active_log = await crud.get_active_time_log(db, current_user.id)
        if not active_log:
            raise Exception("No active time log found")

        log = await crud.end_time_log(db, current_user.id, notes=notes)
        await db.commit()
        return types.TimeLog.from_instance(log)

    @strawberry.mutation
    async def admin_clock_in(
            self,
            user_id: int,
            info: strawberry.Info,
            custom_time: Optional[datetime.datetime] = None
    ) -> types.TimeLog:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")

        await verify_module_enabled("shifts", db)

        active_log = await crud.get_active_time_log(db, user_id)
        if active_log:
            raise Exception("User already has an active time log")

        log = await crud.start_time_log(db, user_id, custom_time=custom_time)
        return types.TimeLog.from_instance(log)

    @strawberry.mutation
    async def admin_clock_out(
            self,
            user_id: int,
            info: strawberry.Info,
            notes: Optional[str] = None,
            custom_time: Optional[datetime.datetime] = None
    ) -> types.TimeLog:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")

        await verify_module_enabled("shifts", db)

        active_log = await crud.get_active_time_log(db, user_id)
        if not active_log:
            raise Exception("No active time log found")

        log = await crud.end_time_log(db, user_id, notes=notes, end_time=custom_time)
        return types.TimeLog.from_instance(log)

    @strawberry.mutation
    async def create_schedule_template(self, name: str, description: Optional[str],
                                       items: List[inputs.ScheduleTemplateItemInput],
                                       info: strawberry.Info) -> types.ScheduleTemplate:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")

        await verify_module_enabled("shifts", db)

        template = await crud.create_schedule_template(db, name, description, items)
        return types.ScheduleTemplate.from_instance(template)

    @strawberry.mutation
    async def delete_schedule_template(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")

        await verify_module_enabled("shifts", db)
        return await crud.delete_schedule_template(db, id)

    @strawberry.mutation
    async def apply_schedule_template(
            self,
            template_id: int,
            user_ids: List[int],
            start_date: datetime.date,
            info: strawberry.Info
    ) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")

        await verify_module_enabled("shifts", db)

        await crud.apply_schedule_template(db, template_id, user_ids, start_date)
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
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")

        await crud.set_global_setting(db, "pwd_min_length", str(settings.min_length))
        await crud.set_global_setting(db, "pwd_max_length", str(settings.max_length))
        await crud.set_global_setting(db, "pwd_require_upper", "true" if settings.require_upper else "false")
        await crud.set_global_setting(db, "pwd_require_lower", "true" if settings.require_lower else "false")
        await crud.set_global_setting(db, "pwd_require_digit", "true" if settings.require_digit else "false")
        await crud.set_global_setting(db, "pwd_require_special", "true" if settings.require_special else "false")

        # Increment password settings version
        current_version = int(await crud.get_global_setting(db, "password_settings_version") or "0")
        await crud.set_global_setting(db, "password_settings_version", str(current_version + 1))

        # Set password_force_change to True for all users
        await crud.force_password_change_for_all_users(db)

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
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")

        return await fetch_and_store_holidays(db, year)

    @strawberry.mutation
    async def sync_orthodox_holidays(self, year: int, info: strawberry.Info) -> int:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")

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
            raise Exception(f"Failed to sync holidays: {str(e)}")

    @strawberry.mutation
    async def add_bonus(self, input: BonusCreateInput, info: strawberry.Info) -> types.Bonus:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")

        bonus = await crud.create_bonus(
            db,
            user_id=input.user_id,
            amount=input.amount,
            date=input.date,
            description=input.description
        )
        await db.commit()
        return types.Bonus.from_instance(bonus)

    @strawberry.mutation
    async def remove_bonus(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")

        await crud.delete_bonus(db, id)
        await db.commit()
        return True

    @strawberry.mutation
    async def regenerate_my_qr_code(self, info: strawberry.Info) -> str:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

        return await crud.regenerate_user_qr_token(db, current_user.id)

    @strawberry.mutation
    async def create_advance_payment(
            self,
            user_id: int,
            amount: float,
            payment_date: datetime.date,
            description: Optional[str] = None,
            info: strawberry.Info = None
    ) -> types.AdvancePayment:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")

        advance = await crud.create_advance_payment(
            db, user_id=user_id, amount=amount, payment_date=payment_date, description=description
        )
        return types.AdvancePayment.from_instance(advance)

    @strawberry.mutation
    async def create_service_loan(
            self,
            user_id: int,
            total_amount: float,
            installments_count: int,
            start_date: datetime.date,
            description: Optional[str] = None,
            info: strawberry.Info = None
    ) -> types.ServiceLoan:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")

        loan = await crud.create_service_loan(
            db, user_id=user_id, total_amount=total_amount, installments_count=installments_count,
            start_date=start_date, description=description
        )
        return types.ServiceLoan.from_instance(loan)

    @strawberry.mutation
    async def set_monthly_work_days(self, input: MonthlyWorkDaysInput, info: strawberry.Info) -> types.MonthlyWorkDays:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")

        res = await crud.set_monthly_work_days(db, input.year, input.month, input.days_count)
        return types.MonthlyWorkDays.from_instance(res)

    @strawberry.mutation
    async def create_manual_time_log(
            self,
            user_id: int,
            start_time: datetime.datetime,
            end_time: datetime.datetime,
            break_duration_minutes: int = 0,
            notes: Optional[str] = None,
            info: strawberry.Info = None
    ) -> types.TimeLog:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")

        log = await crud.create_manual_time_log(
            db, user_id, start_time, end_time, break_duration_minutes, notes
        )
        return types.TimeLog.from_instance(log)

    @strawberry.mutation
    async def delete_work_schedule(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")

        return await crud.delete_schedule(db, id)

    @strawberry.mutation
    async def set_work_schedule(self, user_id: int, shift_id: int, date: datetime.date,
                                info: strawberry.Info) -> types.WorkSchedule:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")

        res = await crud.create_or_update_schedule(db, user_id, shift_id, date)
        return types.WorkSchedule.from_instance(res)

    @strawberry.mutation
    async def bulk_set_schedule(self, user_ids: List[int], shift_id: int, start_date: datetime.date,
                                end_date: datetime.date, days_of_week: List[int], info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")

        return await crud.create_bulk_schedules(db, user_ids, shift_id, start_date, end_date, days_of_week)

    @strawberry.mutation
    async def respond_to_swap(self, swap_id: int, accept: bool, info: strawberry.Info) -> types.ShiftSwapRequest:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

        new_status = "accepted" if accept else "rejected"
        res = await crud.update_swap_status(db, swap_id, new_status)
        return types.ShiftSwapRequest.from_instance(res)

    @strawberry.mutation
    async def approve_swap(self, swap_id: int, approve: bool, info: strawberry.Info) -> types.ShiftSwapRequest:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")

        new_status = "approved" if approve else "rejected"
        res = await crud.update_swap_status(db, swap_id, new_status, admin_user_id=current_user.id)
        return types.ShiftSwapRequest.from_instance(res)

    @strawberry.mutation
    async def create_swap_request(self, requestor_schedule_id: int, target_user_id: int, target_schedule_id: int,
                                  info: strawberry.Info) -> types.ShiftSwapRequest:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

        res = await crud.create_swap_request(db, current_user.id, requestor_schedule_id, target_user_id,
                                             target_schedule_id)
        return types.ShiftSwapRequest.from_instance(res)

    # --- Confectionery Module Mutations ---

    @strawberry.mutation
    async def create_storage_zone(self, input: inputs.StorageZoneInput, info: strawberry.Info) -> types.StorageZone:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Not authorized")

        target_company_id = input.company_id if current_user.role.name == "super_admin" else current_user.company_id
        if not target_company_id:
            raise HTTPException(status_code=400, detail="Company ID is required")

        # Validate company exists
        from backend.database.models import Company
        stmt = select(Company).where(Company.id == target_company_id)
        res = await db.execute(stmt)
        if not res.scalar_one_or_none():
            raise HTTPException(status_code=400,
                                detail=f"Фирма с ID {target_company_id} не съществува. Моля, първо създайте фирма.")

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
            raise HTTPException(status_code=403, detail="Not authorized")

        from backend.database.models import StorageZone
        from sqlalchemy import select
        stmt = select(StorageZone).where(StorageZone.id == input.id)
        res = await db.execute(stmt)
        zone = res.scalar_one_or_none()
        if not zone:
            raise HTTPException(status_code=404, detail="Зоната не е намерена")

        if current_user.role.name not in ["super_admin"] and zone.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="Нямате достъп до тази зона")

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
    async def create_supplier(self, input: inputs.SupplierInput, info: strawberry.Info) -> types.Supplier:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin", "Warehouse_Manager"]:
            raise HTTPException(status_code=403, detail="Not authorized")

        target_company_id = input.company_id if current_user.role.name == "super_admin" else current_user.company_id
        if not target_company_id:
            raise HTTPException(status_code=400, detail="Company ID is required")

        # Validate company exists
        from backend.database.models import Company
        stmt = select(Company).where(Company.id == target_company_id)
        res = await db.execute(stmt)
        if not res.scalar_one_or_none():
            raise HTTPException(status_code=400,
                                detail=f"Фирма с ID {target_company_id} не съществува. Моля, първо създайте фирма.")

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
            raise HTTPException(status_code=403, detail="Not authorized")

        from backend.database.models import Supplier
        from sqlalchemy import select
        stmt = select(Supplier).where(Supplier.id == input.id)
        res = await db.execute(stmt)
        supplier = res.scalar_one_or_none()
        if not supplier:
            raise HTTPException(status_code=404, detail="Доставчикът не е намерен")

        if current_user.role.name not in ["super_admin"] and supplier.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="Нямате достъп до този доставчик")

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
            raise HTTPException(status_code=403, detail="Not authorized")

        target_company_id = input.company_id if current_user.role.name == "super_admin" else current_user.company_id
        if not target_company_id:
            raise HTTPException(status_code=400, detail="Company ID is required")

        # Validate company exists
        from backend.database.models import Company
        stmt = select(Company).where(Company.id == target_company_id)
        res = await db.execute(stmt)
        if not res.scalar_one_or_none():
            raise HTTPException(status_code=400, detail=f"Фирма с ID {target_company_id} не съществува.")

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
            raise HTTPException(status_code=403, detail="Not authorized")

        from backend.database.models import Ingredient
        ingredient = await db.get(Ingredient, input.id)
        if not ingredient:
            raise HTTPException(status_code=404, detail="Ingredient not found")

        if current_user.role.name != "super_admin" and ingredient.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="Not authorized")

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
            raise HTTPException(status_code=403, detail="Not authorized")

        from backend.database.models import Batch, Ingredient
        # Verify ingredient belongs to company
        res = await db.get(Ingredient, input.ingredient_id)
        if not res or (current_user.role.name != "super_admin" and res.company_id != current_user.company_id):
            raise HTTPException(status_code=403, detail="Not authorized for this ingredient")

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
            raise HTTPException(status_code=403, detail="Not authorized")

        from backend.database.models import Batch, Ingredient
        batch = await db.get(Batch, id)
        if not batch: raise HTTPException(status_code=404, detail="Batch not found")

        ingredient = await db.get(Ingredient, batch.ingredient_id)
        if current_user.role.name != "super_admin" and ingredient.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        batch.status = status
        await db.commit()
        await db.refresh(batch)
        return types.Batch.from_instance(batch)

    @strawberry.mutation
    async def update_batch(self, input: inputs.BatchInput, info: strawberry.Info) -> types.Batch:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin", "Warehouse_Manager"]:
            raise HTTPException(status_code=403, detail="Not authorized")

        from backend.database.models import Batch, Ingredient
        batch = await db.get(Batch, input.id)
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")

        ingredient = await db.get(Ingredient, batch.ingredient_id)
        if current_user.role.name != "super_admin" and ingredient.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="Not authorized")

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
    async def create_recipe(self, input: inputs.RecipeInput, info: strawberry.Info) -> types.Recipe:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Not authorized")

        target_company_id = input.company_id if current_user.role.name == "super_admin" else current_user.company_id
        if not target_company_id:
            raise HTTPException(status_code=400, detail="Company ID is required")

        # Validate company exists
        from backend.database.models import Company
        stmt = select(Company).where(Company.id == target_company_id)
        res = await db.execute(stmt)
        if not res.scalar_one_or_none():
            raise HTTPException(status_code=400, detail=f"Фирма с ID {target_company_id} не съществува.")

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
    async def create_workstation(self, name: str, description: Optional[str], company_id: int,
                                 info: strawberry.Info) -> types.Workstation:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Not authorized")

        target_company_id = company_id if current_user.role.name == "super_admin" else current_user.company_id
        if not target_company_id:
            raise HTTPException(status_code=400, detail="Company ID is required")

        # Validate company exists
        from backend.database.models import Company
        stmt = select(Company).where(Company.id == target_company_id)
        res = await db.execute(stmt)
        if not res.scalar_one_or_none():
            raise HTTPException(status_code=400, detail=f"Фирма с ID {target_company_id} не съществува.")

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
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise HTTPException(status_code=401, detail="Not authenticated")

        target_company_id = input.company_id if current_user.role.name == "super_admin" else current_user.company_id
        if not target_company_id:
            raise HTTPException(status_code=400, detail="Company ID is required")

        # Validate company exists
        from backend.database.models import Company
        stmt = select(Company).where(Company.id == target_company_id)
        res = await db.execute(stmt)
        if not res.scalar_one_or_none():
            raise HTTPException(status_code=400, detail=f"Фирма с ID {target_company_id} не съществува.")

        from backend.database.models import ProductionOrder, Recipe, ProductionTask, Batch, sofia_now
        from datetime import timedelta

        # Calculate production_deadline
        production_deadline = None
        recipe = await db.get(Recipe, input.recipe_id)
        if recipe and recipe.production_deadline_days and recipe.shelf_life_days:
            # production_deadline = due_date - production_deadline_days
            production_deadline = input.due_date - timedelta(days=recipe.production_deadline_days)

        # 1. Create Order
        order = ProductionOrder(
            recipe_id=input.recipe_id,
            quantity=input.quantity,
            due_date=input.due_date,
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
            res = await db.execute(stmt)
            available = sum((b.quantity for b in res.scalars().all()), Decimal("0"))
            if available < required:
                all_available = False
                break

        if all_available:
            order.status = "ready"

        db.add(order)
        await db.flush()

        # 3. Create initial tasks from recipe steps
        for step in recipe.steps:
            task = ProductionTask(
                order_id=order.id,
                workstation_id=step.workstation_id,
                step_id=step.id,
                name=step.name,
                status="pending"
            )
            db.add(task)

        await db.commit()
        await db.refresh(order)
        return types.ProductionOrder.from_instance(order)

    @strawberry.mutation
    async def update_production_order_status(self, id: int, status: str,
                                             info: strawberry.Info) -> types.ProductionOrder:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise HTTPException(status_code=401, detail="Not authenticated")

        from backend.database.models import ProductionOrder
        order = await db.get(ProductionOrder, id)
        if not order: raise HTTPException(status_code=404, detail="Order not found")

        if current_user.role.name != "super_admin" and order.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        order.status = status
        await db.commit()
        await db.refresh(order)
        return types.ProductionOrder.from_instance(order)

    @strawberry.mutation
    async def confirm_production_order(self, id: int, info: strawberry.Info) -> types.ProductionOrder:
        """Department head confirms order is ready for transport"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise HTTPException(status_code=401, detail="Not authenticated")

        from backend.database.models import (
            ProductionOrder, ProductionTask, ProductionRecord,
            ProductionRecordIngredient, ProductionRecordWorker,
            Recipe, Batch, sofia_now
        )
        from sqlalchemy import select
        from datetime import timedelta

        order = await db.get(ProductionOrder, id)
        if not order: raise HTTPException(status_code=404, detail="Order not found")

        if current_user.role.name != "super_admin" and order.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        if order.status != "ready":
            raise HTTPException(status_code=400, detail="Order must be in 'ready' status to confirm")

        # Get recipe for shelf_life_days
        recipe = await db.get(Recipe, order.recipe_id)
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
        if not current_user: raise HTTPException(status_code=401, detail="Not authenticated")

        from backend.database.models import ProductionTask, ProductionOrder, Recipe, RecipeIngredient, Batch, \
            RecipeStep, sofia_now
        from sqlalchemy import select

        task = await db.get(ProductionTask, id)
        if not task: raise HTTPException(status_code=404, detail="Task not found")

        order = await db.get(ProductionOrder, task.order_id)
        if current_user.role.name != "super_admin" and order.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        # Mark task as scrap
        task.is_scrap = True
        task.status = "completed"
        task.completed_at = sofia_now()

        # Get recipe and step to determine which ingredients to deduct
        recipe = await db.get(Recipe, order.recipe_id)

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
        if not current_user: raise HTTPException(status_code=401, detail="Not authenticated")

        from backend.database.models import ProductionTask, ProductionOrder, ProductionScrapLog, sofia_now

        task = await db.get(ProductionTask, input.task_id)
        if not task: raise HTTPException(status_code=404, detail="Task not found")

        order = await db.get(ProductionOrder, task.order_id)
        if current_user.role.name != "super_admin" and order.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        # Validate quantity
        if input.quantity <= 0:
            raise HTTPException(status_code=400, detail="Quantity must be positive")

        if input.quantity > float(order.quantity):
            raise HTTPException(status_code=400, detail="Cannot scrap more than the order quantity")

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
        if not current_user: raise HTTPException(status_code=401, detail="Not authenticated")

        from backend.database.models import ProductionScrapLog, ProductionTask, ProductionOrder
        from sqlalchemy import select

        task = await db.get(ProductionTask, task_id)
        if not task: raise HTTPException(status_code=404, detail="Task not found")

        order = await db.get(ProductionOrder, task.order_id)
        if current_user.role.name != "super_admin" and order.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        stmt = select(ProductionScrapLog).where(ProductionScrapLog.task_id == task_id).order_by(
            ProductionScrapLog.created_at.desc())
        res = await db.execute(stmt)
        return [types.ProductionScrapLog.from_instance(s) for s in res.scalars().all()]

    @strawberry.mutation
    async def update_production_task_status(self, id: int, status: str, info: strawberry.Info) -> types.ProductionTask:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise HTTPException(status_code=401, detail="Not authenticated")

        from backend.database.models import ProductionTask, ProductionOrder, sofia_now
        task = await db.get(ProductionTask, id)
        if not task: raise HTTPException(status_code=404, detail="Task not found")

        # Verify ownership
        order = await db.get(ProductionOrder, task.order_id)
        if current_user.role.name != "super_admin" and order.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="Not authorized")

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
                from backend.database.models import Recipe as RecipeModel, RecipeIngredient, Batch as BatchModel
                recipe = await db.get(RecipeModel, order.recipe_id)
                stmt_ings = select(RecipeIngredient).where(RecipeIngredient.recipe_id == recipe.id)
                recipe_ings = (await db.execute(stmt_ings)).scalars().all()

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

                        if batch.quantity >= needed:
                            batch.quantity -= needed
                            needed = 0
                        else:
                            needed -= batch.quantity
                            batch.quantity = 0
                            batch.status = "depleted"
                # ----------------------------------

        await db.commit()
        await db.refresh(task)
        return types.ProductionTask.from_instance(task)

    @strawberry.mutation
    async def start_inventory_session(self, info: strawberry.Info) -> types.InventorySession:
        """Start a new inventory session"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise HTTPException(status_code=401, detail="Not authenticated")

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
        if not current_user: raise HTTPException(status_code=401, detail="Not authenticated")

        from backend.database.models import InventorySession, InventoryItem, Ingredient, Batch
        from sqlalchemy import func, select

        # Verify session exists and belongs to company
        session = await db.get(InventorySession, session_id)
        if not session: raise HTTPException(status_code=404, detail="Session not found")
        if session.company_id != current_user.company_id and current_user.role.name != "super_admin":
            raise HTTPException(status_code=403, detail="Not authorized")
        if session.status != "active":
            raise HTTPException(status_code=400, detail="Session is not active")

        # Get ingredient
        ingredient = await db.get(Ingredient, ingredient_id)
        if not ingredient: raise HTTPException(status_code=404, detail="Ingredient not found")

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
        if not current_user: raise HTTPException(status_code=401, detail="Not authenticated")

        from backend.database.models import InventorySession, InventoryItem, Batch, sofia_now
        from sqlalchemy import select
        import uuid

        # Verify session
        session = await db.get(InventorySession, session_id)
        if not session: raise HTTPException(status_code=404, detail="Session not found")
        if session.company_id != current_user.company_id and current_user.role.name != "super_admin":
            raise HTTPException(status_code=403, detail="Not authorized")
        if session.status != "active":
            raise HTTPException(status_code=400, detail="Session is not active")

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
            raise HTTPException(status_code=401, detail="Not authenticated")

        from backend.database import models
        from decimal import Decimal

        # Generate invoice number
        year = invoice_data.date.year
        prefix = "ВХ" if invoice_data.type == "incoming" else "ИЗХ"

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

        db.add(invoice)
        await db.flush()

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
                discount_percent=item.discount_percent,
                total=item_total
            )
            db.add(invoice_item)

        await db.commit()

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
            raise HTTPException(status_code=401, detail="Not authenticated")

        from backend.database import models
        from decimal import Decimal

        invoice = await db.get(models.Invoice, id)
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")

        if current_user.role.name != "super_admin" and invoice.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="Not authorized")

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
                discount_percent=item.discount_percent,
                total=item_total
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

        await db.commit()
        await db.refresh(invoice)
        return types.Invoice.from_instance(invoice)

    @strawberry.mutation
    async def delete_invoice(
            self,
            id: int,
            info: strawberry.Info
    ) -> bool:
        """Delete an invoice"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise HTTPException(status_code=401, detail="Not authenticated")

        from backend.database import models

        invoice = await db.get(models.Invoice, id)
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")

        if current_user.role.name != "super_admin" and invoice.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        # Log the deletion before deleting
        log_entry = models.OperationLog(
            operation="delete",
            entity_type="invoice",
            entity_id=invoice.id,
            user_id=current_user.id,
            changes={"number": invoice.number, "type": invoice.type, "total": str(invoice.total)}
        )
        db.add(log_entry)

        await db.delete(invoice)
        await db.commit()
        return True

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
            raise HTTPException(status_code=401, detail="Not authenticated")

        from backend.database import models
        from decimal import Decimal

        batch = await db.get(models.Batch, batch_id)
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")

        if current_user.role.name != "super_admin" and batch.ingredient.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="Not authorized")

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
            discount_percent=Decimal("0"),
            total=subtotal
        )
        db.add(invoice_item)

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
            raise HTTPException(status_code=401, detail="Not authenticated")

        from backend.database import models
        from decimal import Decimal

        batches = []
        invoice_items_data = []
        total_subtotal = Decimal("0")

        # 1. Create Batches
        for item_input in items:
            ingredient = await db.get(models.Ingredient, item_input.ingredient_id)
            if not ingredient:
                continue

            new_batch = models.Batch(
                ingredient_id=item_input.ingredient_id,
                batch_number=item_input.batch_number,
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
                    "total": item_total
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
                    total=item_data["total"]
                )
                db.add(inv_item)

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
            raise HTTPException(status_code=401, detail="Not authenticated")

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
            raise HTTPException(status_code=401, detail="Not authenticated")

        from backend.database import models

        entry = await db.get(models.CashJournalEntry, id)
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found")

        if current_user.role.name != "super_admin" and entry.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="Not authorized")

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
            raise HTTPException(status_code=401, detail="Not authenticated")

        from backend.database import models
        import datetime
        from decimal import Decimal

        target_date = datetime.date.fromisoformat(date)

        if current_user.role.name != "super_admin":
            company_id = current_user.company_id
        else:
            company_id = 1

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
            raise HTTPException(status_code=401, detail="Not authenticated")

        from backend.database import models
        import datetime
        from decimal import Decimal
        from sqlalchemy import func

        if current_user.role.name != "super_admin":
            company_id = current_user.company_id
        else:
            company_id = 1

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
            raise HTTPException(status_code=401, detail="Not authenticated")

        from backend.database import models
        import datetime
        from decimal import Decimal

        if current_user.role.name != "super_admin":
            company_id = current_user.company_id
        else:
            company_id = 1

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
            raise HTTPException(status_code=401, detail="Not authenticated")

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
            raise HTTPException(
                status_code=500,
                detail=f"Error generating SAF-T file: {str(e)}"
            )

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
            raise HTTPException(status_code=401, detail="Not authenticated")

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
                discount_percent=item.discount_percent or Decimal("0"),
                total=item_total
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
            raise HTTPException(status_code=401, detail="Not authenticated")

        from backend.database import models

        proforma = await db.get(models.Invoice, proforma_id)
        if not proforma or proforma.type != "proforma":
            raise HTTPException(status_code=404, detail="Proforma invoice not found")

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
                discount_percent=item.discount_percent,
                total=item.total
            )
            db.add(new_item)

        # Mark proforma as converted
        proforma.status = "converted"

        await db.commit()
        await db.refresh(invoice)
        return types.Invoice.from_instance(invoice)

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
            raise HTTPException(status_code=401, detail="Not authenticated")

        from backend.database import models

        original_invoice = await db.get(models.Invoice, original_invoice_id)
        if not original_invoice:
            raise HTTPException(status_code=404, detail="Original invoice not found")

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
        await db.refresh(correction)
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
            raise HTTPException(status_code=401, detail="Not authenticated")

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
            raise HTTPException(status_code=401, detail="Not authenticated")

        from backend.database import models

        receipt = await db.get(models.CashReceipt, id)
        if not receipt:
            raise HTTPException(status_code=404, detail="Cash receipt not found")

        if receipt.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="Not authorized")

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
            raise HTTPException(status_code=401, detail="Not authenticated")

        from backend.database import models

        receipt = await db.get(models.CashReceipt, id)
        if not receipt:
            raise HTTPException(status_code=404, detail="Cash receipt not found")

        if receipt.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="Not authorized")

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
            raise HTTPException(status_code=401, detail="Not authenticated")

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
            raise HTTPException(status_code=401, detail="Not authenticated")

        from backend.database import models

        account = await db.get(models.BankAccount, id)
        if not account:
            raise HTTPException(status_code=404, detail="Bank account not found")

        if account.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="Not authorized")

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
            raise HTTPException(status_code=401, detail="Not authenticated")

        from backend.database import models

        account = await db.get(models.BankAccount, id)
        if not account:
            raise HTTPException(status_code=404, detail="Bank account not found")

        if account.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="Not authorized")

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
            raise HTTPException(status_code=401, detail="Not authenticated")

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
            raise HTTPException(status_code=401, detail="Not authenticated")

        from backend.database import models

        transaction = await db.get(models.BankTransaction, id)
        if not transaction:
            raise HTTPException(status_code=404, detail="Bank transaction not found")

        if transaction.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="Not authorized")

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
            raise HTTPException(status_code=401, detail="Not authenticated")

        from backend.database import models

        transaction = await db.get(models.BankTransaction, id)
        if not transaction:
            raise HTTPException(status_code=404, detail="Bank transaction not found")

        if transaction.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="Not authorized")

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
            raise HTTPException(status_code=401, detail="Not authenticated")

        from backend.database import models

        transaction = await db.get(models.BankTransaction, transaction_id)
        if not transaction:
            raise HTTPException(status_code=404, detail="Bank transaction not found")

        invoice = await db.get(models.Invoice, invoice_id)
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")

        if transaction.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        transaction.invoice_id = invoice_id
        transaction.matched = True

        await db.commit()
        await db.refresh(transaction)
        return types.BankTransaction.from_instance(transaction)

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
            raise HTTPException(status_code=401, detail="Not authenticated")

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
            raise HTTPException(status_code=401, detail="Not authenticated")

        from backend.database import models

        account = await db.get(models.Account, id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")

        if account.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="Not authorized")

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
            raise HTTPException(status_code=401, detail="Not authenticated")

        from backend.database import models

        account = await db.get(models.Account, id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")

        if account.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="Not authorized")

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
            raise HTTPException(status_code=401, detail="Not authenticated")

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
            raise HTTPException(status_code=401, detail="Not authenticated")

        from backend.database import models

        entry = await db.get(models.AccountingEntry, id)
        if not entry:
            raise HTTPException(status_code=404, detail="Accounting entry not found")

        if entry.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="Not authorized")

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
            raise HTTPException(status_code=401, detail="Not authenticated")

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
        if not current_user: raise HTTPException(status_code=401, detail="Not authenticated")

        from backend.database.models import ProductionTask, ProductionOrder

        task = await db.get(ProductionTask, task_id)
        if not task: raise HTTPException(status_code=404, detail="Task not found")

        order = await db.get(ProductionOrder, task.order_id)
        if current_user.role.name != "super_admin" and order.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="Not authorized")

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
        if not current_user: raise HTTPException(status_code=401, detail="Not authenticated")

        from backend.database.models import ProductionOrder, Recipe, sofia_now
        from datetime import timedelta

        order = await db.get(ProductionOrder, order_id)
        if not order: raise HTTPException(status_code=404, detail="Order not found")

        if current_user.role.name != "super_admin" and order.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        recipe = await db.get(Recipe, order.recipe_id)
        if recipe and recipe.production_deadline_days and order.due_date:
            order.production_deadline = order.due_date - timedelta(days=recipe.production_deadline_days)

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
        if not current_user: raise HTTPException(status_code=401, detail="Not authenticated")

        from backend.database.models import ProductionOrder
        from decimal import Decimal

        order = await db.get(ProductionOrder, order_id)
        if not order: raise HTTPException(status_code=404, detail="Order not found")

        if current_user.role.name != "super_admin" and order.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        if quantity <= 0:
            raise HTTPException(status_code=400, detail="Quantity must be positive")

        order.quantity = Decimal(str(quantity))
        await db.commit()
        await db.refresh(order)
        return types.ProductionOrder.from_instance(order)