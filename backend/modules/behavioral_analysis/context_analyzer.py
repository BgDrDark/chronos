import logging
from datetime import date, datetime
from typing import Any

from backend.database.models import (
    LeaveRequest,
    Position,
    TimeLog,
    User,
    WorkSchedule,
)
from backend.modules.behavioral_analysis.models import (
    BehavioralAnomaly,
    BehavioralProfile,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)

class ContextAnalyzer:
    """Layer 2: Context - Analyzes why an anomaly might have occurred"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze_anomaly(self, anomaly: BehavioralAnomaly, profile: BehavioralProfile) -> dict[str, Any]:
        context = {
            "recent_schedule_changes": await self._check_schedule_changes(profile.user_id, profile.period_start, profile.period_end),
            "leave_history": await self._check_leave_history(profile.user_id, profile.period_start, profile.period_end),
            "workload_trend": await self._check_workload_trend(profile.user_id, profile.period_start, profile.period_end),
            "team_comparison": await self._get_team_comparison(profile.user_id, profile.company_id, anomaly.metric_name),
        }

        anomaly.context_summary = context
        await self.db.commit()
        return context

    async def _check_schedule_changes(self, user_id: int, start: date, end: date) -> list[dict[str, Any]]:
        result = await self.db.execute(
            select(WorkSchedule).where(
                WorkSchedule.user_id == user_id,
                WorkSchedule.date >= start,
                WorkSchedule.date <= end,
            ).options(selectinload(WorkSchedule.shift)),
        )
        schedules = result.scalars().all()
        changes = []
        if len(schedules) > 1:
            for i in range(1, len(schedules)):
                if schedules[i].shift_id != schedules[i-1].shift_id:
                    changes.append({
                        "date": schedules[i].date.isoformat(),
                        "from": schedules[i-1].shift.name if schedules[i-1].shift else "Unknown",
                        "to": schedules[i].shift.name if schedules[i].shift else "Unknown",
                    })
        return changes

    async def _check_leave_history(self, user_id: int, start: date, end: date) -> dict[str, Any]:
        result = await self.db.execute(
            select(LeaveRequest).where(
                LeaveRequest.user_id == user_id,
                LeaveRequest.start_date >= start,
                LeaveRequest.end_date <= end,
            ),
        )
        leaves = result.scalars().all()
        total_days = sum((leaf.end_date - leaf.start_date).days for leaf in leaves)
        types = {}
        for leaf in leaves:
            types[leaf.leave_type] = types.get(leaf.leave_type, 0) + 1

        return {
            "total_days": total_days,
            "types": types,
            "count": len(leaves),
        }

    async def _check_workload_trend(self, user_id: int, start: date, end: date) -> dict[str, Any]:
        start_dt = datetime.combine(start, datetime.min.time())
        end_dt = datetime.combine(end, datetime.max.time())

        logs_result = await self.db.execute(
            select(func.count(TimeLog.id)).where(
                TimeLog.user_id == user_id,
                TimeLog.start_time >= start_dt,
                TimeLog.start_time <= end_dt,
            ),
        )
        total_logs = logs_result.scalar() or 0
        return {"total_logs": int(total_logs), "trend": "stable"}

    async def _get_team_comparison(self, user_id: int, company_id: int, metric: str) -> dict[str, Any]:
        user_res = await self.db.execute(
            select(User).where(User.id == user_id).options(
                selectinload(User.position_rel).selectinload(Position.department),
            ),
        )
        user = user_res.scalar_one_or_none()
        if not user or not user.position_rel or not user.position_rel.department:
            return {"department_avg": None}

        dept_id = user.position_rel.department.id

        dept_avg_result = await self.db.execute(
            select(func.avg(getattr(BehavioralProfile, metric, BehavioralProfile.punctuality_score))).join(
                User, BehavioralProfile.user_id == User.id,
            ).join(
                Position, User.position_id == Position.id,
            ).where(
                Position.department_id == dept_id,
                BehavioralProfile.period_start >= (user.position_rel.created_at.date() if hasattr(user.position_rel, "created_at") else date.today()),
            ),
        )
        dept_avg = dept_avg_result.scalar()

        return {"department_avg": float(dept_avg) if dept_avg else None}
