"""Database operations for aliases."""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from shared.models.alias import Alias


async def create_alias(
    db: AsyncSession,
    domain_id: int,
    local_part: str,
    targets: str,
    expires_at: Optional[str] = None
) -> Alias:
    """Create a new alias."""
    alias = Alias(
        domain_id=domain_id,
        local_part=local_part,
        targets=targets,
        expires_at=expires_at,
        is_deleted=False
    )

    db.add(alias)
    await db.commit()
    await db.refresh(alias)
    return alias


async def get_alias_by_id(db: AsyncSession, alias_id: int) -> Optional[Alias]:
    """Get an alias by ID."""
    stmt = select(Alias).options(selectinload(Alias.domain)).where(
        and_(Alias.id == alias_id, Alias.is_deleted == False)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_aliases_by_domain(
    db: AsyncSession,
    domain_id: int,
    skip: int = 0,
    limit: int = 20,
    include_deleted: bool = False
) -> list[Alias]:
    """Get all aliases for a domain with pagination."""
    stmt = select(Alias).options(selectinload(Alias.domain)).where(
        Alias.domain_id == domain_id
    )

    if not include_deleted:
        stmt = stmt.where(Alias.is_deleted == False)

    stmt = stmt.offset(skip).limit(limit).order_by(Alias.created_at.desc())

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_aliases_by_organization(
    db: AsyncSession,
    organization_id: int,
    skip: int = 0,
    limit: int = 20,
    include_deleted: bool = False
) -> list[Alias]:
    """Get all aliases for an organization with pagination."""
    from shared.models.domain import Domain

    stmt = (
        select(Alias)
        .join(Domain, Alias.domain_id == Domain.id)
        .options(selectinload(Alias.domain))
        .where(Domain.organization_id == organization_id)
    )

    if not include_deleted:
        stmt = stmt.where(Alias.is_deleted == False)

    stmt = stmt.offset(skip).limit(limit).order_by(Alias.created_at.desc())

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def count_aliases_by_domain(
    db: AsyncSession,
    domain_id: int,
    include_deleted: bool = False
) -> int:
    """Count aliases for a domain."""
    stmt = select(func.count()).select_from(Alias).where(
        Alias.domain_id == domain_id
    )

    if not include_deleted:
        stmt = stmt.where(Alias.is_deleted == False)

    result = await db.execute(stmt)
    return int(result.scalar() or 0)


async def count_aliases_by_organization(
    db: AsyncSession,
    organization_id: int,
    include_deleted: bool = False
) -> int:
    """Count aliases for an organization."""
    from shared.models.domain import Domain

    stmt = (
        select(func.count())
        .select_from(Alias)
        .join(Domain, Alias.domain_id == Domain.id)
        .where(Domain.organization_id == organization_id)
    )

    if not include_deleted:
        stmt = stmt.where(Alias.is_deleted == False)

    result = await db.execute(stmt)
    return int(result.scalar() or 0)


async def update_alias(
    db: AsyncSession,
    alias_id: int,
    **updates
) -> Optional[Alias]:
    """Update an alias."""
    alias = await get_alias_by_id(db, alias_id)
    if not alias:
        return None

    for key, value in updates.items():
        if hasattr(alias, key):
            setattr(alias, key, value)

    await db.commit()
    await db.refresh(alias)
    return alias


async def delete_alias(db: AsyncSession, alias_id: int, soft_delete: bool = True) -> bool:
    """Delete an alias (soft or hard delete)."""
    alias = await get_alias_by_id(db, alias_id)
    if not alias:
        return False

    if soft_delete:
        alias.is_deleted = True
        await db.commit()
    else:
        await db.delete(alias)
        await db.commit()

    return True


async def get_alias_by_email(
    db: AsyncSession,
    local_part: str,
    domain_id: int
) -> Optional[Alias]:
    """Get an alias by email components."""
    stmt = select(Alias).options(selectinload(Alias.domain)).where(
        and_(
            Alias.local_part == local_part,
            Alias.domain_id == domain_id,
            Alias.is_deleted == False
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
