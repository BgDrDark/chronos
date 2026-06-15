from sqlalchemy import delete as sql_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import PushSubscription

from .base import BaseRepository


class PushSubscriptionRepository(BaseRepository):
    """Repository за push абонаменти"""

    model = PushSubscription

    async def get_subscriptions_by_user(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> list[PushSubscription]:
        result = await db.execute(
            select(PushSubscription).where(PushSubscription.user_id == user_id),
        )
        return list(result.scalars().all())

    async def delete_by_endpoint(
        self,
        db: AsyncSession,
        endpoint: str,
    ) -> int:
        result = await db.execute(
            sql_delete(PushSubscription).where(PushSubscription.endpoint == endpoint),
        )
        await db.flush()
        return getattr(result, "rowcount", 0)

    async def delete_by_user_and_endpoint(
        self,
        db: AsyncSession,
        user_id: int,
        endpoint: str,
    ) -> int:
        result = await db.execute(
            sql_delete(PushSubscription)
            .where(PushSubscription.user_id == user_id)
            .where(PushSubscription.endpoint == endpoint),
        )
        await db.flush()
        return getattr(result, "rowcount", 0)

    async def get_all_subscriptions(self, db: AsyncSession) -> list[PushSubscription]:
        result = await db.execute(select(PushSubscription))
        return list(result.scalars().all())


push_subscription_repo = PushSubscriptionRepository()
