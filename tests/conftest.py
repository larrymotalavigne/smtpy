from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, clear_mappers

from database.models import Base

# Use a shared in-memory SQLite DB for all connections
TEST_DATABASE_URL = "sqlite:///file::memory:?cache=shared&uri=true"


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    # Create test engine with shared cache
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Session = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine)
    # Patch db module directly
    from utils import db

    db.engine = engine
    db.SessionLocal = Session
    # Create tables on the patched engine
    Base.metadata.create_all(engine)
    # Patch email sending functions to prevent actual email sending in tests
    # Also patch CSRF validation to disable it during testing
    with (
        patch("utils.user.send_verification_email"),
        patch("utils.user.send_invitation_email"),
        patch("smtplib.SMTP"),
        patch("utils.csrf.validate_csrf") as mock_csrf,
    ):
        # Make CSRF validation always pass in tests
        mock_csrf.return_value = None
        yield
    # Drop tables after tests
    Base.metadata.drop_all(engine)
    clear_mappers()
