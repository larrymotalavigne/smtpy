"""Alias view layer for SMTPy v2."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..controllers import aliases_controller
from shared.core.db import get_db
from ..schemas.common import PaginatedResponse, PaginationParams, ErrorResponse
from ..schemas.alias import AliasCreate, AliasUpdate, AliasResponse
from .auth_view import get_current_user

# Create router
router = APIRouter(prefix="/aliases", tags=["aliases"])


@router.post(
    "",
    response_model=AliasResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new alias",
    responses={
        400: {"model": ErrorResponse, "description": "Alias already exists or invalid data"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Domain not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def create_alias(
    alias_data: AliasCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new email alias for forwarding."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    organization_id = current_user.get("organization_id")
    if not organization_id:
        raise HTTPException(status_code=400, detail="No organization found for user")

    try:
        return await aliases_controller.create_alias(
            db=db,
            alias_data=alias_data,
            organization_id=organization_id
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
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def list_aliases(
    domain_id: int = Query(None, description="Filter by domain ID"),
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all aliases for the organization with optional domain filter."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    organization_id = current_user.get("organization_id")
    if not organization_id:
        raise HTTPException(status_code=400, detail="No organization found for user")

    try:
        return await aliases_controller.list_aliases(
            db=db,
            organization_id=organization_id,
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
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Alias not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_alias(
    alias_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get detailed information about a specific alias."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    organization_id = current_user.get("organization_id")
    if not organization_id:
        raise HTTPException(status_code=400, detail="No organization found for user")

    try:
        alias = await aliases_controller.get_alias(
            db=db,
            alias_id=alias_id,
            organization_id=organization_id
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
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Alias not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def update_alias(
    alias_id: int,
    alias_update: AliasUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update alias settings."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    organization_id = current_user.get("organization_id")
    if not organization_id:
        raise HTTPException(status_code=400, detail="No organization found for user")

    try:
        updated_alias = await aliases_controller.update_alias(
            db=db,
            alias_id=alias_id,
            organization_id=organization_id,
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
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Alias not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def delete_alias(
    alias_id: int,
    hard_delete: bool = Query(False, description="Permanently delete (true) or soft delete (false)"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete an alias."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    organization_id = current_user.get("organization_id")
    if not organization_id:
        raise HTTPException(status_code=400, detail="No organization found for user")

    try:
        deleted = await aliases_controller.delete_alias(
            db=db,
            alias_id=alias_id,
            organization_id=organization_id,
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
