import datetime
from decimal import Decimal
from typing import Optional

import strawberry
from sqlalchemy import Time, desc, select

from backend import crud
from backend.config import settings
from backend.crud.repositories import company_repo, settings_repo, time_repo, user_repo
from backend.exceptions import (
    AuthenticationException,
    NotFoundException,
    PermissionDeniedException,
)
from backend.chronos_graphql import types
from backend.chronos_graphql.queries.access_policy import AccessPolicyQuery
from backend.chronos_graphql.queries.access_control import AccessControlQuery
from backend.chronos_graphql.queries.security import SecurityQueries
from backend.chronos_graphql.queries.elevator import ElevatorQueries
from backend.chronos_graphql.queries.accounting import AccountingQuery
from backend.chronos_graphql.queries.company import CompanyQuery
from backend.chronos_graphql.queries.contract import ContractQuery
from backend.chronos_graphql.queries.cost_center import CostCenterQuery
from backend.chronos_graphql.queries.documentation import DocumentationQuery
from backend.chronos_graphql.queries.hardware import HardwareQuery
from backend.chronos_graphql.queries.leave import LeaveQuery
from backend.chronos_graphql.queries.logistics import LogisticsQuery
from backend.chronos_graphql.queries.notifications import NotificationsQuery
from backend.chronos_graphql.queries.payroll import PayrollQuery
from backend.chronos_graphql.queries.production import ProductionQuery
from backend.chronos_graphql.queries.shifts import ShiftsQuery
from backend.chronos_graphql.queries.stats import StatsQuery
from backend.chronos_graphql.queries.system import SystemQuery
from backend.chronos_graphql.queries.time_tracking import TimeTrackingQuery
from backend.chronos_graphql.queries.user import UserQuery
from backend.chronos_graphql.queries.vehicle import VehicleQuery
from backend.modules.behavioral_analysis.graphql.queries import BehavioralQuery
from backend.services.payroll_calculator import PayrollCalculator

authenticate_msg = "Трябва да се автентикирате"
@strawberry.type
class Query(AccessPolicyQuery, LeaveQuery, UserQuery, NotificationsQuery, VehicleQuery, CostCenterQuery, ShiftsQuery, LogisticsQuery, ProductionQuery, AccountingQuery, ContractQuery, HardwareQuery, AccessControlQuery, SecurityQueries, ElevatorQueries, PayrollQuery, BehavioralQuery, TimeTrackingQuery, SystemQuery, CompanyQuery, StatsQuery, DocumentationQuery):
    @strawberry.field
    async def hello(self) -> str:
        return "Hello World"
