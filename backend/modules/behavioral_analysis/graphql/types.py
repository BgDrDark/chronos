import strawberry
from typing import Optional, List
from datetime import datetime, date
from backend.utils.json_type import JSONScalar


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
    engagement_score: float
    scrap_rate: float
    peer_group_percentile: float
    trend_direction: str
    status: str
    confidence_score: float

    contribution_factors: Optional[JSONScalar] = None
    rule_engine_version: str
    computed_at: datetime
    version: int


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
    suppression_reason: Optional[str] = None
    description: str
    context_summary: Optional[JSONScalar] = None
    detected_at: datetime


@strawberry.type
class BehavioralRuleType:
    id: int
    name: str
    description: Optional[str] = None
    rule_type: str
    is_system: bool
    is_active: bool
    shadow_mode: bool
    company_id: int
    condition_type: str
    condition_config: JSONScalar
    recommendation_template: JSONScalar
    auto_execute_action: Optional[str] = None
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
    anomaly_id: Optional[int] = None
    type: str
    priority: str
    title: str
    description: str
    suggested_action: str
    explanation: str
    coaching_tips: Optional[JSONScalar] = None
    confidence_score: float
    status: str
    auto_executed: bool
    throttled: bool
    aggregated_count: int
    dispute_reason: Optional[str] = None
    dispute_notes: Optional[str] = None
    created_at: datetime
    expires_at: Optional[datetime] = None


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
    avg_engagement: float
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
    manager_notes: Optional[str] = None
    action_taken_at: datetime
    outcome: str
    outcome_measured_at: datetime
    days_to_outcome: int
    metric_before: Optional[JSONScalar] = None
    metric_after: Optional[JSONScalar] = None
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
    last_computation_at: Optional[datetime] = None
    last_computation_status: str = "unknown"
    last_computation_duration_seconds: Optional[int] = None
    employees_processed: int = 0
    employees_failed: int = 0
    circuit_breaker_open: bool = False
    circuit_breaker_failure_count: int = 0
    last_successful_profile_date: Optional[datetime] = None
    triggered_alerts_today: int = 0
    last_bias_check: Optional[datetime] = None
