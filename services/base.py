"""Base service class for SMTPy application."""

from abc import ABC
from typing import Optional, Type, TypeVar, Generic
from contextlib import contextmanager
from sqlalchemy.orm import Session

from utils.db import get_session
from utils.logging_config import get_logger
from utils.error_handling import (
    SMTPyError, DatabaseError, ValidationError as SMTPyValidationError, 
    ResourceNotFoundError, AuthorizationError, handle_database_error, ErrorContext
)
from database.models import Base

T = TypeVar('T', bound=Base)


# Use the centralized error handling system
ServiceError = SMTPyError
ValidationError = SMTPyValidationError
NotFoundError = ResourceNotFoundError
PermissionError = AuthorizationError


class BaseService(ABC, Generic[T]):
    """Base service class providing common functionality."""
    
    def __init__(self, model_class: Optional[Type[T]] = None):
        """Initialize the service.
        
        Args:
            model_class: The SQLAlchemy model class this service manages
        """
        self.model_class = model_class
        self.logger = get_logger(self.__class__.__name__.lower())
    
    @contextmanager
    def get_db_session(self):
        """Get a database session with automatic cleanup."""
        with get_session() as session:
            try:
                with ErrorContext(f"{self.__class__.__name__}_database_operation"):
                    yield session
            except Exception as e:
                self.logger.error(f"Database error in {self.__class__.__name__}: {e}")
                session.rollback()
                raise DatabaseError(
                    message=f"Database operation failed: {str(e)}",
                    details={"service": self.__class__.__name__}
                ) from e
    
    def get_by_id(self, id: int, session: Optional[Session] = None) -> Optional[T]:
        """Get a model instance by ID.
        
        Args:
            id: The ID of the instance to retrieve
            session: Optional database session to use
            
        Returns:
            The model instance or None if not found
        """
        if not self.model_class:
            raise NotImplementedError("model_class must be set")
        
        if session:
            return session.get(self.model_class, id)
        
        with self.get_db_session() as db_session:
            return db_session.get(self.model_class, id)
    
    def get_by_id_or_404(self, id: int, session: Optional[Session] = None) -> T:
        """Get a model instance by ID or raise NotFoundError.
        
        Args:
            id: The ID of the instance to retrieve
            session: Optional database session to use
            
        Returns:
            The model instance
            
        Raises:
            NotFoundError: If the instance is not found
        """
        instance = self.get_by_id(id, session)
        if not instance:
            raise NotFoundError(f"{self.model_class.__name__} with id {id} not found")
        return instance
    
    @handle_database_error
    def create(self, session: Session, **kwargs) -> T:
        """Create a new model instance.
        
        Args:
            session: Database session to use
            **kwargs: Fields to set on the new instance
            
        Returns:
            The created instance
        """
        if not self.model_class:
            raise NotImplementedError("model_class must be set")
        
        try:
            instance = self.model_class(**kwargs)
            session.add(instance)
            session.commit()
            session.refresh(instance)
            
            self.logger.info(f"Created {self.model_class.__name__} with id {instance.id}")
            return instance
            
        except Exception as e:
            session.rollback()
            self.logger.error(f"Failed to create {self.model_class.__name__}: {e}")
            raise ServiceError(f"Failed to create {self.model_class.__name__}: {str(e)}") from e
    
    @handle_database_error
    def update(self, session: Session, instance: T, **kwargs) -> T:
        """Update a model instance.
        
        Args:
            session: Database session to use
            instance: The instance to update
            **kwargs: Fields to update
            
        Returns:
            The updated instance
        """
        try:
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            
            session.commit()
            session.refresh(instance)
            
            self.logger.info(f"Updated {self.model_class.__name__} with id {instance.id}")
            return instance
            
        except Exception as e:
            session.rollback()
            self.logger.error(f"Failed to update {self.model_class.__name__}: {e}")
            raise ServiceError(f"Failed to update {self.model_class.__name__}: {str(e)}") from e
    
    @handle_database_error
    def delete(self, session: Session, instance: T) -> None:
        """Delete a model instance.
        
        Args:
            session: Database session to use
            instance: The instance to delete
        """
        try:
            instance_id = instance.id
            session.delete(instance)
            session.commit()
            
            self.logger.info(f"Deleted {self.model_class.__name__} with id {instance_id}")
            
        except Exception as e:
            session.rollback()
            self.logger.error(f"Failed to delete {self.model_class.__name__}: {e}")
            raise ServiceError(f"Failed to delete {self.model_class.__name__}: {str(e)}") from e
    
    @handle_database_error
    def soft_delete(self, session: Session, instance: T) -> T:
        """Soft delete a model instance (if it supports soft delete).
        
        Args:
            session: Database session to use
            instance: The instance to soft delete
            
        Returns:
            The soft deleted instance
        """
        if not hasattr(instance, 'is_deleted') or not hasattr(instance, 'deleted_at'):
            raise NotImplementedError(f"{self.model_class.__name__} does not support soft delete")
        
        from utils.soft_delete import soft_delete
        return soft_delete(session, instance)
    
    def validate_ownership(self, instance: T, user_id: int, user_role: str = "user") -> None:
        """Validate that a user owns a resource or is an admin.
        
        Args:
            instance: The instance to check ownership for
            user_id: The user ID to check
            user_role: The user's role
            
        Raises:
            PermissionError: If the user doesn't own the resource and isn't an admin
        """
        if user_role == "admin":
            return  # Admins can access everything
        
        if not hasattr(instance, 'owner_id'):
            return  # No ownership concept for this model
        
        if instance.owner_id != user_id:
            raise PermissionError(f"Access denied: You can only access your own {self.model_class.__name__.lower()}s")
    
    def log_activity(self, action: str, details: dict = None) -> None:
        """Log an activity for audit purposes.
        
        Args:
            action: The action that was performed
            details: Additional details about the action
        """
        log_data = {
            "service": self.__class__.__name__,
            "action": action,
            **(details or {})
        }
        self.logger.info(f"Activity: {action}", extra=log_data)