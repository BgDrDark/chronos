import logging
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from backend.database.models import (
    TimeLog, WorkSchedule, Shift, LeaveRequest,
    AdvancePayment, ServiceLoan, ProductionTask,
    ProductionScrapLog, User, Company, OvertimeWork
)
from backend.modules.behavioral_analysis.models import (
    BehavioralProfile, BehavioralAnomaly, BehavioralStatusThresholds,
    BehavioralMetricWeights, BehavioralSystemHealth
)

logger = logging.getLogger(__name__)

class BehavioralDetector:
    """Layer 1: Detection - Computes behavioral metrics from existing data"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def compute_profile(self, user_id: int, company_id: int, period_start: date, period_end: date) -> BehavioralProfile:
        user_result = await self.db.execute(
            select(User).where(User.id == user_id).options(selectinload(User.company_rel))
        )
        user = user_result.scalar_one_or_none()
        if not user:
            raise ValueError(f"User {user_id} not found")

        punctuality = await self._compute_punctuality(user_id, company_id, period_start, period_end)
        efficiency = await self._compute_efficiency(user_id, company_id, period_start, period_end)
        overtime = await self._compute_overtime(user_id, company_id, period_start, period_end)
        burnout = await self._compute_burnout_risk(user_id, company_id, period_start, period_end, overtime)
        financial = await self._compute_financial_stress(user_id, company_id, period_start, period_end)
        engagement = await self._compute_engagement(user_id, company_id, period_start, period_end)
        scrap = await self._compute_scrap_rate(user_id, company_id, period_start, period_end)

        thresholds = await self._get_thresholds(company_id)
        weights = await self._get_weights(company_id)

        hire_date = user.contract_start_date or user.created_at.date() if hasattr(user, 'created_at') else period_start
        tenure_days = (period_end - hire_date).days if hire_date else 0
        probation_days = getattr(user.company_rel, 'probation_period_days', 90) if user.company_rel else 90
        probation_mode = tenure_days <= probation_days

        status = self._determine_status(punctuality, efficiency, burnout, financial, engagement, thresholds, probation_mode)
        contribution_factors = self._compute_contribution_factors(burnout, overtime, engagement, scrap)

        profile_result = await self.db.execute(
            select(BehavioralProfile).where(
                BehavioralProfile.user_id == user_id,
                BehavioralProfile.period_start == period_start,
                BehavioralProfile.period_end == period_end
            )
        )
        profile = profile_result.scalar_one_or_none()

        employee_type = getattr(user, 'employment_type', 'full_time') or 'full_time'

        if not profile:
            profile = BehavioralProfile(
                user_id=user_id, company_id=company_id,
                period_start=period_start, period_end=period_end,
                employee_type=employee_type
            )
            self.db.add(profile)

        profile.tenure_days = max(0, tenure_days)
        profile.probation_mode = probation_mode
        profile.punctuality_score = punctuality
        profile.efficiency_score = efficiency
        profile.overtime_score = overtime
        profile.burnout_risk = burnout
        profile.financial_stress_score = financial
        profile.engagement_score = engagement
        profile.scrap_rate = scrap
        profile.status = status
        profile.contribution_factors = contribution_factors
        profile.computed_at = datetime.now(timezone.utc)
        profile.version += 1

        return profile

    async def compute_all_profiles(self, company_id: int, period_start: date, period_end: date, incremental: bool = True) -> List[BehavioralProfile]:
        stmt = select(User.id).where(User.company_id == company_id, User.is_active == True)
        result = await self.db.execute(stmt)
        user_ids = [row[0] for row in result.all()]

        profiles = []
        for uid in user_ids:
            try:
                p = await self.compute_profile(uid, company_id, period_start, period_end)
                profiles.append(p)
            except Exception as e:
                logger.error(f"Failed to compute profile for user {uid}: {e}")

        await self.db.commit()
        await self._update_system_health(company_id, len(profiles), len(user_ids) - len(profiles))
        return profiles

    async def _compute_punctuality(self, user_id: int, company_id: int, start: date, end: date) -> float:
        start_dt = datetime.combine(start, datetime.min.time())
        end_dt = datetime.combine(end, datetime.max.time())

        logs_result = await self.db.execute(
            select(func.count(TimeLog.id)).where(
                TimeLog.user_id == user_id,
                TimeLog.start_time >= start_dt,
                TimeLog.start_time <= end_dt,
                TimeLog.type == 'work'
            )
        )
        total_days = logs_result.scalar() or 0
        if total_days == 0:
            return 100.0

        late_result = await self.db.execute(
            select(func.count(TimeLog.id)).where(
                TimeLog.user_id == user_id,
                TimeLog.start_time >= start_dt,
                TimeLog.start_time <= end_dt,
                TimeLog.type == 'work',
                TimeLog.is_manual == True
            )
        )
        late_days = late_result.scalar() or 0
        return max(0.0, 100.0 - ((late_days / total_days) * 100.0))

    async def _compute_efficiency(self, user_id: int, company_id: int, start: date, end: date) -> float:
        tasks_result = await self.db.execute(
            select(func.avg(ProductionTask.efficiency)).where(
                ProductionTask.user_id == user_id,
                ProductionTask.created_at >= datetime.combine(start, datetime.min.time()),
                ProductionTask.created_at <= datetime.combine(end, datetime.max.time())
            )
        )
        avg_eff = tasks_result.scalar()
        return float(avg_eff) if avg_eff else 100.0

    async def _compute_overtime(self, user_id: int, company_id: int, start: date, end: date) -> float:
        ot_result = await self.db.execute(
            select(func.sum(OvertimeWork.hours)).where(
                OvertimeWork.user_id == user_id,
                OvertimeWork.date >= start,
                OvertimeWork.date <= end
            )
        )
        total_ot = ot_result.scalar() or Decimal('0')
        weeks = max(1, (end - start).days / 7)
        ot_per_week = float(total_ot) / weeks
        return min(100.0, (ot_per_week / 10.0) * 100.0)

    async def _compute_burnout_risk(self, user_id: int, company_id: int, start: date, end: date, overtime_score: float) -> float:
        leave_result = await self.db.execute(
            select(func.count(LeaveRequest.id)).where(
                LeaveRequest.user_id == user_id,
                LeaveRequest.start_date >= start,
                LeaveRequest.end_date <= end,
                LeaveRequest.status.in_(['approved', 'pending'])
            )
        )
        leave_days = leave_result.scalar() or 0
        leave_penalty = min(0.3, (leave_days / 10.0) * 0.3)

        ot_factor = (overtime_score / 100.0) * 0.5
        return min(1.0, ot_factor + leave_penalty + 0.2)

    async def _compute_financial_stress(self, user_id: int, company_id: int, start: date, end: date) -> float:
        adv_result = await self.db.execute(
            select(func.count(AdvancePayment.id)).where(
                AdvancePayment.user_id == user_id,
                AdvancePayment.payment_date >= start,
                AdvancePayment.payment_date <= end
            )
        )
        advances = adv_result.scalar() or 0
        return min(1.0, (advances / 3.0) * 0.8)

    async def _compute_engagement(self, user_id: int, company_id: int, start: date, end: date) -> float:
        start_dt = datetime.combine(start, datetime.min.time())
        end_dt = datetime.combine(end, datetime.max.time())

        logs_result = await self.db.execute(
            select(func.count(TimeLog.id)).where(
                TimeLog.user_id == user_id,
                TimeLog.start_time >= start_dt,
                TimeLog.start_time <= end_dt,
                TimeLog.type == 'work'
            )
        )
        presence_days = logs_result.scalar() or 0
        expected_days = max(1, (end - start).days * 5 / 7)
        return min(100.0, (presence_days / expected_days) * 100.0)

    async def _compute_scrap_rate(self, user_id: int, company_id: int, start: date, end: date) -> float:
        scrap_result = await self.db.execute(
            select(func.sum(ProductionScrapLog.quantity)).where(
                ProductionScrapLog.user_id == user_id,
                ProductionScrapLog.created_at >= datetime.combine(start, datetime.min.time()),
                ProductionScrapLog.created_at <= datetime.combine(end, datetime.max.time())
            )
        )
        total_scrap = scrap_result.scalar() or Decimal('0')
        return min(100.0, float(total_scrap) * 2.0)

    async def _get_thresholds(self, company_id: int) -> Optional[BehavioralStatusThresholds]:
        res = await self.db.execute(select(BehavioralStatusThresholds).where(BehavioralStatusThresholds.company_id == company_id))
        return res.scalar_one_or_none()

    async def _get_weights(self, company_id: int) -> Optional[BehavioralMetricWeights]:
        res = await self.db.execute(select(BehavioralMetricWeights).where(BehavioralMetricWeights.company_id == company_id))
        return res.scalar_one_or_none()

    def _determine_status(self, punctuality: float, efficiency: float, burnout: float, financial: float, engagement: float, thresholds: Optional[BehavioralStatusThresholds], probation_mode: bool) -> str:
        t = thresholds
        pw = t.punctuality_warning if t else 70.0
        pc = t.punctuality_critical if t else 50.0
        ew = t.efficiency_warning if t else 60.0
        ec = t.efficiency_critical if t else 40.0
        bw = t.burnout_warning if t else 0.6
        bc = t.burnout_critical if t else 0.8

        if probation_mode:
            pw *= 1.5; pc *= 1.5; ew *= 1.5; ec *= 1.5; bw *= 0.7; bc *= 0.8

        if burnout >= bc or (punctuality <= pc and efficiency <= ec):
            return "critical"
        if burnout >= bw or punctuality <= pw or efficiency <= ew:
            return "at_risk"
        if punctuality >= 95 and efficiency >= 90 and burnout < 0.3:
            return "star"
        return "stable"

    def _compute_contribution_factors(self, burnout: float, overtime: float, engagement: float, scrap: float) -> Dict[str, float]:
        total = max(0.01, burnout + (overtime/100) + (1 - engagement/100) + (scrap/100))
        return {
            "burnout_risk": round(burnout / total, 2),
            "overtime_hours": round((overtime/100) / total, 2),
            "engagement_drop": round((1 - engagement/100) / total, 2),
            "scrap_rate": round((scrap/100) / total, 2)
        }

    async def _update_system_health(self, company_id: int, processed: int, failed: int):
        res = await self.db.execute(select(BehavioralSystemHealth).where(BehavioralSystemHealth.company_id == company_id))
        health = res.scalar_one_or_none()
        if not health:
            health = BehavioralSystemHealth(company_id=company_id)
            self.db.add(health)

        health.last_computation_at = datetime.now(timezone.utc)
        health.last_computation_status = "success" if failed == 0 else "partial"
        health.employees_processed = processed
        health.employees_failed = failed
        await self.db.commit()
