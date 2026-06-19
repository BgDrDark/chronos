from datetime import date, datetime

import strawberry
from backend.utils.json_type import JSONScalar


@strawberry.type
class BehavioralPulseSurveyType:
    id: int
    user_id: int
    company_id: int
    submitted_at: datetime

    burnout_feeling: int | None = None
    engagement_feeling: int | None = None
    stress_level: int | None = None
    energy_level: int | None = None
    work_satisfaction: int | None = None

    survey_version: str = "v1"
    notes: str | None = None


@strawberry.type
class BehavioralProfileType:
    id: int
    user_id: int
    company_id: int
    period_start: date
    period_end: date
    employee_type: str
    tenure_days: int
    probation_mode: bool
    data_completeness: float

    punctuality_score: float
    efficiency_score: float
    overtime_score: float
    burnout_risk: float
    financial_stress_score: float
    attendance_score: float
    engagement_score: float | None = None
    scrap_rate: float
    peer_group_percentile: float
    trend_direction: str
    status: str
    confidence_score: float

    contribution_factors: JSONScalar | None = None
    rule_engine_version: str
    computed_at: datetime
    version: int


@strawberry.type
class PersonalityQuestionType:
    id: int
    bg: str
    en: str
    factor: str
    direction: str


@strawberry.type
class PersonalityTestTemplateType:
    id: int
    company_id: int
    name: str
    selected_question_ids: list[int]
    shuffle: bool
    is_active: bool
    created_by: int
    created_at: datetime


@strawberry.type
class BehavioralPersonalityProfileType:
    id: int
    user_id: int
    company_id: int
    template_id: int
    completed_at: datetime

    openness: int
    conscientiousness: int
    extraversion: int
    agreeableness: int
    neuroticism: int

    openness_raw: float
    conscientiousness_raw: float
    extraversion_raw: float
    agreeableness_raw: float
    neuroticism_raw: float

    interpretation: str | None = None


@strawberry.type
class ManagerEffectivenessType:
    id: int
    manager_id: int
    company_id: int
    period_start: date
    period_end: date

    team_avg_attendance: float
    team_avg_engagement: float
    team_avg_burnout: float
    team_burnout_variance: float
    team_turnover_rate: float
    team_size: int
    team_anomaly_count: int

    manager_effectiveness_score: float
    sentiment_score: float
    trend_direction: str

    computed_at: datetime


@strawberry.type
class BehavioralAnomalyType:
    id: int
    profile_id: int
    user_id: int
    anomaly_type: str
    severity: int
    metric_name: str
    actual_value: float
    expected_value: float
    deviation: float
    confidence_score: float
    suppressed: bool
    suppression_reason: str | None = None
    description: str
    context_summary: JSONScalar | None = None
    detected_at: datetime


@strawberry.type
class BehavioralRuleType:
    id: int
    name: str
    description: str | None = None
    rule_type: str
    is_system: bool
    is_active: bool
    shadow_mode: bool
    company_id: int
    condition_type: str
    condition_config: JSONScalar
    recommendation_template: JSONScalar
    auto_execute_action: str | None = None
    auto_execute: bool
    effectiveness_score: float
    false_positive_rate: float
    trigger_count: int
    accepted_count: int
    effective_count: int
    false_positive_count: int
    created_by: int
    created_at: datetime
    updated_at: datetime


@strawberry.type
class BehavioralRecommendationType:
    id: int
    rule_id: int
    user_id: int
    anomaly_id: int | None = None
    type: str
    priority: str
    title: str
    description: str
    suggested_action: str
    explanation: str
    coaching_tips: JSONScalar | None = None
    confidence_score: float
    status: str
    auto_executed: bool
    throttled: bool
    aggregated_count: int
    dispute_reason: str | None = None
    dispute_notes: str | None = None
    created_at: datetime
    expires_at: datetime | None = None


@strawberry.type
class BehavioralSettingsType:
    id: int
    company_id: int
    raw_profile_days: int
    aggregated_profile_months: int
    recommendation_months: int
    feedback_months: int
    audit_log_months: int
    auto_cleanup_enabled: bool
    cleanup_schedule: str
    anonymize_instead_of_delete: bool
    updated_by: int
    updated_at: datetime


@strawberry.type
class OrganizationalHealthType:
    department_id: int
    department_name: str
    avg_burnout_risk: float
    avg_attendance: float
    avg_efficiency: float
    avg_punctuality: float
    anomaly_count: int
    employee_count: int
    turnover_rate: float
    trend: str
    is_systemic_issue: bool


@strawberry.type
class RecommendationFeedbackType:
    id: int
    recommendation_id: int
    manager_id: int
    manager_action: str
    manager_notes: str | None = None
    action_taken_at: datetime
    outcome: str
    outcome_measured_at: datetime
    days_to_outcome: int
    metric_before: JSONScalar | None = None
    metric_after: JSONScalar | None = None
    improvement_delta: float


@strawberry.type
class BiasReportType:
    id: int
    company_id: int
    period_start: date
    period_end: date
    findings: JSONScalar
    overall_bias_detected: bool
    generated_at: datetime


@strawberry.type
class BehavioralSystemHealthType:
    id: int
    company_id: int
    last_computation_at: datetime | None = None
    last_computation_status: str = "unknown"
    last_computation_duration_seconds: int | None = None
    employees_processed: int = 0
    employees_failed: int = 0
    circuit_breaker_open: bool = False
    circuit_breaker_failure_count: int = 0
    last_successful_profile_date: datetime | None = None
    triggered_alerts_today: int = 0
    last_bias_check: datetime | None = None


@strawberry.type
class PersonalityTestAssignmentType:
    id: int
    user_id: int
    company_id: int
    template_id: int
    assigned_by: int
    assigned_at: datetime
    due_by: datetime
    completed_at: datetime | None = None
    status: str = "pending"
    notified_overdue: bool = False

    user_name: str = ""
    user_email: str = ""
    template_name: str = ""
    assigner_name: str = ""
