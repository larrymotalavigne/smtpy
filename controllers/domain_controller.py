"""Domain controller for domain management operations."""

from datetime import datetime
from typing import List, Optional, Dict, Any

from database import domain_database
from database.models import Domain
from utils.db import get_db
from utils.logging_config import get_logger

logger = get_logger("domain_controller")


def log_activity(event_type: str, details: Dict[str, Any]) -> None:
    """Log activity to the database."""
    try:
        with get_db() as session:
            activity_log = ActivityLog(
                event_type=event_type,
                timestamp=datetime.utcnow(),
                details=str(details),
                status="success"
            )
            session.add(activity_log)
            session.commit()
    except Exception as e:
        logger.error(f"Failed to log activity: {e}")


def get_by_id_or_404(session, model_class, record_id: int):
    """Get a record by ID or raise an error if not found."""
    record = session.get(model_class, record_id)
    if not record:
        raise ResourceNotFoundError(f"{model_class.__name__} with id {record_id} not found")
    return record


def validate_ownership(record, user_id: int, user_role: str = "user") -> None:
    """Validate that a user owns a record or is an admin."""
    if user_role != "admin" and getattr(record, 'owner_id', None) != user_id:
        raise PermissionError("Access denied: insufficient permissions")


def create_domain_record(session, **domain_data) -> Domain:
    """Create a new domain record in the database."""
    domain = Domain(**domain_data)
    session.add(domain)
    session.commit()
    session.refresh(domain)
    return domain


def update_domain_record(session, domain, **kwargs):
    """Update a domain record with the given fields."""
    for key, value in kwargs.items():
        if hasattr(domain, key):
            setattr(domain, key, value)
    session.commit()
    session.refresh(domain)
    return domain


def create_domain(name: str, owner_id: int, catch_all: Optional[str] = None) -> Domain:
    """Create a new domain.

    Args:
        name: The domain name
        owner_id: ID of the user who owns this domain
        catch_all: Optional catch-all email address

    Returns:
        The created domain

    Raises:
        ValidationError: If input validation fails
        ServiceError: If domain creation fails
    """
    try:
        # Validate input
        name = validate_domain_name(name)
        if catch_all:
            catch_all = validate_email(catch_all)

        with get_db() as session:
            # Check if domain already exists
            existing_domain = db_get_active_domain_by_name(session, name)
            if existing_domain:
                raise ValidationError(f"Domain '{name}' already exists")

            # Verify owner exists
            owner = db_get_user_by_id(session, owner_id)
            if not owner:
                raise ValidationError(f"Owner with id {owner_id} not found")

            # Create domain
            domain_data = {"name": name, "owner_id": owner_id, "catch_all": catch_all}

            domain = create_domain_record(session, **domain_data)

            log_activity(
                "domain_created",
                {
                    "domain_id": domain.id,
                    "domain_name": name,
                    "owner_id": owner_id,
                    "catch_all": catch_all,
                },
            )

            return domain

    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Failed to create domain '{name}': {e}")
        raise


def get_user_domains(user_id: int, user_role: str = "user") -> List[Domain]:
    """Get domains owned by a user.

    Args:
        user_id: ID of the user
        user_role: Role of the user (admin can see all domains)

    Returns:
        List of domains owned by the user
    """
    try:
        with get_db() as session:
            include_aliases = True
            domains = db_list_user_domains(
                session,
                user_id=None if user_role == "admin" else user_id,
                include_aliases=include_aliases,
            )

            log_activity(
                "domains_retrieved",
                {"user_id": user_id, "user_role": user_role, "domain_count": len(domains)},
            )

            return domains

    except Exception as e:
        logger.error(f"Failed to get domains for user {user_id}: {e}")
        raise


def get_domain_with_status(
        self, domain_id: int, user_id: int, user_role: str = "user"
) -> Dict[str, Any]:
    """Get domain with DNS status information.

    Args:
        domain_id: ID of the domain
        user_id: ID of the requesting user
        user_role: Role of the requesting user

    Returns:
        Dictionary containing domain info and DNS status

    Raises:
        ResourceNotFoundError: If domain not found
        PermissionError: If user lacks permission
    """
    try:
        with get_db() as session:
            domain = get_by_id_or_404(session, Domain, domain_id)

            # Check ownership
            validate_ownership(domain, user_id, user_role)

            # Get DNS status
            dns_results = check_dns_records(domain.name)

            # Check MX records
            mx_valid = False
            try:
                import dns.resolver

                answers = dns.resolver.resolve(domain.name, "MX")
                mx_valid = any(answers)
            except Exception:
                mx_valid = False

            domain_status = {
                "id": domain.id,
                "name": domain.name,
                "catch_all": domain.catch_all,
                "owner_id": domain.owner_id,
                "created_at": domain.created_at,
                "updated_at": domain.updated_at,
                "verified": dns_results.get("spf", {}).get("status") == "valid",
                "mx_valid": mx_valid,
                "spf_valid": dns_results.get("spf", {}).get("status") == "valid",
                "dkim_valid": dns_results.get("dkim", {}).get("status") == "valid",
                "dmarc_valid": dns_results.get("dmarc", {}).get("status") == "valid",
                "dns_results": dns_results,
            }

            log_activity(
                "domain_status_checked",
                {
                    "domain_id": domain_id,
                    "user_id": user_id,
                    "dns_status": {
                        "spf": dns_results.get("spf", {}).get("status"),
                        "dkim": dns_results.get("dkim", {}).get("status"),
                        "dmarc": dns_results.get("dmarc", {}).get("status"),
                        "mx": mx_valid,
                    },
                },
            )

            return domain_status

    except (ResourceNotFoundError, PermissionError):
        raise
    except Exception as e:
        logger.error(f"Failed to get domain status for domain {domain_id}: {e}")
        raise


def update_domain(domain_id: int, user_id: int, user_role: str = "user", **kwargs) -> Domain:
    """Update a domain.

    Args:
        domain_id: ID of the domain to update
        user_id: ID of the requesting user
        user_role: Role of the requesting user
        **kwargs: Fields to update

    Returns:
        The updated domain

    Raises:
        ResourceNotFoundError: If domain not found
        PermissionError: If user lacks permission
        ValidationError: If validation fails
    """
    try:
        with get_db() as session:
            domain = get_by_id_or_404(session, Domain, domain_id)

            # Check ownership
            validate_ownership(domain, user_id, user_role)

            # Validate updates
            if "name" in kwargs:
                kwargs["name"] = validate_domain_name(kwargs["name"])

                # Check if new name already exists (excluding current domain)
                existing_domain = db_get_active_domain_by_name(session, kwargs["name"])
                if existing_domain and existing_domain.id != domain_id:
                    raise ValidationError(f"Domain '{kwargs['name']}' already exists")

            if "catch_all" in kwargs and kwargs["catch_all"]:
                kwargs["catch_all"] = validate_email(kwargs["catch_all"])
            elif "catch_all" in kwargs and not kwargs["catch_all"]:
                kwargs["catch_all"] = None

            updated_domain = update_domain_record(session, session, domain, **kwargs)

            log_activity(
                "domain_updated",
                {"domain_id": domain_id, "user_id": user_id, "fields": list(kwargs.keys())},
            )

            return updated_domain

    except (ResourceNotFoundError, PermissionError, ValidationError):
        raise
    except Exception as e:
        logger.error(f"Failed to update domain {domain_id}: {e}")
        raise


def delete_domain(domain_id: int, user_id: int, user_role: str = "user") -> bool:
    """Soft delete a domain and all its aliases.

    Args:
        domain_id: ID of the domain to delete
        user_id: ID of the requesting user
        user_role: Role of the requesting user

    Raises:
        ResourceNotFoundError: If domain not found
        PermissionError: If user lacks permission
    """
    try:
        with get_db() as session:
            domain = get_by_id_or_404(session, Domain, domain_id)

            # Check ownership
            validate_ownership(domain, user_id, user_role)

            # Soft delete domain and cascade to aliases
            soft_delete_domain(session, domain_id)

            log_activity(
                "domain_deleted",
                {"domain_id": domain_id, "domain_name": domain.name, "user_id": user_id},
            )

            return True

    except (ResourceNotFoundError, PermissionError):
        raise
    except Exception as e:
        logger.error(f"Failed to delete domain {domain_id}: {e}")
        raise


def check_domain_dns(domain_name: str) -> Dict[str, Any]:
    """Check DNS records for a domain.

    Args:
        domain_name: The domain name to check

    Returns:
        Dictionary containing DNS check results
    """
    try:
        # Validate domain name
        domain_name = validate_domain_name(domain_name)

        # Check DNS records
        dns_results = check_dns_records(domain_name)

        log_activity(
            "dns_check_performed", {"domain_name": domain_name, "results": dns_results}
        )

        return dns_results

    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Failed to check DNS for domain '{domain_name}': {e}")
        raise


def get_domain_statistics(user_id: int, user_role: str = "user") -> Dict[str, Any]:
    """Get domain statistics for a user.

    Args:
        user_id: ID of the user
        user_role: Role of the user

    Returns:
        Dictionary containing domain statistics
    """
    try:
        with get_db() as session:
            query = get_active_domains(session)

            if user_role != "admin":
                query = query.filter_by(owner_id=user_id)

            domains = query.all()

            # Calculate statistics
            total_domains = len(domains)
            domains_with_catch_all = sum(1 for d in domains if d.catch_all)

            # Check DNS status for each domain
            verified_domains = 0
            for domain in domains:
                try:
                    dns_results = check_dns_records(domain.name)
                    if dns_results.get("spf", {}).get("status") == "valid":
                        verified_domains += 1
                except Exception:
                    continue  # Skip domains with DNS check errors

            stats = {
                "total_domains": total_domains,
                "verified_domains": verified_domains,
                "domains_with_catch_all": domains_with_catch_all,
                "verification_rate": (verified_domains / total_domains * 100)
                if total_domains > 0
                else 0,
            }

            log_activity(
                "domain_statistics_retrieved",
                {"user_id": user_id, "user_role": user_role, "statistics": stats},
            )

            return stats

    except Exception as e:
        logger.error(f"Failed to get domain statistics for user {user_id}: {e}")
        raise


def validate_domain_ownership(
        self, domain_name: str, user_id: int, user_role: str = "user"
) -> bool:
    """Validate that a user owns a domain.

    Args:
        domain_name: The domain name to check
        user_id: ID of the user
        user_role: Role of the user

    Returns:
        True if user owns the domain or is admin, False otherwise
    """
    try:
        with get_db() as session:
            domain = get_active_domains(session).filter_by(name=domain_name).first()

            if not domain:
                return False

            if user_role == "admin":
                return True

            return domain.owner_id == user_id

    except Exception as e:
        logger.error(f"Failed to validate domain ownership for '{domain_name}': {e}")
        return False


"""Domain controller for domain management operations."""

from typing import List, Optional, Dict, Any

from utils.error_handling import (
    ValidationError,
    ResourceNotFoundError,
)
from database.models import Domain, ActivityLog
from utils.validation import validate_domain_name, validate_email
from utils.soft_delete import get_active_domains, soft_delete_domain
from controllers.dns_controller import check_dns_records
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.domain_database import (
    db_get_user_by_id,
    db_get_active_domain_by_name,
    db_list_user_domains,
    db_update_domain_fields,
    db_list_all_domains,
    db_get_domain_by_id,
    db_create_domain,
    db_delete_domain,
)


def create_domain(name: str, owner_id: int, catch_all: Optional[str] = None) -> Domain:
    """Create a new domain.

    Args:
        name: The domain name
        owner_id: ID of the user who owns this domain
        catch_all: Optional catch-all email address

    Returns:
        The created domain

    Raises:
        ValidationError: If input validation fails
        ServiceError: If domain creation fails
    """
    try:
        # Validate input
        name = validate_domain_name(name)
        if catch_all:
            catch_all = validate_email(catch_all)

        with get_db() as session:
            # Check if domain already exists
            existing_domain = db_get_active_domain_by_name(session, name)
            if existing_domain:
                raise ValidationError(f"Domain '{name}' already exists")

            # Verify owner exists
            owner = db_get_user_by_id(session, owner_id)
            if not owner:
                raise ValidationError(f"Owner with id {owner_id} not found")

            # Create domain
            domain_data = {"name": name, "owner_id": owner_id, "catch_all": catch_all}

            domain = create_domain_record(session, **domain_data)

            log_activity(
                "domain_created",
                {
                    "domain_id": domain.id,
                    "domain_name": name,
                    "owner_id": owner_id,
                    "catch_all": catch_all,
                },
            )

            return domain

    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Failed to create domain '{name}': {e}")
        raise


def get_user_domains(user_id: int, user_role: str = "user") -> List[Domain]:
    """Get domains owned by a user.

    Args:
        user_id: ID of the user
        user_role: Role of the user (admin can see all domains)

    Returns:
        List of domains owned by the user
    """
    try:
        with get_db() as session:
            include_aliases = True
            domains = db_list_user_domains(
                session,
                user_id=None if user_role == "admin" else user_id,
                include_aliases=include_aliases,
            )

            log_activity(
                "domains_retrieved",
                {"user_id": user_id, "user_role": user_role, "domain_count": len(domains)},
            )

            return domains

    except Exception as e:
        logger.error(f"Failed to get domains for user {user_id}: {e}")
        raise


def get_domain_with_status(
        self, domain_id: int, user_id: int, user_role: str = "user"
) -> Dict[str, Any]:
    """Get domain with DNS status information.

    Args:
        domain_id: ID of the domain
        user_id: ID of the requesting user
        user_role: Role of the requesting user

    Returns:
        Dictionary containing domain info and DNS status

    Raises:
        ResourceNotFoundError: If domain not found
        PermissionError: If user lacks permission
    """
    try:
        with get_db() as session:
            domain = get_by_id_or_404(session, Domain, domain_id)

            # Check ownership
            validate_ownership(domain, user_id, user_role)

            # Get DNS status
            dns_results = check_dns_records(domain.name)

            # Check MX records
            mx_valid = False
            try:
                import dns.resolver

                answers = dns.resolver.resolve(domain.name, "MX")
                mx_valid = any(answers)
            except Exception:
                mx_valid = False

            domain_status = {
                "id": domain.id,
                "name": domain.name,
                "catch_all": domain.catch_all,
                "owner_id": domain.owner_id,
                "created_at": domain.created_at,
                "updated_at": domain.updated_at,
                "verified": dns_results.get("spf", {}).get("status") == "valid",
                "mx_valid": mx_valid,
                "spf_valid": dns_results.get("spf", {}).get("status") == "valid",
                "dkim_valid": dns_results.get("dkim", {}).get("status") == "valid",
                "dmarc_valid": dns_results.get("dmarc", {}).get("status") == "valid",
                "dns_results": dns_results,
            }

            log_activity(
                "domain_status_checked",
                {
                    "domain_id": domain_id,
                    "user_id": user_id,
                    "dns_status": {
                        "spf": dns_results.get("spf", {}).get("status"),
                        "dkim": dns_results.get("dkim", {}).get("status"),
                        "dmarc": dns_results.get("dmarc", {}).get("status"),
                        "mx": mx_valid,
                    },
                },
            )

            return domain_status

    except (ResourceNotFoundError, PermissionError):
        raise
    except Exception as e:
        logger.error(f"Failed to get domain status for domain {domain_id}: {e}")
        raise


def update_domain(domain_id: int, user_id: int, user_role: str = "user", **kwargs) -> Domain:
    """Update a domain.

    Args:
        domain_id: ID of the domain to update
        user_id: ID of the requesting user
        user_role: Role of the requesting user
        **kwargs: Fields to update

    Returns:
        The updated domain

    Raises:
        ResourceNotFoundError: If domain not found
        PermissionError: If user lacks permission
        ValidationError: If validation fails
    """
    try:
        with get_db() as session:
            domain = get_by_id_or_404(session, Domain, domain_id)

            # Check ownership
            validate_ownership(domain, user_id, user_role)

            # Validate updates
            if "name" in kwargs:
                kwargs["name"] = validate_domain_name(kwargs["name"])

                # Check if new name already exists (excluding current domain)
                existing_domain = db_get_active_domain_by_name(session, kwargs["name"])
                if existing_domain and existing_domain.id != domain_id:
                    raise ValidationError(f"Domain '{kwargs['name']}' already exists")

            if "catch_all" in kwargs and kwargs["catch_all"]:
                kwargs["catch_all"] = validate_email(kwargs["catch_all"])
            elif "catch_all" in kwargs and not kwargs["catch_all"]:
                kwargs["catch_all"] = None

            updated_domain = update_domain_record(session, session, domain, **kwargs)

            log_activity(
                "domain_updated",
                {"domain_id": domain_id, "user_id": user_id, "fields": list(kwargs.keys())},
            )

            return updated_domain

    except (ResourceNotFoundError, PermissionError, ValidationError):
        raise
    except Exception as e:
        logger.error(f"Failed to update domain {domain_id}: {e}")
        raise


def delete_domain(domain_id: int, user_id: int, user_role: str = "user") -> bool:
    """Soft delete a domain and all its aliases.

    Args:
        domain_id: ID of the domain to delete
        user_id: ID of the requesting user
        user_role: Role of the requesting user

    Raises:
        ResourceNotFoundError: If domain not found
        PermissionError: If user lacks permission
    """
    try:
        with get_db() as session:
            domain = get_by_id_or_404(session, Domain, domain_id)

            # Check ownership
            validate_ownership(domain, user_id, user_role)

            # Soft delete domain and cascade to aliases
            soft_delete_domain(session, domain_id)

            log_activity(
                "domain_deleted",
                {"domain_id": domain_id, "domain_name": domain.name, "user_id": user_id},
            )

            return True

    except (ResourceNotFoundError, PermissionError):
        raise
    except Exception as e:
        logger.error(f"Failed to delete domain {domain_id}: {e}")
        raise


def check_domain_dns(domain_name: str) -> Dict[str, Any]:
    """Check DNS records for a domain.

    Args:
        domain_name: The domain name to check

    Returns:
        Dictionary containing DNS check results
    """
    try:
        # Validate domain name
        domain_name = validate_domain_name(domain_name)

        # Check DNS records
        dns_results = check_dns_records(domain_name)

        log_activity(
            "dns_check_performed", {"domain_name": domain_name, "results": dns_results}
        )

        return dns_results

    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Failed to check DNS for domain '{domain_name}': {e}")
        raise


def get_domain_statistics(user_id: int, user_role: str = "user") -> Dict[str, Any]:
    """Get domain statistics for a user.

    Args:
        user_id: ID of the user
        user_role: Role of the user

    Returns:
        Dictionary containing domain statistics
    """
    try:
        with get_db() as session:
            query = get_active_domains(session)

            if user_role != "admin":
                query = query.filter_by(owner_id=user_id)

            domains = query.all()

            # Calculate statistics
            total_domains = len(domains)
            domains_with_catch_all = sum(1 for d in domains if d.catch_all)

            # Check DNS status for each domain
            verified_domains = 0
            for domain in domains:
                try:
                    dns_results = check_dns_records(domain.name)
                    if dns_results.get("spf", {}).get("status") == "valid":
                        verified_domains += 1
                except Exception:
                    continue  # Skip domains with DNS check errors

            stats = {
                "total_domains": total_domains,
                "verified_domains": verified_domains,
                "domains_with_catch_all": domains_with_catch_all,
                "verification_rate": (verified_domains / total_domains * 100)
                if total_domains > 0
                else 0,
            }

            log_activity(
                "domain_statistics_retrieved",
                {"user_id": user_id, "user_role": user_role, "statistics": stats},
            )

            return stats

    except Exception as e:
        logger.error(f"Failed to get domain statistics for user {user_id}: {e}")
        raise


def validate_domain_ownership(
        self, domain_name: str, user_id: int, user_role: str = "user"
) -> bool:
    """Validate that a user owns a domain.

    Args:
        domain_name: The domain name to check
        user_id: ID of the user
        user_role: Role of the user

    Returns:
        True if user owns the domain or is admin, False otherwise
    """
    try:
        with get_db() as session:
            domain = get_active_domains(session).filter_by(name=domain_name).first()

            if not domain:
                return False

            if user_role == "admin":
                return True

            return domain.owner_id == user_id

    except Exception as e:
        logger.error(f"Failed to validate domain ownership for '{domain_name}': {e}")
        return False


def _domain_to_dict(domain: Domain) -> Dict[str, Any]:
    return {
        "id": domain.id,
        "name": domain.name,
        "owner_id": domain.owner_id,
        "catch_all": domain.catch_all,
        "created_at": getattr(domain, "created_at", None),
        "updated_at": getattr(domain, "updated_at", None),
    }


async def list_domains_simple(session: AsyncSession) -> List[Dict[str, Any]]:
    domains = await db_list_all_domains(session, include_aliases=False)
    return [_domain_to_dict(d) for d in domains]


async def create_domain_simple(
        session: AsyncSession, name: str, owner_id: int, catch_all: Optional[str] = None
) -> Dict[str, Any]:
    # Basic sanitize/validate similar to service
    name = validate_domain_name(name)
    if catch_all:
        catch_all = validate_email(catch_all)
    # Ensure not duplicate
    exists = await db_get_active_domain_by_name(session, name)  # type: ignore[arg-type]
    if exists:
        raise ValidationError(f"Domain '{name}' already exists")
    domain = await db_create_domain(session, name=name, owner_id=owner_id, catch_all=catch_all)
    return _domain_to_dict(domain)


async def get_domain_simple(session: AsyncSession, domain_id: int) -> Optional[Dict[str, Any]]:
    domain = await db_get_domain_by_id(session, domain_id)
    return _domain_to_dict(domain) if domain else None


async def delete_domain_simple(session: AsyncSession, domain_id: int) -> bool:
    return await db_delete_domain(session, domain_id)


async def update_domain_catchall(
        session: AsyncSession, domain_id: int, catch_all: Optional[str]
) -> Optional[Dict[str, Any]]:
    domain = await db_get_domain_by_id(session, domain_id)
    if not domain:
        return None
    # Normalize blank to None and validate if provided
    if catch_all:
        catch_all = validate_email(catch_all)
    else:
        catch_all = None
    updated = await db_update_domain_fields(session, domain, catch_all=catch_all)
    return _domain_to_dict(updated)


async def get_dns_status_simple(session: AsyncSession, domain_id: int) -> Optional[Dict[str, Any]]:
    domain = await db_get_domain_by_id(session, domain_id)
    if not domain:
        return None
    # External DNS lookups (sync lib) are ok here for simplicity
    results: Dict[str, Any] = {}
    try:
        import dns.resolver

        mx_answers = dns.resolver.resolve(domain.name, "MX")
        results["mx"] = [str(r.exchange).rstrip(".") for r in mx_answers]
    except Exception:
        results["mx"] = []
    try:
        import dns.resolver

        txt_answers = dns.resolver.resolve(domain.name, "TXT")
        spf = [
            r.strings[0].decode()
            for r in txt_answers
            if r.strings and r.strings[0].decode().startswith("v=spf1")
        ]
        results["spf"] = spf
    except Exception:
        results["spf"] = []
    try:
        import dns.resolver

        dkim_name = f"mail._domainkey.{domain.name}"
        dkim_txt = dns.resolver.resolve(dkim_name, "TXT")
        dkim = [r.strings[0].decode() for r in dkim_txt if r.strings]
        results["dkim"] = dkim
    except Exception:
        results["dkim"] = []
    try:
        import dns.resolver

        dmarc_name = f"_dmarc.{domain.name}"
        dmarc_txt = dns.resolver.resolve(dmarc_name, "TXT")
        dmarc = [r.strings[0].decode() for r in dmarc_txt if r.strings]
        results["dmarc"] = dmarc
    except Exception:
        results["dmarc"] = []
    return results


async def activity_stats_simple(session: AsyncSession) -> Dict[str, List[int]]:
    cutoff_stmt = select(ActivityLog).where(
        ActivityLog.timestamp >= (select(ActivityLog.timestamp).scalar_subquery())
    )
    # Simpler approach: fetch last 30 days in Python using now - 30d
    from datetime import datetime, timedelta

    cutoff = datetime.utcnow() - timedelta(days=30)
    result = await session.execute(select(ActivityLog).where(ActivityLog.timestamp >= cutoff))
    logs = list(result.scalars().all())
    from collections import defaultdict

    stats = defaultdict(lambda: {"forward": 0, "bounce": 0, "error": 0})
    for log in logs:
        date = str(log.timestamp)[:10]
        if log.event_type in ("forward", "bounce", "error"):
            stats[date][log.event_type] += 1
    sorted_stats = sorted(stats.items())
    return {
        "dates": [d for d, _ in sorted_stats],
        "forward": [v["forward"] for _, v in sorted_stats],
        "bounce": [v["bounce"] for _, v in sorted_stats],
        "error": [v["error"] for _, v in sorted_stats],
    }


async def get_domain_count(db):
    return await domain_database.get_domain_count(db)
