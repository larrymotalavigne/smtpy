import logging
import time
from contextlib import contextmanager
from typing import Annotated

import sqlalchemy
from fastapi import Depends
from sqlalchemy import event, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker

from core.config import SETTINGS

log_sqltime = logging.getLogger("sqltime")

ASYNC_ENGINE = create_async_engine(
    SETTINGS.ASYNC_SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
    pool_recycle=3600,  # 1 hour
    pool_size=10,
)

ASYNC_LOCAL_SESSION = async_sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=ASYNC_ENGINE)

# Sync engine for non-async operations like startup tasks
SYNC_DATABASE_URI = SETTINGS.ASYNC_SQLALCHEMY_DATABASE_URI.replace('postgresql+asyncpg://', 'postgresql://').replace('sqlite+aiosqlite://', 'sqlite://')
SYNC_ENGINE = create_engine(SYNC_DATABASE_URI, pool_pre_ping=True, pool_recycle=3600)
SYNC_LOCAL_SESSION = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=SYNC_ENGINE)


async def get_db():
    try:
        async with ASYNC_LOCAL_SESSION() as db:
            yield db
    finally:
        await db.aclose()


@contextmanager
def get_sync_db():
    """Sync version of get_db for non-async operations."""
    db = SYNC_LOCAL_SESSION()
    try:
        yield db
    finally:
        db.close()


def sync_get_db():
    """Sync version of get_db for FastAPI dependency injection."""
    db = SYNC_LOCAL_SESSION()
    try:
        yield db
    finally:
        db.close()


dbDep = Annotated[AsyncSession, Depends(get_db)]


@event.listens_for(sqlalchemy.engine.Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault("query_start_time", []).append(time.time())
    conn.info.setdefault("query_type", []).append(statement.split()[0].upper())
    log_sqltime.debug("Start Query: %s", statement)


@event.listens_for(sqlalchemy.engine.Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    start_time = conn.info["query_start_time"].pop(-1)
    query_type = conn.info.get("query_type", ["UNKNOWN"]).pop(-1)
    duration = time.time() - start_time

    log_sqltime.debug("Query Complete => Total Time: %f", duration)
