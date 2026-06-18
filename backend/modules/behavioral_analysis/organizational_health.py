import logging
from datetime import date, datetime
from zoneinfo import ZoneInfo

from backend.config import settings
from backend.database.models import Department, Position, User
from backend.modules.behavioral_analysis.models import (
    BehavioralProfile,
    BiasReport,
    DepartmentHealthReport,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

class OrganizationalHealth:
    """Generates department heatmaps and bias reports"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_department_reports(self, company_id: int, period_start: date, period_end: date) -> list[DepartmentHealthReport]:
        depts_result = await self.db.execute(
            select(Department).where(Department.company_id == company_id),
        )
        departments = depts_result.scalars().all()

        reports = []
        for dept in departments:
            stmt = (
                select(
                    func.avg(BehavioralProfile.burnout_risk).label("avg_burnout"),
                    func.avg(BehavioralProfile.attendance_score).label("avg_attendance"),
                    func.avg(BehavioralProfile.efficiency_score).label("avg_efficiency"),
                    func.avg(BehavioralProfile.punctuality_score).label("avg_punctuality"),
                    func.count(BehavioralProfile.id).label("count"),
                )
                .join(User, BehavioralProfile.user_id == User.id)
                .join(Position, User.position_id == Position.id)
                .where(
                    Position.department_id == dept.id,
                    BehavioralProfile.period_start >= period_start,
                    BehavioralProfile.period_end <= period_end,
                )
            )
            result = await self.db.execute(stmt)
            row = result.first()

            if row and row.count > 0:
                report = DepartmentHealthReport(
                    company_id=company_id,
                    department_id=dept.id,
                    period_start=period_start,
                    period_end=period_end,
                    avg_burnout_risk=float(row.avg_burnout or 0),
                    avg_attendance=float(row.avg_attendance or 0),
                    avg_efficiency=float(row.avg_efficiency or 0),
                    avg_punctuality=float(row.avg_punctuality or 0),
                    anomaly_count=0,
                    employee_count=int(row.count),
                    turnover_rate=0.0,
                    trend="stable",
                    is_systemic_issue=(row.avg_burnout or 0) > 0.7,
                )
                self.db.add(report)
                reports.append(report)

        await self.db.commit()
        return reports

    async def generate_bias_report(self, company_id: int, period_start: date, period_end: date) -> BiasReport:
        findings = []

        depts_result = await self.db.execute(select(Department).where(Department.company_id == company_id))
        departments = depts_result.scalars().all()

        if len(departments) < 2:
            return BiasReport(
                company_id=company_id,
                period_start=period_start,
                period_end=period_end,
                findings=[],
                overall_bias_detected=False,
                generated_at=datetime.now(ZoneInfo(settings.TIMEZONE)).replace(tzinfo=None),
            )

        for i in range(len(departments)):
            for j in range(i + 1, len(departments)):
                dept_a = departments[i]
                dept_b = departments[j]

                avg_a = await self._get_dept_avg(dept_a.id, period_start, period_end, "burnout_risk")
                avg_b = await self._get_dept_avg(dept_b.id, period_start, period_end, "burnout_risk")

                if avg_a is not None and avg_b is not None and abs(avg_a - avg_b) > 0.2:
                    findings.append({
                        "metric": "burnout_risk",
                        "group_a": dept_a.name,
                        "group_b": dept_b.name,
                        "group_a_avg": avg_a,
                        "group_b_avg": avg_b,
                        "difference": abs(avg_a - avg_b),
                        "recommendation": f"Review workload distribution between {dept_a.name} and {dept_b.name}",
                    })

        report = BiasReport(
            company_id=company_id,
            period_start=period_start,
            period_end=period_end,
            findings=findings,
            overall_bias_detected=len(findings) > 0,
            generated_at=datetime.now(ZoneInfo(settings.TIMEZONE)).replace(tzinfo=None),
        )
        self.db.add(report)
        await self.db.commit()
        return report

    async def _get_dept_avg(self, dept_id: int, start: date, end: date, metric: str) -> float:
        stmt = (
            select(func.avg(getattr(BehavioralProfile, metric)))
            .join(User, BehavioralProfile.user_id == User.id)
            .join(Position, User.position_id == Position.id)
            .where(
                Position.department_id == dept_id,
                BehavioralProfile.period_start >= start,
                BehavioralProfile.period_end <= end,
            )
        )
        result = await self.db.execute(stmt)
        val = result.scalar()
        return float(val) if val else 0.0
