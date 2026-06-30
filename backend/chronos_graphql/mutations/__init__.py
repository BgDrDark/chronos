import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*strawberry.scalar.*")
warnings.filterwarnings("ignore", message=".*Extension.*")
warnings.filterwarnings("ignore", message=".*Pydantic.*")

import logging

import strawberry

from backend.chronos_graphql.mutations.access_policy import AccessPolicyMutation
from backend.chronos_graphql.mutations.access_control import AccessControlMutation
from backend.chronos_graphql.mutations.security import SecurityMutations
from backend.chronos_graphql.mutations.elevator import ElevatorMutations
from backend.chronos_graphql.mutations.accounting import AccountingMutation
from backend.chronos_graphql.mutations.calendar import CalendarMutation
from backend.chronos_graphql.mutations.company import CompanyMutation
from backend.chronos_graphql.mutations.contract import ContractMutation
from backend.chronos_graphql.mutations.cost_center import CostCenterMutation
from backend.chronos_graphql.mutations.documentation import DocumentationMutation
from backend.chronos_graphql.mutations.hardware import HardwareMutation
from backend.chronos_graphql.mutations.hr import HRMutation
from backend.chronos_graphql.mutations.inventory import InventoryMutation
from backend.chronos_graphql.mutations.leave import LeaveMutation
from backend.chronos_graphql.mutations.logistics import LogisticsMutation
from backend.chronos_graphql.mutations.nap_reports import NapReportMutation
from backend.chronos_graphql.mutations.notifications import NotificationsMutation
from backend.chronos_graphql.mutations.payroll import PayrollMutation
from backend.chronos_graphql.mutations.production import ProductionMutation
from backend.chronos_graphql.mutations.settings import SettingsMutation
from backend.chronos_graphql.mutations.shift_swap import ShiftSwapMutation
from backend.chronos_graphql.mutations.shifts import ShiftMutation
from backend.chronos_graphql.mutations.trz import TrzMutation
from backend.chronos_graphql.mutations.user import UserMutation
from backend.chronos_graphql.mutations.vehicle import VehicleMutation
from backend.modules.behavioral_analysis.graphql.mutations import BehavioralMutation

logger = logging.getLogger(__name__)

authenticate_msg = "Трябва да се автентикирате"


@strawberry.type
class Mutation(AccessPolicyMutation, VehicleMutation, CostCenterMutation, NotificationsMutation, ShiftMutation, LogisticsMutation, ProductionMutation, AccountingMutation, ContractMutation, HardwareMutation, AccessControlMutation, SecurityMutations, ElevatorMutations, PayrollMutation, TrzMutation, LeaveMutation, CalendarMutation, NapReportMutation, BehavioralMutation, HRMutation, InventoryMutation, ShiftSwapMutation, CompanyMutation, SettingsMutation, UserMutation, DocumentationMutation):
    pass

