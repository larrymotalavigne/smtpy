"""Domain schemas for SMTPy v2."""

from typing import Optional

from pydantic import Field, field_validator

from shared.models.domain import DomainStatus
from .common import BaseSchema, TimestampSchema


class DomainCreate(BaseSchema):
    """Schema for creating a new domain."""
    
    name: str = Field(
        ..., 
        min_length=3, 
        max_length=255,
        description="Domain name (e.g., example.com)",
        pattern=r"^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?)*$"
    )
    
    @field_validator("name")
    @classmethod
    def validate_domain_name(cls, v: str) -> str:
        """Validate domain name format."""
        v = v.lower().strip()
        if not v:
            raise ValueError("Domain name cannot be empty")
        if v.startswith(".") or v.endswith("."):
            raise ValueError("Domain name cannot start or end with a dot")
        if ".." in v:
            raise ValueError("Domain name cannot contain consecutive dots")
        return v


class DomainUpdate(BaseSchema):
    """Schema for updating domain settings."""
    
    is_active: Optional[bool] = Field(
        None, 
        description="Whether domain is active for forwarding"
    )


class DNSVerificationStatus(BaseSchema):
    """Schema for DNS record verification status."""
    
    mx_record_verified: bool = Field(..., description="MX record verification status")
    spf_record_verified: bool = Field(..., description="SPF record verification status")
    dkim_record_verified: bool = Field(..., description="DKIM record verification status")
    dmarc_record_verified: bool = Field(..., description="DMARC record verification status")
    is_fully_verified: bool = Field(..., description="All DNS records verified")


class DomainResponse(TimestampSchema):
    """Schema for domain response."""
    
    id: int = Field(..., description="Domain ID")
    name: str = Field(..., description="Domain name")
    organization_id: int = Field(..., description="Organization ID")
    status: DomainStatus = Field(..., description="Domain verification status")
    is_active: bool = Field(..., description="Whether domain is active")
    
    # DNS verification status
    mx_record_verified: bool = Field(..., description="MX record verified")
    spf_record_verified: bool = Field(..., description="SPF record verified")
    dkim_record_verified: bool = Field(..., description="DKIM record verified")
    dmarc_record_verified: bool = Field(..., description="DMARC record verified")
    
    # DNS record values
    dkim_public_key: Optional[str] = Field(None, description="DKIM public key")
    verification_token: Optional[str] = Field(None, description="Domain verification token")
    
    @property
    def is_fully_verified(self) -> bool:
        """Check if all DNS records are verified."""
        return (
            self.mx_record_verified and 
            self.spf_record_verified and 
            self.dkim_record_verified and 
            self.dmarc_record_verified
        )


class DomainList(TimestampSchema):
    """Schema for domain list response."""
    
    id: int = Field(..., description="Domain ID")
    name: str = Field(..., description="Domain name")
    status: DomainStatus = Field(..., description="Domain verification status")
    is_active: bool = Field(..., description="Whether domain is active")
    is_fully_verified: bool = Field(..., description="All DNS records verified")


class DomainVerificationResponse(BaseSchema):
    """Schema for domain verification response."""
    
    success: bool = Field(..., description="Whether verification check succeeded")
    message: str = Field(..., description="Verification result message")
    dns_status: DNSVerificationStatus = Field(..., description="DNS record verification details")
    
    
class DNSRecords(BaseSchema):
    """Schema for required DNS records."""
    
    mx_record: str = Field(..., description="Required MX record")
    spf_record: str = Field(..., description="Required SPF record")
    dkim_record: str = Field(..., description="Required DKIM record")
    dmarc_record: str = Field(..., description="Required DMARC record")
    verification_record: Optional[str] = Field(None, description="Domain verification TXT record")


class DomainStats(BaseSchema):
    """Schema for per-domain statistics used by the frontend."""
    
    total_aliases: int = Field(0, description="Total number of aliases for the domain")
    active_aliases: int = Field(0, description="Number of active aliases for the domain")
    messages_received: int = Field(0, description="Total number of messages received for the domain")
    messages_forwarded: int = Field(0, description="Number of messages successfully forwarded (delivered)")
    last_message_at: Optional[str] = Field(None, description="ISO timestamp of the last message activity")