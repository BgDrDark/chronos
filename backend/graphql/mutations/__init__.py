import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*strawberry.scalar.*")
warnings.filterwarnings("ignore", message=".*Extension.*")
warnings.filterwarnings("ignore", message=".*Pydantic.*")

import logging

import strawberry

from backend.graphql.mutations.access_policy import AccessPolicyMutation
from backend.graphql.mutations.access_control import AccessControlMutation
from backend.graphql.mutations.security import SecurityMutations
from backend.graphql.mutations.elevator import ElevatorMutations
from backend.graphql.mutations.accounting import AccountingMutation
from backend.graphql.mutations.calendar import CalendarMutation
from backend.graphql.mutations.company import CompanyMutation
from backend.graphql.mutations.contract import ContractMutation
from backend.graphql.mutations.cost_center import CostCenterMutation
from backend.graphql.mutations.documentation import DocumentationMutation
from backend.graphql.mutations.hardware import HardwareMutation
from backend.graphql.mutations.hr import HRMutation
from backend.graphql.mutations.inventory import InventoryMutation
from backend.graphql.mutations.leave import LeaveMutation
from backend.graphql.mutations.logistics import LogisticsMutation
from backend.graphql.mutations.nap_reports import NapReportMutation
from backend.graphql.mutations.notifications import NotificationsMutation
from backend.graphql.mutations.payroll import PayrollMutation
from backend.graphql.mutations.production import ProductionMutation
from backend.graphql.mutations.settings import SettingsMutation
from backend.graphql.mutations.shift_swap import ShiftSwapMutation
from backend.graphql.mutations.shifts import ShiftMutation
from backend.graphql.mutations.trz import TrzMutation
from backend.graphql.mutations.user import UserMutation
from backend.graphql.mutations.vehicle import VehicleMutation
from backend.modules.behavioral_analysis.graphql.mutations import BehavioralMutation

logger = logging.getLogger(__name__)

authenticate_msg = "Трябва да се автентикирате"


@strawberry.type
class Mutation(AccessPolicyMutation, VehicleMutation, CostCenterMutation, NotificationsMutation, ShiftMutation, LogisticsMutation, ProductionMutation, AccountingMutation, ContractMutation, HardwareMutation, AccessControlMutation, SecurityMutations, ElevatorMutations, PayrollMutation, TrzMutation, LeaveMutation, CalendarMutation, NapReportMutation, BehavioralMutation, HRMutation, InventoryMutation, ShiftSwapMutation, CompanyMutation, SettingsMutation, UserMutation, DocumentationMutation):
    pass

