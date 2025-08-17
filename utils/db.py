from config import SETTINGS
import asyncio
import os
import subprocess
from contextlib import contextmanager, asynccontextmanager
from typing import Annotated, Optional

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker

from database.models import Base
from utils.logging_config import get_logger

try:
    import greenlet  # type: ignore
    _GREENLET_AVAILABLE = True
except Exception:  # pragma: no cover - test env may not have greenlet
    _GREENLET_AVAILABLE = False

# Database URL configuration
if SETTINGS.DATABASE_URL:
    DATABASE_URL = SETTINGS.DATABASE_URL
    # For async URL, convert postgres:// to postgresql+psycopg://
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1) if DATABASE_URL.startswith("postgresql://") else DATABASE_URL
else:
    DB_PATH = SETTINGS.DB_PATH
    DATABASE_URL = f"sqlite:///{DB_PATH}"
    ASYNC_DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"

# Sync database setup (default for app and tests)
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite://") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine)

# Async database setup (available for async endpoints; tests may still use sync engine)
async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    autoflush=False,
    expire_on_commit=False,
    autocommit=False,
    class_=AsyncSession,
)


def init_db():
    """Initialize database by running alembic migrations and creating tables if needed."""
    logger = get_logger("database")
    
    try:
        # Run alembic upgrade head to ensure database is up to date
        logger.info("Running alembic upgrade head...")
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=os.path.dirname(os.path.dirname(__file__)),  # Go to project root
            capture_output=True,
            text=True,
            check=True
        )
        logger.info("Alembic upgrade completed successfully")
        if result.stdout:
            logger.debug(f"Alembic output: {result.stdout}")
    except subprocess.CalledProcessError as e:
        logger.warning(f"Alembic upgrade failed: {e}")
        logger.warning(f"Alembic stderr: {e.stderr}")
        logger.info("Falling back to creating tables directly with SQLAlchemy")
        # Fallback to creating tables directly if alembic fails
        Base.metadata.create_all(bind=engine)
    except FileNotFoundError:
        logger.warning("Alembic command not found, falling back to creating tables directly with SQLAlchemy")
        # Fallback if alembic is not available
        Base.metadata.create_all(bind=engine)

@contextmanager
def get_db():
    """Context manager for sync database sessions (also used directly in tests)."""
    session = SessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


async def get_async_db():
    _ensure_async_bind()
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


adbDep = Annotated[AsyncSession, Depends(get_async_db)]


def get_db_dep():
    """FastAPI dependency wrapper to yield a sync session using context manager."""
    with get_db() as session:
        yield session


# --- Async session compatibility helpers ---
_async_bound_url: str = None


def _to_async_url_from_sync(url: str) -> str:
    """Convert a SQLAlchemy sync URL string to an async URL (sqlite -> sqlite+aiosqlite)."""
    if url.startswith("sqlite://"):
        return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    return url


def _ensure_async_bind():
    """Ensure the async engine/session are bound to the same database as the sync engine.

    During tests, utils.db.engine is monkey-patched to a shared in-memory DB. This helper
    rebuilds the async engine/sessionmaker to point to the same database URL so that
    async queries (e.g., in smtp_server.handler) see the same data.
    """
    global async_engine, AsyncSessionLocal, _async_bound_url
    sync_url = str(engine.url)
    async_url = _to_async_url_from_sync(sync_url)
    if _async_bound_url != async_url:
        async_engine = create_async_engine(async_url, echo=False, future=True)
        AsyncSessionLocal = async_sessionmaker(
            bind=async_engine,
            autoflush=False,
            expire_on_commit=False,
            autocommit=False,
            class_=AsyncSession,
        )
        _async_bound_url = async_url



class _ScalarOneOrNoneResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class AsyncSessionProxy:
    """Lightweight async proxy over a synchronous SQLAlchemy Session for tests.

    Provides the minimal async API used by smtp_server.handler: execute(), add(), commit().
    """

    def __init__(self, sync_session):
        self._s = sync_session

    async def execute(self, statement):
        def _exec():
            return self._s.execute(statement)

        return await asyncio.to_thread(_exec)

    def add(self, obj):
        return self._s.add(obj)

    async def commit(self):
        return await asyncio.to_thread(self._s.commit)

    async def rollback(self):
        return await asyncio.to_thread(self._s.rollback)

    async def close(self):
        return await asyncio.to_thread(self._s.close)


@asynccontextmanager
async def get_async_session():
    """Async context manager returning an AsyncSession bound to the current DB.

    Uses real AsyncSession when greenlet is available; otherwise falls back to
    an AsyncSessionProxy over the synchronous Session to avoid greenlet deps in tests.
    """
    if _GREENLET_AVAILABLE:
        _ensure_async_bind()
        async with AsyncSessionLocal() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    else:
        # Fallback for test environment without greenlet
        session = SessionLocal()
        try:
            yield AsyncSessionProxy(session)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
