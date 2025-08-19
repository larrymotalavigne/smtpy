from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, clear_mappers

from back.core.database.models import Base, User, Domain, Alias, ActivityLog, ForwardingRule, Invitation


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    # Use file-based SQLite database for better compatibility
    test_database_url = "sqlite:///test_database.db"
    
    # Create test engine with better isolation
    test_engine = create_engine(test_database_url, connect_args={"check_same_thread": False}, echo=False)
    TestSession = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=test_engine)
    
    # Patch db module directly - store original values
    from back.core.utils import db
    original_engine = db.engine
    original_session = db.SessionLocal
    
    db.engine = test_engine
    db.SessionLocal = TestSession
    
    # Create all tables on the test engine
    Base.metadata.drop_all(test_engine)  # Clean slate
    Base.metadata.create_all(test_engine)
    
    # Patch email sending functions to prevent actual email sending in tests
    # Also patch CSRF validation to disable it during testing
    with (
        patch("back.core.utils.user.send_verification_email"),
        patch("back.core.utils.user.send_invitation_email"),
        patch("smtplib.SMTP"),
        patch("back.core.utils.csrf.validate_csrf") as mock_csrf,
    ):
        # Make CSRF validation always pass in tests
        mock_csrf.return_value = None
        yield
        
    # Clean up test database file and restore original db settings
    Base.metadata.drop_all(test_engine)
    test_engine.dispose()
    
    # Remove test database file
    import os
    if os.path.exists("test_database.db"):
        os.remove("test_database.db")
        
    db.engine = original_engine
    db.SessionLocal = original_session
    clear_mappers()
