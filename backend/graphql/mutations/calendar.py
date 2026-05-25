import datetime
import logging

import strawberry

from backend.auth.module_guard import verify_module_enabled
from backend.exceptions import AuthenticationException
from backend.services.holiday_service import fetch_and_store_holidays
from backend.services.orthodox_holiday_service import fetch_and_store_orthodox_holidays

logger = logging.getLogger(__name__)
authenticate_msg = "Трябва да се автентикирате"


@strawberry.type
class CalendarMutation:
    @strawberry.mutation
    async def fetch_holidays(self, info: strawberry.Info, year: int | None = None) -> str:
        db = info.context.db
        user = info.context.user
        if not user:
            raise AuthenticationException(authenticate_msg)
        await verify_module_enabled(db, "payroll", user.company_id)
        target_year = year or datetime.date.today().year
        result = await fetch_and_store_holidays(db, target_year)
        return f"Добавени {result} нови празника за {target_year} година."

    @strawberry.mutation
    async def fetch_orthodox_holidays(self, info: strawberry.Info, year: int | None = None) -> str:
        db = info.context.db
        user = info.context.user
        if not user:
            raise AuthenticationException(authenticate_msg)
        await verify_module_enabled(db, "payroll", user.company_id)
        target_year = year or datetime.date.today().year
        result = await fetch_and_store_orthodox_holidays(db, target_year)
        return f"Добавени {result} нови православни празника за {target_year} година."
