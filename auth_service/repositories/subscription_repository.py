from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, UUID

from models.db_models import Subscription


class SubscriptionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, sub_id: UUID):
        result = await self.session.execute(
            select(Subscription).where(Subscription.id == sub_id)
        )
        return result.scalar_one_or_none()

    async def list_for_user(self, user_id: UUID):
        result = await self.session.execute(
            select(Subscription).where(Subscription.user_id == user_id)
        )
        return result.scalars().all()

    async def create(self, **kwargs):
        sub = Subscription(**kwargs)
        self.session.add(sub)
        await self.session.flush()
        return sub

    async def update(self, subscription: Subscription, **kwargs):
        for k, v in kwargs.items():
            setattr(subscription, k, v)
        await self.session.flush()
        return subscription

    async def delete(self, subscription: Subscription):
        await self.session.delete(subscription)
