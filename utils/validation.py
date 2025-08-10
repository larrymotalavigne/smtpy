"""Input validation and sanitization utilities for SMTPy."""

import re
import html
from typing import Optional, List
from fastapi import HTTPException


class ValidationError(Exception):
    """Custom validation error."""

    pass


def sanitize_string(value: str, max_length: int = None, allow_html: bool = False) -> str:
    """Sanitize a string input."""
    if not isinstance(value, str):
        raise ValidationError("Input must be a string")

    # Strip whitespace
    value = value.strip()

    # HTML escape if not allowing HTML
    if not allow_html:
        value = html.escape(value)

    # Check length
    if max_length and len(value) > max_length:
        raise ValidationError(f"Input too long (max {max_length} characters)")

    return value


def validate_username(username: str) -> str:
    """Validate and sanitize username."""
    username = sanitize_string(username, max_length=50)

    if not username:
        raise ValidationError("Username cannot be empty")

    if len(username) < 3:
        raise ValidationError("Username must be at least 3 characters long")

    # Allow alphanumeric, underscore, hyphen, and dot
    if not re.match(r"^[a-zA-Z0-9._-]+$", username):
        raise ValidationError(
            "Username can only contain letters, numbers, dots, underscores, and hyphens"
        )

    # Don't allow usernames that start or end with special characters
    if username[0] in "._-" or username[-1] in "._-":
        raise ValidationError("Username cannot start or end with special characters")

    return username


def validate_email(email: str) -> str:
    """Validate and sanitize email address."""
    email = sanitize_string(email, max_length=255)

    if not email:
        raise ValidationError("Email cannot be empty")

    # Basic email regex (RFC 5322 compliant)
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_pattern, email):
        raise ValidationError("Invalid email format")

    # Convert to lowercase for consistency
    return email.lower()


def validate_domain_name(domain: str) -> str:
    """Validate and sanitize domain name."""
    domain = sanitize_string(domain, max_length=255)

    if not domain:
        raise ValidationError("Domain name cannot be empty")

    # Convert to lowercase
    domain = domain.lower()

    # Basic domain validation
    domain_pattern = r"^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
    if not re.match(domain_pattern, domain):
        raise ValidationError("Invalid domain name format")

    # Check for valid TLD (at least 2 characters)
    if "." not in domain or len(domain.split(".")[-1]) < 2:
        raise ValidationError("Domain must have a valid top-level domain")

    return domain


def validate_password(password: str) -> str:
    """Validate password strength."""
    if not isinstance(password, str):
        raise ValidationError("Password must be a string")

    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long")

    if len(password) > 128:
        raise ValidationError("Password too long (max 128 characters)")

    # Check for at least one uppercase, lowercase, digit, and special character
    if not re.search(r"[A-Z]", password):
        raise ValidationError("Password must contain at least one uppercase letter")

    if not re.search(r"[a-z]", password):
        raise ValidationError("Password must contain at least one lowercase letter")

    if not re.search(r"\d", password):
        raise ValidationError("Password must contain at least one digit")

    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise ValidationError("Password must contain at least one special character")

    return password


def validate_alias_local_part(local_part: str) -> str:
    """Validate email alias local part."""
    local_part = sanitize_string(local_part, max_length=100)

    if not local_part:
        raise ValidationError("Alias local part cannot be empty")

    # Allow alphanumeric, dots, hyphens, underscores, and plus signs
    if not re.match(r"^[a-zA-Z0-9._+-]+$", local_part):
        raise ValidationError("Invalid characters in alias local part")

    # Don't allow consecutive dots
    if ".." in local_part:
        raise ValidationError("Consecutive dots not allowed in alias")

    # Don't allow starting or ending with dots
    if local_part.startswith(".") or local_part.endswith("."):
        raise ValidationError("Alias cannot start or end with a dot")

    return local_part.lower()


def validate_email_list(email_list: str) -> List[str]:
    """Validate a comma-separated list of email addresses."""
    if not email_list:
        raise ValidationError("Email list cannot be empty")

    emails = [email.strip() for email in email_list.split(",")]
    validated_emails = []

    for email in emails:
        if email:  # Skip empty strings
            try:
                validated_email = validate_email(email)
                validated_emails.append(validated_email)
            except ValidationError as e:
                raise ValidationError(f"Invalid email '{email}': {str(e)}")

    if not validated_emails:
        raise ValidationError("At least one valid email address is required")

    if len(validated_emails) > 10:
        raise ValidationError("Too many target emails (max 10)")

    return validated_emails


def sanitize_html_content(content: str, max_length: int = 1000) -> str:
    """Sanitize HTML content for safe display."""
    if not isinstance(content, str):
        raise ValidationError("Content must be a string")

    # Strip whitespace
    content = content.strip()

    # HTML escape everything for now (can be enhanced with allowlist later)
    content = html.escape(content)

    # Check length
    if len(content) > max_length:
        raise ValidationError(f"Content too long (max {max_length} characters)")

    return content


def validate_and_sanitize_form_data(data: dict, validation_rules: dict) -> dict:
    """
    Validate and sanitize form data based on validation rules.

    Args:
        data: Dictionary of form data
        validation_rules: Dictionary mapping field names to validation functions

    Returns:
        Dictionary of validated and sanitized data
    """
    validated_data = {}

    for field_name, validator in validation_rules.items():
        if field_name in data:
            try:
                validated_data[field_name] = validator(data[field_name])
            except ValidationError as e:
                raise HTTPException(
                    status_code=400, detail=f"Validation error for {field_name}: {str(e)}"
                )
        elif hasattr(validator, "__defaults__") and validator.__defaults__:
            # Field is optional, use default
            validated_data[field_name] = validator.__defaults__[0]

    return validated_data
