import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from backend.config import settings
from backend.modules.behavioral_analysis.models import (
    BehavioralRecommendation,
    BehavioralRule,
    RecommendationFeedback,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

class FeedbackLoop:
    """Layer 4: Feedback - Collects and processes manager feedback"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_feedback(
        self,
        recommendation_id: int,
        manager_id: int,
        action: str,
        notes: str | None = None,
        outcome: str | None = None,
    ) -> RecommendationFeedback:
        rec_result = await self.db.execute(
            select(BehavioralRecommendation).where(BehavioralRecommendation.id == recommendation_id),
        )
        rec = rec_result.scalar_one_or_none()
        if not rec:
            raise ValueError(f"Recommendation {recommendation_id} not found")

        now = datetime.now(ZoneInfo(settings.TIMEZONE)).replace(tzinfo=None)
        feedback = RecommendationFeedback(
            recommendation_id=recommendation_id,
            manager_id=manager_id,
            manager_action=action,
            manager_notes=notes,
            action_taken_at=now,
            outcome=outcome or "unknown",
            outcome_measured_at=now,
            days_to_outcome=0,
            improvement_delta=0.0,
        )
        self.db.add(feedback)

        if action == "accepted":
            rec.status = "accepted"
            rule_result = await self.db.execute(select(BehavioralRule).where(BehavioralRule.id == rec.rule_id))
            rule = rule_result.scalar_one_or_none()
            if rule:
                rule.accepted_count += 1
                rule.effectiveness_score = min(1.0, rule.effectiveness_score + 0.1)
        elif action == "ignored":
            rec.status = "ignored"
            rule_result = await self.db.execute(select(BehavioralRule).where(BehavioralRule.id == rec.rule_id))
            rule = rule_result.scalar_one_or_none()
            if rule:
                rule.false_positive_count += 1
                rule.effectiveness_score = max(0.0, rule.effectiveness_score - 0.05)

        await self.db.commit()
        return feedback
