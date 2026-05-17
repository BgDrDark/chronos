import logging
from datetime import datetime, date, timedelta, timezone
from zoneinfo import ZoneInfo
from backend.config import settings
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from backend.database.models import TimeLog, User
from backend.modules.behavioral_analysis.models import (
    BehavioralAnomaly, BehavioralProfile, BehavioralSystemHealth
)
from backend.modules.behavioral_analysis.detector import BehavioralDetector
from backend.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class TriggeredEventProcessor:
    """Real-time event processor for behavioral analysis"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.notification_service = NotificationService(db)

    async def handle_clock_out(self, time_log: TimeLog) -> List[BehavioralAnomaly]:
        """Process a clock-out event to detect immediate risks"""
        anomalies = []
        user_id = time_log.user_id
        duration = time_log.hours_worked or 0
        now = datetime.now(ZoneInfo(settings.TIMEZONE)).replace(tzinfo=None)

        # 1. Check for excessive duration (> 12 hours)
        if duration > 12:
            anomaly = BehavioralAnomaly(
                user_id=user_id,
                profile_id=None,
                anomaly_type="real_time_excessive_hours",
                severity=4,
                metric_name="overtime_score",
                actual_value=duration,
                expected_value=8.0,
                deviation=duration - 8.0,
                description=f"Clock-out detected with {duration:.1f} hours worked (Threshold: 12h)",
                detected_at=now
            )
            self.db.add(anomaly)
            anomalies.append(anomaly)
            logger.warning(f"Real-time alert: User {user_id} worked {duration} hours")

            # Send notification
            try:
                await self.notification_service.create_notification(
                    user_id=user_id,
                    message=f"⚠️ Висок риск: Работили сте {duration:.1f} часа днес."
                )
            except Exception as e:
                logger.error(f"Failed to send notification: {e}")

        # 2. Check for missed breaks (if duration > 6 and break < 30min)
        if duration > 6 and (time_log.break_duration or 0) < 0.5:
            anomaly = BehavioralAnomaly(
                user_id=user_id,
                profile_id=None,
                anomaly_type="real_time_missed_break",
                severity=3,
                metric_name="burnout_risk",
                actual_value=time_log.break_duration or 0,
                expected_value=0.5,
                deviation=0.5 - (time_log.break_duration or 0),
                description=f"Missed break: {duration:.1f}h work with only {(time_log.break_duration or 0)*60:.0f}min break",
                detected_at=now
            )
            self.db.add(anomaly)
            anomalies.append(anomaly)
            logger.warning(f"Real-time alert: User {user_id} missed break")

        # 3. Check for night shift overtime (End > 23:00 AND Duration > 8)
        if time_log.end_time:
            end_hour = time_log.end_time.hour + time_log.end_time.minute / 60.0
            if end_hour > 23.0 and duration > 8:
                anomaly = BehavioralAnomaly(
                    user_id=user_id,
                    profile_id=None,
                    anomaly_type="real_time_night_overtime",
                    severity=3,
                    metric_name="burnout_risk",
                    actual_value=end_hour,
                    expected_value=23.0,
                    deviation=end_hour - 23.0,
                    description=f"Night overtime: worked until {time_log.end_time.strftime('%H:%M')} ({duration:.1f}h)",
                    detected_at=now
                )
                self.db.add(anomaly)
                anomalies.append(anomaly)

        if anomalies:
            await self._update_triggered_alerts_count(time_log.user_id)
            await self.db.commit()

        return anomalies

    async def check_consecutive_days(self, user_id: int) -> List[BehavioralAnomaly]:
        """Check if user has worked too many consecutive days"""
        today = date.today()
        anomalies = []

        consecutive_days = 0
        check_date = today

        while True:
            next_day = check_date + timedelta(days=1)
            res = await self.db.execute(
                select(func.count(TimeLog.id)).where(
                    TimeLog.user_id == user_id,
                    TimeLog.start_time >= check_date,
                    TimeLog.start_time < next_day
                )
            )
            count = res.scalar() or 0
            if count > 0:
                consecutive_days += 1
                check_date -= timedelta(days=1)
            else:
                break

        if consecutive_days > 10:
            anomaly = BehavioralAnomaly(
                user_id=user_id,
                profile_id=None,
                anomaly_type="real_time_consecutive_days",
                severity=4,
                metric_name="burnout_risk",
                actual_value=consecutive_days,
                expected_value=5.0,
                deviation=consecutive_days - 5.0,
                description=f"Consecutive work days: {consecutive_days} (Threshold: 10)",
                detected_at=datetime.now(ZoneInfo(settings.TIMEZONE)).replace(tzinfo=None)
            )
            self.db.add(anomaly)
            anomalies.append(anomaly)
            logger.warning(f"Real-time alert: User {user_id} worked {consecutive_days} consecutive days")

            # Send notification
            try:
                await self.notification_service.create_notification(
                    user_id=user_id,
                    message=f"📅 Внимание: Работили сте {consecutive_days} поредни дни без почивка."
                )
            except Exception as e:
                logger.error(f"Failed to send notification: {e}")

        if anomalies:
            await self.db.commit()
        return anomalies

    async def _update_triggered_alerts_count(self, user_id: int):
        """Update the daily alert counter in system health"""
        user_res = await self.db.execute(select(User).where(User.id == user_id))
        user = user_res.scalar_one_or_none()
        if not user or not user.company_id:
            return

        health_res = await self.db.execute(
            select(BehavioralSystemHealth).where(BehavioralSystemHealth.company_id == user.company_id)
        )
        health = health_res.scalar_one_or_none()
        if not health:
            health = BehavioralSystemHealth(company_id=user.company_id)
            self.db.add(health)

        health.triggered_alerts_today += 1
