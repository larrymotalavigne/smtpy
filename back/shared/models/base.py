"""Base models for SMTPy v2."""

from datetime import datetime

from sqlalchemy import DateTime, func, Column
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all database models."""
    pass


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True),
        default=func.now(),
        nullable=False,
        doc="Record creation timestamp"
    )

    updated_at: Mapped[datetime] = Column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Record last update timestamp"
    )
