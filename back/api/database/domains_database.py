"""Domain database operations for SMTPy v2."""

from typing import Optional

from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.models.domain import Domain, DomainStatus


async def create_domain(
    db: AsyncSession,
    name: str,
    organization_id: int,
    verification_token: Optional[str] = None,
    dkim_public_key: Optional[str] = None,
    dkim_private_key: Optional[str] = None,
    dkim_selector: Optional[str] = "default"
) -> Domain:
    """Create a new domain with optional DKIM keys."""
    domain = Domain(
        name=name.lower().strip(),
        organization_id=organization_id,
        verification_token=verification_token,
        dkim_public_key=dkim_public_key,
        dkim_private_key=dkim_private_key,
        dkim_selector=dkim_selector,
        status=DomainStatus.PENDING
    )
    db.add(domain)
    await db.commit()
    await db.refresh(domain)
    return domain


async def get_domain_by_id(db: AsyncSession, domain_id: int) -> Optional[Domain]:
    """Get domain by ID."""
    stmt = (
        select(Domain)
        .options(selectinload(Domain.organization))
        .where(Domain.id == domain_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_domain_by_name(db: AsyncSession, name: str) -> Optional[Domain]:
    """Get domain by name."""
    stmt = (
        select(Domain)
        .options(selectinload(Domain.organization))
        .where(Domain.name == name.lower().strip())
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_domains_by_organization(
    db: AsyncSession, 
    organization_id: int,
    skip: int = 0,
    limit: int = 20
) -> list[Domain]:
    """Get domains for an organization with pagination."""
    stmt = (
        select(Domain)
        .where(Domain.organization_id == organization_id)
        .order_by(Domain.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def count_domains_by_organization(db: AsyncSession, organization_id: int) -> int:
    """Count total domains for an organization."""
    stmt = (
        select(func.count(Domain.id))
        .where(Domain.organization_id == organization_id)
    )
    result = await db.execute(stmt)
    return result.scalar() or 0


async def update_domain(
    db: AsyncSession, 
    domain_id: int, 
    **updates
) -> Optional[Domain]:
    """Update domain fields."""
    stmt = (
        update(Domain)
        .where(Domain.id == domain_id)
        .values(**updates)
        .returning(Domain)
    )
    result = await db.execute(stmt)
    await db.commit()
    updated_domain = result.scalar_one_or_none()
    if updated_domain:
        await db.refresh(updated_domain)
    return updated_domain


async def update_dns_verification(
    db: AsyncSession,
    domain_id: int,
    mx_verified: Optional[bool] = None,
    spf_verified: Optional[bool] = None,
    dkim_verified: Optional[bool] = None,
    dmarc_verified: Optional[bool] = None
) -> Optional[Domain]:
    """Update DNS verification status for a domain."""
    updates = {}
    if mx_verified is not None:
        updates["mx_record_verified"] = mx_verified
    if spf_verified is not None:
        updates["spf_record_verified"] = spf_verified
    if dkim_verified is not None:
        updates["dkim_record_verified"] = dkim_verified
    if dmarc_verified is not None:
        updates["dmarc_record_verified"] = dmarc_verified
    
    if not updates:
        return await get_domain_by_id(db, domain_id)
    
    # Check if all records are verified to update status
    domain = await get_domain_by_id(db, domain_id)
    if domain:
        all_verified = (
            updates.get("mx_record_verified", domain.mx_record_verified) and
            updates.get("spf_record_verified", domain.spf_record_verified) and
            updates.get("dkim_record_verified", domain.dkim_record_verified) and
            updates.get("dmarc_record_verified", domain.dmarc_record_verified)
        )
        if all_verified:
            updates["status"] = DomainStatus.VERIFIED
    
    return await update_domain(db, domain_id, **updates)


async def delete_domain(db: AsyncSession, domain_id: int) -> bool:
    """Delete a domain."""
    stmt = delete(Domain).where(Domain.id == domain_id)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0


async def get_domains_by_status(
    db: AsyncSession, 
    status: DomainStatus,
    organization_id: Optional[int] = None
) -> list[Domain]:
    """Get domains by verification status."""
    stmt = select(Domain).where(Domain.status == status)
    if organization_id:
        stmt = stmt.where(Domain.organization_id == organization_id)
    
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_active_domains_by_organization(
    db: AsyncSession, 
    organization_id: int
) -> list[Domain]:
    """Get active domains for an organization."""
    stmt = (
        select(Domain)
        .where(
            Domain.organization_id == organization_id,
            Domain.is_active == True,
            Domain.status == DomainStatus.VERIFIED
        )
        .order_by(Domain.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())