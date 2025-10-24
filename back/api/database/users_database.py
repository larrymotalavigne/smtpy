"""User database operations for SMTPy v2."""

import bcrypt
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import User, PasswordResetToken, EmailVerificationToken, UserRole


class UsersDatabase:
    """Database operations for users."""

    @staticmethod
    async def create_user(
        session: AsyncSession,
        username: str,
        email: str,
        password: str,
        organization_id: Optional[int] = None,
        role: UserRole = UserRole.USER,
        is_verified: bool = False,
    ) -> User:
        """Create a new user with hashed password."""
        user = User(
            username=username,
            email=email,
            organization_id=organization_id,
            role=role,
            is_verified=is_verified,
        )
        user.set_password(password)

        session.add(user)
        await session.flush()
        await session.refresh(user)
        return user

    @staticmethod
    async def get_user_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
        """Get user by ID."""
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
        """Get user by email address."""
        result = await session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_username(session: AsyncSession, username: str) -> Optional[User]:
        """Get user by username."""
        result = await session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_credentials(
        session: AsyncSession, username_or_email: str
    ) -> Optional[User]:
        """Get user by username or email."""
        result = await session.execute(
            select(User).where(
                (User.username == username_or_email) | (User.email == username_or_email)
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def verify_password(
        session: AsyncSession, username_or_email: str, password: str
    ) -> Optional[User]:
        """Verify user credentials and return user if valid."""
        from sqlalchemy.orm import selectinload

        # Eagerly load organization to avoid lazy loading issues
        result = await session.execute(
            select(User)
            .where(
                (User.username == username_or_email) | (User.email == username_or_email)
            )
            .options(selectinload(User.organization))
        )
        user = result.scalar_one_or_none()

        if not user:
            return None

        if not user.is_active:
            return None

        # Access password_hash directly to avoid any lazy loading issues
        password_matches = bcrypt.checkpw(
            password.encode('utf-8'),
            user.password_hash.encode('utf-8')
        )

        if not password_matches:
            return None

        # Update last login timestamp
        user.last_login = datetime.now(timezone.utc)
        await session.flush()
        await session.refresh(user)

        return user

    @staticmethod
    async def update_password(session: AsyncSession, user: User, new_password: str) -> User:
        """Update user's password."""
        user.set_password(new_password)
        await session.flush()
        await session.refresh(user)
        return user

    @staticmethod
    async def update_user(
        session: AsyncSession,
        user: User,
        **kwargs
    ) -> User:
        """Update user fields."""
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)

        await session.flush()
        await session.refresh(user)
        return user

    @staticmethod
    async def create_password_reset_token(
        session: AsyncSession, user: User, expires_in_hours: int = 1
    ) -> PasswordResetToken:
        """Create a password reset token for user."""
        # Generate secure random token
        token = secrets.token_urlsafe(32)

        # Calculate expiration
        expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)

        # Create token record
        reset_token = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=expires_at,
            used=False
        )

        session.add(reset_token)
        await session.flush()
        await session.refresh(reset_token)
        return reset_token

    @staticmethod
    async def get_password_reset_token(
        session: AsyncSession, token: str
    ) -> Optional[PasswordResetToken]:
        """Get password reset token by token string."""
        result = await session.execute(
            select(PasswordResetToken).where(PasswordResetToken.token == token)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def use_password_reset_token(
        session: AsyncSession, reset_token: PasswordResetToken, new_password: str
    ) -> bool:
        """Use a password reset token to change password."""
        if not reset_token.is_valid():
            return False

        # Mark token as used
        reset_token.used = True

        # Update user password
        await UsersDatabase.update_password(session, reset_token.user, new_password)

        await session.flush()
        return True

    @staticmethod
    async def create_email_verification_token(
        session: AsyncSession, user: User, expires_in_hours: int = 24
    ) -> EmailVerificationToken:
        """Create an email verification token for user."""
        # Generate secure random token
        token = secrets.token_urlsafe(32)

        # Calculate expiration
        expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)

        # Create token record
        verification_token = EmailVerificationToken(
            user_id=user.id,
            token=token,
            expires_at=expires_at,
            used=False
        )

        session.add(verification_token)
        await session.flush()
        await session.refresh(verification_token)
        return verification_token

    @staticmethod
    async def get_email_verification_token(
        session: AsyncSession, token: str
    ) -> Optional[EmailVerificationToken]:
        """Get email verification token by token string."""
        result = await session.execute(
            select(EmailVerificationToken).where(EmailVerificationToken.token == token)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def verify_email(
        session: AsyncSession, verification_token: EmailVerificationToken
    ) -> bool:
        """Verify user's email using verification token."""
        if not verification_token.is_valid():
            return False

        # Mark token as used
        verification_token.used = True

        # Update user verification status
        user = verification_token.user
        user.is_verified = True

        await session.flush()
        return True

    @staticmethod
    async def deactivate_user(session: AsyncSession, user: User) -> User:
        """Deactivate a user account."""
        user.is_active = False
        await session.flush()
        await session.refresh(user)
        return user

    @staticmethod
    async def activate_user(session: AsyncSession, user: User) -> User:
        """Activate a user account."""
        user.is_active = True
        await session.flush()
        await session.refresh(user)
        return user
