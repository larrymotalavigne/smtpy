import os

from pydantic_settings import BaseSettings
from starlette.templating import Jinja2Templates


class Settings(BaseSettings):
    STRIPE_TEST_API_KEY: str = os.environ.get("STRIPE_TEST_API_KEY", "sk_test_...")
    STRIPE_BILLING_PORTAL_RETURN_URL: str = os.environ.get("STRIPE_BILLING_PORTAL_RETURN_URL", "http://localhost:8000/billing")
    TEMPLATES: Jinja2Templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "./templates"))
    SECRET_KEY: str = os.environ.get("SMTPY_SECRET_KEY", "change-this-secret-key")
    SMTP_HOST: str = os.environ.get("SMTP_HOST", "localhost")
    SMTP_PORT: int = int(os.environ.get("SMTP_PORT", 25))

SETTINGS = Settings()
