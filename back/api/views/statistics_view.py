"""Statistics API endpoints for SMTPy v2."""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import func, select, and_, case
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.db import get_async_session
from ..models import Message, Domain, MessageStatus
from ..views.auth_view import get_current_user

router = APIRouter(prefix="/statistics", tags=["statistics"])


@router.get("/overall")
async def get_overall_stats(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(get_current_user)
):
    """Get overall statistics summary."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    organization_id = current_user.get("organization_id")
    # Parse dates
    if date_from:
        start_date = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
    else:
        start_date = datetime.utcnow() - timedelta(days=7)

    if date_to:
        end_date = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
    else:
        end_date = datetime.utcnow()

    # Build base query for user's organization
    base_query = select(Message).join(Domain).where(
        Domain.organization_id == organization_id
    )

    if date_from or date_to:
        base_query = base_query.where(
            and_(
                Message.created_at >= start_date,
                Message.created_at <= end_date
            )
        )

    # Total emails
    total_result = await session.execute(
        select(func.count(Message.id)).select_from(Message).join(Domain).where(
            Domain.organization_id == organization_id
        ).where(
            and_(
                Message.created_at >= start_date,
                Message.created_at <= end_date
            )
        )
    )
    total_emails = total_result.scalar() or 0

    # Emails sent (delivered successfully)
    sent_result = await session.execute(
        select(func.count(Message.id)).select_from(Message).join(Domain).where(
            Domain.organization_id == organization_id,
            Message.status == MessageStatus.DELIVERED
        ).where(
            and_(
                Message.created_at >= start_date,
                Message.created_at <= end_date
            )
        )
    )
    emails_sent = sent_result.scalar() or 0

    # Emails failed
    failed_result = await session.execute(
        select(func.count(Message.id)).select_from(Message).join(Domain).where(
            Domain.organization_id == organization_id,
            Message.status == MessageStatus.FAILED
        ).where(
            and_(
                Message.created_at >= start_date,
                Message.created_at <= end_date
            )
        )
    )
    emails_failed = failed_result.scalar() or 0

    # Active domains count
    domains_result = await session.execute(
        select(func.count(Domain.id)).where(
            Domain.organization_id == organization_id,
            Domain.is_active == True
        )
    )
    active_domains = domains_result.scalar() or 0

    # Active aliases count (unique recipient_email in domains)
    aliases_result = await session.execute(
        select(func.count(func.distinct(Message.recipient_email))).select_from(Message).join(Domain).where(
            Domain.organization_id == organization_id
        )
    )
    active_aliases = aliases_result.scalar() or 0

    # Calculate success rate
    success_rate = (emails_sent / total_emails * 100) if total_emails > 0 else 0

    return {
        "success": True,
        "data": {
            "total_emails": total_emails,
            "emails_sent": emails_sent,
            "emails_failed": emails_failed,
            "active_domains": active_domains,
            "active_aliases": active_aliases,
            "success_rate": round(success_rate, 2),
            "total_size_mb": 0  # TODO: implement if tracking message sizes
        }
    }


@router.get("/time-series")
async def get_time_series(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    granularity: str = Query("day", pattern="^(day|week|month)$"),
    domain_id: Optional[int] = Query(None),
    session: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(get_current_user)
):
    """Get time series data for charts."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    organization_id = current_user.get("organization_id")
    # Parse dates
    if date_from:
        start_date = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
    else:
        start_date = datetime.utcnow() - timedelta(days=7)

    if date_to:
        end_date = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
    else:
        end_date = datetime.utcnow()

    # Generate time series data (simplified - returns daily aggregates)
    time_series = []
    current_date = start_date.date()
    end_date_only = end_date.date()

    while current_date <= end_date_only:
        day_start = datetime.combine(current_date, datetime.min.time())
        day_end = datetime.combine(current_date, datetime.max.time())

        # Count sent emails
        sent_query = select(func.count(Message.id)).select_from(Message).join(Domain).where(
            Domain.organization_id == organization_id,
            Message.status == MessageStatus.DELIVERED,
            and_(
                Message.created_at >= day_start,
                Message.created_at <= day_end
            )
        )
        if domain_id:
            sent_query = sent_query.where(Message.domain_id == domain_id)

        sent_result = await session.execute(sent_query)
        emails_sent = sent_result.scalar() or 0

        # Count failed emails
        failed_query = select(func.count(Message.id)).select_from(Message).join(Domain).where(
            Domain.organization_id == organization_id,
            Message.status == MessageStatus.FAILED,
            and_(
                Message.created_at >= day_start,
                Message.created_at <= day_end
            )
        )
        if domain_id:
            failed_query = failed_query.where(Message.domain_id == domain_id)

        failed_result = await session.execute(failed_query)
        emails_failed = failed_result.scalar() or 0

        total = emails_sent + emails_failed
        success_rate = (emails_sent / total * 100) if total > 0 else 0

        time_series.append({
            "date": current_date.isoformat(),
            "emails_sent": emails_sent,
            "emails_failed": emails_failed,
            "success_rate": round(success_rate, 2)
        })

        current_date += timedelta(days=1)

    return {
        "success": True,
        "data": time_series
    }


@router.get("/top-domains")
async def get_top_domains(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    limit: int = Query(5, ge=1, le=50),
    session: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(get_current_user)
):
    """Get top domains by email count."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    organization_id = current_user.get("organization_id")
    # Parse dates
    if date_from:
        start_date = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
    else:
        start_date = datetime.utcnow() - timedelta(days=30)

    if date_to:
        end_date = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
    else:
        end_date = datetime.utcnow()

    # Query for domain statistics
    query = select(
        Domain.id,
        Domain.name,
        func.count(Message.id).label('email_count'),
        func.sum(case((Message.status == MessageStatus.DELIVERED, 1), else_=0)).label('success_count'),
        func.sum(case((Message.status == MessageStatus.FAILED, 1), else_=0)).label('failure_count')
    ).select_from(Domain).outerjoin(Message).where(
        Domain.organization_id == organization_id
    ).where(
        and_(
            Message.created_at >= start_date,
            Message.created_at <= end_date
        )
    ).group_by(Domain.id, Domain.name).order_by(func.count(Message.id).desc()).limit(limit)

    result = await session.execute(query)
    domains = result.all()

    # Calculate total for percentages
    total_emails = sum(d.email_count for d in domains)

    domain_stats = []
    for domain in domains:
        success_rate = (domain.success_count / domain.email_count * 100) if domain.email_count > 0 else 0
        percentage = (domain.email_count / total_emails * 100) if total_emails > 0 else 0

        domain_stats.append({
            "domain_id": domain.id,
            "domain_name": domain.name,
            "email_count": domain.email_count,
            "success_count": domain.success_count or 0,
            "failure_count": domain.failure_count or 0,
            "success_rate": round(success_rate, 2),
            "percentage_of_total": round(percentage, 2)
        })

    return {
        "success": True,
        "data": domain_stats
    }


@router.get("/top-aliases")
async def get_top_aliases(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    limit: int = Query(5, ge=1, le=50),
    session: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(get_current_user)
):
    """Get top aliases by email count."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    organization_id = current_user.get("organization_id")
    # Parse dates
    if date_from:
        start_date = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
    else:
        start_date = datetime.utcnow() - timedelta(days=30)

    if date_to:
        end_date = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
    else:
        end_date = datetime.utcnow()

    # Query for alias statistics
    query = select(
        Message.recipient_email.label('alias_email'),
        Domain.name,
        Domain.id.label('domain_id'),
        func.count(Message.id).label('email_count'),
        func.max(Message.created_at).label('last_used')
    ).select_from(Message).join(Domain).where(
        Domain.organization_id == organization_id
    ).where(
        and_(
            Message.created_at >= start_date,
            Message.created_at <= end_date
        )
    ).group_by(Message.recipient_email, Domain.name, Domain.id).order_by(
        func.count(Message.id).desc()
    ).limit(limit)

    result = await session.execute(query)
    aliases = result.all()

    alias_stats = []
    for alias in aliases:
        alias_stats.append({
            "alias_id": alias.domain_id,  # Using domain_id as proxy
            "alias_email": alias.alias_email,
            "domain_name": alias.name,
            "email_count": alias.email_count,
            "last_used": alias.last_used.isoformat() if alias.last_used else None
        })

    return {
        "success": True,
        "data": alias_stats
    }


@router.get("")
async def get_statistics(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    granularity: str = Query("day", pattern="^(day|week|month)$"),
    domain_id: Optional[int] = Query(None),
    session: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(get_current_user)
):
    """Get complete statistics with all data."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Get all statistics components
    overall_response = await get_overall_stats(date_from, date_to, session, current_user)
    time_series_response = await get_time_series(date_from, date_to, granularity, domain_id, session, current_user)
    top_domains_response = await get_top_domains(date_from, date_to, 10, session, current_user)
    top_aliases_response = await get_top_aliases(date_from, date_to, 10, session, current_user)

    return {
        "success": True,
        "data": {
            "overall": overall_response["data"],
            "time_series": time_series_response["data"],
            "top_domains": top_domains_response["data"],
            "top_aliases": top_aliases_response["data"]
        }
    }
