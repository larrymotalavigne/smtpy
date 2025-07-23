import os
import secrets
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from passlib.context import CryptContext
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from config import SETTINGS, validate_configuration
from database.models import User
from utils.db import get_session, init_db
from utils.logging_config import setup_logging, get_logger
from utils.error_handling import ErrorHandlingMiddleware
from views import domain_view, alias_view, billing_view, user_view, main_view


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
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
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
    logger = get_logger("auth")
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    with get_session() as session:
        if not session.query(User).first():
            # Generate a secure random password
            temp_password = secrets.token_urlsafe(16)
            hashed = pwd_context.hash(temp_password)
            user = User(
                username="admin",
                hashed_password=hashed,
                email=None,
                role="admin",
                is_active=True,
                email_verified=True
            )
            session.add(user)
            session.commit()
            logger.info("Created default admin user with temporary password")
            logger.warning(f"Default admin credentials - Username: admin, Password: {temp_password}")
            logger.warning("SECURITY: Please change the default admin password immediately after first login!")
            # Also print to console for immediate visibility
            print(f"\n\033[92mCreated default admin user with temporary password:\033[0m")
            print(f"\033[92mUsername: admin\033[0m")
            print(f"\033[92mPassword: {temp_password}\033[0m")
            print(f"\033[93mWARNING: Please change this password immediately after first login!\033[0m\n")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize logging first
    setup_logging()
    logger = get_logger("main")
    logger.info("Starting SMTPy application")
    
    # Validate configuration
    validate_configuration()
    
    # Initialize database and create default admin
    init_db()
    create_default_admin()
    
    logger.info("SMTPy application startup completed")
    yield
    logger.info("SMTPy application shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title="SMTPy API",
        lifespan=lifespan
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
        same_site="lax"  # CSRF protection
    )
    app.include_router(domain_view.router, prefix="/api")
    app.include_router(alias_view.router, prefix="/api")
    app.include_router(user_view.router, prefix="/api")
    app.include_router(billing_view.router, prefix="/api")
    app.include_router(main_view.router)

    app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "./static")), name="static")
    return app


if __name__ == "__main__":
    from uvicorn import run

    run("main:create_app", host="0.0.0.0", port=8000, reload=True, factory=True)
