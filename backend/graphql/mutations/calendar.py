import logging

import strawberry

from backend.graphql.utils.permission_checker import get_current_user
from backend.services.holiday_service import fetch_and_store_holidays
from backend.services.orthodox_holiday_service import fetch_and_store_orthodox_holidays

logger = logging.getLogger(__name__)


@strawberry.type
class CalendarMutation:
    @strawberry.mutation
    async def sync_holidays(self, year: int, info: strawberry.Info) -> int:
        db = info.context["db"]
        get_current_user(info)

        return await fetch_and_store_holidays(db, year)

    @strawberry.mutation
    async def sync_orthodox_holidays(self, year: int, info: strawberry.Info) -> int:
        db = info.context["db"]
        get_current_user(info)

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
                        select(OrthodoxHoliday.date).where(
                            OrthodoxHoliday.date >= start_date
                        ).where(OrthodoxHoliday.date <= end_date)
                    )
                    existing = result.scalars().all()
                    return len(existing)
                except Exception:
                    pass
            from backend.exceptions import DatabaseException
            raise DatabaseException(detail=f"Failed to sync holidays: {str(e)}") from None
