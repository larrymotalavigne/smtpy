"""Domain service for domain management operations."""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, selectinload

from .base import BaseService, ValidationError, NotFoundError, PermissionError
from database.models import Domain, User
from utils.validation import validate_domain_name, validate_email
from utils.soft_delete import get_active_domains, soft_delete_domain
from controllers.dns_controller import check_dns_records


class DomainService(BaseService[Domain]):
    """Service for domain management operations."""
    
    def __init__(self):
        super().__init__(Domain)
    
    def create_domain(self, name: str, owner_id: int, catch_all: Optional[str] = None) -> Domain:
        """Create a new domain.
        
        Args:
            name: The domain name
            owner_id: ID of the user who owns this domain
            catch_all: Optional catch-all email address
            
        Returns:
            The created domain
            
        Raises:
            ValidationError: If input validation fails
            ServiceError: If domain creation fails
        """
        try:
            # Validate input
            name = validate_domain_name(name)
            if catch_all:
                catch_all = validate_email(catch_all)
            
            with self.get_db_session() as session:
                # Check if domain already exists
                existing_domain = get_active_domains(session).filter_by(name=name).first()
                if existing_domain:
                    raise ValidationError(f"Domain '{name}' already exists")
                
                # Verify owner exists
                owner = session.get(User, owner_id)
                if not owner:
                    raise ValidationError(f"Owner with id {owner_id} not found")
                
                # Create domain
                domain_data = {
                    "name": name,
                    "owner_id": owner_id,
                    "catch_all": catch_all
                }
                
                domain = self.create(session, **domain_data)
                
                self.log_activity("domain_created", {
                    "domain_id": domain.id,
                    "domain_name": name,
                    "owner_id": owner_id,
                    "catch_all": catch_all
                })
                
                return domain
                
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to create domain '{name}': {e}")
            raise
    
    def get_user_domains(self, user_id: int, user_role: str = "user") -> List[Domain]:
        """Get domains owned by a user.
        
        Args:
            user_id: ID of the user
            user_role: Role of the user (admin can see all domains)
            
        Returns:
            List of domains owned by the user
        """
        try:
            with self.get_db_session() as session:
                query = get_active_domains(session).options(selectinload(Domain.aliases))
                
                if user_role != "admin":
                    query = query.filter_by(owner_id=user_id)
                
                domains = query.all()
                
                self.log_activity("domains_retrieved", {
                    "user_id": user_id,
                    "user_role": user_role,
                    "domain_count": len(domains)
                })
                
                return domains
                
        except Exception as e:
            self.logger.error(f"Failed to get domains for user {user_id}: {e}")
            raise
    
    def get_domain_with_status(self, domain_id: int, user_id: int, user_role: str = "user") -> Dict[str, Any]:
        """Get domain with DNS status information.
        
        Args:
            domain_id: ID of the domain
            user_id: ID of the requesting user
            user_role: Role of the requesting user
            
        Returns:
            Dictionary containing domain info and DNS status
            
        Raises:
            NotFoundError: If domain not found
            PermissionError: If user lacks permission
        """
        try:
            with self.get_db_session() as session:
                domain = self.get_by_id_or_404(domain_id, session)
                
                # Check ownership
                self.validate_ownership(domain, user_id, user_role)
                
                # Get DNS status
                dns_results = check_dns_records(domain.name)
                
                # Check MX records
                mx_valid = False
                try:
                    import dns.resolver
                    answers = dns.resolver.resolve(domain.name, 'MX')
                    mx_valid = any(answers)
                except Exception:
                    mx_valid = False
                
                domain_status = {
                    'id': domain.id,
                    'name': domain.name,
                    'catch_all': domain.catch_all,
                    'owner_id': domain.owner_id,
                    'created_at': domain.created_at,
                    'updated_at': domain.updated_at,
                    'verified': dns_results.get('spf', {}).get('status') == 'valid',
                    'mx_valid': mx_valid,
                    'spf_valid': dns_results.get('spf', {}).get('status') == 'valid',
                    'dkim_valid': dns_results.get('dkim', {}).get('status') == 'valid',
                    'dmarc_valid': dns_results.get('dmarc', {}).get('status') == 'valid',
                    'dns_results': dns_results
                }
                
                self.log_activity("domain_status_checked", {
                    "domain_id": domain_id,
                    "user_id": user_id,
                    "dns_status": {
                        "spf": dns_results.get('spf', {}).get('status'),
                        "dkim": dns_results.get('dkim', {}).get('status'),
                        "dmarc": dns_results.get('dmarc', {}).get('status'),
                        "mx": mx_valid
                    }
                })
                
                return domain_status
                
        except (NotFoundError, PermissionError):
            raise
        except Exception as e:
            self.logger.error(f"Failed to get domain status for domain {domain_id}: {e}")
            raise
    
    def update_domain(self, domain_id: int, user_id: int, user_role: str = "user", **kwargs) -> Domain:
        """Update a domain.
        
        Args:
            domain_id: ID of the domain to update
            user_id: ID of the requesting user
            user_role: Role of the requesting user
            **kwargs: Fields to update
            
        Returns:
            The updated domain
            
        Raises:
            NotFoundError: If domain not found
            PermissionError: If user lacks permission
            ValidationError: If validation fails
        """
        try:
            with self.get_db_session() as session:
                domain = self.get_by_id_or_404(domain_id, session)
                
                # Check ownership
                self.validate_ownership(domain, user_id, user_role)
                
                # Validate updates
                if "name" in kwargs:
                    kwargs["name"] = validate_domain_name(kwargs["name"])
                    
                    # Check if new name already exists (excluding current domain)
                    existing_domain = get_active_domains(session).filter_by(name=kwargs["name"]).first()
                    if existing_domain and existing_domain.id != domain_id:
                        raise ValidationError(f"Domain '{kwargs['name']}' already exists")
                
                if "catch_all" in kwargs and kwargs["catch_all"]:
                    kwargs["catch_all"] = validate_email(kwargs["catch_all"])
                elif "catch_all" in kwargs and not kwargs["catch_all"]:
                    kwargs["catch_all"] = None
                
                updated_domain = self.update(session, domain, **kwargs)
                
                self.log_activity("domain_updated", {
                    "domain_id": domain_id,
                    "user_id": user_id,
                    "fields": list(kwargs.keys())
                })
                
                return updated_domain
                
        except (NotFoundError, PermissionError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Failed to update domain {domain_id}: {e}")
            raise
    
    def delete_domain(self, domain_id: int, user_id: int, user_role: str = "user") -> bool:
        """Soft delete a domain and all its aliases.
        
        Args:
            domain_id: ID of the domain to delete
            user_id: ID of the requesting user
            user_role: Role of the requesting user
            
        Raises:
            NotFoundError: If domain not found
            PermissionError: If user lacks permission
        """
        try:
            with self.get_db_session() as session:
                domain = self.get_by_id_or_404(domain_id, session)
                
                # Check ownership
                self.validate_ownership(domain, user_id, user_role)
                
                # Soft delete domain and cascade to aliases
                soft_delete_domain(session, domain_id)
                
                self.log_activity("domain_deleted", {
                    "domain_id": domain_id,
                    "domain_name": domain.name,
                    "user_id": user_id
                })
                
                return True
                
        except (NotFoundError, PermissionError):
            raise
        except Exception as e:
            self.logger.error(f"Failed to delete domain {domain_id}: {e}")
            raise
    
    def check_domain_dns(self, domain_name: str) -> Dict[str, Any]:
        """Check DNS records for a domain.
        
        Args:
            domain_name: The domain name to check
            
        Returns:
            Dictionary containing DNS check results
        """
        try:
            # Validate domain name
            domain_name = validate_domain_name(domain_name)
            
            # Check DNS records
            dns_results = check_dns_records(domain_name)
            
            self.log_activity("dns_check_performed", {
                "domain_name": domain_name,
                "results": dns_results
            })
            
            return dns_results
            
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to check DNS for domain '{domain_name}': {e}")
            raise
    
    def get_domain_statistics(self, user_id: int, user_role: str = "user") -> Dict[str, Any]:
        """Get domain statistics for a user.
        
        Args:
            user_id: ID of the user
            user_role: Role of the user
            
        Returns:
            Dictionary containing domain statistics
        """
        try:
            with self.get_db_session() as session:
                query = get_active_domains(session)
                
                if user_role != "admin":
                    query = query.filter_by(owner_id=user_id)
                
                domains = query.all()
                
                # Calculate statistics
                total_domains = len(domains)
                domains_with_catch_all = sum(1 for d in domains if d.catch_all)
                
                # Check DNS status for each domain
                verified_domains = 0
                for domain in domains:
                    try:
                        dns_results = check_dns_records(domain.name)
                        if dns_results.get('spf', {}).get('status') == 'valid':
                            verified_domains += 1
                    except Exception:
                        continue  # Skip domains with DNS check errors
                
                stats = {
                    "total_domains": total_domains,
                    "verified_domains": verified_domains,
                    "domains_with_catch_all": domains_with_catch_all,
                    "verification_rate": (verified_domains / total_domains * 100) if total_domains > 0 else 0
                }
                
                self.log_activity("domain_statistics_retrieved", {
                    "user_id": user_id,
                    "user_role": user_role,
                    "statistics": stats
                })
                
                return stats
                
        except Exception as e:
            self.logger.error(f"Failed to get domain statistics for user {user_id}: {e}")
            raise
    
    def validate_domain_ownership(self, domain_name: str, user_id: int, user_role: str = "user") -> bool:
        """Validate that a user owns a domain.
        
        Args:
            domain_name: The domain name to check
            user_id: ID of the user
            user_role: Role of the user
            
        Returns:
            True if user owns the domain or is admin, False otherwise
        """
        try:
            with self.get_db_session() as session:
                domain = get_active_domains(session).filter_by(name=domain_name).first()
                
                if not domain:
                    return False
                
                if user_role == "admin":
                    return True
                
                return domain.owner_id == user_id
                
        except Exception as e:
            self.logger.error(f"Failed to validate domain ownership for '{domain_name}': {e}")
            return False