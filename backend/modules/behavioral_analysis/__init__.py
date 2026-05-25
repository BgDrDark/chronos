MODULE_CONFIG = {
    "code": "behavioral_analysis",
    "name": "Поведенчески анализ",
    "description": "4-слоен поведенчески анализ с динамични правила",
    "version": "1.0.0",
    "super_admin_only": True,
    "core_module": False,
    "required_permissions": ["behavioral_analysis:view", "behavioral_analysis:manage"],
}

async def initialize_module(db, company_id: int):
    """Create default settings and built-in rules for new company"""
    from sqlalchemy import select

    from .config import DEFAULT_RULES, DEFAULT_SETTINGS
    from .models import (
        BehavioralComputationSettings,
        BehavioralMetricWeights,
        BehavioralRetentionSettings,
        BehavioralRule,
        BehavioralStatusThresholds,
    )

    existing = await db.execute(
        select(BehavioralRetentionSettings).where(
            BehavioralRetentionSettings.company_id == company_id,
        ),
    )
    if existing.scalar_one_or_none():
        return

    defaults = DEFAULT_SETTINGS(company_id)
    retention = BehavioralRetentionSettings(**defaults["retention"])
    thresholds = BehavioralStatusThresholds(**defaults["thresholds"])
    computation = BehavioralComputationSettings(**defaults["computation"])
    weights = BehavioralMetricWeights(**defaults["weights"])

    db.add_all([retention, thresholds, computation, weights])

    for rule_data in DEFAULT_RULES(company_id):
        rule = BehavioralRule(**rule_data)
        db.add(rule)

    await db.commit()


async def cleanup_module(db, company_id: int):
    """Anonymize behavioral data when module is disabled"""
    from sqlalchemy import update

    from .models import BehavioralProfile, BehavioralRecommendation

    await db.execute(
        update(BehavioralProfile)
        .where(BehavioralProfile.company_id == company_id)
        .values(status="archived", contribution_factors=None),
    )
    await db.execute(
        update(BehavioralRecommendation)
        .where(BehavioralRecommendation.status == "pending")
        .values(status="archived"),
    )
    await db.commit()
