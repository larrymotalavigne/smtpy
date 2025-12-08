"""Pydantic schemas for forwarding rule API."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator


class RuleCreate(BaseModel):
    """Schema for creating a forwarding rule."""
    alias_id: int
    name: str
    condition_type: str  # SENDER_CONTAINS, SENDER_EQUALS, etc.
    condition_value: str
    action_type: str  # FORWARD, BLOCK, REDIRECT
    action_value: Optional[str] = None
    priority: int = 100
    description: Optional[str] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate rule name."""
        if not v or len(v) > 255:
            raise ValueError("Rule name must be between 1 and 255 characters")
        return v

    @field_validator('condition_type')
    @classmethod
    def validate_condition_type(cls, v: str) -> str:
        """Validate condition type."""
        valid_types = [
            'SENDER_CONTAINS', 'SENDER_EQUALS', 'SENDER_DOMAIN',
            'SUBJECT_CONTAINS', 'SUBJECT_EQUALS',
            'SIZE_GREATER_THAN', 'SIZE_LESS_THAN', 'HAS_ATTACHMENTS'
        ]
        if v not in valid_types:
            raise ValueError(f"Invalid condition type. Must be one of: {', '.join(valid_types)}")
        return v

    @field_validator('action_type')
    @classmethod
    def validate_action_type(cls, v: str) -> str:
        """Validate action type."""
        valid_types = ['FORWARD', 'BLOCK', 'REDIRECT']
        if v not in valid_types:
            raise ValueError(f"Invalid action type. Must be one of: {', '.join(valid_types)}")
        return v

    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v: int) -> int:
        """Validate priority."""
        if v < 0 or v > 1000:
            raise ValueError("Priority must be between 0 and 1000")
        return v


class RuleUpdate(BaseModel):
    """Schema for updating a forwarding rule."""
    name: Optional[str] = None
    condition_type: Optional[str] = None
    condition_value: Optional[str] = None
    action_type: Optional[str] = None
    action_value: Optional[str] = None
    priority: Optional[int] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate rule name."""
        if v is not None and (not v or len(v) > 255):
            raise ValueError("Rule name must be between 1 and 255 characters")
        return v

    @field_validator('condition_type')
    @classmethod
    def validate_condition_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate condition type."""
        if v is not None:
            valid_types = [
                'SENDER_CONTAINS', 'SENDER_EQUALS', 'SENDER_DOMAIN',
                'SUBJECT_CONTAINS', 'SUBJECT_EQUALS',
                'SIZE_GREATER_THAN', 'SIZE_LESS_THAN', 'HAS_ATTACHMENTS'
            ]
            if v not in valid_types:
                raise ValueError(f"Invalid condition type. Must be one of: {', '.join(valid_types)}")
        return v

    @field_validator('action_type')
    @classmethod
    def validate_action_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate action type."""
        if v is not None:
            valid_types = ['FORWARD', 'BLOCK', 'REDIRECT']
            if v not in valid_types:
                raise ValueError(f"Invalid action type. Must be one of: {', '.join(valid_types)}")
        return v

    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v: Optional[int]) -> Optional[int]:
        """Validate priority."""
        if v is not None and (v < 0 or v > 1000):
            raise ValueError("Priority must be between 0 and 1000")
        return v


class RuleResponse(BaseModel):
    """Schema for forwarding rule response."""
    id: int
    alias_id: int
    priority: int
    name: str
    description: Optional[str] = None
    condition_type: str
    condition_value: str
    action_type: str
    action_value: Optional[str] = None
    is_active: bool
    match_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }


class RuleListResponse(BaseModel):
    """Schema for list of forwarding rules."""
    rules: list[RuleResponse]
    total: int
