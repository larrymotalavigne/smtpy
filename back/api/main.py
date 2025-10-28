import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.views import auth_view, billing_view, domains_view, messages_view, subscriptions_view, webhooks_view, statistics_view
from api.views import utils_view
from shared.core.config import SETTINGS
from shared.core.db import create_tables
from shared.core.logging_config import setup_logging, get_logger
from shared.core.middlewares import SecurityHeadersMiddleware, SimpleRateLimiter

# Initialize logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Application startup - creating database tables")
    await create_tables()
    logger.info("Application startup complete")
    yield
    # Shutdown
    logger.info("Application shutdown")
    pass


def create_app() -> FastAPI:
    # Support env var name from guidelines
    secret_from_env = os.environ.get("SMTPY_SECRET_KEY")
    secret_key = secret_from_env or SETTINGS.SECRET_KEY

    # Enforce secret requirements
    if (not secret_key) or (secret_key == "change-this-secret-key-in-production"):
        if SETTINGS.is_production:
            raise RuntimeError("SMTPY_SECRET_KEY/SECRET_KEY must be set to a non-default value in production")
        else:
            logger.warning("Using default SECRET_KEY in development; set SMTPY_SECRET_KEY for better security")

    app = FastAPI(
        title="SMTPy v2 API",
        description="Self-hosted email forwarding + domain management service",
        version="2.0.0",
        docs_url='/docs',
        lifespan=lifespan
    )

    # Middleware order matters: last added runs first, so these run in reverse order

    # Security headers (added last, runs first)
    app.add_middleware(SecurityHeadersMiddleware, enable_hsts=SETTINGS.is_production)

    # Rate limiting for sensitive endpoints
    app.add_middleware(
        SimpleRateLimiter,
        requests=10,
        window_seconds=60,
        paths=["/auth/login", "/auth/register", "/auth/password-reset"],
    )

    # Session timeout middleware
    # app.add_middleware(SessionTimeoutMiddleware, idle_timeout_seconds=1800, absolute_timeout_seconds=86400)

    # Session middleware (requires starlette.middleware.sessions)
    # app.add_middleware(SessionMiddleware, secret_key=secret_key, same_site="lax", https_only=SETTINGS.is_production)

    # CORS middleware for frontend development
    # IMPORTANT: In production, restrict origins to your actual frontend domain
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:4200", "http://127.0.0.1:4200"],  # Angular dev server
        allow_credentials=True,  # Required for cookies
        allow_methods=["*"],  # Allow all HTTP methods
        allow_headers=["*"],  # Allow all headers
    )

    # Root health check endpoint
    @app.get("/", tags=["health"])
    async def root_health():
        """Root health check endpoint - returns JSON instead of docs."""
        return {
            "status": "healthy",
            "service": "SMTPy v2 API",
            "version": "2.0.0"
        }

    # Include routers
    app.include_router(auth_view.router)
    app.include_router(billing_view.router)
    app.include_router(domains_view.router)
    app.include_router(messages_view.router)
    app.include_router(statistics_view.router)
    app.include_router(subscriptions_view.router)
    app.include_router(utils_view.router)
    app.include_router(webhooks_view.router)

    return app


if __name__ == "__main__":
    from uvicorn import run

    run("main:create_app", host="0.0.0.0", port=8000, reload=True, factory=True)
