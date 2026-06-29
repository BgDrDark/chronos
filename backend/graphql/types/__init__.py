import datetime
import enum
import json
import os
import sys
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

import strawberry
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.crud.repositories import settings_repo, time_repo
from backend.database import models
from backend.database.models import sofia_now
from backend.utils.json_type import JSONScalar

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Foundational types (import early since others depend on them)
from backend.graphql.types.company import *  # noqa: F403
from backend.graphql.types.hardware import *  # noqa: F403
from backend.graphql.types.system import *  # noqa: F403  # PresenceStatus, Module, PasswordSettings
from backend.graphql.types.user import *  # noqa: F403

if TYPE_CHECKING:
    from backend.graphql.types import Workstation

from backend.graphql.types.access_policy import *  # noqa: F403
from backend.graphql.types.access_control import *  # noqa: F403
from backend.graphql.types.security import *  # noqa: F403
from backend.graphql.types.elevator import *  # noqa: F403
from backend.graphql.types.accounting import *  # noqa: F403
from backend.graphql.types.calendar import *  # noqa: F403
from backend.graphql.types.contract import *  # noqa: F403
from backend.graphql.types.cost_center import *  # noqa: F403
from backend.graphql.types.leave import *  # noqa: F403
from backend.graphql.types.logistics import *  # noqa: F403
from backend.graphql.types.nap_reports import *  # noqa: F403
from backend.graphql.types.notifications import *  # noqa: F403
from backend.graphql.types.payroll import *  # noqa: F403
from backend.graphql.types.production import *  # noqa: F403
from backend.graphql.types.shifts import *  # noqa: F403
from backend.graphql.types.stats import *  # noqa: F403
from backend.graphql.types.system import *  # noqa: F403
from backend.graphql.types.time_tracking import *  # noqa: F403
from backend.graphql.types.trz import *  # noqa: F403
from backend.graphql.types.vehicle import *  # noqa: F403

