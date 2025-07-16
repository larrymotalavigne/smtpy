import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, clear_mappers
from database.models import Base
from views.web import app
from unittest.mock import patch

# Use a shared in-memory SQLite DB for all connections
TEST_DATABASE_URL = "sqlite:///file::memory:?cache=shared&uri=true"

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    # Create test engine with shared cache
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    # Patch db module directly
    from database import db
    db.engine = engine
    db.SessionLocal = Session
    # Create tables on the patched engine
    Base.metadata.create_all(engine)
    # Patch only the email sending function that exists
    with patch("views.web.send_verification_email"):
        yield
    # Drop tables after tests
    Base.metadata.drop_all(engine)
    clear_mappers() 