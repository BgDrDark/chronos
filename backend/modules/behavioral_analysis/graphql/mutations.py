from datetime import date

import strawberry
from backend.database.models import User
from backend.exceptions import NotFoundException, PermissionDeniedException
from backend.modules.behavioral_analysis.feedback_loop import FeedbackLoop
from backend.modules.behavioral_analysis.graphql.types import (
    BehavioralRecommendationType,
    BehavioralRuleType,
    BehavioralSettingsType,
    BiasReportType,
    OrganizationalHealthType,
    RecommendationFeedbackType,
)
from backend.modules.behavioral_analysis.models import (
    BehavioralRecommendation,
    BehavioralRetentionSettings,
    BehavioralRule,
)
from backend.modules.behavioral_analysis.organizational_health import (
    OrganizationalHealth,
)
from sqlalchemy import select
from strawberry.types import Info


@strawberry.input
class BehavioralRuleInput:
    name: str
    description: str | None = None
    rule_type: str = "custom"
    condition_type: str
    condition_config: strawberry.scalars.JSON
    recommendation_template: strawberry.scalars.JSON
    auto_execute_action: str | None = None
    auto_execute: bool = False
    is_active: bool = True
    shadow_mode: bool = False


@strawberry.input
class BehavioralSettingsInput:
    raw_profile_days: int = 90
    aggregated_profile_months: int = 12
    recommendation_months: int = 6
    feedback_months: int = 24
    audit_log_months: int = 36
    auto_cleanup_enabled: bool = True
    cleanup_schedule: str = "nightly"
    anonymize_instead_of_delete: bool = False


@strawberry.type
class BehavioralMutation:
    @strawberry.mutation
    async def create_behavioral_rule(
        self, info: Info, input: BehavioralRuleInput,
    ) -> BehavioralRuleType:
        db = info.context["db"]
        current_user: User = info.context["current_user"]

        if current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("create behavioral rule")

        rule = BehavioralRule(
            name=input.name,
            description=input.description,
            rule_type=input.rule_type,
            is_system=False,
            is_active=input.is_active,
            shadow_mode=input.shadow_mode,
            company_id=current_user.company_id,
            condition_type=input.condition_type,
            condition_config=input.condition_config,
            recommendation_template=input.recommendation_template,
            auto_execute_action=input.auto_execute_action,
            auto_execute=input.auto_execute,
            created_by=current_user.id,
        )
        db.add(rule)
        await db.commit()
        await db.refresh(rule)

        return BehavioralRuleType(
            id=rule.id,
            name=rule.name,
            description=rule.description,
            rule_type=rule.rule_type,
            is_system=rule.is_system,
            is_active=rule.is_active,
            shadow_mode=rule.shadow_mode,
            company_id=rule.company_id,
            condition_type=rule.condition_type,
            condition_config=rule.condition_config,
            recommendation_template=rule.recommendation_template,
            auto_execute_action=rule.auto_execute_action,
            auto_execute=rule.auto_execute,
            effectiveness_score=rule.effectiveness_score,
            false_positive_rate=rule.false_positive_rate,
            trigger_count=rule.trigger_count,
            accepted_count=rule.accepted_count,
            effective_count=rule.effective_count,
            false_positive_count=rule.false_positive_count,
            created_by=rule.created_by,
            created_at=rule.created_at,
            updated_at=rule.updated_at,
        )

    @strawberry.mutation
    async def update_behavioral_rule(
        self, info: Info, rule_id: int, input: BehavioralRuleInput,
    ) -> BehavioralRuleType:
        db = info.context["db"]
        current_user: User = info.context["current_user"]

        result = await db.execute(
            select(BehavioralRule).where(
                BehavioralRule.id == rule_id,
                BehavioralRule.company_id == current_user.company_id,
            ),
        )
        rule = result.scalar_one_or_none()
        if not rule:
            raise NotFoundException.resource("BehavioralRule", rule_id=rule_id)

        if rule.is_system and current_user.role.name != "super_admin":
            raise PermissionDeniedException.for_action("update system rule")

        rule.name = input.name
        rule.description = input.description
        rule.condition_type = input.condition_type
        rule.condition_config = input.condition_config
        rule.recommendation_template = input.recommendation_template
        rule.auto_execute_action = input.auto_execute_action
        rule.auto_execute = input.auto_execute
        rule.is_active = input.is_active
        rule.shadow_mode = input.shadow_mode

        await db.commit()
        await db.refresh(rule)

        return BehavioralRuleType(
            id=rule.id,
            name=rule.name,
            description=rule.description,
            rule_type=rule.rule_type,
            is_system=rule.is_system,
            is_active=rule.is_active,
            shadow_mode=rule.shadow_mode,
            company_id=rule.company_id,
            condition_type=rule.condition_type,
            condition_config=rule.condition_config,
            recommendation_template=rule.recommendation_template,
            auto_execute_action=rule.auto_execute_action,
            auto_execute=rule.auto_execute,
            effectiveness_score=rule.effectiveness_score,
            false_positive_rate=rule.false_positive_rate,
            trigger_count=rule.trigger_count,
            accepted_count=rule.accepted_count,
            effective_count=rule.effective_count,
            false_positive_count=rule.false_positive_count,
            created_by=rule.created_by,
            created_at=rule.created_at,
            updated_at=rule.updated_at,
        )

    @strawberry.mutation
    async def delete_behavioral_rule(self, info: Info, rule_id: int) -> bool:
        db = info.context["db"]
        current_user: User = info.context["current_user"]

        result = await db.execute(
            select(BehavioralRule).where(
                BehavioralRule.id == rule_id,
                BehavioralRule.company_id == current_user.company_id,
            ),
        )
        rule = result.scalar_one_or_none()
        if not rule:
            raise NotFoundException.resource("BehavioralRule", rule_id=rule_id)

        if rule.is_system:
            raise PermissionDeniedException.for_action("delete system rule")

        await db.delete(rule)
        await db.commit()
        return True

    @strawberry.mutation
    async def update_behavioral_settings(
        self, info: Info, input: BehavioralSettingsInput,
    ) -> BehavioralSettingsType:
        db = info.context["db"]
        current_user: User = info.context["current_user"]

        if current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("update behavioral settings")

        result = await db.execute(
            select(BehavioralRetentionSettings).where(
                BehavioralRetentionSettings.company_id == current_user.company_id,
            ),
        )
        settings = result.scalar_one_or_none()

        if not settings:
            settings = BehavioralRetentionSettings(
                company_id=current_user.company_id,
                updated_by=current_user.id,
            )
            db.add(settings)

        settings.raw_profile_days = input.raw_profile_days
        settings.aggregated_profile_months = input.aggregated_profile_months
        settings.recommendation_months = input.recommendation_months
        settings.feedback_months = input.feedback_months
        settings.audit_log_months = input.audit_log_months
        settings.auto_cleanup_enabled = input.auto_cleanup_enabled
        settings.cleanup_schedule = input.cleanup_schedule
        settings.anonymize_instead_of_delete = input.anonymize_instead_of_delete
        settings.updated_by = current_user.id

        await db.commit()
        await db.refresh(settings)

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

    @strawberry.mutation
    async def update_recommendation_status(
        self, info: Info, recommendation_id: int, status: str, dispute_reason: str | None = None, dispute_notes: str | None = None,
    ) -> BehavioralRecommendationType:
        db = info.context["db"]
        current_user: User = info.context["current_user"]

        result = await db.execute(
            select(BehavioralRecommendation).where(
                BehavioralRecommendation.id == recommendation_id,
                BehavioralRecommendation.user_id == current_user.id,
            ),
        )
        rec = result.scalar_one_or_none()
        if not rec:
            raise NotFoundException.resource("Recommendation", id=recommendation_id)

        rec.status = status
        if dispute_reason:
            rec.dispute_reason = dispute_reason
        if dispute_notes:
            rec.dispute_notes = dispute_notes

        await db.commit()
        await db.refresh(rec)

        return BehavioralRecommendationType(
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

    @strawberry.mutation
    async def record_recommendation_feedback(
        self, info: Info, recommendation_id: int, action: str, notes: str | None = None,
    ) -> RecommendationFeedbackType:
        db = info.context["db"]
        current_user: User = info.context["current_user"]

        if current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("record feedback")

        loop = FeedbackLoop(db)
        feedback = await loop.record_feedback(
            recommendation_id=recommendation_id,
            manager_id=current_user.id,
            action=action,
            notes=notes,
        )

        return RecommendationFeedbackType(
            id=feedback.id,
            recommendation_id=feedback.recommendation_id,
            manager_id=feedback.manager_id,
            manager_action=feedback.manager_action,
            manager_notes=feedback.manager_notes,
            action_taken_at=feedback.action_taken_at,
            outcome=feedback.outcome,
            outcome_measured_at=feedback.outcome_measured_at,
            days_to_outcome=feedback.days_to_outcome,
            metric_before=feedback.metric_before,
            metric_after=feedback.metric_after,
            improvement_delta=feedback.improvement_delta,
        )

    @strawberry.mutation
    async def compute_organizational_health(
        self, info: Info, period_start: str | None = None, period_end: str | None = None,
    ) -> list[OrganizationalHealthType]:
        db = info.context["db"]
        current_user: User = info.context["current_user"]

        if current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("compute health")

        start = date.fromisoformat(period_start) if period_start else date.today().replace(day=1)
        end = date.fromisoformat(period_end) if period_end else date.today()

        health = OrganizationalHealth(db)
        reports = await health.generate_department_reports(current_user.company_id, start, end)

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

    @strawberry.mutation
    async def compute_bias_report(
        self, info: Info, period_start: str | None = None, period_end: str | None = None,
    ) -> BiasReportType:
        db = info.context["db"]
        current_user: User = info.context["current_user"]

        if current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("compute bias report")

        start = date.fromisoformat(period_start) if period_start else date.today().replace(day=1)
        end = date.fromisoformat(period_end) if period_end else date.today()

        health = OrganizationalHealth(db)
        report = await health.generate_bias_report(current_user.company_id, start, end)

        return BiasReportType(
            id=report.id,
            company_id=report.company_id,
            period_start=report.period_start,
            period_end=report.period_end,
            findings=report.findings,
            overall_bias_detected=report.overall_bias_detected,
            generated_at=report.generated_at,
        )
