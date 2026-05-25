"""add behavioral analysis module tables

Revision ID: ba_001_behavioral_analysis
Revises: 5138fc0e331c
Create Date: 2026-05-10 06:10:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "ba_001_behavioral_analysis"
down_revision = "5138fc0e331c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("behavioral_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("employee_type", sa.String(length=20), nullable=False, server_default="full_time"),
        sa.Column("tenure_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("probation_mode", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("data_completeness", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("punctuality_score", sa.Float(), nullable=False, server_default="100.0"),
        sa.Column("efficiency_score", sa.Float(), nullable=False, server_default="100.0"),
        sa.Column("overtime_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("burnout_risk", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("financial_stress_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("engagement_score", sa.Float(), nullable=False, server_default="100.0"),
        sa.Column("scrap_rate", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("peer_group_percentile", sa.Float(), nullable=False, server_default="50.0"),
        sa.Column("trend_direction", sa.String(length=20), nullable=False, server_default="stable"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="stable"),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("contribution_factors", sa.JSON(), nullable=True),
        sa.Column("rule_engine_version", sa.String(length=20), nullable=False, server_default="v1.0.0"),
        sa.Column("computed_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"] ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_behavioral_profiles_company_id"), "behavioral_profiles", ["company_id"], unique=False)
    op.create_index(op.f("ix_behavioral_profiles_user_id"), "behavioral_profiles", ["user_id"], unique=False)

    op.create_table("behavioral_rules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("rule_type", sa.String(length=20), nullable=False),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("shadow_mode", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("condition_type", sa.String(length=30), nullable=False),
        sa.Column("condition_config", sa.JSON(), nullable=False),
        sa.Column("recommendation_template", sa.JSON(), nullable=False),
        sa.Column("auto_execute_action", sa.String(length=20), nullable=True),
        sa.Column("auto_execute", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("effectiveness_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("false_positive_rate", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("trigger_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("accepted_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("effective_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("false_positive_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"] ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"] ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_behavioral_rules_company_id"), "behavioral_rules", ["company_id"], unique=False)

    op.create_table("behavioral_anomalies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("anomaly_type", sa.String(length=30), nullable=False),
        sa.Column("severity", sa.Integer(), nullable=False),
        sa.Column("metric_name", sa.String(length=50), nullable=False),
        sa.Column("actual_value", sa.Float(), nullable=False),
        sa.Column("expected_value", sa.Float(), nullable=False),
        sa.Column("deviation", sa.Float(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("suppressed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("suppression_reason", sa.String(length=200), nullable=True),
        sa.Column("description", sa.String(length=500), nullable=False),
        sa.Column("context_summary", sa.JSON(), nullable=True),
        sa.Column("detected_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["profile_id"], ["behavioral_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_behavioral_anomalies_profile_id"), "behavioral_anomalies", ["profile_id"], unique=False)
    op.create_index(op.f("ix_behavioral_anomalies_user_id"), "behavioral_anomalies", ["user_id"], unique=False)

    op.create_table("behavioral_computation_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("computation_frequency", sa.String(length=20), nullable=False, server_default="nightly"),
        sa.Column("incremental_updates_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("peer_group_cache_hours", sa.Integer(), nullable=False, server_default="24"),
        sa.Column("min_data_completeness", sa.Float(), nullable=False, server_default="0.6"),
        sa.Column("triggered_alerts_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("max_triggered_alerts_per_day", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"] ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id"),
    )

    op.create_table("behavioral_metric_weights",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("burnout_overtime_weight", sa.Float(), nullable=False, server_default="0.4"),
        sa.Column("burnout_consecutive_days_weight", sa.Float(), nullable=False, server_default="0.3"),
        sa.Column("burnout_leave_usage_weight", sa.Float(), nullable=False, server_default="0.2"),
        sa.Column("burnout_productivity_decline_weight", sa.Float(), nullable=False, server_default="0.1"),
        sa.Column("efficiency_output_weight", sa.Float(), nullable=False, server_default="0.6"),
        sa.Column("efficiency_quality_weight", sa.Float(), nullable=False, server_default="0.3"),
        sa.Column("efficiency_timeliness_weight", sa.Float(), nullable=False, server_default="0.1"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"] ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id"),
    )

    op.create_table("behavioral_peer_group_cache",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("metric_name", sa.String(length=50), nullable=False),
        sa.Column("mean", sa.Float(), nullable=False),
        sa.Column("stddev", sa.Float(), nullable=False),
        sa.Column("p10", sa.Float(), nullable=False),
        sa.Column("p25", sa.Float(), nullable=False),
        sa.Column("p50", sa.Float(), nullable=False),
        sa.Column("p75", sa.Float(), nullable=False),
        sa.Column("p90", sa.Float(), nullable=False),
        sa.Column("sample_size", sa.Integer(), nullable=False),
        sa.Column("computed_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"] ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_behavioral_peer_group_cache_company_id"), "behavioral_peer_group_cache", ["company_id"], unique=False)

    op.create_table("behavioral_retention_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("raw_profile_days", sa.Integer(), nullable=False, server_default="90"),
        sa.Column("aggregated_profile_months", sa.Integer(), nullable=False, server_default="12"),
        sa.Column("recommendation_months", sa.Integer(), nullable=False, server_default="6"),
        sa.Column("feedback_months", sa.Integer(), nullable=False, server_default="24"),
        sa.Column("audit_log_months", sa.Integer(), nullable=False, server_default="36"),
        sa.Column("auto_cleanup_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("cleanup_schedule", sa.String(length=20), nullable=False, server_default="nightly"),
        sa.Column("anonymize_instead_of_delete", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("updated_by", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"] ),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"] ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id"),
    )

    op.create_table("behavioral_status_thresholds",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("punctuality_warning", sa.Float(), nullable=False, server_default="70.0"),
        sa.Column("punctuality_critical", sa.Float(), nullable=False, server_default="50.0"),
        sa.Column("efficiency_warning", sa.Float(), nullable=False, server_default="60.0"),
        sa.Column("efficiency_critical", sa.Float(), nullable=False, server_default="40.0"),
        sa.Column("burnout_warning", sa.Float(), nullable=False, server_default="0.6"),
        sa.Column("burnout_critical", sa.Float(), nullable=False, server_default="0.8"),
        sa.Column("stress_warning", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("stress_critical", sa.Float(), nullable=False, server_default="0.7"),
        sa.Column("engagement_warning", sa.Float(), nullable=False, server_default="60.0"),
        sa.Column("engagement_critical", sa.Float(), nullable=False, server_default="40.0"),
        sa.Column("probation_multiplier", sa.Float(), nullable=False, server_default="1.5"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"] ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id"),
    )

    op.create_table("behavioral_system_health",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("last_computation_at", sa.DateTime(), nullable=True),
        sa.Column("last_computation_status", sa.String(length=20), nullable=False, server_default="unknown"),
        sa.Column("last_computation_duration_seconds", sa.Integer(), nullable=True),
        sa.Column("employees_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("employees_failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("circuit_breaker_open", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("circuit_breaker_failure_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_successful_profile_date", sa.DateTime(), nullable=True),
        sa.Column("triggered_alerts_today", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_bias_check", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"] ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id"),
    )

    op.create_table("bias_reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("findings", sa.JSON(), nullable=False),
        sa.Column("overall_bias_detected", sa.Boolean(), nullable=False),
        sa.Column("generated_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"] ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_bias_reports_company_id"), "bias_reports", ["company_id"], unique=False)

    op.create_table("department_health_reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("department_id", sa.Integer(), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("avg_burnout_risk", sa.Float(), nullable=False),
        sa.Column("avg_engagement", sa.Float(), nullable=False),
        sa.Column("avg_efficiency", sa.Float(), nullable=False),
        sa.Column("avg_punctuality", sa.Float(), nullable=False),
        sa.Column("anomaly_count", sa.Integer(), nullable=False),
        sa.Column("employee_count", sa.Integer(), nullable=False),
        sa.Column("turnover_rate", sa.Float(), nullable=False),
        sa.Column("trend", sa.String(length=20), nullable=False),
        sa.Column("is_systemic_issue", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("generated_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"] ),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"] ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_department_health_reports_company_id"), "department_health_reports", ["company_id"], unique=False)

    op.create_table("behavioral_recommendations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("rule_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("anomaly_id", sa.Integer(), nullable=True),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("priority", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=False),
        sa.Column("suggested_action", sa.String(length=500), nullable=False),
        sa.Column("explanation", sa.String(length=500), nullable=False),
        sa.Column("coaching_tips", sa.JSON(), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("auto_executed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("throttled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("aggregated_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("dispute_reason", sa.String(length=500), nullable=True),
        sa.Column("dispute_notes", sa.String(length=1000), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["anomaly_id"], ["behavioral_anomalies.id"] ),
        sa.ForeignKeyConstraint(["rule_id"], ["behavioral_rules.id"] ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_behavioral_recommendations_rule_id"), "behavioral_recommendations", ["rule_id"], unique=False)
    op.create_index(op.f("ix_behavioral_recommendations_user_id"), "behavioral_recommendations", ["user_id"], unique=False)

    op.create_table("recommendation_feedback",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("recommendation_id", sa.Integer(), nullable=False),
        sa.Column("manager_id", sa.Integer(), nullable=False),
        sa.Column("manager_action", sa.String(length=20), nullable=False),
        sa.Column("manager_notes", sa.String(length=1000), nullable=True),
        sa.Column("action_taken_at", sa.DateTime(), nullable=False),
        sa.Column("outcome", sa.String(length=20), nullable=False),
        sa.Column("outcome_measured_at", sa.DateTime(), nullable=False),
        sa.Column("days_to_outcome", sa.Integer(), nullable=False),
        sa.Column("metric_before", sa.JSON(), nullable=True),
        sa.Column("metric_after", sa.JSON(), nullable=True),
        sa.Column("improvement_delta", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["manager_id"], ["users.id"] ),
        sa.ForeignKeyConstraint(["recommendation_id"], ["behavioral_recommendations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_recommendation_feedback_recommendation_id"), "recommendation_feedback", ["recommendation_id"], unique=False)


def downgrade() -> None:
    op.drop_table("recommendation_feedback")
    op.drop_table("behavioral_recommendations")
    op.drop_table("department_health_reports")
    op.drop_table("bias_reports")
    op.drop_table("behavioral_system_health")
    op.drop_table("behavioral_status_thresholds")
    op.drop_table("behavioral_retention_settings")
    op.drop_table("behavioral_peer_group_cache")
    op.drop_table("behavioral_metric_weights")
    op.drop_table("behavioral_computation_settings")
    op.drop_table("behavioral_anomalies")
    op.drop_table("behavioral_rules")
    op.drop_table("behavioral_profiles")
