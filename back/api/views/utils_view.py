from fastapi import APIRouter

router = APIRouter(tags=["health"])



@router.get("/health", tags=["health"])
async def detailed_health_check():
    """Detailed health check with version info."""
    return {
        "status": "healthy",
        "service": "SMTPy v2 API",
        "version": "2.0.0",
        "features": ["domains", "messages", "billing", "stripe_integration"]
    }
