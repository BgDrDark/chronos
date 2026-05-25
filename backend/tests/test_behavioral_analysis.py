"""Standalone Backend Tests for Behavioral Analysis Module
Tests: Detector, RuleEngine, ContextAnalyzer, FeedbackLoop, 
       OrganizationalHealth, TriggeredEvents, Resilience
"""
import asyncio
import os
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from zoneinfo import ZoneInfo

import pytest
from backend.config import settings

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Backend imports
from backend.modules.behavioral_analysis.context_analyzer import ContextAnalyzer
from backend.modules.behavioral_analysis.detector import BehavioralDetector
from backend.modules.behavioral_analysis.feedback_loop import FeedbackLoop

# Models
from backend.modules.behavioral_analysis.models import (
    BehavioralProfile,
    BehavioralRule,
    BehavioralStatusThresholds,
)
from backend.modules.behavioral_analysis.organizational_health import (
    OrganizationalHealth,
)
from backend.modules.behavioral_analysis.resilience import (
    CircuitBreaker,
    CircuitBreakerError,
)
from backend.modules.behavioral_analysis.rule_engine import RuleEngine
from backend.modules.behavioral_analysis.triggered_events import TriggeredEventProcessor

# ==========================================
# Helpers
# ==========================================

def create_mock_db():
    """Create a mock db session with synchronous add() method"""
    db = AsyncMock()
    db.add = MagicMock()
    db.add_all = MagicMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db

def create_mock_profile(**kwargs):
    defaults = {
        "id": 1, "user_id": 1, "company_id": 1,
        "period_start": date.today() - timedelta(days=30),
        "period_end": date.today(),
        "employee_type": "full_time", "tenure_days": 365,
        "probation_mode": False, "data_completeness": 1.0,
        "punctuality_score": 85.0, "efficiency_score": 90.0,
        "overtime_score": 10.0, "burnout_risk": 0.3,
        "financial_stress_score": 0.1, "engagement_score": 95.0,
        "scrap_rate": 2.0, "peer_group_percentile": 70.0,
        "trend_direction": "stable", "status": "stable",
        "confidence_score": 1.0, "contribution_factors": None,
        "rule_engine_version": "v1.0.0", "computed_at": datetime.now(ZoneInfo(settings.TIMEZONE)).replace(tzinfo=None),
        "version": 1, "anomalies": [],
    }
    defaults.update(kwargs)
    profile = MagicMock(spec=BehavioralProfile)
    for k, v in defaults.items():
        setattr(profile, k, v)
    return profile

def create_mock_thresholds(**kwargs):
    defaults = {
        "id": 1, "company_id": 1,
        "punctuality_warning": 70.0, "punctuality_critical": 50.0,
        "efficiency_warning": 60.0, "efficiency_critical": 40.0,
        "burnout_warning": 0.6, "burnout_critical": 0.8,
        "stress_warning": 0.5, "stress_critical": 0.7,
        "engagement_warning": 60.0, "engagement_critical": 40.0,
        "probation_multiplier": 1.5,
        "updated_at": datetime.now(ZoneInfo(settings.TIMEZONE)).replace(tzinfo=None),
    }
    defaults.update(kwargs)
    t = MagicMock(spec=BehavioralStatusThresholds)
    for k, v in defaults.items():
        setattr(t, k, v)
    return t

def create_mock_rule(**kwargs):
    defaults = {
        "id": 1, "name": "Test Rule", "description": "Test",
        "rule_type": "custom", "is_system": False, "is_active": True,
        "shadow_mode": False, "company_id": 1,
        "condition_type": "threshold",
        "condition_config": {"metric": "burnout_risk", "operator": ">", "threshold": 0.7},
        "recommendation_template": {
            "type": "general", "priority": "high", "title": "Test Rec",
            "description": "Test", "suggested_action": "Test", "explanation": "Test",
        },
        "auto_execute_action": None, "auto_execute": False,
        "effectiveness_score": 0.0, "false_positive_rate": 0.0,
        "trigger_count": 0, "accepted_count": 0, "effective_count": 0,
        "false_positive_count": 0, "created_by": 1,
        "created_at": datetime.now(ZoneInfo(settings.TIMEZONE)).replace(tzinfo=None), "updated_at": datetime.now(ZoneInfo(settings.TIMEZONE)).replace(tzinfo=None),
    }
    defaults.update(kwargs)
    rule = MagicMock(spec=BehavioralRule)
    for k, v in defaults.items():
        setattr(rule, k, v)
    return rule

# ==========================================
# 1. Detector Tests
# ==========================================

class TestBehavioralDetector:
    """Tests for Layer 1: Detection - Metric computation"""

    @pytest.mark.asyncio
    async def test_compute_punctuality_perfect(self):
        """Perfect attendance should yield 100% score"""
        db = create_mock_db()
        detector = BehavioralDetector(db)

        db.execute = AsyncMock(side_effect=[
            MagicMock(scalar=MagicMock(return_value=20)),
            MagicMock(scalar=MagicMock(return_value=0)),
        ])

        result = await detector._compute_punctuality(1, 1, date.today()-timedelta(days=30), date.today())
        assert result == 100.0

    @pytest.mark.asyncio
    async def test_compute_punctuality_partial(self):
        """20% late days should yield 80% score"""
        db = create_mock_db()
        detector = BehavioralDetector(db)

        db.execute = AsyncMock(side_effect=[
            MagicMock(scalar=MagicMock(return_value=10)),
            MagicMock(scalar=MagicMock(return_value=2)),
        ])

        result = await detector._compute_punctuality(1, 1, date.today()-timedelta(days=30), date.today())
        assert result == 80.0

    @pytest.mark.asyncio
    async def test_compute_punctuality_no_data(self):
        """No logs should default to 100%"""
        db = create_mock_db()
        detector = BehavioralDetector(db)

        db.execute = AsyncMock(side_effect=[
            MagicMock(scalar=MagicMock(return_value=0)),
            MagicMock(scalar=MagicMock(return_value=0)),
        ])

        result = await detector._compute_punctuality(1, 1, date.today()-timedelta(days=30), date.today())
        assert result == 100.0

    @pytest.mark.asyncio
    async def test_compute_overtime_capped(self):
        """Overtime score should cap at 100%"""
        db = create_mock_db()
        detector = BehavioralDetector(db)

        # 20 hours OT per week (max is 10h for 100%)
        db.execute = AsyncMock(return_value=MagicMock(scalar=MagicMock(return_value=Decimal(140))))

        result = await detector._compute_overtime(1, 1, date.today()-timedelta(days=30), date.today())
        assert result == 100.0

    @pytest.mark.asyncio
    async def test_compute_burnout_risk_composite(self):
        """Burnout risk should combine OT, leave, and base factors"""
        db = create_mock_db()
        detector = BehavioralDetector(db)

        db.execute = AsyncMock(return_value=MagicMock(scalar=MagicMock(return_value=5)))

        result = await detector._compute_burnout_risk(1, 1, date.today()-timedelta(days=30), date.today(), 50.0)
        assert 0.0 <= result <= 1.0

    @pytest.mark.asyncio
    async def test_compute_financial_stress_capped(self):
        """Financial stress should cap at 1.0"""
        db = create_mock_db()
        detector = BehavioralDetector(db)

        # 10 advances (max is 3 for 0.8, so 10 should cap)
        db.execute = AsyncMock(return_value=MagicMock(scalar=MagicMock(return_value=10)))

        result = await detector._compute_financial_stress(1, 1, date.today()-timedelta(days=30), date.today())
        assert result == 1.0

    def test_determine_status_stable(self):
        """Good metrics should result in stable status"""
        db = create_mock_db()
        detector = BehavioralDetector(db)
        thresholds = create_mock_thresholds()

        status = detector._determine_status(
            punctuality=90.0, efficiency=90.0, burnout=0.2,
            financial=0.1, engagement=95.0, thresholds=thresholds,
            probation_mode=False,
        )
        assert status == "stable"

    def test_determine_status_critical_burnout(self):
        """High burnout should result in critical status"""
        db = create_mock_db()
        detector = BehavioralDetector(db)
        thresholds = create_mock_thresholds(burnout_critical=0.8)

        status = detector._determine_status(
            punctuality=90.0, efficiency=90.0, burnout=0.9,
            financial=0.1, engagement=95.0, thresholds=thresholds,
            probation_mode=False,
        )
        assert status == "critical"

    def test_determine_status_critical_low_metrics(self):
        """Low punctuality AND efficiency should result in critical"""
        db = create_mock_db()
        detector = BehavioralDetector(db)
        thresholds = create_mock_thresholds()

        status = detector._determine_status(
            punctuality=40.0, efficiency=30.0, burnout=0.2,
            financial=0.1, engagement=95.0, thresholds=thresholds,
            probation_mode=False,
        )
        assert status == "critical"

    def test_determine_status_star(self):
        """Excellent metrics should result in star status"""
        db = create_mock_db()
        detector = BehavioralDetector(db)
        thresholds = create_mock_thresholds()

        status = detector._determine_status(
            punctuality=98.0, efficiency=95.0, burnout=0.1,
            financial=0.0, engagement=98.0, thresholds=thresholds,
            probation_mode=False,
        )
        assert status == "star"

    def test_determine_status_probation_adjusted(self):
        """Probation mode should have stricter thresholds"""
        db = create_mock_db()
        detector = BehavioralDetector(db)
        thresholds = create_mock_thresholds()

        # These would be stable normally, but critical in probation
        status = detector._determine_status(
            punctuality=60.0, efficiency=50.0, burnout=0.2,
            financial=0.1, engagement=95.0, thresholds=thresholds,
            probation_mode=True,
        )
        assert status == "critical"

    def test_compute_contribution_factors(self):
        """Contribution factors should sum to 1.0"""
        db = create_mock_db()
        detector = BehavioralDetector(db)

        factors = detector._compute_contribution_factors(
            burnout=0.5, overtime=50.0, engagement=80.0, scrap=5.0,
        )
        assert "burnout_risk" in factors
        assert "overtime_hours" in factors
        assert abs(sum(factors.values()) - 1.0) < 0.01

# ==========================================
# 2. Rule Engine Tests
# ==========================================

class TestRuleEngine:
    """Tests for Layer 3: Rule Engine - Rule evaluation"""

    def test_evaluate_threshold_greater(self):
        """Threshold > operator should work correctly"""
        db = create_mock_db()
        engine = RuleEngine(db)
        profile = create_mock_profile(burnout_risk=0.8)
        config = {"metric": "burnout_risk", "operator": ">", "threshold": 0.7}

        assert engine._evaluate_threshold(config, profile) is True
        assert engine._evaluate_threshold({"metric": "burnout_risk", "operator": ">", "threshold": 0.9}, profile) is False

    def test_evaluate_threshold_less(self):
        """Threshold < operator should work correctly"""
        db = create_mock_db()
        engine = RuleEngine(db)
        profile = create_mock_profile(punctuality_score=60.0)
        config = {"metric": "punctuality_score", "operator": "<", "threshold": 70.0}

        assert engine._evaluate_threshold(config, profile) is True

    def test_evaluate_threshold_equal(self):
        """Threshold == operator should work with tolerance"""
        db = create_mock_db()
        engine = RuleEngine(db)
        profile = create_mock_profile(efficiency_score=85.0)
        config = {"metric": "efficiency_score", "operator": "==", "threshold": 85.0}

        assert engine._evaluate_threshold(config, profile) is True

    def test_evaluate_composite_and(self):
        """Composite AND should require all conditions"""
        db = create_mock_db()
        engine = RuleEngine(db)
        profile = create_mock_profile(burnout_risk=0.8, overtime_score=60.0)
        config = {
            "logic": "AND",
            "conditions": [
                {"metric": "burnout_risk", "operator": ">", "threshold": 0.7},
                {"metric": "overtime_score", "operator": ">", "threshold": 50.0},
            ],
        }

        assert engine._evaluate_composite(config, profile) is True

        config["conditions"][1]["threshold"] = 70.0
        assert engine._evaluate_composite(config, profile) is False

    def test_evaluate_composite_or(self):
        """Composite OR should require at least one condition"""
        db = create_mock_db()
        engine = RuleEngine(db)
        profile = create_mock_profile(burnout_risk=0.8, overtime_score=10.0)
        config = {
            "logic": "OR",
            "conditions": [
                {"metric": "burnout_risk", "operator": ">", "threshold": 0.7},
                {"metric": "overtime_score", "operator": ">", "threshold": 50.0},
            ],
        }

        assert engine._evaluate_composite(config, profile) is True

    def test_evaluate_trend_decreasing(self):
        """Trend decreasing should detect drops"""
        db = create_mock_db()
        engine = RuleEngine(db)
        profile = create_mock_profile(efficiency_score=80.0)
        config = {"metric": "efficiency_score", "direction": "decreasing", "min_decline_percent": 15.0}

        assert engine._evaluate_trend(config, profile) is True

        config["min_decline_percent"] = 25.0
        assert engine._evaluate_trend(config, profile) is False

    def test_evaluate_custom_expression(self):
        """Custom expression should evaluate safely"""
        db = create_mock_db()
        engine = RuleEngine(db)
        profile = create_mock_profile(burnout_risk=0.9, overtime_score=80.0)
        config = {"expression": "burnout > 0.8 and overtime > 70"}

        assert engine._evaluate_custom_expression(config, profile) is True

    def test_evaluate_custom_expression_invalid(self):
        """Invalid expression should return False"""
        db = create_mock_db()
        engine = RuleEngine(db)
        profile = create_mock_profile()
        config = {"expression": "invalid syntax !!!"}

        assert engine._evaluate_custom_expression(config, profile) is False

    @pytest.mark.asyncio
    async def test_create_recommendation_new(self):
        """Should create new recommendation if none exists"""
        db = create_mock_db()
        engine = RuleEngine(db)
        profile = create_mock_profile()
        rule = create_mock_rule()

        db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))

        rec = await engine._create_recommendation(rule, profile)
        assert rec is not None
        assert rec.type == "general"
        assert rec.priority == "high"

    @pytest.mark.asyncio
    async def test_create_recommendation_throttle(self):
        """Should throttle if recommendation already exists"""
        db = create_mock_db()
        engine = RuleEngine(db)
        profile = create_mock_profile()
        rule = create_mock_rule()

        existing_rec = MagicMock(aggregated_count=1, throttled=False)
        db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=existing_rec)))

        rec = await engine._create_recommendation(rule, profile)
        assert rec is None
        assert existing_rec.aggregated_count == 2
        assert existing_rec.throttled is True

# ==========================================
# 3. Context Analyzer Tests
# ==========================================

class TestContextAnalyzer:
    """Tests for Layer 2: Context - Why anomalies occur"""

    @pytest.mark.asyncio
    async def test_check_schedule_changes(self):
        """Should detect shift changes"""
        db = create_mock_db()
        analyzer = ContextAnalyzer(db)

        mock_shift_1 = MagicMock()
        mock_shift_1.name = "Morning"
        mock_shift_2 = MagicMock()
        mock_shift_2.name = "Night"

        mock_sched_1 = MagicMock(shift_id=1, shift=mock_shift_1, date=date.today()-timedelta(days=2))
        mock_sched_2 = MagicMock(shift_id=2, shift=mock_shift_2, date=date.today()-timedelta(days=1))

        mock_result = MagicMock()
        mock_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[mock_sched_1, mock_sched_2])))
        db.execute = AsyncMock(return_value=mock_result)

        result = await analyzer._check_schedule_changes(1, date.today()-timedelta(days=5), date.today())
        assert len(result) == 1
        assert result[0]["from"] == "Morning"
        assert result[0]["to"] == "Night"

    @pytest.mark.asyncio
    async def test_check_leave_history(self):
        """Should aggregate leave history"""
        db = create_mock_db()
        analyzer = ContextAnalyzer(db)

        mock_leave_1 = MagicMock()
        mock_leave_1.start_date = date.today()-timedelta(days=10)
        mock_leave_1.end_date = date.today()-timedelta(days=8)
        mock_leave_1.leave_type = "vacation"

        mock_leave_2 = MagicMock()
        mock_leave_2.start_date = date.today()-timedelta(days=5)
        mock_leave_2.end_date = date.today()-timedelta(days=4)
        mock_leave_2.leave_type = "sick"

        mock_result = MagicMock()
        mock_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[mock_leave_1, mock_leave_2])))
        db.execute = AsyncMock(return_value=mock_result)

        result = await analyzer._check_leave_history(1, date.today()-timedelta(days=30), date.today())
        assert result["total_days"] == 3
        assert result["types"]["vacation"] == 1
        assert result["types"]["sick"] == 1

    @pytest.mark.asyncio
    async def test_get_team_comparison(self):
        """Should compare user to department average"""
        db = create_mock_db()
        analyzer = ContextAnalyzer(db)

        mock_dept = MagicMock(id=1)
        mock_pos = MagicMock(department=mock_dept)
        mock_user = MagicMock(id=1, position_rel=mock_pos)

        mock_user_result = MagicMock()
        mock_user_result.scalar_one_or_none = MagicMock(return_value=mock_user)

        mock_avg_result = MagicMock()
        mock_avg_result.scalar = MagicMock(return_value=75.0)

        db.execute = AsyncMock(side_effect=[mock_user_result, mock_avg_result])

        result = await analyzer._get_team_comparison(1, 1, "punctuality_score")
        assert result["department_avg"] == 75.0

# ==========================================
# 4. Feedback Loop Tests
# ==========================================

class TestFeedbackLoop:
    """Tests for Layer 4: Feedback - Manager feedback collection"""

    @pytest.mark.asyncio
    async def test_record_feedback_accepted(self):
        """Accepted feedback should improve rule effectiveness"""
        db = create_mock_db()
        loop = FeedbackLoop(db)

        mock_rec = MagicMock(id=1, rule_id=10, status="pending")
        mock_rule = MagicMock(id=10, accepted_count=0, effectiveness_score=0.5)

        db.execute = AsyncMock(side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_rec)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_rule)),
        ])

        await loop.record_feedback(1, 1, "accepted")

        assert mock_rec.status == "accepted"
        assert mock_rule.accepted_count == 1
        assert mock_rule.effectiveness_score == 0.6

    @pytest.mark.asyncio
    async def test_record_feedback_ignored(self):
        """Ignored feedback should decrease rule effectiveness"""
        db = create_mock_db()
        loop = FeedbackLoop(db)

        mock_rec = MagicMock(id=1, rule_id=10, status="pending")
        mock_rule = MagicMock(id=10, false_positive_count=0, effectiveness_score=0.5)

        db.execute = AsyncMock(side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_rec)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_rule)),
        ])

        await loop.record_feedback(1, 1, "ignored")

        assert mock_rec.status == "ignored"
        assert mock_rule.false_positive_count == 1
        assert mock_rule.effectiveness_score == 0.45

    @pytest.mark.asyncio
    async def test_record_feedback_not_found(self):
        """Should raise error for non-existent recommendation"""
        db = create_mock_db()
        loop = FeedbackLoop(db)

        db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))

        with pytest.raises(ValueError, match="not found"):
            await loop.record_feedback(999, 1, "accepted")

# ==========================================
# 5. Organizational Health Tests
# ==========================================

class TestOrganizationalHealth:
    """Tests for department heatmaps and bias reports"""

    @pytest.mark.asyncio
    async def test_generate_bias_report_no_bias(self):
        """Similar departments should not trigger bias"""
        db = create_mock_db()
        health = OrganizationalHealth(db)

        dept_1 = MagicMock(id=1, name="Sales")
        dept_2 = MagicMock(id=2, name="IT")
        mock_result = MagicMock()
        mock_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[dept_1, dept_2])))
        db.execute = AsyncMock(return_value=mock_result)

        async def mock_avg(dept_id, *args):
            return 0.4

        health._get_dept_avg = mock_avg

        report = await health.generate_bias_report(1, date.today(), date.today())
        assert report.overall_bias_detected is False
        assert len(report.findings) == 0

    @pytest.mark.asyncio
    async def test_generate_bias_report_detected(self):
        """Different departments should trigger bias"""
        db = create_mock_db()
        health = OrganizationalHealth(db)

        dept_1 = MagicMock()
        dept_1.id = 1
        dept_1.name = "Sales"
        dept_2 = MagicMock()
        dept_2.id = 2
        dept_2.name = "IT"
        mock_result = MagicMock()
        mock_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[dept_1, dept_2])))
        db.execute = AsyncMock(return_value=mock_result)

        async def mock_avg(dept_id, *args):
            return 0.9 if dept_id == 1 else 0.2

        health._get_dept_avg = mock_avg

        report = await health.generate_bias_report(1, date.today(), date.today())
        assert report.overall_bias_detected is True
        assert len(report.findings) == 1
        assert report.findings[0]["group_a"] == "Sales"

    @pytest.mark.asyncio
    async def test_generate_bias_report_single_dept(self):
        """Single department should not trigger bias"""
        db = create_mock_db()
        health = OrganizationalHealth(db)

        dept_1 = MagicMock(id=1, name="Sales")
        mock_result = MagicMock()
        mock_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[dept_1])))
        db.execute = AsyncMock(return_value=mock_result)

        report = await health.generate_bias_report(1, date.today(), date.today())
        assert report.overall_bias_detected is False

# ==========================================
# 6. Resilience Tests
# ==========================================

class TestResilience:
    """Tests for circuit breaker and fallback mechanisms"""

    def test_circuit_breaker_opens_after_failures(self):
        """Should open circuit after threshold failures"""
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=60)

        async def failing_func():
            raise Exception("Test error")

        wrapped = cb.call(failing_func)

        for _ in range(3):
            with pytest.raises(Exception):
                asyncio.get_event_loop().run_until_complete(wrapped())

        assert cb.state == "open"

        with pytest.raises(CircuitBreakerError):
            asyncio.get_event_loop().run_until_complete(wrapped())

    def test_circuit_breaker_resets_on_success(self):
        """Should reset to closed on success"""
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=60)

        async def success_func():
            return "ok"

        wrapped = cb.call(success_func)

        result = asyncio.get_event_loop().run_until_complete(wrapped())
        assert result == "ok"
        assert cb.state == "closed"
        assert cb.failure_count == 0

    def test_circuit_breaker_half_open_recovery(self):
        """Should allow one test call after recovery timeout"""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0)

        async def failing_func():
            raise Exception("Test error")

        wrapped = cb.call(failing_func)

        with pytest.raises(Exception):
            asyncio.get_event_loop().run_until_complete(wrapped())

        assert cb.state == "open"

        # After timeout, should move to half-open
        import time
        time.sleep(0.1)

        # Next call should attempt execution
        async def success_func():
            return "recovered"

        wrapped_success = cb.call(success_func)
        result = asyncio.get_event_loop().run_until_complete(wrapped_success())
        assert result == "recovered"
        assert cb.state == "closed"

# ==========================================
# 7. Triggered Events Tests
# ==========================================

class TestTriggeredEvents:
    """Tests for real-time event processing"""

    @pytest.mark.asyncio
    async def test_handle_clock_out_excessive_hours(self):
        """Should detect >12h work sessions"""
        db = create_mock_db()
        processor = TriggeredEventProcessor(db)

        mock_user = MagicMock(company_id=1)
        mock_health = MagicMock(triggered_alerts_today=0)

        db.execute = AsyncMock(side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_user)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_health)),
        ])

        mock_log = MagicMock(
            user_id=1,
            hours_worked=13.0,
            break_duration=1.0,
            end_time=datetime.now(ZoneInfo(settings.TIMEZONE)).replace(tzinfo=None),
        )

        anomalies = await processor.handle_clock_out(mock_log)
        assert len(anomalies) >= 1
        assert anomalies[0].anomaly_type == "real_time_excessive_hours"
        assert anomalies[0].severity == 4

    @pytest.mark.asyncio
    async def test_handle_clock_out_missed_break(self):
        """Should detect missed breaks"""
        db = create_mock_db()
        processor = TriggeredEventProcessor(db)

        mock_user = MagicMock(company_id=1)
        mock_health = MagicMock(triggered_alerts_today=0)

        db.execute = AsyncMock(side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_user)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_health)),
        ])

        mock_log = MagicMock(
            user_id=1,
            hours_worked=7.0,
            break_duration=10/60,
            end_time=datetime.now(ZoneInfo(settings.TIMEZONE)).replace(tzinfo=None),
        )

        anomalies = await processor.handle_clock_out(mock_log)
        assert len(anomalies) >= 1
        assert anomalies[0].anomaly_type == "real_time_missed_break"

    @pytest.mark.asyncio
    async def test_handle_clock_out_night_overtime(self):
        """Should detect night overtime"""
        db = create_mock_db()
        processor = TriggeredEventProcessor(db)

        mock_user = MagicMock(company_id=1)
        mock_health = MagicMock(triggered_alerts_today=0)

        db.execute = AsyncMock(side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_user)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_health)),
        ])

        mock_log = MagicMock(
            user_id=1,
            hours_worked=9.0,
            break_duration=1.0,
            end_time=datetime.now(ZoneInfo(settings.TIMEZONE)).replace(tzinfo=None).replace(hour=23, minute=30),
        )

        anomalies = await processor.handle_clock_out(mock_log)
        assert len(anomalies) >= 1
        assert anomalies[0].anomaly_type == "real_time_night_overtime"

    @pytest.mark.asyncio
    async def test_check_consecutive_days_risk(self):
        """Should detect >10 consecutive work days"""
        db = create_mock_db()
        processor = TriggeredEventProcessor(db)

        db.execute = AsyncMock(side_effect=[
            MagicMock(scalar=MagicMock(return_value=1)) for _ in range(11)
        ] + [MagicMock(scalar=MagicMock(return_value=0))])

        anomalies = await processor.check_consecutive_days(1)
        assert len(anomalies) == 1
        assert anomalies[0].actual_value == 11

    @pytest.mark.asyncio
    async def test_update_triggered_alerts_count(self):
        """Should increment daily alert counter"""
        db = create_mock_db()
        processor = TriggeredEventProcessor(db)

        mock_user = MagicMock(company_id=1)
        mock_health = MagicMock(triggered_alerts_today=0)

        db.execute = AsyncMock(side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_user)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_health)),
        ])

        await processor._update_triggered_alerts_count(1)
        assert mock_health.triggered_alerts_today == 1
