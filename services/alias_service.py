"""Alias service for email alias management operations."""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from .base import BaseService, ValidationError, NotFoundError, PermissionError
from database.models import Alias, Domain, User
from utils.validation import validate_alias_local_part, validate_email_list
from utils.soft_delete import get_active_aliases, get_active_domains, soft_delete_alias


class AliasService(BaseService[Alias]):
    """Service for alias management operations."""
    
    def __init__(self):
        super().__init__(Alias)
    
    def create_alias(self, local_part: str, targets: str, domain_id: int, owner_id: int, 
                    expires_at: Optional[datetime] = None) -> Alias:
        """Create a new email alias.
        
        Args:
            local_part: The local part of the email alias (before @)
            targets: Comma-separated list of target email addresses
            domain_id: ID of the domain this alias belongs to
            owner_id: ID of the user who owns this alias
            expires_at: Optional expiration date for the alias
            
        Returns:
            The created alias
            
        Raises:
            ValidationError: If input validation fails
            ServiceError: If alias creation fails
        """
        try:
            # Validate input
            local_part = validate_alias_local_part(local_part)
            target_emails = validate_email_list(targets)
            targets_str = ", ".join(target_emails)  # Store as comma-separated string
            
            with self.get_db_session() as session:
                # Verify domain exists and user has access
                domain = session.get(Domain, domain_id)
                if not domain:
                    raise ValidationError(f"Domain with id {domain_id} not found")
                
                # Check if domain is active
                if not get_active_domains(session).filter_by(id=domain_id).first():
                    raise ValidationError(f"Domain is not active")
                
                # Check domain ownership (admin can create aliases for any domain)
                owner = session.get(User, owner_id)
                if not owner:
                    raise ValidationError(f"Owner with id {owner_id} not found")
                
                if owner.role != "admin" and domain.owner_id != owner_id:
                    raise PermissionError("You can only create aliases for your own domains")
                
                # Check if alias already exists for this domain
                existing_alias = get_active_aliases(session).filter_by(
                    domain_id=domain_id, 
                    local_part=local_part
                ).first()
                if existing_alias:
                    raise ValidationError(f"Alias '{local_part}@{domain.name}' already exists")
                
                # Validate expiration date
                if expires_at and expires_at <= datetime.utcnow():
                    raise ValidationError("Expiration date must be in the future")
                
                # Create alias
                alias_data = {
                    "local_part": local_part,
                    "targets": targets_str,
                    "domain_id": domain_id,
                    "owner_id": owner_id,
                    "expires_at": expires_at
                }
                
                alias = self.create(session, **alias_data)
                
                self.log_activity("alias_created", {
                    "alias_id": alias.id,
                    "local_part": local_part,
                    "domain_id": domain_id,
                    "domain_name": domain.name,
                    "owner_id": owner_id,
                    "targets": target_emails,
                    "expires_at": expires_at.isoformat() if expires_at else None
                })
                
                return alias
                
        except (ValidationError, PermissionError):
            raise
        except Exception as e:
            self.logger.error(f"Failed to create alias '{local_part}': {e}")
            raise
    
    def get_user_aliases(self, user_id: int, user_role: str = "user", domain_id: Optional[int] = None) -> List[Alias]:
        """Get aliases owned by a user.
        
        Args:
            user_id: ID of the user
            user_role: Role of the user (admin can see all aliases)
            domain_id: Optional domain ID to filter by
            
        Returns:
            List of aliases owned by the user
        """
        try:
            with self.get_db_session() as session:
                query = get_active_aliases(session)
                
                if user_role != "admin":
                    query = query.filter_by(owner_id=user_id)
                
                if domain_id:
                    query = query.filter_by(domain_id=domain_id)
                
                aliases = query.all()
                
                self.log_activity("aliases_retrieved", {
                    "user_id": user_id,
                    "user_role": user_role,
                    "domain_id": domain_id,
                    "alias_count": len(aliases)
                })
                
                return aliases
                
        except Exception as e:
            self.logger.error(f"Failed to get aliases for user {user_id}: {e}")
            raise
    
    def get_alias_with_details(self, alias_id: int, user_id: int, user_role: str = "user") -> Dict[str, Any]:
        """Get alias with detailed information.
        
        Args:
            alias_id: ID of the alias
            user_id: ID of the requesting user
            user_role: Role of the requesting user
            
        Returns:
            Dictionary containing alias details
            
        Raises:
            NotFoundError: If alias not found
            PermissionError: If user lacks permission
        """
        try:
            with self.get_db_session() as session:
                alias = self.get_by_id_or_404(alias_id, session)
                
                # Check ownership
                self.validate_ownership(alias, user_id, user_role)
                
                # Get domain information
                domain = session.get(Domain, alias.domain_id)
                
                # Check if alias is expired
                is_expired = alias.expires_at and alias.expires_at <= datetime.utcnow()
                
                # Parse targets
                target_emails = [email.strip() for email in alias.targets.split(",") if email.strip()]
                
                alias_details = {
                    'id': alias.id,
                    'local_part': alias.local_part,
                    'full_address': f"{alias.local_part}@{domain.name}",
                    'targets': target_emails,
                    'targets_count': len(target_emails),
                    'domain_id': alias.domain_id,
                    'domain_name': domain.name,
                    'owner_id': alias.owner_id,
                    'expires_at': alias.expires_at,
                    'is_expired': is_expired,
                    'created_at': alias.created_at,
                    'updated_at': alias.updated_at
                }
                
                self.log_activity("alias_details_retrieved", {
                    "alias_id": alias_id,
                    "user_id": user_id,
                    "full_address": alias_details['full_address']
                })
                
                return alias_details
                
        except (NotFoundError, PermissionError):
            raise
        except Exception as e:
            self.logger.error(f"Failed to get alias details for alias {alias_id}: {e}")
            raise
    
    def update_alias(self, alias_id: int, user_id: int, user_role: str = "user", **kwargs) -> Alias:
        """Update an alias.
        
        Args:
            alias_id: ID of the alias to update
            user_id: ID of the requesting user
            user_role: Role of the requesting user
            **kwargs: Fields to update
            
        Returns:
            The updated alias
            
        Raises:
            NotFoundError: If alias not found
            PermissionError: If user lacks permission
            ValidationError: If validation fails
        """
        try:
            with self.get_db_session() as session:
                alias = self.get_by_id_or_404(alias_id, session)
                
                # Check ownership
                self.validate_ownership(alias, user_id, user_role)
                
                # Validate updates
                if "local_part" in kwargs:
                    kwargs["local_part"] = validate_alias_local_part(kwargs["local_part"])
                    
                    # Check if new local_part already exists for this domain (excluding current alias)
                    existing_alias = get_active_aliases(session).filter_by(
                        domain_id=alias.domain_id,
                        local_part=kwargs["local_part"]
                    ).first()
                    if existing_alias and existing_alias.id != alias_id:
                        domain = session.get(Domain, alias.domain_id)
                        raise ValidationError(f"Alias '{kwargs['local_part']}@{domain.name}' already exists")
                
                if "targets" in kwargs:
                    target_emails = validate_email_list(kwargs["targets"])
                    kwargs["targets"] = ", ".join(target_emails)
                
                if "expires_at" in kwargs and kwargs["expires_at"]:
                    if kwargs["expires_at"] <= datetime.utcnow():
                        raise ValidationError("Expiration date must be in the future")
                elif "expires_at" in kwargs and not kwargs["expires_at"]:
                    kwargs["expires_at"] = None
                
                updated_alias = self.update(session, alias, **kwargs)
                
                self.log_activity("alias_updated", {
                    "alias_id": alias_id,
                    "user_id": user_id,
                    "fields": list(kwargs.keys())
                })
                
                return updated_alias
                
        except (NotFoundError, PermissionError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Failed to update alias {alias_id}: {e}")
            raise
    
    def delete_alias(self, alias_id: int, user_id: int, user_role: str = "user") -> bool:
        """Soft delete an alias.
        
        Args:
            alias_id: ID of the alias to delete
            user_id: ID of the requesting user
            user_role: Role of the requesting user
            
        Raises:
            NotFoundError: If alias not found
            PermissionError: If user lacks permission
        """
        try:
            with self.get_db_session() as session:
                alias = self.get_by_id_or_404(alias_id, session)
                
                # Check ownership
                self.validate_ownership(alias, user_id, user_role)
                
                # Get domain for logging
                domain = session.get(Domain, alias.domain_id)
                full_address = f"{alias.local_part}@{domain.name}"
                
                # Soft delete alias
                soft_delete_alias(session, alias_id)
                
                self.log_activity("alias_deleted", {
                    "alias_id": alias_id,
                    "full_address": full_address,
                    "user_id": user_id
                })
                
                return True
                
        except (NotFoundError, PermissionError):
            raise
        except Exception as e:
            self.logger.error(f"Failed to delete alias {alias_id}: {e}")
            raise
    
    def get_expired_aliases(self, user_id: Optional[int] = None) -> List[Alias]:
        """Get aliases that have expired.
        
        Args:
            user_id: Optional user ID to filter by (admin only if None)
            
        Returns:
            List of expired aliases
        """
        try:
            with self.get_db_session() as session:
                query = get_active_aliases(session).filter(
                    Alias.expires_at.isnot(None),
                    Alias.expires_at <= datetime.utcnow()
                )
                
                if user_id:
                    query = query.filter_by(owner_id=user_id)
                
                expired_aliases = query.all()
                
                self.log_activity("expired_aliases_retrieved", {
                    "user_id": user_id,
                    "expired_count": len(expired_aliases)
                })
                
                return expired_aliases
                
        except Exception as e:
            self.logger.error(f"Failed to get expired aliases: {e}")
            raise
    
    def get_alias_statistics(self, user_id: int, user_role: str = "user") -> Dict[str, Any]:
        """Get alias statistics for a user.
        
        Args:
            user_id: ID of the user
            user_role: Role of the user
            
        Returns:
            Dictionary containing alias statistics
        """
        try:
            with self.get_db_session() as session:
                query = get_active_aliases(session)
                
                if user_role != "admin":
                    query = query.filter_by(owner_id=user_id)
                
                aliases = query.all()
                
                # Calculate statistics
                total_aliases = len(aliases)
                expired_aliases = sum(1 for a in aliases if a.expires_at and a.expires_at <= datetime.utcnow())
                expiring_soon = sum(1 for a in aliases if a.expires_at and 
                                  datetime.utcnow() <= a.expires_at <= datetime.utcnow() + timedelta(days=7))
                
                # Count aliases by domain
                domain_counts = {}
                for alias in aliases:
                    domain = session.get(Domain, alias.domain_id)
                    if domain:
                        domain_counts[domain.name] = domain_counts.get(domain.name, 0) + 1
                
                stats = {
                    "total_aliases": total_aliases,
                    "expired_aliases": expired_aliases,
                    "expiring_soon": expiring_soon,
                    "active_aliases": total_aliases - expired_aliases,
                    "domain_distribution": domain_counts
                }
                
                self.log_activity("alias_statistics_retrieved", {
                    "user_id": user_id,
                    "user_role": user_role,
                    "statistics": stats
                })
                
                return stats
                
        except Exception as e:
            self.logger.error(f"Failed to get alias statistics for user {user_id}: {e}")
            raise
    
    def test_alias_forwarding(self, alias_id: int, user_id: int, user_role: str = "user") -> Dict[str, Any]:
        """Test alias forwarding configuration.
        
        Args:
            alias_id: ID of the alias to test
            user_id: ID of the requesting user
            user_role: Role of the requesting user
            
        Returns:
            Dictionary containing test results
            
        Raises:
            NotFoundError: If alias not found
            PermissionError: If user lacks permission
        """
        try:
            with self.get_db_session() as session:
                alias = self.get_by_id_or_404(alias_id, session)
                
                # Check ownership
                self.validate_ownership(alias, user_id, user_role)
                
                # Get domain
                domain = session.get(Domain, alias.domain_id)
                full_address = f"{alias.local_part}@{domain.name}"
                
                # Parse targets
                target_emails = [email.strip() for email in alias.targets.split(",") if email.strip()]
                
                # Check if alias is expired
                is_expired = alias.expires_at and alias.expires_at <= datetime.utcnow()
                
                # Validate target emails
                valid_targets = []
                invalid_targets = []
                
                for target in target_emails:
                    try:
                        from utils.validation import validate_email
                        validate_email(target)
                        valid_targets.append(target)
                    except Exception:
                        invalid_targets.append(target)
                
                test_results = {
                    "alias_id": alias_id,
                    "full_address": full_address,
                    "is_active": not is_expired,
                    "is_expired": is_expired,
                    "expires_at": alias.expires_at,
                    "total_targets": len(target_emails),
                    "valid_targets": valid_targets,
                    "invalid_targets": invalid_targets,
                    "forwarding_ready": not is_expired and len(valid_targets) > 0 and len(invalid_targets) == 0
                }
                
                self.log_activity("alias_forwarding_tested", {
                    "alias_id": alias_id,
                    "user_id": user_id,
                    "full_address": full_address,
                    "test_results": test_results
                })
                
                return test_results
                
        except (NotFoundError, PermissionError):
            raise
        except Exception as e:
            self.logger.error(f"Failed to test alias forwarding for alias {alias_id}: {e}")
            raise
    
    def cleanup_expired_aliases(self, dry_run: bool = True) -> Dict[str, Any]:
        """Clean up expired aliases (admin only).
        
        Args:
            dry_run: If True, only return what would be cleaned up without actually doing it
            
        Returns:
            Dictionary containing cleanup results
        """
        try:
            with self.get_db_session() as session:
                # Get expired aliases
                expired_aliases = get_active_aliases(session).filter(
                    Alias.expires_at.isnot(None),
                    Alias.expires_at <= datetime.utcnow()
                ).all()
                
                cleanup_results = {
                    "total_expired": len(expired_aliases),
                    "cleaned_up": 0,
                    "dry_run": dry_run,
                    "aliases": []
                }
                
                for alias in expired_aliases:
                    domain = session.get(Domain, alias.domain_id)
                    full_address = f"{alias.local_part}@{domain.name}"
                    
                    alias_info = {
                        "id": alias.id,
                        "full_address": full_address,
                        "expired_at": alias.expires_at,
                        "owner_id": alias.owner_id
                    }
                    
                    cleanup_results["aliases"].append(alias_info)
                    
                    if not dry_run:
                        # Soft delete the expired alias
                        soft_delete_alias(session, alias.id)
                        cleanup_results["cleaned_up"] += 1
                
                self.log_activity("expired_aliases_cleanup", {
                    "dry_run": dry_run,
                    "total_expired": cleanup_results["total_expired"],
                    "cleaned_up": cleanup_results["cleaned_up"]
                })
                
                return cleanup_results
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup expired aliases: {e}")
            raise