import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.core.config import SETTINGS
from api.core.db import create_tables
from api.views import auth_view, billing_view, domains_view, messages_view, subscriptions_view, webhooks_view
from api.views import utils_view


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    await create_tables()
    yield
    # Shutdown
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
            logging.warning("Using default SECRET_KEY in development; set SMTPY_SECRET_KEY for better security")

    app = FastAPI(
        title="SMTPy v2 API",
        description="Self-hosted email forwarding + domain management service",
        version="2.0.0",
        docs_url='/',
        lifespan=lifespan
    )

    # CORS middleware for frontend development
    # IMPORTANT: In production, restrict origins to your actual frontend domain
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:4200", "http://127.0.0.1:4200"],  # Angular dev server
        allow_credentials=True,  # Required for cookies
        allow_methods=["*"],  # Allow all HTTP methods
        allow_headers=["*"],  # Allow all headers
    )

    # # Other middleware (commented out for now)
    # # Middleware order matters: last added runs first.
    # app.add_middleware(SecurityHeadersMiddleware, enable_hsts=SETTINGS.is_production)
    # app.add_middleware(
    #     SimpleRateLimiter,
    #     requests=5,
    #     window_seconds=60,
    #     paths=["/login", "/register", "/password-reset"],
    # )
    # app.add_middleware(SessionTimeoutMiddleware, idle_timeout_seconds=1800, absolute_timeout_seconds=86400)
    # app.add_middleware(SessionMiddleware, secret_key=secret_key, same_site="lax", https_only=SETTINGS.is_production)

    # Include routers
    app.include_router(auth_view.router)
    app.include_router(billing_view.router)
    app.include_router(domains_view.router)
    app.include_router(messages_view.router)
    app.include_router(subscriptions_view.router)
    app.include_router(utils_view.router)
    app.include_router(webhooks_view.router)

    return app


if __name__ == "__main__":
    from uvicorn import run

    run("main:create_app", host="0.0.0.0", port=8000, reload=True, factory=True)
