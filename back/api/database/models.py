import datetime
from typing import Optional, List

from sqlalchemy import ForeignKey, Boolean, String, DateTime, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    role: Mapped[str] = mapped_column(String(20), default="user")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_token: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    invited_by: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id"), nullable=True)
    password_reset_token: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    password_reset_expiry: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime, nullable=True
    )
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    subscription_status: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True, index=True
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    deleted_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime, nullable=True, index=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=func.now(), index=True)
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )
    invitations: Mapped[List["Invitation"]] = relationship(
        "Invitation", back_populates="inviter", cascade="delete"
    )
    domains: Mapped[List["Domain"]] = relationship(
        "Domain", back_populates="owner", cascade="delete"
    )
    aliases: Mapped[List["Alias"]] = relationship("Alias", back_populates="owner", cascade="delete")


class Domain(Base):
    __tablename__ = "domain"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    catch_all: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )  # Email address for catch-all alias (if set)
    owner_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    deleted_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime, nullable=True, index=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=func.now(), index=True)
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )
    owner: Mapped["User"] = relationship("User", back_populates="domains")
    aliases: Mapped[List["Alias"]] = relationship(
        "Alias", back_populates="domain", cascade="delete"
    )
    forwarding_rules: Mapped[List["ForwardingRule"]] = relationship(
        "ForwardingRule", back_populates="domain", cascade="delete"
    )


class Alias(Base):
    __tablename__ = "alias"
    __table_args__ = (UniqueConstraint("domain_id", "local_part", name="uix_alias_domain_local_part"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    local_part: Mapped[str] = mapped_column(String(100), index=True)
    targets: Mapped[str] = mapped_column(String(1000))  # Comma-separated list of destination emails
    expires_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime, nullable=True, index=True
    )
    domain_id: Mapped[int] = mapped_column(ForeignKey("domain.id"), index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    deleted_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime, nullable=True, index=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=func.now(), index=True)
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )
    domain: Mapped["Domain"] = relationship("Domain", back_populates="aliases")
    owner: Mapped["User"] = relationship("User", back_populates="aliases")


class ForwardingRule(Base):
    __tablename__ = "forwarding_rule"
    id: Mapped[int] = mapped_column(primary_key=True)
    pattern: Mapped[str] = mapped_column(String(255))
    target: Mapped[str] = mapped_column(String(255))
    domain_id: Mapped[int] = mapped_column(ForeignKey("domain.id"), index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=func.now(), index=True)
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )
    domain: Mapped["Domain"] = relationship("Domain", back_populates="forwarding_rules")


class ActivityLog(Base):
    __tablename__ = "activity_log"
    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime.datetime] = mapped_column(DateTime, default=func.now(), index=True)
    event_type: Mapped[str] = mapped_column(String(50), index=True)
    sender: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    recipient: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    subject: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), index=True)
    message: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)


class Invitation(Base):
    __tablename__ = "invitation"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), index=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime.datetime] = mapped_column(DateTime, index=True)
    invited_by: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=func.now(), index=True)
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )
    inviter: Mapped["User"] = relationship("User", back_populates="invitations")
