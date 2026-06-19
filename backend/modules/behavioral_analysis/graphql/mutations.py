from datetime import date, datetime, timedelta

import strawberry
from backend.database.models import User
from backend.exceptions import NotFoundException, PermissionDeniedException, ValidationException
from backend.modules.behavioral_analysis.feedback_loop import FeedbackLoop
from backend.modules.behavioral_analysis.graphql.types import (
    BehavioralPersonalityProfileType,
    BehavioralPulseSurveyType,
    BehavioralRecommendationType,
    BehavioralRuleType,
    BehavioralSettingsType,
    BiasReportType,
    ManagerEffectivenessType,
    OrganizationalHealthType,
    PersonalityTestTemplateType,
    RecommendationFeedbackType,
)
from backend.modules.behavioral_analysis.models import (
    BehavioralAnomaly,
    BehavioralPersonalityProfile,
    BehavioralPersonalityTestTemplate,
    BehavioralProfile,
    BehavioralPulseSurvey,
    BehavioralRecommendation,
    BehavioralRetentionSettings,
    BehavioralRule,
    ManagerEffectiveness,
)
from backend.modules.behavioral_analysis.personality import (
    generate_interpretation,
    get_questions_by_ids,
    score_ipip,
)
from backend.database.models import User as DbUser, Department
from backend.modules.behavioral_analysis.organizational_health import (
    OrganizationalHealth,
)
from sqlalchemy import func, select
from strawberry.types import Info


@strawberry.input
class PersonalityTestAnswers:
    template_id: int
    answers: list[int]


@strawberry.input
class PulseSurveyInput:
    burnout_feeling: int | None = None
    engagement_feeling: int | None = None
    stress_level: int | None = None
    energy_level: int | None = None
    work_satisfaction: int | None = None
    notes: str | None = None


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


@strawberry.input
class CreatePersonalityTemplateInput:
    name: str
    selected_question_ids: list[int]
    shuffle: bool = True
    is_active: bool = True


@strawberry.input
class UpdatePersonalityTemplateInput:
    id: int
    name: str | None = None
    selected_question_ids: list[int] | None = None
    shuffle: bool | None = None
    is_active: bool | None = None


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

    @strawberry.mutation
    async def compute_manager_effectiveness(
        self, info: Info, manager_id: int,
        period_start: str | None = None, period_end: str | None = None,
    ) -> ManagerEffectivenessType:
        db = info.context["db"]
        current_user: User = info.context["current_user"]

        manager_result = await db.execute(
            select(DbUser).where(
                DbUser.id == manager_id,
                DbUser.company_id == current_user.company_id,
            ),
        )
        manager = manager_result.scalar_one_or_none()
        if not manager:
            raise NotFoundException.resource("User", id=manager_id)

        start = date.fromisoformat(period_start) if period_start else date.today().replace(day=1)
        end = date.fromisoformat(period_end) if period_end else date.today()

        team_result = await db.execute(
            select(DbUser).where(
                DbUser.company_id == manager.company_id,
                DbUser.department_id == manager.department_id,
                DbUser.is_active,
                DbUser.id != manager_id,
            ),
        )
        team = team_result.scalars().all()
        team_ids = [u.id for u in team]
        team_size = len(team_ids)

        if team_size == 0:
            raise ValueError("Manager has no team members in their department")

        profiles_result = await db.execute(
            select(
                func.avg(BehavioralProfile.attendance_score).label("avg_att"),
                func.avg(BehavioralProfile.engagement_score).label("avg_eng"),
                func.avg(BehavioralProfile.burnout_risk).label("avg_burn"),
            ).where(
                BehavioralProfile.user_id.in_(team_ids),
                BehavioralProfile.period_start >= start,
                BehavioralProfile.period_end <= end,
            ),
        )
        row = profiles_result.first()
        team_avg_att = float(row.avg_att) if row and row.avg_att else 80.0
        team_avg_eng = float(row.avg_eng) if row and row.avg_eng else 0.0
        team_avg_burn = float(row.avg_burn) if row and row.avg_burn else 0.0

        all_burn = await db.execute(
            select(BehavioralProfile.burnout_risk).where(
                BehavioralProfile.user_id.in_(team_ids),
                BehavioralProfile.period_start >= start,
                BehavioralProfile.period_end <= end,
            ),
        )
        burn_values = [float(r[0]) for r in all_burn.all() if r[0] is not None]
        burnout_var = sum((x - team_avg_burn)**2 for x in burn_values) / len(burn_values) if len(burn_values) > 1 else 0.0

        inactive_result = await db.execute(
            select(func.count(DbUser.id)).where(
                DbUser.company_id == manager.company_id,
                DbUser.department_id == manager.department_id,
                DbUser.is_active == False,
                DbUser.updated_at >= datetime.combine(start, datetime.min.time()),
            ),
        )
        turnover_count = inactive_result.scalar() or 0
        turnover_rate = turnover_count / (team_size + turnover_count) if (team_size + turnover_count) > 0 else 0.0

        anomaly_result = await db.execute(
            select(func.count(BehavioralAnomaly.id)).where(
                BehavioralAnomaly.user_id.in_(team_ids),
            ),
        )
        anomaly_count = anomaly_result.scalar() or 0

        att_score = team_avg_att
        eng_score = team_avg_eng
        burn_penalty = max(0.0, 100.0 - (team_avg_burn * 150.0))
        turn_penalty = max(0.0, 100.0 - (turnover_rate * 500.0))
        anom_penalty = max(0.0, 100.0 - ((anomaly_count / team_size) * 50.0)) if team_size > 0 else 0.0

        effectiveness = (
            att_score * 0.15 + eng_score * 0.25 +
            burn_penalty * 0.20 + turn_penalty * 0.25 + anom_penalty * 0.15
        )

        me = ManagerEffectiveness(
            manager_id=manager_id,
            company_id=current_user.company_id,
            period_start=start, period_end=end,
            team_avg_attendance=team_avg_att,
            team_avg_engagement=team_avg_eng,
            team_avg_burnout=team_avg_burn,
            team_burnout_variance=burnout_var,
            team_turnover_rate=turnover_rate,
            team_size=team_size,
            team_anomaly_count=anomaly_count,
            manager_effectiveness_score=round(effectiveness, 2),
        )
        db.add(me)
        await db.commit()
        await db.refresh(me)

        return ManagerEffectivenessType(
            id=me.id, manager_id=me.manager_id,
            company_id=me.company_id,
            period_start=me.period_start, period_end=me.period_end,
            team_avg_attendance=me.team_avg_attendance,
            team_avg_engagement=me.team_avg_engagement,
            team_avg_burnout=me.team_avg_burnout,
            team_burnout_variance=me.team_burnout_variance,
            team_turnover_rate=me.team_turnover_rate,
            team_size=me.team_size,
            team_anomaly_count=me.team_anomaly_count,
            manager_effectiveness_score=me.manager_effectiveness_score,
            sentiment_score=me.sentiment_score,
            trend_direction=me.trend_direction,
            computed_at=me.computed_at,
        )

    @strawberry.mutation
    async def submit_personality_test(
        self, info: Info, input: PersonalityTestAnswers,
    ) -> BehavioralPersonalityProfileType:
        db = info.context["db"]
        current_user: User = info.context["current_user"]

        template_result = await db.execute(
            select(BehavioralPersonalityTestTemplate).where(
                BehavioralPersonalityTestTemplate.id == input.template_id,
            ),
        )
        template = template_result.scalar_one_or_none()
        if not template:
            raise NotFoundException.resource("TestTemplate", id=input.template_id)

        questions = get_questions_by_ids(template.selected_question_ids)
        scores = score_ipip(input.answers, questions)

        profile = BehavioralPersonalityProfile(
            user_id=current_user.id,
            company_id=current_user.company_id,
            template_id=input.template_id,
            openness=scores["openness"]["sten"],
            conscientiousness=scores["conscientiousness"]["sten"],
            extraversion=scores["extraversion"]["sten"],
            agreeableness=scores["agreeableness"]["sten"],
            neuroticism=scores["neuroticism"]["sten"],
            openness_raw=scores["openness"]["raw"],
            conscientiousness_raw=scores["conscientiousness"]["raw"],
            extraversion_raw=scores["extraversion"]["raw"],
            agreeableness_raw=scores["agreeableness"]["raw"],
            neuroticism_raw=scores["neuroticism"]["raw"],
            interpretation=generate_interpretation(scores),
        )
        db.add(profile)
        await db.commit()
        await db.refresh(profile)

        return BehavioralPersonalityProfileType(
            id=profile.id, user_id=profile.user_id,
            company_id=profile.company_id, template_id=profile.template_id,
            completed_at=profile.completed_at,
            openness=profile.openness, conscientiousness=profile.conscientiousness,
            extraversion=profile.extraversion, agreeableness=profile.agreeableness,
            neuroticism=profile.neuroticism,
            openness_raw=profile.openness_raw, conscientiousness_raw=profile.conscientiousness_raw,
            extraversion_raw=profile.extraversion_raw, agreeableness_raw=profile.agreeableness_raw,
            neuroticism_raw=profile.neuroticism_raw,
            interpretation=profile.interpretation,
        )

    @strawberry.mutation
    async def submit_pulse_survey(
        self, info: Info, input: PulseSurveyInput,
    ) -> BehavioralPulseSurveyType:
        db = info.context["db"]
        current_user: User = info.context["current_user"]

        survey = BehavioralPulseSurvey(
            user_id=current_user.id,
            company_id=current_user.company_id,
            burnout_feeling=input.burnout_feeling,
            engagement_feeling=input.engagement_feeling,
            stress_level=input.stress_level,
            energy_level=input.energy_level,
            work_satisfaction=input.work_satisfaction,
            notes=input.notes,
        )
        db.add(survey)
        await db.commit()
        await db.refresh(survey)

        return BehavioralPulseSurveyType(
            id=survey.id,
            user_id=survey.user_id,
            company_id=survey.company_id,
            submitted_at=survey.submitted_at,
            burnout_feeling=survey.burnout_feeling,
            engagement_feeling=survey.engagement_feeling,
            stress_level=survey.stress_level,
            energy_level=survey.energy_level,
            work_satisfaction=survey.work_satisfaction,
            survey_version=survey.survey_version,
            notes=survey.notes,
        )

    @strawberry.mutation
    async def create_personality_template(
        self, info: Info, input: CreatePersonalityTemplateInput,
    ) -> PersonalityTestTemplateType:
        db = info.context["db"]
        current_user: User = info.context["current_user"]
        if current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("create personality template")
        if len(input.selected_question_ids) != 50:
            raise ValidationException("Трябва да изберете точно 50 въпроса.")
        template = BehavioralPersonalityTestTemplate(
            company_id=current_user.company_id,
            name=input.name,
            selected_question_ids=input.selected_question_ids,
            shuffle=input.shuffle,
            is_active=input.is_active,
            created_by=current_user.id,
        )
        db.add(template)
        await db.commit()
        await db.refresh(template)
        return PersonalityTestTemplateType(
            id=template.id, company_id=template.company_id,
            name=template.name, selected_question_ids=template.selected_question_ids,
            shuffle=template.shuffle, is_active=template.is_active,
            created_by=template.created_by, created_at=template.created_at,
        )

    @strawberry.mutation
    async def update_personality_template(
        self, info: Info, input: UpdatePersonalityTemplateInput,
    ) -> PersonalityTestTemplateType:
        db = info.context["db"]
        current_user: User = info.context["current_user"]
        if current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("update personality template")
        result = await db.execute(
            select(BehavioralPersonalityTestTemplate).where(
                BehavioralPersonalityTestTemplate.id == input.id,
                BehavioralPersonalityTestTemplate.company_id == current_user.company_id,
            ),
        )
        template = result.scalar_one_or_none()
        if not template:
            raise NotFoundException.resource("PersonalityTestTemplate", id=input.id)
        if input.name is not None:
            template.name = input.name
        if input.selected_question_ids is not None:
            if len(input.selected_question_ids) != 50:
                raise ValidationException("Трябва да изберете точно 50 въпроса.")
            template.selected_question_ids = input.selected_question_ids
        if input.shuffle is not None:
            template.shuffle = input.shuffle
        if input.is_active is not None:
            template.is_active = input.is_active
        await db.commit()
        await db.refresh(template)
        return PersonalityTestTemplateType(
            id=template.id, company_id=template.company_id,
            name=template.name, selected_question_ids=template.selected_question_ids,
            shuffle=template.shuffle, is_active=template.is_active,
            created_by=template.created_by, created_at=template.created_at,
        )

    @strawberry.mutation
    async def delete_personality_template(
        self, info: Info, id: int,
    ) -> bool:
        db = info.context["db"]
        current_user: User = info.context["current_user"]
        if current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("delete personality template")
        result = await db.execute(
            select(BehavioralPersonalityTestTemplate).where(
                BehavioralPersonalityTestTemplate.id == id,
                BehavioralPersonalityTestTemplate.company_id == current_user.company_id,
            ),
        )
        template = result.scalar_one_or_none()
        if not template:
            raise NotFoundException.resource("PersonalityTestTemplate", id=id)
        await db.delete(template)
        await db.commit()
        return True
