"""Messages view layer for SMTPy v2."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..controllers import messages_controller
from shared.core.db import get_db
from shared.models.message import MessageStatus
from ..schemas.common import PaginatedResponse, PaginationParams, ErrorResponse
from ..schemas.message import (
    MessageResponse,
    MessageList,
    MessageStats,
    MessageFilter
)

# Create router
router = APIRouter(prefix="/messages", tags=["messages"])

# For now, we'll use a hardcoded organization_id
# In a real implementation, this would come from authentication/session
MOCK_ORGANIZATION_ID = 1


@router.get(
    "",
    response_model=PaginatedResponse,
    summary="List messages",
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def list_messages(
    pagination: PaginationParams = Depends(),
    status: Optional[MessageStatus] = Query(None, description="Filter by message status"),
    domain_id: Optional[int] = Query(None, description="Filter by domain ID"),
    sender_email: Optional[str] = Query(None, description="Filter by sender email"),
    recipient_email: Optional[str] = Query(None, description="Filter by recipient email"),
    has_attachments: Optional[bool] = Query(None, description="Filter by attachment presence"),
    date_from: Optional[str] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db)
):
    """List all messages for the organization with pagination and filtering."""
    try:
        # Create filter object
        filters = MessageFilter(
            domain_id=domain_id,
            status=status,
            sender_email=sender_email,
            recipient_email=recipient_email,
            has_attachments=has_attachments,
            date_from=date_from,
            date_to=date_to
        )
        
        return await messages_controller.list_messages(
            db=db,
            organization_id=MOCK_ORGANIZATION_ID,
            page=pagination.page,
            page_size=pagination.page_size,
            filters=filters
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch messages"
        )


@router.get(
    "/search",
    response_model=PaginatedResponse,
    summary="Search messages",
    responses={
        400: {"model": ErrorResponse, "description": "Search term is required"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def search_messages(
    q: str = Query(..., description="Search term", min_length=1),
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Search messages by subject, sender, or recipient."""
    try:
        return await messages_controller.search_messages(
            db=db,
            organization_id=MOCK_ORGANIZATION_ID,
            search_term=q,
            page=pagination.page,
            page_size=pagination.page_size
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search messages"
        )


@router.get(
    "/stats",
    response_model=MessageStats,
    summary="Get message statistics",
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_message_statistics(
    since: Optional[str] = Query(None, description="Get stats since date (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db)
):
    """Get message statistics for the organization."""
    try:
        since_date = None
        if since:
            try:
                since_date = datetime.fromisoformat(since)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date format. Use YYYY-MM-DD"
                )
        
        return await messages_controller.get_message_statistics(
            db=db,
            organization_id=MOCK_ORGANIZATION_ID,
            since_date=since_date
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch message statistics"
        )


@router.get(
    "/recent",
    response_model=list[MessageList],
    summary="Get recent messages",
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_recent_messages(
    limit: int = Query(10, ge=1, le=50, description="Number of recent messages to return"),
    db: AsyncSession = Depends(get_db)
):
    """Get most recent messages for the organization."""
    try:
        return await messages_controller.get_recent_messages(
            db=db,
            organization_id=MOCK_ORGANIZATION_ID,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch recent messages"
        )


@router.get(
    "/{message_id}",
    response_model=MessageResponse,
    summary="Get message details",
    responses={
        404: {"model": ErrorResponse, "description": "Message not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_message(
    message_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a specific message."""
    try:
        message = await messages_controller.get_message(
            db=db,
            message_id=message_id,
            organization_id=MOCK_ORGANIZATION_ID
        )
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        return message
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch message"
        )


@router.delete(
    "/{message_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a message",
    responses={
        404: {"model": ErrorResponse, "description": "Message not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def delete_message(
    message_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a message."""
    try:
        deleted = await messages_controller.delete_message(
            db=db,
            message_id=message_id,
            organization_id=MOCK_ORGANIZATION_ID
        )
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete message"
        )


@router.get(
    "/domain/{domain_id}",
    response_model=PaginatedResponse,
    summary="Get messages for a domain",
    responses={
        404: {"model": ErrorResponse, "description": "Domain not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_messages_by_domain(
    domain_id: int,
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Get all messages for a specific domain."""
    try:
        messages = await messages_controller.get_messages_by_domain(
            db=db,
            domain_id=domain_id,
            organization_id=MOCK_ORGANIZATION_ID,
            page=pagination.page,
            page_size=pagination.page_size
        )
        
        if messages is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Domain not found"
            )
        
        return messages
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch messages for domain"
        )


@router.get(
    "/thread/{thread_id}",
    response_model=list[MessageResponse],
    summary="Get messages in a thread",
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_messages_by_thread(
    thread_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get all messages in a thread."""
    try:
        return await messages_controller.get_messages_by_thread(
            db=db,
            thread_id=thread_id,
            organization_id=MOCK_ORGANIZATION_ID
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch thread messages"
        )


@router.patch(
    "/{message_id}/status",
    response_model=MessageResponse,
    summary="Update message status",
    responses={
        404: {"model": ErrorResponse, "description": "Message not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def update_message_status(
    message_id: int,
    new_status: MessageStatus = Query(..., description="New message status"),
    error_message: Optional[str] = Query(None, description="Error message if processing failed"),
    db: AsyncSession = Depends(get_db)
):
    """Update the processing status of a message."""
    try:
        updated_message = await messages_controller.update_message_status(
            db=db,
            message_id=message_id,
            organization_id=MOCK_ORGANIZATION_ID,
            status=new_status,
            error_message=error_message
        )

        if not updated_message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        return updated_message
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update message status"
        )