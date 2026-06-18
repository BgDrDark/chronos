import logging
import math
from datetime import date, datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from backend.config import settings
from backend.database.models import (
    AdvancePayment,
    LeaveRequest,
    OvertimeWork,
    ProductionScrapLog,
    ProductionTask,
    RecipeStep,
    Shift,
    TimeLog,
    User,
    WorkSchedule,
)

from backend.modules.behavioral_analysis.models import (
    BehavioralMetricWeights,
    BehavioralProfile,
    BehavioralPulseSurvey,
    BehavioralStatusThresholds,
    BehavioralSystemHealth,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)


def mann_kendall_trend(values: list[float]) -> tuple[str, float]:
    """Mann-Kendall test for monotonic trend.

    Returns (direction, p_value).
    p < 0.05 → statistically significant trend.
    Pure Python — no scipy dependency. Uses normal approximation for n >= 8.
    """
    n = len(values)
    if n < 3:
        return "insufficient_data", 1.0

    s = 0
    ties: dict[float, int] = {}
    for i in range(n):
        ties[values[i]] = ties.get(values[i], 0) + 1
        for j in range(i + 1, n):
            if values[j] > values[i]:
                s += 1
            elif values[j] < values[i]:
                s -= 1

    if n < 8:
        return _mk_exact(values, s, n)

    var_s = n * (n - 1) * (2 * n + 5) / 18
    tie_correction = sum(t * (t - 1) * (2 * t + 5) for t in ties.values() if t > 1)
    var_s -= tie_correction / 18
    if var_s <= 0:
        return "stable", 1.0
    var_s = max(var_s, 1.0)

    if s > 0:
        z = (s - 1) / (var_s ** 0.5)
    elif s < 0:
        z = (s + 1) / (var_s ** 0.5)
    else:
        z = 0.0

    p_value = 2.0 * _normal_sf(abs(z))

    if p_value > 0.05:
        return "stable", min(p_value, 1.0)
    return ("increasing", min(p_value, 1.0)) if z > 0 else ("decreasing", min(p_value, 1.0))


def _mk_exact(values: list[float], s: int, n: int) -> tuple[str, float]:
    """Exact p-value for small samples (n < 8) using combinatorial enumeration."""
    total_combinations = 1 << (n * (n - 1) // 2)
    from itertools import combinations

    possible_s = set()
    for perm in __import__("itertools").permutations(values):
        sp = 0
        for i in range(n):
            for j in range(i + 1, n):
                if perm[j] > perm[i]:
                    sp += 1
                elif perm[j] < perm[i]:
                    sp -= 1
        possible_s.add(sp)

    extreme = sum(1 for ps in possible_s if abs(ps) >= abs(s))
    p_value = extreme / len(possible_s) if possible_s else 1.0

    if p_value > 0.05:
        return "stable", min(p_value, 1.0)
    return ("increasing", min(p_value, 1.0)) if s > 0 else ("decreasing", min(p_value, 1.0))


def _normal_sf(z: float) -> float:
    """Survival function of the standard normal distribution (no scipy)."""
    return 0.5 * math.erfc(z / 2 ** 0.5)


def compute_z_score(value: float, mean: float, std: float) -> float:
    if std == 0:
        return 0.0
    return (value - mean) / std


def normalize_anomaly_severity(metric_value: float, history: list[float]) -> tuple[float, str]:
    """Z-score based severity. z <1 → normal, 1-2 → mild, 2-3 → notable, 3+ → severe."""
    if len(history) < 5:
        return 0.5, "insufficient_data"

    mean = sum(history) / len(history)
    variance = sum((x - mean) ** 2 for x in history) / (len(history) - 1)
    std = math.sqrt(variance) if variance > 0 else 0
    z = compute_z_score(metric_value, mean, std)
    abs_z = abs(z)

    if abs_z < 1:
        return round(abs_z * 0.2, 2), "normal"
    if abs_z < 2:
        return round(0.2 + (abs_z - 1) * 0.3, 2), "mild"
    if abs_z < 3:
        return round(0.5 + (abs_z - 2) * 0.3, 2), "notable"
    return 1.0, "severe"


class BehavioralDetector:
    """Layer 1: Detection - Computes behavioral metrics from existing data"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def compute_profile(self, user_id: int, company_id: int, period_start: date, period_end: date) -> BehavioralProfile:
        user_result = await self.db.execute(
            select(User).where(User.id == user_id).options(selectinload(User.company_rel)),
        )
        user = user_result.scalar_one_or_none()
        if not user:
            raise ValueError(f"User {user_id} not found")

        punctuality = await self._compute_punctuality(user_id, company_id, period_start, period_end)
        efficiency = await self._compute_efficiency(user_id, company_id, period_start, period_end)
        overtime = await self._compute_overtime(user_id, company_id, period_start, period_end)
        burnout = await self._compute_burnout_risk(user_id, company_id, period_start, period_end, overtime)
        financial = await self._compute_financial_stress(user_id, company_id, period_start, period_end)
        attendance = await self._compute_attendance(user_id, company_id, period_start, period_end)
        scrap = await self._compute_scrap_rate(user_id, company_id, period_start, period_end)

        burnout_adjusted, burnout_conf = await self._triangulate_burnout(user_id, company_id, burnout)
        attendance_adjusted, engagement_conf = await self._triangulate_engagement(user_id, company_id, attendance)
        burnout = burnout_adjusted
        attendance = attendance_adjusted
        profile_confidence = min(burnout_conf, engagement_conf)

        thresholds = await self._get_thresholds(company_id)
        await self._get_weights(company_id)

        hire_date = user.contract_start_date or user.created_at.date() if hasattr(user, "created_at") else period_start
        tenure_days = (period_end - hire_date).days if hire_date else 0
        probation_days = getattr(user.company_rel, "probation_period_days", 90) if user.company_rel else 90
        probation_mode = tenure_days <= probation_days

        status = self._determine_status(punctuality, efficiency, burnout, financial, attendance, thresholds, probation_mode)
        contribution_factors = self._compute_contribution_factors(burnout, overtime, attendance, scrap)

        profile_result = await self.db.execute(
            select(BehavioralProfile).where(
                BehavioralProfile.user_id == user_id,
                BehavioralProfile.period_start == period_start,
                BehavioralProfile.period_end == period_end,
            ),
        )
        profile = profile_result.scalar_one_or_none()

        employee_type = getattr(user, "employment_type", "full_time") or "full_time"

        if not profile:
            profile = BehavioralProfile(
                user_id=user_id, company_id=company_id,
                period_start=period_start, period_end=period_end,
                employee_type=employee_type,
            )
            self.db.add(profile)

        profile.tenure_days = max(0, tenure_days)
        profile.probation_mode = probation_mode
        profile.punctuality_score = punctuality
        profile.efficiency_score = efficiency
        profile.overtime_score = overtime
        profile.burnout_risk = burnout
        profile.financial_stress_score = financial
        profile.attendance_score = attendance
        profile.scrap_rate = scrap

        severity_history = await self._get_metric_history(user_id, company_id, "burnout_risk", days=90)
        severity, label = normalize_anomaly_severity(burnout, severity_history)
        profile.anomaly_severity_score = severity
        profile.anomaly_severity_label = label
        profile.status = status
        profile.confidence_score = profile_confidence
        profile.contribution_factors = contribution_factors
        profile.computed_at = datetime.now(ZoneInfo(settings.TIMEZONE)).replace(tzinfo=None)
        profile.version += 1

        return profile

    async def compute_all_profiles(self, company_id: int, period_start: date, period_end: date, incremental: bool = True) -> list[BehavioralProfile]:
        stmt = select(User.id).where(User.company_id == company_id, User.is_active)
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
            select(
                TimeLog.id, TimeLog.start_time,
                func.date(TimeLog.start_time).label("log_date"),
                Shift.start_time.label("shift_start"),
                Shift.tolerance_minutes,
            )
            .join(WorkSchedule,
                  (WorkSchedule.user_id == TimeLog.user_id) &
                  (func.date(TimeLog.start_time) == WorkSchedule.date),
                  isouter=True)
            .join(Shift, WorkSchedule.shift_id == Shift.id, isouter=True)
            .where(
                TimeLog.user_id == user_id,
                TimeLog.start_time >= start_dt,
                TimeLog.start_time <= end_dt,
                TimeLog.type == "work",
            )
            .order_by(TimeLog.start_time),
        )
        rows = logs_result.all()

        if not rows:
            return 100.0

        on_time = 0
        for row in rows:
            if row.shift_start is None:
                on_time += 1
                continue

            log_time = row.start_time.time()
            tolerance = timedelta(minutes=row.tolerance_minutes or 15)

            shift_start_dt = datetime.combine(row.start_time.date(), row.shift_start)
            grace_end = (shift_start_dt + tolerance).time()

            if log_time <= grace_end:
                on_time += 1

        return (on_time / len(rows)) * 100.0

    async def _compute_efficiency(self, user_id: int, company_id: int, start: date, end: date) -> float:
        tasks_result = await self.db.execute(
            select(ProductionTask.id, ProductionTask.started_at, ProductionTask.completed_at, RecipeStep.estimated_duration_minutes)
            .join(RecipeStep, ProductionTask.step_id == RecipeStep.id, isouter=True)
            .where(
                ProductionTask.assigned_user_id == user_id,
                ProductionTask.completed_at.isnot(None),
                ProductionTask.started_at.isnot(None),
                ProductionTask.completed_at >= datetime.combine(start, datetime.min.time()),
                ProductionTask.completed_at <= datetime.combine(end, datetime.max.time()),
            ),
        )
        rows = tasks_result.all()
        if not rows:
            return 100.0

        efficiencies = []
        for row in rows:
            estimated = row.estimated_duration_minutes
            if not estimated or estimated <= 0:
                continue
            actual = (row.completed_at - row.started_at).total_seconds() / 60.0
            if actual <= 0:
                continue
            eff = min(100.0, (estimated / actual) * 100.0)
            efficiencies.append(eff)

        return sum(efficiencies) / len(efficiencies) if efficiencies else 100.0

    async def _compute_overtime(self, user_id: int, company_id: int, start: date, end: date) -> float:
        ot_result = await self.db.execute(
            select(func.sum(OvertimeWork.hours)).where(
                OvertimeWork.user_id == user_id,
                OvertimeWork.date >= start,
                OvertimeWork.date <= end,
            ),
        )
        total_ot = ot_result.scalar() or Decimal(0)
        weeks = max(1, (end - start).days / 7)
        ot_per_week = float(total_ot) / weeks
        return min(100.0, (ot_per_week / 10.0) * 100.0)

    async def _compute_burnout_risk(self, user_id: int, company_id: int, start: date, end: date, overtime_score: float) -> float:
        leave_result = await self.db.execute(
            select(func.count(LeaveRequest.id)).where(
                LeaveRequest.user_id == user_id,
                LeaveRequest.start_date >= start,
                LeaveRequest.end_date <= end,
                LeaveRequest.status.in_(["approved", "pending"]),
            ),
        )
        leave_days = leave_result.scalar() or 0
        leave_penalty = min(0.3, (leave_days / 10.0) * 0.3)

        ot_factor = (overtime_score / 100.0) * 0.5
        return min(1.0, ot_factor + leave_penalty)

    async def _compute_financial_stress(self, user_id: int, company_id: int, start: date, end: date) -> float:
        adv_result = await self.db.execute(
            select(func.count(AdvancePayment.id)).where(
                AdvancePayment.user_id == user_id,
                AdvancePayment.payment_date >= start,
                AdvancePayment.payment_date <= end,
            ),
        )
        advances = adv_result.scalar() or 0
        return min(1.0, (advances / 3.0) * 0.8)

    async def _compute_attendance(self, user_id: int, company_id: int, start: date, end: date) -> float:
        start_dt = datetime.combine(start, datetime.min.time())
        end_dt = datetime.combine(end, datetime.max.time())

        logs_result = await self.db.execute(
            select(func.count(TimeLog.id)).where(
                TimeLog.user_id == user_id,
                TimeLog.start_time >= start_dt,
                TimeLog.start_time <= end_dt,
                TimeLog.type == "work",
            ),
        )
        presence_days = logs_result.scalar() or 0
        expected_days = max(1, (end - start).days * 5 / 7)
        return min(100.0, (presence_days / expected_days) * 100.0)

    async def _compute_scrap_rate(self, user_id: int, company_id: int, start: date, end: date) -> float:
        scrap_result = await self.db.execute(
            select(func.sum(ProductionScrapLog.quantity)).where(
                ProductionScrapLog.user_id == user_id,
                ProductionScrapLog.created_at >= datetime.combine(start, datetime.min.time()),
                ProductionScrapLog.created_at <= datetime.combine(end, datetime.max.time()),
            ),
        )
        total_scrap = scrap_result.scalar() or Decimal(0)
        return min(100.0, float(total_scrap) * 2.0)

    async def _get_metric_history(self, user_id: int, company_id: int, metric: str, days: int = 90) -> list[float]:
        """Fetch historical values of a metric from past BehavioralProfile records."""
        period_start = date.today() - timedelta(days=days)
        res = await self.db.execute(
            select(getattr(BehavioralProfile, metric))
            .where(
                BehavioralProfile.user_id == user_id,
                BehavioralProfile.company_id == company_id,
                BehavioralProfile.period_start >= period_start,
            )
            .order_by(BehavioralProfile.period_start),
        )
        return [float(r[0]) for r in res.all() if r[0] is not None]

    async def _get_latest_pulse(self, user_id: int, company_id: int) -> BehavioralPulseSurvey | None:
        res = await self.db.execute(
            select(BehavioralPulseSurvey)
            .where(
                BehavioralPulseSurvey.user_id == user_id,
                BehavioralPulseSurvey.company_id == company_id,
            )
            .order_by(BehavioralPulseSurvey.submitted_at.desc())
            .limit(1),
        )
        return res.scalar_one_or_none()

    async def _triangulate_burnout(self, user_id: int, company_id: int, objective_burnout: float) -> tuple[float, float]:
        pulse = await self._get_latest_pulse(user_id, company_id)

        if not pulse or pulse.burnout_feeling is None:
            return objective_burnout, 0.7

        pulse_burnout = (pulse.burnout_feeling - 1) / 4.0
        adjusted = (objective_burnout * 0.6) + (pulse_burnout * 0.4)
        diff = abs(objective_burnout - pulse_burnout)
        confidence = max(0.3, min(1.0, 1.0 - diff))

        return min(1.0, adjusted), confidence

    async def _triangulate_engagement(self, user_id: int, company_id: int, objective_attendance: float) -> tuple[float, float]:
        pulse = await self._get_latest_pulse(user_id, company_id)

        if not pulse or pulse.engagement_feeling is None:
            return objective_attendance, 0.7

        pulse_engagement = ((pulse.engagement_feeling - 1) / 4.0) * 100.0
        adjusted = (objective_attendance * 0.4) + (pulse_engagement * 0.6)
        diff = abs(objective_attendance - pulse_engagement) / 100.0
        confidence = max(0.3, min(1.0, 1.0 - diff))

        return min(100.0, adjusted), confidence

    async def _detect_trend(self, user_id: int, company_id: int, metric: str, days: int = 90) -> dict:
        values = await self._get_metric_history(user_id, company_id, metric, days)
        direction, p_value = mann_kendall_trend(values)

        if p_value < 0.01:
            confidence = 0.95
        elif p_value < 0.05:
            confidence = 0.80
        elif p_value < 0.10:
            confidence = 0.60
        else:
            confidence = 0.30

        return {"direction": direction, "p_value": round(p_value, 4), "confidence": confidence}

    async def _get_thresholds(self, company_id: int) -> BehavioralStatusThresholds | None:
        res = await self.db.execute(select(BehavioralStatusThresholds).where(BehavioralStatusThresholds.company_id == company_id))
        return res.scalar_one_or_none()

    async def _get_weights(self, company_id: int) -> BehavioralMetricWeights | None:
        res = await self.db.execute(select(BehavioralMetricWeights).where(BehavioralMetricWeights.company_id == company_id))
        return res.scalar_one_or_none()

    def _determine_status(self, punctuality: float, efficiency: float, burnout: float, financial: float, attendance: float, thresholds: BehavioralStatusThresholds | None, probation_mode: bool) -> str:
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

    def _compute_contribution_factors(self, burnout: float, overtime: float, attendance: float, scrap: float) -> dict[str, float]:
        total = max(0.01, burnout + (overtime/100) + (1 - attendance/100) + (scrap/100))
        return {
            "burnout_risk": round(burnout / total, 2),
            "overtime_hours": round((overtime/100) / total, 2),
            "engagement_drop": round((1 - attendance/100) / total, 2),
            "scrap_rate": round((scrap/100) / total, 2),
        }

    async def _update_system_health(self, company_id: int, processed: int, failed: int):
        res = await self.db.execute(select(BehavioralSystemHealth).where(BehavioralSystemHealth.company_id == company_id))
        health = res.scalar_one_or_none()
        if not health:
            health = BehavioralSystemHealth(company_id=company_id)
            self.db.add(health)

        health.last_computation_at = datetime.now(ZoneInfo(settings.TIMEZONE)).replace(tzinfo=None)
        health.last_computation_status = "success" if failed == 0 else "partial"
        health.employees_processed = processed
        health.employees_failed = failed
        await self.db.commit()
