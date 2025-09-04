"""Domain view layer for SMTPy v2."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..controllers import domains_controller
from ..core.db import get_db
from ..schemas.common import PaginatedResponse, PaginationParams, ErrorResponse
from ..schemas.domain import (
    DomainCreate,
    DomainUpdate,
    DomainResponse,
    DomainVerificationResponse,
    DNSRecords
)

# Create router
router = APIRouter(prefix="/domains", tags=["domains"])

# For now, we'll use a hardcoded organization_id
# In a real implementation, this would come from authentication/session
MOCK_ORGANIZATION_ID = 1


@router.post(
    "",
    response_model=DomainResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new domain",
    responses={
        400: {"model": ErrorResponse, "description": "Domain already exists or invalid data"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def create_domain(
    domain_data: DomainCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new domain for email forwarding."""
    try:
        return await domains_controller.create_domain(
            db=db,
            domain_data=domain_data,
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
            detail="Failed to create domain"
        )


@router.get(
    "",
    response_model=PaginatedResponse,
    summary="List domains",
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def list_domains(
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """List all domains for the organization with pagination."""
    try:
        return await domains_controller.list_domains(
            db=db,
            organization_id=MOCK_ORGANIZATION_ID,
            page=pagination.page,
            page_size=pagination.page_size
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch domains"
        )


@router.get(
    "/{domain_id}",
    response_model=DomainResponse,
    summary="Get domain details",
    responses={
        404: {"model": ErrorResponse, "description": "Domain not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_domain(
    domain_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a specific domain."""
    try:
        domain = await domains_controller.get_domain(
            db=db,
            domain_id=domain_id,
            organization_id=MOCK_ORGANIZATION_ID
        )
        
        if not domain:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Domain not found"
            )
        
        return domain
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch domain"
        )


@router.patch(
    "/{domain_id}",
    response_model=DomainResponse,
    summary="Update domain settings",
    responses={
        404: {"model": ErrorResponse, "description": "Domain not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def update_domain(
    domain_id: int,
    domain_update: DomainUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update domain settings."""
    try:
        updated_domain = await domains_controller.update_domain(
            db=db,
            domain_id=domain_id,
            organization_id=MOCK_ORGANIZATION_ID,
            is_active=domain_update.is_active
        )
        
        if not updated_domain:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Domain not found"
            )
        
        return updated_domain
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update domain"
        )


@router.delete(
    "/{domain_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a domain",
    responses={
        404: {"model": ErrorResponse, "description": "Domain not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def delete_domain(
    domain_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a domain and all associated data."""
    try:
        deleted = await domains_controller.delete_domain(
            db=db,
            domain_id=domain_id,
            organization_id=MOCK_ORGANIZATION_ID
        )
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Domain not found"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete domain"
        )


@router.post(
    "/{domain_id}/verify",
    response_model=DomainVerificationResponse,
    summary="Verify domain DNS configuration",
    responses={
        404: {"model": ErrorResponse, "description": "Domain not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def verify_domain(
    domain_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Verify domain DNS records (MX, SPF, DKIM, DMARC)."""
    try:
        verification_result = await domains_controller.verify_domain(
            db=db,
            domain_id=domain_id,
            organization_id=MOCK_ORGANIZATION_ID
        )
        
        if not verification_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Domain not found"
            )
        
        return verification_result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify domain"
        )


@router.get(
    "/{domain_id}/dns-records",
    response_model=DNSRecords,
    summary="Get required DNS records",
    responses={
        404: {"model": ErrorResponse, "description": "Domain not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_dns_records(
    domain_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get the required DNS records for domain setup."""
    try:
        dns_records = await domains_controller.get_dns_records(
            db=db,
            domain_id=domain_id,
            organization_id=MOCK_ORGANIZATION_ID
        )
        
        if not dns_records:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Domain not found"
            )
        
        return dns_records
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch DNS records"
        )