"""Alias controller for SMTPy v2."""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import aliases_database, domains_database
from ..schemas.common import PaginatedResponse
from ..schemas.alias import AliasCreate, AliasUpdate, AliasResponse, AliasListItem


async def create_alias(
    db: AsyncSession,
    alias_data: AliasCreate,
    organization_id: int
) -> Optional[AliasResponse]:
    """Create a new alias."""
    # Verify domain belongs to organization
    domain = await domains_database.get_domain_by_id(db, alias_data.domain_id)
    if not domain or domain.organization_id != organization_id:
        raise ValueError("Domain not found or does not belong to organization")

    # Check if alias already exists
    existing = await aliases_database.get_alias_by_email(
        db, alias_data.local_part, alias_data.domain_id
    )
    if existing:
        raise ValueError(f"Alias {alias_data.local_part}@{domain.name} already exists")

    # Convert target list to comma-separated string
    targets_str = ','.join(alias_data.targets)

    # Create alias
    alias = await aliases_database.create_alias(
        db=db,
        domain_id=alias_data.domain_id,
        local_part=alias_data.local_part,
        targets=targets_str,
        expires_at=alias_data.expires_at
    )

    return AliasResponse.model_validate(alias)


async def get_alias(
    db: AsyncSession,
    alias_id: int,
    organization_id: int
) -> Optional[AliasResponse]:
    """Get an alias by ID."""
    alias = await aliases_database.get_alias_by_id(db, alias_id)

    if not alias:
        return None

    # Verify domain belongs to organization
    if alias.domain.organization_id != organization_id:
        return None

    return AliasResponse.model_validate(alias)


async def list_aliases(
    db: AsyncSession,
    organization_id: int,
    domain_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 20
) -> PaginatedResponse:
    """List aliases for an organization with optional domain filter."""
    skip = (page - 1) * page_size

    if domain_id:
        # Verify domain belongs to organization
        domain = await domains_database.get_domain_by_id(db, domain_id)
        if not domain or domain.organization_id != organization_id:
            raise ValueError("Domain not found or does not belong to organization")

        # Get aliases for specific domain
        aliases = await aliases_database.get_aliases_by_domain(
            db=db,
            domain_id=domain_id,
            skip=skip,
            limit=page_size
        )
        total = await aliases_database.count_aliases_by_domain(db, domain_id)
    else:
        # Get all aliases for organization
        aliases = await aliases_database.get_aliases_by_organization(
            db=db,
            organization_id=organization_id,
            skip=skip,
            limit=page_size
        )
        total = await aliases_database.count_aliases_by_organization(db, organization_id)

    # Convert to list items
    alias_items = [AliasListItem.model_validate(alias) for alias in aliases]

    return PaginatedResponse.create(
        items=alias_items,
        total=total,
        page=page,
        page_size=page_size
    )


async def update_alias(
    db: AsyncSession,
    alias_id: int,
    organization_id: int,
    alias_update: AliasUpdate
) -> Optional[AliasResponse]:
    """Update an alias."""
    # Get alias and verify ownership
    alias = await aliases_database.get_alias_by_id(db, alias_id)
    if not alias:
        return None

    if alias.domain.organization_id != organization_id:
        return None

    # Prepare updates
    updates = {}
    if alias_update.targets is not None:
        updates["targets"] = ','.join(alias_update.targets)
    if alias_update.expires_at is not None:
        updates["expires_at"] = alias_update.expires_at
    if alias_update.is_deleted is not None:
        updates["is_deleted"] = alias_update.is_deleted

    if not updates:
        return AliasResponse.model_validate(alias)

    # Update alias
    updated_alias = await aliases_database.update_alias(db, alias_id, **updates)
    if not updated_alias:
        return None

    return AliasResponse.model_validate(updated_alias)


async def delete_alias(
    db: AsyncSession,
    alias_id: int,
    organization_id: int,
    soft_delete: bool = True
) -> bool:
    """Delete an alias."""
    # Get alias and verify ownership
    alias = await aliases_database.get_alias_by_id(db, alias_id)
    if not alias:
        return False

    if alias.domain.organization_id != organization_id:
        return False

    return await aliases_database.delete_alias(db, alias_id, soft_delete=soft_delete)
