from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, clear_mappers
from testcontainers.postgres import PostgresContainer

from back.api.database.models import Base


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    # Start PostgreSQL container
    postgres = PostgresContainer("postgres:15-alpine")
    postgres.start()
    
    try:
        # Get the database URL from the container
        test_database_url = postgres.get_connection_url()
        
        # Create test engine
        engine = create_engine(test_database_url)
        Session = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine)
        
        # Patch db module directly
        from back.core.utils import db
        db.engine = engine
        db.SessionLocal = Session
        
        # Create tables on the patched engine
        Base.metadata.create_all(engine)
        
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
            
        # Drop tables after tests
        Base.metadata.drop_all(engine)
        clear_mappers()
    finally:
        # Stop and remove the container
        postgres.stop()
