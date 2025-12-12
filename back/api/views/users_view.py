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
    theme: str = "light"
    language: str = "en"


class CreateAPIKeyRequest(BaseModel):
    """Create API key request."""
    name: str = Field(..., min_length=1, max_length=100, description="Name for the API key")


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

    # Get or create preferences
    prefs = await UsersDatabase.get_or_create_preferences(session, current_user["id"])
    await session.commit()

    return {
        "success": True,
        "data": {
            "email_on_new_message": prefs.email_on_new_message,
            "email_on_domain_verified": prefs.email_on_domain_verified,
            "email_on_quota_warning": prefs.email_on_quota_warning,
            "email_weekly_summary": prefs.email_weekly_summary,
            "theme": prefs.theme,
            "language": prefs.language
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

    try:
        # Get or create preferences
        prefs = await UsersDatabase.get_or_create_preferences(session, current_user["id"])

        # Update preferences
        prefs = await UsersDatabase.update_user_preferences(
            session, prefs,
            email_on_new_message=data.email_on_new_message,
            email_on_domain_verified=data.email_on_domain_verified,
            email_on_quota_warning=data.email_on_quota_warning,
            email_weekly_summary=data.email_weekly_summary,
            theme=data.theme,
            language=data.language
        )
        await session.commit()

        return {
            "success": True,
            "message": "Preferences updated successfully",
            "data": {
                "email_on_new_message": prefs.email_on_new_message,
                "email_on_domain_verified": prefs.email_on_domain_verified,
                "email_on_quota_warning": prefs.email_on_quota_warning,
                "email_weekly_summary": prefs.email_weekly_summary,
                "theme": prefs.theme,
                "language": prefs.language
            }
        }
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update preferences: {str(e)}")


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
        current_user: dict = Depends(require_auth),
        session: AsyncSession = Depends(get_async_session)
):
    """List user's API keys."""
    try:
        api_keys = await UsersDatabase.get_api_keys(session, current_user["id"], active_only=True)

        return {
            "success": True,
            "data": [
                {
                    "id": str(key.id),
                    "name": key.name,
                    "key": f"{key.prefix}_{'*' * 24}",  # Masked key for display
                    "created_at": key.created_at.isoformat() if key.created_at else None,
                    "last_used": key.last_used_at.isoformat() if key.last_used_at else None
                }
                for key in api_keys
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list API keys: {str(e)}")


@router.post("/api-keys", summary="Generate API Key")
async def generate_api_key(
        data: CreateAPIKeyRequest,
        current_user: dict = Depends(require_auth),
        session: AsyncSession = Depends(get_async_session)
):
    """Generate a new API key."""
    try:
        # Create API key
        api_key, full_key = await UsersDatabase.create_api_key(
            session, current_user["id"], data.name
        )
        await session.commit()

        return {
            "success": True,
            "message": "API key generated successfully. Save this key now - it won't be shown again!",
            "data": {
                "id": api_key.id,
                "name": api_key.name,
                "key": full_key,  # Only shown once!
                "prefix": api_key.prefix,
                "created_at": api_key.created_at.isoformat() if api_key.created_at else None
            }
        }
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to generate API key: {str(e)}")


@router.delete("/api-keys/{key_id}", summary="Revoke API Key")
async def revoke_api_key(
        key_id: int,
        current_user: dict = Depends(require_auth),
        session: AsyncSession = Depends(get_async_session)
):
    """Revoke an API key."""
    try:
        # Get the API key
        api_key = await UsersDatabase.get_api_key_by_id(session, key_id)

        if not api_key:
            raise HTTPException(status_code=404, detail="API key not found")

        # Verify ownership
        if api_key.user_id != current_user["id"]:
            raise HTTPException(status_code=403, detail="You don't have permission to revoke this API key")

        # Revoke the key
        await UsersDatabase.revoke_api_key(session, api_key)
        await session.commit()

        return {
            "success": True,
            "message": "API key revoked successfully",
            "data": None
        }
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to revoke API key: {str(e)}")


@router.get("/sessions", summary="List Active Sessions")
async def list_sessions(
        current_user: dict = Depends(require_auth),
        session: AsyncSession = Depends(get_async_session)
):
    """List user's active sessions."""
    try:
        sessions = await UsersDatabase.get_user_sessions(session, current_user["id"], active_only=True)

        # Get current session token from auth
        current_session_token = current_user.get("session_token")

        return {
            "success": True,
            "data": [
                {
                    "id": str(s.id),
                    "device": s.device_info.get("device", "Unknown Device") if isinstance(s.device_info, dict) else str(s.device_info or "Unknown Device"),
                    "location": s.location or "Unknown Location",
                    "ip_address": s.ip_address or "Unknown IP",
                    "last_active": s.last_activity_at.isoformat() if s.last_activity_at else None,
                    "is_current": s.session_token == current_session_token if current_session_token else False
                }
                for s in sessions
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")


@router.delete("/sessions/{session_id}", summary="Revoke Session")
async def revoke_session(
        session_id: int,
        current_user: dict = Depends(require_auth),
        session: AsyncSession = Depends(get_async_session)
):
    """Revoke a specific session."""
    try:
        # Get all user sessions
        user_sessions = await UsersDatabase.get_user_sessions(session, current_user["id"], active_only=False)

        # Find the target session
        target_session = None
        for s in user_sessions:
            if s.id == session_id:
                target_session = s
                break

        if not target_session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Verify ownership (should already be verified by above, but double-check)
        if target_session.user_id != current_user["id"]:
            raise HTTPException(status_code=403, detail="You don't have permission to revoke this session")

        # Revoke the session
        await UsersDatabase.revoke_session(session, target_session)
        await session.commit()

        return {
            "success": True,
            "message": "Session revoked successfully",
            "data": None
        }
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to revoke session: {str(e)}")


@router.delete("/sessions", summary="Revoke All Sessions")
async def revoke_all_sessions(
        current_user: dict = Depends(require_auth),
        session: AsyncSession = Depends(get_async_session)
):
    """Revoke all sessions except current."""
    try:
        # Get current session token from the request (if available)
        # For now, we'll revoke all sessions - in production you'd want to preserve the current one
        # This would require access to the request object to get the session cookie

        count = await UsersDatabase.revoke_all_user_sessions(
            session, current_user["id"], except_token=None
        )
        await session.commit()

        return {
            "success": True,
            "message": f"Successfully revoked {count} session(s)",
            "data": {"revoked_count": count}
        }
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to revoke sessions: {str(e)}")
