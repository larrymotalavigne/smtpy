"""Messages controller for SMTPy v2."""

from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.message import MessageStatus
from ..database import messages_database
from ..schemas.common import PaginatedResponse
from ..schemas.message import (
    MessageResponse,
    MessageList,
    MessageStats,
    MessageFilter
)


async def list_messages(
    db: AsyncSession,
    organization_id: int,
    page: int = 1,
    page_size: int = 20,
    filters: Optional[MessageFilter] = None
) -> PaginatedResponse:
    """List messages for an organization with pagination and filtering."""
    skip = (page - 1) * page_size
    
    # Parse date filters
    date_from = None
    date_to = None
    if filters:
        if filters.date_from:
            try:
                date_from = datetime.fromisoformat(filters.date_from)
            except ValueError:
                pass  # Invalid date format, ignore
        if filters.date_to:
            try:
                date_to = datetime.fromisoformat(filters.date_to)
            except ValueError:
                pass  # Invalid date format, ignore
    
    # Get messages and count
    messages = await messages_database.get_messages_by_organization(
        db=db,
        organization_id=organization_id,
        skip=skip,
        limit=page_size,
        status=filters.status if filters else None,
        domain_id=filters.domain_id if filters else None,
        sender_email=filters.sender_email if filters else None,
        recipient_email=filters.recipient_email if filters else None,
        has_attachments=filters.has_attachments if filters else None,
        date_from=date_from,
        date_to=date_to
    )
    
    total = await messages_database.count_messages_by_organization(
        db=db,
        organization_id=organization_id,
        status=filters.status if filters else None,
        domain_id=filters.domain_id if filters else None,
        sender_email=filters.sender_email if filters else None,
        recipient_email=filters.recipient_email if filters else None,
        has_attachments=filters.has_attachments if filters else None,
        date_from=date_from,
        date_to=date_to
    )
    
    # Convert to response schemas
    message_responses = [MessageList.model_validate(message) for message in messages]
    
    return PaginatedResponse.create(
        items=message_responses,
        total=total,
        page=page,
        page_size=page_size
    )


async def get_message(
    db: AsyncSession,
    message_id: int,
    organization_id: int
) -> Optional[MessageResponse]:
    """Get a specific message if it belongs to the organization."""
    message = await messages_database.get_message_by_id(db, message_id)
    
    if not message or message.domain.organization_id != organization_id:
        return None
    
    return MessageResponse.model_validate(message)


async def search_messages(
    db: AsyncSession,
    organization_id: int,
    search_term: str,
    page: int = 1,
    page_size: int = 20
) -> PaginatedResponse:
    """Search messages by subject, sender, or recipient."""
    if not search_term.strip():
        # Return empty results for empty search term
        return PaginatedResponse.create(
            items=[],
            total=0,
            page=page,
            page_size=page_size
        )
    
    skip = (page - 1) * page_size
    
    # Get search results
    messages = await messages_database.search_messages(
        db=db,
        organization_id=organization_id,
        search_term=search_term.strip(),
        skip=skip,
        limit=page_size
    )
    
    # For simplicity, we'll get a rough count by querying without pagination
    # In a production system, you might want to implement a proper count query
    all_results = await messages_database.search_messages(
        db=db,
        organization_id=organization_id,
        search_term=search_term.strip(),
        skip=0,
        limit=1000  # Reasonable limit for counting
    )
    total = len(all_results)
    
    # Convert to response schemas
    message_responses = [MessageList.model_validate(message) for message in messages]
    
    return PaginatedResponse.create(
        items=message_responses,
        total=total,
        page=page,
        page_size=page_size
    )


async def get_message_statistics(
    db: AsyncSession,
    organization_id: int,
    since_date: Optional[datetime] = None
) -> MessageStats:
    """Get message statistics for an organization."""
    stats_data = await messages_database.get_message_stats_by_organization(
        db=db,
        organization_id=organization_id,
        since_date=since_date
    )
    
    return MessageStats(
        total_messages=stats_data["total_messages"],
        delivered_messages=stats_data["delivered_messages"],
        failed_messages=stats_data["failed_messages"],
        pending_messages=stats_data["pending_messages"],
        total_size_bytes=stats_data["total_size_bytes"]
    )


async def get_recent_messages(
    db: AsyncSession,
    organization_id: int,
    limit: int = 10
) -> list[MessageList]:
    """Get most recent messages for an organization."""
    messages = await messages_database.get_recent_messages_by_organization(
        db=db,
        organization_id=organization_id,
        limit=limit
    )
    
    return [MessageList.model_validate(message) for message in messages]


async def get_messages_by_domain(
    db: AsyncSession,
    domain_id: int,
    organization_id: int,
    page: int = 1,
    page_size: int = 20
) -> Optional[PaginatedResponse]:
    """Get messages for a specific domain if it belongs to the organization."""
    # First verify the domain belongs to the organization
    from ..database import domains_database
    domain = await domains_database.get_domain_by_id(db, domain_id)
    if not domain or domain.organization_id != organization_id:
        return None
    
    skip = (page - 1) * page_size
    
    # Get messages for the domain
    messages = await messages_database.get_messages_by_domain(
        db=db,
        domain_id=domain_id,
        skip=skip,
        limit=page_size
    )
    
    # Get total count by filtering organization messages by domain
    total = await messages_database.count_messages_by_organization(
        db=db,
        organization_id=organization_id,
        domain_id=domain_id
    )
    
    # Convert to response schemas
    message_responses = [MessageList.model_validate(message) for message in messages]
    
    return PaginatedResponse.create(
        items=message_responses,
        total=total,
        page=page,
        page_size=page_size
    )


async def get_messages_by_thread(
    db: AsyncSession,
    thread_id: str,
    organization_id: int
) -> list[MessageResponse]:
    """Get all messages in a thread for an organization."""
    messages = await messages_database.get_messages_by_thread(
        db=db,
        thread_id=thread_id,
        organization_id=organization_id
    )
    
    return [MessageResponse.model_validate(message) for message in messages]


async def update_message_status(
    db: AsyncSession,
    message_id: int,
    organization_id: int,
    status: MessageStatus,
    forwarded_to: Optional[str] = None,
    error_message: Optional[str] = None
) -> Optional[MessageResponse]:
    """Update message status if the message belongs to the organization."""
    # First check if message belongs to organization
    message = await messages_database.get_message_by_id(db, message_id)
    if not message or message.domain.organization_id != organization_id:
        return None
    
    # Update the message
    updated_message = await messages_database.update_message_status(
        db=db,
        message_id=message_id,
        status=status,
        forwarded_to=forwarded_to,
        error_message=error_message
    )
    
    if not updated_message:
        return None
    
    return MessageResponse.model_validate(updated_message)


async def delete_message(
    db: AsyncSession,
    message_id: int,
    organization_id: int
) -> bool:
    """Delete a message if it belongs to the organization."""
    # First check if message belongs to organization
    message = await messages_database.get_message_by_id(db, message_id)
    if not message or message.domain.organization_id != organization_id:
        return False
    
    return await messages_database.delete_message(db, message_id)


async def create_message(
    db: AsyncSession,
    message_id: str,
    domain_id: int,
    organization_id: int,
    sender_email: str,
    recipient_email: str,
    subject: Optional[str] = None,
    body_preview: Optional[str] = None,
    size_bytes: Optional[int] = None,
    has_attachments: bool = False,
    thread_id: Optional[str] = None
) -> Optional[MessageResponse]:
    """Create a new message if the domain belongs to the organization."""
    # First verify the domain belongs to the organization
    from ..database import domains_database
    domain = await domains_database.get_domain_by_id(db, domain_id)
    if not domain or domain.organization_id != organization_id:
        return None
    
    # Check if message already exists
    existing_message = await messages_database.get_message_by_message_id(db, message_id)
    if existing_message:
        return MessageResponse.model_validate(existing_message)
    
    # Create the message
    message = await messages_database.create_message(
        db=db,
        message_id=message_id,
        domain_id=domain_id,
        sender_email=sender_email,
        recipient_email=recipient_email,
        subject=subject,
        body_preview=body_preview,
        size_bytes=size_bytes,
        has_attachments=has_attachments,
        thread_id=thread_id
    )
    
    return MessageResponse.model_validate(message)