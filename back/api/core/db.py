"""Async database setup for SMTPy v2."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .config import SETTINGS


# Create async engine
async_engine = create_async_engine(
    SETTINGS.DATABASE_URL,
    echo=SETTINGS.DEBUG,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=10,
    max_overflow=20,
)

# Create async sessionmaker
async_sessionmaker_factory = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to get database session.
    
    Yields:
        AsyncSession: Database session
    """
    async with async_sessionmaker_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables():
    """Create all database tables."""
    from ..models.base import Base
    
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables():
    """Drop all database tables."""
    from ..models.base import Base
    
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)