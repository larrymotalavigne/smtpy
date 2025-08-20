"""Main controller for core application functionality."""

import logging
import secrets
from datetime import datetime, timedelta, UTC
from typing import Dict, Any, List, Optional

from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database.models import User, Domain, Alias, Invitation, ActivityLog
from core.utils.db import get_sync_db
from core.utils.user import hash_password, verify_password
from core.utils.validation import ValidationError


def log_activity(event_type: str, data: Dict[str, Any]) -> None:
    """Log activity to the database."""
    try:
        with get_sync_db() as session:
            log_entry = ActivityLog(
                event_type=event_type,
                timestamp=datetime.now(UTC),
                message=str(data)
            )
            session.add(log_entry)
            session.commit()
    except Exception as e:
        logging.error(f"Failed to log activity: {e}")


def get_by_id_or_404(session: Session, model_class, object_id: int) -> Any:
    """Get object by ID or raise error if not found."""
    obj = session.get(model_class, object_id)
    if not obj:
        raise ValueError(f"{model_class.__name__} not found")
    return obj


def create_invitation(admin_user_id: int, email: str) -> Dict[str, Any]:
    """Create an invitation for a new user.

    Args:
        admin_user_id: ID of the admin creating the invitation
        email: Email address to invite

    Returns:
        Dictionary containing invitation results

    Raises:
        PermissionError: If user is not admin
        ValidationError: If email already registered or invitation exists
    """
    try:
        with get_sync_db() as session:
            # Verify admin user
            admin_user = get_by_id_or_404(session, User, admin_user_id)
            if admin_user.role != "admin":
                raise PermissionError("Admin access required")

            # Check if email already registered
            if session.query(User).filter_by(email=email).first():
                raise ValidationError("Email already registered")

            # Check if invitation already exists
            existing_invitation = session.query(Invitation).filter_by(email=email).first()
            if existing_invitation and existing_invitation.expires_at > datetime.now(UTC):
                raise ValidationError("Invitation already sent")

            # Create invitation
            token = secrets.token_urlsafe(32)
            expires = datetime.now(UTC) + timedelta(hours=24)
            invitation = Invitation(
                email=email, token=token, expires_at=expires, invited_by=admin_user_id
            )
            session.add(invitation)
            session.commit()

            log_activity(
                "invitation_created", {"email": email, "invited_by": admin_user_id, "token": token}
            )

            return {"success": True, "message": "Invitation sent", "token": token, "email": email}

    except (PermissionError, ValidationError):
        raise
    except Exception as e:
        logging.error(f"Failed to create invitation for {email}: {e}")
        raise


def register_user(username: str, password: str, email: str = "", invite_token: str = "") -> Dict[str, Any]:
    """Register a new user.

    Args:
        username: Username for the new user
        password: Password for the new user
        email: Email address (optional)
        invite_token: Invitation token (optional)

    Returns:
        Dictionary containing registration results

    Raises:
        ValidationError: If validation fails
    """
    try:
        email_val = email if email else None
        invite_val = invite_token if invite_token else None

        with get_sync_db() as session:
            # Handle invitation
            invitation = None
            if invite_val:
                invitation = session.query(Invitation).filter_by(token=invite_val).first()
                if not invitation or invitation.expires_at < datetime.now(UTC):
                    raise ValidationError("Invalid or expired invitation")
                email_val = invitation.email

            # Check if username exists
            if session.query(User).filter_by(username=username).first():
                raise ValidationError("Username already exists")

            # Check if email exists
            if email_val and session.query(User).filter_by(email=email_val).first():
                raise ValidationError("Email already registered")

            # Create user
            verification_token = None if invite_val else secrets.token_urlsafe(32)
            user = User(
                username=username,
                email=email_val,
                hashed_password=hash_password(password),
                is_active=bool(invite_val),  # Active if invited
                email_verified=bool(invite_val),  # Verified if invited
                verification_token=verification_token,
            )
            session.add(user)

            # Delete invitation if used
            if invitation:
                session.delete(invitation)

            session.commit()

            log_activity(
                "user_registered",
                {
                    "user_id": user.id,
                    "username": username,
                    "email": email_val,
                    "invited": bool(invite_val),
                },
            )

            result = {
                "success": True,
                "user_id": user.id,
                "username": username,
                "requires_verification": not bool(invite_val),
            }

            # Send verification email if needed
            if email_val and not invite_val:
                result["verification_token"] = verification_token
                result["message"] = "Check your email to verify your account"
            else:
                result["message"] = "Account created. You can now log in"

            return result

    except ValidationError:
        raise
    except Exception as e:
        logging.error(f"Failed to register user {username}: {e}")
        raise


def verify_email(token: str) -> Dict[str, Any]:
    """Verify a user's email address.

    Args:
        token: Email verification token

    Returns:
        Dictionary containing verification results

    Raises:
        ValidationError: If token is invalid or expired
    """
    try:
        with get_sync_db() as session:
            user = session.query(User).filter_by(verification_token=token).first()
            if not user:
                raise ValidationError("Invalid verification token")

            user.email_verified = True
            user.is_active = True
            user.verification_token = None
            session.commit()

            log_activity("email_verified", {"user_id": user.id, "username": user.username})

            return {"success": True, "message": "Email verified successfully"}

    except ValidationError:
        raise
    except Exception as e:
        logging.error(f"Failed to verify email with token {token}: {e}")
        raise


def authenticate_user(username: str, password: str) -> Dict[str, Any]:
    """Authenticate a user.

    Args:
        username: Username to authenticate
        password: Password to verify

    Returns:
        Dictionary containing authentication results

    Raises:
        ValidationError: If authentication fails
    """
    try:
        with get_sync_db() as session:
            user = session.query(User).filter_by(username=username).first()
            if not user or not verify_password(password, user.hashed_password):
                raise ValidationError("Invalid username or password")

            if not user.is_active:
                raise ValidationError("Account is not active")

            log_activity("user_login", {"user_id": user.id, "username": username})

            return {
                "success": True,
                "user_id": user.id,
                "username": user.username,
                "role": user.role,
                "email": user.email,
            }

    except ValidationError:
        raise
    except Exception as e:
        logging.error(f"Failed to authenticate user {username}: {e}")
        raise


def get_dashboard_data(user_id: int) -> Dict[str, Any]:
    """Get dashboard data for a user.

    Args:
        user_id: ID of the user

    Returns:
        Dictionary containing dashboard data
    """
    try:
        with get_sync_db() as session:
            user = get_by_id_or_404(session, User, user_id)
            
            # Get user's domains
            domains = session.query(Domain).filter_by(owner_id=user_id, is_deleted=False).all()
            
            # Get user's aliases
            aliases = session.query(Alias).filter_by(owner_id=user_id, is_deleted=False).all()
            
            # Get recent activity
            recent_activity = (
                session.query(ActivityLog)
                .filter(ActivityLog.message.contains(f'"user_id": {user_id}'))
                .order_by(ActivityLog.timestamp.desc())
                .limit(10)
                .all()
            )

            return {
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                },
                "domains": [
                    {
                        "id": domain.id,
                        "name": domain.name,
                        "catch_all": domain.catch_all,
                        "created_at": domain.created_at,
                    }
                    for domain in domains
                ],
                "aliases": [
                    {
                        "id": alias.id,
                        "local_part": alias.local_part,
                        "domain": alias.domain.name,
                        "targets": alias.targets,
                        "expires_at": alias.expires_at,
                    }
                    for alias in aliases
                ],
                "recent_activity": [
                    {
                        "timestamp": activity.timestamp,
                        "event_type": activity.event_type,
                        "message": activity.message,
                    }
                    for activity in recent_activity
                ],
            }

    except Exception as e:
        logging.error(f"Failed to get dashboard data for user {user_id}: {e}")
        raise


def get_admin_panel_data(user_id: int) -> Dict[str, Any]:
    """Get admin panel data.

    Args:
        user_id: ID of the admin user

    Returns:
        Dictionary containing admin panel data

    Raises:
        PermissionError: If user is not admin
    """
    try:
        with get_sync_db() as session:
            admin_user = get_by_id_or_404(session, User, user_id)
            if admin_user.role != "admin":
                raise PermissionError("Admin access required")

            # Get all users
            users = session.query(User).filter_by(is_deleted=False).all()
            
            # Get all domains
            domains = session.query(Domain).filter_by(is_deleted=False).all()
            
            # Get all aliases
            aliases = session.query(Alias).filter_by(is_deleted=False).all()
            
            # Get recent activity
            recent_activity = (
                session.query(ActivityLog)
                .order_by(ActivityLog.timestamp.desc())
                .limit(20)
                .all()
            )

            return {
                "users": [
                    {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "role": user.role,
                        "is_active": user.is_active,
                        "created_at": user.created_at,
                    }
                    for user in users
                ],
                "domains": [
                    {
                        "id": domain.id,
                        "name": domain.name,
                        "owner": domain.owner.username,
                        "created_at": domain.created_at,
                    }
                    for domain in domains
                ],
                "aliases": [
                    {
                        "id": alias.id,
                        "local_part": alias.local_part,
                        "domain": alias.domain.name,
                        "owner": alias.owner.username,
                        "targets": alias.targets,
                        "created_at": alias.created_at,
                    }
                    for alias in aliases
                ],
                "recent_activity": [
                    {
                        "timestamp": activity.timestamp,
                        "event_type": activity.event_type,
                        "message": activity.message,
                    }
                    for activity in recent_activity
                ],
            }

    except PermissionError:
        raise
    except Exception as e:
        logging.error(f"Failed to get admin panel data for user {user_id}: {e}")
        raise


def get_users_list(admin_user_id: int) -> List[Dict[str, Any]]:
    """Get list of all users (admin only).

    Args:
        admin_user_id: ID of the admin user

    Returns:
        List of user dictionaries

    Raises:
        PermissionError: If user is not admin
    """
    try:
        with get_sync_db() as session:
            admin_user = get_by_id_or_404(session, User, admin_user_id)
            if admin_user.role != "admin":
                raise PermissionError("Admin access required")

            users = session.query(User).filter_by(is_deleted=False).all()
            return [
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                    "is_active": user.is_active,
                    "email_verified": user.email_verified,
                    "created_at": user.created_at,
                }
                for user in users
            ]

    except PermissionError:
        raise
    except Exception as e:
        logging.error(f"Failed to get users list for admin {admin_user_id}: {e}")
        raise


def get_dkim_public_key(domain: str) -> Dict[str, Any]:
    """Get DKIM public key for a domain.

    Args:
        domain: Domain name

    Returns:
        Dictionary containing DKIM public key information
    """
    try:
        # This is a placeholder - actual DKIM implementation would be more complex
        return {
            "domain": domain,
            "dkim_public_key": "Not configured",
            "message": f"DKIM public key for {domain} not found or not configured",
        }
    except Exception as e:
        logging.error(f"Failed to get DKIM public key for domain {domain}: {e}")
        raise


def get_domain_dns_info(domain_id: int, user_id: int) -> Dict[str, Any]:
    """Get DNS information for a domain.

    Args:
        domain_id: ID of the domain
        user_id: ID of the user (for permission check)

    Returns:
        Dictionary containing DNS information

    Raises:
        PermissionError: If user doesn't own the domain
    """
    try:
        with get_sync_db() as session:
            domain = get_by_id_or_404(session, Domain, domain_id)
            
            # Check permission (user must own domain or be admin)
            user = get_by_id_or_404(session, User, user_id)
            if domain.owner_id != user_id and user.role != "admin":
                raise PermissionError("Access denied")

            return {
                "domain": domain.name,
                "mx_record": f"10 mail.{domain.name}",
                "spf_record": f"v=spf1 mx include:_{domain.name} ~all",
                "dkim_record": f"v=DKIM1; k=rsa; p=...",
                "dmarc_record": "v=DMARC1; p=quarantine; rua=mailto:dmarc@{domain.name}",
            }

    except PermissionError:
        raise
    except Exception as e:
        logging.error(f"Failed to get DNS info for domain {domain_id}: {e}")
        raise


def get_domain_aliases_info(domain_id: int, user_id: int) -> Dict[str, Any]:
    """Get aliases information for a domain.

    Args:
        domain_id: ID of the domain
        user_id: ID of the user (for permission check)

    Returns:
        Dictionary containing domain and aliases information

    Raises:
        PermissionError: If user doesn't own the domain
    """
    try:
        with get_sync_db() as session:
            domain = get_by_id_or_404(session, Domain, domain_id)
            
            # Check permission (user must own domain or be admin)
            user = get_by_id_or_404(session, User, user_id)
            if domain.owner_id != user_id and user.role != "admin":
                raise PermissionError("Access denied")

            aliases = session.query(Alias).filter_by(domain_id=domain_id, is_deleted=False).all()

            return {
                "domain": {
                    "id": domain.id,
                    "name": domain.name,
                    "catch_all": domain.catch_all,
                },
                "aliases": [
                    {
                        "id": alias.id,
                        "local_part": alias.local_part,
                        "targets": alias.targets,
                        "expires_at": alias.expires_at,
                        "created_at": alias.created_at,
                    }
                    for alias in aliases
                ],
            }

    except PermissionError:
        raise
    except Exception as e:
        logging.error(f"Failed to get aliases info for domain {domain_id}: {e}")
        raise


def check_health() -> Dict[str, Any]:
    """Check application health.

    Returns:
        Dictionary containing health status
    """
    try:
        # Basic health check - can be expanded
        with get_sync_db() as session:
            # Test database connection
            session.execute(select(1))
            
        return {"status": "healthy", "timestamp": datetime.now(UTC)}
    except Exception as e:
        logging.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e), "timestamp": datetime.now(UTC)}


def check_readiness() -> Dict[str, Any]:
    """Check application readiness.

    Returns:
        Dictionary containing readiness status
    """
    try:
        # Check database and other dependencies
        with get_sync_db() as session:
            # Test database connection
            session.execute(select(1))
            
            # Check if admin user exists
            admin_exists = session.query(User).filter_by(role="admin").first() is not None
            
        return {
            "status": "ready" if admin_exists else "not_ready",
            "database": "connected",
            "admin_user": "exists" if admin_exists else "missing",
            "timestamp": datetime.now(UTC),
        }
    except Exception as e:
        logging.error(f"Readiness check failed: {e}")
        return {"status": "not_ready", "error": str(e), "timestamp": datetime.now(UTC)}


def get_activity_stats() -> Dict[str, Any]:
    """Get activity statistics.

    Returns:
        Dictionary containing activity statistics
    """
    try:
        with get_sync_db() as session:
            # Get activity counts by event type
            activity_counts = {}
            activities = session.query(ActivityLog).all()
            
            for activity in activities:
                event_type = activity.event_type
                activity_counts[event_type] = activity_counts.get(event_type, 0) + 1
            
            # Get recent activity (last 24 hours)
            yesterday = datetime.now(UTC) - timedelta(days=1)
            recent_activities = (
                session.query(ActivityLog)
                .filter(ActivityLog.timestamp >= yesterday)
                .count()
            )

            return {
                "total_activities": len(activities),
                "activity_counts": activity_counts,
                "recent_activities_24h": recent_activities,
                "timestamp": datetime.now(UTC),
            }

    except Exception as e:
        logging.error(f"Failed to get activity stats: {e}")
        raise


def edit_user(admin_user_id: int, user_id: int, email: str, role: str) -> Dict[str, Any]:
    """Edit user information (admin only).

    Args:
        admin_user_id: ID of the admin user
        user_id: ID of the user to edit
        email: New email address
        role: New role

    Returns:
        Dictionary containing edit results

    Raises:
        PermissionError: If user is not admin
        ValidationError: If validation fails
    """
    try:
        with get_sync_db() as session:
            # Verify admin user
            admin_user = get_by_id_or_404(session, User, admin_user_id)
            if admin_user.role != "admin":
                raise PermissionError("Admin access required")

            # Get user to edit
            user = get_by_id_or_404(session, User, user_id)

            # Validate role
            if role not in ["user", "admin"]:
                raise ValidationError("Invalid role")

            # Check if email is already taken by another user
            if email and email != user.email:
                existing_user = session.query(User).filter_by(email=email).first()
                if existing_user and existing_user.id != user_id:
                    raise ValidationError("Email already taken")

            # Update user
            if email:
                user.email = email
            user.role = role
            session.commit()

            log_activity(
                "user_edited",
                {
                    "admin_user_id": admin_user_id,
                    "edited_user_id": user_id,
                    "new_email": email,
                    "new_role": role,
                },
            )

            return {"success": True, "message": "User updated successfully"}

    except (PermissionError, ValidationError):
        raise
    except Exception as e:
        logging.error(f"Failed to edit user {user_id}: {e}")
        raise


# Async versions for compatibility
async def invite_user_simple(session: AsyncSession, email: str, invited_by_id: int) -> Dict[str, Any]:
    """Simple async invitation function."""
    return create_invitation(invited_by_id, email)


async def register_user_simple(
    session: AsyncSession,
    username: str,
    password: str,
    email: Optional[str] = None,
    invite_token: Optional[str] = None,
) -> Dict[str, Any]:
    """Simple async registration function."""
    return register_user(username, password, email or "", invite_token or "")


async def verify_email_simple(session: AsyncSession, token: str) -> Dict[str, Any]:
    """Simple async email verification function."""
    return verify_email(token)


async def authenticate_simple(session: AsyncSession, username: str, password: str) -> Dict[str, Any]:
    """Simple async authentication function."""
    return authenticate_user(username, password)


# Sync versions for compatibility
def invite_user_simple_sync(session: Session, email: str, invited_by_id: int) -> Dict[str, Any]:
    """Simple sync invitation function."""
    return create_invitation(invited_by_id, email)


def register_user_simple_sync(
    session: Session,
    username: str,
    password: str,
    email: Optional[str],
    invite_token: Optional[str],
) -> Dict[str, Any]:
    """Simple sync registration function."""
    return register_user(username, password, email or "", invite_token or "")


def verify_email_simple_sync(session: Session, token: str) -> Dict[str, Any]:
    """Simple sync email verification function."""
    return verify_email(token)


def authenticate_simple_sync(session: Session, username: str, password: str) -> Dict[str, Any]:
    """Simple sync authentication function."""
    return authenticate_user(username, password)