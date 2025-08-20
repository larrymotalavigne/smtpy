"""Database layer functions for user and invitation operations.

All direct database interactions (session.query/add/commit) related to users
and invitations are defined here to enforce architecture: views -> controllers -> database.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.models import User, Invitation


# User queries


async def db_get_active_user_by_username(session: AsyncSession, username: str) -> Optional[User]:
    # get_active_users returns a Query; rewrite with select
    result = await session.execute(
        select(User).where(User.is_deleted == False, User.username == username)
    )
    return result.scalars().first()


async def db_get_active_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
    result = await session.execute(
        select(User).where(User.is_deleted == False, User.email == email)
    )
    return result.scalars().first()


async def db_get_user_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
    return await session.get(User, user_id)


async def db_get_user_by_verification_token(session: AsyncSession, token: str) -> Optional[User]:
    result = await session.execute(
        select(User).where(User.is_deleted == False, User.verification_token == token)
    )
    return result.scalars().first()


async def db_set_user_verified(session: AsyncSession, user: User) -> None:
    user.is_active = True
    user.email_verified = True
    user.verification_token = None
    await session.commit()


async def db_update_user_fields(session: AsyncSession, user: User, **kwargs) -> User:
    for key, value in kwargs.items():
        if hasattr(user, key):
            setattr(user, key, value)
    await session.commit()
    await session.refresh(user)
    return user


# Invitation queries


async def db_get_invitation_by_email(session: AsyncSession, email: str) -> Optional[Invitation]:
    result = await session.execute(select(Invitation).where(Invitation.email == email))
    return result.scalars().first()


async def db_get_invitation_by_token(session: AsyncSession, token: str) -> Optional[Invitation]:
    result = await session.execute(select(Invitation).where(Invitation.token == token))
    return result.scalars().first()


async def db_create_invitation(
        session: AsyncSession, email: str, token: str, expires_at: datetime, invited_by: Optional[int]
) -> Invitation:
    invitation = Invitation(email=email, token=token, expires_at=expires_at, invited_by=invited_by)
    session.add(invitation)
    await session.commit()
    await session.refresh(invitation)
    return invitation


async def db_delete_invitation(session: AsyncSession, invitation: Invitation) -> None:
    await session.delete(invitation)
    await session.commit()


# --- Additional creation helpers for users ---
async def db_create_user(
        session: AsyncSession,
        username: str,
        hashed_password: str,
        email: Optional[str] = None,
        role: str = "user",
        is_active: bool = False,
        email_verified: bool = False,
        verification_token: Optional[str] = None,
        invited_by: Optional[int] = None,
) -> User:
    user = User(
        username=username,
        hashed_password=hashed_password,
        email=email,
        role=role,
        is_active=is_active,
        email_verified=email_verified,
        verification_token=verification_token,
        invited_by=invited_by,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
