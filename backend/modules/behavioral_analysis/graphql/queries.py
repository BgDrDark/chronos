
import strawberry
from backend.database.models import User
from backend.modules.behavioral_analysis.graphql.types import (
    BehavioralAnomalyType,
    BehavioralProfileType,
    BehavioralRecommendationType,
    BehavioralRuleType,
    BehavioralSettingsType,
    BehavioralSystemHealthType,
    BiasReportType,
    OrganizationalHealthType,
)
from backend.modules.behavioral_analysis.models import (
    BehavioralAnomaly,
    BehavioralProfile,
    BehavioralRecommendation,
    BehavioralRetentionSettings,
    BehavioralRule,
    BehavioralSystemHealth,
    BiasReport,
    DepartmentHealthReport,
)
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from strawberry.types import Info


@strawberry.type
class BehavioralQuery:
    @strawberry.field
    async def behavioral_profiles(
        self, info: Info, company_id: int | None = None, user_id: int | None = None,
    ) -> list[BehavioralProfileType]:
        db = info.context["db"]
        current_user: User = info.context["current_user"]

        stmt = select(BehavioralProfile).options(selectinload(BehavioralProfile.anomalies))

        if current_user.role.name not in ["admin", "super_admin"]:
            stmt = stmt.where(BehavioralProfile.user_id == current_user.id)
        elif company_id:
            stmt = stmt.where(BehavioralProfile.company_id == company_id)

        if user_id:
            stmt = stmt.where(BehavioralProfile.user_id == user_id)

        result = await db.execute(stmt.order_by(BehavioralProfile.computed_at.desc()))
        profiles = result.scalars().all()

        return [
            BehavioralProfileType(
                id=p.id,
                user_id=p.user_id,
                company_id=p.company_id,
                period_start=p.period_start,
                period_end=p.period_end,
                employee_type=p.employee_type,
                tenure_days=p.tenure_days,
                probation_mode=p.probation_mode,
                data_completeness=p.data_completeness,
                punctuality_score=p.punctuality_score,
                efficiency_score=p.efficiency_score,
                overtime_score=p.overtime_score,
                burnout_risk=p.burnout_risk,
                financial_stress_score=p.financial_stress_score,
                engagement_score=p.engagement_score,
                scrap_rate=p.scrap_rate,
                peer_group_percentile=p.peer_group_percentile,
                trend_direction=p.trend_direction,
                status=p.status,
                confidence_score=p.confidence_score,
                contribution_factors=p.contribution_factors,
                rule_engine_version=p.rule_engine_version,
                computed_at=p.computed_at,
                version=p.version,
            )
            for p in profiles
        ]

    @strawberry.field
    async def behavioral_anomalies(
        self, info: Info, profile_id: int | None = None, user_id: int | None = None,
    ) -> list[BehavioralAnomalyType]:
        db = info.context["db"]
        current_user: User = info.context["current_user"]

        stmt = select(BehavioralAnomaly)

        if current_user.role.name not in ["admin", "super_admin"]:
            stmt = stmt.where(BehavioralAnomaly.user_id == current_user.id)

        if profile_id:
            stmt = stmt.where(BehavioralAnomaly.profile_id == profile_id)
        if user_id:
            stmt = stmt.where(BehavioralAnomaly.user_id == user_id)

        result = await db.execute(stmt.order_by(BehavioralAnomaly.detected_at.desc()))
        anomalies = result.scalars().all()

        return [
            BehavioralAnomalyType(
                id=a.id,
                profile_id=a.profile_id,
                user_id=a.user_id,
                anomaly_type=a.anomaly_type,
                severity=a.severity,
                metric_name=a.metric_name,
                actual_value=a.actual_value,
                expected_value=a.expected_value,
                deviation=a.deviation,
                confidence_score=a.confidence_score,
                suppressed=a.suppressed,
                suppression_reason=a.suppression_reason,
                description=a.description,
                context_summary=a.context_summary,
                detected_at=a.detected_at,
            )
            for a in anomalies
        ]

    @strawberry.field
    async def behavioral_rules(self, info: Info) -> list[BehavioralRuleType]:
        db = info.context["db"]
        current_user: User = info.context["current_user"]

        stmt = select(BehavioralRule).where(
            BehavioralRule.company_id == current_user.company_id,
        )
        result = await db.execute(stmt.order_by(BehavioralRule.name))
        rules = result.scalars().all()

        return [
            BehavioralRuleType(
                id=r.id,
                name=r.name,
                description=r.description,
                rule_type=r.rule_type,
                is_system=r.is_system,
                is_active=r.is_active,
                shadow_mode=r.shadow_mode,
                company_id=r.company_id,
                condition_type=r.condition_type,
                condition_config=r.condition_config,
                recommendation_template=r.recommendation_template,
                auto_execute_action=r.auto_execute_action,
                auto_execute=r.auto_execute,
                effectiveness_score=r.effectiveness_score,
                false_positive_rate=r.false_positive_rate,
                trigger_count=r.trigger_count,
                accepted_count=r.accepted_count,
                effective_count=r.effective_count,
                false_positive_count=r.false_positive_count,
                created_by=r.created_by,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
            for r in rules
        ]

    @strawberry.field
    async def behavioral_recommendations(
        self, info: Info, user_id: int | None = None, status: str | None = None,
    ) -> list[BehavioralRecommendationType]:
        db = info.context["db"]
        current_user: User = info.context["current_user"]

        stmt = select(BehavioralRecommendation)

        if current_user.role.name not in ["admin", "super_admin"]:
            stmt = stmt.where(BehavioralRecommendation.user_id == current_user.id)
        else:
            stmt = stmt.where(BehavioralRecommendation.user_id.in_(
                select(User.id).where(User.company_id == current_user.company_id),
            ))

        if user_id:
            stmt = stmt.where(BehavioralRecommendation.user_id == user_id)
        if status:
            stmt = stmt.where(BehavioralRecommendation.status == status)

        result = await db.execute(stmt.order_by(BehavioralRecommendation.created_at.desc()))
        recommendations = result.scalars().all()

        return [
            BehavioralRecommendationType(
                id=rec.id,
                rule_id=rec.rule_id,
                user_id=rec.user_id,
                anomaly_id=rec.anomaly_id,
                type=rec.type,
                priority=rec.priority,
                title=rec.title,
                description=rec.description,
                suggested_action=rec.suggested_action,
                explanation=rec.explanation,
                coaching_tips=rec.coaching_tips,
                confidence_score=rec.confidence_score,
                status=rec.status,
                auto_executed=rec.auto_executed,
                throttled=rec.throttled,
                aggregated_count=rec.aggregated_count,
                dispute_reason=rec.dispute_reason,
                dispute_notes=rec.dispute_notes,
                created_at=rec.created_at,
                expires_at=rec.expires_at,
            )
            for rec in recommendations
        ]

    @strawberry.field
    async def behavioral_settings(self, info: Info) -> BehavioralSettingsType | None:
        db = info.context["db"]
        current_user: User = info.context["current_user"]

        result = await db.execute(
            select(BehavioralRetentionSettings).where(
                BehavioralRetentionSettings.company_id == current_user.company_id,
            ),
        )
        settings = result.scalar_one_or_none()

        if not settings:
            return None

        return BehavioralSettingsType(
            id=settings.id,
            company_id=settings.company_id,
            raw_profile_days=settings.raw_profile_days,
            aggregated_profile_months=settings.aggregated_profile_months,
            recommendation_months=settings.recommendation_months,
            feedback_months=settings.feedback_months,
            audit_log_months=settings.audit_log_months,
            auto_cleanup_enabled=settings.auto_cleanup_enabled,
            cleanup_schedule=settings.cleanup_schedule,
            anonymize_instead_of_delete=settings.anonymize_instead_of_delete,
            updated_by=settings.updated_by,
            updated_at=settings.updated_at,
        )

    @strawberry.field
    async def organizational_health(self, info: Info, period_start: str | None = None, period_end: str | None = None) -> list[OrganizationalHealthType]:
        db = info.context["db"]
        current_user: User = info.context["current_user"]

        stmt = select(DepartmentHealthReport).where(
            DepartmentHealthReport.company_id == current_user.company_id,
        )
        if period_start:
            stmt = stmt.where(DepartmentHealthReport.period_start >= period_start)
        if period_end:
            stmt = stmt.where(DepartmentHealthReport.period_end <= period_end)

        result = await db.execute(stmt.order_by(DepartmentHealthReport.generated_at.desc()))
        reports = result.scalars().all()

        return [
            OrganizationalHealthType(
                department_id=r.department_id,
                department_name=f"Department {r.department_id}",
                avg_burnout_risk=r.avg_burnout_risk,
                avg_engagement=r.avg_engagement,
                avg_efficiency=r.avg_efficiency,
                avg_punctuality=r.avg_punctuality,
                anomaly_count=r.anomaly_count,
                employee_count=r.employee_count,
                turnover_rate=r.turnover_rate,
                trend=r.trend,
                is_systemic_issue=r.is_systemic_issue,
            )
            for r in reports
        ]

    @strawberry.field
    async def bias_reports(self, info: Info) -> list[BiasReportType]:
        db = info.context["db"]
        current_user: User = info.context["current_user"]

        result = await db.execute(
            select(BiasReport)
            .where(BiasReport.company_id == current_user.company_id)
            .order_by(BiasReport.generated_at.desc()),
        )
        reports = result.scalars().all()

        return [
            BiasReportType(
                id=rep.id,
                company_id=rep.company_id,
                period_start=rep.period_start,
                period_end=rep.period_end,
                findings=rep.findings,
                overall_bias_detected=rep.overall_bias_detected,
                generated_at=rep.generated_at,
            )
            for rep in reports
        ]

    @strawberry.field
    async def behavioral_system_health(self, info: Info, company_id: int | None = None) -> BehavioralSystemHealthType | None:
        db = info.context["db"]
        current_user: User = info.context["current_user"]

        if current_user.role.name not in ["admin", "super_admin"]:
            return None

        cid = company_id or current_user.company_id

        result = await db.execute(
            select(BehavioralSystemHealth).where(BehavioralSystemHealth.company_id == cid),
        )
        health = result.scalar_one_or_none()

        if not health:
            return None

        return BehavioralSystemHealthType(
            id=health.id,
            company_id=health.company_id,
            last_computation_at=health.last_computation_at,
            last_computation_status=health.last_computation_status,
            last_computation_duration_seconds=health.last_computation_duration_seconds,
            employees_processed=health.employees_processed,
            employees_failed=health.employees_failed,
            circuit_breaker_open=health.circuit_breaker_open,
            circuit_breaker_failure_count=health.circuit_breaker_failure_count,
            last_successful_profile_date=health.last_successful_profile_date,
            triggered_alerts_today=health.triggered_alerts_today,
            last_bias_check=health.last_bias_check,
        )
