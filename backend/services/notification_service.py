from typing import Optional, List
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete as sql_delete

from backend.database.models import PushSubscription, GlobalSetting, Notification


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def subscribe(
        self,
        user_id: int,
        endpoint: str,
        p256dh: str,
        auth: str
    ) -> PushSubscription:
        """Subscribe user to push notifications"""
        if not endpoint or not p256dh or not auth:
            raise ValueError("Invalid subscription data")

        await self.db.execute(
            sql_delete(PushSubscription).where(PushSubscription.endpoint == endpoint)
        )

        new_sub = PushSubscription(
            user_id=user_id,
            endpoint=endpoint,
            p256dh=p256dh,
            auth=auth
        )
        self.db.add(new_sub)
        await self.db.commit()
        await self.db.refresh(new_sub)
        return new_sub

    async def create_notification(
        self,
        user_id: int,
        message: str
    ) -> Notification:
        """Create an in-app notification"""
        notification = Notification(user_id=user_id, message=message)
        self.db.add(notification)
        await self.db.flush()
        return notification

    async def get_notifications(
        self,
        user_id: int,
        limit: int = 50,
        unread_only: bool = False
    ) -> List[Notification]:
        """Get notifications for a user"""
        stmt = select(Notification).where(Notification.user_id == user_id)
        
        if unread_only:
            stmt = stmt.where(Notification.is_read == False)
        
        stmt = stmt.order_by(Notification.created_at.desc()).limit(limit)
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        """Mark a notification as read"""
        stmt = select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id
        )
        result = await self.db.execute(stmt)
        notification = result.scalars().first()
        
        if notification:
            notification.is_read = True
            self.db.add(notification)
            await self.db.commit()
            return True
        
        return False

    async def mark_all_as_read(self, user_id: int) -> int:
        """Mark all notifications as read for a user"""
        stmt = select(Notification).where(
            Notification.user_id == user_id,
            Notification.is_read == False
        )
        result = await self.db.execute(stmt)
        notifications = result.scalars().all()
        
        count = 0
        for notification in notifications:
            notification.is_read = True
            self.db.add(notification)
            count += 1
        
        if count > 0:
            await self.db.commit()
        
        return count

    async def delete_notification(self, notification_id: int, user_id: int) -> bool:
        """Delete a notification"""
        stmt = select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id
        )
        result = await self.db.execute(stmt)
        notification = result.scalars().first()
        
        if notification:
            await self.db.delete(notification)
            await self.db.commit()
            return True
        
        return False

    async def get_unread_count(self, user_id: int) -> int:
        """Get count of unread notifications"""
        from sqlalchemy import func
        
        stmt = select(func.count(Notification.id)).where(
            Notification.user_id == user_id,
            Notification.is_read == False
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def unsubscribe(
        self,
        user_id: int,
        endpoint: str
    ) -> bool:
        """Unsubscribe from push notifications"""
        result = await self.db.execute(
            sql_delete(PushSubscription)
            .where(PushSubscription.user_id == user_id)
            .where(PushSubscription.endpoint == endpoint)
        )
        await self.db.commit()
        return result.rowcount > 0

    async def send(
        self,
        user_id: int,
        title: str,
        body: str,
        icon: str = "/pwa-192x192.png",
        url: str = "/"
    ) -> int:
        """Send push notification to user. Returns number of sent notifications."""
        from pywebpush import webpush, WebPushException

        vapid_private = await self._get_setting("vapid_private_key")
        vapid_email = await self._get_setting("mail_from") or "admin@chronos.local"

        if not vapid_private:
            print("Push failed: No VAPID private key")
            return 0

        stmt = select(PushSubscription).where(PushSubscription.user_id == user_id)
        result = await self.db.execute(stmt)
        subs = result.scalars().all()

        if not subs:
            return 0

        payload = {
            "notification": {
                "title": title,
                "body": body,
                "icon": icon,
                "data": {"url": url}
            }
        }

        sent = 0
        for sub in subs:
            try:
                webpush(
                    subscription_info={
                        "endpoint": sub.endpoint,
                        "keys": {"p256dh": sub.p256dh, "auth": sub.auth}
                    },
                    data=json.dumps(payload),
                    vapid_private_key=vapid_private,
                    vapid_claims={"sub": f"mailto:{vapid_email}"}
                )
                sent += 1
            except WebPushException as ex:
                print(f"Push failed for {sub.endpoint}: {ex}")
                if "410" in str(ex) or "404" in str(ex):
                    await self.db.delete(sub)
                    await self.db.commit()

        return sent

    async def send_multiple(
        self,
        user_ids: List[int],
        title: str,
        body: str,
        icon: str = "/pwa-192x192.png",
        url: str = "/"
    ) -> int:
        """Send push to multiple users. Returns total sent."""
        total = 0
        for user_id in user_ids:
            try:
                sent = await self.send(user_id, title, body, icon, url)
                total += sent
            except Exception as e:
                print(f"Push to user {user_id} failed: {e}")
        return total

    async def broadcast(
        self,
        title: str,
        body: str,
        icon: str = "/pwa-192x192.png",
        url: str = "/"
    ) -> int:
        """Send push to all subscribed users."""
        from backend.database.models import User, PushSubscription
        from sqlalchemy import func

        stmt = select(func.count(PushSubscription.id))
        result = await self.db.execute(stmt)
        total_subs = result.scalar() or 0

        if total_subs == 0:
            return 0

        return total_subs

    async def get_subscriptions(
        self,
        user_id: int
    ) -> List[PushSubscription]:
        """Get all subscriptions for user"""
        stmt = select(PushSubscription).where(PushSubscription.user_id == user_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def _get_setting(self, key: str) -> Optional[str]:
        """Get global setting value"""
        stmt = select(GlobalSetting).where(GlobalSetting.key == key)
        result = await self.db.execute(stmt)
        setting = result.scalars().first()
        return setting.value if setting else None


notification_service = NotificationService