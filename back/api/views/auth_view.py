"""Authentication views for SMTPy v2."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, Request
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from ..core.config import SETTINGS
from ..core.db import get_async_session
from ..database.users_database import UsersDatabase
from ..models import UserRole


router = APIRouter(prefix="/auth", tags=["authentication"])

# Session serializer for secure cookies
serializer = URLSafeTimedSerializer(SETTINGS.SECRET_KEY)
SESSION_COOKIE_NAME = "session"
SESSION_MAX_AGE = 7 * 24 * 60 * 60  # 7 days in seconds


# Pydantic models for request/response
class RegisterRequest(BaseModel):
    """User registration request."""
    username: str = Field(..., min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_-]+$')
    email: EmailStr
    password: str = Field(..., min_length=8)

    @field_validator('password')
    @classmethod
    def password_strength(cls, v):
        """Validate password strength."""
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() or not c.isalnum() for c in v):
            raise ValueError('Password must contain at least one number or special character')
        return v


class LoginRequest(BaseModel):
    """User login request."""
    username: str  # Can be username or email
    password: str


class PasswordResetRequest(BaseModel):
    """Password reset request."""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Reset password with token."""
    token: str
    new_password: str = Field(..., min_length=8)

    @field_validator('new_password')
    @classmethod
    def password_strength(cls, v):
        """Validate password strength."""
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() or not c.isalnum() for c in v):
            raise ValueError('Password must contain at least one number or special character')
        return v


class UserResponse(BaseModel):
    """User response model."""
    id: int
    username: str
    email: str
    is_active: bool
    role: str
    created_at: str
    updated_at: str


class AuthResponse(BaseModel):
    """Authentication response."""
    user: UserResponse
    access_token: Optional[str] = None


# Dependency to get current user from session
async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_async_session)
) -> Optional[dict]:
    """Get current user from session cookie."""
    session_cookie = request.cookies.get(SESSION_COOKIE_NAME)

    if not session_cookie:
        return None

    try:
        # Deserialize and verify session (max age: 7 days)
        user_id = serializer.loads(session_cookie, max_age=SESSION_MAX_AGE)

        # Get user from database
        user = await UsersDatabase.get_user_by_id(session, user_id)

        if not user or not user.is_active:
            return None

        return user.to_dict()

    except (BadSignature, SignatureExpired):
        return None


async def require_auth(current_user: Optional[dict] = Depends(get_current_user)):
    """Require authentication."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return current_user


@router.post("/register")
async def register(
    data: RegisterRequest,
    response: Response,
    session: AsyncSession = Depends(get_async_session)
):
    """Register a new user."""
    # Check if username already exists
    existing_user = await UsersDatabase.get_user_by_username(session, data.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    # Check if email already exists
    existing_email = await UsersDatabase.get_user_by_email(session, data.email)
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")

    try:
        # Create organization for the new user
        from ..models.organization import Organization

        organization = Organization(
            name=f"{data.username}'s Organization",
            email=data.email
        )
        session.add(organization)
        await session.flush()
        await session.refresh(organization)

        # Create new user with organization
        user = await UsersDatabase.create_user(
            session=session,
            username=data.username,
            email=data.email,
            password=data.password,
            organization_id=organization.id,
            role=UserRole.USER,
            is_verified=False  # Email verification can be added later
        )

        await session.commit()

        # Create session cookie
        session_token = serializer.dumps(user.id)
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=session_token,
            httponly=True,
            secure=SETTINGS.is_production,
            samesite="lax",
            max_age=SESSION_MAX_AGE
        )

        return {
            "success": True,
            "message": "User registered successfully",
            "data": {
                "user": UserResponse(**user.to_dict()),
                "access_token": session_token
            }
        }

    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@router.post("/login")
async def login(
    data: LoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_async_session)
):
    """Login user and create session."""
    # Verify credentials
    user = await UsersDatabase.verify_password(
        session=session,
        username_or_email=data.username,
        password=data.password
    )

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    try:
        # Extract user data before commit to avoid lazy loading issues
        user_id = user.id
        user_dict = user.to_dict()

        await session.commit()

        # Create session cookie
        session_token = serializer.dumps(user_id)
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=session_token,
            httponly=True,
            secure=SETTINGS.is_production,
            samesite="lax",
            max_age=SESSION_MAX_AGE
        )

        return {
            "success": True,
            "message": "Login successful",
            "data": {
                "user": UserResponse(**user_dict),
                "access_token": session_token
            }
        }

    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


@router.post("/logout")
async def logout(response: Response):
    """Logout user and clear session."""
    response.delete_cookie(key=SESSION_COOKIE_NAME)

    return {
        "success": True,
        "message": "Logged out successfully",
        "data": None
    }


@router.get("/me")
async def get_current_user_info(
    current_user: Optional[dict] = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get current authenticated user information."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Refresh user data from database
    user = await UsersDatabase.get_user_by_id(session, current_user["id"])

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "success": True,
        "data": UserResponse(**user.to_dict())
    }


@router.post("/request-password-reset")
async def request_password_reset(
    data: PasswordResetRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """Request a password reset token."""
    # Get user by email
    user = await UsersDatabase.get_user_by_email(session, data.email)

    # Don't reveal if email exists or not (security best practice)
    if not user:
        return {
            "success": True,
            "message": "If the email exists, a password reset link has been sent",
            "data": None
        }

    try:
        # Create password reset token
        reset_token = await UsersDatabase.create_password_reset_token(
            session=session,
            user=user,
            expires_in_hours=1
        )

        await session.commit()

        # TODO: Send email with reset link
        # For now, we'll just return success
        # In production, you would send an email here with:
        # reset_link = f"https://yourdomain.com/auth/reset-password?token={reset_token.token}"

        return {
            "success": True,
            "message": "If the email exists, a password reset link has been sent",
            "data": {
                "token": reset_token.token  # Only for testing; remove in production
            }
        }

    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create reset token: {str(e)}")


@router.post("/reset-password")
async def reset_password(
    data: ResetPasswordRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """Reset password using reset token."""
    # Get reset token
    reset_token = await UsersDatabase.get_password_reset_token(session, data.token)

    if not reset_token:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    if not reset_token.is_valid():
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    try:
        # Use token to reset password
        success = await UsersDatabase.use_password_reset_token(
            session=session,
            reset_token=reset_token,
            new_password=data.new_password
        )

        if not success:
            raise HTTPException(status_code=400, detail="Failed to reset password")

        await session.commit()

        return {
            "success": True,
            "message": "Password reset successfully",
            "data": None
        }

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to reset password: {str(e)}")
