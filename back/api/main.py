import logging
import os
import secrets
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware

from core.config import SETTINGS, validate_configuration
from core.database.models import User
from core.utils.db import get_sync_db
from core.utils.error_handling import ErrorHandlingMiddleware
from api.views import domain_view, alias_view, billing_view, user_view, main_view


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://unpkg.com; "
            "img-src 'self' data:; "
            "font-src 'self' https://unpkg.com; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        response.headers["Content-Security-Policy"] = csp

        # HTTPS security headers (only in production)
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response


def create_default_admin():
    """Create default admin user with secure random password if no users exist."""
    from core.utils.user import hash_password
    with get_sync_db() as session:
        if not session.query(User).first():
            # Generate a secure random password
            temp_password = secrets.token_urlsafe(16)
            hashed = hash_password(temp_password)
            user = User(
                username="admin",
                hashed_password=hashed,
                email=None,
                role="admin",
                is_active=True,
                email_verified=True,
            )
            session.add(user)
            session.commit()
            logging.info("Created default admin user with temporary password")
            if SETTINGS.is_development:
                logging.warning(
                    f"Default admin credentials - Username: admin, Password: {temp_password}"
                )
                logging.warning(
                    "SECURITY: Please change the default admin password immediately after first login!"
                )
                # Log credentials for immediate visibility in development
                logging.info("=" * 60)
                logging.info("DEFAULT ADMIN CREDENTIALS CREATED")
                logging.info(f"Username: admin")
                logging.info(f"Password: {temp_password}")
                logging.info("IMPORTANT: Change this password immediately after first login!")
                logging.info("=" * 60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Starting SMTPy application")

    # Validate configuration
    validate_configuration()
    
    # Log key configuration for debugging
    logging.info(f"Environment: {SETTINGS.ENVIRONMENT.value}")
    logging.info(f"Debug mode: {SETTINGS.DEBUG}")
    logging.info(f"Log level: {SETTINGS.LOG_LEVEL}")
    
    # Log database configuration summary
    if SETTINGS.ASYNC_SQLALCHEMY_DATABASE_URI:
        if SETTINGS.ASYNC_SQLALCHEMY_DATABASE_URI.startswith("postgresql://") or SETTINGS.ASYNC_SQLALCHEMY_DATABASE_URI.startswith("postgresql+"):
            db_type = "PostgreSQL"
        elif SETTINGS.ASYNC_SQLALCHEMY_DATABASE_URI.startswith("sqlite://"):
            db_type = "SQLite"
        else:
            db_type = "Unknown"
        logging.info(f"Database: {db_type} (from ASYNC_SQLALCHEMY_DATABASE_URI)")
    else:
        logging.info(f"Database: SQLite (from DB_PATH: {SETTINGS.DB_PATH})")

    # Initialize database and create default admin
    create_default_admin()

    logging.info("SMTPy application startup completed")
    yield
    logging.info("SMTPy application shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title="SMTPy API",
        lifespan=lifespan,
    )

    # Add error handling middleware (first to catch all exceptions)
    app.add_middleware(ErrorHandlingMiddleware)

    # Add security headers middleware
    app.add_middleware(SecurityHeadersMiddleware)

    # Add session middleware with timeout and secure settings
    app.add_middleware(
        SessionMiddleware,
        secret_key=SETTINGS.SECRET_KEY,
        max_age=SETTINGS.SESSION_MAX_AGE,
        https_only=SETTINGS.is_production,  # Enable HTTPS-only cookies in production
        same_site="lax",  # CSRF protection
    )
    app.include_router(domain_view.router)
    app.include_router(alias_view.router)
    app.include_router(user_view.router)
    app.include_router(billing_view.router)
    app.include_router(main_view.router)

    app.mount(
        "/static",
        StaticFiles(directory=os.path.join(os.path.dirname(__file__), "./static")),
        name="static",
    )
    return app


if __name__ == "__main__":
    from uvicorn import run

    run("main:create_app", host="0.0.0.0", port=8000, reload=True, factory=True)
