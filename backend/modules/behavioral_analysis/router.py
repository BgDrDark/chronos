import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.database import get_db
from backend.modules.behavioral_analysis.cleanup import BehavioralCleanup
from backend.modules.behavioral_analysis.triggered_events import TriggeredEventProcessor
from backend.services.module_service import ModuleService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/behavioral-analysis", tags=["behavioral-analysis"])


@router.post("/cleanup/{company_id}")
async def trigger_cleanup(company_id: int, db: AsyncSession = Depends(get_db)):
    """Trigger data cleanup for a company based on retention settings"""
    is_enabled = await ModuleService.is_enabled(db, "behavioral_analysis")
    if not is_enabled:
        raise HTTPException(status_code=403, detail="Behavioral analysis module is disabled")

    cleanup = BehavioralCleanup(db)
    results = await cleanup.cleanup_expired_data(company_id)
    return {"status": "completed", "results": results}


@router.get("/cleanup/status/{company_id}")
async def get_cleanup_status(company_id: int, db: AsyncSession = Depends(get_db)):
    """Get cleanup status and retention settings for a company"""
    is_enabled = await ModuleService.is_enabled(db, "behavioral_analysis")
    if not is_enabled:
        raise HTTPException(status_code=403, detail="Behavioral analysis module is disabled")

    from backend.modules.behavioral_analysis.models import BehavioralRetentionSettings
    from sqlalchemy import select

    result = await db.execute(
        select(BehavioralRetentionSettings).where(
            BehavioralRetentionSettings.company_id == company_id
        )
    )
    settings = result.scalar_one_or_none()

    if not settings:
        return {"status": "no_settings", "company_id": company_id}

    return {
        "company_id": company_id,
        "auto_cleanup_enabled": settings.auto_cleanup_enabled,
        "cleanup_schedule": settings.cleanup_schedule,
        "anonymize_instead_of_delete": settings.anonymize_instead_of_delete,
        "raw_profile_days": settings.raw_profile_days,
        "aggregated_profile_months": settings.aggregated_profile_months,
        "recommendation_months": settings.recommendation_months,
        "feedback_months": settings.feedback_months,
    }


@router.post("/triggered-events/check-consecutive/{user_id}")
async def check_consecutive_days(user_id: int, db: AsyncSession = Depends(get_db)):
    """Check consecutive work days for a user and trigger alerts if needed"""
    is_enabled = await ModuleService.is_enabled(db, "behavioral_analysis")
    if not is_enabled:
        raise HTTPException(status_code=403, detail="Behavioral analysis module is disabled")

    processor = TriggeredEventProcessor(db)
    anomalies = await processor.check_consecutive_days(user_id)

    return {
        "user_id": user_id,
        "anomalies_detected": len(anomalies),
        "anomalies": [
            {
                "type": a.anomaly_type,
                "severity": a.severity,
                "description": a.description,
            }
            for a in anomalies
        ],
    }
