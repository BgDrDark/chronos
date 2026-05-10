import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.modules.behavioral_analysis.models import (
    BehavioralRule, BehavioralAnomaly, BehavioralRecommendation,
    BehavioralProfile, BehavioralSystemHealth
)

logger = logging.getLogger(__name__)

class RuleEngine:
    """Layer 3: Rule Engine - Evaluates rules against profiles and generates recommendations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def evaluate_all_rules(self, company_id: int) -> List[BehavioralRecommendation]:
        rules_result = await self.db.execute(
            select(BehavioralRule).where(
                BehavioralRule.company_id == company_id,
                BehavioralRule.is_active == True
            )
        )
        rules = rules_result.scalars().all()
        
        profiles_result = await self.db.execute(
            select(BehavioralProfile).where(
                BehavioralProfile.company_id == company_id
            ).options(selectinload(BehavioralProfile.anomalies))
        )
        profiles = profiles_result.scalars().all()
        
        recommendations = []
        for profile in profiles:
            for rule in rules:
                if rule.shadow_mode:
                    continue
                    
                triggered = await self._evaluate_rule(rule, profile)
                if triggered:
                    rec = await self._create_recommendation(rule, profile)
                    if rec:
                        recommendations.append(rec)
                        rule.trigger_count += 1
                        
        await self.db.commit()
        return recommendations

    async def _evaluate_rule(self, rule: BehavioralRule, profile: BehavioralProfile) -> bool:
        condition_type = rule.condition_type
        config = rule.condition_config
        
        if condition_type == "threshold":
            return self._evaluate_threshold(config, profile)
        elif condition_type == "composite":
            return self._evaluate_composite(config, profile)
        elif condition_type == "trend":
            return self._evaluate_trend(config, profile)
        elif condition_type == "custom_expression":
            return self._evaluate_custom_expression(config, profile)
        return False

    def _evaluate_threshold(self, config: Dict[str, Any], profile: BehavioralProfile) -> bool:
        metric = config.get("metric")
        operator = config.get("operator", ">")
        threshold = config.get("threshold", 0)
        
        value = getattr(profile, metric, None)
        if value is None:
            return False
            
        if operator == ">":
            return value > threshold
        elif operator == ">=":
            return value >= threshold
        elif operator == "<":
            return value < threshold
        elif operator == "<=":
            return value <= threshold
        elif operator == "==":
            return abs(value - threshold) < 0.01
        return False

    def _evaluate_composite(self, config: Dict[str, Any], profile: BehavioralProfile) -> bool:
        logic = config.get("logic", "AND")
        conditions = config.get("conditions", [])
        
        results = []
        for cond in conditions:
            metric = cond.get("metric")
            operator = cond.get("operator", ">")
            threshold = cond.get("threshold", 0)
            value = getattr(profile, metric, None)
            if value is None:
                results.append(False)
                continue
                
            if operator == ">":
                results.append(value > threshold)
            elif operator == ">=":
                results.append(value >= threshold)
            elif operator == "<":
                results.append(value < threshold)
            elif operator == "<=":
                results.append(value <= threshold)
                
        if logic == "AND":
            return all(results)
        elif logic == "OR":
            return any(results)
        return False

    def _evaluate_trend(self, config: Dict[str, Any], profile: BehavioralProfile) -> bool:
        direction = config.get("direction", "decreasing")
        min_decline = config.get("min_decline_percent", 5.0)
        metric = config.get("metric")
        
        value = getattr(profile, metric, None)
        if value is None:
            return False
            
        if direction == "decreasing":
            return value < (100.0 - min_decline)
        elif direction == "increasing":
            return value > min_decline
        return False

    def _evaluate_custom_expression(self, config: Dict[str, Any], profile: BehavioralProfile) -> bool:
        expression = config.get("expression", "")
        try:
            safe_vars = {
                "punctuality": profile.punctuality_score,
                "efficiency": profile.efficiency_score,
                "overtime": profile.overtime_score,
                "burnout": profile.burnout_risk,
                "financial_stress": profile.financial_stress_score,
                "engagement": profile.engagement_score,
                "scrap_rate": profile.scrap_rate,
            }
            for key, val in safe_vars.items():
                expression = expression.replace(key, str(val))
            return bool(eval(expression, {"__builtins__": {}}, {}))
        except Exception as e:
            logger.error(f"Custom expression evaluation failed: {e}")
            return False

    async def _create_recommendation(self, rule: BehavioralRule, profile: BehavioralProfile) -> Optional[BehavioralRecommendation]:
        template = rule.recommendation_template
        
        existing_result = await self.db.execute(
            select(BehavioralRecommendation).where(
                BehavioralRecommendation.user_id == profile.user_id,
                BehavioralRecommendation.rule_id == rule.id,
                BehavioralRecommendation.status.in_(["pending", "accepted"])
            )
        )
        existing = existing_result.scalar_one_or_none()
        if existing:
            existing.aggregated_count += 1
            existing.throttled = True
            return None
            
        rec = BehavioralRecommendation(
            rule_id=rule.id,
            user_id=profile.user_id,
            type=template.get("type", "general"),
            priority=template.get("priority", "medium"),
            title=template.get("title", "Препоръка"),
            description=template.get("description", ""),
            suggested_action=template.get("suggested_action", ""),
            explanation=template.get("explanation", ""),
            coaching_tips=template.get("coaching_tips"),
            confidence_score=0.8,
            status="pending",
        )
        self.db.add(rec)
        return rec

    async def detect_anomalies(self, profile: BehavioralProfile, company_id: int) -> List[BehavioralAnomaly]:
        anomalies = []
        metrics = [
            ("punctuality_score", 70.0, "low"),
            ("efficiency_score", 60.0, "low"),
            ("burnout_risk", 0.7, "high"),
            ("financial_stress_score", 0.6, "high"),
            ("engagement_score", 50.0, "low"),
            ("scrap_rate", 10.0, "high"),
        ]
        
        for metric_name, threshold, direction in metrics:
            value = getattr(profile, metric_name, 0)
            is_anomaly = False
            if direction == "low" and value < threshold:
                is_anomaly = True
            elif direction == "high" and value > threshold:
                is_anomaly = True
                
            if is_anomaly:
                anomaly = BehavioralAnomaly(
                    profile_id=profile.id,
                    user_id=profile.user_id,
                    anomaly_type="threshold_breach",
                    severity=4 if abs(value - threshold) > threshold * 0.3 else 2,
                    metric_name=metric_name,
                    actual_value=value,
                    expected_value=threshold,
                    deviation=abs(value - threshold),
                    description=f"{metric_name} = {value:.1f} (праг: {threshold})",
                )
                self.db.add(anomaly)
                anomalies.append(anomaly)
                
        await self.db.commit()
        return anomalies
