"""Utility functions for Chronos Gateway"""

import zoneinfo
from datetime import datetime, timezone

from gateway.config import config


def now_tz() -> datetime:
    """Връща текущото време в конфигурираната часова зона"""
    try:
        tz = zoneinfo.ZoneInfo(config.timezone)
    except (KeyError, TypeError):
        tz = zoneinfo.ZoneInfo("Europe/Sofia")
    return datetime.now(tz)


def now_utc() -> datetime:
    """Връща текущото време в UTC"""
    return datetime.now(timezone.utc)
