"""User profile and settings views for SMTPy v2."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from shared.core.db import get_async_session
from ..database.users_database import UsersDatabase
from .auth_view import require_auth

router = APIRouter(prefix="/users", tags=["users"])


# Pydantic models
class UpdateProfileRequest(BaseModel):
    """Update user profile request."""
    email: EmailStr


class ChangePasswordRequest(BaseModel):
    """Change password request."""
    current_password: str
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


class UserPreferencesRequest(BaseModel):
    """User notification preferences."""
    email_on_new_message: bool = True
    email_on_domain_verified: bool = True
    email_on_quota_warning: bool = True
    email_weekly_summary: bool = False


@router.put("/profile", summary="Update User Profile")
async def update_profile(
        data: UpdateProfileRequest,
        current_user: dict = Depends(require_auth),
        session: AsyncSession = Depends(get_async_session)
):
    """Update user profile information."""
    user = await UsersDatabase.get_user_by_id(session, current_user["id"])

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if email is already taken by another user
    if data.email != user.email:
        existing_user = await UsersDatabase.get_user_by_email(session, data.email)
        if existing_user and existing_user.id != user.id:
            raise HTTPException(status_code=400, detail="Email already in use")

    try:
        # Update user email
        user = await UsersDatabase.update_user(session, user, email=data.email)
        await session.commit()

        return {
            "success": True,
            "message": "Profile updated successfully",
            "data": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_active": user.is_active,
                "role": user.role.value,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None
            }
        }

    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {str(e)}")


@router.post("/change-password", summary="Change Password")
async def change_password(
        data: ChangePasswordRequest,
        current_user: dict = Depends(require_auth),
        session: AsyncSession = Depends(get_async_session)
):
    """Change user password."""
    # Verify current password
    user = await UsersDatabase.verify_password(
        session=session,
        username_or_email=current_user["username"],
        password=data.current_password
    )

    if not user:
        raise HTTPException(status_code=401, detail="Current password is incorrect")

    try:
        # Update password
        await UsersDatabase.update_password(session, user, data.new_password)
        await session.commit()

        return {
            "success": True,
            "message": "Password changed successfully",
            "data": None
        }

    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to change password: {str(e)}")


@router.get("/preferences", summary="Get User Preferences")
async def get_preferences(
        current_user: dict = Depends(require_auth),
        session: AsyncSession = Depends(get_async_session)
):
    """Get user notification preferences."""
    user = await UsersDatabase.get_user_by_id(session, current_user["id"])

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # TODO: Store preferences in database
    # For now, return default preferences
    return {
        "success": True,
        "data": {
            "email_on_new_message": True,
            "email_on_domain_verified": True,
            "email_on_quota_warning": True,
            "email_weekly_summary": False
        }
    }


@router.put("/preferences", summary="Update User Preferences")
async def update_preferences(
        data: UserPreferencesRequest,
        current_user: dict = Depends(require_auth),
        session: AsyncSession = Depends(get_async_session)
):
    """Update user notification preferences."""
    user = await UsersDatabase.get_user_by_id(session, current_user["id"])

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # TODO: Store preferences in database
    # For now, just return success

    return {
        "success": True,
        "message": "Preferences updated successfully",
        "data": {
            "email_on_new_message": data.email_on_new_message,
            "email_on_domain_verified": data.email_on_domain_verified,
            "email_on_quota_warning": data.email_on_quota_warning,
            "email_weekly_summary": data.email_weekly_summary
        }
    }


@router.delete("/account", summary="Delete User Account")
async def delete_account(
        current_user: dict = Depends(require_auth),
        session: AsyncSession = Depends(get_async_session)
):
    """Delete user account (soft delete)."""
    user = await UsersDatabase.get_user_by_id(session, current_user["id"])

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        # Deactivate user account (soft delete)
        await UsersDatabase.deactivate_user(session, user)
        await session.commit()

        return {
            "success": True,
            "message": "Account deleted successfully",
            "data": None
        }

    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete account: {str(e)}")


# API Keys and Sessions will be implemented when we add proper session/token management
# For now, these are placeholder responses

@router.get("/api-keys", summary="List API Keys")
async def list_api_keys(
        current_user: dict = Depends(require_auth)
):
    """List user's API keys."""
    # TODO: Implement API key management
    return {
        "success": True,
        "data": []
    }


@router.post("/api-keys", summary="Generate API Key")
async def generate_api_key(
        current_user: dict = Depends(require_auth)
):
    """Generate a new API key."""
    # TODO: Implement API key generation
    import secrets
    api_key = f"sk_live_{secrets.token_urlsafe(32)}"

    return {
        "success": True,
        "message": "API key generated successfully",
        "data": {
            "key": api_key,
            "created_at": "2025-11-05T00:00:00Z"
        }
    }


@router.delete("/api-keys/{key_id}", summary="Revoke API Key")
async def revoke_api_key(
        key_id: str,
        current_user: dict = Depends(require_auth)
):
    """Revoke an API key."""
    # TODO: Implement API key revocation
    return {
        "success": True,
        "message": "API key revoked successfully",
        "data": None
    }


@router.get("/sessions", summary="List Active Sessions")
async def list_sessions(
        current_user: dict = Depends(require_auth)
):
    """List user's active sessions."""
    # TODO: Implement session management
    return {
        "success": True,
        "data": []
    }


@router.delete("/sessions/{session_id}", summary="Revoke Session")
async def revoke_session(
        session_id: str,
        current_user: dict = Depends(require_auth)
):
    """Revoke a specific session."""
    # TODO: Implement session revocation
    return {
        "success": True,
        "message": "Session revoked successfully",
        "data": None
    }


@router.delete("/sessions", summary="Revoke All Sessions")
async def revoke_all_sessions(
        current_user: dict = Depends(require_auth)
):
    """Revoke all sessions except current."""
    # TODO: Implement revoke all sessions
    return {
        "success": True,
        "message": "All other sessions revoked successfully",
        "data": None
    }
