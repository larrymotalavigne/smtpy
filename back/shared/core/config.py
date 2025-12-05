"""Core configuration for SMTPy v2."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/smtpy",
        description="Async PostgreSQL database URL"
    )

    # API Settings
    API_HOST: str = Field(default="0.0.0.0", description="API host")
    API_PORT: int = Field(default=8000, description="API port")
    DEBUG: bool = Field(default=False, description="Debug mode")

    # Security
    SECRET_KEY: str = Field(
        default="change-this-secret-key-in-production",
        description="Secret key for session management"
    )

    # Stripe Configuration
    STRIPE_API_KEY: str = Field(default="", description="Stripe API key")
    STRIPE_WEBHOOK_SECRET: str = Field(default="", description="Stripe webhook secret")
    STRIPE_SUCCESS_URL: str = Field(
        default="http://localhost:8000/billing/success",
        description="Stripe checkout success URL"
    )
    STRIPE_CANCEL_URL: str = Field(
        default="http://localhost:8000/billing/cancel",
        description="Stripe checkout cancel URL"
    )
    STRIPE_PORTAL_RETURN_URL: str = Field(
        default="http://localhost:8000/billing",
        description="Stripe customer portal return URL"
    )

    # DNS Configuration
    DNS_CHECK_ENABLED: bool = Field(default=True, description="Enable DNS verification checks")

    # Email Configuration (for sending transactional emails via Docker mailserver)
    EMAIL_ENABLED: bool = Field(default=True, description="Enable email sending")
    EMAIL_FROM: str = Field(default="noreply@smtpy.local", description="Default from email address")
    EMAIL_FROM_NAME: str = Field(default="SMTPy", description="Default from name")

    # Docker Mailserver Configuration
    MAILSERVER_HOST: str = Field(default="mailserver", description="Docker mailserver hostname")
    MAILSERVER_PORT: int = Field(default=587, description="Mailserver SMTP submission port")
    MAILSERVER_USER: str = Field(default="", description="Mailserver username (if auth required)")
    MAILSERVER_PASSWORD: str = Field(default="", description="Mailserver password (if auth required)")
    MAILSERVER_USE_TLS: bool = Field(default=True, description="Use STARTTLS for mailserver connection")

    # SMTP Receiver Configuration (for receiving emails from mailserver)
    SMTP_RECEIVER_HOST: str = Field(default="0.0.0.0", description="SMTP receiver bind address")
    SMTP_RECEIVER_PORT: int = Field(default=2525, description="SMTP receiver port")

    # Application URLs
    APP_URL: str = Field(default="http://localhost:4200", description="Frontend application URL")

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return False


# Global settings instance
SETTINGS = Settings()
