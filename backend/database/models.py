import datetime
import enum
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from zoneinfo import ZoneInfo
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Time,
    Date,
    ForeignKey,
    Numeric,
    JSON,
    Float,
    Text,
    LargeBinary,
    Table
)
from sqlalchemy.orm import relationship, declarative_base

try:
    from backend.config import settings
except ImportError:
    from config import settings

Base = declarative_base()

def sofia_now():
    return datetime.datetime.now(ZoneInfo(settings.TIMEZONE)).replace(tzinfo=None)

# Association table for User <-> AccessZone permissions
user_access_zones = Table(
    "user_access_zones",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("zone_id", Integer, ForeignKey("access_zones.id", ondelete="CASCADE"), primary_key=True),
)

class ShiftType(str, enum.Enum):
    REGULAR = "regular"
    SICK_LEAVE = "sick_leave"
    PAID_LEAVE = "paid_leave"
    UNPAID_LEAVE = "unpaid_leave"
    DAY_OFF = "day_off"

class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)
    
    # RBAC enhancements
    is_system_role = Column(Boolean, default=False)  # System vs user-defined roles
    priority = Column(Integer, default=0)  # Role hierarchy priority
    created_at = Column(DateTime, default=sofia_now)
    updated_at = Column(DateTime, nullable=True)

    users = relationship("User", back_populates="role")
    role_permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")
    company_assignments = relationship("CompanyRoleAssignment", back_populates="role", cascade="all, delete-orphan")


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)  # "users:read", "payroll:create"
    resource = Column(String(50), nullable=False, index=True)  # "users", "payroll", "schedules"
    action = Column(String(50), nullable=False, index=True)  # "read", "create", "update", "delete"
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=sofia_now)
    
    # Ensure unique resource-action combinations
    __table_args__ = (
        {"schema": None},
    )
    
    role_permissions = relationship("RolePermission", back_populates="permission", cascade="all, delete-orphan")


class RolePermission(Base):
    __tablename__ = "role_permissions"

    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    permission_id = Column(Integer, ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False)
    granted_at = Column(DateTime, default=sofia_now)
    granted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    role = relationship("Role", back_populates="role_permissions")
    permission = relationship("Permission", back_populates="role_permissions")
    granted_by_user = relationship("User", foreign_keys=[granted_by])


class CompanyRoleAssignment(Base):
    __tablename__ = "company_role_assignments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    assigned_at = Column(DateTime, default=sofia_now)
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)  # For temporary role assignments
    
    user = relationship("User", foreign_keys=[user_id])
    company = relationship("Company", foreign_keys=[company_id])
    role = relationship("Role", back_populates="company_assignments")
    assigned_by_user = relationship("User", foreign_keys=[assigned_by])


class UserPermissionCache(Base):
    __tablename__ = "user_permission_cache"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True)
    permission_name = Column(String(100), nullable=False)
    granted_at = Column(DateTime, default=sofia_now)
    expires_at = Column(DateTime, nullable=False)
    
    user = relationship("User")
    company = relationship("Company")


class PermissionAuditLog(Base):
    __tablename__ = "permission_audit_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(50), nullable=False)  # "GRANTED", "DENIED", "CHECKED"
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(Integer, nullable=True)
    permission = Column(String(100), nullable=False)
    decision = Column(String(20), nullable=False)  # 'GRANTED' or 'DENIED'
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(String, nullable=True)
    created_at = Column(DateTime, default=sofia_now)
    
    user = relationship("User")


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    eik = Column(String, unique=True, nullable=True) # ЕИК
    bulstat = Column(String, unique=True, nullable=True) # БУЛСТАТ
    vat_number = Column(String, unique=True, nullable=True) # ДДС номер
    address = Column(String, nullable=True) # Седалище и адрес на управление
    mol_name = Column(String, nullable=True) # МОЛ

    users = relationship("User", back_populates="company_rel")
    departments = relationship("Department", back_populates="company")


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    manager_id = Column(Integer, ForeignKey("users.id", name="fk_department_manager", use_alter=True), nullable=True) # Началник отдел
    
    company = relationship("Company", back_populates="departments")
    manager = relationship("User", foreign_keys=[manager_id])
    users = relationship("User", back_populates="department_rel", foreign_keys="[User.department_id]")
    positions = relationship("Position", back_populates="department")


class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    
    department = relationship("Department", back_populates="positions")
    users = relationship("User", back_populates="position_rel")
    payrolls = relationship("Payroll", back_populates="position", cascade="all, delete-orphan")


class KioskDevice(Base):
    __tablename__ = "kiosk_devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    device_uid = Column(String(100), unique=True, index=True, nullable=False) # Serial or Hardware ID
    beacon_uuid = Column(String(100), unique=True, nullable=True) # For BLE proximity
    secret_key = Column(String(255), nullable=False)
    ip_address = Column(String(50), nullable=True) # Authorized IP
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True)
    last_heartbeat = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=sofia_now)


class Gateway(Base):
    """Gateway устройство - инсталирано на Windows машина в локалната мрежа"""
    __tablename__ = "gateways"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)  # GATEWAY-001
    
    hardware_uuid = Column(String(64), unique=True, nullable=False)  # Hardware-bound UUID
    
    alias = Column(String(100), nullable=True)  # User-defined alias
    
    api_key = Column(String(64), unique=True, nullable=True)  # API key for authentication
    
    ip_address = Column(String(50), nullable=True)
    local_hostname = Column(String(100), nullable=True)
    
    terminal_port = Column(Integer, default=8080)
    web_port = Column(Integer, default=8888)
    
    is_active = Column(Boolean, default=True)
    system_mode = Column(String(30), default="normal") # normal, emergency_unlock, lockdown
    last_heartbeat = Column(DateTime, nullable=True)
    registered_at = Column(DateTime, default=sofia_now)
    
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    
    terminals = relationship("Terminal", back_populates="gateway")
    printers = relationship("Printer", back_populates="gateway")


class Terminal(Base):
    """Терминал - таблет/киоск свързан към gateway"""
    __tablename__ = "terminals"

    id = Column(Integer, primary_key=True, index=True)
    hardware_uuid = Column(String(64), unique=True, nullable=False)
    
    device_name = Column(String(100), nullable=True)
    device_type = Column(String(50))  # "tablet", "kiosk", "raspberry"
    device_model = Column(String(100), nullable=True)
    os_version = Column(String(50), nullable=True)
    
    gateway_id = Column(Integer, ForeignKey("gateways.id"), nullable=True)
    gateway = relationship("Gateway", back_populates="terminals")
    
    is_active = Column(Boolean, default=True)
    last_seen = Column(DateTime, nullable=True)
    total_scans = Column(Integer, default=0)
    
    alias = Column(String(100), nullable=True)


class Printer(Base):
    """Принтер свързан към gateway"""
    __tablename__ = "printers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    printer_type = Column(String(20))  # "network", "usb", "windows"
    
    ip_address = Column(String(50), nullable=True)
    port = Column(Integer, default=9100)
    protocol = Column(String(20))  # "raw", "lpd", "ipp"
    
    windows_share_name = Column(String(100), nullable=True)
    
    manufacturer = Column(String(50), nullable=True)
    model = Column(String(100), nullable=True)
    
    gateway_id = Column(Integer, ForeignKey("gateways.id"))
    gateway = relationship("Gateway", back_populates="printers")
    
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    last_test = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)


class GatewayHeartbeat(Base):
    """История на heartbeat събития"""
    __tablename__ = "gateway_heartbeats"

    id = Column(Integer, primary_key=True)
    gateway_id = Column(Integer, ForeignKey("gateways.id"))
    timestamp = Column(DateTime, default=sofia_now)
    status = Column(String(20))  # "online", "offline"
    cpu_usage = Column(Float, nullable=True)
    memory_usage = Column(Float, nullable=True)
    terminal_count = Column(Integer, default=0)
    printer_count = Column(Integer, default=0)


class TerminalSession(Base):
    """Сесия на терминал - кой служител на коя станция работи"""
    __tablename__ = "terminal_sessions"

    id = Column(Integer, primary_key=True)
    terminal_id = Column(String(100))  # Hardware UUID на терминала
    employee_id = Column(Integer, ForeignKey("users.id"))
    workstation_id = Column(Integer, ForeignKey("workstations.id"))
    
    started_at = Column(DateTime, default=sofia_now)
    ended_at = Column(DateTime, nullable=True)
    
    gateway_id = Column(Integer, ForeignKey("gateways.id"), nullable=True)
    
    employee = relationship("User")
    workstation = relationship("Workstation")
    task_logs = relationship("ProductionTaskLog", back_populates="session")


class ProductionTaskLog(Base):
    """Лог за изпълнението на задачите"""
    __tablename__ = "production_task_logs"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("terminal_sessions.id"))
    production_order_id = Column(Integer, ForeignKey("production_orders.id"))
    production_task_id = Column(Integer, ForeignKey("production_tasks.id"))
    
    started_at = Column(DateTime, default=sofia_now)
    completed_at = Column(DateTime, nullable=True)
    
    quantity_produced = Column(Integer, default=0)
    scrap_quantity = Column(Integer, default=0)
    
    status = Column(String(20))  # "in_progress", "completed"
    
    session = relationship("TerminalSession", back_populates="task_logs")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True) # Now optional
    username = Column(String, unique=True, index=True, nullable=True) # Added for non-email login
    hashed_password = Column(String, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    phone_number = Column(String(20), nullable=True)
    address = Column(String(255), nullable=True)
    egn = Column(Text, nullable=True) # Encrypted
    birth_date = Column(Date, nullable=True)
    iban = Column(Text, nullable=True) # Encrypted
    is_active = Column(Boolean, default=True)
    qr_secret = Column(String(64), nullable=True) # Secret for dynamic QR generation
    
    # Old String Fields (To be deprecated after migration)
    job_title = Column(String, nullable=True)
    department = Column(String, nullable=True)
    company = Column(String, nullable=True)

    # New Relations
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id", name="fk_user_department", use_alter=True), nullable=True)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=True)
    
    company_rel = relationship("Company", back_populates="users")
    department_rel = relationship("Department", back_populates="users", foreign_keys=[department_id])
    position_rel = relationship("Position", back_populates="users")

    created_at = Column(DateTime, default=sofia_now)
    last_login = Column(DateTime, nullable=True)
    
    # Security Fields
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    qr_token = Column(String, unique=True, index=True, nullable=True)
    password_force_change = Column(Boolean, default=False)
    profile_picture = Column(String, nullable=True) # Filename of the profile picture
    
    role_id = Column(Integer, ForeignKey("roles.id"))
    role = relationship("Role", back_populates="users")

    timelogs = relationship("TimeLog", back_populates="user", cascade="all, delete-orphan")
    payrolls = relationship("Payroll", back_populates="user", cascade="all, delete-orphan")
    payslips = relationship("Payslip", back_populates="user", cascade="all, delete-orphan")
    schedules = relationship("WorkSchedule", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    leave_requests = relationship("LeaveRequest", back_populates="user", cascade="all, delete-orphan")
    leave_balance = relationship("LeaveBalance", back_populates="user", cascade="all, delete-orphan")
    bonuses = relationship("Bonus", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    
    accessible_zones = relationship("AccessZone", secondary=user_access_zones, back_populates="authorized_users")


class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    refresh_token_jti = Column(String, unique=True, index=True, nullable=False)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    device_type = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=sofia_now)
    expires_at = Column(DateTime, nullable=False)
    last_used_at = Column(DateTime, default=sofia_now)

    user = relationship("User", back_populates="sessions")


class AuthKey(Base):
    __tablename__ = "auth_keys"

    id = Column(Integer, primary_key=True, index=True)
    kid = Column(String, unique=True, index=True, nullable=False)
    algorithm = Column(String, default="HS256")
    secret = Column(String, nullable=False)
    state = Column(String, default="active") # active, legacy, expired
    created_at = Column(DateTime, default=sofia_now)


class TimeLog(Base):
    __tablename__ = "timelogs"

    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(DateTime, default=sofia_now)
    end_time = Column(DateTime)
    is_manual = Column(Boolean, default=False)
    break_duration_minutes = Column(Integer, default=0)
    type = Column(String, default='work')  # work, break, overtime, etc.
    notes = Column(String, nullable=True)
    
    latitude = Column(Numeric(10, 6), nullable=True)
    longitude = Column(Numeric(10, 6), nullable=True)
    
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="timelogs")


class Payroll(Base):
    __tablename__ = "payrolls"

    id = Column(Integer, primary_key=True, index=True)
    hourly_rate = Column(Numeric(10, 2))
    monthly_salary = Column(Numeric(10, 2), nullable=True)
    overtime_multiplier = Column(Numeric(4, 2), default=1)
    standard_hours_per_day = Column(Integer, default=8)
    currency = Column(String, default="EUR")
    annual_leave_days = Column(Integer, default=20)
    
    # Deductions
    tax_percent = Column(Numeric(5, 2), default=10.00)
    health_insurance_percent = Column(Numeric(5, 2), default=13.78)
    has_tax_deduction = Column(Boolean, default=False)
    has_health_insurance = Column(Boolean, default=False)
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=True)
    
    user = relationship("User", back_populates="payrolls")
    position = relationship("Position", back_populates="payrolls")


class Payslip(Base):
    __tablename__ = "payslips"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)

    total_regular_hours = Column(Numeric(10, 2), default=0)
    total_overtime_hours = Column(Numeric(10, 2), default=0)

    regular_amount = Column(Numeric(10, 2), default=0)
    overtime_amount = Column(Numeric(10, 2), default=0)
    bonus_amount = Column(Numeric(10, 2), default=0)
    
    # New detail fields
    tax_amount = Column(Numeric(10, 2), default=0)
    insurance_amount = Column(Numeric(10, 2), default=0)
    sick_days = Column(Integer, default=0)
    leave_days = Column(Integer, default=0)
    
    total_amount = Column(Numeric(10, 2), default=0)

    generated_at = Column(DateTime, default=sofia_now)

    user = relationship("User", back_populates="payslips")


class Shift(Base):
    __tablename__ = "shifts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    
    tolerance_minutes = Column(Integer, default=15)
    break_duration_minutes = Column(Integer, default=0)
    pay_multiplier = Column(Numeric(4, 2), default=1.0)
    
    shift_type = Column(String, default=ShiftType.REGULAR.value)

    schedules = relationship("WorkSchedule", back_populates="shift")


class WorkSchedule(Base):
    __tablename__ = "work_schedules"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    
    user_id = Column(Integer, ForeignKey("users.id"))
    shift_id = Column(Integer, ForeignKey("shifts.id"))

    user = relationship("User", back_populates="schedules")
    shift = relationship("Shift", back_populates="schedules")


class GlobalSetting(Base):
    __tablename__ = "global_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    value = Column(String)

class Module(Base):
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True) # 'shifts', 'salaries', 'kiosk', 'integrations'
    is_enabled = Column(Boolean, default=True)
    name = Column(String(100), nullable=False)
    description = Column(String, nullable=True)
    updated_at = Column(DateTime, default=sofia_now, onupdate=sofia_now)

class PublicHoliday(Base):
    __tablename__ = "public_holidays"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    local_name = Column(String, nullable=True) # Името на български

class OrthodoxHoliday(Base):
    __tablename__ = "orthodox_holidays"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    local_name = Column(String, nullable=True)
    is_fixed = Column(Boolean, default=True)
    created_at = Column(DateTime, default=sofia_now)

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id")) # Recipient
    message = Column(String, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=sofia_now)

    user = relationship("User", back_populates="notifications")


class NotificationSetting(Base):
    __tablename__ = "notification_settings"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    event_type = Column(String, nullable=False)  # shift_swap, leave_approved, etc.
    email_enabled = Column(Boolean, default=True)
    push_enabled = Column(Boolean, default=True)
    email_template = Column(Text, nullable=True)  # HTML template
    recipients = Column(JSON, nullable=True)  # [{"type": "role", "value": "employee"}]
    interval_minutes = Column(Integer, default=60)
    enabled = Column(Boolean, default=True)
    last_sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=sofia_now)
    updated_at = Column(DateTime, default=sofia_now, onupdate=sofia_now)


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    leave_type = Column(String, nullable=False)  # paid_leave, sick_leave, unpaid_leave
    reason = Column(String, nullable=True)
    status = Column(String, default="pending")  # pending, approved, rejected
    created_at = Column(DateTime, default=sofia_now)
    
    # Optional: admin comment upon rejection
    admin_comment = Column(String, nullable=True)
    employer_top_up = Column(Boolean, default=False) # Работодателят плаща разликата до 100%

    user = relationship("User", back_populates="leave_requests")


class LeaveBalance(Base):
    __tablename__ = "leave_balances"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    year = Column(Integer, nullable=False)
    total_days = Column(Integer, default=20)
    used_days = Column(Integer, default=0)

    user = relationship("User", back_populates="leave_balance")

class Bonus(Base):
    __tablename__ = "bonuses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Numeric(10, 2), nullable=False)
    # We use a date to represent the month (e.g., 2023-10-01 for Oct 2023)
    date = Column(Date, nullable=False) 
    description = Column(String, nullable=True)

    user = relationship("User", back_populates="bonuses")


class MonthlyWorkDays(Base):
    __tablename__ = "monthly_work_days"

    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    days_count = Column(Integer, nullable=False)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Who performed it (null for system)
    action = Column(String, nullable=False) # e.g. "UPDATE_PAYROLL", "DELETE_USER"
    target_type = Column(String, nullable=True) # e.g. "User", "Shift", "Payroll"
    target_id = Column(Integer, nullable=True) # ID of the affected resource
    details = Column(String, nullable=True) # Detailed message or JSON string
    created_at = Column(DateTime, default=sofia_now)

    user = relationship("User")

class ShiftSwapRequest(Base):
    __tablename__ = "shift_swap_requests"

    id = Column(Integer, primary_key=True, index=True)
    requestor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    target_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    requestor_schedule_id = Column(Integer, ForeignKey("work_schedules.id"), nullable=False)
    target_schedule_id = Column(Integer, ForeignKey("work_schedules.id"), nullable=False)
    
    # status: pending, accepted, rejected, approved, cancelled
    status = Column(String, default="pending")
    
    created_at = Column(DateTime, default=sofia_now)
    updated_at = Column(DateTime, default=sofia_now, onupdate=sofia_now)

    requestor = relationship("User", foreign_keys=[requestor_id])
    target_user = relationship("User", foreign_keys=[target_user_id])
    requestor_schedule = relationship("WorkSchedule", foreign_keys=[requestor_schedule_id])
    target_schedule = relationship("WorkSchedule", foreign_keys=[target_schedule_id])

class ScheduleTemplate(Base):
    __tablename__ = "schedule_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=sofia_now)

    items = relationship("ScheduleTemplateItem", back_populates="template", cascade="all, delete-orphan")

class ScheduleTemplateItem(Base):
    __tablename__ = "schedule_template_items"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("schedule_templates.id"), nullable=False)
    day_index = Column(Integer, nullable=False) # 0, 1, 2... for the rotation
    shift_id = Column(Integer, ForeignKey("shifts.id"), nullable=True) # Null means a day off

    template = relationship("ScheduleTemplate", back_populates="items")
    shift = relationship("Shift")

class PushSubscription(Base):
    __tablename__ = "push_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    endpoint = Column(String, unique=True, nullable=False)
    p256dh = Column(String, nullable=False)
    auth = Column(String, nullable=False)
    preferences = Column(JSON, default={}) # Stores settings like {"leaves": true, "swaps": true}
    created_at = Column(DateTime, default=sofia_now)

    user = relationship("User", backref="push_subscriptions")

class UserDocument(Base):
    __tablename__ = "user_documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String, nullable=True) # e.g. 'contract', 'medical', 'other'
    is_locked = Column(Boolean, default=False) # If true, user cannot download, only see
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=sofia_now)

    user = relationship("User", foreign_keys=[user_id], backref="documents")
    uploader = relationship("User", foreign_keys=[uploaded_by])

class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False) # The admin who owns/created the key
    name = Column(String, nullable=False) # e.g. "Microinvest Integration"
    key_prefix = Column(String, nullable=False) # First 8 chars to identify it
    hashed_key = Column(String, nullable=False)
    permissions = Column(JSON, default=["read:all"]) # e.g. ["read:payroll", "write:logs"]
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=sofia_now)
    last_used_at = Column(DateTime, nullable=True)

    owner = relationship("User", backref="api_keys")

class Webhook(Base):
    __tablename__ = "webhooks"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, nullable=False)
    description = Column(String, nullable=True)
    events = Column(JSON, default=["*"]) # List of events like ["clock_in", "leave_approved"]
    secret = Column(String, nullable=True) # To sign payload
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=sofia_now)

class WorkplaceLocation(Base):
    __tablename__ = "workplace_locations"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    latitude = Column(Numeric(10, 8), nullable=False)
    longitude = Column(Numeric(11, 8), nullable=False)
    radius_meters = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=sofia_now)

    company = relationship("Company", backref="workplace_locations")


# --- Confectionery Production & Warehouse Module ---

class StorageZone(Base):
    __tablename__ = "storage_zones"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    temp_min = Column(Numeric(5, 2), nullable=True)
    temp_max = Column(Numeric(5, 2), nullable=True)
    description = Column(String, nullable=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    
    # Phase 7 additions
    is_active = Column(Boolean, default=True) # Field 'active'
    asset_type = Column(String(20), default="KMA") # 'ДМА' или 'КМА'
    zone_type = Column(String(20), default="food") # 'хранителен' или 'не хранителен'
    
    company = relationship("Company", backref="storage_zones")

class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    eik = Column(String(20), unique=True, nullable=True)
    vat_number = Column(String(20), unique=True, nullable=True)
    address = Column(String, nullable=True)
    contact_person = Column(String, nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String, nullable=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)

    company = relationship("Company", backref="suppliers")

class Ingredient(Base):
    __tablename__ = "ingredients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    unit = Column(String(20), default="kg") # kg, g, l, ml, br
    barcode = Column(String(100), unique=True, index=True, nullable=True)
    
    # Type: raw (суровина), semi_finished (заготовка), finished (готов продукт)
    product_type = Column(String(20), default="raw")
    
    # Stock levels
    baseline_min_stock = Column(Numeric(12, 3), default=0)
    current_price = Column(Numeric(12, 2), nullable=True) # Last purchase price
    
    # Food safety
    storage_zone_id = Column(Integer, ForeignKey("storage_zones.id"), nullable=True)
    is_perishable = Column(Boolean, default=True)
    expiry_warning_days = Column(Integer, default=3)
    allergens = Column(JSON, default=[]) # List of allergens
    
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)

    storage_zone = relationship("StorageZone")
    company = relationship("Company", backref="ingredients")

class Batch(Base):
    __tablename__ = "batches"
    id = Column(Integer, primary_key=True, index=True)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id", ondelete="CASCADE"), nullable=False)
    batch_number = Column(String(100), index=True)
    quantity = Column(Numeric(12, 3), nullable=False)
    
    # Phase 7 additions
    unit_value = Column(Numeric(12, 3), nullable=True) # e.g., 1.0 for 1L if unit is 'br'
    production_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=False, index=True)
    
    price_no_vat = Column(Numeric(12, 2), nullable=True)
    vat_percent = Column(Numeric(5, 2), default=20.0)
    price_with_vat = Column(Numeric(12, 2), nullable=True)
    
    is_stock_receipt = Column(Boolean, default=False) # стокова разписка
    invoice_number = Column(String(100), nullable=True)
    invoice_date = Column(Date, nullable=True)
    
    received_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String(50), default="active") # active, quarantined, expired, depleted, scrap
    
    received_at = Column(DateTime, default=sofia_now)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    storage_zone_id = Column(Integer, ForeignKey("storage_zones.id"), nullable=True)
    
    ingredient = relationship("Ingredient", backref="batches")
    supplier = relationship("Supplier")
    receiver = relationship("User", foreign_keys=[received_by])

class Recipe(Base):
    __tablename__ = "recipes"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String, nullable=True)
    yield_quantity = Column(Numeric(12, 2), default=1.0)
    yield_unit = Column(String(20), default="br")
    shelf_life_days = Column(Integer, default=7)  # Срок на годност в хладилник
    shelf_life_frozen_days = Column(Integer, default=30)  # Срок на годност замразена
    default_pieces = Column(Integer, default=12)  # Първоначален брой парчета
    production_time_days = Column(Integer, default=1) # Фаза 7: срок за изпълнение
    production_deadline_days = Column(Integer, nullable=True)  # Колко дни преди expiry да се произведе
    standard_quantity = Column(Numeric(12, 2), default=1.0) # Стандартно количество за производство
    instructions = Column(Text, nullable=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)

    company = relationship("Company", backref="recipes")
    sections = relationship("RecipeSection", back_populates="recipe", cascade="all, delete-orphan")
    # За съвместимост със стария код
    ingredients = relationship("RecipeIngredient", back_populates="recipe_legacy", cascade="all, delete-orphan")
    steps = relationship("RecipeStep", back_populates="recipe_legacy", cascade="all, delete-orphan")


class RecipeSection(Base):
    __tablename__ = "recipe_sections"
    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False)
    section_type = Column(String(20), nullable=False)  # "dough", "cream", "decoration"
    name = Column(String(255), nullable=False)  # "Блат - Торта Шоколад"
    shelf_life_days = Column(Integer, nullable=True)  # Срок на заготовката
    waste_percentage = Column(Numeric(5, 2), default=0.0)  # Фира %
    section_order = Column(Integer, default=0)  # 1, 2, 3
    
    recipe = relationship("Recipe", back_populates="sections")
    ingredients = relationship("RecipeIngredient", back_populates="section", cascade="all, delete-orphan")
    steps = relationship("RecipeStep", back_populates="section", cascade="all, delete-orphan")

class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"
    id = Column(Integer, primary_key=True, index=True)
    section_id = Column(Integer, ForeignKey("recipe_sections.id", ondelete="CASCADE"), nullable=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id", ondelete="CASCADE"), nullable=True)  # За съвместимост
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), nullable=False)
    workstation_id = Column(Integer, ForeignKey("workstations.id"), nullable=True) # За коя станция е продукта
    
    quantity_gross = Column(Numeric(12, 3), nullable=False) # amount taken from stock
    # quantity_net се изчислява автоматично от section.waste_percentage
    
    # Relationships
    section = relationship("RecipeSection", back_populates="ingredients")
    recipe_legacy = relationship("Recipe", back_populates="ingredients", foreign_keys=[recipe_id])
    ingredient = relationship("Ingredient")
    workstation = relationship("Workstation")

class Workstation(Base):
    __tablename__ = "workstations"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String, nullable=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)

    company = relationship("Company", backref="workstations")

class RecipeStep(Base):
    __tablename__ = "recipe_steps"
    id = Column(Integer, primary_key=True, index=True)
    section_id = Column(Integer, ForeignKey("recipe_sections.id", ondelete="CASCADE"), nullable=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id", ondelete="CASCADE"), nullable=True)  # За съвместимост
    workstation_id = Column(Integer, ForeignKey("workstations.id"), nullable=False)
    name = Column(String(255), nullable=False)
    step_order = Column(Integer, default=0)
    estimated_duration_minutes = Column(Integer, nullable=True)
    
    # Relationships
    section = relationship("RecipeSection", back_populates="steps")
    recipe_legacy = relationship("Recipe", back_populates="steps", foreign_keys=[recipe_id])
    workstation = relationship("Workstation")

class ProductionOrder(Base):
    __tablename__ = "production_orders"
    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    quantity = Column(Numeric(12, 2), nullable=False)
    due_date = Column(DateTime, nullable=False)
    
    # Status: pending, to_start, in_progress, completed, awaiting_delivery
    status = Column(String(50), default="pending")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=sofia_now)
    completed_at = Column(DateTime, nullable=True)
    completed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Confirmation fields - department head confirms ready status
    confirmed_at = Column(DateTime, nullable=True)
    confirmed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Production deadline - кога трябва да се произведе (изчислено от expiry - production_deadline_days)
    production_deadline = Column(DateTime, nullable=True)
    
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)

    recipe = relationship("Recipe")
    company = relationship("Company")
    creator = relationship("User", foreign_keys=[created_by])
    finisher = relationship("User", foreign_keys=[completed_by])
    confirmer = relationship("User", foreign_keys=[confirmed_by])
    tasks = relationship("ProductionTask", back_populates="order", cascade="all, delete-orphan")

class ProductionTask(Base):
    __tablename__ = "production_tasks"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("production_orders.id", ondelete="CASCADE"), nullable=False)
    workstation_id = Column(Integer, ForeignKey("workstations.id"), nullable=False)
    step_id = Column(Integer, ForeignKey("recipe_steps.id"), nullable=True)
    name = Column(String(255), nullable=False)
    
    # Status: pending, in_progress, completed, scrap
    status = Column(String(50), default="pending")
    is_scrap = Column(Boolean, default=False)
    scrap_value = Column(Numeric(12, 2), nullable=True) # Value + 26%
    
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    assigned_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    order = relationship("ProductionOrder", back_populates="tasks")
    workstation = relationship("Workstation")
    step = relationship("RecipeStep")
    assigned_user = relationship("User")


class ProductionScrapLog(Base):
    """Лог за брак на производствени задачи"""
    __tablename__ = "production_scrap_logs"
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("production_tasks.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    quantity = Column(Numeric(12, 3), nullable=False)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=sofia_now)
    
    task = relationship("ProductionTask")
    user = relationship("User")


class ProductionRecord(Base):
    """Запис за проследяемост на произведената продукция"""
    __tablename__ = "production_records"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("production_orders.id", ondelete="CASCADE"), nullable=False)
    confirmed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    confirmed_at = Column(DateTime, default=sofia_now)
    expiry_date = Column(Date, nullable=True)  # Изчислена дата на годност (от рецептата)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=sofia_now)

    order = relationship("ProductionOrder")
    confirmer = relationship("User")
    ingredients = relationship("ProductionRecordIngredient", back_populates="record", cascade="all, delete-orphan")
    workers = relationship("ProductionRecordWorker", back_populates="record", cascade="all, delete-orphan")


class ProductionRecordIngredient(Base):
    """Суровина/продукт използван в производството с партида и срок на годност"""
    __tablename__ = "production_record_ingredients"
    id = Column(Integer, primary_key=True, index=True)
    record_id = Column(Integer, ForeignKey("production_records.id", ondelete="CASCADE"), nullable=False)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), nullable=False)
    batch_number = Column(String(100), nullable=False)
    expiry_date = Column(Date, nullable=True)
    quantity_used = Column(Numeric(12, 2), nullable=False)
    unit = Column(String(20), nullable=True)

    record = relationship("ProductionRecord", back_populates="ingredients")
    ingredient = relationship("Ingredient")


class ProductionRecordWorker(Base):
    """Работник работил по поръчката"""
    __tablename__ = "production_record_workers"
    id = Column(Integer, primary_key=True, index=True)
    record_id = Column(Integer, ForeignKey("production_records.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    workstation_id = Column(Integer, ForeignKey("workstations.id"), nullable=True)
    task_id = Column(Integer, ForeignKey("production_tasks.id"), nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    record = relationship("ProductionRecord", back_populates="workers")
    user = relationship("User")
    workstation = relationship("Workstation")
    task = relationship("ProductionTask")


class InventorySession(Base):
    """Инвентаризация на склада"""
    __tablename__ = "inventory_sessions"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    started_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    started_at = Column(DateTime, default=sofia_now)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="active")  # active, completed
    protocol_number = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)

    company = relationship("Company")
    starter = relationship("User", foreign_keys=[started_by])
    items = relationship("InventoryItem", back_populates="session", cascade="all, delete-orphan")


class InventoryItem(Base):
    """Артикул при инвентаризация"""
    __tablename__ = "inventory_items"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("inventory_sessions.id", ondelete="CASCADE"), nullable=False)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), nullable=False)
    found_quantity = Column(Numeric(12, 3), nullable=True)  # Намерено количество
    system_quantity = Column(Numeric(12, 3), nullable=True)  # Количество по система
    difference = Column(Numeric(12, 3), nullable=True)  # Разлика
    adjusted = Column(Boolean, default=False)

    session = relationship("InventorySession", back_populates="items")
    ingredient = relationship("Ingredient")


class AdvancePayment(Base):
    """Еднократни авансови плащания преди заплата"""
    __tablename__ = "advance_payments"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    payment_date = Column(Date, nullable=False)
    description = Column(String(255), nullable=True)
    is_processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=sofia_now)

    user = relationship("User")


class ServiceLoan(Base):
    """Служебен аванс (заем), удържан на месечни вноски"""
    __tablename__ = "service_loans"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    installment_amount = Column(Numeric(10, 2), nullable=False)
    remaining_amount = Column(Numeric(10, 2), nullable=False)
    installments_count = Column(Integer, nullable=False) 
    installments_paid = Column(Integer, default=0) 
    start_date = Column(Date, nullable=False)
    description = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=sofia_now)

    user = relationship("User")


# Google Calendar Integration Models
class GoogleCalendarAccount(Base):
    __tablename__ = "google_calendar_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    google_user_id = Column(String(255), nullable=False, index=True)
    email = Column(String(255), nullable=False)
    access_token = Column(String, nullable=True)
    refresh_token = Column(String, nullable=False)
    token_expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=sofia_now)
    updated_at = Column(DateTime, nullable=True, onupdate=sofia_now)
    
    user = relationship("User", backref="google_calendar_accounts")
    sync_settings = relationship("GoogleCalendarSyncSettings", back_populates="account", cascade="all, delete-orphan", uselist=False)
    events = relationship("GoogleCalendarEvent", back_populates="account", cascade="all, delete-orphan")


class GoogleCalendarSyncSettings(Base):
    __tablename__ = "google_calendar_sync_settings"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("google_calendar_accounts.id", ondelete="CASCADE"), nullable=False)
    calendar_id = Column(String(255), nullable=False, default='primary')
    sync_work_schedules = Column(Boolean, default=True)
    sync_time_logs = Column(Boolean, default=False)
    sync_leave_requests = Column(Boolean, default=True)
    sync_public_holidays = Column(Boolean, default=True)
    sync_direction = Column(String(20), default='to_google')  # 'to_google', 'from_google', 'bidirectional'
    sync_frequency_minutes = Column(Integer, default=15)
    privacy_level = Column(String(20), default='title_only')  # 'full', 'title_only', 'busy_only'
    default_event_visibility = Column(String(20), default='default')  # 'default', 'public', 'private'
    timezone = Column(String(50), default='Europe/Sofia')
    created_at = Column(DateTime, default=sofia_now)
    updated_at = Column(DateTime, nullable=True, onupdate=sofia_now)
    
    account = relationship("GoogleCalendarAccount", back_populates="sync_settings")


class GoogleCalendarEvent(Base):
    __tablename__ = "google_calendar_events"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("google_calendar_accounts.id", ondelete="CASCADE"), nullable=False)
    google_event_id = Column(String(255), nullable=False)
    google_calendar_id = Column(String(255), nullable=False)
    source_type = Column(String(50), nullable=False)  # 'work_schedule', 'time_log', 'leave_request', 'holiday'
    source_id = Column(Integer, nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(String, nullable=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    is_all_day = Column(Boolean, default=False)
    google_updated_at = Column(DateTime, nullable=True)
    last_sync_at = Column(DateTime, default=sofia_now)
    sync_status = Column(String(20), default='synced')  # 'synced', 'pending', 'error', 'deleted'
    sync_error = Column(String, nullable=True)
    created_at = Column(DateTime, default=sofia_now)
    
    account = relationship("GoogleCalendarAccount", back_populates="events")


class GoogleSyncLog(Base):
    __tablename__ = "google_sync_log"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("google_calendar_accounts.id", ondelete="CASCADE"), nullable=False)
    sync_type = Column(String(50), nullable=False)  # 'full_sync', 'incremental', 'error_retry'
    events_processed = Column(Integer, default=0)
    events_created = Column(Integer, default=0)
    events_updated = Column(Integer, default=0)
    events_deleted = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(20), default='running')  # 'running', 'completed', 'failed'
    error_details = Column(String, nullable=True)
    created_at = Column(DateTime, default=sofia_now)
    
    account = relationship("GoogleCalendarAccount")


# Enhanced Payroll System Models
class PayrollPaymentSchedule(Base):
    __tablename__ = "payroll_payment_schedules"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    payment_day = Column(Integer, nullable=False)  # 25-то число например
    payment_month_offset = Column(Integer, default=0)  # 0 за текущия месец, 1 за следващия
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=sofia_now)
    updated_at = Column(DateTime, nullable=True, onupdate=sofia_now)
    
    company = relationship("Company", backref="payment_schedules")


class PayrollDeduction(Base):
    __tablename__ = "payroll_deductions"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    deduction_type = Column(String(50), nullable=False)  # 'fixed', 'percentage', 'conditional'
    amount = Column(Numeric(10, 2), nullable=True)
    percentage = Column(Numeric(5, 2), nullable=True)
    comment = Column(String(255), nullable=True)
    priority = Column(Integer, default=0) # Поредност на удържане
    is_active = Column(Boolean, default=True)
    apply_to_all = Column(Boolean, default=True)
    employee_ids = Column(JSON, nullable=True)  # Specific employees as array
    created_at = Column(DateTime, default=sofia_now)
    updated_at = Column(DateTime, nullable=True, onupdate=sofia_now)
    
    company = relationship("Company", backref="payroll_deductions")


class SickLeaveRecord(Base):
    __tablename__ = "sick_leave_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    sick_leave_type = Column(String(50), nullable=False)  # 'general', 'work_related', 'maternity', 'child_care'
    is_paid_by_noi = Column(Boolean, default=True)
    employer_payment_percentage = Column(Numeric(5, 2), default=75.00)  # 75% от работодателя
    daily_amount = Column(Numeric(10, 2), nullable=True)  # Дневно обезщетение
    total_days = Column(Integer, nullable=False)
    noi_payment_days = Column(Integer, default=0)  # Дни платени от НОЙ
    employer_payment_days = Column(Integer, default=0)  # Дни платени от работодателя
    medical_document_number = Column(String(100), nullable=True)
    status = Column(String(20), default='active')  # 'active', 'expired', 'cancelled'
    created_at = Column(DateTime, default=sofia_now)
    updated_at = Column(DateTime, nullable=True, onupdate=sofia_now)
    
    user = relationship("User", backref="sick_leave_records")


class NOIPaymentDays(Base):
    __tablename__ = "noi_payment_days"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    year = Column(Integer, nullable=False)
    total_noi_days_available = Column(Integer, default=30)  # Според Кодекса на труда
    noi_days_used = Column(Integer, default=0)
    noi_days_remaining = Column(Integer, nullable=False)  # Computed column
    employer_payment_percentage = Column(Numeric(5, 2), default=75.00)
    created_at = Column(DateTime, default=sofia_now)
    updated_at = Column(DateTime, nullable=True, onupdate=sofia_now)
    
    user = relationship("User", backref="noi_payment_days")


class WebAuthnChallenge(Base):
    __tablename__ = "webauthn_challenges"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True) # Optional for login
    challenge = Column(String(255), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=sofia_now)


class WebAuthnCredential(Base):
    __tablename__ = "webauthn_credentials"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    credential_id = Column(LargeBinary, unique=True, index=True, nullable=False)
    public_key = Column(LargeBinary, nullable=False)
    sign_count = Column(Integer, default=0)
    transports = Column(String(255), nullable=True)  # comma separated list
    created_at = Column(DateTime, default=sofia_now)
    last_used_at = Column(DateTime, nullable=True)
    friendly_name = Column(String(100), nullable=True)

    user = relationship("User", backref="webauthn_credentials")


class EmploymentContract(Base):
    __tablename__ = "employment_contracts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    contract_type = Column(String(50), nullable=False)  # "full_time", "part_time", "contractor", "internship"
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)  # For fixed-term contracts
    base_salary = Column(Numeric(10, 2), nullable=True)
    work_hours_per_week = Column(Integer, default=40)
    probation_months = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    salary_calculation_type = Column(String(20), default='gross')  # 'gross', 'net'
    salary_installments_count = Column(Integer, default=1)  # Брой плащания (вноски) на заплатата
    monthly_advance_amount = Column(Numeric(10, 2), default=0) # Фиксиран месечен аванс
    tax_resident = Column(Boolean, default=True)
    insurance_contributor = Column(Boolean, default=True)  # Whether employee pays insurance
    has_income_tax = Column(Boolean, default=True) # Whether to withhold income tax
    created_at = Column(DateTime, default=sofia_now)
    updated_at = Column(DateTime, nullable=True, onupdate=sofia_now)
    
    user = relationship("User", backref="employment_contracts")
    company = relationship("Company", backref="employment_contracts")


class PayrollPeriod(Base):
    __tablename__ = "payroll_periods"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String(20), default='open')  # 'open', 'processing', 'closed'
    processing_date = Column(DateTime, nullable=True)
    payment_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=sofia_now)
    
    company = relationship("Company", backref="payroll_periods")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    payslip_id = Column(Integer, ForeignKey("payslips.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    payment_date = Column(DateTime, nullable=True)
    payment_method = Column(String(50), nullable=True)  # 'bank_transfer', 'cash', 'check'
    status = Column(String(20), default='pending')  # 'pending', 'completed', 'failed'
    reference = Column(String(255), nullable=True)  # Bank reference, receipt number
    created_at = Column(DateTime, default=sofia_now)
    
    payslip = relationship("Payslip", backref="payments")


# Configuration Framework Models
class ConfigurationCategory(Base):
    __tablename__ = "configuration_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String, nullable=True)
    is_system = Column(Boolean, default=False)  # System vs user-defined
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True)
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=sofia_now)
    
    company = relationship("Company", backref="configuration_categories")
    fields = relationship("ConfigurationField", back_populates="category", cascade="all, delete-orphan")


class ConfigurationField(Base):
    __tablename__ = "configuration_fields"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("configuration_categories.id", ondelete="CASCADE"), nullable=False)
    key = Column(String(100), nullable=False)
    label = Column(String(255), nullable=False)
    field_type = Column(String(50), nullable=False)  # 'text', 'number', 'select', 'checkbox', 'date'
    validation_rules = Column(JSON, nullable=True)  # {"required": true, "min": 0, "max": 100}
    default_value = Column(String, nullable=True)
    display_order = Column(Integer, default=0)
    options = Column(JSON, nullable=True)  # For select fields
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=sofia_now)
    
    category = relationship("ConfigurationCategory", back_populates="fields")
    company_configurations = relationship("CompanyConfiguration", back_populates="field", cascade="all, delete-orphan")


class CompanyConfiguration(Base):
    __tablename__ = "company_configurations"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    field_id = Column(Integer, ForeignKey("configuration_fields.id", ondelete="CASCADE"), nullable=False)
    value = Column(String, nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime, default=sofia_now, onupdate=sofia_now)
    
    company = relationship("Company", backref="configurations")
    field = relationship("ConfigurationField", back_populates="company_configurations")
    updated_by_user = relationship("User", foreign_keys=[updated_by])


class InvoiceType(str, enum.Enum):
    INCOMING = "incoming"  # Входяща (от доставчик)
    OUTGOING = "outgoing"  # Изходяща (към клиент)


class InvoiceStatus(str, enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class PaymentMethod(str, enum.Enum):
    BANK = "bank"
    CASH = "cash"
    CARD = "card"


class Invoice(Base):
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    number = Column(String(50), unique=True, nullable=False, index=True)
    type = Column(String(20), nullable=False)  # incoming / outgoing
    
    # Нов полета за българска фактура
    document_type = Column(String(50), default="ФАКТУРА")  # ФАКТУРА, ПРОФОРМА, КОРЕКЦИЯ
    griff = Column(String(20), default="ОРИГИНАЛ")  # ОРИГИНАЛ, КОПИЕ
    description = Column(Text, nullable=True)  # Основание за сделката
    
    date = Column(Date, nullable=False)
    
    # За входящи фактури
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    batch_id = Column(Integer, ForeignKey("batches.id"), nullable=True)  # Свързана партида
    
    # За изходящи фактури
    client_name = Column(String(255), nullable=True)
    client_eik = Column(String(20), nullable=True)
    client_address = Column(Text, nullable=True)
    
    # Суми
    subtotal = Column(Numeric(12, 2), default=0)
    discount_percent = Column(Numeric(5, 2), default=0)
    discount_amount = Column(Numeric(12, 2), default=0)
    vat_rate = Column(Numeric(5, 2), default=20.0)
    vat_amount = Column(Numeric(12, 2), default=0)
    total = Column(Numeric(12, 2), default=0)
    
    # Плащане и доставка
    payment_method = Column(String(50), nullable=True)  # Банков превод, В брой, Карта
    delivery_method = Column(String(50), default="Доставка до адрес")  # Доставка до адрес, Взимане от склад, Куриер
    due_date = Column(Date, nullable=True)
    payment_date = Column(Date, nullable=True)
    
    status = Column(String(20), default="draft")  # draft, sent, paid, overdue, cancelled
    
    notes = Column(Text, nullable=True)
    
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=sofia_now)
    updated_at = Column(DateTime, nullable=True, onupdate=sofia_now)
    
    company = relationship("Company", backref="invoices")
    supplier = relationship("Supplier", backref="invoices")
    batch = relationship("Batch", backref="invoices")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by])


class InvoiceItem(Base):
    __tablename__ = "invoice_items"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    
    # За входящи фактури - свързаност със склада
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), nullable=True)
    batch_id = Column(Integer, ForeignKey("batches.id"), nullable=True)
    
    # За изходящи фактури - свободни артикули
    name = Column(String(255), nullable=False)
    quantity = Column(Numeric(12, 3), nullable=False)
    unit = Column(String(20), default="br")
    unit_price = Column(Numeric(12, 2), nullable=False)
    discount_percent = Column(Numeric(5, 2), default=0)
    total = Column(Numeric(12, 2), nullable=False)
    
    invoice = relationship("Invoice", back_populates="items")
    ingredient = relationship("Ingredient", backref="invoice_items")
    batch = relationship("Batch", backref="invoice_items")


class CashJournalEntry(Base):
    __tablename__ = "cash_journal_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    operation_type = Column(String(20), nullable=False)  # income / expense
    amount = Column(Numeric(12, 2), nullable=False)
    description = Column(Text, nullable=True)
    reference_type = Column(String(20), nullable=True)  # invoice / manual / other
    reference_id = Column(Integer, nullable=True)
    payment_method = Column(String(50), nullable=True)  # Банков превод, В брой, Карта
    
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=sofia_now)
    
    company = relationship("Company", backref="cash_journal_entries")
    creator = relationship("User", foreign_keys=[created_by])


class OperationLog(Base):
    __tablename__ = "operation_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=sofia_now, nullable=False, index=True)
    operation = Column(String(20), nullable=False)  # create / update / delete
    entity_type = Column(String(50), nullable=False)  # invoice / cash_journal / etc
    entity_id = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    changes = Column(JSON, nullable=True)  # JSON with the changes made
    
    user = relationship("User", foreign_keys=[user_id])


class DailySummary(Base):
    __tablename__ = "daily_summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, nullable=False, index=True)
    
    # Invoice counts
    invoices_count = Column(Integer, default=0)
    incoming_invoices_count = Column(Integer, default=0)
    outgoing_invoices_count = Column(Integer, default=0)
    
    # Invoice totals
    invoices_total = Column(Numeric(12, 2), default=0)
    incoming_invoices_total = Column(Numeric(12, 2), default=0)
    outgoing_invoices_total = Column(Numeric(12, 2), default=0)
    
    # Cash operations
    cash_income = Column(Numeric(12, 2), default=0)
    cash_expense = Column(Numeric(12, 2), default=0)
    cash_balance = Column(Numeric(12, 2), default=0)
    
    # VAT
    vat_collected = Column(Numeric(12, 2), default=0)
    vat_paid = Column(Numeric(12, 2), default=0)
    
    # Payment status
    paid_invoices_count = Column(Integer, default=0)
    unpaid_invoices_count = Column(Integer, default=0)
    overdue_invoices_count = Column(Integer, default=0)
    
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=sofia_now)
    
    company = relationship("Company", backref="daily_summaries")


class MonthlySummary(Base):
    __tablename__ = "monthly_summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=False)  # 1-12
    
    # Invoice counts
    invoices_count = Column(Integer, default=0)
    incoming_invoices_count = Column(Integer, default=0)
    outgoing_invoices_count = Column(Integer, default=0)
    
    # Invoice totals
    invoices_total = Column(Numeric(12, 2), default=0)
    incoming_invoices_total = Column(Numeric(12, 2), default=0)
    outgoing_invoices_total = Column(Numeric(12, 2), default=0)
    
    # Cash operations
    cash_income = Column(Numeric(12, 2), default=0)
    cash_expense = Column(Numeric(12, 2), default=0)
    cash_balance = Column(Numeric(12, 2), default=0)
    
    # VAT
    vat_collected = Column(Numeric(12, 2), default=0)
    vat_paid = Column(Numeric(12, 2), default=0)
    
    # Payment status
    paid_invoices_count = Column(Integer, default=0)
    unpaid_invoices_count = Column(Integer, default=0)
    overdue_invoices_count = Column(Integer, default=0)
    
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=sofia_now)
    
    company = relationship("Company", backref="monthly_summaries")


class YearlySummary(Base):
    __tablename__ = "yearly_summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, nullable=False, unique=True, index=True)
    
    # Invoice counts
    invoices_count = Column(Integer, default=0)
    incoming_invoices_count = Column(Integer, default=0)
    outgoing_invoices_count = Column(Integer, default=0)
    
    # Invoice totals
    invoices_total = Column(Numeric(12, 2), default=0)
    incoming_invoices_total = Column(Numeric(12, 2), default=0)
    outgoing_invoices_total = Column(Numeric(12, 2), default=0)
    
    # Cash operations
    cash_income = Column(Numeric(12, 2), default=0)
    cash_expense = Column(Numeric(12, 2), default=0)
    cash_balance = Column(Numeric(12, 2), default=0)
    
    # VAT
    vat_collected = Column(Numeric(12, 2), default=0)
    vat_paid = Column(Numeric(12, 2), default=0)
    
    # Payment status
    paid_invoices_count = Column(Integer, default=0)
    unpaid_invoices_count = Column(Integer, default=0)
    overdue_invoices_count = Column(Integer, default=0)
    
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=sofia_now)
    
    company = relationship("Company", backref="yearly_summaries")


# ============== ACCOUNTING MODELS FOR SAF-T COMPLIANCE ==============

class InvoiceCorrection(Base):
    __tablename__ = "invoice_corrections"
    
    id = Column(Integer, primary_key=True, index=True)
    number = Column(String(50), nullable=False)
    type = Column(String(20), nullable=False)  # 'credit', 'debit'
    original_invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    correction_type = Column(String(20), nullable=False)  # 'credit', 'debit'
    reason = Column(Text, nullable=True)
    amount_diff = Column(Numeric(12, 2), default=0)
    vat_diff = Column(Numeric(12, 2), default=0)
    correction_date = Column(Date, nullable=False)
    date = Column(Date, nullable=False)  # alias for correction_date for GraphQL
    new_invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=True)
    status = Column(String(20), default="draft")
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=sofia_now)
    
    original_invoice = relationship("Invoice", foreign_keys=[original_invoice_id])
    new_invoice = relationship("Invoice", foreign_keys=[new_invoice_id])


class CashReceipt(Base):
    __tablename__ = "cash_receipts"
    
    id = Column(Integer, primary_key=True, index=True)
    receipt_number = Column(String(50), unique=True, nullable=False)
    date = Column(Date, nullable=False)
    payment_type = Column(String(20), default="cash")  # 'cash', 'card'
    amount = Column(Numeric(12, 2), nullable=False)
    vat_amount = Column(Numeric(12, 2), default=0)
    items_json = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=sofia_now)
    
    company = relationship("Company", backref="cash_receipts")
    creator = relationship("User", foreign_keys=[created_by])


class BankAccount(Base):
    __tablename__ = "bank_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    iban = Column(String(34), unique=True, nullable=False)
    bic = Column(String(11), nullable=True)
    bank_name = Column(String(255), nullable=False)
    account_type = Column(String(20), default="current")  # 'current', 'escrow'
    currency = Column(String(3), default="BGN")
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=sofia_now)
    
    company = relationship("Company", backref="bank_accounts")
    transactions = relationship("BankTransaction", back_populates="bank_account", cascade="all, delete-orphan")


class BankTransaction(Base):
    __tablename__ = "bank_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    bank_account_id = Column(Integer, ForeignKey("bank_accounts.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    type = Column(String(20), nullable=False)  # 'credit', 'debit'
    description = Column(Text, nullable=True)
    reference = Column(String(100), nullable=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=True)
    matched = Column(Boolean, default=False)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=sofia_now)
    
    bank_account = relationship("BankAccount", back_populates="transactions")
    invoice = relationship("Invoice", backref="bank_transactions")
    company = relationship("Company", backref="bank_transactions")


class Account(Base):
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    type = Column(String(20), nullable=False)  # 'asset', 'liability', 'equity', 'revenue', 'expense'
    parent_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    opening_balance = Column(Numeric(12, 2), default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=sofia_now)
    
    company = relationship("Company", backref="accounts")
    parent = relationship("Account", remote_side=[id], backref="children")
    debit_entries = relationship("AccountingEntry", foreign_keys="AccountingEntry.debit_account_id", back_populates="debit_account")
    credit_entries = relationship("AccountingEntry", foreign_keys="AccountingEntry.credit_account_id", back_populates="credit_account")


class AccountingEntry(Base):
    __tablename__ = "accounting_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    entry_number = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    
    debit_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    credit_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    vat_amount = Column(Numeric(12, 2), default=0)
    
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=True)
    bank_transaction_id = Column(Integer, ForeignKey("bank_transactions.id"), nullable=True)
    cash_journal_id = Column(Integer, ForeignKey("cash_journal_entries.id"), nullable=True)
    
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=sofia_now)
    
    debit_account = relationship("Account", foreign_keys=[debit_account_id], back_populates="debit_entries")
    credit_account = relationship("Account", foreign_keys=[credit_account_id], back_populates="credit_entries")
    invoice = relationship("Invoice", backref="accounting_entries")
    company = relationship("Company", backref="accounting_entries")
    creator = relationship("User", foreign_keys=[created_by])


class VATRegister(Base):
    __tablename__ = "vat_registers"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    period_month = Column(Integer, nullable=False)
    period_year = Column(Integer, nullable=False)
    
    vat_collected_20 = Column(Numeric(12, 2), default=0)
    vat_collected_9 = Column(Numeric(12, 2), default=0)
    vat_collected_0 = Column(Numeric(12, 2), default=0)
    
    vat_paid_20 = Column(Numeric(12, 2), default=0)
    vat_paid_9 = Column(Numeric(12, 2), default=0)
    vat_paid_0 = Column(Numeric(12, 2), default=0)
    
    vat_adjustment = Column(Numeric(12, 2), default=0)
    vat_due = Column(Numeric(12, 2), default=0)
    vat_credit = Column(Numeric(12, 2), default=0)
    
    created_at = Column(DateTime, default=sofia_now)
    updated_at = Column(DateTime, nullable=True, onupdate=sofia_now)
    
    company = relationship("Company", backref="vat_registers")


class AccessZone(Base):
    """Зона за контрол на достъп"""
    __tablename__ = "access_zones"

    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(String(50), unique=True, index=True, nullable=False) # zone_1
    name = Column(String(100), nullable=False)
    level = Column(Integer, default=1)
    depends_on = Column(JSON, default=[]) # List of zone_id strings
    
    required_hours_start = Column(String(5), default="00:00")
    required_hours_end = Column(String(5), default="23:59")
    
    anti_passback_enabled = Column(Boolean, default=False)
    anti_passback_type = Column(String(20), default="soft") # soft, hard, timed
    anti_passback_timeout = Column(Integer, default=5)
    
    description = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    
    doors = relationship("AccessDoor", back_populates="zone")
    authorized_users = relationship("User", secondary=user_access_zones, back_populates="accessible_zones")


class AccessDoor(Base):
    """Врата за контрол на достъп"""
    __tablename__ = "access_doors"

    id = Column(Integer, primary_key=True, index=True)
    door_id = Column(String(50), unique=True, index=True, nullable=False) # door_1
    name = Column(String(100), nullable=False)
    
    zone_db_id = Column(Integer, ForeignKey("access_zones.id", ondelete="CASCADE"), nullable=False)
    gateway_id = Column(Integer, ForeignKey("gateways.id", ondelete="CASCADE"), nullable=False)
    
    device_id = Column(String(50), nullable=False) # ID of relay device
    relay_number = Column(Integer, default=1)
    terminal_id = Column(String(100), nullable=True) # Hardware UUID of associated terminal
    terminal_mode = Column(String(20), default="access") # "clock", "access", "both"
    
    description = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    
    zone = relationship("AccessZone", back_populates="doors")
    gateway = relationship("Gateway")


class AccessCode(Base):
    """Код за еднократен/временен достъп"""
    __tablename__ = "access_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, index=True, nullable=False)
    code_type = Column(String(20), default="one_time") # one_time, daily, guest, permanent
    
    zones = Column(JSON, default=[]) # List of zone_id strings
    uses_remaining = Column(Integer, default=1)
    
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=sofia_now)
    last_used_at = Column(DateTime, nullable=True)
    
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    
    gateway_id = Column(Integer, ForeignKey("gateways.id", ondelete="CASCADE"), nullable=True)


class AccessLog(Base):
    """Лог за достъп (синхронизиран от gateway)"""
    __tablename__ = "access_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, index=True, nullable=False)
    
    user_id = Column(String(100), nullable=True)
    user_name = Column(String(255), nullable=True)
    
    zone_id = Column(String(50), nullable=True)
    zone_name = Column(String(100), nullable=True)
    
    door_id = Column(String(50), nullable=True)
    door_name = Column(String(100), nullable=True)
    
    action = Column(String(20)) # enter, exit
    result = Column(String(20)) # granted, denied
    reason = Column(String(100), nullable=True)
    method = Column(String(20)) # qr_scan, code, remote
    
    terminal_id = Column(String(100), nullable=True)
    gateway_id = Column(Integer, ForeignKey("gateways.id", ondelete="CASCADE"), nullable=False)
    
    gateway = relationship("Gateway")
