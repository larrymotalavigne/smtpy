"""Domain controller for SMTPy v2."""

import secrets
import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from shared.models.domain import Domain, DomainStatus
from shared.models.message import Message, MessageStatus
from ..database import domains_database
from ..schemas.common import PaginatedResponse
from ..schemas.domain import (
    DomainCreate,
    DomainResponse,
    DomainList,
    DomainVerificationResponse,
    DNSVerificationStatus,
    DNSRecords,
    DomainStats
)
from ..services.dns_service import DNSService
from ..services.dkim_service import DKIMService

logger = logging.getLogger(__name__)


async def create_domain(
    db: AsyncSession,
    domain_data: DomainCreate,
    organization_id: int
) -> DomainResponse:
    """Create a new domain with DKIM keys."""
    # Check if domain already exists
    existing_domain = await domains_database.get_domain_by_name(db, domain_data.name)
    if existing_domain:
        raise ValueError(f"Domain {domain_data.name} already exists")

    # Generate verification token
    verification_token = secrets.token_urlsafe(32)

    # Generate DKIM keypair
    logger.info(f"Generating DKIM keys for domain: {domain_data.name}")
    try:
        dkim_service = DKIMService()
        private_key_pem, public_key_base64 = dkim_service.generate_dkim_keypair(key_size=2048)
        dkim_selector = dkim_service.get_dkim_selector()

        logger.info(f"DKIM keys generated successfully for {domain_data.name}")
    except Exception as e:
        logger.error(f"Failed to generate DKIM keys for {domain_data.name}: {e}")
        # Continue without DKIM keys rather than failing domain creation
        private_key_pem = None
        public_key_base64 = None
        dkim_selector = "default"

    # Create domain with DKIM keys
    domain = await domains_database.create_domain(
        db=db,
        name=domain_data.name,
        organization_id=organization_id,
        verification_token=verification_token,
        dkim_public_key=public_key_base64,
        dkim_private_key=private_key_pem,
        dkim_selector=dkim_selector
    )

    return DomainResponse.model_validate(domain)


async def get_domain(db: AsyncSession, domain_id: int, organization_id: int) -> Optional[DomainResponse]:
    """Get a domain by ID for a specific organization."""
    domain = await domains_database.get_domain_by_id(db, domain_id)
    
    if not domain or domain.organization_id != organization_id:
        return None
    
    return DomainResponse.model_validate(domain)


async def list_domains(
    db: AsyncSession,
    organization_id: int,
    page: int = 1,
    page_size: int = 20
) -> PaginatedResponse:
    """List domains for an organization with pagination."""
    skip = (page - 1) * page_size
    
    # Get domains and total count
    domains = await domains_database.get_domains_by_organization(
        db=db,
        organization_id=organization_id,
        skip=skip,
        limit=page_size
    )
    total = await domains_database.count_domains_by_organization(db, organization_id)
    
    # Convert to response schemas
    domain_responses = [DomainList.model_validate(domain) for domain in domains]
    
    return PaginatedResponse.create(
        items=domain_responses,
        total=total,
        page=page,
        page_size=page_size
    )


async def update_domain(
    db: AsyncSession,
    domain_id: int,
    organization_id: int,
    is_active: Optional[bool] = None
) -> Optional[DomainResponse]:
    """Update domain settings."""
    # Check if domain exists and belongs to organization
    domain = await domains_database.get_domain_by_id(db, domain_id)
    if not domain or domain.organization_id != organization_id:
        return None
    
    # Prepare updates
    updates = {}
    if is_active is not None:
        updates["is_active"] = is_active
    
    if not updates:
        return DomainResponse.model_validate(domain)
    
    # Update domain
    updated_domain = await domains_database.update_domain(db, domain_id, **updates)
    if not updated_domain:
        return None
    
    return DomainResponse.model_validate(updated_domain)


async def delete_domain(db: AsyncSession, domain_id: int, organization_id: int) -> bool:
    """Delete a domain."""
    # Check if domain exists and belongs to organization
    domain = await domains_database.get_domain_by_id(db, domain_id)
    if not domain or domain.organization_id != organization_id:
        return False
    
    return await domains_database.delete_domain(db, domain_id)


async def verify_domain(
    db: AsyncSession,
    domain_id: int,
    organization_id: int,
    dns_service: Optional[DNSService] = None
) -> Optional[DomainVerificationResponse]:
    """Verify domain DNS records using real DNS lookups."""
    # Check if domain exists and belongs to organization
    domain = await domains_database.get_domain_by_id(db, domain_id)
    if not domain or domain.organization_id != organization_id:
        return None

    # Initialize DNS service if not provided
    if dns_service is None:
        dns_service = DNSService(timeout=10.0)

    logger.info(f"Starting DNS verification for domain: {domain.name}")

    # Perform real DNS verification
    verification_results = dns_service.verify_all(
        domain=domain.name,
        expected_mx="smtp.smtpy.fr",
        expected_spf_include="smtpy.fr",
        dkim_selector="default"
    )

    mx_verified = verification_results["mx_verified"]
    spf_verified = verification_results["spf_verified"]
    dkim_verified = verification_results["dkim_verified"]
    dmarc_verified = verification_results["dmarc_verified"]

    logger.info(
        f"DNS verification results for {domain.name}: "
        f"MX={mx_verified}, SPF={spf_verified}, "
        f"DKIM={dkim_verified}, DMARC={dmarc_verified}"
    )

    # Update verification status in database
    updated_domain = await domains_database.update_dns_verification(
        db=db,
        domain_id=domain_id,
        mx_verified=mx_verified,
        spf_verified=spf_verified,
        dkim_verified=dkim_verified,
        dmarc_verified=dmarc_verified
    )

    if not updated_domain:
        return None

    dns_status = DNSVerificationStatus(
        mx_record_verified=updated_domain.mx_record_verified,
        spf_record_verified=updated_domain.spf_record_verified,
        dkim_record_verified=updated_domain.dkim_record_verified,
        dmarc_record_verified=updated_domain.dmarc_record_verified,
        is_fully_verified=updated_domain.is_fully_verified
    )

    success = updated_domain.is_fully_verified

    # Build detailed message based on verification results
    if success:
        message = "Domain fully verified! All DNS records are configured correctly."
    else:
        failed_records = []
        if not mx_verified:
            failed_records.append("MX record")
        if not spf_verified:
            failed_records.append("SPF record")
        if not dkim_verified:
            failed_records.append("DKIM record")
        if not dmarc_verified:
            failed_records.append("DMARC record")

        message = f"DNS verification incomplete. Missing or incorrect: {', '.join(failed_records)}. Please check your DNS configuration."

    return DomainVerificationResponse(
        success=success,
        message=message,
        dns_status=dns_status
    )


async def get_dns_records(
    db: AsyncSession,
    domain_id: int,
    organization_id: int
) -> Optional[DNSRecords]:
    """Get required DNS records for domain setup."""
    # Check if domain exists and belongs to organization
    domain = await domains_database.get_domain_by_id(db, domain_id)
    if not domain or domain.organization_id != organization_id:
        return None
    
    # Generate required DNS records
    # Production configuration for smtpy.fr
    # Note: Trailing dot prevents DNS providers from appending the domain
    mx_record = f"10 smtp.smtpy.fr."
    spf_record = f"v=spf1 include:smtpy.fr ~all"
    dkim_record = f"v=DKIM1; k=rsa; p={domain.dkim_public_key or 'YOUR_DKIM_PUBLIC_KEY'}"
    dmarc_record = f"v=DMARC1; p=quarantine; rua=mailto:dmarc@{domain.name}"
    verification_record = f"smtpy-verification={domain.verification_token}" if domain.verification_token else None
    
    return DNSRecords(
        mx_record=mx_record,
        spf_record=spf_record,
        dkim_record=dkim_record,
        dmarc_record=dmarc_record,
        verification_record=verification_record
    )


async def get_active_domains_for_organization(
    db: AsyncSession,
    organization_id: int
) -> list[DomainResponse]:
    """Get all active verified domains for an organization."""
    domains = await domains_database.get_active_domains_by_organization(db, organization_id)
    return [DomainResponse.model_validate(domain) for domain in domains]


async def get_domain_stats(
    db: AsyncSession,
    domain_id: int,
    organization_id: int
) -> Optional[DomainStats]:
    """Compute statistics for a given domain.
    Returns None if the domain does not exist or does not belong to the organization.
    """
    # Validate domain ownership
    domain = await domains_database.get_domain_by_id(db, domain_id)
    if not domain or domain.organization_id != organization_id:
        return None

    # Messages received (all statuses count) for this domain
    total_messages_stmt = select(func.count()).select_from(Message).where(Message.domain_id == domain_id)
    result = await db.execute(total_messages_stmt)
    messages_received = int(result.scalar() or 0)

    # Messages forwarded = delivered
    delivered_stmt = (
        select(func.count())
        .select_from(Message)
        .where(
            (Message.domain_id == domain_id) & (Message.status == MessageStatus.DELIVERED)
        )
    )
    result = await db.execute(delivered_stmt)
    messages_forwarded = int(result.scalar() or 0)

    # Last message at (max created_at)
    last_msg_stmt = select(func.max(Message.created_at)).where(Message.domain_id == domain_id)
    result = await db.execute(last_msg_stmt)
    last_message_dt = result.scalar()
    last_message_at = last_message_dt.isoformat() if last_message_dt else None

    # Alias counts – no Alias model detected, default to 0 for now
    total_aliases = 0
    active_aliases = 0

    return DomainStats(
        total_aliases=total_aliases,
        active_aliases=active_aliases,
        messages_received=messages_received,
        messages_forwarded=messages_forwarded,
        last_message_at=last_message_at,
    )