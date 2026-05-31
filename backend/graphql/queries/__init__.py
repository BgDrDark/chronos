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
from backend.graphql import types
from backend.graphql.queries.access_control import AccessControlQuery
from backend.graphql.queries.accounting import AccountingQuery
from backend.graphql.queries.company import CompanyQuery
from backend.graphql.queries.contract import ContractQuery
from backend.graphql.queries.cost_center import CostCenterQuery
from backend.graphql.queries.hardware import HardwareQuery
from backend.graphql.queries.leave import LeaveQuery
from backend.graphql.queries.logistics import LogisticsQuery
from backend.graphql.queries.notifications import NotificationsQuery
from backend.graphql.queries.payroll import PayrollQuery
from backend.graphql.queries.production import ProductionQuery
from backend.graphql.queries.shifts import ShiftsQuery
from backend.graphql.queries.stats import StatsQuery
from backend.graphql.queries.system import SystemQuery
from backend.graphql.queries.time_tracking import TimeTrackingQuery
from backend.graphql.queries.user import UserQuery
from backend.graphql.queries.vehicle import VehicleQuery
from backend.modules.behavioral_analysis.graphql.queries import BehavioralQuery
from backend.services.payroll_calculator import PayrollCalculator

authenticate_msg = "Трябва да се автентикирате"
@strawberry.type
class Query(LeaveQuery, UserQuery, NotificationsQuery, VehicleQuery, CostCenterQuery, ShiftsQuery, LogisticsQuery, ProductionQuery, AccountingQuery, ContractQuery, HardwareQuery, AccessControlQuery, PayrollQuery, BehavioralQuery, TimeTrackingQuery, SystemQuery, CompanyQuery, StatsQuery):
    @strawberry.field
    async def hello(self) -> str:
        return "Hello World"
