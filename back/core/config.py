import os
import secrets
from enum import Enum
from pathlib import Path
from typing import Optional, List
from urllib.parse import urlparse

try:
    from alembic.config import Config
    ALEMBIC_AVAILABLE = True
except ImportError:
    Config = None
    ALEMBIC_AVAILABLE = False

from fastapi import Request
from pydantic import Field, field_validator, model_validator, ConfigDict
from pydantic_settings import BaseSettings
from starlette.templating import Jinja2Templates

# Get the directory where this config.py file is located
_CONFIG_DIR = Path(__file__).parent
# Get the project root directory (two levels up from back/core/)
_PROJECT_ROOT = _CONFIG_DIR.parent.parent

# Only create ALEMBIC_CONFIG if alembic is available
ALEMBIC_CONFIG = None
if ALEMBIC_AVAILABLE:
    ALEMBIC_CONFIG = Config(str(_PROJECT_ROOT / "back" / "alembic.ini"))
    ALEMBIC_CONFIG.set_main_option(
        "script_location",
        str(_PROJECT_ROOT / "alembic"),
    )


class Environment(str, Enum):
    """Application environment types."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Application settings with validation and environment support."""

    # Environment
    ENVIRONMENT: Environment = Field(
        default=Environment.DEVELOPMENT, description="Application environment", json_schema_extra={"env": "SMTPY_ENV"}
    )

    # Security
    SECRET_KEY: str = Field(
        default="",
        description="Secret key for session management and CSRF protection",
        json_schema_extra={"env": "SMTPY_SECRET_KEY"}
    )

    # Database
    DB_PATH: str = Field(
        default="smtpy.db", description="Path to SQLite database file (deprecated, use DATABASE_URL)", json_schema_extra={"env": "SMTPY_DB_PATH"}
    )
    ASYNC_SQLALCHEMY_DATABASE_URI: str = Field(
        default="postgresql+psycopg://smtpy:smtpy@localhost:5432/smtpy", description="Database connection URL", json_schema_extra={"env": "SMTPY_DATABASE_URL"}
    )

    # SMTP Configuration
    SMTP_HOST: str = Field(default="localhost", description="SMTP relay host", json_schema_extra={"env": "SMTP_HOST"})
    SMTP_PORT: int = Field(
        default=25, ge=1, le=65535, description="SMTP relay port", json_schema_extra={"env": "SMTP_PORT"}
    )

    # Stripe Configuration
    STRIPE_TEST_API_KEY: str = Field(
        default="sk_test_...", description="Stripe API key for billing", json_schema_extra={"env": "STRIPE_TEST_API_KEY"}
    )
    STRIPE_BILLING_PORTAL_RETURN_URL: str = Field(
        default="http://localhost:8000/billing",
        description="Stripe billing portal return URL",
        json_schema_extra={"env": "STRIPE_BILLING_PORTAL_RETURN_URL"}
    )

    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Logging level", json_schema_extra={"env": "SMTPY_LOG_LEVEL"})
    LOG_FILE: Optional[str] = Field(
        default=None, description="Log file path (optional)", json_schema_extra={"env": "SMTPY_LOG_FILE"}
    )

    # Application Settings
    DEBUG: bool = Field(default=False, description="Enable debug mode", json_schema_extra={"env": "SMTPY_DEBUG"})
    ALLOWED_HOSTS: List[str] = Field(
        default=["localhost", "127.0.0.1"],
        description="Allowed hosts for the application",
        json_schema_extra={"env": "SMTPY_ALLOWED_HOSTS"}
    )

    # Session Configuration
    SESSION_MAX_AGE: int = Field(
        default=3600,
        ge=300,
        le=86400,
        description="Session timeout in seconds (5 minutes to 24 hours)",
        json_schema_extra={"env": "SMTPY_SESSION_MAX_AGE"}
    )

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(
        default=True, description="Enable rate limiting", json_schema_extra={"env": "SMTPY_RATE_LIMIT_ENABLED"}
    )

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=True)

    @field_validator("SECRET_KEY", mode="before")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate and generate secret key if needed."""
        if not v or v == "change-this-secret-key":
            # Generate a secure random secret key
            generated_key = secrets.token_urlsafe(32)

            # Check if we're in production by looking at environment variable
            env_var = os.getenv("SMTPY_ENV", "development").lower()
            if env_var == "production":
                raise ValueError(
                    "SECRET_KEY must be set in production environment. "
                    "Set SMTPY_SECRET_KEY environment variable."
                )
            else:
                print(
                    f"\n\033[93mWARNING: Using auto-generated secret key. "
                    f"Set SMTPY_SECRET_KEY environment variable for production.\033[0m"
                )
                print(f"\033[93mGenerated key: {generated_key}\033[0m\n")
                return generated_key

        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")

        return v

    @field_validator("DB_PATH")
    @classmethod
    def validate_db_path(cls, v: str) -> str:
        """Validate database path."""
        if not v:
            raise ValueError("DB_PATH cannot be empty")

        # Ensure directory exists
        db_path = Path(v)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        return str(db_path.absolute())

    @field_validator("STRIPE_BILLING_PORTAL_RETURN_URL")
    @classmethod
    def validate_stripe_url(cls, v: str) -> str:
        """Validate Stripe billing portal return URL."""
        if not v:
            raise ValueError("STRIPE_BILLING_PORTAL_RETURN_URL cannot be empty")

        parsed = urlparse(v)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("STRIPE_BILLING_PORTAL_RETURN_URL must be a valid URL")

        return v

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of: {', '.join(valid_levels)}")
        return v.upper()

    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def validate_allowed_hosts(cls, v) -> List[str]:
        """Validate allowed hosts."""
        if isinstance(v, str):
            # Split comma-separated string
            hosts = [host.strip() for host in v.split(",") if host.strip()]
        elif isinstance(v, list):
            hosts = [str(host).strip() for host in v if str(host).strip()]
        else:
            raise ValueError("ALLOWED_HOSTS must be a list or comma-separated string")

        if not hosts:
            raise ValueError("ALLOWED_HOSTS cannot be empty")

        return hosts

    @model_validator(mode="after")
    def validate_environment_specific_settings(self) -> "Settings":
        """Validate environment-specific settings."""
        import logging
        
        env = self.ENVIRONMENT
        
        # Log database configuration
        if self.ASYNC_SQLALCHEMY_DATABASE_URI:
            # Detect database type for logging
            if self.ASYNC_SQLALCHEMY_DATABASE_URI.startswith("postgresql://") or self.ASYNC_SQLALCHEMY_DATABASE_URI.startswith("postgresql+"):
                db_type = "PostgreSQL"
            elif self.ASYNC_SQLALCHEMY_DATABASE_URI.startswith("sqlite://"):
                db_type = "SQLite"
            else:
                db_type = "Unknown"
            logging.info(f"Database configuration: Using {db_type} from ASYNC_SQLALCHEMY_DATABASE_URI")
            logging.debug(f"Database URL: {self.ASYNC_SQLALCHEMY_DATABASE_URI}")
        else:
            logging.info(f"Database configuration: Using SQLite with DB_PATH")
            logging.debug(f"SQLite path: {self.DB_PATH}")

        if env == Environment.PRODUCTION:
            # Production-specific validations
            if self.DEBUG:
                raise ValueError("DEBUG must be False in production environment")

            if self.STRIPE_TEST_API_KEY.startswith("sk_test_"):
                print("\033[93mWARNING: Using test Stripe API key in production environment\033[0m")

        elif env == Environment.TESTING:
            # Testing-specific settings
            if not self.DB_PATH.endswith(":memory:") and "test" not in self.DB_PATH:
                self.DB_PATH = "test_smtpy.db"

        return self

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT == Environment.DEVELOPMENT

    @property
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.ENVIRONMENT == Environment.TESTING

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == Environment.PRODUCTION

    @property
    def templates(self) -> Jinja2Templates:
        """Get Jinja2 templates instance."""
        template_dir = Path(__file__).parent.parent / "api" / "templates"
        return Jinja2Templates(directory=str(template_dir))


def validate_configuration() -> None:
    """Validate configuration on application startup."""
    try:
        settings = Settings()

        # Additional runtime validations
        if settings.is_production:
            # Check critical production settings
            if settings.SECRET_KEY == "change-this-secret-key":
                raise ValueError("Production environment requires a secure SECRET_KEY")

            if not settings.STRIPE_TEST_API_KEY.startswith("sk_live_"):
                print("\033[93mWARNING: Using test Stripe API key in production\033[0m")

        print(f"✓ Configuration validated for {settings.ENVIRONMENT.value} environment")

    except Exception as e:
        print(f"\033[91mConfiguration validation failed: {e}\033[0m")
        raise


# Global settings instance
SETTINGS = Settings()


def template_response(request: Request, template_name: str, context: dict = None):
    """Create a template response with CSRF token automatically included."""
    from core.utils.csrf import get_csrf_token

    if context is None:
        context = {}

    try:
        # Add CSRF token to context
        context["csrf_token"] = get_csrf_token(request)

        return SETTINGS.templates.TemplateResponse(request, template_name, context)
    except Exception as e:
        # Debug: Log the exception and return error context
        import logging
        logging.error(f"Template response error: {e}")
        logging.error(f"Template: {template_name}, Context: {context}")
        # Return the context dict directly (this will cause the encode error, but helps debug)
        return context
