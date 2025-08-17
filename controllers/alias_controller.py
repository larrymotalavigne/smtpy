"""Alias controller for email alias management operations."""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

# Merged async thin operations (formerly in controllers.alias_ops)
from sqlalchemy.ext.asyncio import AsyncSession

from database.alias_database import (
    db_list_aliases,
    db_create_alias,
    db_get_alias,
    db_delete_alias,
    db_list_aliases_by_domain,
    db_add_alias,
)
from database.models import Alias, Domain, User, ActivityLog
from utils.db import get_db
from utils.error_handling import ValidationError, ResourceNotFoundError
from utils.soft_delete import get_active_aliases, get_active_domains, soft_delete_alias
from utils.validation import validate_alias_local_part, validate_email_list

logger = logging.getLogger("smtpy.alias_controller")


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


def create_alias_record(session, **alias_data) -> Alias:
    """Create a new alias record in the database."""
    alias = Alias(**alias_data)
    session.add(alias)
    session.commit()
    session.refresh(alias)
    return alias


def get_by_id_or_404(session, model_class, record_id: int):
    """Get a record by ID or raise an error if not found."""
    record = session.get(model_class, record_id)
    if not record:
        raise ValidationError(f"{model_class.__name__} with id {record_id} not found")
    return record


def validate_ownership(record, user_id: int, user_role: str = "user") -> None:
    """Validate that a user owns a record or is an admin."""
    if user_role != "admin" and getattr(record, 'owner_id', None) != user_id:
        raise PermissionError("Access denied: insufficient permissions")


def update_alias_record(session, alias, **kwargs):
    """Update an alias record with the given fields."""
    for key, value in kwargs.items():
        if hasattr(alias, key):
            setattr(alias, key, value)
    session.commit()
    session.refresh(alias)
    return alias


def create_alias(
        local_part: str,
        targets: str,
        domain_id: int,
        owner_id: int,
        expires_at: Optional[datetime] = None,
) -> Alias:
    """Create a new email alias.

    Args:
        local_part: The local part of the email alias (before @)
        targets: Comma-separated list of target email addresses
        domain_id: ID of the domain this alias belongs to
        owner_id: ID of the user who owns this alias
        expires_at: Optional expiration date for the alias

    Returns:
        The created alias

    Raises:
        ValidationError: If input validation fails
        ServiceError: If alias creation fails
    """
    try:
        # Validate input
        local_part = validate_alias_local_part(local_part)
        target_emails = validate_email_list(targets)
        targets_str = ", ".join(target_emails)  # Store as comma-separated string

        with get_db() as session:
            # Verify domain exists and user has access
            domain = session.get(Domain, domain_id)
            if not domain:
                raise ValidationError(f"Domain with id {domain_id} not found")

            # Check if domain is active
            if not get_active_domains(session).filter_by(id=domain_id).first():
                raise ValidationError(f"Domain is not active")

            # Check domain ownership (admin can create aliases for any domain)
            owner = session.get(User, owner_id)
            if not owner:
                raise ValidationError(f"Owner with id {owner_id} not found")

            if owner.role != "admin" and domain.owner_id != owner_id:
                raise PermissionError("You can only create aliases for your own domains")

            # Check if alias already exists for this domain
            existing_alias = (
                get_active_aliases(session)
                .filter_by(domain_id=domain_id, local_part=local_part)
                .first()
            )
            if existing_alias:
                raise ValidationError(f"Alias '{local_part}@{domain.name}' already exists")

            # Validate expiration date
            if expires_at and expires_at <= datetime.utcnow():
                raise ValidationError("Expiration date must be in the future")

            # Create alias
            alias_data = {
                "local_part": local_part,
                "targets": targets_str,
                "domain_id": domain_id,
                "owner_id": owner_id,
                "expires_at": expires_at,
            }

            alias = create_alias_record(session, **alias_data)

            log_activity(
                "alias_created",
                {
                    "alias_id": alias.id,
                    "local_part": local_part,
                    "domain_id": domain_id,
                    "domain_name": domain.name,
                    "owner_id": owner_id,
                    "targets": target_emails,
                    "expires_at": expires_at.isoformat() if expires_at else None,
                },
            )

            return alias

    except (ValidationError, PermissionError):
        raise
    except Exception as e:
        logger.error(f"Failed to create alias '{local_part}': {e}")
        raise


def get_user_aliases(
        user_id: int, user_role: str = "user", domain_id: Optional[int] = None
) -> List[Alias]:
    """Get aliases owned by a user.

    Args:
        user_id: ID of the user
        user_role: Role of the user (admin can see all aliases)
        domain_id: Optional domain ID to filter by

    Returns:
        List of aliases owned by the user
    """
    try:
        with get_db() as session:
            query = get_active_aliases(session)

            if user_role != "admin":
                query = query.filter_by(owner_id=user_id)

            if domain_id:
                query = query.filter_by(domain_id=domain_id)

            aliases = query.all()

            log_activity(
                "aliases_retrieved",
                {
                    "user_id": user_id,
                    "user_role": user_role,
                    "domain_id": domain_id,
                    "alias_count": len(aliases),
                },
            )

            return aliases

    except Exception as e:
        logger.error(f"Failed to get aliases for user {user_id}: {e}")
        raise


def get_alias_with_details(
        self, alias_id: int, user_id: int, user_role: str = "user"
) -> Dict[str, Any]:
    """Get alias with detailed information.

    Args:
        alias_id: ID of the alias
        user_id: ID of the requesting user
        user_role: Role of the requesting user

    Returns:
        Dictionary containing alias details

    Raises:
        ResourceNotFoundError: If alias not found
        PermissionError: If user lacks permission
    """
    try:
        with get_db() as session:
            alias = get_by_id_or_404(session, Alias, alias_id, session)

            # Check ownership
            validate_ownership(alias, user_id, user_role)

            # Get domain information
            domain = session.get(Domain, alias.domain_id)

            # Check if alias is expired
            is_expired = alias.expires_at and alias.expires_at <= datetime.utcnow()

            # Parse targets
            target_emails = [email.strip() for email in alias.targets.split(",") if email.strip()]

            alias_details = {
                "id": alias.id,
                "local_part": alias.local_part,
                "full_address": f"{alias.local_part}@{domain.name}",
                "targets": target_emails,
                "targets_count": len(target_emails),
                "domain_id": alias.domain_id,
                "domain_name": domain.name,
                "owner_id": alias.owner_id,
                "expires_at": alias.expires_at,
                "is_expired": is_expired,
                "created_at": alias.created_at,
                "updated_at": alias.updated_at,
            }

            log_activity(
                "alias_details_retrieved",
                {
                    "alias_id": alias_id,
                    "user_id": user_id,
                    "full_address": alias_details["full_address"],
                },
            )

            return alias_details

    except (ResourceNotFoundError, PermissionError):
        raise
    except Exception as e:
        logger.error(f"Failed to get alias details for alias {alias_id}: {e}")
        raise


def update_alias(alias_id: int, user_id: int, user_role: str = "user", **kwargs) -> Alias:
    """Update an alias.

    Args:
        alias_id: ID of the alias to update
        user_id: ID of the requesting user
        user_role: Role of the requesting user
        **kwargs: Fields to update

    Returns:
        The updated alias

    Raises:
        ResourceNotFoundError: If alias not found
        PermissionError: If user lacks permission
        ValidationError: If validation fails
    """
    try:
        with get_db() as session:
            alias = get_by_id_or_404(session, Alias, alias_id, session)

            # Check ownership
            validate_ownership(alias, user_id, user_role)

            # Validate updates
            if "local_part" in kwargs:
                kwargs["local_part"] = validate_alias_local_part(kwargs["local_part"])

                # Check if new local_part already exists for this domain (excluding current alias)
                existing_alias = (
                    get_active_aliases(session)
                    .filter_by(domain_id=alias.domain_id, local_part=kwargs["local_part"])
                    .first()
                )
                if existing_alias and existing_alias.id != alias_id:
                    domain = session.get(Domain, alias.domain_id)
                    raise ValidationError(
                        f"Alias '{kwargs['local_part']}@{domain.name}' already exists"
                    )

            if "targets" in kwargs:
                target_emails = validate_email_list(kwargs["targets"])
                kwargs["targets"] = ", ".join(target_emails)

            if "expires_at" in kwargs and kwargs["expires_at"]:
                if kwargs["expires_at"] <= datetime.utcnow():
                    raise ValidationError("Expiration date must be in the future")
            elif "expires_at" in kwargs and not kwargs["expires_at"]:
                kwargs["expires_at"] = None

            updated_alias = update_alias_record(session, alias, **kwargs)

            log_activity(
                "alias_updated",
                {"alias_id": alias_id, "user_id": user_id, "fields": list(kwargs.keys())},
            )

            return updated_alias

    except (ResourceNotFoundError, PermissionError, ValidationError):
        raise
    except Exception as e:
        logger.error(f"Failed to update alias {alias_id}: {e}")
        raise


def delete_alias(alias_id: int, user_id: int, user_role: str = "user") -> bool:
    """Soft delete an alias.

    Args:
        alias_id: ID of the alias to delete
        user_id: ID of the requesting user
        user_role: Role of the requesting user

    Raises:
        ResourceNotFoundError: If alias not found
        PermissionError: If user lacks permission
    """
    try:
        with get_db() as session:
            alias = get_by_id_or_404(session, Alias, alias_id, session)

            # Check ownership
            validate_ownership(alias, user_id, user_role)

            # Get domain for logging
            domain = session.get(Domain, alias.domain_id)
            full_address = f"{alias.local_part}@{domain.name}"

            # Soft delete alias
            soft_delete_alias(session, alias_id)

            log_activity(
                "alias_deleted",
                {"alias_id": alias_id, "full_address": full_address, "user_id": user_id},
            )

            return True

    except (ResourceNotFoundError, PermissionError):
        raise
    except Exception as e:
        logger.error(f"Failed to delete alias {alias_id}: {e}")
        raise


def get_expired_aliases(user_id: Optional[int] = None) -> List[Alias]:
    """Get aliases that have expired.

    Args:
        user_id: Optional user ID to filter by (admin only if None)

    Returns:
        List of expired aliases
    """
    try:
        with get_db() as session:
            query = get_active_aliases(session).filter(
                Alias.expires_at.isnot(None), Alias.expires_at <= datetime.utcnow()
            )

            if user_id:
                query = query.filter_by(owner_id=user_id)

            expired_aliases = query.all()

            log_activity(
                "expired_aliases_retrieved",
                {"user_id": user_id, "expired_count": len(expired_aliases)},
            )

            return expired_aliases

    except Exception as e:
        logger.error(f"Failed to get expired aliases: {e}")
        raise


def get_alias_statistics(user_id: int, user_role: str = "user") -> Dict[str, Any]:
    """Get alias statistics for a user.

    Args:
        user_id: ID of the user
        user_role: Role of the user

    Returns:
        Dictionary containing alias statistics
    """
    try:
        with get_db() as session:
            query = get_active_aliases(session)

            if user_role != "admin":
                query = query.filter_by(owner_id=user_id)

            aliases = query.all()

            # Calculate statistics
            total_aliases = len(aliases)
            expired_aliases = sum(
                1 for a in aliases if a.expires_at and a.expires_at <= datetime.utcnow()
            )
            expiring_soon = sum(
                1
                for a in aliases
                if a.expires_at
                and datetime.utcnow() <= a.expires_at <= datetime.utcnow() + timedelta(days=7)
            )

            # Count aliases by domain
            domain_counts = {}
            for alias in aliases:
                domain = session.get(Domain, alias.domain_id)
                if domain:
                    domain_counts[domain.name] = domain_counts.get(domain.name, 0) + 1

            stats = {
                "total_aliases": total_aliases,
                "expired_aliases": expired_aliases,
                "expiring_soon": expiring_soon,
                "active_aliases": total_aliases - expired_aliases,
                "domain_distribution": domain_counts,
            }

            log_activity(
                "alias_statistics_retrieved",
                {"user_id": user_id, "user_role": user_role, "statistics": stats},
            )

            return stats

    except Exception as e:
        logger.error(f"Failed to get alias statistics for user {user_id}: {e}")
        raise


def test_alias_forwarding(
        self, alias_id: int, user_id: int, user_role: str = "user"
) -> Dict[str, Any]:
    """Test alias forwarding configuration.

    Args:
        alias_id: ID of the alias to test
        user_id: ID of the requesting user
        user_role: Role of the requesting user

    Returns:
        Dictionary containing test results

    Raises:
        ResourceNotFoundError: If alias not found
        PermissionError: If user lacks permission
    """
    try:
        with get_db() as session:
            alias = get_by_id_or_404(session, Alias, alias_id, session)

            # Check ownership
            validate_ownership(alias, user_id, user_role)

            # Get domain
            domain = session.get(Domain, alias.domain_id)
            full_address = f"{alias.local_part}@{domain.name}"

            # Parse targets
            target_emails = [email.strip() for email in alias.targets.split(",") if email.strip()]

            # Check if alias is expired
            is_expired = alias.expires_at and alias.expires_at <= datetime.utcnow()

            # Validate target emails
            valid_targets = []
            invalid_targets = []

            for target in target_emails:
                try:
                    from utils.validation import validate_email

                    validate_email(target)
                    valid_targets.append(target)
                except Exception:
                    invalid_targets.append(target)

            test_results = {
                "alias_id": alias_id,
                "full_address": full_address,
                "is_active": not is_expired,
                "is_expired": is_expired,
                "expires_at": alias.expires_at,
                "total_targets": len(target_emails),
                "valid_targets": valid_targets,
                "invalid_targets": invalid_targets,
                "forwarding_ready": not is_expired
                                    and len(valid_targets) > 0
                                    and len(invalid_targets) == 0,
            }

            log_activity(
                "alias_forwarding_tested",
                {
                    "alias_id": alias_id,
                    "user_id": user_id,
                    "full_address": full_address,
                    "test_results": test_results,
                },
            )

            return test_results

    except (ResourceNotFoundError, PermissionError):
        raise
    except Exception as e:
        logger.error(f"Failed to test alias forwarding for alias {alias_id}: {e}")
        raise


def cleanup_expired_aliases(dry_run: bool = True) -> Dict[str, Any]:
    """Clean up expired aliases (admin only).

    Args:
        dry_run: If True, only return what would be cleaned up without actually doing it

    Returns:
        Dictionary containing cleanup results
    """
    try:
        with get_db() as session:
            # Get expired aliases
            expired_aliases = (
                get_active_aliases(session)
                .filter(Alias.expires_at.isnot(None), Alias.expires_at <= datetime.utcnow())
                .all()
            )

            cleanup_results = {
                "total_expired": len(expired_aliases),
                "cleaned_up": 0,
                "dry_run": dry_run,
                "aliases": [],
            }

            for alias in expired_aliases:
                domain = session.get(Domain, alias.domain_id)
                full_address = f"{alias.local_part}@{domain.name}"

                alias_info = {
                    "id": alias.id,
                    "full_address": full_address,
                    "expired_at": alias.expires_at,
                    "owner_id": alias.owner_id,
                }

                cleanup_results["aliases"].append(alias_info)

                if not dry_run:
                    # Soft delete the expired alias
                    soft_delete_alias(session, alias.id)
                    cleanup_results["cleaned_up"] += 1

            log_activity(
                "expired_aliases_cleanup",
                {
                    "dry_run": dry_run,
                    "total_expired": cleanup_results["total_expired"],
                    "cleaned_up": cleanup_results["cleaned_up"],
                },
            )

            return cleanup_results

    except Exception as e:
        logger.error(f"Failed to cleanup expired aliases: {e}")
        raise


# ---- Thin async alias operations merged from controllers.alias_ops ----
# annotations future import not needed here

import datetime as _dt


def _alias_to_dict(alias: Alias) -> Dict[str, Any]:
    return {
        "id": alias.id,
        "local_part": alias.local_part,
        "targets": alias.targets,
        "domain_id": alias.domain_id,
        "owner_id": getattr(alias, "owner_id", None),
        "expires_at": alias.expires_at.isoformat() if getattr(alias, "expires_at", None) else None,
        "created_at": alias.created_at.isoformat() if getattr(alias, "created_at", None) else None,
        "updated_at": alias.updated_at.isoformat() if getattr(alias, "updated_at", None) else None,
    }


async def list_aliases(
        session: AsyncSession, domain_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    aliases = await db_list_aliases(session, domain_id=domain_id)
    return [_alias_to_dict(a) for a in aliases]


async def create_alias(
        session: AsyncSession, local_part: str, targets: str, domain_id: int
) -> Dict[str, Any]:
    alias = await db_create_alias(
        session, local_part=local_part, targets=targets, domain_id=domain_id
    )
    return _alias_to_dict(alias)


async def get_alias(session: AsyncSession, alias_id: int) -> Dict[str, Any]:
    alias = await db_get_alias(session, alias_id)
    if not alias:
        raise LookupError("Alias not found")
    return _alias_to_dict(alias)


async def delete_alias(session: AsyncSession, alias_id: int) -> bool:
    return await db_delete_alias(session, alias_id)


async def list_aliases_by_domain(session: AsyncSession, domain_id: int) -> List[Dict[str, Any]]:
    aliases = await db_list_aliases_by_domain(session, domain_id=domain_id)
    result: List[Dict[str, Any]] = []
    for a in aliases:
        result.append(
            {
                "id": a.id,
                "local_part": a.local_part,
                "targets": a.targets,
                "expires_at": a.expires_at.isoformat() if getattr(a, "expires_at", None) else None,
            }
        )
    return result


async def add_alias(
        session: AsyncSession,
        domain_id: int,
        local_part: str,
        targets: str,
        expires_at_iso: Optional[str] = None,
) -> int:
    exp: Optional[_dt.datetime] = None
    if expires_at_iso:
        exp = _dt.datetime.fromisoformat(expires_at_iso)
    alias = await db_add_alias(
        session, domain_id=domain_id, local_part=local_part, targets=targets, expires_at=exp
    )
    return alias.id


async def test_alias(session: AsyncSession, alias_id: int) -> Dict[str, str]:
    alias = await db_get_alias(session, alias_id)
    if not alias:
        raise LookupError("Alias not found")
    # This is a stubbed operation; just return a message that would be logged/sent
    return {"message": f"Test email sent to {alias.targets}"}
