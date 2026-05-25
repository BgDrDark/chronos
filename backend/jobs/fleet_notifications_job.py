import logging
from datetime import datetime, timedelta

from sqlalchemy import select

from backend.database import models
from backend.database.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def get_fleet_notification_recipients(db, company_id):
    """Get users who should receive fleet notifications for a company.
    Returns admin, super_admin, and fleet_manager roles.
    Falls back to all active users if no specific roles found.
    """
    stmt = select(models.User).where(
        models.User.company_id == company_id,
        models.User.is_active,
        models.User.role_id.in_(
            select(models.Role.id).where(
                models.Role.name.in_(["admin", "super_admin", "fleet_manager"]),
            ),
        ),
    )
    result = await db.execute(stmt)
    users = list(result.scalars().all())

    if not users:
        stmt = select(models.User).where(
            models.User.company_id == company_id,
            models.User.is_active,
        )
        result = await db.execute(stmt)
        users = list(result.scalars().all())

    return users


async def check_fleet_notifications():
    """Periodic job to check for expiring fleet items and send notifications.
    Runs daily at 6:00 AM.
    """
    logger.info("Starting scheduled fleet notifications check...")

    async with AsyncSessionLocal() as db:
        try:
            today = datetime.now().date()
            thirty_days = today + timedelta(days=30)
            seven_days = today + timedelta(days=7)

            notifications_created = 0

            stmt_insurance = select(models.VehicleInsurance).where(
                models.VehicleInsurance.end_date <= thirty_days,
                models.VehicleInsurance.end_date >= today,
            )
            result = await db.execute(stmt_insurance)
            insurances = result.scalars().all()

            for insurance in insurances:
                days_left = (insurance.end_date - today).days
                vehicle = insurance.vehicle
                message = f"Застраховката на {vehicle.registration_number} изтича след {days_left} дни"
                logger.info(message)

                recipients = await get_fleet_notification_recipients(db, vehicle.company_id)
                for recipient in recipients:
                    notification = models.Notification(
                        user_id=recipient.id,
                        title="Изтичаща застраховка",
                        message=message,
                        notification_type="fleet_insurance",
                        reference_id=insurance.id,
                        company_id=vehicle.company_id,
                    )
                    db.add(notification)
                    notifications_created += 1

            stmt_inspection = select(models.VehicleInspection).where(
                models.VehicleInspection.valid_until <= thirty_days,
                models.VehicleInspection.valid_until >= today,
            )
            result = await db.execute(stmt_inspection)
            inspections = result.scalars().all()

            for inspection in inspections:
                days_left = (inspection.valid_until - today).days
                vehicle = inspection.vehicle
                message = f"ГТП на {vehicle.registration_number} изтича след {days_left} дни"
                logger.info(message)

                recipients = await get_fleet_notification_recipients(db, vehicle.company_id)
                for recipient in recipients:
                    notification = models.Notification(
                        user_id=recipient.id,
                        title="Изтичащо ГТП",
                        message=message,
                        notification_type="fleet_inspection",
                        reference_id=inspection.id,
                        company_id=vehicle.company_id,
                    )
                    db.add(notification)
                    notifications_created += 1

            stmt_vignette = select(models.VehicleVignette).where(
                models.VehicleVignette.valid_until <= seven_days,
                models.VehicleVignette.valid_until >= today,
            )
            result = await db.execute(stmt_vignette)
            vignettes = result.scalars().all()

            for vignette in vignettes:
                days_left = (vignette.valid_until - today).days
                vehicle = vignette.vehicle
                message = f"Винетката на {vehicle.registration_number} изтича след {days_left} дни"
                logger.info(message)

                recipients = await get_fleet_notification_recipients(db, vehicle.company_id)
                for recipient in recipients:
                    notification = models.Notification(
                        user_id=recipient.id,
                        title="Изтичаща винетка",
                        message=message,
                        notification_type="fleet_vignette",
                        reference_id=vignette.id,
                        company_id=vehicle.company_id,
                    )
                    db.add(notification)
                    notifications_created += 1

            stmt_schedule = select(models.VehicleSchedule).where(
                models.VehicleSchedule.next_service_date <= seven_days,
                models.VehicleSchedule.next_service_date >= today,
            )
            result = await db.execute(stmt_schedule)
            schedules = result.scalars().all()

            for schedule in schedules:
                days_left = (schedule.next_service_date - today).days
                vehicle = schedule.vehicle
                message = f"Поддръжка на {vehicle.registration_number} ( {schedule.schedule_type} ) след {days_left} дни"
                logger.info(message)

                recipients = await get_fleet_notification_recipients(db, vehicle.company_id)
                for recipient in recipients:
                    notification = models.Notification(
                        user_id=recipient.id,
                        title="Предстояща поддръжка",
                        message=message,
                        notification_type="fleet_schedule",
                        reference_id=schedule.id,
                        company_id=vehicle.company_id,
                    )
                    db.add(notification)
                    notifications_created += 1

            await db.commit()
            logger.info(f"Fleet notifications check completed. Created {notifications_created} notifications.")

        except Exception as e:
            logger.error(f"Error during fleet notifications check: {e}")
            await db.rollback()
            raise
