"""Alias view layer for SMTPy v2."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..controllers import aliases_controller
from shared.core.db import get_db
from ..schemas.common import PaginatedResponse, PaginationParams, ErrorResponse
from ..schemas.alias import AliasCreate, AliasUpdate, AliasResponse

# Create router
router = APIRouter(prefix="/aliases", tags=["aliases"])

# For now, we'll use a hardcoded organization_id
# In a real implementation, this would come from authentication/session
MOCK_ORGANIZATION_ID = 1


@router.post(
    "",
    response_model=AliasResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new alias",
    responses={
        400: {"model": ErrorResponse, "description": "Alias already exists or invalid data"},
        404: {"model": ErrorResponse, "description": "Domain not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def create_alias(
    alias_data: AliasCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new email alias for forwarding."""
    try:
        return await aliases_controller.create_alias(
            db=db,
            alias_data=alias_data,
            organization_id=MOCK_ORGANIZATION_ID
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create alias"
        )


@router.get(
    "",
    response_model=PaginatedResponse,
    summary="List aliases",
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def list_aliases(
    domain_id: int = Query(None, description="Filter by domain ID"),
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """List all aliases for the organization with optional domain filter."""
    try:
        return await aliases_controller.list_aliases(
            db=db,
            organization_id=MOCK_ORGANIZATION_ID,
            domain_id=domain_id,
            page=pagination.page,
            page_size=pagination.page_size
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch aliases"
        )


@router.get(
    "/{alias_id}",
    response_model=AliasResponse,
    summary="Get alias details",
    responses={
        404: {"model": ErrorResponse, "description": "Alias not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_alias(
    alias_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a specific alias."""
    try:
        alias = await aliases_controller.get_alias(
            db=db,
            alias_id=alias_id,
            organization_id=MOCK_ORGANIZATION_ID
        )

        if not alias:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alias not found"
            )

        return alias
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch alias"
        )


@router.patch(
    "/{alias_id}",
    response_model=AliasResponse,
    summary="Update alias",
    responses={
        404: {"model": ErrorResponse, "description": "Alias not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def update_alias(
    alias_id: int,
    alias_update: AliasUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update alias settings."""
    try:
        updated_alias = await aliases_controller.update_alias(
            db=db,
            alias_id=alias_id,
            organization_id=MOCK_ORGANIZATION_ID,
            alias_update=alias_update
        )

        if not updated_alias:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alias not found"
            )

        return updated_alias
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update alias"
        )


@router.delete(
    "/{alias_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an alias",
    responses={
        404: {"model": ErrorResponse, "description": "Alias not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def delete_alias(
    alias_id: int,
    hard_delete: bool = Query(False, description="Permanently delete (true) or soft delete (false)"),
    db: AsyncSession = Depends(get_db)
):
    """Delete an alias."""
    try:
        deleted = await aliases_controller.delete_alias(
            db=db,
            alias_id=alias_id,
            organization_id=MOCK_ORGANIZATION_ID,
            soft_delete=not hard_delete
        )

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alias not found"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete alias"
        )
