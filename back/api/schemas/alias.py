"""Pydantic schemas for alias API."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator


class AliasCreate(BaseModel):
    """Schema for creating an alias."""
    local_part: str
    domain_id: int
    targets: list[EmailStr]  # List of target email addresses
    expires_at: Optional[datetime] = None

    @field_validator('local_part')
    @classmethod
    def validate_local_part(cls, v: str) -> str:
        """Validate local part of email."""
        if not v or len(v) > 64:
            raise ValueError("Local part must be between 1 and 64 characters")
        # Basic validation for email local part
        if not all(c.isalnum() or c in '._-+' for c in v):
            raise ValueError("Local part contains invalid characters")
        return v.lower()

    @field_validator('targets')
    @classmethod
    def validate_targets(cls, v: list[EmailStr]) -> list[EmailStr]:
        """Validate targets list."""
        if not v or len(v) == 0:
            raise ValueError("At least one target email is required")
        if len(v) > 10:
            raise ValueError("Maximum 10 target emails allowed")
        return v


class AliasUpdate(BaseModel):
    """Schema for updating an alias."""
    targets: Optional[list[EmailStr]] = None
    expires_at: Optional[datetime] = None
    is_deleted: Optional[bool] = None

    @field_validator('targets')
    @classmethod
    def validate_targets(cls, v: Optional[list[EmailStr]]) -> Optional[list[EmailStr]]:
        """Validate targets list."""
        if v is not None:
            if len(v) == 0:
                raise ValueError("At least one target email is required")
            if len(v) > 10:
                raise ValueError("Maximum 10 target emails allowed")
        return v


class AliasResponse(BaseModel):
    """Schema for alias response."""
    id: int
    domain_id: int
    local_part: str
    targets: str  # Comma-separated in database
    is_deleted: bool
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    # Computed fields
    domain_name: Optional[str] = None
    full_address: Optional[str] = None
    target_list: list[str] = []

    model_config = {
        "from_attributes": True
    }

    def __init__(self, **data):
        """Initialize with computed fields."""
        super().__init__(**data)

        # Parse targets from comma-separated string
        if self.targets:
            self.target_list = [t.strip() for t in self.targets.split(',')]

        # Build full email address if domain info available
        if hasattr(data.get('domain'), 'name'):
            self.domain_name = data['domain'].name
            self.full_address = f"{self.local_part}@{self.domain_name}"


class AliasListItem(BaseModel):
    """Schema for alias list item (lighter than full response)."""
    id: int
    local_part: str
    domain_id: int
    domain_name: Optional[str] = None
    full_address: Optional[str] = None
    target_count: int = 0
    target_list: list[str] = []
    is_deleted: bool
    expires_at: Optional[datetime] = None
    created_at: datetime

    model_config = {
        "from_attributes": True
    }

    @classmethod
    def model_validate(cls, obj, **kwargs):
        """Validate model and compute fields from the source object."""
        # Extract computed values from the source object before validation
        data = {}

        # Get basic attributes
        if hasattr(obj, '__dict__'):
            # It's a SQLAlchemy model
            data['id'] = obj.id
            data['local_part'] = obj.local_part
            data['domain_id'] = obj.domain_id
            data['is_deleted'] = obj.is_deleted
            data['expires_at'] = obj.expires_at
            data['created_at'] = obj.created_at

            # Compute target_count and target_list from targets field
            if hasattr(obj, 'targets') and obj.targets:
                targets = [t.strip() for t in obj.targets.split(',') if t.strip()]
                data['target_count'] = len(targets)
                data['target_list'] = targets
            else:
                data['target_count'] = 0
                data['target_list'] = []

            # Compute domain name and full address
            if hasattr(obj, 'domain') and obj.domain and hasattr(obj.domain, 'name'):
                data['domain_name'] = obj.domain.name
                data['full_address'] = f"{obj.local_part}@{obj.domain.name}"

        # If data is already a dict, use it directly
        if isinstance(obj, dict):
            data = obj

        return super(cls, cls).model_validate(data, **kwargs)
