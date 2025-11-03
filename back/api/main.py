import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.views import auth_view, billing_view, domains_view, messages_view, subscriptions_view, webhooks_view, statistics_view, aliases_view
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
        description="""
## SMTPy - Self-hosted Email Forwarding Service

A comprehensive email forwarding and domain management platform built with FastAPI.

### Features

* **Email Forwarding**: Catch-all email forwarding with custom aliases
* **Domain Management**: Multi-domain support with DNS verification
* **Subscription Billing**: Stripe integration for tiered plans
* **Real-time Statistics**: Email delivery tracking and analytics
* **Secure Authentication**: Session-based auth with bcrypt password hashing

### Authentication

This API uses **session-based authentication** with HTTP-only cookies. To authenticate:

1. Call `POST /auth/login` with credentials
2. Cookie is set automatically on successful login
3. Include cookies in all subsequent requests
4. Call `POST /auth/logout` to end session

### Rate Limiting

Authentication endpoints (`/auth/login`, `/auth/register`, `/auth/password-reset`)
are rate-limited to 10 requests per minute per IP address.

### Error Responses

All endpoints return errors in a consistent format:

```json
{
  "success": false,
  "message": "Error description",
  "errors": ["Detailed error 1", "Detailed error 2"]
}
```

### Response Format

Success responses follow this structure:

```json
{
  "success": true,
  "message": "Operation successful",
  "data": { /* Response data */ }
}
```
        """,
        version="2.0.0",
        docs_url='/docs',
        redoc_url='/redoc',
        openapi_tags=[
            {
                "name": "health",
                "description": "Health check endpoints for monitoring service status"
            },
            {
                "name": "authentication",
                "description": "User registration, login, logout, and password management"
            },
            {
                "name": "domains",
                "description": "Domain registration, verification, and DNS configuration"
            },
            {
                "name": "aliases",
                "description": "Email alias creation, management, and forwarding configuration"
            },
            {
                "name": "messages",
                "description": "Email message viewing, filtering, and management"
            },
            {
                "name": "billing",
                "description": "Subscription plans, Stripe checkout, and usage limits"
            },
            {
                "name": "subscriptions",
                "description": "Active subscription management and cancellation"
            },
            {
                "name": "statistics",
                "description": "Email delivery statistics and analytics"
            },
            {
                "name": "webhooks",
                "description": "Stripe webhook handlers for payment events"
            },
            {
                "name": "utilities",
                "description": "Utility endpoints for DNS checks and system status"
            }
        ],
        contact={
            "name": "SMTPy Support",
            "url": "https://smtpy.fr",
            "email": "support@smtpy.fr"
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT"
        },
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
        allow_origins=["http://localhost:4200", "http://127.0.0.1:4200", "https://smtpy.fr"],  # Angular dev server
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
    app.include_router(aliases_view.router)
    app.include_router(messages_view.router)
    app.include_router(statistics_view.router)
    app.include_router(subscriptions_view.router)
    app.include_router(utils_view.router)
    app.include_router(webhooks_view.router)

    return app


if __name__ == "__main__":
    from uvicorn import run

    run("main:create_app", host="0.0.0.0", port=8000, reload=True, factory=True)
