"""Authentication views for SMTPy v2."""

import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, Request
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from shared.core.config import SETTINGS
from shared.core.db import get_async_session
from ..database.users_database import UsersDatabase
from shared.models import UserRole

router = APIRouter(prefix="/auth", tags=["authentication"])

# Session serializer for secure cookies
serializer = URLSafeTimedSerializer(SETTINGS.SECRET_KEY)
SESSION_COOKIE_NAME = "session"
SESSION_MAX_AGE = 7 * 24 * 60 * 60  # 7 days in seconds

# Cookie security settings (adjust for test environment)
IS_TESTING = os.getenv("TESTING", "False").lower() == "true"
COOKIE_SECURE = not IS_TESTING  # Disable secure flag in tests (uses HTTP not HTTPS)
COOKIE_SAMESITE = "lax" if IS_TESTING else "none"  # Use 'lax' for tests, 'none' for production


# Pydantic models for request/response
class RegisterRequest(BaseModel):
    """User registration request."""
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=r'^[a-zA-Z0-9_-]+$',
        description="Username (3-50 characters, alphanumeric with dashes/underscores)",
        examples=["john_doe", "user123"]
    )
    email: EmailStr = Field(
        ...,
        description="Valid email address",
        examples=["user@example.com"]
    )
    password: str = Field(
        ...,
        min_length=8,
        description="Password (min 8 chars, must include uppercase, lowercase, and number/special char)",
        examples=["SecurePass123!"]
    )

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

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "username": "john_doe",
                    "email": "john@example.com",
                    "password": "SecurePass123!"
                }
            ]
        }
    }


class LoginRequest(BaseModel):
    """User login request."""
    username: str = Field(
        ...,
        description="Username or email address",
        examples=["admin", "user@example.com"]
    )
    password: str = Field(
        ...,
        description="User password",
        examples=["password"]
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "username": "admin",
                    "password": "password"
                }
            ]
        }
    }


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


class VerifyEmailRequest(BaseModel):
    """Verify email with token."""
    token: str


class ResendVerificationRequest(BaseModel):
    """Resend email verification."""
    email: EmailStr


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
        response: Response,
        session: AsyncSession = Depends(get_async_session)
) -> Optional[dict]:
    """Get current user from session cookie and refresh it (sliding window)."""
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

        # Refresh session cookie with new expiration (sliding window)
        # This keeps the user logged in as long as they're active
        new_session_token = serializer.dumps(user.id)
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=new_session_token,
            httponly=True,
            secure=COOKIE_SECURE,
            samesite=COOKIE_SAMESITE,
            max_age=SESSION_MAX_AGE
        )

        return user.to_dict()

    except (BadSignature, SignatureExpired):
        return None


async def require_auth(current_user: Optional[dict] = Depends(get_current_user)):
    """Require authentication."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return current_user


@router.post(
    "/register",
    summary="Register New User",
    description="""
    Register a new user account with the following steps:

    1. Validates username, email, and password requirements
    2. Creates a new organization for the user
    3. Creates the user account with USER role
    4. Automatically logs in the user with a session cookie

    **Password Requirements:**
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number or special character

    **Rate Limit:** 10 requests per minute
    """,
    responses={
        200: {
            "description": "User registered successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "User registered successfully",
                        "data": {
                            "user": {
                                "id": 1,
                                "username": "john_doe",
                                "email": "john@example.com",
                                "is_active": True,
                                "role": "user",
                                "created_at": "2025-10-28T12:00:00",
                                "updated_at": "2025-10-28T12:00:00"
                            }
                        }
                    }
                }
            }
        },
        400: {
            "description": "Username or email already registered",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Username already registered"
                    }
                }
            }
        },
        422: {
            "description": "Validation error (invalid email, weak password, etc.)",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "type": "value_error",
                                "loc": ["body", "password"],
                                "msg": "Password must contain at least one uppercase letter"
                            }
                        ]
                    }
                }
            }
        }
    }
)
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
        from shared.models.organization import Organization

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

        # Send verification email via Docker mailserver
        from ..services.email_service import EmailService
        import logging
        logger = logging.getLogger(__name__)

        try:
            # Create email verification token
            verification_token = await UsersDatabase.create_email_verification_token(
                session=session,
                user=user,
                expires_in_hours=24
            )
            await session.commit()

            # Send verification email
            await EmailService.send_email_verification(
                to=user.email,
                username=user.username,
                verification_token=verification_token.token
            )
        except Exception as e:
            logger.error(f"Failed to send verification email: {str(e)}")
            # Don't fail registration if email fails

        # Create session cookie
        session_token = serializer.dumps(user.id)
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=session_token,
            httponly=True,
            secure=COOKIE_SECURE,
            samesite=COOKIE_SAMESITE,
            max_age=SESSION_MAX_AGE
        )

        return {
            "success": True,
            "message": "User registered successfully. Please check your email to verify your account.",
            "data": {
                "user": UserResponse(**user.to_dict()),
                "access_token": session_token
            }
        }

    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@router.post(
    "/login",
    summary="User Login",
    description="""
    Authenticate user and create a session cookie.

    **Authentication Flow:**
    1. Accepts username or email address
    2. Verifies password using bcrypt
    3. Creates secure session cookie (HTTP-only, 7-day expiry)
    4. Returns user profile and session token

    **Rate Limit:** 10 requests per minute

    **Session Cookie:**
    - Name: `session`
    - HTTP-only: True
    - Secure: True (in production)
    - SameSite: Lax
    - Max-Age: 7 days
    """,
    responses={
        200: {
            "description": "Login successful",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Login successful",
                        "data": {
                            "user": {
                                "id": 1,
                                "username": "admin",
                                "email": "admin@example.com",
                                "is_active": True,
                                "role": "admin",
                                "created_at": "2025-10-28T12:00:00",
                                "updated_at": "2025-10-28T12:00:00"
                            },
                            "access_token": "session_token_here"
                        }
                    }
                }
            }
        },
        401: {
            "description": "Invalid credentials",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid credentials"
                    }
                }
            }
        }
    }
)
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
            secure=COOKIE_SECURE,
            samesite=COOKIE_SAMESITE,
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

        # Send password reset email via Docker mailserver
        from ..services.email_service import EmailService
        import logging
        logger = logging.getLogger(__name__)

        try:
            email_sent = await EmailService.send_password_reset_email(
                to=user.email,
                username=user.username,
                reset_token=reset_token.token
            )

            if not email_sent:
                # Log error but still return success (don't reveal if email exists)
                logger.error(f"Failed to send password reset email to {user.email}")
        except Exception as e:
            logger.error(f"Error sending password reset email: {str(e)}")

        return {
            "success": True,
            "message": "If the email exists, a password reset link has been sent",
            "data": None  # Never expose tokens in production
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


@router.post(
    "/verify-email",
    summary="Verify Email Address",
    description="Verify user email address with verification token sent during registration"
)
async def verify_email(
        data: VerifyEmailRequest,
        session: AsyncSession = Depends(get_async_session)
):
    """Verify user email with token."""
    # Get verification token
    verification_token = await UsersDatabase.get_email_verification_token(session, data.token)

    if not verification_token:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")

    if not verification_token.is_valid():
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")

    try:
        # Verify email
        success = await UsersDatabase.verify_email(session, verification_token)

        if not success:
            raise HTTPException(status_code=400, detail="Failed to verify email")

        await session.commit()

        return {
            "success": True,
            "message": "Email verified successfully",
            "data": None
        }

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to verify email: {str(e)}")


@router.post(
    "/resend-verification",
    summary="Resend Email Verification",
    description="Resend email verification link to user's email address"
)
async def resend_verification(
        data: ResendVerificationRequest,
        session: AsyncSession = Depends(get_async_session)
):
    """Resend email verification link."""
    # Get user by email
    user = await UsersDatabase.get_user_by_email(session, data.email)

    # Don't reveal if email exists (security best practice)
    if not user:
        return {
            "success": True,
            "message": "If the email exists and is not yet verified, a verification link has been sent",
            "data": None
        }

    # Check if already verified
    if user.is_verified:
        return {
            "success": True,
            "message": "Email is already verified",
            "data": None
        }

    try:
        # Create new verification token
        verification_token = await UsersDatabase.create_email_verification_token(
            session=session,
            user=user,
            expires_in_hours=24
        )

        await session.commit()

        # Send verification email
        from ..services.email_service import EmailService

        email_sent = EmailService.send_email_verification(
            to=user.email,
            username=user.username,
            verification_token=verification_token.token
        )

        if not email_sent:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send verification email to {user.email}")

        return {
            "success": True,
            "message": "If the email exists and is not yet verified, a verification link has been sent",
            "data": None
        }

    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to resend verification: {str(e)}")
