"""Unit tests for authentication functionality."""

import pytest
from datetime import datetime, timedelta, timezone

from api.models import User, PasswordResetToken, EmailVerificationToken, UserRole


class TestUserModel:
    """Test User model functionality."""

    def test_set_password(self):
        """Test password hashing."""
        user = User(
            username="testuser",
            email="test@example.com",
            role=UserRole.USER
        )

        password = "SecurePass123!"
        user.set_password(password)

        assert user.password_hash is not None
        assert user.password_hash != password
        assert len(user.password_hash) > 0

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        user = User(
            username="testuser",
            email="test@example.com",
            role=UserRole.USER
        )

        password = "SecurePass123!"
        user.set_password(password)

        assert user.verify_password(password) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        user = User(
            username="testuser",
            email="test@example.com",
            role=UserRole.USER
        )

        user.set_password("SecurePass123!")

        assert user.verify_password("WrongPassword") is False

    def test_password_hash_different_for_same_password(self):
        """Test that same password generates different hashes (bcrypt salt)."""
        password = "SecurePass123!"

        user1 = User(username="user1", email="user1@example.com", role=UserRole.USER)
        user1.set_password(password)

        user2 = User(username="user2", email="user2@example.com", role=UserRole.USER)
        user2.set_password(password)

        # Hashes should be different due to salt
        assert user1.password_hash != user2.password_hash

        # But both should verify correctly
        assert user1.verify_password(password) is True
        assert user2.verify_password(password) is True

    def test_is_admin_property(self):
        """Test is_admin property."""
        user_regular = User(username="user", email="user@example.com", role=UserRole.USER)
        assert user_regular.is_admin is False

        user_admin = User(username="admin", email="admin@example.com", role=UserRole.ADMIN)
        assert user_admin.is_admin is True

    def test_to_dict_excludes_password_by_default(self):
        """Test to_dict method excludes password hash by default."""
        user = User(
            username="testuser",
            email="test@example.com",
            role=UserRole.USER,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        user.set_password("SecurePass123!")

        user_dict = user.to_dict()

        assert "password_hash" not in user_dict
        assert user_dict["username"] == "testuser"
        assert user_dict["email"] == "test@example.com"
        assert user_dict["role"] == "user"

    def test_to_dict_includes_password_when_requested(self):
        """Test to_dict method includes password hash when requested."""
        user = User(
            username="testuser",
            email="test@example.com",
            role=UserRole.USER,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        user.set_password("SecurePass123!")

        user_dict = user.to_dict(include_sensitive=True)

        assert "password_hash" in user_dict
        assert user_dict["password_hash"] == user.password_hash


class TestPasswordResetToken:
    """Test PasswordResetToken model."""

    def test_is_valid_not_used_not_expired(self):
        """Test token is valid when not used and not expired."""
        token = PasswordResetToken(
            user_id=1,
            token="test_token",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            used=False
        )

        assert token.is_valid() is True

    def test_is_valid_used(self):
        """Test token is invalid when used."""
        token = PasswordResetToken(
            user_id=1,
            token="test_token",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            used=True
        )

        assert token.is_valid() is False

    def test_is_valid_expired(self):
        """Test token is invalid when expired."""
        token = PasswordResetToken(
            user_id=1,
            token="test_token",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
            used=False
        )

        assert token.is_valid() is False

    def test_is_valid_used_and_expired(self):
        """Test token is invalid when both used and expired."""
        token = PasswordResetToken(
            user_id=1,
            token="test_token",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
            used=True
        )

        assert token.is_valid() is False


class TestEmailVerificationToken:
    """Test EmailVerificationToken model."""

    def test_is_valid_not_used_not_expired(self):
        """Test token is valid when not used and not expired."""
        token = EmailVerificationToken(
            user_id=1,
            token="test_token",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
            used=False
        )

        assert token.is_valid() is True

    def test_is_valid_used(self):
        """Test token is invalid when used."""
        token = EmailVerificationToken(
            user_id=1,
            token="test_token",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
            used=True
        )

        assert token.is_valid() is False

    def test_is_valid_expired(self):
        """Test token is invalid when expired."""
        token = EmailVerificationToken(
            user_id=1,
            token="test_token",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
            used=False
        )

        assert token.is_valid() is False
