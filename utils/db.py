from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager, asynccontextmanager
import os
from database.models import Base

DB_PATH = os.environ.get("SMTPY_DB_PATH", "smtpy.db")

# Synchronous database setup
engine = create_engine(f"sqlite:///{DB_PATH}", echo=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

# Async database setup
async_engine = create_async_engine(f"sqlite+aiosqlite:///{DB_PATH}", echo=True, future=True)
AsyncSessionLocal = async_sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)

@contextmanager
def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@asynccontextmanager
async def get_async_session():
    """Async context manager for database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def init_db():
    Base.metadata.create_all(bind=engine)


async def init_async_db():
    """Initialize database tables using async engine."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


