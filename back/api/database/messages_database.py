"""Message database operations for SMTPy v2."""

from datetime import datetime
from typing import Optional

from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.models.message import Message, MessageStatus
from shared.models.domain import Domain


async def create_message(
    db: AsyncSession,
    message_id: str,
    domain_id: int,
    sender_email: str,
    recipient_email: str,
    subject: Optional[str] = None,
    body_preview: Optional[str] = None,
    size_bytes: Optional[int] = None,
    has_attachments: bool = False,
    thread_id: Optional[str] = None
) -> Message:
    """Create a new message record."""
    message = Message(
        message_id=message_id,
        domain_id=domain_id,
        sender_email=sender_email.lower().strip(),
        recipient_email=recipient_email.lower().strip(),
        subject=subject,
        body_preview=body_preview,
        size_bytes=size_bytes,
        has_attachments=has_attachments,
        thread_id=thread_id,
        status=MessageStatus.PENDING
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


async def get_message_by_id(db: AsyncSession, message_id: int) -> Optional[Message]:
    """Get message by ID."""
    stmt = (
        select(Message)
        .options(selectinload(Message.domain))
        .where(Message.id == message_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_message_by_message_id(db: AsyncSession, message_id: str) -> Optional[Message]:
    """Get message by unique message ID."""
    stmt = (
        select(Message)
        .options(selectinload(Message.domain))
        .where(Message.message_id == message_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_messages_by_organization(
    db: AsyncSession,
    organization_id: int,
    skip: int = 0,
    limit: int = 20,
    status: Optional[MessageStatus] = None,
    domain_id: Optional[int] = None,
    sender_email: Optional[str] = None,
    recipient_email: Optional[str] = None,
    has_attachments: Optional[bool] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None
) -> list[Message]:
    """Get messages for an organization with filtering and pagination."""
    stmt = (
        select(Message)
        .join(Domain, Message.domain_id == Domain.id)
        .options(selectinload(Message.domain))
        .where(Domain.organization_id == organization_id)
    )
    
    # Apply filters
    if status:
        stmt = stmt.where(Message.status == status)
    if domain_id:
        stmt = stmt.where(Message.domain_id == domain_id)
    if sender_email:
        stmt = stmt.where(Message.sender_email.ilike(f"%{sender_email}%"))
    if recipient_email:
        stmt = stmt.where(Message.recipient_email.ilike(f"%{recipient_email}%"))
    if has_attachments is not None:
        stmt = stmt.where(Message.has_attachments == has_attachments)
    if date_from:
        stmt = stmt.where(Message.created_at >= date_from)
    if date_to:
        stmt = stmt.where(Message.created_at <= date_to)
    
    stmt = stmt.order_by(Message.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def count_messages_by_organization(
    db: AsyncSession,
    organization_id: int,
    status: Optional[MessageStatus] = None,
    domain_id: Optional[int] = None,
    sender_email: Optional[str] = None,
    recipient_email: Optional[str] = None,
    has_attachments: Optional[bool] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None
) -> int:
    """Count messages for an organization with filtering."""
    stmt = (
        select(func.count(Message.id))
        .join(Domain, Message.domain_id == Domain.id)
        .where(Domain.organization_id == organization_id)
    )
    
    # Apply same filters as get_messages_by_organization
    if status:
        stmt = stmt.where(Message.status == status)
    if domain_id:
        stmt = stmt.where(Message.domain_id == domain_id)
    if sender_email:
        stmt = stmt.where(Message.sender_email.ilike(f"%{sender_email}%"))
    if recipient_email:
        stmt = stmt.where(Message.recipient_email.ilike(f"%{recipient_email}%"))
    if has_attachments is not None:
        stmt = stmt.where(Message.has_attachments == has_attachments)
    if date_from:
        stmt = stmt.where(Message.created_at >= date_from)
    if date_to:
        stmt = stmt.where(Message.created_at <= date_to)
    
    result = await db.execute(stmt)
    return result.scalar() or 0


async def get_messages_by_domain(
    db: AsyncSession,
    domain_id: int,
    skip: int = 0,
    limit: int = 20
) -> list[Message]:
    """Get messages for a specific domain."""
    stmt = (
        select(Message)
        .options(selectinload(Message.domain))
        .where(Message.domain_id == domain_id)
        .order_by(Message.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_message_status(
    db: AsyncSession,
    message_id: int,
    status: MessageStatus,
    forwarded_to: Optional[str] = None,
    error_message: Optional[str] = None
) -> Optional[Message]:
    """Update message processing status."""
    updates = {"status": status}
    if forwarded_to:
        updates["forwarded_to"] = forwarded_to.lower().strip()
    if error_message:
        updates["error_message"] = error_message
    
    stmt = (
        update(Message)
        .where(Message.id == message_id)
        .values(**updates)
        .returning(Message)
    )
    result = await db.execute(stmt)
    await db.commit()
    updated_message = result.scalar_one_or_none()
    if updated_message:
        await db.refresh(updated_message)
    return updated_message


async def delete_message(db: AsyncSession, message_id: int) -> bool:
    """Delete a message."""
    stmt = delete(Message).where(Message.id == message_id)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0


async def get_message_stats_by_organization(
    db: AsyncSession,
    organization_id: int,
    since_date: Optional[datetime] = None
) -> dict:
    """Get message statistics for an organization."""
    # Base query joining with domains
    base_stmt = (
        select(Message)
        .join(Domain, Message.domain_id == Domain.id)
        .where(Domain.organization_id == organization_id)
    )
    
    if since_date:
        base_stmt = base_stmt.where(Message.created_at >= since_date)
    
    # Total messages
    total_stmt = select(func.count()).select_from(base_stmt.subquery())
    total_result = await db.execute(total_stmt)
    total_messages = total_result.scalar() or 0
    
    # Messages by status
    status_stats = {}
    for status in MessageStatus:
        status_stmt = (
            select(func.count(Message.id))
            .join(Domain, Message.domain_id == Domain.id)
            .where(
                Domain.organization_id == organization_id,
                Message.status == status
            )
        )
        if since_date:
            status_stmt = status_stmt.where(Message.created_at >= since_date)
        
        status_result = await db.execute(status_stmt)
        status_stats[status.value] = status_result.scalar() or 0
    
    # Total size
    size_stmt = (
        select(func.sum(Message.size_bytes))
        .join(Domain, Message.domain_id == Domain.id)
        .where(Domain.organization_id == organization_id)
    )
    if since_date:
        size_stmt = size_stmt.where(Message.created_at >= since_date)
    
    size_result = await db.execute(size_stmt)
    total_size_bytes = size_result.scalar() or 0
    
    return {
        "total_messages": total_messages,
        "delivered_messages": status_stats.get("delivered", 0),
        "failed_messages": status_stats.get("failed", 0) + status_stats.get("bounced", 0) + status_stats.get("rejected", 0),
        "pending_messages": status_stats.get("pending", 0) + status_stats.get("processing", 0),
        "total_size_bytes": total_size_bytes,
        "status_breakdown": status_stats
    }


async def get_messages_by_thread(
    db: AsyncSession,
    thread_id: str,
    organization_id: Optional[int] = None
) -> list[Message]:
    """Get messages in a thread."""
    stmt = (
        select(Message)
        .options(selectinload(Message.domain))
        .where(Message.thread_id == thread_id)
    )
    
    if organization_id:
        stmt = stmt.join(Domain, Message.domain_id == Domain.id).where(
            Domain.organization_id == organization_id
        )
    
    stmt = stmt.order_by(Message.created_at.asc())
    
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def search_messages(
    db: AsyncSession,
    organization_id: int,
    search_term: str,
    skip: int = 0,
    limit: int = 20
) -> list[Message]:
    """Search messages by subject, sender, or recipient."""
    search_pattern = f"%{search_term}%"
    
    stmt = (
        select(Message)
        .join(Domain, Message.domain_id == Domain.id)
        .options(selectinload(Message.domain))
        .where(
            Domain.organization_id == organization_id,
            or_(
                Message.subject.ilike(search_pattern),
                Message.sender_email.ilike(search_pattern),
                Message.recipient_email.ilike(search_pattern),
                Message.forwarded_to.ilike(search_pattern)
            )
        )
        .order_by(Message.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_recent_messages_by_organization(
    db: AsyncSession,
    organization_id: int,
    limit: int = 10
) -> list[Message]:
    """Get most recent messages for an organization."""
    stmt = (
        select(Message)
        .join(Domain, Message.domain_id == Domain.id)
        .options(selectinload(Message.domain))
        .where(Domain.organization_id == organization_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())