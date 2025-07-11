from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Boolean, String, DateTime
from sqlalchemy.sql import func
from typing import Optional, List
import datetime

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column()
    email: Mapped[Optional[str]] = mapped_column(nullable=True)
    role: Mapped[str] = mapped_column(default="user")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_token: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    invited_by: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id"), nullable=True)
    password_reset_token: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    password_reset_expiry: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)

class Domain(Base):
    __tablename__ = "domain"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True, index=True)
    catch_all: Mapped[Optional[str]] = mapped_column(nullable=True)  # Email address for catch-all alias (if set)
    aliases: Mapped[List["Alias"]] = relationship("Alias", back_populates="domain")

class Alias(Base):
    __tablename__ = "alias"
    id: Mapped[int] = mapped_column(primary_key=True)
    local_part: Mapped[str] = mapped_column(index=True)
    targets: Mapped[str] = mapped_column()  # Comma-separated list of destination emails
    expires_at: Mapped[datetime.datetime] = mapped_column(DateTime)
    domain_id: Mapped[int] = mapped_column(ForeignKey("domain.id"))
    domain: Mapped["Domain"] = relationship("Domain", back_populates="aliases")

class ForwardingRule(Base):
    __tablename__ = "forwarding_rule"
    id: Mapped[int] = mapped_column(primary_key=True)
    pattern: Mapped[str]
    target: Mapped[str]
    domain_id: Mapped[int] = mapped_column(ForeignKey("domain.id"))

class ActivityLog(Base):
    __tablename__ = "activity_log"
    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime.datetime] = mapped_column(DateTime, default=func.now())
    event_type: Mapped[str] = mapped_column()
    sender: Mapped[Optional[str]] = mapped_column(nullable=True)
    recipient: Mapped[Optional[str]] = mapped_column(nullable=True)
    subject: Mapped[Optional[str]] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column()
    message: Mapped[Optional[str]] = mapped_column(nullable=True) 