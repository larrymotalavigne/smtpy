import os
import asyncio
from contextlib import contextmanager, asynccontextmanager
from typing import Annotated, Optional

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker

from database.models import Base

try:
    import greenlet  # type: ignore
    _GREENLET_AVAILABLE = True
except Exception:  # pragma: no cover - test env may not have greenlet
    _GREENLET_AVAILABLE = False

DB_PATH = os.environ.get("SMTPY_DB_PATH", "smtpy.db")

# Sync database setup (default for app and tests)
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine)

# Async database setup (available for async endpoints; tests may still use sync engine)
async_engine = create_async_engine(f"sqlite+aiosqlite:///{DB_PATH}", echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    autoflush=False,
    expire_on_commit=False,
    autocommit=False,
    class_=AsyncSession,
)


def init_db():
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
