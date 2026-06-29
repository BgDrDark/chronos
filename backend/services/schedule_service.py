from datetime import date, datetime, time, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import AccessSchedule, PublicHoliday


class ScheduleService:

    async def is_access_allowed(
        self,
        schedule_id: int,
        at: datetime,
        db: AsyncSession,
    ) -> tuple[bool, str]:
        schedule = await db.get(AccessSchedule, schedule_id)
        if not schedule or not schedule.is_active:
            return False, "Графикът не е активен"

        config = schedule.config or {}
        at_date = at.date()
        at_time = at.time()

        date_overrides = config.get("overrides", [])
        for override in date_overrides:
            start = override.get("start_date")
            end = override.get("end_date")
            action = override.get("action", "deny")
            if start and end:
                try:
                    sd = date.fromisoformat(start)
                    ed = date.fromisoformat(end)
                    if sd <= at_date <= ed:
                        if action == "allow":
                            return True, "Разрешено от override"
                        return False, f"Забранено от override: {override.get('reason', '')}"
                except (ValueError, TypeError):
                    continue

        if schedule.holiday_override_auto:
            holiday_result = await db.execute(
                select(PublicHoliday).where(PublicHoliday.date == at_date),
            )
            holiday = holiday_result.scalar_one_or_none()
            if holiday:
                holiday_behavior = config.get("holiday_behavior", "deny")
                if holiday_behavior == "deny":
                    return False, f"Празничен ден: {holiday.name or holiday.local_name}"
                if holiday_behavior == "allow":
                    return True, "Разрешено на празник"
                if holiday_behavior == "work_schedule":
                    return False, "Празник — изчакване work schedule sync"

        entries = config.get("entries", [])
        if not entries:
            return True, "Няма ограничения (24/7)"

        for entry in entries:
            days = entry.get("days", [])
            if days and at_date.weekday() not in days:
                continue

            time_windows = entry.get("time_windows", [])
            for tw in time_windows:
                start_str = tw.get("start")
                end_str = tw.get("end")
                if not start_str or not end_str:
                    continue
                try:
                    start_t = time.fromisoformat(start_str)
                    end_t = time.fromisoformat(end_str)
                except (ValueError, TypeError):
                    continue

                if start_t <= end_t:
                    if start_t <= at_time <= end_t:
                        return True, "Разрешено от time window"
                else:
                    if at_time >= start_t or at_time <= end_t:
                        return True, "Разрешено от overnight time window"

        return False, "Извън работно време"

    def build_schedule_config(self, schedule: AccessSchedule) -> dict[str, Any]:
        config = schedule.config or {}
        return {
            "id": schedule.id,
            "name": schedule.name,
            "timezone": schedule.timezone,
            "entries": config.get("entries", []),
            "overrides": config.get("overrides", []),
            "holiday_behavior": config.get("holiday_behavior", "deny"),
            "holiday_override_auto": schedule.holiday_override_auto,
        }


schedule_service = ScheduleService()
