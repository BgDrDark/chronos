from datetime import date, datetime

from backend.database.models import Base
from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship


class BehavioralProfile(Base):
    __tablename__ = "behavioral_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)
    employee_type: Mapped[str] = mapped_column(String(20), default="full_time")
    tenure_days: Mapped[int] = mapped_column(Integer, default=0)
    probation_mode: Mapped[bool] = mapped_column(default=False)
    data_completeness: Mapped[float] = mapped_column(Float, default=1.0)

    punctuality_score: Mapped[float] = mapped_column(Float, default=100.0)
    efficiency_score: Mapped[float] = mapped_column(Float, default=100.0)
    overtime_score: Mapped[float] = mapped_column(Float, default=0.0)
    burnout_risk: Mapped[float] = mapped_column(Float, default=0.0)
    financial_stress_score: Mapped[float] = mapped_column(Float, default=0.0)
    attendance_score: Mapped[float] = mapped_column(Float, default=100.0)
    engagement_score: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)
    scrap_rate: Mapped[float] = mapped_column(Float, default=0.0)
    peer_group_percentile: Mapped[float] = mapped_column(Float, default=50.0)
    trend_direction: Mapped[str] = mapped_column(String(20), default="stable")
    status: Mapped[str] = mapped_column(String(20), default="stable")
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0)
    anomaly_severity_score: Mapped[float] = mapped_column(Float, default=0.0)
    anomaly_severity_label: Mapped[str] = mapped_column(String(20), default="normal")

    contribution_factors: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    rule_engine_version: Mapped[str] = mapped_column(String(20), default="v1.0.0")

    computed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    version: Mapped[int] = mapped_column(Integer, default=1)

    personality_profile_id: Mapped[int | None] = mapped_column(
        ForeignKey("behavioral_personality_profiles.id"), nullable=True,
    )

    anomalies: Mapped[list["BehavioralAnomaly"]] = relationship(back_populates="profile", cascade="all, delete-orphan")


class BehavioralPersonalityTestTemplate(Base):
    __tablename__ = "behavioral_personality_test_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    selected_question_ids: Mapped[list] = mapped_column(JSON)
    shuffle: Mapped[bool] = mapped_column(default=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class BehavioralPersonalityProfile(Base):
    __tablename__ = "behavioral_personality_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("behavioral_personality_test_templates.id"))
    completed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    openness: Mapped[int] = mapped_column(Integer)
    conscientiousness: Mapped[int] = mapped_column(Integer)
    extraversion: Mapped[int] = mapped_column(Integer)
    agreeableness: Mapped[int] = mapped_column(Integer)
    neuroticism: Mapped[int] = mapped_column(Integer)

    openness_raw: Mapped[float] = mapped_column(Float)
    conscientiousness_raw: Mapped[float] = mapped_column(Float)
    extraversion_raw: Mapped[float] = mapped_column(Float)
    agreeableness_raw: Mapped[float] = mapped_column(Float)
    neuroticism_raw: Mapped[float] = mapped_column(Float)

    interpretation: Mapped[str | None] = mapped_column(String(1000), nullable=True)


class BehavioralAnomaly(Base):
    __tablename__ = "behavioral_anomalies"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("behavioral_profiles.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    anomaly_type: Mapped[str] = mapped_column(String(30))
    severity: Mapped[int] = mapped_column(Integer)
    metric_name: Mapped[str] = mapped_column(String(50))
    actual_value: Mapped[float] = mapped_column(Float)
    expected_value: Mapped[float] = mapped_column(Float)
    deviation: Mapped[float] = mapped_column(Float)
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0)
    suppressed: Mapped[bool] = mapped_column(default=False)
    suppression_reason: Mapped[str | None] = mapped_column(String(200), nullable=True)
    description: Mapped[str] = mapped_column(String(500))
    context_summary: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    profile: Mapped["BehavioralProfile"] = relationship(back_populates="anomalies")


class BehavioralRule(Base):
    __tablename__ = "behavioral_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    rule_type: Mapped[str] = mapped_column(String(20))
    is_system: Mapped[bool] = mapped_column(default=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    shadow_mode: Mapped[bool] = mapped_column(default=False)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    condition_type: Mapped[str] = mapped_column(String(30))
    condition_config: Mapped[dict] = mapped_column(JSON)
    recommendation_template: Mapped[dict] = mapped_column(JSON)
    auto_execute_action: Mapped[str | None] = mapped_column(String(20), nullable=True)
    auto_execute: Mapped[bool] = mapped_column(default=False)
    effectiveness_score: Mapped[float] = mapped_column(Float, default=0.0)
    false_positive_rate: Mapped[float] = mapped_column(Float, default=0.0)
    trigger_count: Mapped[int] = mapped_column(Integer, default=0)
    accepted_count: Mapped[int] = mapped_column(Integer, default=0)
    effective_count: Mapped[int] = mapped_column(Integer, default=0)
    false_positive_count: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class BehavioralRecommendation(Base):
    __tablename__ = "behavioral_recommendations"

    id: Mapped[int] = mapped_column(primary_key=True)
    rule_id: Mapped[int] = mapped_column(ForeignKey("behavioral_rules.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    anomaly_id: Mapped[int | None] = mapped_column(ForeignKey("behavioral_anomalies.id"), nullable=True)
    type: Mapped[str] = mapped_column(String(50))
    priority: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(String(1000))
    suggested_action: Mapped[str] = mapped_column(String(500))
    explanation: Mapped[str] = mapped_column(String(500))
    coaching_tips: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    auto_executed: Mapped[bool] = mapped_column(default=False)
    throttled: Mapped[bool] = mapped_column(default=False)
    aggregated_count: Mapped[int] = mapped_column(Integer, default=1)
    dispute_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    dispute_notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class RecommendationFeedback(Base):
    __tablename__ = "recommendation_feedback"

    id: Mapped[int] = mapped_column(primary_key=True)
    recommendation_id: Mapped[int] = mapped_column(ForeignKey("behavioral_recommendations.id", ondelete="CASCADE"), index=True)
    manager_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    manager_action: Mapped[str] = mapped_column(String(20))
    manager_notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    action_taken_at: Mapped[datetime] = mapped_column(DateTime)
    outcome: Mapped[str] = mapped_column(String(20))
    outcome_measured_at: Mapped[datetime] = mapped_column(DateTime)
    days_to_outcome: Mapped[int] = mapped_column(Integer)
    metric_before: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    metric_after: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    improvement_delta: Mapped[float] = mapped_column(Float)


class BehavioralRetentionSettings(Base):
    __tablename__ = "behavioral_retention_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), unique=True)
    raw_profile_days: Mapped[int] = mapped_column(Integer, default=90)
    aggregated_profile_months: Mapped[int] = mapped_column(Integer, default=12)
    recommendation_months: Mapped[int] = mapped_column(Integer, default=6)
    feedback_months: Mapped[int] = mapped_column(Integer, default=24)
    audit_log_months: Mapped[int] = mapped_column(Integer, default=36)
    auto_cleanup_enabled: Mapped[bool] = mapped_column(default=True)
    cleanup_schedule: Mapped[str] = mapped_column(String(20), default="nightly")
    anonymize_instead_of_delete: Mapped[bool] = mapped_column(default=False)
    updated_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class BehavioralStatusThresholds(Base):
    __tablename__ = "behavioral_status_thresholds"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), unique=True)
    punctuality_warning: Mapped[float] = mapped_column(Float, default=70.0)
    punctuality_critical: Mapped[float] = mapped_column(Float, default=50.0)
    efficiency_warning: Mapped[float] = mapped_column(Float, default=60.0)
    efficiency_critical: Mapped[float] = mapped_column(Float, default=40.0)
    burnout_warning: Mapped[float] = mapped_column(Float, default=0.6)
    burnout_critical: Mapped[float] = mapped_column(Float, default=0.8)
    stress_warning: Mapped[float] = mapped_column(Float, default=0.5)
    stress_critical: Mapped[float] = mapped_column(Float, default=0.7)
    engagement_warning: Mapped[float] = mapped_column(Float, default=60.0)
    engagement_critical: Mapped[float] = mapped_column(Float, default=40.0)
    probation_multiplier: Mapped[float] = mapped_column(Float, default=1.5)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class BehavioralComputationSettings(Base):
    __tablename__ = "behavioral_computation_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), unique=True)
    computation_frequency: Mapped[str] = mapped_column(String(20), default="nightly")
    incremental_updates_enabled: Mapped[bool] = mapped_column(default=True)
    peer_group_cache_hours: Mapped[int] = mapped_column(Integer, default=24)
    min_data_completeness: Mapped[float] = mapped_column(Float, default=0.6)
    triggered_alerts_enabled: Mapped[bool] = mapped_column(default=True)
    max_triggered_alerts_per_day: Mapped[int] = mapped_column(Integer, default=10)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class BehavioralPulseSurvey(Base):
    __tablename__ = "behavioral_pulse_surveys"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    burnout_feeling: Mapped[int | None] = mapped_column(Integer, nullable=True)
    engagement_feeling: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stress_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    energy_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    work_satisfaction: Mapped[int | None] = mapped_column(Integer, nullable=True)

    survey_version: Mapped[str] = mapped_column(String(10), default="v1")
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)


class ManagerEffectiveness(Base):
    __tablename__ = "manager_effectiveness"

    id: Mapped[int] = mapped_column(primary_key=True)
    manager_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)

    team_avg_attendance: Mapped[float] = mapped_column(Float)
    team_avg_engagement: Mapped[float] = mapped_column(Float, default=0.0)
    team_avg_burnout: Mapped[float] = mapped_column(Float)
    team_burnout_variance: Mapped[float] = mapped_column(Float, default=0.0)
    team_turnover_rate: Mapped[float] = mapped_column(Float, default=0.0)
    team_size: Mapped[int] = mapped_column(Integer)
    team_anomaly_count: Mapped[int] = mapped_column(Integer, default=0)

    manager_effectiveness_score: Mapped[float] = mapped_column(Float)
    sentiment_score: Mapped[float] = mapped_column(Float, default=0.0)
    trend_direction: Mapped[str] = mapped_column(String(20), default="stable")

    computed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class BehavioralMetricWeights(Base):
    __tablename__ = "behavioral_metric_weights"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), unique=True)
    burnout_overtime_weight: Mapped[float] = mapped_column(Float, default=0.4)
    burnout_consecutive_days_weight: Mapped[float] = mapped_column(Float, default=0.3)
    burnout_leave_usage_weight: Mapped[float] = mapped_column(Float, default=0.2)
    burnout_productivity_decline_weight: Mapped[float] = mapped_column(Float, default=0.1)
    efficiency_output_weight: Mapped[float] = mapped_column(Float, default=0.6)
    efficiency_quality_weight: Mapped[float] = mapped_column(Float, default=0.3)
    efficiency_timeliness_weight: Mapped[float] = mapped_column(Float, default=0.1)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class BehavioralPeerGroupCache(Base):
    __tablename__ = "behavioral_peer_group_cache"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    metric_name: Mapped[str] = mapped_column(String(50))
    mean: Mapped[float] = mapped_column(Float)
    stddev: Mapped[float] = mapped_column(Float)
    p10: Mapped[float] = mapped_column(Float)
    p25: Mapped[float] = mapped_column(Float)
    p50: Mapped[float] = mapped_column(Float)
    p75: Mapped[float] = mapped_column(Float)
    p90: Mapped[float] = mapped_column(Float)
    sample_size: Mapped[int] = mapped_column(Integer)
    computed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime)


class BehavioralSystemHealth(Base):
    __tablename__ = "behavioral_system_health"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), unique=True)
    last_computation_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_computation_status: Mapped[str] = mapped_column(String(20), default="unknown")
    last_computation_duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    employees_processed: Mapped[int] = mapped_column(Integer, default=0)
    employees_failed: Mapped[int] = mapped_column(Integer, default=0)
    circuit_breaker_open: Mapped[bool] = mapped_column(default=False)
    circuit_breaker_failure_count: Mapped[int] = mapped_column(Integer, default=0)
    last_successful_profile_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    triggered_alerts_today: Mapped[int] = mapped_column(Integer, default=0)
    last_bias_check: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class DepartmentHealthReport(Base):
    __tablename__ = "department_health_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"))
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)
    avg_burnout_risk: Mapped[float] = mapped_column(Float)
    avg_attendance: Mapped[float] = mapped_column(Float)
    avg_engagement: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_efficiency: Mapped[float] = mapped_column(Float)
    avg_punctuality: Mapped[float] = mapped_column(Float)
    anomaly_count: Mapped[int] = mapped_column(Integer)
    employee_count: Mapped[int] = mapped_column(Integer)
    turnover_rate: Mapped[float] = mapped_column(Float)
    trend: Mapped[str] = mapped_column(String(20))
    is_systemic_issue: Mapped[bool] = mapped_column(default=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class BiasReport(Base):
    __tablename__ = "bias_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)
    findings: Mapped[list] = mapped_column(JSON)
    overall_bias_detected: Mapped[bool] = mapped_column(Boolean)
    generated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
