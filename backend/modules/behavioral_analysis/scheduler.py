import logging
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from backend.database.models import Company
from backend.modules.behavioral_analysis.detector import BehavioralDetector
from backend.modules.behavioral_analysis.rule_engine import RuleEngine
from backend.services.module_service import ModuleService
from sqlalchemy import select

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

async def compute_nightly_profiles():
    """Nightly job: compute behavioral profiles for all active companies"""
    from backend.database.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        companies_result = await db.execute(select(Company).where(Company.is_active))
        companies = companies_result.scalars().all()

        for company in companies:
            is_enabled = await ModuleService.is_enabled(db, "behavioral_analysis")
            if not is_enabled:
                continue

            period_end = date.today()
            period_start = period_end - timedelta(days=30)

            logger.info(f"Computing behavioral profiles for company {company.id} ({company.name})")

            try:
                detector = BehavioralDetector(db)
                profiles = await detector.compute_all_profiles(
                    company_id=company.id,
                    period_start=period_start,
                    period_end=period_end,
                    incremental=True,
                )
                logger.info(f"Computed {len(profiles)} profiles for company {company.id}")

                rule_engine = RuleEngine(db)
                for profile in profiles:
                    await rule_engine.detect_anomalies(profile, company.id)

                await rule_engine.evaluate_all_rules(company.id)

            except Exception as e:
                logger.error(f"Failed to compute profiles for company {company.id}: {e}")

async def cleanup_old_data():
    """Cleanup job: remove old data based on retention settings"""
    from backend.database.database import AsyncSessionLocal
    from backend.modules.behavioral_analysis.models import (
        BehavioralProfile,
        BehavioralRetentionSettings,
    )

    async with AsyncSessionLocal() as db:
        settings_result = await db.execute(select(BehavioralRetentionSettings))
        settings_list = settings_result.scalars().all()

        for settings in settings_list:
            if not settings.auto_cleanup_enabled:
                continue

            cutoff_date = datetime.now(ZoneInfo(settings.TIMEZONE)).replace(tzinfo=None) - timedelta(days=settings.raw_profile_days)

            await db.execute(
                select(BehavioralProfile).where(BehavioralProfile.computed_at < cutoff_date),
            )
            logger.info(f"Cleaned up old data for company {settings.company_id}")

def start_scheduler():
    """Start the behavioral analysis scheduler"""
    scheduler.add_job(
        compute_nightly_profiles,
        "cron",
        hour=2,
        minute=0,
        id="behavioral_nightly_computation",
        replace_existing=True,
    )
    scheduler.add_job(
        cleanup_old_data,
        "cron",
        hour=3,
        minute=0,
        id="behavioral_cleanup",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Behavioral analysis scheduler started")

def stop_scheduler():
    """Stop the behavioral analysis scheduler"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Behavioral analysis scheduler stopped")
