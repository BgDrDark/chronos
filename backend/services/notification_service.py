import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from backend.crud.repositories import (
    notification_repo,
    push_subscription_repo,
    settings_repo,
)
from backend.database.models import Notification, PushSubscription


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.notification_repo = notification_repo
        self.push_repo = push_subscription_repo
        self.settings_repo = settings_repo

    async def subscribe(
        self,
        user_id: int,
        endpoint: str,
        p256dh: str,
        auth: str,
    ) -> PushSubscription:
        """Subscribe user to push notifications"""
        if not endpoint or not p256dh or not auth:
            raise ValueError("Invalid subscription data")

        await self.push_repo.delete_by_endpoint(self.db, endpoint)

        new_sub = await self.push_repo.create(
            self.db,
            user_id=user_id,
            endpoint=endpoint,
            p256dh=p256dh,
            auth=auth,
        )
        await self.db.commit()
        return new_sub

    async def create_notification(
        self,
        user_id: int,
        message: str,
    ) -> Notification:
        """Create an in-app notification"""
        return await self.notification_repo.create(self.db, user_id=user_id, message=message)

    async def get_notifications(
        self,
        user_id: int,
        limit: int = 50,
        unread_only: bool = False,
        offset: int = 0,
    ) -> list[Notification]:
        """Get notifications for a user"""
        return await self.notification_repo.get_user_notifications(self.db, user_id, limit, unread_only, offset)

    async def get_count(self, user_id: int) -> int:
        """Get total notification count for a user"""
        return await self.notification_repo.get_notifications_count(self.db, user_id)

    async def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        """Mark a notification as read"""
        success = await self.notification_repo.mark_as_read(self.db, notification_id, user_id)
        if success:
            await self.db.commit()
        return success

    async def mark_all_as_read(self, user_id: int) -> int:
        """Mark all notifications as read for a user"""
        count = await self.notification_repo.mark_all_as_read(self.db, user_id)
        if count > 0:
            await self.db.commit()
        return count

    async def delete_notification(self, notification_id: int, user_id: int) -> bool:
        """Delete a notification"""
        success = await self.notification_repo.delete_user_notification(self.db, notification_id, user_id)
        if success:
            await self.db.commit()
        return success

    async def get_unread_count(self, user_id: int) -> int:
        """Get count of unread notifications"""
        return await self.notification_repo.get_unread_count(self.db, user_id)

    async def unsubscribe(
        self,
        user_id: int,
        endpoint: str,
    ) -> bool:
        """Unsubscribe from push notifications"""
        deleted = await self.push_repo.delete_by_user_and_endpoint(self.db, user_id, endpoint)
        await self.db.commit()
        return deleted > 0

    async def send(
        self,
        user_id: int,
        title: str,
        body: str,
        icon: str = "/pwa-192x192.png",
        url: str = "/",
    ) -> int:
        """Send push notification to user. Returns number of sent notifications."""
        from pywebpush import WebPushException, webpush

        vapid_private = await self._get_setting("vapid_private_key")
        vapid_email = await self._get_setting("mail_from") or "admin@chronos.local"

        if not vapid_private:
            print("Push failed: No VAPID private key")
            return 0

        subs = await self.push_repo.get_subscriptions_by_user(self.db, user_id)

        if not subs:
            return 0

        payload = {
            "notification": {
                "title": title,
                "body": body,
                "icon": icon,
                "data": {"url": url},
            },
        }

        sent = 0
        for sub in subs:
            try:
                webpush(
                    subscription_info={
                        "endpoint": sub.endpoint,
                        "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
                    },
                    data=json.dumps(payload),
                    vapid_private_key=vapid_private,
                    vapid_claims={"sub": f"mailto:{vapid_email}"},
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
        user_ids: list[int],
        title: str,
        body: str,
        icon: str = "/pwa-192x192.png",
        url: str = "/",
    ) -> int:
        """Send push to multiple users. Returns total sent."""
        total = 0
        for user_id in user_ids:
            try:
                sent = await self.send(user_id, title, body, icon, url)
                total += sent
            except Exception as e:
                logger.error(f"Push to user {user_id} failed: {e}")
        return total

    async def broadcast(
        self,
        title: str,
        body: str,
        icon: str = "/pwa-192x192.png",
        url: str = "/",
    ) -> int:
        """Send push to all subscribed users. Returns total sent."""
        all_subs = await self.push_repo.get_all_subscriptions(self.db)

        if not all_subs:
            return 0

        sent = 0
        for sub in all_subs:
            try:
                count = await self.send(
                    user_id=sub.user_id,
                    title=title,
                    body=body,
                    icon=icon,
                    url=url,
                )
                sent += count
            except Exception as e:
                logger.error(f"Broadcast push failed for user {sub.user_id}: {e}")

        return sent

    async def get_subscriptions(
        self,
        user_id: int,
    ) -> list[PushSubscription]:
        """Get all subscriptions for user"""
        return await self.push_repo.get_subscriptions_by_user(self.db, user_id)

    async def _get_setting(self, key: str) -> str | None:
        return await self.settings_repo.get_setting(self.db, key)


notification_service = NotificationService
