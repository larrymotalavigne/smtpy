"""Main controller for core application functionality."""

import os
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict

from controllers.base import BaseService, ValidationError, NotFoundError, PermissionError
from database.models import User, Invitation, Domain, Alias, ActivityLog
from utils.db import get_session
from sqlalchemy.orm import selectinload
from utils.user import hash_password, send_invitation_email, send_verification_email
from utils.soft_delete import (
    soft_delete_domain, soft_delete_alias, soft_delete_user, 
    get_active_domains, get_active_aliases, get_active_users
)
from controllers.dns_controller import check_dns_records
from passlib.context import CryptContext


class MainController(BaseService[User]):
    """Controller for main application functionality."""
    
    def __init__(self):
        super().__init__(User)
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def create_invitation(self, admin_user_id: int, email: str) -> Dict[str, Any]:
        """Create an invitation for a new user.
        
        Args:
            admin_user_id: ID of the admin creating the invitation
            email: Email address to invite
            
        Returns:
            Dictionary containing invitation results
            
        Raises:
            PermissionError: If user is not admin
            ValidationError: If email already registered or invitation exists
        """
        try:
            with self.get_db_session() as session:
                # Verify admin user
                admin_user = self.get_by_id_or_404(admin_user_id, session)
                if admin_user.role != "admin":
                    raise PermissionError("Admin access required")
                
                # Check if email already registered
                if session.query(User).filter_by(email=email).first():
                    raise ValidationError("Email already registered")
                
                # Check if invitation already exists
                existing_invitation = session.query(Invitation).filter_by(email=email).first()
                if existing_invitation and existing_invitation.expires_at > datetime.utcnow():
                    raise ValidationError("Invitation already sent")
                
                # Create invitation
                token = secrets.token_urlsafe(32)
                expires = datetime.utcnow() + timedelta(hours=24)
                invitation = Invitation(
                    email=email, 
                    token=token, 
                    expires_at=expires, 
                    invited_by=admin_user_id
                )
                session.add(invitation)
                session.commit()
                
                self.log_activity("invitation_created", {
                    "email": email,
                    "invited_by": admin_user_id,
                    "token": token
                })
                
                return {
                    "success": True,
                    "message": "Invitation sent",
                    "token": token,
                    "email": email
                }
                
        except (PermissionError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Failed to create invitation for {email}: {e}")
            raise
    
    def register_user(self, username: str, password: str, email: str = "", invite_token: str = "") -> Dict[str, Any]:
        """Register a new user.
        
        Args:
            username: Username for the new user
            password: Password for the new user
            email: Email address (optional)
            invite_token: Invitation token (optional)
            
        Returns:
            Dictionary containing registration results
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            email_val = email if email else None
            invite_val = invite_token if invite_token else None
            
            with self.get_db_session() as session:
                # Handle invitation
                invitation = None
                if invite_val:
                    invitation = session.query(Invitation).filter_by(token=invite_val).first()
                    if not invitation or invitation.expires_at < datetime.utcnow():
                        raise ValidationError("Invalid or expired invitation")
                    email_val = invitation.email
                
                # Check if username exists
                if session.query(User).filter_by(username=username).first():
                    raise ValidationError("Username already exists")
                
                # Check if email exists
                if email_val and session.query(User).filter_by(email=email_val).first():
                    raise ValidationError("Email already registered")
                
                # Create user
                verification_token = None if invite_val else secrets.token_urlsafe(32)
                user = User(
                    username=username,
                    email=email_val,
                    hashed_password=hash_password(password),
                    is_active=bool(invite_val),  # Active if invited
                    email_verified=bool(invite_val),  # Verified if invited
                    verification_token=verification_token
                )
                session.add(user)
                
                # Delete invitation if used
                if invitation:
                    session.delete(invitation)
                
                session.commit()
                
                self.log_activity("user_registered", {
                    "user_id": user.id,
                    "username": username,
                    "email": email_val,
                    "invited": bool(invite_val)
                })
                
                result = {
                    "success": True,
                    "user_id": user.id,
                    "username": username,
                    "requires_verification": not bool(invite_val)
                }
                
                # Send verification email if needed
                if email_val and not invite_val:
                    result["verification_token"] = verification_token
                    result["message"] = "Check your email to verify your account"
                else:
                    result["message"] = "Account created. You can now log in"
                
                return result
                
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to register user {username}: {e}")
            raise
    
    def verify_email(self, token: str) -> Dict[str, Any]:
        """Verify a user's email address.
        
        Args:
            token: Verification token
            
        Returns:
            Dictionary containing verification results
        """
        try:
            with self.get_db_session() as session:
                user = session.query(User).filter_by(verification_token=token).first()
                if not user:
                    raise ValidationError("Invalid or expired token")
                
                user.is_active = True
                user.email_verified = True
                user.verification_token = None
                session.commit()
                
                self.log_activity("email_verified", {
                    "user_id": user.id,
                    "username": user.username
                })
                
                return {
                    "success": True,
                    "message": "Email verified. You can now log in",
                    "user_id": user.id
                }
                
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to verify email with token {token}: {e}")
            raise
    
    def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate a user.
        
        Args:
            username: Username
            password: Password
            
        Returns:
            Dictionary containing authentication results
            
        Raises:
            ValidationError: If authentication fails
        """
        try:
            with self.get_db_session() as session:
                user = get_active_users(session).filter_by(username=username).first()
                if not user or not self.pwd_context.verify(password, user.hashed_password):
                    raise ValidationError("Invalid credentials")
                
                self.log_activity("user_login", {
                    "user_id": user.id,
                    "username": username
                })
                
                return {
                    "success": True,
                    "user_id": user.id,
                    "username": user.username,
                    "role": user.role,
                    "email": user.email
                }
                
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to authenticate user {username}: {e}")
            raise
    
    def get_dashboard_data(self, user_id: int) -> Dict[str, Any]:
        """Get dashboard data for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dictionary containing dashboard data
        """
        try:
            with self.get_db_session() as session:
                user = self.get_by_id_or_404(user_id, session)
                
                # Get counts
                domains_query = get_active_domains(session)
                aliases_query = get_active_aliases(session)
                
                if user.role != "admin":
                    domains_query = domains_query.filter_by(owner_id=user_id)
                    aliases_query = aliases_query.filter_by(owner_id=user_id)
                
                num_domains = domains_query.count()
                num_aliases = aliases_query.count()
                
                # Get recent activity
                activity_query = session.query(ActivityLog).order_by(ActivityLog.timestamp.desc()).limit(10)
                if user.role != "admin":
                    # Filter activity for user's resources
                    activity_query = activity_query.filter(
                        ActivityLog.details.contains(f'"user_id": {user_id}')
                    )
                
                recent_activity = activity_query.all()
                
                self.log_activity("dashboard_accessed", {
                    "user_id": user_id,
                    "domains_count": num_domains,
                    "aliases_count": num_aliases
                })
                
                return {
                    "num_domains": num_domains,
                    "num_aliases": num_aliases,
                    "recent_activity": [
                        {
                            "id": log.id,
                            "event_type": log.event_type,
                            "timestamp": log.timestamp,
                            "details": log.details
                        }
                        for log in recent_activity
                    ],
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "role": user.role,
                        "email": user.email
                    }
                }
                
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to get dashboard data for user {user_id}: {e}")
            raise
    
    def get_admin_panel_data(self, user_id: int) -> Dict[str, Any]:
        """Get admin panel data.
        
        Args:
            user_id: ID of the requesting user
            
        Returns:
            Dictionary containing admin panel data
            
        Raises:
            PermissionError: If user is not admin
        """
        try:
            with self.get_db_session() as session:
                user = self.get_by_id_or_404(user_id, session)
                if user.role != "admin":
                    raise PermissionError("Admin access required")
                
                # Get all domains with aliases
                domains = get_active_domains(session).options(
                    selectinload(Domain.aliases)
                ).all()
                
                # Get all aliases
                aliases = get_active_aliases(session).all()
                
                # Prepare domain statuses with DNS checks
                domain_statuses = []
                for domain in domains:
                    dns_results = check_dns_records(domain.name)
                    verified = dns_results.get('spf', {}).get('status') == 'valid'
                    
                    # Check MX records
                    mx_valid = False
                    try:
                        import dns.resolver
                        answers = dns.resolver.resolve(domain.name, 'MX')
                        mx_valid = any(answers)
                    except Exception:
                        mx_valid = False
                    
                    domain_statuses.append({
                        'id': domain.id,
                        'name': domain.name,
                        'catch_all': domain.catch_all,
                        'owner_id': domain.owner_id,
                        'verified': verified,
                        'mx_valid': mx_valid,
                        'spf_valid': dns_results.get('spf', {}).get('status') == 'valid',
                        'dkim_valid': dns_results.get('dkim', {}).get('status') == 'valid',
                        'dmarc_valid': dns_results.get('dmarc', {}).get('status') == 'valid'
                    })
                
                self.log_activity("admin_panel_accessed", {
                    "user_id": user_id,
                    "domains_count": len(domains),
                    "aliases_count": len(aliases)
                })
                
                return {
                    "domains": domain_statuses,
                    "aliases": [
                        {
                            "id": alias.id,
                            "local_part": alias.local_part,
                            "targets": alias.targets,
                            "domain_id": alias.domain_id,
                            "owner_id": alias.owner_id,
                            "expires_at": alias.expires_at,
                            "created_at": alias.created_at
                        }
                        for alias in aliases
                    ],
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "role": user.role,
                        "email": user.email
                    }
                }
                
        except (NotFoundError, PermissionError):
            raise
        except Exception as e:
            self.logger.error(f"Failed to get admin panel data for user {user_id}: {e}")
            raise
    
    def get_users_list(self, admin_user_id: int) -> List[Dict[str, Any]]:
        """Get list of all users (admin only).
        
        Args:
            admin_user_id: ID of the admin user
            
        Returns:
            List of user dictionaries
            
        Raises:
            PermissionError: If user is not admin
        """
        try:
            with self.get_db_session() as session:
                admin_user = self.get_by_id_or_404(admin_user_id, session)
                if admin_user.role != "admin":
                    raise PermissionError("Admin access required")
                
                users = get_active_users(session).all()
                
                self.log_activity("users_list_accessed", {
                    "admin_user_id": admin_user_id,
                    "users_count": len(users)
                })
                
                return [
                    {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "role": user.role,
                        "is_active": user.is_active,
                        "email_verified": user.email_verified,
                        "created_at": user.created_at,
                        "updated_at": user.updated_at
                    }
                    for user in users
                ]
                
        except (NotFoundError, PermissionError):
            raise
        except Exception as e:
            self.logger.error(f"Failed to get users list for admin {admin_user_id}: {e}")
            raise
    
    def get_dkim_public_key(self, domain: str) -> str:
        """Get DKIM public key for a domain.
        
        Args:
            domain: Domain name
            
        Returns:
            DKIM public key content
            
        Raises:
            NotFoundError: If key file not found
        """
        try:
            if not domain:
                raise ValidationError("Please specify a domain")
            
            # Sanitize domain name
            safe_domain = domain.replace('/', '').replace('..', '')
            path = os.path.join(os.path.dirname(__file__), "../static", f"dkim-public-{safe_domain}.txt")
            
            if not os.path.exists(path):
                raise NotFoundError(f"DKIM public key for {domain} not found. Please generate and mount the key as dkim-public-{domain}.txt.")
            
            with open(path) as f:
                content = f.read()
            
            self.log_activity("dkim_key_retrieved", {
                "domain": domain,
                "file_path": path
            })
            
            return content
            
        except (ValidationError, NotFoundError):
            raise
        except Exception as e:
            self.logger.error(f"Failed to get DKIM key for domain {domain}: {e}")
            raise NotFoundError(f"DKIM public key for {domain} not found")
    
    def get_domain_dns_info(self, domain_id: int, user_id: int) -> Dict[str, Any]:
        """Get DNS information for a domain.
        
        Args:
            domain_id: ID of the domain
            user_id: ID of the requesting user
            
        Returns:
            Dictionary containing domain and DNS information
            
        Raises:
            NotFoundError: If domain not found
            PermissionError: If user lacks access
        """
        try:
            with self.get_db_session() as session:
                domain = session.get(Domain, domain_id)
                if not domain:
                    raise NotFoundError("Domain not found")
                
                user = self.get_by_id_or_404(user_id, session)
                
                # Check access
                if user.role != "admin" and domain.owner_id != user_id:
                    raise PermissionError("Access denied")
                
                dns_results = check_dns_records(domain.name)
                
                self.log_activity("domain_dns_info_accessed", {
                    "domain_id": domain_id,
                    "domain_name": domain.name,
                    "user_id": user_id
                })
                
                return {
                    "domain": {
                        "id": domain.id,
                        "name": domain.name,
                        "catch_all": domain.catch_all,
                        "owner_id": domain.owner_id,
                        "created_at": domain.created_at
                    },
                    "dns_results": dns_results
                }
                
        except (NotFoundError, PermissionError):
            raise
        except Exception as e:
            self.logger.error(f"Failed to get DNS info for domain {domain_id}: {e}")
            raise
    
    def get_domain_aliases_info(self, domain_id: int, user_id: int) -> Dict[str, Any]:
        """Get aliases information for a domain.
        
        Args:
            domain_id: ID of the domain
            user_id: ID of the requesting user
            
        Returns:
            Dictionary containing domain and aliases information
            
        Raises:
            NotFoundError: If domain not found
            PermissionError: If user lacks access
        """
        try:
            with self.get_db_session() as session:
                domain = session.get(Domain, domain_id)
                if not domain:
                    raise NotFoundError("Domain not found")
                
                user = self.get_by_id_or_404(user_id, session)
                
                # Check access
                if user.role != "admin" and domain.owner_id != user_id:
                    raise PermissionError("Access denied")
                
                aliases = get_active_aliases(session).filter_by(domain_id=domain_id).all()
                
                self.log_activity("domain_aliases_info_accessed", {
                    "domain_id": domain_id,
                    "domain_name": domain.name,
                    "user_id": user_id,
                    "aliases_count": len(aliases)
                })
                
                return {
                    "domain": {
                        "id": domain.id,
                        "name": domain.name,
                        "catch_all": domain.catch_all,
                        "owner_id": domain.owner_id,
                        "created_at": domain.created_at
                    },
                    "aliases": [
                        {
                            "id": alias.id,
                            "local_part": alias.local_part,
                            "targets": alias.targets,
                            "expires_at": alias.expires_at,
                            "created_at": alias.created_at
                        }
                        for alias in aliases
                    ]
                }
                
        except (NotFoundError, PermissionError):
            raise
        except Exception as e:
            self.logger.error(f"Failed to get aliases info for domain {domain_id}: {e}")
            raise
    
    def check_health(self) -> Dict[str, Any]:
        """Health check endpoint.
        
        Returns:
            Dictionary containing health status
        """
        return {
            "status": "healthy",
            "service": "smtpy",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def check_readiness(self) -> Dict[str, Any]:
        """Readiness check endpoint.
        
        Returns:
            Dictionary containing readiness status
            
        Raises:
            Exception: If not ready
        """
        try:
            # Check database connectivity
            with get_session() as session:
                session.execute("SELECT 1")
            
            return {
                "status": "ready",
                "service": "smtpy",
                "database": "connected",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Readiness check failed: {e}")
            raise Exception(f"Service not ready: {e}")
    
    def get_activity_stats(self) -> Dict[str, Any]:
        """Get activity statistics for the last 30 days.
        
        Returns:
            Dictionary containing activity statistics
        """
        try:
            with get_session() as session:
                cutoff = datetime.utcnow() - timedelta(days=30)
                logs = session.query(ActivityLog).filter(ActivityLog.timestamp >= cutoff).all()
                
                stats = defaultdict(lambda: {"forward": 0, "bounce": 0, "error": 0})
                for log in logs:
                    date = str(log.timestamp)[:10]
                    event_type = log.event_type
                    if event_type in ["forward", "bounce", "error"]:
                        stats[date][event_type] += 1
                
                sorted_stats = sorted(stats.items())
                
                self.log_activity("activity_stats_retrieved", {
                    "days_count": len(sorted_stats),
                    "total_events": len(logs)
                })
                
                return {
                    "dates": [d for d, _ in sorted_stats],
                    "forward": [v["forward"] for _, v in sorted_stats],
                    "bounce": [v["bounce"] for _, v in sorted_stats],
                    "error": [v["error"] for _, v in sorted_stats],
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get activity stats: {e}")
            raise
    
    def edit_user(self, admin_user_id: int, user_id: int, email: str, role: str) -> Dict[str, Any]:
        """Edit a user (admin only).
        
        Args:
            admin_user_id: ID of the admin user
            user_id: ID of the user to edit
            email: New email address
            role: New role
            
        Returns:
            Dictionary containing edit results
            
        Raises:
            PermissionError: If user is not admin
            NotFoundError: If user not found
        """
        try:
            with self.get_db_session() as session:
                admin_user = self.get_by_id_or_404(admin_user_id, session)
                if admin_user.role != "admin":
                    raise PermissionError("Admin access required")
                
                user = session.get(User, user_id)
                if not user:
                    raise NotFoundError("User not found")
                
                old_email = user.email
                old_role = user.role
                
                user.email = email
                user.role = role
                session.commit()
                
                self.log_activity("user_edited", {
                    "admin_user_id": admin_user_id,
                    "user_id": user_id,
                    "old_email": old_email,
                    "new_email": email,
                    "old_role": old_role,
                    "new_role": role
                })
                
                return {
                    "success": True,
                    "message": "User updated successfully",
                    "user_id": user_id
                }
                
        except (PermissionError, NotFoundError):
            raise
        except Exception as e:
            self.logger.error(f"Failed to edit user {user_id}: {e}")
            raise