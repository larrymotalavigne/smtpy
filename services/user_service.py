"""User service for authentication and user management."""

import secrets
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from .base import BaseService, ValidationError, NotFoundError, PermissionError
from database.models import User, Invitation
from utils.validation import validate_username, validate_email, validate_password
from utils.soft_delete import get_active_users, soft_delete_user


class UserService(BaseService[User]):
    """Service for user management and authentication."""
    
    def __init__(self):
        super().__init__(User)
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user with username and password.
        
        Args:
            username: The username to authenticate
            password: The password to verify
            
        Returns:
            The authenticated user or None if authentication fails
        """
        try:
            # Validate input
            username = validate_username(username)
            
            with self.get_db_session() as session:
                user = get_active_users(session).filter_by(username=username).first()
                
                if not user:
                    self.logger.warning(f"Authentication failed: user '{username}' not found")
                    return None
                
                if not user.is_active:
                    self.logger.warning(f"Authentication failed: user '{username}' is inactive")
                    return None
                
                if not self.pwd_context.verify(password, user.hashed_password):
                    self.logger.warning(f"Authentication failed: invalid password for user '{username}'")
                    return None
                
                self.logger.info(f"User '{username}' authenticated successfully")
                self.log_activity("user_login", {"username": username, "user_id": user.id})
                return user
                
        except Exception as e:
            self.logger.error(f"Authentication error for user '{username}': {e}")
            return None
    
    def create_user(self, username: str, password: str, email: Optional[str] = None, 
                   role: str = "user", invited_by: Optional[int] = None) -> User:
        """Create a new user.
        
        Args:
            username: The username for the new user
            password: The password for the new user
            email: Optional email address
            role: User role (default: "user")
            invited_by: ID of the user who invited this user
            
        Returns:
            The created user
            
        Raises:
            ValidationError: If input validation fails
            ServiceError: If user creation fails
        """
        try:
            # Validate input
            username = validate_username(username)
            password = validate_password(password)
            if email:
                email = validate_email(email)
            
            with self.get_db_session() as session:
                # Check if username already exists
                if get_active_users(session).filter_by(username=username).first():
                    raise ValidationError(f"Username '{username}' already exists")
                
                # Check if email already exists
                if email and get_active_users(session).filter_by(email=email).first():
                    raise ValidationError(f"Email '{email}' already registered")
                
                # Hash password
                hashed_password = self.pwd_context.hash(password)
                
                # Create user
                user_data = {
                    "username": username,
                    "hashed_password": hashed_password,
                    "email": email,
                    "role": role,
                    "is_active": bool(invited_by),  # Active if invited, inactive if self-registered
                    "email_verified": bool(invited_by),  # Verified if invited
                    "invited_by": invited_by
                }
                
                # Generate verification token if not invited
                if not invited_by and email:
                    user_data["verification_token"] = secrets.token_urlsafe(32)
                
                user = self.create(session, **user_data)
                
                self.log_activity("user_created", {
                    "user_id": user.id,
                    "username": username,
                    "email": email,
                    "role": role,
                    "invited": bool(invited_by)
                })
                
                return user
                
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to create user '{username}': {e}")
            raise
    
    def verify_email(self, token: str) -> Optional[User]:
        """Verify a user's email address using a verification token.
        
        Args:
            token: The verification token
            
        Returns:
            The verified user or None if token is invalid
        """
        try:
            with self.get_db_session() as session:
                user = get_active_users(session).filter_by(verification_token=token).first()
                
                if not user:
                    self.logger.warning(f"Email verification failed: invalid token")
                    return None
                
                # Update user
                user.is_active = True
                user.email_verified = True
                user.verification_token = None
                session.commit()
                
                self.logger.info(f"Email verified for user '{user.username}'")
                self.log_activity("email_verified", {"user_id": user.id, "username": user.username})
                
                return user
                
        except Exception as e:
            self.logger.error(f"Email verification error: {e}")
            return None
    
    def create_invitation(self, email: str, invited_by_id: int) -> Invitation:
        """Create an invitation for a new user.
        
        Args:
            email: Email address to invite
            invited_by_id: ID of the user creating the invitation
            
        Returns:
            The created invitation
            
        Raises:
            ValidationError: If email is invalid or already registered
        """
        try:
            # Validate email
            email = validate_email(email)
            
            with self.get_db_session() as session:
                # Check if email already registered
                if get_active_users(session).filter_by(email=email).first():
                    raise ValidationError(f"Email '{email}' already registered")
                
                # Check if invitation already exists
                existing_invitation = session.query(Invitation).filter_by(email=email).first()
                if existing_invitation and existing_invitation.expires_at > datetime.utcnow():
                    raise ValidationError(f"Invitation already sent to '{email}'")
                
                # Create invitation
                token = secrets.token_urlsafe(32)
                expires_at = datetime.utcnow() + timedelta(hours=24)
                
                invitation = Invitation(
                    email=email,
                    token=token,
                    expires_at=expires_at,
                    invited_by=invited_by_id
                )
                
                session.add(invitation)
                session.commit()
                session.refresh(invitation)
                
                self.log_activity("invitation_created", {
                    "email": email,
                    "invited_by": invited_by_id,
                    "token": token
                })
                
                return invitation
                
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to create invitation for '{email}': {e}")
            raise
    
    def get_user_by_invitation_token(self, token: str) -> Optional[Invitation]:
        """Get invitation by token.
        
        Args:
            token: The invitation token
            
        Returns:
            The invitation or None if not found/expired
        """
        try:
            with self.get_db_session() as session:
                invitation = session.query(Invitation).filter_by(token=token).first()
                
                if not invitation:
                    return None
                
                if invitation.expires_at < datetime.utcnow():
                    self.logger.warning(f"Invitation token expired for email '{invitation.email}'")
                    return None
                
                return invitation
                
        except Exception as e:
            self.logger.error(f"Error retrieving invitation: {e}")
            return None
    
    def update_user(self, user_id: int, current_user_id: int, current_user_role: str, **kwargs) -> User:
        """Update a user's information.
        
        Args:
            user_id: ID of the user to update
            current_user_id: ID of the user making the request
            current_user_role: Role of the user making the request
            **kwargs: Fields to update
            
        Returns:
            The updated user
            
        Raises:
            NotFoundError: If user not found
            PermissionError: If user lacks permission
            ValidationError: If validation fails
        """
        try:
            with self.get_db_session() as session:
                user = self.get_by_id_or_404(user_id, session)
                
                # Check permissions
                if current_user_role != "admin" and current_user_id != user_id:
                    raise PermissionError("You can only update your own profile")
                
                # Validate updates
                if "email" in kwargs and kwargs["email"]:
                    kwargs["email"] = validate_email(kwargs["email"])
                    
                    # Check if email already exists (excluding current user)
                    existing_user = get_active_users(session).filter_by(email=kwargs["email"]).first()
                    if existing_user and existing_user.id != user_id:
                        raise ValidationError(f"Email '{kwargs['email']}' already registered")
                
                if "password" in kwargs:
                    kwargs["password"] = validate_password(kwargs["password"])
                    kwargs["hashed_password"] = self.pwd_context.hash(kwargs["password"])
                    del kwargs["password"]  # Don't store plain password
                
                # Only admins can change roles
                if "role" in kwargs and current_user_role != "admin":
                    del kwargs["role"]
                
                updated_user = self.update(session, user, **kwargs)
                
                self.log_activity("user_updated", {
                    "user_id": user_id,
                    "updated_by": current_user_id,
                    "fields": list(kwargs.keys())
                })
                
                return updated_user
                
        except (NotFoundError, PermissionError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Failed to update user {user_id}: {e}")
            raise
    
    def delete_user(self, user_id: int, current_user_id: int, current_user_role: str) -> bool:
        """Soft delete a user.
        
        Args:
            user_id: ID of the user to delete
            current_user_id: ID of the user making the request
            current_user_role: Role of the user making the request
            
        Raises:
            NotFoundError: If user not found
            PermissionError: If user lacks permission
            ValidationError: If trying to delete self
        """
        try:
            with self.get_db_session() as session:
                user = self.get_by_id_or_404(user_id, session)
                
                # Check permissions
                if current_user_role != "admin":
                    raise PermissionError("Only admins can delete users")
                
                # Prevent self-deletion
                if current_user_id == user_id:
                    raise ValidationError("Cannot delete yourself")
                
                # Soft delete user and cascade to domains/aliases
                soft_delete_user(session, user_id)
                
                self.log_activity("user_deleted", {
                    "user_id": user_id,
                    "username": user.username,
                    "deleted_by": current_user_id
                })
                
                return True
                
        except (NotFoundError, PermissionError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Failed to delete user {user_id}: {e}")
            raise
    
    def get_all_users(self, current_user_role: str) -> List[User]:
        """Get all active users (admin only).
        
        Args:
            current_user_role: Role of the user making the request
            
        Returns:
            List of all active users
            
        Raises:
            PermissionError: If user is not admin
        """
        if current_user_role != "admin":
            raise PermissionError("Only admins can view all users")
        
        try:
            with self.get_db_session() as session:
                return get_active_users(session).all()
        except Exception as e:
            self.logger.error(f"Failed to get all users: {e}")
            raise