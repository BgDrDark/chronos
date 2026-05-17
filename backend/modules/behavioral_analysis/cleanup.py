import logging
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from backend.config import settings
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func

from backend.modules.behavioral_analysis.models import (
    BehavioralProfile,
    BehavioralAnomaly,
    BehavioralRecommendation,
    RecommendationFeedback,
    BehavioralRetentionSettings,
    DepartmentHealthReport,
    BiasReport,
)

logger = logging.getLogger(__name__)


class BehavioralCleanup:
    """Data retention and cleanup service for behavioral analysis module"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def cleanup_expired_data(self, company_id: int) -> dict:
        """Delete or anonymize expired behavioral data based on retention settings"""
        settings = await self._get_retention_settings(company_id)
        if not settings:
            logger.info(f"No retention settings found for company {company_id}")
            return {"status": "skipped", "reason": "no_settings"}

        results = {
            "profiles_deleted": 0,
            "profiles_anonymized": 0,
            "anomalies_deleted": 0,
            "recommendations_deleted": 0,
            "feedback_deleted": 0,
            "reports_deleted": 0,
        }

        if settings.auto_cleanup_enabled:
            now = datetime.now(ZoneInfo(settings.TIMEZONE)).replace(tzinfo=None)
            cutoff_profiles = now - timedelta(days=settings.raw_profile_days)
            cutoff_recommendations = now - timedelta(days=settings.recommendation_months * 30)
            cutoff_feedback = now - timedelta(days=settings.feedback_months * 30)

            if settings.anonymize_instead_of_delete:
                results["profiles_anonymized"] = await self._anonymize_expired_profiles(company_id, cutoff_profiles)
            else:
                results["profiles_deleted"] = await self._delete_expired_profiles(company_id, cutoff_profiles)

            results["anomalies_deleted"] = await self._delete_expired_anomalies(company_id, cutoff_profiles)
            results["recommendations_deleted"] = await self._delete_expired_recommendations(company_id, cutoff_recommendations)
            results["feedback_deleted"] = await self._delete_expired_feedback(company_id, cutoff_feedback)
            results["reports_deleted"] = await self._delete_expired_reports(company_id)

        logger.info(f"Cleanup completed for company {company_id}: {results}")
        return results

    async def _get_retention_settings(self, company_id: int) -> Optional[BehavioralRetentionSettings]:
        result = await self.db.execute(
            select(BehavioralRetentionSettings).where(
                BehavioralRetentionSettings.company_id == company_id
            )
        )
        return result.scalar_one_or_none()

    async def _delete_expired_profiles(self, company_id: int, cutoff: datetime) -> int:
        stmt = delete(BehavioralProfile).where(
            BehavioralProfile.company_id == company_id,
            BehavioralProfile.computed_at < cutoff,
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount or 0

    async def _anonymize_expired_profiles(self, company_id: int, cutoff: datetime) -> int:
        stmt = (
            update(BehavioralProfile)
            .where(
                BehavioralProfile.company_id == company_id,
                BehavioralProfile.computed_at < cutoff,
            )
            .values(
                user_id=None,
                status="anonymized",
                contribution_factors=None,
            )
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount or 0

    async def _delete_expired_anomalies(self, company_id: int, cutoff: datetime) -> int:
        stmt = delete(BehavioralAnomaly).where(
            BehavioralAnomaly.detected_at < cutoff,
            BehavioralAnomaly.profile_id.in_(
                select(BehavioralProfile.id).where(
                    BehavioralProfile.company_id == company_id
                )
            ),
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount or 0

    async def _delete_expired_recommendations(self, company_id: int, cutoff: datetime) -> int:
        stmt = delete(BehavioralRecommendation).where(
            BehavioralRecommendation.created_at < cutoff,
            BehavioralRecommendation.user_id.in_(
                select(BehavioralProfile.user_id).where(
                    BehavioralProfile.company_id == company_id
                )
            ),
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount or 0

    async def _delete_expired_feedback(self, company_id: int, cutoff: datetime) -> int:
        stmt = delete(RecommendationFeedback).where(
            RecommendationFeedback.action_taken_at < cutoff,
            RecommendationFeedback.recommendation_id.in_(
                select(BehavioralRecommendation.id).where(
                    BehavioralRecommendation.user_id.in_(
                        select(BehavioralProfile.user_id).where(
                            BehavioralProfile.company_id == company_id
                        )
                    )
                )
            ),
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount or 0

    async def _delete_expired_reports(self, company_id: int) -> int:
        six_months_ago = datetime.now(ZoneInfo(settings.TIMEZONE)).replace(tzinfo=None) - timedelta(days=180)
        deleted = 0

        dept_stmt = delete(DepartmentHealthReport).where(
            DepartmentHealthReport.company_id == company_id,
            DepartmentHealthReport.generated_at < six_months_ago,
        )
        dept_result = await self.db.execute(dept_stmt)
        deleted += dept_result.rowcount or 0

        bias_stmt = delete(BiasReport).where(
            BiasReport.company_id == company_id,
            BiasReport.generated_at < six_months_ago,
        )
        bias_result = await self.db.execute(bias_stmt)
        deleted += bias_result.rowcount or 0

        await self.db.commit()
        return deleted
