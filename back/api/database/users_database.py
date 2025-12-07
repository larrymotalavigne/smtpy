"""User database operations for SMTPy v2."""

import bcrypt
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import (
    User, PasswordResetToken, EmailVerificationToken, UserRole,
    UserPreferences, APIKey, Session
)


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

    # ========== User Preferences Operations ==========

    @staticmethod
    async def get_user_preferences(
        session: AsyncSession, user_id: int
    ) -> Optional[UserPreferences]:
        """Get user preferences by user ID."""
        result = await session.execute(
            select(UserPreferences).where(UserPreferences.user_id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_user_preferences(
        session: AsyncSession,
        user_id: int,
        **preferences
    ) -> UserPreferences:
        """Create user preferences with default values."""
        user_prefs = UserPreferences(
            user_id=user_id,
            **preferences
        )
        session.add(user_prefs)
        await session.flush()
        await session.refresh(user_prefs)
        return user_prefs

    @staticmethod
    async def update_user_preferences(
        session: AsyncSession,
        user_prefs: UserPreferences,
        **updates
    ) -> UserPreferences:
        """Update user preferences."""
        for key, value in updates.items():
            if hasattr(user_prefs, key):
                setattr(user_prefs, key, value)

        await session.flush()
        await session.refresh(user_prefs)
        return user_prefs

    @staticmethod
    async def get_or_create_preferences(
        session: AsyncSession, user_id: int
    ) -> UserPreferences:
        """Get user preferences or create with defaults if not exists."""
        prefs = await UsersDatabase.get_user_preferences(session, user_id)
        if not prefs:
            prefs = await UsersDatabase.create_user_preferences(session, user_id)
        return prefs

    # ========== API Key Operations ==========

    @staticmethod
    async def create_api_key(
        session: AsyncSession,
        user_id: int,
        name: str,
        expires_at: Optional[datetime] = None
    ) -> tuple[APIKey, str]:
        """
        Create a new API key for user.

        Returns:
            tuple: (APIKey instance, full_key string)
                The full_key should be returned to user only once during creation.
        """
        # Generate API key
        full_key, key_hash, prefix = APIKey.generate_key()

        # Create API key record
        api_key = APIKey(
            user_id=user_id,
            name=name,
            key_hash=key_hash,
            prefix=prefix,
            expires_at=expires_at,
            is_active=True
        )

        session.add(api_key)
        await session.flush()
        await session.refresh(api_key)

        return api_key, full_key

    @staticmethod
    async def get_api_keys(
        session: AsyncSession, user_id: int, active_only: bool = True
    ) -> list[APIKey]:
        """Get all API keys for a user."""
        query = select(APIKey).where(APIKey.user_id == user_id)

        if active_only:
            query = query.where(APIKey.is_active == True)

        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_api_key_by_id(
        session: AsyncSession, key_id: int
    ) -> Optional[APIKey]:
        """Get API key by ID."""
        result = await session.execute(
            select(APIKey).where(APIKey.id == key_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_api_key_by_prefix(
        session: AsyncSession, prefix: str
    ) -> list[APIKey]:
        """Get API keys by prefix (there might be multiple with same prefix)."""
        result = await session.execute(
            select(APIKey).where(APIKey.prefix == prefix, APIKey.is_active == True)
        )
        return list(result.scalars().all())

    @staticmethod
    async def verify_api_key(
        session: AsyncSession, key: str
    ) -> Optional[User]:
        """
        Verify an API key and return the associated user if valid.

        Args:
            key: The full API key string

        Returns:
            User object if key is valid, None otherwise
        """
        # Extract prefix from key
        if not key.startswith("smtpy_sk_"):
            return None

        prefix = key[:16]

        # Get all active keys with this prefix
        api_keys = await UsersDatabase.get_api_key_by_prefix(session, prefix)

        # Try to verify against each key (should typically be only one)
        for api_key in api_keys:
            if api_key.verify_key(key) and api_key.is_valid():
                # Update last used timestamp
                api_key.last_used_at = datetime.now(timezone.utc)
                await session.flush()

                # Return the user
                return api_key.user

        return None

    @staticmethod
    async def revoke_api_key(
        session: AsyncSession, api_key: APIKey
    ) -> APIKey:
        """Revoke (deactivate) an API key."""
        api_key.is_active = False
        await session.flush()
        await session.refresh(api_key)
        return api_key

    @staticmethod
    async def delete_api_key(
        session: AsyncSession, api_key: APIKey
    ) -> None:
        """Permanently delete an API key."""
        await session.delete(api_key)
        await session.flush()

    # ========== Session Operations ==========

    @staticmethod
    async def create_session(
        session: AsyncSession,
        user_id: int,
        session_token: str,
        expires_at: datetime,
        device_info: Optional[dict] = None,
        ip_address: Optional[str] = None,
        location: Optional[str] = None
    ) -> Session:
        """Create a new session for user."""
        user_session = Session(
            user_id=user_id,
            session_token=session_token,
            device_info=device_info,
            ip_address=ip_address,
            location=location,
            last_activity_at=datetime.now(timezone.utc),
            expires_at=expires_at,
            is_active=True
        )

        session.add(user_session)
        await session.flush()
        await session.refresh(user_session)
        return user_session

    @staticmethod
    async def get_session_by_token(
        session: AsyncSession, session_token: str
    ) -> Optional[Session]:
        """Get session by token."""
        result = await session.execute(
            select(Session).where(Session.session_token == session_token)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_sessions(
        session: AsyncSession, user_id: int, active_only: bool = True
    ) -> list[Session]:
        """Get all sessions for a user."""
        query = select(Session).where(Session.user_id == user_id)

        if active_only:
            query = query.where(Session.is_active == True)

        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def update_session_activity(
        session: AsyncSession, user_session: Session
    ) -> Session:
        """Update session last activity timestamp."""
        user_session.last_activity_at = datetime.now(timezone.utc)
        await session.flush()
        await session.refresh(user_session)
        return user_session

    @staticmethod
    async def revoke_session(
        session: AsyncSession, user_session: Session
    ) -> Session:
        """Revoke (deactivate) a session."""
        user_session.is_active = False
        await session.flush()
        await session.refresh(user_session)
        return user_session

    @staticmethod
    async def revoke_all_user_sessions(
        session: AsyncSession, user_id: int, except_token: Optional[str] = None
    ) -> int:
        """
        Revoke all sessions for a user, optionally except the current one.

        Returns:
            Number of sessions revoked
        """
        sessions = await UsersDatabase.get_user_sessions(session, user_id, active_only=True)

        count = 0
        for user_session in sessions:
            if except_token and user_session.session_token == except_token:
                continue

            user_session.is_active = False
            count += 1

        await session.flush()
        return count

    @staticmethod
    async def cleanup_expired_sessions(session: AsyncSession) -> int:
        """
        Clean up expired sessions (mark as inactive).

        Returns:
            Number of sessions cleaned up
        """
        now = datetime.now(timezone.utc)

        result = await session.execute(
            select(Session).where(
                Session.is_active == True,
                Session.expires_at < now
            )
        )
        expired_sessions = list(result.scalars().all())

        for user_session in expired_sessions:
            user_session.is_active = False

        await session.flush()
        return len(expired_sessions)
