
import strawberry
from backend.database.models import User
from backend.modules.behavioral_analysis.graphql.types import (
    BehavioralAnomalyType,
    BehavioralPersonalityProfileType,
    BehavioralProfileType,
    BehavioralRecommendationType,
    BehavioralRuleType,
    BehavioralSettingsType,
    BehavioralSystemHealthType,
    BiasReportType,
    ManagerEffectivenessType,
    OrganizationalHealthType,
    PersonalityQuestionType,
    PersonalityTestAssignmentType,
    PersonalityTestTemplateType,
)
from backend.modules.behavioral_analysis.models import (
    BehavioralAnomaly,
    BehavioralPersonalityProfile,
    BehavioralPersonalityTestAssignment,
    BehavioralPersonalityTestTemplate,
    BehavioralProfile,
    BehavioralRecommendation,
    BehavioralRetentionSettings,
    BehavioralRule,
    BehavioralSystemHealth,
    BiasReport,
    DepartmentHealthReport,
    ManagerEffectiveness,
)
from backend.modules.behavioral_analysis.personality import load_all_questions
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
                attendance_score=p.attendance_score,
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
                avg_attendance=r.avg_attendance,
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
    async def personality_templates(self, info: Info) -> list[PersonalityTestTemplateType]:
        db = info.context["db"]
        current_user: User = info.context["current_user"]

        stmt = select(BehavioralPersonalityTestTemplate).where(
            BehavioralPersonalityTestTemplate.company_id == current_user.company_id,
        )
        result = await db.execute(stmt)
        return [
            PersonalityTestTemplateType(
                id=t.id, company_id=t.company_id, name=t.name,
                selected_question_ids=t.selected_question_ids,
                shuffle=t.shuffle, is_active=t.is_active,
                created_by=t.created_by, created_at=t.created_at,
            )
            for t in result.scalars().all()
        ]

    @strawberry.field
    async def personality_questions(
        self, info: Info, template_id: int | None = None,
    ) -> list[PersonalityQuestionType]:
        db = info.context["db"]
        current_user: User = info.context["current_user"]

        all_questions = load_all_questions()

        if template_id is not None:
            result = await db.execute(
                select(BehavioralPersonalityTestTemplate).where(
                    BehavioralPersonalityTestTemplate.id == template_id,
                    BehavioralPersonalityTestTemplate.company_id == current_user.company_id,
                ),
            )
            template = result.scalar_one_or_none()
            if template:
                ids = set(template.selected_question_ids)
                all_questions = [q for q in all_questions if q["id"] in ids]

        return [
            PersonalityQuestionType(
                id=q["id"], bg=q["bg"], en=q["en"],
                factor=q["factor"], direction=q["direction"],
            )
            for q in all_questions
        ]

    @strawberry.field
    async def personality_profiles(
        self, info: Info, user_id: int | None = None,
    ) -> list[BehavioralPersonalityProfileType]:
        db = info.context["db"]
        current_user: User = info.context["current_user"]

        stmt = select(BehavioralPersonalityProfile).order_by(BehavioralPersonalityProfile.completed_at.desc())

        if current_user.role.name not in ["admin", "super_admin"]:
            stmt = stmt.where(BehavioralPersonalityProfile.user_id == current_user.id)
        elif user_id:
            stmt = stmt.where(BehavioralPersonalityProfile.user_id == user_id)

        result = await db.execute(stmt)
        return [
            BehavioralPersonalityProfileType(
                id=p.id, user_id=p.user_id, company_id=p.company_id,
                template_id=p.template_id, completed_at=p.completed_at,
                openness=p.openness, conscientiousness=p.conscientiousness,
                extraversion=p.extraversion, agreeableness=p.agreeableness,
                neuroticism=p.neuroticism,
                openness_raw=p.openness_raw, conscientiousness_raw=p.conscientiousness_raw,
                extraversion_raw=p.extraversion_raw, agreeableness_raw=p.agreeableness_raw,
                neuroticism_raw=p.neuroticism_raw,
                interpretation=p.interpretation,
            )
            for p in result.scalars().all()
        ]

    @strawberry.field
    async def manager_effectiveness(
        self, info: Info, manager_id: int | None = None,
    ) -> list[ManagerEffectivenessType]:
        db = info.context["db"]
        current_user: User = info.context["current_user"]

        stmt = select(ManagerEffectiveness).where(
            ManagerEffectiveness.company_id == current_user.company_id,
        ).order_by(ManagerEffectiveness.computed_at.desc())

        if manager_id:
            stmt = stmt.where(ManagerEffectiveness.manager_id == manager_id)
        elif current_user.role.name not in ["admin", "super_admin"]:
            stmt = stmt.where(ManagerEffectiveness.manager_id == current_user.id)

        result = await db.execute(stmt)
        return [
            ManagerEffectivenessType(
                id=m.id, manager_id=m.manager_id, company_id=m.company_id,
                period_start=m.period_start, period_end=m.period_end,
                team_avg_attendance=m.team_avg_attendance,
                team_avg_engagement=m.team_avg_engagement,
                team_avg_burnout=m.team_avg_burnout,
                team_burnout_variance=m.team_burnout_variance,
                team_turnover_rate=m.team_turnover_rate,
                team_size=m.team_size, team_anomaly_count=m.team_anomaly_count,
                manager_effectiveness_score=m.manager_effectiveness_score,
                sentiment_score=m.sentiment_score, trend_direction=m.trend_direction,
                computed_at=m.computed_at,
            )
            for m in result.scalars().all()
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

    @strawberry.field
    async def personality_test_assignments(
        self,
        info: Info,
        user_id: int | None = None,
        status: str | None = None,
    ) -> list[PersonalityTestAssignmentType]:
        db = info.context["db"]
        current_user: User = info.context["current_user"]
        stmt = (
            select(BehavioralPersonalityTestAssignment)
            .where(BehavioralPersonalityTestAssignment.company_id == current_user.company_id)
        )
        if user_id:
            stmt = stmt.where(BehavioralPersonalityTestAssignment.user_id == user_id)
        if status:
            stmt = stmt.where(BehavioralPersonalityTestAssignment.status == status)
        stmt = stmt.order_by(BehavioralPersonalityTestAssignment.assigned_at.desc())
        result = await db.execute(stmt)
        assignments = result.scalars().all()

        user_ids = {a.user_id for a in assignments}
        assigner_ids = {a.assigned_by for a in assignments}
        template_ids = {a.template_id for a in assignments}

        all_users_result = await db.execute(
            select(User.id, User.first_name, User.last_name, User.email).where(User.id.in_(user_ids | assigner_ids)),
        )
        users = all_users_result.all()
        user_name_map = {u.id: f"{u.first_name or ''} {u.last_name or ''}".strip() for u in users}
        user_email_map = {u.id: u.email for u in users}

        templates_result = await db.execute(
            select(BehavioralPersonalityTestTemplate.id, BehavioralPersonalityTestTemplate.name).where(
                BehavioralPersonalityTestTemplate.id.in_(template_ids),
            ),
        )
        template_map = {t.id: t.name for t in templates_result.all()}

        result_list: list[PersonalityTestAssignmentType] = []
        for a in assignments:
            result_list.append(PersonalityTestAssignmentType(
                id=a.id,
                user_id=a.user_id,
                company_id=a.company_id,
                template_id=a.template_id,
                assigned_by=a.assigned_by,
                assigned_at=a.assigned_at,
                due_by=a.due_by,
                completed_at=a.completed_at,
                status=a.status,
                notified_overdue=a.notified_overdue,
                user_name=user_name_map.get(a.user_id, ""),
                user_email=user_email_map.get(a.user_id, ""),
                template_name=template_map.get(a.template_id, ""),
                assigner_name=user_name_map.get(a.assigned_by, ""),
            ))
        return result_list
