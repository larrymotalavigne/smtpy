"""Comprehensive error handling utilities for SMTPy."""

import logging
import traceback
from typing import Dict, Any

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("smtpy.error_handler")


class SMTPyError(Exception):
    """Base exception class for SMTPy application errors."""

    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)


class DatabaseError(SMTPyError):
    """Raised when database operations fail."""

    pass


class ValidationError(SMTPyError):
    """Raised when input validation fails."""

    pass


class AuthenticationError(SMTPyError):
    """Raised when authentication fails."""

    pass


class AuthorizationError(SMTPyError):
    """Raised when authorization fails."""

    pass


class ResourceNotFoundError(SMTPyError):
    """Raised when a requested resource is not found."""

    pass


class RateLimitError(SMTPyError):
    """Raised when rate limits are exceeded."""

    pass


class EmailProcessingError(SMTPyError):
    """Raised when email processing fails."""

    pass


def create_error_response(
        status_code: int,
        message: str,
        error_code: str = None,
        details: Dict[str, Any] = None,
        request_id: str = None,
) -> JSONResponse:
    """Create a standardized error response."""
    error_data = {
        "error": {
            "message": message,
            "code": error_code or "UNKNOWN_ERROR",
            "status_code": status_code,
            "details": details or {},
        }
    }

    if request_id:
        error_data["error"]["request_id"] = request_id

    return JSONResponse(status_code=status_code, content=error_data)


def log_error(
        error: Exception,
        request: Request = None,
        user_id: int = None,
        additional_context: Dict[str, Any] = None,
) -> str:
    """Log an error with comprehensive context information."""
    import uuid

    # Generate unique error ID for tracking
    error_id = str(uuid.uuid4())

    # Build context information
    context = {
        "error_id": error_id,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "user_id": user_id,
    }

    # Add request context if available
    if request:
        context.update(
            {
                "method": request.method,
                "url": str(request.url),
                "client_ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown"),
            }
        )

        # Add user ID from session if available
        if hasattr(request, "session") and "user_id" in request.session:
            context["user_id"] = request.session.get("user_id")

    # Add additional context
    if additional_context:
        context.update(additional_context)

    # Log the error with full context
    logger.error(f"Error {error_id}: {str(error)}", extra=context, exc_info=True)

    return error_id


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware to handle unhandled exceptions and provide consistent error responses."""

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except HTTPException:
            # Re-raise HTTPExceptions to let FastAPI handle them
            raise
        except SMTPyError as e:
            # Handle our custom exceptions
            error_id = log_error(e, request)

            # Map custom exceptions to HTTP status codes
            status_code_map = {
                ValidationError: 400,
                AuthenticationError: 401,
                AuthorizationError: 403,
                ResourceNotFoundError: 404,
                RateLimitError: 429,
                DatabaseError: 500,
                EmailProcessingError: 500,
            }

            status_code = status_code_map.get(type(e), 500)

            return create_error_response(
                status_code=status_code,
                message=e.message,
                error_code=e.error_code,
                details=e.details,
                request_id=error_id,
            )
        except Exception as e:
            # Handle unexpected exceptions
            error_id = log_error(e, request)

            # Don't expose internal error details in production
            from config import SETTINGS

            if SETTINGS.is_production:
                message = "An internal server error occurred"
                details = {"error_id": error_id}
            else:
                message = str(e)
                details = {"error_id": error_id, "traceback": traceback.format_exc()}

            return create_error_response(
                status_code=500,
                message=message,
                error_code="INTERNAL_SERVER_ERROR",
                details=details,
                request_id=error_id,
            )


def handle_database_error(func):
    """Decorator to handle database errors in service methods."""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Log the database error
            logger.error(f"Database error in {func.__name__}: {str(e)}", exc_info=True)

            # Convert to our custom exception
            raise DatabaseError(
                message=f"Database operation failed: {str(e)}",
                details={"function": func.__name__, "args": str(args), "kwargs": str(kwargs)},
            )

    return wrapper


def handle_validation_error(func):
    """Decorator to handle validation errors."""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            raise ValidationError(message=str(e))
        except Exception as e:
            if "validation" in str(e).lower():
                raise ValidationError(message=str(e))
            raise

    return wrapper


def safe_execute(operation_name: str, func, *args, **kwargs):
    """Safely execute a function with comprehensive error handling."""
    try:
        return func(*args, **kwargs)
    except SMTPyError:
        # Re-raise our custom exceptions
        raise
    except Exception as e:
        logger.error(f"Error in {operation_name}: {str(e)}", exc_info=True)
        raise SMTPyError(
            message=f"Operation '{operation_name}' failed: {str(e)}",
            error_code="OPERATION_FAILED",
            details={"operation": operation_name, "error": str(e)},
        )


# Context manager for error handling
class ErrorContext:
    """Context manager for handling errors in specific operations."""

    def __init__(self, operation_name: str, request: Request = None):
        self.operation_name = operation_name
        self.request = request

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # Log the error with context
            log_error(exc_val, self.request, additional_context={"operation": self.operation_name})
        return False  # Don't suppress the exception
