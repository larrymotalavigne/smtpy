"""Database layer functions for alias operations.

All direct database interactions (session.query/add/commit) related to aliases
are defined here to enforce architecture: views -> controllers -> database.
"""

from __future__ import annotations

import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Alias


async def db_list_aliases(session: AsyncSession, domain_id: Optional[int] = None) -> List[Alias]:
    stmt = select(Alias)
    if domain_id:
        stmt = stmt.where(Alias.domain_id == domain_id)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def db_create_alias(
        session: AsyncSession, local_part: str, targets: str, domain_id: int
) -> Alias:
    alias = Alias(local_part=local_part, targets=targets, domain_id=domain_id)
    session.add(alias)
    await session.commit()
    await session.refresh(alias)
    return alias


async def db_get_alias(session: AsyncSession, alias_id: int) -> Optional[Alias]:
    return await session.get(Alias, alias_id)


async def db_delete_alias(session: AsyncSession, alias_id: int) -> bool:
    alias = await session.get(Alias, alias_id)
    if not alias:
        return False
    await session.delete(alias)
    await session.commit()
    return True


async def db_list_aliases_by_domain(session: AsyncSession, domain_id: int) -> List[Alias]:
    result = await session.execute(select(Alias).where(Alias.domain_id == domain_id))
    return list(result.scalars().all())


async def db_add_alias(
        session: AsyncSession,
        domain_id: int,
        local_part: str,
        targets: str,
        expires_at: Optional[datetime.datetime] = None,
) -> Alias:
    alias = Alias(
        local_part=local_part,
        targets=targets,
        domain_id=domain_id,
        expires_at=expires_at,
    )
    session.add(alias)
    await session.commit()
    await session.refresh(alias)
    return alias
