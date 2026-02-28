from datetime import datetime, timedelta

from sqlalchemy import UUID

from models.db_models import Subscription
from repositories.subscription_repository import SubscriptionRepository


class SubscriptionService:
    def __init__(self, repo: SubscriptionRepository):
        self.repo = repo

    async def assign(self, user_id: int, subscription_type: str) -> Subscription:
        # Here you can check if the user already has the subscription
        return await self.repo.create(
            user_id=user_id,
            subscription_type=subscription_type,
            started_at=datetime.utcnow(),
        )

    async def revoke(self, subscription_id: UUID):
        sub = await self.repo.get_by_id(subscription_id)
        if not sub:
            raise ValueError("Subscription not found")
        await self.repo.delete(sub)

    async def extend(self, subscription: Subscription, extra_days: int):
        if subscription.ends_at:
            subscription.ends_at += timedelta(days=extra_days)
        else:
            subscription.ends_at = datetime.utcnow() + timedelta(days=extra_days)
        await self.repo.update(subscription)
        return subscription
