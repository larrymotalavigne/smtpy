"""Database layer functions for domain operations.

All direct database interactions (session.query/add/commit) related to domains
are defined here to enforce architecture: views -> controllers -> database.
"""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.functions import count

from .models import Domain, User


async def db_get_domain_by_id(session: AsyncSession, domain_id: int) -> Optional[Domain]:
    return await session.get(Domain, domain_id)


async def db_get_user_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
    return await session.get(User, user_id)


async def db_get_active_domain_by_name(session: AsyncSession, name: str) -> Optional[Domain]:
    result = await session.execute(
        select(Domain).where(Domain.is_deleted == False, Domain.name == name)
    )
    return result.scalars().first()


async def db_list_user_domains(
        session: AsyncSession, user_id: Optional[int] = None, include_aliases: bool = False
) -> List[Domain]:
    stmt = select(Domain).where(Domain.is_deleted == False)
    if user_id is not None:
        stmt = stmt.where(Domain.owner_id == user_id)
    if include_aliases:
        stmt = stmt.options(selectinload(Domain.aliases))
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def db_list_all_domains(session: AsyncSession, include_aliases: bool = False) -> List[Domain]:
    stmt = select(Domain).where(Domain.is_deleted == False)
    if include_aliases:
        stmt = stmt.options(selectinload(Domain.aliases))
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def db_create_domain(
        session: AsyncSession, name: str, owner_id: int, catch_all: Optional[str] = None
) -> Domain:
    domain = Domain(name=name, owner_id=owner_id, catch_all=catch_all)
    session.add(domain)
    await session.commit()
    await session.refresh(domain)
    return domain


async def db_delete_domain(session: AsyncSession, domain_id: int) -> bool:
    domain = await session.get(Domain, domain_id)
    if not domain:
        return False
    await session.delete(domain)
    await session.commit()
    return True


async def db_update_domain_fields(session: AsyncSession, domain: Domain, **kwargs) -> Domain:
    for key, value in kwargs.items():
        if hasattr(domain, key):
            setattr(domain, key, value)
    await session.commit()
    await session.refresh(domain)
    return domain


async def get_domain_count(db: AsyncSession):
    return await db.execute(select(count(Domain)))
