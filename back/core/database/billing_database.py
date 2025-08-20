"""Database layer functions for billing-related operations.

All direct database interactions (session.query/add/commit) related to billing
(user Stripe fields) are defined here to enforce architecture: views -> controllers -> database.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.models import User


async def db_get_user_by_stripe_customer_id(
        session: AsyncSession, customer_id: str
) -> Optional[User]:
    result = await session.execute(select(User).where(User.stripe_customer_id == customer_id))
    return result.scalars().first()


async def db_set_user_stripe_customer_id(
        session: AsyncSession, user: User, customer_id: str
) -> None:
    user.stripe_customer_id = customer_id
    await session.commit()


async def db_update_user_subscription_status(
        session: AsyncSession, user: User, status: str
) -> None:
    user.subscription_status = status
    await session.commit()
