import datetime
import enum
import sys
import os
from decimal import Decimal
from typing import Optional, List
from backend.utils.json_type import JSONScalar
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
from sqlalchemy.orm import relationship, declarative_base, Mapped, mapped_column

from backend.config import settings


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

    id:Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True)
    description: Mapped[str] = mapped_column(String)
    
    # RBAC enhancements
    is_system_role: Mapped[bool] = mapped_column(Boolean, default=False)  # System vs user-defined roles
    priority: Mapped[int] = mapped_column(Integer, default=0)  # Role hierarchy priority
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=sofia_now)
    updated_at: Mapped[DateTime] = mapped_column(DateTime, nullable=True)

    users: Mapped[list["User"]]= relationship("User", back_populates="role")
    role_permissions: Mapped[list["RolePermission"]] = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")
    company_assignments: Mapped[list["CompanyRoleAssignment"]] = relationship("CompanyRoleAssignment", back_populates="role", cascade="all, delete-orphan")


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)  # "users:read", "payroll:create"
    resource: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # "users", "payroll", "schedules"
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # "read", "create", "update", "delete"
    description: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=sofia_now)
    
    # Ensure unique resource-action combinations
    __table_args__ = (
        {"schema": None},
    )
    
    role_permissions = relationship("RolePermission", back_populates="permission", cascade="all, delete-orphan")


class RolePermission(Base):
    __tablename__ = "role_permissions"

    id:Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    permission_id: Mapped[int] = mapped_column(Integer, ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False)
    granted_at: Mapped[DateTime] = mapped_column(DateTime, default=sofia_now)
    granted_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    
    role = relationship("Role", back_populates="role_permissions")
    permission = relationship("Permission", back_populates="role_permissions")
    granted_by_user = relationship("User", foreign_keys=[granted_by])


class CompanyRoleAssignment(Base):
    __tablename__ = "company_role_assignments"

    id:Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    assigned_at: Mapped[DateTime] = mapped_column(DateTime, default=sofia_now)
    assigned_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[DateTime] = mapped_column(DateTime, nullable=True)  # For temporary role assignments
    
    user = relationship("User", foreign_keys=[user_id])
    company = relationship("Company", foreign_keys=[company_id])
    role = relationship("Role", back_populates="company_assignments")
    assigned_by_user = relationship("User", foreign_keys=[assigned_by])


class UserPermissionCache(Base):
    __tablename__ = "user_permission_cache"

    id:Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True)
    permission_name: Mapped[str] = mapped_column(String(100), nullable=False)
    granted_at: Mapped[DateTime] = mapped_column(DateTime, default=sofia_now)
    expires_at: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    
    user = relationship("User")
    company = relationship("Company")


class PermissionAuditLog(Base):
    __tablename__ = "permission_audit_log"

    id:Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # "GRANTED", "DENIED", "CHECKED"
    resource_type: Mapped[str] = mapped_column(String(50), nullable=True)
    resource_id: Mapped[int] = mapped_column(Integer, nullable=True)
    permission: Mapped[str] = mapped_column(String(100), nullable=False)
    decision: Mapped[str] = mapped_column(String(20), nullable=False)  # 'GRANTED' or 'DENIED'
    ip_address: Mapped[str] = mapped_column(String(45), nullable=True)  # IPv6 compatible
    user_agent: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=sofia_now)
    
    user = relationship("User")


class Company(Base):
    __tablename__ = "companies"

    id:Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    eik: Mapped[str] = mapped_column(String, unique=True, nullable=True) # ЕИК
    bulstat: Mapped[str] = mapped_column(String, unique=True, nullable=True) # БУЛСТАТ
    vat_number: Mapped[str] = mapped_column(String, unique=True, nullable=True) # ДДС номер
    address: Mapped[str] = mapped_column(String, nullable=True) # Седалище и адрес на управление
    mol_name: Mapped[str] = mapped_column(String, nullable=True) # МOL
    
    # Default accounting accounts for automation
    default_sales_account_id: Mapped[int] = mapped_column(Integer, nullable=True)  # 701 - Приходи от продажби
    default_expense_account_id: Mapped[int] = mapped_column(Integer, nullable=True)  # 601 - Разходи за материали
    default_vat_account_id: Mapped[int] = mapped_column(Integer, nullable=True)  # 453 - ДДС
    default_customer_account_id: Mapped[int] = mapped_column(Integer, nullable=True)  # 411 - Вземания от клиенти
    default_supplier_account_id: Mapped[int] = mapped_column(Integer, nullable=True)  # 401 - Задължения към доставчици
    default_cash_account_id: Mapped[int] = mapped_column(Integer, nullable=True)  # 501 - Каса
    default_bank_account_id: Mapped[int] = mapped_column(Integer, nullable=True)  # 503 - Банкови сметки

    users = relationship("User", back_populates="company_rel")
    departments = relationship("Department", back_populates="company")


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True, nullable=False)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), nullable=True)
    manager_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", name="fk_department_manager", use_alter=True), nullable=True) # Началник отдел
    
    company = relationship("Company", back_populates="departments")
    manager = relationship("User", foreign_keys=[manager_id])
    users = relationship("User", back_populates="department_rel", foreign_keys="[User.department_id]")
    positions = relationship("Position", back_populates="department")
    contract_template_versions = relationship("ContractTemplateVersion", back_populates="department")


class Position(Base):
    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String, index=True, nullable=False)
    department_id: Mapped[int] = mapped_column(Integer, ForeignKey("departments.id"), nullable=True)

    department = relationship("Department", back_populates="positions")
    users = relationship("User", back_populates="position_rel")
    payrolls = relationship("Payroll", back_populates="position", cascade="all, delete-orphan")
    contract_template_versions = relationship("ContractTemplateVersion", back_populates="position")


class KioskDevice(Base):
    __tablename__ = "kiosk_devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    device_uid: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False) # Serial or Hardware ID
    beacon_uuid: Mapped[str] = mapped_column(String(100), unique=True, nullable=True) # For BLE proximity
    secret_key: Mapped[str] = mapped_column(String(255), nullable=False)
    ip_address: Mapped[str] = mapped_column(String(50), nullable=True) # Authorized IP
    latitude: Mapped[float] = mapped_column(Float, nullable=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_heartbeat: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=sofia_now)


class Gateway(Base):
    """Gateway устройство - инсталирано на Windows машина в локалната мрежа"""
    __tablename__ = "gateways"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)  # GATEWAY-001
    hardware_uuid: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)  # Hardware-bound UUID
    alias: Mapped[str] = mapped_column(String(100), nullable=True)  # User-defined alias
    api_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=True)  # API key for authentication
    ip_address: Mapped[str] = mapped_column(String(50), nullable=True)
    local_hostname: Mapped[str] = mapped_column(String(100), nullable=True)
    terminal_port: Mapped[int] = mapped_column(Integer, default=8080)
    web_port: Mapped[int] = mapped_column(Integer, default=8888)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_online: Mapped[bool] = mapped_column(Boolean, default=True)
    system_mode: Mapped[str] = mapped_column(String(30), default="normal") # normal, emergency_unlock, lockdown
    last_heartbeat: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True)
    registered_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), nullable=True)

    company = relationship("Company")
    terminals = relationship("Terminal", back_populates="gateway")
    printers = relationship("Printer", back_populates="gateway")


class Terminal(Base):
    """Терминал - таблет/киоск свързан към gateway"""
    __tablename__ = "terminals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    hardware_uuid: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    
    device_name: Mapped[str] = mapped_column(String(100), nullable=True)
    device_type: Mapped[str] = mapped_column(String(50))  # "tablet", "kiosk", "raspberry"
    device_model: Mapped[str] = mapped_column(String(100), nullable=True)
    os_version: Mapped[str] = mapped_column(String(50), nullable=True)
    gateway_id: Mapped[int] = mapped_column(Integer, ForeignKey("gateways.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_seen: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True)
    total_scans: Mapped[int] = mapped_column(Integer, default=0)
    alias: Mapped[str] = mapped_column(String(100), nullable=True)

    gateway = relationship("Gateway", back_populates="terminals")
    
 
    # Terminal mode: "clock" (Clock In/Out), "access" (Достъп), "both" (Комбиниран)
    mode: Mapped[str] = mapped_column(String(20), default="both")


class Printer(Base):
    """Принтер свързан към gateway"""
    __tablename__ = "printers"

    id: Mapped[int]= mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    printer_type: Mapped[str] = mapped_column(String(20))  # "network", "usb", "windows"
    ip_address: Mapped[str] = mapped_column(String(50), nullable=True)
    port: Mapped[int] = mapped_column(Integer, default=9100)
    protocol: Mapped[str] = mapped_column(String(20))  # "raw", "lpd", "ipp"
    windows_share_name: Mapped[str] = mapped_column(String(100), nullable=True)
    manufacturer: Mapped[str] = mapped_column(String(50), nullable=True)
    model: Mapped[str] = mapped_column(String(100), nullable=True)
    gateway_id: Mapped[int] = mapped_column(Integer, ForeignKey("gateways.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    last_test: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True)
    last_error: Mapped[str] = mapped_column(Text, nullable=True)

    gateway = relationship("Gateway", back_populates="printers")


class GatewayHeartbeat(Base):
    """История на heartbeat събития"""
    __tablename__ = "gateway_heartbeats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    gateway_id: Mapped[int] = mapped_column(Integer, ForeignKey("gateways.id"))
    timestamp: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    status: Mapped[str] = mapped_column(String(20))  # "online", "offline"
    cpu_usage = Column(Float, nullable=True)
    memory_usage = Column(Float, nullable=True)
    terminal_count = Column(Integer, default=0)
    printer_count = Column(Integer, default=0)


class TerminalSession(Base):
    """Сесия на терминал - кой служител на коя станция работи"""
    __tablename__ = "terminal_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    terminal_id: Mapped[str] = mapped_column(String(100))  # Hardware UUID на терминала
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    workstation_id: Mapped[int] = mapped_column(Integer, ForeignKey("workstations.id"))
    started_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    ended_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True)
    gateway_id: Mapped[int] = mapped_column(Integer, ForeignKey("gateways.id"), nullable=True)

    employee = relationship("User")
    workstation = relationship("Workstation")
    task_logs = relationship("ProductionTaskLog", back_populates="session")


class ProductionTaskLog(Base):
    """Лог за изпълнението на задачите"""
    __tablename__ = "production_task_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("terminal_sessions.id"))
    production_order_id: Mapped[int] = mapped_column(Integer, ForeignKey("production_orders.id"))
    production_task_id: Mapped[int] = mapped_column(Integer, ForeignKey("production_tasks.id"))
    started_at: Mapped[DateTime] = mapped_column(DateTime, default=sofia_now)
    completed_at: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    quantity_produced: Mapped[int] = mapped_column(Integer, default=0)
    scrap_quantity: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20))  # "in_progress", "completed"

    session = relationship("TerminalSession", back_populates="task_logs")


class User(Base):
    __tablename__ = "users"

    id:Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=True) # Now optional
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    first_name: Mapped[str] = mapped_column(String, nullable=True)
    surname: Mapped[str] = mapped_column(String, nullable=True)
    last_name: Mapped[str] = mapped_column(String, nullable=True)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=True)
    address: Mapped[str] = mapped_column(String(255), nullable=True)
    egn: Mapped[str] = mapped_column(Text, nullable=True) # Encrypted
    birth_date: Mapped[datetime.date] = mapped_column(Date, nullable=True)
    iban: Mapped[str] = mapped_column(Text, nullable=True) # Encrypted
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    qr_secret: Mapped[str] = mapped_column(String(64), nullable=True) # Secret for dynamic QR generation
    is_qr_enabled: Mapped[bool] = mapped_column(Boolean, default=False) # Enable QR code access
    # Old String Fields (To be deprecated after migration)
    job_title: Mapped[str] = mapped_column(String, nullable=True)
    department: Mapped[str] = mapped_column(String, nullable=True)
    company: Mapped[str] = mapped_column(String, nullable=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), nullable=True)
    department_id: Mapped[int] = mapped_column(Integer, ForeignKey("departments.id", name="fk_user_department", use_alter=True), nullable=True)
    position_id: Mapped[int] = mapped_column(Integer, ForeignKey("positions.id"), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    last_login: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True)

    company_rel = relationship("Company", back_populates="users")
    department_rel = relationship("Department", back_populates="users", foreign_keys=[department_id])
    position_rel = relationship("Position", back_populates="users")
    
    
    # Security Fields
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True)
    qr_token: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=True)
    password_force_change: Mapped[bool] = mapped_column(Boolean, default=False)
    profile_picture: Mapped[str] = mapped_column(String, nullable=True) # Filename of the profile picture
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("roles.id"))

    # RBAC enhancements
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

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    refresh_token_jti: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    ip_address: Mapped[str] = mapped_column(String, nullable=True)
    user_agent: Mapped[str] = mapped_column(String, nullable=True)
    device_type: Mapped[str] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    expires_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    last_used_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)

    user = relationship("User", back_populates="sessions")


class AuthKey(Base):
    __tablename__ = "auth_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    kid: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    algorithm: Mapped[str] = mapped_column(String, default="HS256")
    secret: Mapped[str] = mapped_column(String, nullable=False)
    state: Mapped[str] = mapped_column(String, default="active") # active, legacy, expired
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)


class TimeLog(Base):
    __tablename__ = "timelogs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    start_time: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    end_time: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True)
    is_manual: Mapped[bool] = mapped_column(Boolean, default=False)
    break_duration_minutes: Mapped[int] = mapped_column(Integer, default=0)
    type: Mapped[str] = mapped_column(String, default='work')  # work, break, overtime, etc.
    notes: Mapped[str] = mapped_column(String, nullable=True)

    latitude: Mapped[Decimal] = mapped_column(Numeric(10, 6), nullable=True)
    longitude: Mapped[Decimal] = mapped_column(Numeric(10, 6), nullable=True)

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="timelogs")


class Payroll(Base):
    __tablename__ = "payrolls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    hourly_rate: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    monthly_salary: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=True)
    overtime_multiplier: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=1)
    standard_hours_per_day: Mapped[int] = mapped_column(Integer, default=8)
    currency: Mapped[str] = mapped_column(String, default="EUR")
    annual_leave_days: Mapped[int] = mapped_column(Integer, default=20)
    sick_leave_days: Mapped[int] = mapped_column(Integer, default=10)
    # Deductions
    tax_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=10.00)
    health_insurance_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=13.78)
    has_tax_deduction: Mapped[bool] = mapped_column(Boolean, default=False)
    has_health_insurance: Mapped[bool] = mapped_column(Boolean, default=False)

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    position_id: Mapped[int] = mapped_column(Integer, ForeignKey("positions.id"), nullable=True)

    user = relationship("User", back_populates="payrolls")
    position = relationship("Position", back_populates="payrolls")


class Payslip(Base):
    __tablename__ = "payslips"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))

    period_start: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    period_end: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)

    total_regular_hours: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    total_overtime_hours: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)

    regular_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    overtime_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    bonus_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    
    # ТРЗ разширение - нови полета
    night_work_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)  # Нощен труд
    trip_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)  # Командировъчни
    voucher_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)  # Ваучери за храна
    benefit_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)  # Фирмени придобивки
    sick_leave_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)  # Болнични

    # Existing detail fields
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    insurance_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    sick_days: Mapped[int] = mapped_column(Integer, default=0)
    leave_days: Mapped[int] = mapped_column(Integer, default=0)

    # Осигуровки - детайлни полета (Фаза 1)
    doo_employee: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)  # ДОО служител
    doo_employer: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)  # ДОО работodatel
    zo_employee: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)  # ЗО служител
    zo_employer: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)  # ЗО работodatel
    dzpo_employee: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)  # ДЗПO служител
    dzpo_employer: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)  # ДЗПО работodatel
    tzpb_employer: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)  # ТЗПБ само работodatel

    # ДДФЛ - детайлни полета (Фаза 1)
    tax_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=10.00)
    has_tax_deduction: Mapped[bool] = mapped_column(Boolean, default=False)
    # Данъци - детайлни полета (Фаза 2)
    gross_salary: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)  # Брутна заплата
    taxable_base: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)  # Данъчна база
    income_tax: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)  # ДДФЛ
    standard_deduction: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)  # Стандартно подобрения

    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)

    # Статус на плащане
    payment_status: Mapped[str] = mapped_column(String(20), default='pending')  # pending, paid, cancelled, sent_to_bank
    actual_payment_date: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True)  # Реална дата на превод
    payment_method: Mapped[str] = mapped_column(String(20), default='bank')  # bank, cash

    generated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)

    user = relationship("User", back_populates="payslips")


class InsuranceRateHistory(Base):
    """История на осигурителните ставки"""
    __tablename__ = "insurance_rate_history"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=True)  # null = цяла година
    category: Mapped[str] = mapped_column(String(20), nullable=False)  # "doo", "zo", "dzpo", "tzpb"
    employee_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    employer_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    effective_from: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[datetime.date] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)


class TaxRateHistory(Base):
    """История на данъчните ставки (ДДФЛ)"""
    __tablename__ = "tax_rate_history"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=True)  # null = цяла година
    rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)  # % напр. 10.00
    effective_from: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[datetime.date] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)


class TaxDeductionHistory(Base):
    """История на данъчните подобрения"""
    __tablename__ = "tax_deduction_history"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=True)
    deduction_type: Mapped[str] = mapped_column(String(50))  # "standard", "professional"
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    effective_from: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[datetime.date] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)


class Shift(Base):
    __tablename__ = "shifts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True)
    start_time: Mapped[datetime.time] = mapped_column(Time, nullable=False)
    end_time: Mapped[datetime.time] = mapped_column(Time, nullable=False)
    tolerance_minutes: Mapped[int] = mapped_column(Integer, default=15)
    break_duration_minutes: Mapped[int] = mapped_column(Integer, default=0)
    pay_multiplier: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=1.0)
    shift_type: Mapped[str] = mapped_column(String, default=ShiftType.REGULAR.value)

    schedules = relationship("WorkSchedule", back_populates="shift")


class WorkSchedule(Base):
    __tablename__ = "work_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    shift_id: Mapped[int] = mapped_column(Integer, ForeignKey("shifts.id"))

    user = relationship("User", back_populates="schedules")
    shift = relationship("Shift", back_populates="schedules")


class GlobalSetting(Base):
    __tablename__ = "global_settings"

    id:Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    key:Mapped[str] = mapped_column(String, unique=True, index=True)
    value:Mapped[str] = mapped_column(String)

class Module(Base):
    __tablename__ = "modules"

    id:Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code:Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True) # 'shifts', 'salaries', 'kiosk', 'integrations'
    is_enabled:Mapped[bool] = mapped_column(Boolean, default=True)
    name:Mapped[str] = mapped_column(String(100), nullable=False)
    description:Mapped[str] = mapped_column(String, nullable=True)
    updated_at:Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now, onupdate=sofia_now)


class ThrottleLog(Base):
    __tablename__ = "throttle_logs"

    id:Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id:Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    field_name:Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    called_at:Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now, nullable=False, index=True)
    ip_address:Mapped[Optional[str]] = mapped_column(String(45), nullable=True)


class PublicHoliday(Base):
    __tablename__ = "public_holidays"

    id:Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    date: Mapped[datetime.date] = mapped_column(Date, unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    local_name: Mapped[str] = mapped_column(String, nullable=True) # Името на български

class OrthodoxHoliday(Base):
    __tablename__ = "orthodox_holidays"

    id:Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    date: Mapped[datetime.date] = mapped_column(Date, unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    local_name: Mapped[str] = mapped_column(String, nullable=True)
    is_fixed: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)

class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id")) # Recipient
    message: Mapped[str] = mapped_column(String, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)

    user = relationship("User", back_populates="notifications")


class NotificationSetting(Base):
    __tablename__ = "notification_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String, nullable=False)  # shift_swap, leave_approved, etc.
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    push_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    email_template: Mapped[str] = mapped_column(Text, nullable=True)  # HTML template
    recipients: Mapped[list] = mapped_column(JSON, nullable=True)  # [{"type": "role", "value": "employee"}]
    interval_minutes: Mapped[int] = mapped_column(Integer, default=60)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_sent_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now, onupdate=sofia_now)


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id:Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id:Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    start_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    end_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    leave_type: Mapped[str] = mapped_column(String, nullable=False)  
    # leave_type values:
    # - annual_paid: Годишен платен отпуск
    # - sick: Болничен
    # - unpaid: Неплатен отпуск
    # - maternity: Майчинство (чл. 163 КТ - 410 дни)
    # - paternity: Бащинство (15 дни)
    # - parental: Родителски отпуск
    # - child_care: Отпуск за грижа за дете
    # - study: Ученически
    reason: Mapped[str] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="pending")  # pending, approved, rejected
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)

    # Optional: admin comment upon rejection
    admin_comment: Mapped[str] = mapped_column(String, nullable=True)
    employer_top_up: Mapped[bool] = mapped_column(Boolean, default=False) # Работодателят плаща разликата до 100%
    
    # За майчинство и родителски
    maternity_start_date: Mapped[datetime.date] = mapped_column(Date, nullable=True)
    expected_birth_date: Mapped[datetime.date] = mapped_column(Date, nullable=True)
    child_birth_date: Mapped[datetime.date] = mapped_column(Date, nullable=True)

    user = relationship("User", back_populates="leave_requests")


class LeaveBalance(Base):
    __tablename__ = "leave_balances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    total_days: Mapped[int] = mapped_column(Integer, default=20)
    used_days: Mapped[int] = mapped_column(Integer, default=0)

    user = relationship("User", back_populates="leave_balance")

class Bonus(Base):
    __tablename__ = "bonuses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    # We use a date to represent the month (e.g., 2023-10-01 for Oct 2023)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)

    user = relationship("User", back_populates="bonuses")


class MonthlyWorkDays(Base):
    __tablename__ = "monthly_work_days"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    days_count: Mapped[int] = mapped_column(Integer, nullable=False)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True) # Who performed it (null for system)
    action: Mapped[str] = mapped_column(String, nullable=False) # e.g. "UPDATE_PAYROLL", "DELETE_USER"
    target_type: Mapped[str] = mapped_column(String, nullable=True) # e.g. "User", "Shift", "Payroll"
    target_id: Mapped[int] = mapped_column(Integer, nullable=True) # ID of the affected resource
    details: Mapped[str] = mapped_column(String, nullable=True) # Detailed message or JSON string
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)

    user = relationship("User")

class ShiftSwapRequest(Base):
    __tablename__ = "shift_swap_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    requestor_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    target_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    requestor_schedule_id: Mapped[int] = mapped_column(Integer, ForeignKey("work_schedules.id"), nullable=False)
    target_schedule_id: Mapped[int] = mapped_column(Integer, ForeignKey("work_schedules.id"), nullable=False)

    # status: pending, accepted, rejected, approved, cancelled
    status: Mapped[str] = mapped_column(String, default="pending")

    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now, onupdate=sofia_now)

    requestor = relationship("User", foreign_keys=[requestor_id])
    target_user = relationship("User", foreign_keys=[target_user_id])
    requestor_schedule = relationship("WorkSchedule", foreign_keys=[requestor_schedule_id])
    target_schedule = relationship("WorkSchedule", foreign_keys=[target_schedule_id])

class ScheduleTemplate(Base):
    __tablename__ = "schedule_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)

    items = relationship("ScheduleTemplateItem", back_populates="template", cascade="all, delete-orphan")
    company = relationship("Company")

class ScheduleTemplateItem(Base):
    __tablename__ = "schedule_template_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    template_id: Mapped[int] = mapped_column(Integer, ForeignKey("schedule_templates.id"), nullable=False)
    day_index: Mapped[int] = mapped_column(Integer, nullable=False) # 0, 1, 2... for the rotation
    shift_id: Mapped[int] = mapped_column(Integer, ForeignKey("shifts.id"), nullable=True) # Null means a day off

    template = relationship("ScheduleTemplate", back_populates="items")
    shift = relationship("Shift")

class PushSubscription(Base):
    __tablename__ = "push_subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    endpoint: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    p256dh: Mapped[str] = mapped_column(String, nullable=False)
    auth: Mapped[str] = mapped_column(String, nullable=False)
    preferences: Mapped[dict] = mapped_column(JSON, default={}) # Stores settings like {"leaves": true, "swaps": true}
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)

    user = relationship("User", backref="push_subscriptions")

class UserDocument(Base):
    __tablename__ = "user_documents"

    id:Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    file_type: Mapped[str] = mapped_column(String, nullable=True) # e.g. 'contract', 'medical', 'other'
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False) # If true, user cannot download, only see
    uploaded_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)

    user = relationship("User", foreign_keys=[user_id], backref="documents")
    uploader = relationship("User", foreign_keys=[uploaded_by])

class APIKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False) # The admin who owns/created the key
    name: Mapped[str] = mapped_column(String, nullable=False) # e.g. "Microinvest Integration"
    key_prefix: Mapped[str] = mapped_column(String, nullable=False) # First 8 chars to identify it
    hashed_key: Mapped[str] = mapped_column(String, nullable=False)
    permissions: Mapped[list] = mapped_column(JSON, default=["read:all"]) # e.g. ["read:payroll", "write:logs"]
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    last_used_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True)

    owner = relationship("User", backref="api_keys")

class Webhook(Base):
    __tablename__ = "webhooks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    url: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    events: Mapped[list] = mapped_column(JSON, default=["*"]) # List of events like ["clock_in", "leave_approved"]
    secret: Mapped[str] = mapped_column(String, nullable=True) # To sign payload
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)

class WorkplaceLocation(Base):
    __tablename__ = "workplace_locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    address: Mapped[str] = mapped_column(String, nullable=False)
    latitude: Mapped[float] = mapped_column(Numeric(10, 8), nullable=False)
    longitude: Mapped[float] = mapped_column(Numeric(11, 8), nullable=False)
    radius_meters: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)

    company = relationship("Company", backref="workplace_locations")


# --- Confectionery Production & Warehouse Module ---

class StorageZone(Base):
    __tablename__ = "storage_zones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    temp_min: Mapped[float] = mapped_column(Numeric(5, 2), nullable=True)
    temp_max: Mapped[float] = mapped_column(Numeric(5, 2), nullable=True)
    description: Mapped[str] = mapped_column(String, nullable=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    # Phase 7 additions
    is_active: Mapped[bool] = mapped_column(Boolean, default=True) # Field 'active'
    asset_type: Mapped[str] = mapped_column(String(20), default="KMA") # 'ДМА' или 'КМА'
    zone_type: Mapped[str] = mapped_column(String(20), default="food") # 'хранителен' или 'не хранителен'

    company = relationship("Company", backref="storage_zones")

class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    eik: Mapped[str] = mapped_column(String(20), unique=True, nullable=True)
    vat_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=True)
    address: Mapped[str] = mapped_column(String, nullable=True)
    contact_person: Mapped[str] = mapped_column(String, nullable=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    email: Mapped[str] = mapped_column(String, nullable=True)
    mol: Mapped[str] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True)

    company = relationship("Company", backref="suppliers")


class Ingredient(Base):
    __tablename__ = "ingredients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    unit: Mapped[str] = mapped_column(String(20), default="kg") # kg, g, l, ml, br
    barcode: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=True)
    # Type: raw (суровина), semi_finished (заготовка), finished (готов продукт)
    product_type: Mapped[str] = mapped_column(String(20), default="raw")
    # Stock levels
    baseline_min_stock: Mapped[Decimal] = mapped_column(Numeric(12, 3), default=0)
    current_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=True) # Last purchase price
    # Auto-reorder fields
    min_quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=True)
    reorder_quantity: Mapped[float] = mapped_column(Numeric(12, 3), nullable=True)
    is_auto_reorder: Mapped[bool] = mapped_column(Boolean, default=False)
    preferred_supplier_id: Mapped[int] = mapped_column(Integer, ForeignKey("suppliers.id"), nullable=True)
    # Food safety
    storage_zone_id: Mapped[int] = mapped_column(Integer, ForeignKey("storage_zones.id"), nullable=True)
    is_perishable: Mapped[bool] = mapped_column(Boolean, default=True)
    expiry_warning_days: Mapped[int] = mapped_column(Integer, default=3)
    allergens: Mapped[list] = mapped_column(JSON, default=[]) # List of allergens
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)

    storage_zone = relationship("StorageZone")
    company = relationship("Company", backref="ingredients")
    preferred_supplier = relationship("Supplier")

class Batch(Base):
    __tablename__ = "batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ingredient_id: Mapped[int] = mapped_column(Integer, ForeignKey("ingredients.id", ondelete="CASCADE"), nullable=False)
    batch_number: Mapped[str] = mapped_column(String(100), index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    unit_value: Mapped[float] = mapped_column(Numeric(12, 3), nullable=True) # e.g., 1.0 for 1L if unit is 'br'
    production_date: Mapped[datetime.date] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[datetime.date] = mapped_column(Date, nullable=False, index=True)
    price_no_vat: Mapped[float] = mapped_column(Numeric(12, 2), nullable=True)
    vat_percent: Mapped[float] = mapped_column(Numeric(5, 2), default=20.0)
    price_with_vat: Mapped[float] = mapped_column(Numeric(12, 2), nullable=True)
    is_stock_receipt: Mapped[bool] = mapped_column(Boolean, default=False) # стокова разписка
    invoice_number: Mapped[str] = mapped_column(String(100), nullable=True)
    invoice_date: Mapped[datetime.date] = mapped_column(Date, nullable=True)
    received_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active") # active, quarantined, expired, depleted, scrap
    received_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    supplier_id: Mapped[int] = mapped_column(Integer, ForeignKey("suppliers.id"), nullable=True)
    storage_zone_id: Mapped[int] = mapped_column(Integer, ForeignKey("storage_zones.id"), nullable=True)

    ingredient = relationship("Ingredient", backref="batches")
    supplier = relationship("Supplier")
    receiver = relationship("User", foreign_keys=[received_by])

class StockConsumptionLog(Base):
    """Лог за изразходване на стока"""
    __tablename__ = "stock_consumption_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ingredient_id: Mapped[int] = mapped_column(Integer, ForeignKey("ingredients.id", ondelete="CASCADE"), nullable=False)
    batch_id: Mapped[int] = mapped_column(Integer, ForeignKey("batches.id", ondelete="CASCADE"), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    price_per_unit: Mapped[Optional[float]] = mapped_column(Numeric(12, 4), nullable=True)  # Цена на единица от партидата
    total_price: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)  # Обща стойност
    reason: Mapped[str] = mapped_column(String(50), nullable=False)  # "manual", "production", "expiry", "damaged", "quality_check"
    production_order_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("production_orders.id", ondelete="SET NULL"), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)

    ingredient: Mapped["Ingredient"] = relationship("Ingredient")
    batch: Mapped["Batch"] = relationship("Batch")
    production_order: Mapped[Optional["ProductionOrder"]] = relationship("ProductionOrder")
    creator: Mapped["User"] = relationship("User")

class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=True)  # Категория на рецептата
    description: Mapped[str] = mapped_column(String, nullable=True)
    yield_quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=1.0)
    yield_unit: Mapped[str] = mapped_column(String(20), default="br")
    shelf_life_days: Mapped[int] = mapped_column(Integer, default=7)  # Срок на годност в хладилник
    shelf_life_frozen_days: Mapped[int] = mapped_column(Integer, default=30)  # Срок на годност замразена
    default_pieces: Mapped[int] = mapped_column(Integer, default=12)  # Първоначален брой парчета
    production_time_days: Mapped[int] = mapped_column(Integer, default=1) # Фаза 7: срок за изпълнение
    production_deadline_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Колко дни преди expiry да се произведе
    standard_quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=1.0) # Стандартно количество за производство
    instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    selling_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)  # Продажна цена
    cost_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)  # Себестойност (изчислена)
    markup_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)  # Марж %
    premium_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)  # Надценка (лв)
    portions: Mapped[int] = mapped_column(Integer, default=1)  # Брой порции
    last_price_update: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)  # Кога е обновена цената
    price_calculated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)  # Кога е изчислена себестойността

    company = relationship("Company", backref="recipes")
    sections = relationship("RecipeSection", back_populates="recipe", cascade="all, delete-orphan")
    ingredients = relationship("RecipeIngredient", back_populates="recipe_legacy", cascade="all, delete-orphan")
    steps = relationship("RecipeStep", back_populates="recipe_legacy", cascade="all, delete-orphan")


class RecipeSection(Base):
    __tablename__ = "recipe_sections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    recipe_id: Mapped[int] = mapped_column(Integer, ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False)
    section_type: Mapped[str] = mapped_column(String(20), nullable=False)  # "dough", "cream", "decoration"
    name: Mapped[str] = mapped_column(String(255), nullable=False)  # "Блат - Торта Шоколад"
    shelf_life_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Срок на заготовката
    waste_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0.0)  # Фира %
    section_order: Mapped[int] = mapped_column(Integer, default=0)  # 1, 2, 3

    recipe = relationship("Recipe", back_populates="sections")
    ingredients = relationship("RecipeIngredient", back_populates="section", cascade="all, delete-orphan")
    steps = relationship("RecipeStep", back_populates="section", cascade="all, delete-orphan")

class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    section_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("recipe_sections.id", ondelete="CASCADE"), nullable=True)
    recipe_id: Mapped[int] = mapped_column(Integer, ForeignKey("recipes.id", ondelete="CASCADE"), nullable=True)  # За съвместимost
    ingredient_id: Mapped[int] = mapped_column(Integer, ForeignKey("ingredients.id"), nullable=False)
    workstation_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("workstations.id"), nullable=True) # За коя станция е продукта
    quantity_gross: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False) # amount taken from stock
    quantity_net: Mapped[Decimal] = mapped_column(Numeric(12, 3), default=0.0)
    waste_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0.0)

    section = relationship("RecipeSection", back_populates="ingredients")
    recipe_legacy = relationship("Recipe", back_populates="ingredients", foreign_keys=[recipe_id])
    ingredient = relationship("Ingredient")
    workstation = relationship("Workstation")

class Workstation(Base):
    __tablename__ = "workstations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)

    company = relationship("Company", backref="workstations")

class RecipeStep(Base):
    __tablename__ = "recipe_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    section_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("recipe_sections.id", ondelete="CASCADE"), nullable=True)
    recipe_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("recipes.id", ondelete="CASCADE"), nullable=True)  # За съвместимost
    workstation_id: Mapped[int] = mapped_column(Integer, ForeignKey("workstations.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    step_order: Mapped[int] = mapped_column(Integer, default=0)
    estimated_duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    section = relationship("RecipeSection", back_populates="steps")
    recipe_legacy = relationship("Recipe", back_populates="steps", foreign_keys=[recipe_id])
    workstation = relationship("Workstation")

class ProductionOrder(Base):
    __tablename__ = "production_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    recipe_id: Mapped[int] = mapped_column(Integer, ForeignKey("recipes.id"), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    due_date: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    completed_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    confirmed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    confirmed_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    production_deadline: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)

    recipe = relationship("Recipe")
    company = relationship("Company")
    creator = relationship("User", foreign_keys=[created_by])
    finisher = relationship("User", foreign_keys=[completed_by])
    confirmer = relationship("User", foreign_keys=[confirmed_by])
    tasks = relationship("ProductionTask", back_populates="order", cascade="all, delete-orphan")

class ProductionTask(Base):
    __tablename__ = "production_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("production_orders.id", ondelete="CASCADE"), nullable=False)
    workstation_id: Mapped[int] = mapped_column(Integer, ForeignKey("workstations.id"), nullable=False)
    step_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("recipe_steps.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    is_scrap: Mapped[bool] = mapped_column(Boolean, default=False)
    scrap_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True) # Value + 26% 
    started_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    assigned_user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    
    order = relationship("ProductionOrder", back_populates="tasks")
    workstation = relationship("Workstation")
    step = relationship("RecipeStep")
    assigned_user = relationship("User")


class ProductionScrapLog(Base):
    """Лог за брак на производствени задачи"""
    __tablename__ = "production_scrap_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    task_id: Mapped[int] = mapped_column(Integer, ForeignKey("production_tasks.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    
    task = relationship("ProductionTask")
    user = relationship("User")


class PriceHistory(Base):
    """История на промените на цените на рецепти"""
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    recipe_id: Mapped[int] = mapped_column(Integer, ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False)
    old_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    new_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    old_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    new_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    old_markup: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    new_markup: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    old_premium: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    new_premium: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    changed_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    changed_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    recipe = relationship("Recipe")
    user = relationship("User")


class ProductionRecord(Base):
    """Запис за проследяемост на произведената продукция"""
    __tablename__ = "production_records"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("production_orders.id", ondelete="CASCADE"), nullable=False)
    confirmed_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    confirmed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, default=sofia_now)
    expiry_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)  # Изчислена дата на годност (от рецептата)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)

    order = relationship("ProductionOrder")
    confirmer = relationship("User")
    ingredients = relationship("ProductionRecordIngredient", back_populates="record", cascade="all, delete-orphan")
    workers = relationship("ProductionRecordWorker", back_populates="record", cascade="all, delete-orphan")


class ProductionRecordIngredient(Base):
    """Суровина/продукт използван в производството с партида и срок на годност"""
    __tablename__ = "production_record_ingredients"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    record_id: Mapped[int] = mapped_column(Integer, ForeignKey("production_records.id", ondelete="CASCADE"), nullable=False)
    ingredient_id: Mapped[int] = mapped_column(Integer, ForeignKey("ingredients.id"), nullable=False)
    batch_number: Mapped[str] = mapped_column(String(100), nullable=False)
    expiry_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    quantity_used: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    unit: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    record = relationship("ProductionRecord", back_populates="ingredients")
    ingredient = relationship("Ingredient")


class ProductionRecordWorker(Base):
    """Работник работил по поръчката"""
    __tablename__ = "production_record_workers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    record_id: Mapped[int] = mapped_column(Integer, ForeignKey("production_records.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    workstation_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("workstations.id"), nullable=True)
    task_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("production_tasks.id"), nullable=True)
    started_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)

    record = relationship("ProductionRecord", back_populates="workers")
    user = relationship("User")
    workstation = relationship("Workstation")
    task = relationship("ProductionTask")


class InventorySession(Base):
    """Инвентаризация на склада"""
    __tablename__ = "inventory_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    started_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    started_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active, completed
    protocol_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    company = relationship("Company")
    starter = relationship("User", foreign_keys=[started_by])
    items = relationship("InventoryItem", back_populates="session", cascade="all, delete-orphan")


class InventoryItem(Base):
    """Артикул при инвентаризация"""
    __tablename__ = "inventory_items"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("inventory_sessions.id", ondelete="CASCADE"), nullable=False)
    ingredient_id: Mapped[int] = mapped_column(Integer, ForeignKey("ingredients.id"), nullable=False)
    found_quantity: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 3), nullable=True)  # Намерено количество
    system_quantity: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 3), nullable=True)  # Количество по система
    difference: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 3), nullable=True)  # Разлика
    adjusted: Mapped[bool] = mapped_column(Boolean, default=False)

    session = relationship("InventorySession", back_populates="items")
    ingredient = relationship("Ingredient")


class AdvancePayment(Base):
    """Еднократни авансови плащания преди заплата"""
    __tablename__ = "advance_payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    payment_date: Mapped[datetime.date] = mapped_column(DateTime, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)

    user = relationship("User")


class ServiceLoan(Base):
    """Служебен аванс (заем), удържан на месечни вноски"""
    __tablename__ = "service_loans"
    id:Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    installment_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    remaining_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    installments_count: Mapped[int] = mapped_column (Integer, nullable=False) 
    installments_paid: Mapped[int] = mapped_column(Integer, default=0) 
    start_date: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)

    user = relationship("User")


# Google Calendar Integration Models
class GoogleCalendarAccount(Base):
    __tablename__ = "google_calendar_accounts"

    id:Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    google_user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    access_token: Mapped[str] = mapped_column(String, nullable=True)
    refresh_token: Mapped[str] = mapped_column(String, nullable=False)
    token_expires_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[Boolean] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True, onupdate=sofia_now)

    user = relationship("User", backref="google_calendar_accounts")
    sync_settings = relationship("GoogleCalendarSyncSettings", back_populates="account", cascade="all, delete-orphan", uselist=False)
    events = relationship("GoogleCalendarEvent", back_populates="account", cascade="all, delete-orphan")


class GoogleCalendarSyncSettings(Base):
    __tablename__ = "google_calendar_sync_settings"

    id:Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey("google_calendar_accounts.id", ondelete="CASCADE"), nullable=False)
    calendar_id: Mapped[str] = mapped_column(String(255), nullable=False, default='primary')
    sync_work_schedules: Mapped[Boolean] = mapped_column(Boolean, default=True)
    sync_time_logs: Mapped[Boolean] = mapped_column(Boolean, default=False)
    sync_leave_requests: Mapped[Boolean] = mapped_column(Boolean, default=True)
    sync_public_holidays: Mapped[Boolean] = mapped_column(Boolean, default=True)
    sync_direction: Mapped[str] = mapped_column(String(20), default='to_google')  # 'to_google', 'from_google', 'bidirectional'
    sync_frequency_minutes: Mapped[int] = mapped_column(Integer, default=15)
    privacy_level: Mapped[str] = mapped_column(String(20), default='title_only')  # 'full', 'title_only', 'busy_only'
    default_event_visibility: Mapped[str] = mapped_column(String(20), default='default')  # 'default', 'public', 'private'
    timezone: Mapped[str] = mapped_column(String(50), default='Europe/Sofia')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True, onupdate=sofia_now)
    
    account = relationship("GoogleCalendarAccount", back_populates="sync_settings")


class GoogleCalendarEvent(Base):
    __tablename__ = "google_calendar_events"

    id:Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey("google_calendar_accounts.id", ondelete="CASCADE"), nullable=False)
    google_event_id: Mapped[str] = mapped_column(String(255), nullable=False)
    google_calendar_id: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'work_schedule', 'time_log', 'leave_request', 'holiday'
    source_id: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    start_time: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    is_all_day: Mapped[Boolean] = mapped_column(Boolean, default=False)
    google_updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True)
    last_sync_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    sync_status: Mapped[str] = mapped_column(String(20), default='synced')  # 'synced', 'pending', 'error', 'deleted'
    sync_error: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)

    account = relationship("GoogleCalendarAccount", back_populates="events")


class GoogleSyncLog(Base):
    __tablename__ = "google_sync_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey("google_calendar_accounts.id", ondelete="CASCADE"), nullable=False)
    sync_type: Mapped[str]= mapped_column(String(50), nullable=False)  # 'full_sync', 'incremental', 'error_retry'
    events_processed: Mapped[int] = mapped_column(Integer, default=0)
    events_created: Mapped[int] = mapped_column(Integer, default=0)
    events_updated: Mapped[int] = mapped_column(Integer, default=0)
    events_deleted: Mapped[int] = mapped_column(Integer, default=0)
    errors_count: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    completed_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default='running')  # 'running', 'completed', 'failed'
    error_details: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    
    account = relationship("GoogleCalendarAccount")


# Enhanced Payroll System Models
class PayrollPaymentSchedule(Base):
    __tablename__ = "payroll_payment_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    payment_day: Mapped[int] = mapped_column(Integer, nullable=False)  # 25-то число например
    payment_month_offset: Mapped[int] = mapped_column(Integer, default=0)  # 0 за текущия месец, 1 за следващия
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True, onupdate=sofia_now)
    
    company = relationship("Company", backref="payment_schedules")

    
class PayrollDeduction(Base):
    __tablename__ = "payroll_deductions"

    id: Mapped[int]= mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    deduction_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'fixed', 'percentage', 'conditional'
    amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    percentage: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=0) # Поредност на удържане
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    apply_to_all: Mapped[bool] = mapped_column(Boolean, default=True)
    employee_ids: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # Specific employees as array
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True, onupdate=sofia_now)
    
    company = relationship("Company", backref="payroll_deductions")


class SickLeaveRecord(Base):
    __tablename__ = "sick_leave_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    start_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    end_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    sick_leave_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'general', 'work_related', 'maternity', 'child_care'
    is_paid_by_noi: Mapped[bool] = mapped_column(Boolean, default=True)
    employer_payment_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=75.00)  # 75% от работодателя
    daily_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)  # Дневно обезщетение
    total_days: Mapped[int] = mapped_column(Integer, nullable=False)
    noi_payment_days: Mapped[int] = mapped_column(Integer, default=0)  # Дни платени от НОЙ
    employer_payment_days: Mapped[int] = mapped_column(Integer, default=0)  # Дни платени от работодателя
    medical_document_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default='active')  # 'active', 'expired', 'cancelled'
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True, onupdate=sofia_now)

    user = relationship("User", backref="sick_leave_records")


class NOIPaymentDays(Base):
    __tablename__ = "noi_payment_days"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    total_noi_days_available: Mapped[int] = mapped_column(Integer, default=30)  # Според Кодекса на труда
    noi_days_used: Mapped[int] = mapped_column(Integer, default=0)
    noi_days_remaining: Mapped[int] = mapped_column(Integer, nullable=False)  # Computed column
    employer_payment_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=75.00)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True, onupdate=sofia_now)

    user = relationship("User", backref="noi_payment_days")


class WebAuthnChallenge(Base):
    __tablename__ = "webauthn_challenges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True) # Optional for login
    challenge: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)


class WebAuthnCredential(Base):
    __tablename__ = "webauthn_credentials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    credential_id: Mapped[bytes] = mapped_column(LargeBinary, unique=True, index=True, nullable=False)
    public_key: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    sign_count: Mapped[int] = mapped_column(Integer, default=0)
    transports: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # comma separated list
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    last_used_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    friendly_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    user = relationship("User", backref="webauthn_credentials")


class EmploymentContract(Base):
    __tablename__ = "employment_contracts"

    id:Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    # user_id е nullable заради TRZ договори - може да се създаде договор ПРЕДИ потребителят да е регистриран
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    contract_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "full_time", "part_time", "contractor", "internship"
    contract_number: Mapped[str] = mapped_column(String(50), nullable=True)  # Уникален номер на договора
    start_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    end_date: Mapped[datetime.date] = mapped_column(Date, nullable=True)  # For fixed-term contracts
    base_salary: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=True)
    work_hours_per_week: Mapped[int] = mapped_column(Integer, default=40)
    probation_months: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    salary_calculation_type: Mapped[str] = mapped_column(String(20), default='gross')  # 'gross', 'net'
    salary_installments_count: Mapped[int] = mapped_column(Integer, default=1)  # Брой плащания (вноски) на заплатата
    monthly_advance_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0) # Фиксиран месечен аванс
    tax_resident: Mapped[bool] = mapped_column(Boolean, default=True)
    insurance_contributor: Mapped[bool] = mapped_column(Boolean, default=True)  # Whether employee pays insurance
    has_income_tax: Mapped[bool] = mapped_column(Boolean, default=True) # Whether to withhold income tax
    # ТРЗ разширение - ставки за надбавки
    payment_day: Mapped[int] = mapped_column(Integer, default=25)  # Ден от месеца за изплащане
    experience_start_date: Mapped[datetime.date] = mapped_column(Date, nullable=True)  # Начало на трудов стаж за "клас"
    night_work_rate: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=0.5)  # 50% надбавка за нощен труд
    overtime_rate: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=1.5)  # 50% множител за извънреден
    holiday_rate: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=2.0)  # 100% множител за празници
    work_class: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # Трудов клас (I, II, III, IV)
    dangerous_work: Mapped[bool] = mapped_column(Boolean, default=False)  # Вредни условия на труд
    # Връзка към шаблон
    template_id: Mapped[int] = mapped_column(Integer, ForeignKey("contract_templates.id", ondelete="SET NULL"), nullable=True)
    position_id: Mapped[int] = mapped_column(Integer, ForeignKey("positions.id", ondelete="SET NULL"), nullable=True)
    department_id: Mapped[int] = mapped_column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    # Клаузи - JSON string с ID-та на клаузи
    clause_ids: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Нови полета за трудов договор (преди регистрация)
    employee_name: Mapped[str] = mapped_column(String(200), nullable=True)  # Име на служителя (преди регистрация)
    employee_egn: Mapped[str] = mapped_column(String(10), nullable=True)  # ЕГН (преди регистрация)
    status: Mapped[str] = mapped_column(String(20), default='draft')  # draft/signed/linked
    signed_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True)  # Дата на подписване
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True, onupdate=sofia_now)

    user = relationship("User", backref="employment_contracts")
    company = relationship("Company", backref="employment_contracts")
    position = relationship("Position", backref="employment_contracts")
    department = relationship("Department", backref="employment_contracts")


class ContractAnnex(Base):
    """Допълнително споразумение (чл. 119 КТ)"""
    __tablename__ = "contract_annexes"

    id:Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    contract_id: Mapped[int] = mapped_column(Integer, ForeignKey("employment_contracts.id", ondelete="CASCADE"), nullable=False)
    annex_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    effective_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    # Промени (всички са незадължителни, ако не се променят)
    base_salary: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    position_id: Mapped[int] = mapped_column(Integer, ForeignKey("positions.id", ondelete="SET NULL"), nullable=True)
    work_hours_per_week: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    probation_months: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # Нови ТРЗ ставки
    night_work_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2), nullable=True)
    overtime_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2), nullable=True)
    holiday_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2), nullable=True)
    work_class: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    # Статус
    is_signed: Mapped[bool] = mapped_column(Boolean, default=False)
    signed_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True) 
    # Нови полета за e-signature и шаблони
    status: Mapped[str] = mapped_column(String(20), default="draft")
    template_id: Mapped[int] = mapped_column(Integer, ForeignKey("annex_templates.id", ondelete="SET NULL"), nullable=True)
    change_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    change_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    signature_requested_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True)
    signed_by_employee: Mapped[bool] = mapped_column(Boolean, default=False)
    signed_by_employee_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True)
    signed_by_employer: Mapped[bool] = mapped_column(Boolean, default=False)
    signed_by_employer_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True, onupdate=sofia_now)

    contract = relationship("EmploymentContract", backref="annexes")
    position = relationship("Position")


class ContractTemplate(Base):
    """Шаблон за трудов договор"""
    __tablename__ = "contract_templates"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    contract_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # Заплащане
    base_salary: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    work_hours_per_week: Mapped[int] = mapped_column(Integer, default=40)
    probation_months: Mapped[int] = mapped_column(Integer, default=6)
    salary_calculation_type: Mapped[str] = mapped_column(String(20), default='gross')
    payment_day: Mapped[int] = mapped_column(Integer, default=25)
    night_work_rate: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=0.5)
    overtime_rate: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=1.5)
    holiday_rate: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=2.0)
    work_class: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    # Длъжност и отдел
    position_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("positions.id", ondelete="SET NULL"), nullable=True)
    department_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True, onupdate=sofia_now)
    
    company = relationship("Company", backref="contract_templates")
    position = relationship("Position", backref="contract_templates")
    department = relationship("Department", backref="contract_templates")
    versions = relationship("ContractTemplateVersion", back_populates="template", cascade="all, delete-orphan")
    clauses = relationship("ContractTemplateClause", back_populates="template", cascade="all, delete-orphan")


class ContractTemplateVersion(Base):
    """Версия на шаблон за договор"""
    __tablename__ = "contract_template_versions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    template_id: Mapped[int] = mapped_column(Integer, ForeignKey("contract_templates.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    contract_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # Заплащане
    base_salary: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    work_hours_per_week: Mapped[int] = mapped_column(Integer, nullable=False)
    probation_months: Mapped[int] = mapped_column(Integer, nullable=False)
    salary_calculation_type: Mapped[str] = mapped_column(String(20), nullable=False)
    payment_day: Mapped[int] = mapped_column(Integer, nullable=False)
    night_work_rate: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    overtime_rate: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    holiday_rate: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    work_class: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    # Длъжност и отдел
    position_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("positions.id", ondelete="SET NULL"), nullable=True)
    department_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    change_note: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    template = relationship("ContractTemplate", back_populates="versions")
    position = relationship("Position", back_populates="contract_template_versions")
    department = relationship("Department", back_populates="contract_template_versions")
    sections = relationship("ContractTemplateSection", back_populates="version", cascade="all, delete-orphan")


class ContractTemplateClause(Base):
    """Асоциация между шаблон на договор и клаузи"""
    __tablename__ = "contract_template_clauses"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    template_id: Mapped[int] = mapped_column(Integer, ForeignKey("contract_templates.id", ondelete="CASCADE"), nullable=False)
    clause_id: Mapped[int] = mapped_column(Integer, ForeignKey("clause_templates.id", ondelete="CASCADE"), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    
    template = relationship("ContractTemplate")
    clause = relationship("ClauseTemplate")


class ContractTemplateSection(Base):
    """Секция/клауза в шаблон за договор"""
    __tablename__ = "contract_template_sections"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    template_id: Mapped[int] = mapped_column(Integer, ForeignKey("contract_templates.id", ondelete="CASCADE"), nullable=False)
    version_id: Mapped[int] = mapped_column(Integer, ForeignKey("contract_template_versions.id", ondelete="CASCADE"), nullable=False)
    
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    is_required: Mapped[bool] = mapped_column(Boolean, default=False)
    
    version = relationship("ContractTemplateVersion", back_populates="sections")


class AnnexTemplate(Base):
    """Шаблон за допълнително споразумение"""
    __tablename__ = "annex_templates"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    change_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    new_base_salary: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    new_work_hours_per_week: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    new_night_work_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2), nullable=True)
    new_overtime_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2), nullable=True)
    new_holiday_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True, onupdate=sofia_now)
    
    company = relationship("Company", backref="annex_templates")
    versions = relationship("AnnexTemplateVersion", back_populates="template", cascade="all, delete-orphan")


class AnnexTemplateVersion(Base):
    """Версия на шаблон за анекс"""
    __tablename__ = "annex_template_versions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    template_id: Mapped[int] = mapped_column(Integer, ForeignKey("annex_templates.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    change_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    new_base_salary: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    new_work_hours_per_week: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    new_night_work_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2), nullable=True)
    new_overtime_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2), nullable=True)
    new_holiday_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2), nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    change_note: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    template = relationship("AnnexTemplate", back_populates="versions")
    sections = relationship("AnnexTemplateSection", back_populates="version", cascade="all, delete-orphan")


class AnnexTemplateSection(Base):
    """Секция/клауза в шаблон за анекс"""
    __tablename__ = "annex_template_sections"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    template_id: Mapped[int] = mapped_column(Integer, ForeignKey("annex_templates.id", ondelete="CASCADE"), nullable=False)
    version_id: Mapped[int] = mapped_column(Integer, ForeignKey("annex_template_versions.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    is_required: Mapped[bool] = mapped_column(Boolean, default=False)
    
    version = relationship("AnnexTemplateVersion", back_populates="sections")


class ClauseTemplate(Base):
    """Библиотека от преизползваеми клаузи"""
    __tablename__ = "clause_templates"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True, onupdate=sofia_now)
    
    company = relationship("Company", backref="clause_templates")


class PayrollPeriod(Base):
    __tablename__ = "payroll_periods"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    start_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    end_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default='open')  # 'open', 'processing', 'closed'
    period_type: Mapped[str] = mapped_column(String(20), default='monthly')  # 'monthly', 'quarterly', 'annual'
    year_bonus_month: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Месец за 13-а заплата
    processing_date: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True)
    payment_date: Mapped[datetime.date] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    
    company = relationship("Company", backref="payroll_periods")


class NightWorkBonus(Base):
    """Нощен труд"""
    __tablename__ = "night_work_bonuses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    period_id: Mapped[int] = mapped_column(Integer, ForeignKey("payroll_periods.id", ondelete="SET NULL"), nullable=True)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    hours: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    hourly_rate: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True, onupdate=sofia_now)

    user = relationship("User", backref="night_work_bonuses")
    period = relationship("PayrollPeriod", backref="night_work_bonuses")


class OvertimeWork(Base):
    """Извънреден труд"""
    __tablename__ = "overtime_works"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    period_id: Mapped[int] = mapped_column(Integer, ForeignKey("payroll_periods.id", ondelete="SET NULL"), nullable=True)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    hours: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    hourly_rate: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    multiplier: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=1.5)  # 1.5 за първи 2 часа, 2.0 за над 2 часа
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True, onupdate=sofia_now)

    user = relationship("User", backref="overtime_works")
    period = relationship("PayrollPeriod", backref="overtime_works")


class WorkOnHoliday(Base):
    """Труд по празници"""
    __tablename__ = "work_on_holidays"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    period_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("payroll_periods.id", ondelete="SET NULL"), nullable=True)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    hours: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    hourly_rate: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    multiplier: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=2.0)  # 100% надбавка
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True, onupdate=sofia_now)

    user = relationship("User", backref="work_on_holidays")
    period = relationship("PayrollPeriod", backref="work_on_holidays")


class BusinessTripStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"


class BusinessTrip(Base):
    """Командировка"""
    __tablename__ = "business_trips"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    period_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("payroll_periods.id", ondelete="SET NULL"), nullable=True)
    department_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    destination: Mapped[str] = mapped_column(String(255), nullable=False)
    start_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    end_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    daily_allowance: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=40.00)  # Дневни
    accommodation: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)  # Нощувки
    transport: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)  # Транспорт
    other_expenses: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)  # Други разходи
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    status: Mapped[str] = mapped_column(String(20), default=BusinessTripStatus.PENDING.value)
    approved_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    approved_notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True, onupdate=sofia_now)

    user = relationship("User", foreign_keys=[user_id], backref="business_trips")
    period = relationship("PayrollPeriod", backref="business_trips")
    department = relationship("Department", backref="business_trips")
    approved_by = relationship("User", foreign_keys=[approved_by_id])


class WorkExperience(Base):
    """Трудов стаж"""
    __tablename__ = "work_experiences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    company_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    start_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)  # NULL = продължава
    years: Mapped[int] = mapped_column(Integer, default=0)
    months: Mapped[int] = mapped_column(Integer, default=0)
    class_level: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # I, II, III, IV
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True, onupdate=sofia_now)

    user = relationship("User", backref="work_experiences")
    company = relationship("Company", backref="work_experiences")


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    payslip_id: Mapped[int] = mapped_column(Integer, ForeignKey("payslips.id", ondelete="CASCADE"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    payment_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    payment_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # 'bank_transfer', 'cash', 'check'
    status: Mapped[str] = mapped_column(String(20), default='pending')  # 'pending', 'completed', 'failed'
    reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Bank reference, receipt number
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)

    payslip = relationship("Payslip", backref="payments")


# Configuration Framework Models
class ConfigurationCategory(Base):
    __tablename__ = "configuration_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)  # System vs user-defined
    company_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)

    company = relationship("Company", backref="configuration_categories")
    fields = relationship("ConfigurationField", back_populates="category", cascade="all, delete-orphan")


class ConfigurationField(Base):
    __tablename__ = "configuration_fields"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("configuration_categories.id", ondelete="CASCADE"), nullable=False)
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    field_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'text', 'number', 'select', 'checkbox', 'date'
    validation_rules: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # {"required": true, "min": 0, "max": 100}
    default_value: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    options: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # For select fields
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)

    category = relationship("ConfigurationCategory", back_populates="fields")
    company_configurations = relationship("CompanyConfiguration", back_populates="field", cascade="all, delete-orphan")


class CompanyConfiguration(Base):
    __tablename__ = "company_configurations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    field_id: Mapped[int] = mapped_column(Integer, ForeignKey("configuration_fields.id", ondelete="CASCADE"), nullable=False)
    value: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    updated_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now, onupdate=sofia_now)

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
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # incoming / outgoing
    document_type: Mapped[str] = mapped_column(String(50), default="ФАКТУРА")  # ФАКТУРА, ПРОФОРМА, КОРЕКЦИЯ
    griff: Mapped[str] = mapped_column(String(20), default="ОРИГИНАЛ")  # ОРИГИНАЛ, КОПИЕ
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Основание за сделката
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    # За входящи фактури
    supplier_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("suppliers.id"), nullable=True)
    batch_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("batches.id"), nullable=True)  # Свързана партида
    
    # За изходящи фактури
    client_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    client_eik: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    client_address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    client_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    client_email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    client_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Суми
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    discount_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    vat_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=20.0)
    vat_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    
    # Плащане и доставка
    payment_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Банков превод, В брой, Карта
    delivery_method: Mapped[Optional[str]] = mapped_column(String(50), default="Доставка до адрес")  # Доставка до адрес, Взимане от склад, Куриер
    due_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    payment_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft, sent, paid, overdue, cancelled
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True, onupdate=sofia_now)
    
    company = relationship("Company", backref="invoices")
    supplier = relationship("Supplier", backref="invoices")
    batch = relationship("Batch", backref="invoices")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by])


class InvoiceItem(Base):
    __tablename__ = "invoice_items"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    invoice_id: Mapped[int] = mapped_column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    # За входящи фактури - свързаност със склада
    ingredient_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("ingredients.id"), nullable=True)
    batch_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("batches.id"), nullable=True)
    # За изходящи фактури - свободни артикули
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    unit: Mapped[Optional[str]] = mapped_column(String(20), default="br")
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    unit_price_with_vat: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    discount_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    expiration_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    batch_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    invoice = relationship("Invoice", back_populates="items")
    ingredient = relationship("Ingredient", backref="invoice_items")
    batch = relationship("Batch", backref="invoice_items")


class CashJournalEntry(Base):
    __tablename__ = "cash_journal_entries"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False, index=True)
    operation_type: Mapped[str] = mapped_column(String(20), nullable=False)  # income / expense
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reference_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # invoice / manual / other
    reference_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    payment_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Банков превод, В брой, Карта
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    
    company = relationship("Company", backref="cash_journal_entries")
    creator = relationship("User", foreign_keys=[created_by])


class OperationLog(Base):
    __tablename__ = "operation_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    timestamp: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now, nullable=False, index=True)
    operation: Mapped[str] = mapped_column(String(20), nullable=False)  # create / update / delete
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # invoice / cash_journal / etc
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    changes: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # JSON with the changes made
    
    user = relationship("User", foreign_keys=[user_id])


class DailySummary(Base):
    __tablename__ = "daily_summaries"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    date: Mapped[datetime.date] = mapped_column(Date, unique=True, nullable=False, index=True)
    # Invoice counts
    invoices_count: Mapped[int] = mapped_column(Integer, default=0)
    incoming_invoices_count: Mapped[int] = mapped_column(Integer, default=0)
    outgoing_invoices_count: Mapped[int] = mapped_column(Integer, default=0)
    # Invoice totals
    invoices_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    incoming_invoices_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    outgoing_invoices_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    # Cash operations
    cash_income: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    cash_expense: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    cash_balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    # VAT
    vat_collected: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    vat_paid: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    # Payment status
    paid_invoices_count: Mapped[int] = mapped_column(Integer, default=0)
    unpaid_invoices_count: Mapped[int] = mapped_column(Integer, default=0)
    overdue_invoices_count: Mapped[int] = mapped_column(Integer, default=0)
    
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    
    company = relationship("Company", backref="daily_summaries")


class MonthlySummary(Base):
    __tablename__ = "monthly_summaries"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    month: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-12
    # Invoice counts
    invoices_count: Mapped[int] = mapped_column(Integer, default=0)
    incoming_invoices_count: Mapped[int] = mapped_column(Integer, default=0)
    outgoing_invoices_count: Mapped[int] = mapped_column(Integer, default=0)
    # Invoice totals
    invoices_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    incoming_invoices_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    outgoing_invoices_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    # Cash operations
    cash_income: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    cash_expense: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    cash_balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    # VAT
    vat_collected: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    vat_paid: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    # Payment status
    paid_invoices_count: Mapped[int] = mapped_column(Integer, default=0)
    unpaid_invoices_count: Mapped[int] = mapped_column(Integer, default=0)
    overdue_invoices_count: Mapped[int] = mapped_column(Integer, default=0)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    
    company = relationship("Company", backref="monthly_summaries")


class YearlySummary(Base):
    __tablename__ = "yearly_summaries"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False, unique=True, index=True)
    # Invoice counts
    invoices_count: Mapped[int] = mapped_column(Integer, default=0)
    incoming_invoices_count: Mapped[int] = mapped_column(Integer, default=0)
    outgoing_invoices_count: Mapped[int] = mapped_column(Integer, default=0)
    # Invoice totals
    invoices_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    incoming_invoices_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    outgoing_invoices_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    # Cash operations
    cash_income: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    cash_expense: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    cash_balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    # VAT
    vat_collected: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    vat_paid: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    # Payment status
    paid_invoices_count: Mapped[int] = mapped_column(Integer, default=0)
    unpaid_invoices_count: Mapped[int] = mapped_column(Integer, default=0)
    overdue_invoices_count: Mapped[int] = mapped_column(Integer, default=0)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    
    company = relationship("Company", backref="yearly_summaries")


# ============== ACCOUNTING MODELS FOR SAF-T COMPLIANCE ==============

class InvoiceCorrection(Base):
    __tablename__ = "invoice_corrections"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    number: Mapped[str] = mapped_column(String(50), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'credit', 'debit'
    original_invoice_id: Mapped[int] = mapped_column(Integer, ForeignKey("invoices.id"), nullable=False)
    correction_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'credit', 'debit'
    reason: Mapped[str] = mapped_column(Text, nullable=True)
    amount_diff: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    vat_diff: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    correction_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)  # alias for correction_date for GraphQL
    new_invoice_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("invoices.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    
    original_invoice = relationship("Invoice", foreign_keys=[original_invoice_id])
    new_invoice = relationship("Invoice", foreign_keys=[new_invoice_id])
    accounting_entries: Mapped[List["AccountingEntry"]] = relationship("AccountingEntry", back_populates="correction")


class CashReceipt(Base):
    __tablename__ = "cash_receipts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    receipt_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    payment_type: Mapped[str] = mapped_column(String(20), default="cash")  # 'cash', 'card'
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    vat_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    items_json: Mapped[str] = mapped_column(JSON, nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    
    company = relationship("Company", backref="cash_receipts")
    creator = relationship("User", foreign_keys=[created_by])


class BankAccount(Base):
    __tablename__ = "bank_accounts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    iban: Mapped[str] = mapped_column(String(34), unique=True, nullable=False)
    bic: Mapped[Optional[str]] = mapped_column(String(11), nullable=True)
    bank_name: Mapped[str] = mapped_column(String(255), nullable=False)
    account_type: Mapped[str] = mapped_column(String(20), default="current")  # 'current', 'escrow'
    currency: Mapped[str] = mapped_column(String(3), default="BGN")
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    
    company = relationship("Company", backref="bank_accounts")
    transactions = relationship("BankTransaction", back_populates="bank_account", cascade="all, delete-orphan")


class BankTransaction(Base):
    __tablename__ = "bank_transactions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    bank_account_id: Mapped[int] = mapped_column(Integer, ForeignKey("bank_accounts.id", ondelete="CASCADE"), nullable=False)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'credit', 'debit'
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    invoice_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("invoices.id"), nullable=True)
    matched: Mapped[bool] = mapped_column(Boolean, default=False)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    
    bank_account = relationship("BankAccount", back_populates="transactions")
    invoice = relationship("Invoice", backref="bank_transactions")
    company = relationship("Company", backref="bank_transactions")


class Account(Base):
    __tablename__ = "accounts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'asset', 'liability', 'equity', 'revenue', 'expense'
    parent_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("accounts.id"), nullable=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    opening_balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    
    company = relationship("Company", backref="accounts")
    parent = relationship("Account", remote_side=[id], backref="children")
    debit_entries = relationship("AccountingEntry", foreign_keys="AccountingEntry.debit_account_id", back_populates="debit_account")
    credit_entries = relationship("AccountingEntry", foreign_keys="AccountingEntry.credit_account_id", back_populates="credit_account")


class AccountingEntry(Base):
    __tablename__ = "accounting_entries"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    entry_number: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    debit_account_id: Mapped[int] = mapped_column(Integer, ForeignKey("accounts.id"), nullable=False)
    credit_account_id: Mapped[int] = mapped_column(Integer, ForeignKey("accounts.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    vat_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    invoice_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("invoices.id"), nullable=True)
    correction_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("invoice_corrections.id"), nullable=True)
    bank_transaction_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("bank_transactions.id"), nullable=True)
    cash_journal_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("cash_journal_entries.id"), nullable=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    is_reversal: Mapped[bool] = mapped_column(Boolean, default=False)
    
    debit_account = relationship("Account", foreign_keys=[debit_account_id], back_populates="debit_entries")
    credit_account = relationship("Account", foreign_keys=[credit_account_id], back_populates="credit_entries")
    invoice = relationship("Invoice", backref="accounting_entries")
    correction = relationship("InvoiceCorrection", back_populates="accounting_entries")
    company = relationship("Company", backref="accounting_entries")
    creator = relationship("User", foreign_keys=[created_by])


class VATRegister(Base):
    __tablename__ = "vat_registers"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    period_month: Mapped[int] = mapped_column(Integer, nullable=False)
    period_year: Mapped[int] = mapped_column(Integer, nullable=False)
    vat_collected_20: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    vat_collected_9: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    vat_collected_0: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    vat_paid_20: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    vat_paid_9: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    vat_paid_0: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    vat_adjustment: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    vat_due: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    vat_credit: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True, onupdate=sofia_now)

    company = relationship("Company", backref="vat_registers")


class AccessZone(Base):
    """Зона за контрол на достъп"""
    __tablename__ = "access_zones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    zone_id: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False) # zone_1
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=1)
    depends_on: Mapped[list] = mapped_column(JSON, default=[]) # List of zone_id strings
    required_hours_start: Mapped[str] = mapped_column(String(5), default="00:00")
    required_hours_end: Mapped[str] = mapped_column(String(5), default="23:59") 
    anti_passback_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    anti_passback_type: Mapped[str] = mapped_column(String(20), default="soft") # soft, hard, timed
    anti_passback_timeout: Mapped[int] = mapped_column(Integer, default=5) 
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True) 
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    
    doors = relationship("AccessDoor", back_populates="zone")
    authorized_users = relationship("User", secondary=user_access_zones, back_populates="accessible_zones")


class AccessDoor(Base):
    """Врата за контрол на достъп"""
    __tablename__ = "access_doors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    door_id: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False) # door_1
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    zone_db_id: Mapped[int] = mapped_column(Integer, ForeignKey("access_zones.id", ondelete="CASCADE"), nullable=False)
    gateway_id: Mapped[int] = mapped_column(Integer, ForeignKey("gateways.id", ondelete="CASCADE"), nullable=False)
    device_id: Mapped[str] = mapped_column(String(50), nullable=False) # ID of relay device
    relay_number: Mapped[int] = mapped_column(Integer, default=1)
    terminal_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True) # Hardware UUID of associated terminal
    terminal_mode: Mapped[str] = mapped_column(String(20), default="access") # "clock", "access", "both"    
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_online: Mapped[bool] = mapped_column(Boolean, default=False)
    last_check: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True)
    
    zone = relationship("AccessZone", back_populates="doors")
    gateway = relationship("Gateway")


class AccessCode(Base):
    """Код за еднократен/временен достъп"""
    __tablename__ = "access_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    code_type: Mapped[str] = mapped_column(String(20), default="one_time") # one_time, daily, guest, permanent
    zones: Mapped[list] = mapped_column(JSON, default=[]) # List of zone_id strings
    uses_remaining: Mapped[int] = mapped_column(Integer, default=1)
    expires_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    last_used_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    gateway_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("gateways.id", ondelete="CASCADE"), nullable=True)


class AccessLog(Base):
    """Лог за достъп (синхронизиран от gateway)"""
    __tablename__ = "access_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    timestamp: Mapped[datetime.datetime] = mapped_column(DateTime, index=True, nullable=False)
    user_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    user_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    zone_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    zone_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    door_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    door_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    action: Mapped[str] = mapped_column(String(20)) # enter, exit
    result: Mapped[str] = mapped_column(String(20)) # granted, denied
    reason: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    method: Mapped[str] = mapped_column(String(20)) # qr_scan, code, remote
    terminal_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    gateway_id: Mapped[int] = mapped_column(Integer, ForeignKey("gateways.id", ondelete="CASCADE"), nullable=False)

    gateway = relationship("Gateway")


# ============================================================
# LOGISTICS MODELS
# ============================================================

class RequestTemplate(Base):
    """Шаблони за заявки"""
    __tablename__ = "request_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    items: Mapped[JSONScalar] = mapped_column(JSON, default=[])
    default_department_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("departments.id"), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)

    company = relationship("Company", backref="request_templates")
    default_department = relationship("Department")


class PurchaseRequestStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    FULFILLED = "fulfilled"


class PurchaseRequestPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class PurchaseRequest(Base):
    """Вътрешни заявки"""
    __tablename__ = "purchase_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    request_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    requested_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    department_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("departments.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=PurchaseRequestStatus.DRAFT.value)
    priority: Mapped[str] = mapped_column(String(20), default=PurchaseRequestPriority.MEDIUM.value)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    due_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    approved_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    is_auto: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)

    company = relationship("Company", backref="purchase_requests")
    requested_by_user = relationship("User", foreign_keys=[requested_by_id], back_populates="purchase_requests")
    department = relationship("Department")
    approved_by = relationship("User", foreign_keys=[approved_by_id])
    items = relationship("PurchaseRequestItem", back_populates="purchase_request", cascade="all, delete-orphan")
    approvals = relationship("PurchaseRequestApproval", back_populates="purchase_request", cascade="all, delete-orphan")
    history = relationship("PurchaseRequestHistory", back_populates="purchase_request", cascade="all, delete-orphan")


class PurchaseRequestItem(Base):
    """Артикули в заявката"""
    __tablename__ = "purchase_request_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    purchase_request_id: Mapped[int] = mapped_column(Integer, ForeignKey("purchase_requests.id", ondelete="CASCADE"), nullable=False)
    item_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    unit: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    purchase_request = relationship("PurchaseRequest", back_populates="items")


class PurchaseRequestApproval(Base):
    """История на одобрения"""
    __tablename__ = "purchase_request_approvals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    request_id: Mapped[int] = mapped_column(Integer, ForeignKey("purchase_requests.id", ondelete="CASCADE"), nullable=False)
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    action_date: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_auto: Mapped[bool] = mapped_column(Boolean, default=False)

    purchase_request = relationship("PurchaseRequest", back_populates="approvals")
    user = relationship("User")


class PurchaseRequestHistory(Base):
    """История на промените"""
    __tablename__ = "purchase_request_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    request_id: Mapped[int] = mapped_column(Integer, ForeignKey("purchase_requests.id", ondelete="CASCADE"), nullable=False)
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    old_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    new_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    changed_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    changed_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)

    purchase_request = relationship("PurchaseRequest", back_populates="history")
    changed_by = relationship("User")


class PurchaseOrderStatus(str, enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    CONFIRMED = "confirmed"
    PARTIAL = "partial"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class PurchaseOrder(Base):
    """Покупни поръчки"""
    __tablename__ = "purchase_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    supplier_id: Mapped[int] = mapped_column(Integer, ForeignKey("suppliers.id"), nullable=False)
    purchase_request_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("purchase_requests.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=PurchaseOrderStatus.DRAFT.value)
    order_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    expected_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    received_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    vat_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)

    company = relationship("Company", backref="purchase_orders")
    supplier = relationship("Supplier", backref="purchase_orders")
    purchase_request = relationship("PurchaseRequest")
    items = relationship("PurchaseOrderItem", back_populates="purchase_order", cascade="all, delete-orphan")
    deliveries = relationship("Delivery", back_populates="purchase_order", cascade="all, delete-orphan")


class PurchaseOrderItem(Base):
    """Артикули в поръчката"""
    __tablename__ = "purchase_order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    purchase_order_id: Mapped[int] = mapped_column(Integer, ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False)
    item_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    received_quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), default=0)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    vat_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=20)
    unit: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    purchase_order = relationship("PurchaseOrder", back_populates="items")


class DeliveryStatus(str, enum.Enum):
    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class Delivery(Base):
    """Доставки"""
    __tablename__ = "deliveries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    delivery_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    purchase_order_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("purchase_orders.id"), nullable=True)
    vehicle_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("vehicles.id"), nullable=True)
    driver_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=DeliveryStatus.PENDING.value)
    shipped_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    delivery_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    tracking_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)

    company = relationship("Company", backref="deliveries")
    purchase_order = relationship("PurchaseOrder", back_populates="deliveries")
    vehicle = relationship("Vehicle", back_populates="deliveries")
    driver = relationship("User", foreign_keys=[driver_id])
    trips = relationship("VehicleTrip", back_populates="delivery")


# ============================================================
# FLEET MODELS
# ============================================================

class VehicleType(Base):
    """Типове автомобили"""
    __tablename__ = "vehicle_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    vehicles = relationship("Vehicle", back_populates="vehicle_type")


class VehicleStatus(str, enum.Enum):
    ACTIVE = "active"
    IN_REPAIR = "in_repair"
    OUT_OF_SERVICE = "out_of_service"
    SOLD = "sold"


class FuelType(str, enum.Enum):
    BENZIN = "benzin"
    DIZEL = "dizel"
    ELECTRIC = "electric"
    HYBRID = "hybrid"
    LNG = "lng"
    CNG = "cng"


class Vehicle(Base):
    """Автомобили"""
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    registration_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    vin: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    make: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    vehicle_type_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("vehicle_types.id"), nullable=True)
    fuel_type: Mapped[str] = mapped_column(String(20), default=FuelType.DIZEL.value)
    engine_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    chassis_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    initial_mileage: Mapped[int] = mapped_column(Integer, default=0)
    is_company: Mapped[bool] = mapped_column(Boolean, default=True)
    owner_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=VehicleStatus.ACTIVE.value)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)

    company = relationship("Company", backref="vehicles")
    vehicle_type = relationship("VehicleType", back_populates="vehicles")
    documents = relationship("VehicleDocument", back_populates="vehicle", cascade="all, delete-orphan")
    fuel_cards = relationship("VehicleFuelCard", back_populates="vehicle", cascade="all, delete-orphan")
    vignettes = relationship("VehicleVignette", back_populates="vehicle", cascade="all, delete-orphan")
    tolls = relationship("VehicleToll", back_populates="vehicle", cascade="all, delete-orphan")
    mileage_records = relationship("VehicleMileage", back_populates="vehicle", cascade="all, delete-orphan")
    fuel_records = relationship("VehicleFuel", back_populates="vehicle", cascade="all, delete-orphan")
    repairs = relationship("VehicleRepair", back_populates="vehicle", cascade="all, delete-orphan")
    schedules = relationship("VehicleSchedule", back_populates="vehicle", cascade="all, delete-orphan")
    insurances = relationship("VehicleInsurance", back_populates="vehicle", cascade="all, delete-orphan")
    inspections = relationship("VehicleInspection", back_populates="vehicle", cascade="all, delete-orphan")
    pretrip_inspections = relationship("VehiclePreTripInspection", back_populates="vehicle", cascade="all, delete-orphan")
    drivers = relationship("VehicleDriver", back_populates="vehicle", cascade="all, delete-orphan")
    trips = relationship("VehicleTrip", back_populates="vehicle", cascade="all, delete-orphan")
    expenses = relationship("VehicleExpense", back_populates="vehicle", cascade="all, delete-orphan")
    deliveries = relationship("Delivery", back_populates="vehicle")


class VehicleDocumentType(str, enum.Enum):
    INVOICE = "invoice"
    POLICY = "policy"
    INSPECTION = "inspection"
    CONTRACT = "contract"
    OTHER = "other"


class VehicleDocument(Base):
    """Документи на автомобили"""
    __tablename__ = "vehicle_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    vehicle_id: Mapped[int] = mapped_column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    document_type: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    issue_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)

    vehicle = relationship("Vehicle", back_populates="documents")


class VehicleFuelCard(Base):
    """Горивни карти"""
    __tablename__ = "vehicle_fuel_cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    vehicle_id: Mapped[int] = mapped_column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    card_number: Mapped[str] = mapped_column(String(50), nullable=False)
    provider: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    pin: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    limit: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    expiry_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)

    vehicle = relationship("Vehicle", back_populates="fuel_cards")
    fuel_records = relationship("VehicleFuel", back_populates="fuel_card")


class VehicleVignetteType(str, enum.Enum):
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


class VehicleVignette(Base):
    """Е-винетки"""
    __tablename__ = "vehicle_vignettes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    vehicle_id: Mapped[int] = mapped_column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    vignette_type: Mapped[str] = mapped_column(String(20), nullable=False)
    purchase_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    valid_from: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    valid_until: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    provider: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    document_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)

    vehicle = relationship("Vehicle", back_populates="vignettes")


class VehicleToll(Base):
    """Тол такси"""
    __tablename__ = "vehicle_tolls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    vehicle_id: Mapped[int] = mapped_column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    route: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    toll_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    toll_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    section: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    document_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)

    vehicle = relationship("Vehicle", back_populates="tolls")


class MileageSource(str, enum.Enum):
    MANUAL = "manual"
    GPS = "gps"
    TACHO = "tacho"


class VehicleMileage(Base):
    """Километраж"""
    __tablename__ = "vehicle_mileage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    vehicle_id: Mapped[int] = mapped_column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    mileage: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[str] = mapped_column(String(20), default=MileageSource.MANUAL.value)
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)

    vehicle = relationship("Vehicle", back_populates="mileage_records")


class VehicleFuel(Base):
    """Зареждане на гориво"""
    __tablename__ = "vehicle_fuel"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    vehicle_id: Mapped[int] = mapped_column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    date: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    fuel_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    price_per_liter: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    mileage: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    invoice_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    fuel_card_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("vehicle_fuel_cards.id"), nullable=True)
    driver_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)

    vehicle = relationship("Vehicle", back_populates="fuel_records")
    fuel_card = relationship("VehicleFuelCard", back_populates="fuel_records")
    driver = relationship("User", foreign_keys=[driver_id])


class RepairType(str, enum.Enum):
    SCHEDULED = "scheduled"
    UNSCHEDULED = "unscheduled"
    INSPECTION = "inspection"


class VehicleRepair(Base):
    """Ремонти"""
    __tablename__ = "vehicle_repairs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    vehicle_id: Mapped[int] = mapped_column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    repair_date: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    repair_type: Mapped[str] = mapped_column(String(20), default=RepairType.UNSCHEDULED.value)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parts: Mapped[JSONScalar] = mapped_column(JSON, default=[])
    labor_hours: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    labor_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    parts_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    total_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    mileage: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    vehicle_service_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("vehicle_services.id"), nullable=True)
    warranty_months: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    next_service_km: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)

    vehicle = relationship("Vehicle", back_populates="repairs")
    vehicle_service = relationship("VehicleService", back_populates="repairs")


class VehicleService(Base):
    """Сервизи"""
    __tablename__ = "vehicle_services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_person: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)

    repairs = relationship("VehicleRepair", back_populates="vehicle_service")
    schedules = relationship("VehicleSchedule", back_populates="vehicle_service")


class ScheduleType(str, enum.Enum):
    OIL_CHANGE = "oil_change"
    TIRE_ROTATION = "tire_rotation"
    INSPECTION = "inspection"
    GENERAL = "general"


class VehicleSchedule(Base):
    """График за поддръжка"""
    __tablename__ = "vehicle_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    vehicle_id: Mapped[int] = mapped_column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    schedule_type: Mapped[str] = mapped_column(String(20), nullable=False)
    interval_km: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    interval_months: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    last_service_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    last_service_km: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    next_service_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    next_service_km: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    vehicle_service_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("vehicle_services.id"), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)

    vehicle = relationship("Vehicle", back_populates="schedules")
    vehicle_service = relationship("VehicleService", back_populates="schedules")


class InsuranceType(str, enum.Enum):
    CIVIL = "civil"
    KASKO = "kasko"
    BORDER = "border"


class PaymentType(str, enum.Enum):
    ANNUAL = "annual"
    SEMI_ANNUAL = "semi_annual"
    QUARTERLY = "quarterly"


class VehicleInsurance(Base):
    """Застраховки"""
    __tablename__ = "vehicle_insurances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    vehicle_id: Mapped[int] = mapped_column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    insurance_type: Mapped[str] = mapped_column(String(20), nullable=False)
    policy_number: Mapped[str] = mapped_column(String(50), nullable=False)
    insurance_company: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    start_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    end_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    premium: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    coverage_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    payment_type: Mapped[str] = mapped_column(String(20), default=PaymentType.ANNUAL.value)
    document_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)

    vehicle = relationship("Vehicle", back_populates="insurances")


class InspectionResult(str, enum.Enum):
    PASSED = "passed"
    FAILED = "failed"
    PENDING = "pending"


class VehicleInspection(Base):
    """ГТП"""
    __tablename__ = "vehicle_inspections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    vehicle_id: Mapped[int] = mapped_column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    inspection_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    valid_until: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    result: Mapped[str] = mapped_column(String(20), default=InspectionResult.PENDING.value)
    mileage: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    inspector: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    certificate_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    next_inspection_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)

    vehicle = relationship("Vehicle", back_populates="inspections")


class PreTripStatus(str, enum.Enum):
    PASSED = "passed"
    FAILED = "failed"


class VehiclePreTripInspection(Base):
    """Инспекция преди път"""
    __tablename__ = "vehicle_pretrip_inspections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    vehicle_id: Mapped[int] = mapped_column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    driver_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    inspection_date: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    tires_condition: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    tires_pressure: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    tires_tread: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    brakes_condition: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    brakes_parking: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    lights_headlights: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    lights_brake: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    lights_turn: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    lights_warning: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    fluids_oil: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    fluids_coolant: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    fluids_washer: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    fluids_brake: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    mirrors: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    wipers: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    horn: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    seatbelts: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    first_aid_kit: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    fire_extinguisher: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    warning_triangle: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    overall_status: Mapped[str] = mapped_column(String(20), default=PreTripStatus.FAILED.value)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    photos: Mapped[Optional[JSONScalar]] = mapped_column(JSON, default=[])
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)

    vehicle = relationship("Vehicle", back_populates="pretrip_inspections")
    driver = relationship("User")


class VehicleDriver(Base):
    """Водачи"""
    __tablename__ = "vehicle_drivers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    vehicle_id: Mapped[int] = mapped_column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_from: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    assigned_to: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)

    vehicle = relationship("Vehicle", back_populates="drivers")
    user = relationship("User", back_populates="vehicle_assignments")


class VehicleTrip(Base):
    """Маршрути"""
    __tablename__ = "vehicle_trips"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    vehicle_id: Mapped[int] = mapped_column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    driver_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    delivery_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("deliveries.id"), nullable=True)
    start_address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    end_address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    start_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    end_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    distance_km: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    purpose: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    expenses: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), default=0)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)

    vehicle = relationship("Vehicle", back_populates="trips")
    driver = relationship("User", foreign_keys=[driver_id], back_populates="vehicle_trips")
    delivery = relationship("Delivery", back_populates="trips")


class ExpenseType(str, enum.Enum):
    FUEL = "fuel"
    REPAIR = "repair"
    INSURANCE = "insurance"
    INSPECTION = "inspection"
    VIGNETTE = "vignette"
    TOLL = "toll"
    TAX = "tax"
    OTHER = "other"


class VehicleExpense(Base):
    """Разходи"""
    __tablename__ = "vehicle_expenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    vehicle_id: Mapped[int] = mapped_column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    expense_type: Mapped[str] = mapped_column(String(20), nullable=False)
    expense_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    vat_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    reference_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reference_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_deductible: Mapped[bool] = mapped_column(Boolean, default=True)
    cost_center_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("vehicle_cost_centers.id"), nullable=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)

    vehicle = relationship("Vehicle", back_populates="expenses")
    cost_center = relationship("VehicleCostCenter", back_populates="expenses")
    company = relationship("Company", backref="vehicle_expenses")


class VehicleCostCenter(Base):
    """Разходни центрове"""
    __tablename__ = "vehicle_cost_centers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    department_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("departments.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=sofia_now)

    department = relationship("Department")
    company = relationship("Company", backref="vehicle_cost_centers")
    expenses = relationship("VehicleExpense", back_populates="cost_center")


# Add back_populates relationships after all models are defined
User.purchase_requests = relationship("PurchaseRequest", foreign_keys=[PurchaseRequest.requested_by_id], back_populates="requested_by_user")
User.vehicle_fuel_records = relationship("VehicleFuel", foreign_keys=[VehicleFuel.driver_id], back_populates="driver")
User.vehicle_trips = relationship("VehicleTrip", foreign_keys=[VehicleTrip.driver_id], back_populates="driver")
User.vehicle_assignments = relationship("VehicleDriver", back_populates="user")
