"""Fixed sync functions for main_controller.py"""

import secrets
from datetime import datetime, timedelta, UTC
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from core.database.models import User, Invitation
from core.utils.error_handling import ValidationError
from core.utils.soft_delete import get_active_users

_pwd_ctx_sync = CryptContext(schemes=["bcrypt"], deprecated="auto")


def invite_user_simple_sync(session: Session, email: str, invited_by_id: int) -> Dict[str, Any]:
    # Fix: Use session.execute() with select statement
    users_result = session.execute(get_active_users(session).where(User.email == email))
    if users_result.scalars().first():
        raise ValidationError("Email already registered")
    existing = session.query(Invitation).filter_by(email=email).first()
    if existing and existing.expires_at > datetime.now(UTC):
        raise ValidationError("Invitation already sent")
    token = secrets.token_urlsafe(32)
    invitation = Invitation(
        email=email,
        token=token,
        expires_at=datetime.now(UTC) + timedelta(hours=24),
        invited_by=invited_by_id,
    )
    session.add(invitation)
    session.commit()
    return {"token": token, "email": email}


def register_user_simple_sync(
        session: Session,
        username: str,
        password: str,
        email: Optional[str],
        invite_token: Optional[str],
):
    email_val = email
    invitation = None
    if invite_token:
        invitation = session.query(Invitation).filter_by(token=invite_token).first()
        if not invitation or invitation.expires_at < datetime.now(UTC):
            raise ValidationError("Invalid or expired invitation")
        email_val = invitation.email
    
    # Fix: Use session.execute() with select statement
    users_result = session.execute(get_active_users(session).where(User.username == username))
    if users_result.scalars().first():
        raise ValidationError("Username already exists")
    
    if email_val:
        users_result = session.execute(get_active_users(session).where(User.email == email_val))
        if users_result.scalars().first():
            raise ValidationError("Email already registered")
    
    verification_token = None if invite_token else secrets.token_urlsafe(32)
    user = User(
        username=username,
        email=email_val,
        hashed_password=_pwd_ctx_sync.hash(password),
        is_active=bool(invite_token),
        email_verified=bool(invite_token),
        verification_token=verification_token,
    )
    session.add(user)
    if invitation:
        session.delete(invitation)
    session.commit()
    return {
        "user_id": user.id,
        "requires_verification": not bool(invite_token),
        "verification_token": verification_token,
    }


def verify_email_simple_sync(session: Session, token: str) -> bool:
    user = session.query(User).filter_by(verification_token=token).first()
    if not user:
        return False
    user.is_active = True
    user.email_verified = True
    user.verification_token = None
    session.commit()
    return True


def authenticate_simple_sync(session: Session, username: str, password: str) -> Optional[int]:
    # Fix: Use session.execute() with select statement
    users_result = session.execute(get_active_users(session).where(User.username == username))
    user = users_result.scalars().first()
    if not user:
        return None
    if not _pwd_ctx_sync.verify(password, user.hashed_password):
        return None
    return user.id