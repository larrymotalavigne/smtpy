import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .core.db import create_tables
from .views.domains_view import router as domains_router
from .views.messages_view import router as messages_router
from .views.billing_view import get_billing_routers


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    await create_tables()
    yield
    # Shutdown
    pass


def create_app() -> FastAPI:
    """Create FastAPI application with all configurations."""
    app = FastAPI(
        title="SMTPy v2 API",
        description="Self-hosted email forwarding + domain management service",
        version="2.0.0",
        lifespan=lifespan
    )

    # Include routers
    app.include_router(domains_router)
    app.include_router(messages_router)
    
    # Include billing routers
    for billing_router in get_billing_routers():
        app.include_router(billing_router)

    # Mount static files
    app.mount(
        "/static",
        StaticFiles(directory=os.path.join(os.path.dirname(__file__), "./static")),
        name="static",
    )
    
    @app.get("/", tags=["health"])
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "service": "SMTPy v2 API"}
    
    @app.get("/health", tags=["health"])
    async def detailed_health_check():
        """Detailed health check with version info."""
        return {
            "status": "healthy",
            "service": "SMTPy v2 API",
            "version": "2.0.0",
            "features": ["domains", "messages", "billing", "stripe_integration"]
        }
    
    return app


if __name__ == "__main__":
    from uvicorn import run

    run("main:create_app", host="0.0.0.0", port=8000, reload=True, factory=True)
