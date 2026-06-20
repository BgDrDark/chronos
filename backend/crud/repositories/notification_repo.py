
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import Notification

from .base import BaseRepository


class NotificationRepository(BaseRepository):
    """Repository за уведомления"""

    model = Notification

    async def get_user_notifications(
        self,
        db: AsyncSession,
        user_id: int,
        limit: int = 50,
        unread_only: bool = False,
        offset: int = 0,
    ) -> list[Notification]:
        query = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            query = query.where(~Notification.is_read)
        query = query.order_by(Notification.created_at.desc()).offset(offset).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_notifications_count(self, db: AsyncSession, user_id: int) -> int:
        result = await db.execute(
            select(func.count(Notification.id)).where(Notification.user_id == user_id),
        )
        return result.scalar() or 0

    async def get_user_notification(
        self,
        db: AsyncSession,
        notification_id: int,
        user_id: int,
    ) -> Notification | None:
        result = await db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            ),
        )
        return result.scalar_one_or_none()

    async def mark_as_read(
        self,
        db: AsyncSession,
        notification_id: int,
        user_id: int,
    ) -> bool:
        notification = await self.get_user_notification(db, notification_id, user_id)
        if not notification:
            return False
        notification.is_read = True
        await db.flush()
        return True

    async def mark_all_as_read(self, db: AsyncSession, user_id: int) -> int:
        result = await db.execute(
            select(Notification).where(
                Notification.user_id == user_id,
                ~Notification.is_read,
            ),
        )
        notifications = result.scalars().all()
        count = 0
        for notification in notifications:
            notification.is_read = True
            count += 1
        if count > 0:
            await db.flush()
        return count

    async def get_unread_count(self, db: AsyncSession, user_id: int) -> int:
        result = await db.execute(
            select(func.count(Notification.id)).where(
                Notification.user_id == user_id,
                ~Notification.is_read,
            ),
        )
        return result.scalar() or 0

    async def delete_user_notification(
        self,
        db: AsyncSession,
        notification_id: int,
        user_id: int,
    ) -> bool:
        notification = await self.get_user_notification(db, notification_id, user_id)
        if not notification:
            return False
        await db.delete(notification)
        await db.flush()
        return True


notification_repo = NotificationRepository()
