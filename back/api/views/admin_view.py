"""Admin view layer for SMTPy v2.

Provides admin-only endpoints for system statistics and management.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr
import stripe
import asyncio
import socket

from shared.core.db import get_db
from shared.core.config import SETTINGS
from .auth_view import get_current_user
from ..schemas.common import ErrorResponse
from shared.models.user import User, UserRole
from shared.models.organization import Organization
from shared.models.domain import Domain
from shared.models.alias import Alias
from shared.models.message import Message, MessageStatus

# Create router
router = APIRouter(prefix="/admin", tags=["admin"])


async def require_admin(current_user: dict = Depends(get_current_user)):
    """Require admin role."""
    if not current_user or current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


@router.get(
    "/stats",
    summary="Get database statistics",
    responses={
        403: {"model": ErrorResponse, "description": "Admin access required"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_database_stats(
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(require_admin)
):
    """Get comprehensive database statistics (admin only)."""
    try:
        now = datetime.utcnow()
        thirty_days_ago = now - timedelta(days=30)
        today_start = datetime(now.year, now.month, now.day)
        week_start = now - timedelta(days=7)
        month_start = datetime(now.year, now.month, 1)

        # User statistics
        users_total = await db.scalar(select(func.count(User.id)))
        users_active = await db.scalar(select(func.count(User.id)).where(User.is_active == True))
        users_admins = await db.scalar(select(func.count(User.id)).where(User.role == UserRole.ADMIN))
        users_recent = await db.scalar(
            select(func.count(User.id)).where(User.created_at >= thirty_days_ago)
        )

        # Organization statistics
        orgs_total = await db.scalar(select(func.count(Organization.id)))
        # Count organizations with active subscriptions (no is_active field in model)
        orgs_active = await db.scalar(
            select(func.count(Organization.id)).where(Organization.stripe_subscription_id.isnot(None))
        )
        orgs_with_sub = await db.scalar(
            select(func.count(Organization.id)).where(Organization.stripe_subscription_id.isnot(None))
        )

        # Domain statistics
        domains_total = await db.scalar(select(func.count(Domain.id)))
        domains_verified = await db.scalar(
            select(func.count(Domain.id)).where(Domain.is_fully_verified == True)
        )
        domains_unverified = await db.scalar(
            select(func.count(Domain.id)).where(Domain.is_fully_verified == False)
        )
        domains_active = await db.scalar(
            select(func.count(Domain.id)).where(Domain.is_active == True)
        )

        # Alias statistics
        aliases_total = await db.scalar(select(func.count(Alias.id)))
        aliases_active = await db.scalar(
            select(func.count(Alias.id)).where(Alias.is_deleted == False)
        )
        aliases_inactive = await db.scalar(
            select(func.count(Alias.id)).where(Alias.is_deleted == True)
        )

        # Message statistics
        messages_total = await db.scalar(select(func.count(Message.id)))
        messages_today = await db.scalar(
            select(func.count(Message.id)).where(Message.created_at >= today_start)
        )
        messages_week = await db.scalar(
            select(func.count(Message.id)).where(Message.created_at >= week_start)
        )
        messages_month = await db.scalar(
            select(func.count(Message.id)).where(Message.created_at >= month_start)
        )
        messages_failed = await db.scalar(
            select(func.count(Message.id)).where(Message.status == MessageStatus.FAILED)
        )

        return {
            "success": True,
            "data": {
                "users": {
                    "total": users_total or 0,
                    "active": users_active or 0,
                    "admins": users_admins or 0,
                    "recent_signups": users_recent or 0
                },
                "organizations": {
                    "total": orgs_total or 0,
                    "active": orgs_active or 0,
                    "with_subscription": orgs_with_sub or 0
                },
                "domains": {
                    "total": domains_total or 0,
                    "verified": domains_verified or 0,
                    "unverified": domains_unverified or 0,
                    "active": domains_active or 0
                },
                "aliases": {
                    "total": aliases_total or 0,
                    "active": aliases_active or 0,
                    "inactive": aliases_inactive or 0
                },
                "messages": {
                    "total": messages_total or 0,
                    "today": messages_today or 0,
                    "this_week": messages_week or 0,
                    "this_month": messages_month or 0,
                    "failed": messages_failed or 0
                }
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch statistics: {str(e)}"
        )


@router.get(
    "/activity",
    summary="Get recent activity",
    responses={
        403: {"model": ErrorResponse, "description": "Admin access required"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_recent_activity(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(require_admin)
):
    """Get recent platform activity (admin only)."""
    try:
        # For now, return recent users and domains as activity
        # In a real implementation, you'd have an activity/audit log table

        recent_users = await db.execute(
            select(User.id, User.username, User.created_at)
            .order_by(User.created_at.desc())
            .limit(limit // 2)
        )

        recent_domains = await db.execute(
            select(Domain.id, Domain.name, Domain.created_at)
            .order_by(Domain.created_at.desc())
            .limit(limit // 2)
        )

        activity = []

        for user in recent_users:
            activity.append({
                "id": user.id,
                "type": "user_signup",
                "description": f"New user registered: {user.username}",
                "timestamp": user.created_at.isoformat() if user.created_at else None,
                "user": user.username
            })

        for domain in recent_domains:
            activity.append({
                "id": domain.id,
                "type": "domain_added",
                "description": f"New domain added: {domain.name}",
                "timestamp": domain.created_at.isoformat() if domain.created_at else None
            })

        # Sort by timestamp
        activity.sort(key=lambda x: x["timestamp"] or "", reverse=True)

        return {
            "success": True,
            "data": activity[:limit]
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch activity: {str(e)}"
        )


async def check_mailserver_port(host: str, port: int, timeout: float = 2.0) -> bool:
    """Check if a mailserver port is accessible."""
    try:
        # Create a socket connection to test the port
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout
        )
        writer.close()
        await writer.wait_closed()
        return True
    except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
        return False


@router.get(
    "/health",
    summary="Get system health",
    responses={
        403: {"model": ErrorResponse, "description": "Admin access required"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_system_health(
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(require_admin)
):
    """Get system health status (admin only)."""
    health_data = {}

    # Check database connection
    try:
        await db.execute(select(1))

        # Get database size (PostgreSQL specific)
        db_size_result = await db.execute(
            select(func.pg_database_size(func.current_database()))
        )
        db_size_bytes = db_size_result.scalar() or 0
        db_size_mb = db_size_bytes / (1024 * 1024)

        # Get connection count
        conn_count_result = await db.execute(
            select(func.count()).select_from(
                select(1).select_from(func.pg_stat_activity()).subquery()
            )
        )
        conn_count = conn_count_result.scalar() or 0

        health_data["database"] = {
            "status": "healthy",
            "connections": conn_count,
            "size": f"{db_size_mb:.2f} MB"
        }
    except Exception as e:
        health_data["database"] = {
            "status": "error",
            "connections": 0,
            "size": "unknown",
            "error": str(e)
        }

    # Check mailserver ports
    mailserver_host = SETTINGS.mailserver_host or "mailserver"
    smtp_port_25 = await check_mailserver_port(mailserver_host, 25)
    smtp_port_587 = await check_mailserver_port(mailserver_host, 587)
    imap_port_143 = await check_mailserver_port(mailserver_host, 143)
    imap_port_993 = await check_mailserver_port(mailserver_host, 993)

    mailserver_healthy = smtp_port_587 and imap_port_143

    health_data["mailserver"] = {
        "status": "healthy" if mailserver_healthy else "degraded",
        "ports": {
            "smtp_25": "up" if smtp_port_25 else "down",
            "smtp_587": "up" if smtp_port_587 else "down",
            "imap_143": "up" if imap_port_143 else "down",
            "imaps_993": "up" if imap_port_993 else "down"
        }
    }

    return {
        "success": True,
        "data": health_data
    }


@router.get(
    "/users",
    summary="Get all users",
    responses={
        403: {"model": ErrorResponse, "description": "Admin access required"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_all_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(require_admin)
):
    """Get all users with pagination (admin only)."""
    try:
        offset = (page - 1) * page_size

        # Get total count
        total_result = await db.execute(select(func.count(User.id)))
        total = total_result.scalar() or 0

        # Get users
        users_result = await db.execute(
            select(User)
            .order_by(User.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        users = users_result.scalars().all()

        return {
            "success": True,
            "data": {
                "items": [user.to_dict() for user in users],
                "total": total,
                "page": page,
                "page_size": page_size
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch users: {str(e)}"
        )


@router.get(
    "/stripe-config",
    summary="Get Stripe configuration status",
    responses={
        403: {"model": ErrorResponse, "description": "Admin access required"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_stripe_config(
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(require_admin)
):
    """Get Stripe configuration status and health check (admin only)."""
    try:
        # Check API Key
        api_key = SETTINGS.STRIPE_API_KEY
        api_key_configured = bool(api_key)

        # Determine mode
        if api_key and api_key.startswith("sk_test_"):
            mode = "test"
            mode_valid = True
        elif api_key and api_key.startswith("sk_live_"):
            mode = "live"
            mode_valid = True
        elif api_key:
            mode = "unknown"
            mode_valid = False
        else:
            mode = "not_configured"
            mode_valid = False

        # Check webhook secret
        webhook_secret = SETTINGS.STRIPE_WEBHOOK_SECRET
        webhook_secret_configured = bool(webhook_secret)

        # Check URLs
        success_url = SETTINGS.STRIPE_SUCCESS_URL
        cancel_url = SETTINGS.STRIPE_CANCEL_URL
        portal_url = SETTINGS.STRIPE_PORTAL_RETURN_URL

        # Test API connection
        connection_status = "not_tested"
        connection_message = ""

        if api_key_configured and mode_valid:
            try:
                # Initialize Stripe with the API key
                stripe.api_key = api_key

                # Make a simple API call to test connectivity
                # This will raise an error if the key is invalid
                account = stripe.Account.retrieve()

                connection_status = "success"
                # Safely extract account name with fallback to account ID
                account_name = account.id
                try:
                    if account.business_profile and account.business_profile.name:
                        account_name = account.business_profile.name
                except (AttributeError, TypeError, KeyError):
                    pass  # Keep using account.id as fallback
                connection_message = f"Connected to Stripe account: {account_name}"
            except stripe.error.AuthenticationError as e:
                connection_status = "error"
                connection_message = f"Authentication failed: {str(e)}"
            except stripe.error.StripeError as e:
                connection_status = "error"
                connection_message = f"Stripe API error: {str(e)}"
            except Exception as e:
                connection_status = "error"
                connection_message = f"Connection test failed: {str(e)}"
        else:
            connection_status = "skipped"
            connection_message = "API key not configured or invalid"

        # Get recent webhook events count (if configured)
        recent_events_count = 0
        if api_key_configured and mode_valid:
            try:
                # Get events from last 24 hours
                events = stripe.Event.list(limit=100)
                recent_events_count = len(events.data)
            except:
                recent_events_count = 0

        # Count organizations with Stripe customers
        orgs_with_stripe = await db.scalar(
            select(func.count(Organization.id)).where(Organization.stripe_customer_id.isnot(None))
        )

        # Count active subscriptions
        orgs_with_subscriptions = await db.scalar(
            select(func.count(Organization.id)).where(Organization.stripe_subscription_id.isnot(None))
        )

        return {
            "success": True,
            "data": {
                "api_key": {
                    "configured": api_key_configured,
                    "mode": mode,
                    "valid_format": mode_valid,
                    "masked_value": f"{api_key[:10]}...{api_key[-4:]}" if api_key and len(api_key) > 14 else None
                },
                "webhook": {
                    "secret_configured": webhook_secret_configured,
                    "masked_value": f"{webhook_secret[:10]}...{webhook_secret[-4:]}" if webhook_secret and len(webhook_secret) > 14 else None
                },
                "urls": {
                    "success_url": success_url,
                    "cancel_url": cancel_url,
                    "portal_return_url": portal_url
                },
                "connection": {
                    "status": connection_status,
                    "message": connection_message
                },
                "statistics": {
                    "organizations_with_stripe": orgs_with_stripe or 0,
                    "active_subscriptions": orgs_with_subscriptions or 0,
                    "recent_events": recent_events_count
                }
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch Stripe configuration: {str(e)}"
        )
