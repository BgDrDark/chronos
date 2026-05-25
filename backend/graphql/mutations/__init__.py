import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*strawberry.scalar.*")
warnings.filterwarnings("ignore", message=".*Extension.*")
warnings.filterwarnings("ignore", message=".*Pydantic.*")

import datetime
import json
import logging
from datetime import time as dt_time
from decimal import Decimal
from typing import List, Optional

import strawberry
from sqlalchemy import select
from strawberry.file_uploads import Upload

from backend import crud, schemas
from backend.auth.permission_helper import (
    check_permission,
    require_permission_or_role,
    require_role,
)
from backend.crud.repositories import (
    company_repo,
    payroll_repo,
    settings_repo,
    time_repo,
    user_repo,
    vehicle_repo,
)
from backend.database.transaction_manager import (
    atomic_transaction,
    atomic_with_savepoint,
)
from backend.exceptions import (
    AuthenticationException,
    DatabaseException,
    DuplicateException,
    NotFoundException,
    PermissionDeniedException,
    ValidationException,
)
from backend.graphql import inputs, types
from backend.services.auth_service import (
    auth_service,
    force_password_change_for_all_users,
    regenerate_user_qr_token,
)
from backend.services.leave_service import leave_service
from backend.services.payroll_service import payroll_service
from backend.services.settings_service import settings_service
from backend.services.shift_swap_service import shift_swap_service
from backend.services.time_tracking_service import time_tracking_service
from backend.utils.error_handling import handle_db_error
from backend.utils.json_type import JSONScalar

logger = logging.getLogger(__name__)
from backend.auth.module_guard import verify_module_enabled
from backend.auth.security import (
    hash_password,
    validate_password_complexity,
    verify_password,
)
from backend.database.models import (
    AccessCode,
    AccessDoor,
    AccessZone,
    Gateway,
    LeaveRequest,
    NightWorkBonus,
    OvertimeWork,
    Shift,
    WorkOnHoliday,
    WorkSchedule,
)
from backend.graphql.inputs import (
    BonusCreateInput,
    CompanyAccountingSettingsInput,
    CompanyCreateInput,
    CompanyUpdateInput,
    DepartmentCreateInput,
    DepartmentUpdateInput,
    LeaveRequestInput,
    MonthlyWorkDaysInput,
    PasswordSettingsInput,
    PositionCreateInput,
    RoleCreateInput,
    UpdateLeaveRequestStatusInput,
    UpdateUserInput,
    UserCreateInput,
)

authenticate_msg = "Трябва да се автентикирате"

from backend.graphql.mutations.access_control import AccessControlMutation
from backend.graphql.mutations.accounting import AccountingMutation
from backend.graphql.mutations.calendar import CalendarMutation
from backend.graphql.mutations.contract import ContractMutation
from backend.graphql.mutations.cost_center import CostCenterMutation
from backend.graphql.mutations.hardware import HardwareMutation
from backend.graphql.mutations.leave import LeaveMutation
from backend.graphql.mutations.logistics import LogisticsMutation
from backend.graphql.mutations.nap_reports import NapReportMutation
from backend.graphql.mutations.notifications import NotificationsMutation
from backend.graphql.mutations.payroll import PayrollMutation
from backend.graphql.mutations.production import ProductionMutation
from backend.graphql.mutations.shifts import ShiftsMutation
from backend.graphql.mutations.trz import TrzMutation
from backend.graphql.mutations.vehicle import VehicleMutation
from backend.modules.behavioral_analysis.graphql.mutations import BehavioralMutation


@strawberry.type
class Mutation(VehicleMutation, CostCenterMutation, NotificationsMutation, ShiftsMutation, LogisticsMutation, ProductionMutation, AccountingMutation, ContractMutation, HardwareMutation, AccessControlMutation, PayrollMutation, TrzMutation, LeaveMutation, CalendarMutation, NapReportMutation, BehavioralMutation):
    pass

