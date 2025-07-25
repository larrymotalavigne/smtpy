import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import IntegrityError

from database.models import User, Domain, Alias, Invitation
from controllers.user_controller import UserController
from controllers.domain_controller import DomainController
from controllers.alias_controller import AliasController
from controllers.base import NotFoundError, PermissionError
from utils.validation import ValidationError
from utils.error_handling import DatabaseError, ValidationError as ServiceValidationError
from utils.db import get_session


def unique_name(prefix="test"):
    """Generate a unique name for testing."""
    return f"{prefix}{uuid.uuid4().hex[:8]}"


class TestUserController:
    """Test cases for UserController."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.user_service = UserController()
    
    def test_authenticate_user_success(self):
        """Test successful user authentication."""
        # Create a test user using the service
        username = unique_name("testuser")
        password = "TestPassword123!"
        
        # Create user through service
        user = self.user_service.create_user(
            username=username,
            password=password,
            email=f"{unique_name('test')}@example.com"
        )
        
        # Manually activate and verify email for testing
        with get_session() as session:
            db_user = session.get(User, user.id)
            db_user.is_active = True
            db_user.email_verified = True
            session.commit()
        
        # Test authentication
        authenticated_user = self.user_service.authenticate_user(username, password)
        assert authenticated_user is not None
        assert authenticated_user.username == username
    
    def test_authenticate_user_invalid_password(self):
        """Test authentication with invalid password."""
        with get_session() as session:
            username = unique_name("testuser")
            hashed_password = self.user_service.pwd_context.hash("correctpassword")
            
            user = User(
                username=username,
                hashed_password=hashed_password,
                is_active=True,
                email_verified=True
            )
            session.add(user)
            session.commit()
            
            # Test with wrong password
            result = self.user_service.authenticate_user(username, "wrongpassword")
            assert result is None
    
    def test_authenticate_user_inactive(self):
        """Test authentication with inactive user."""
        with get_session() as session:
            username = unique_name("testuser")
            password = "TestPassword123!"
            hashed_password = self.user_service.pwd_context.hash(password)
            
            user = User(
                username=username,
                hashed_password=hashed_password,
                is_active=False,  # Inactive user
                email_verified=True
            )
            session.add(user)
            session.commit()
            
            result = self.user_service.authenticate_user(username, password)
            assert result is None
    
    def test_create_user_success(self):
        """Test successful user creation."""
        username = unique_name("newuser")
        email = f"{unique_name('test')}@example.com"
        password = "SecurePassword123!"
        
        user = self.user_service.create_user(
            username=username,
            password=password,
            email=email,
            role="user"
        )
        
        assert user.username == username
        assert user.email == email
        assert user.role == "user"
        assert user.is_active is False  # Self-registered users are inactive until email verification
        assert user.email_verified is False
        assert user.verification_token is not None
    
    def test_create_user_duplicate_username(self):
        """Test user creation with duplicate username."""
        username = unique_name("duplicate")
        
        # Create first user
        self.user_service.create_user(
            username=username,
            password="Password123!"
        )
        
        # Try to create second user with same username
        with pytest.raises(DatabaseError, match="Username"):
            self.user_service.create_user(
                username=username,
                password="Password456!"
            )
    
    def test_create_user_invalid_username(self):
        """Test user creation with invalid username."""
        with pytest.raises(ValidationError):
            self.user_service.create_user(
                username="a",  # Too short
                password="Password123!"
            )
    
    def test_create_user_weak_password(self):
        """Test user creation with weak password."""
        with pytest.raises(ValidationError):
            self.user_service.create_user(
                username=unique_name("user"),
                password="123"  # Too weak
            )
    
    @patch('utils.user.send_verification_email')
    def test_verify_email_success(self, mock_send_email):
        """Test successful email verification."""
        with get_session() as session:
            username = unique_name("testuser")
            token = "verification_token_123"
            
            user = User(
                username=username,
                hashed_password="hash",
                email="test@example.com",
                email_verified=False,
                verification_token=token
            )
            session.add(user)
            session.commit()
            
            result = self.user_service.verify_email(token)
            assert result is not None  # Returns User object, not boolean
            assert isinstance(result, User)
            
            # Refresh user to check updated state
            session.refresh(user)
            assert user.email_verified is True
            assert user.verification_token is None
    
    def test_verify_email_invalid_token(self):
        """Test email verification with invalid token."""
        result = self.user_service.verify_email("invalid_token")
        assert result is None
    
    @patch('utils.user.send_invitation_email')
    def test_create_invitation_success(self, mock_send_email):
        """Test successful invitation creation."""
        with get_session() as session:
            # Create admin user
            admin = User(
                username=unique_name("admin"),
                hashed_password="hash",
                role="admin"
            )
            session.add(admin)
            session.flush()
            
            # Mock get_db_session to return the test session
            with patch.object(self.user_service, 'get_db_session') as mock_session:
                mock_session.return_value.__enter__ = lambda x: session
                mock_session.return_value.__exit__ = lambda x, y, z, w: None
                
                email = f"{unique_name('invite')}@example.com"
                invitation = self.user_service.create_invitation(email, admin.id)
                
                assert invitation.email == email
                assert invitation.invited_by == admin.id
                assert invitation.token is not None
                assert invitation.expires_at > datetime.utcnow()
    
    def test_create_invitation_duplicate_email(self):
        """Test invitation creation with duplicate email."""
        with get_session() as session:
            admin = User(
                username=unique_name("admin"),
                hashed_password="hash",
                role="admin"
            )
            session.add(admin)
            session.flush()
            
            email = f"{unique_name('duplicate')}@example.com"
            
            # Mock get_db_session to return the test session
            with patch.object(self.user_service, 'get_db_session') as mock_session:
                mock_session.return_value.__enter__ = lambda x: session
                mock_session.return_value.__exit__ = lambda x, y, z, w: None
                
                # Create first invitation
                self.user_service.create_invitation(email, admin.id)
                
                # Try to create second invitation with same email
                with pytest.raises(ServiceValidationError, match="Invitation already sent to"):
                    self.user_service.create_invitation(email, admin.id)
    
    def test_update_user_success(self):
        """Test successful user update."""
        with get_session() as session:
            user = User(
                username=unique_name("testuser"),
                hashed_password="hash",
                email="old@example.com",
                role="user"
            )
            session.add(user)
            session.flush()
            
            # Mock get_db_session to return the test session
            with patch.object(self.user_service, 'get_db_session') as mock_session:
                mock_session.return_value.__enter__ = lambda x: session
                mock_session.return_value.__exit__ = lambda x, y, z, w: None
                
                new_email = f"{unique_name('new')}@example.com"
                updated_user = self.user_service.update_user(
                    user_id=user.id,
                    current_user_id=user.id,
                    current_user_role="user",
                    email=new_email
                )
                
                assert updated_user.email == new_email
    
    def test_update_user_permission_denied(self):
        """Test user update with insufficient permissions."""
        with get_session() as session:
            user1 = User(username=unique_name("user1"), hashed_password="hash")
            user2 = User(username=unique_name("user2"), hashed_password="hash")
            session.add_all([user1, user2])
            session.flush()
            
            # Mock get_db_session to return the test session
            with patch.object(self.user_service, 'get_db_session') as mock_session:
                mock_session.return_value.__enter__ = lambda x: session
                mock_session.return_value.__exit__ = lambda x, y, z, w: None
                
                # User1 tries to update User2 (should fail)
                with pytest.raises(PermissionError):
                    self.user_service.update_user(
                        user_id=user2.id,
                        current_user_id=user1.id,
                        current_user_role="user",
                        email="new@example.com"
                    )
    
    def test_delete_user_success(self):
        """Test successful user deletion (soft delete)."""
        with get_session() as session:
            admin = User(
                username=unique_name("admin"),
                hashed_password="hash",
                role="admin"
            )
            user = User(
                username=unique_name("user"),
                hashed_password="hash",
                role="user"
            )
            session.add_all([admin, user])
            session.flush()
            
            # Mock get_db_session to return the test session
            with patch.object(self.user_service, 'get_db_session') as mock_session:
                mock_session.return_value.__enter__ = lambda x: session
                mock_session.return_value.__exit__ = lambda x, y, z, w: None
                
                result = self.user_service.delete_user(
                    user_id=user.id,
                    current_user_id=admin.id,
                    current_user_role="admin"
                )
                
                assert result is True
                session.refresh(user)
                assert user.is_deleted is True
                assert user.deleted_at is not None
    
    def test_delete_user_permission_denied(self):
        """Test user deletion with insufficient permissions."""
        with get_session() as session:
            user1 = User(username=unique_name("user1"), hashed_password="hash", role="user")
            user2 = User(username=unique_name("user2"), hashed_password="hash", role="user")
            session.add_all([user1, user2])
            session.flush()
            
            # Mock get_db_session to return the test session
            with patch.object(self.user_service, 'get_db_session') as mock_session:
                mock_session.return_value.__enter__ = lambda x: session
                mock_session.return_value.__exit__ = lambda x, y, z, w: None
                
                # Regular user tries to delete another user
                with pytest.raises(PermissionError):
                    self.user_service.delete_user(
                        user_id=user2.id,
                        current_user_id=user1.id,
                        current_user_role="user"
                    )
    
    def test_get_all_users_admin(self):
        """Test getting all users as admin."""
        with get_session() as session:
            users = [
                User(username=unique_name(f"user{i}"), hashed_password="hash")
                for i in range(3)
            ]
            session.add_all(users)
            session.commit()
            
            result = self.user_service.get_all_users("admin")
            assert len(result) >= 3  # At least our test users
    
    def test_get_all_users_non_admin(self):
        """Test getting all users as non-admin (should fail)."""
        with pytest.raises(PermissionError):
            self.user_service.get_all_users("user")


class TestDomainController:
    """Test cases for DomainController."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.domain_service = DomainController()
    
    def test_create_domain_success(self):
        """Test successful domain creation."""
        with get_session() as session:
            user = User(username=unique_name("owner"), hashed_password="hash")
            session.add(user)
            session.flush()
            
            domain_name = f"{unique_name('example')}.com"
            
            # Mock get_db_session to return the test session
            with patch.object(self.domain_service, 'get_db_session') as mock_session:
                mock_session.return_value.__enter__ = lambda x: session
                mock_session.return_value.__exit__ = lambda x, y, z, w: None
                
                domain = self.domain_service.create_domain(
                    name=domain_name,
                    owner_id=user.id
                )
                
                assert domain.name == domain_name
                assert domain.owner_id == user.id
                assert domain.is_deleted is False
    
    def test_create_domain_duplicate(self):
        """Test domain creation with duplicate name."""
        with get_session() as session:
            user = User(username=unique_name("owner"), hashed_password="hash")
            session.add(user)
            session.flush()
            
            domain_name = f"{unique_name('duplicate')}.com"
            
            # Mock get_db_session to return the test session
            with patch.object(self.domain_service, 'get_db_session') as mock_session:
                mock_session.return_value.__enter__ = lambda x: session
                mock_session.return_value.__exit__ = lambda x, y, z, w: None
                
                # Create first domain
                self.domain_service.create_domain(name=domain_name, owner_id=user.id)
                
                # Try to create duplicate
                with pytest.raises(ServiceValidationError, match="already exists"):
                    self.domain_service.create_domain(name=domain_name, owner_id=user.id)
    
    def test_create_domain_invalid_name(self):
        """Test domain creation with invalid name."""
        with get_session() as session:
            user = User(username=unique_name("owner"), hashed_password="hash")
            session.add(user)
            session.flush()
            
            # Mock get_db_session to return the test session
            with patch.object(self.domain_service, 'get_db_session') as mock_session:
                mock_session.return_value.__enter__ = lambda x: session
                mock_session.return_value.__exit__ = lambda x, y, z, w: None
                
                with pytest.raises(ValidationError):
                    self.domain_service.create_domain(
                        name="invalid..domain.com",  # Invalid domain name with double dots
                        owner_id=user.id
                    )
    
    def test_get_user_domains(self):
        """Test getting user domains."""
        with get_session() as session:
            user = User(username=unique_name("owner"), hashed_password="hash")
            session.add(user)
            session.flush()
            
            # Create test domains
            domains = []
            for i in range(3):
                domain = Domain(
                    name=f"{unique_name(f'domain{i}')}.com",
                    owner_id=user.id
                )
                domains.append(domain)
            session.add_all(domains)
            session.commit()
            
            # Mock get_db_session to return the test session
            with patch.object(self.domain_service, 'get_db_session') as mock_session:
                mock_session.return_value.__enter__ = lambda x: session
                mock_session.return_value.__exit__ = lambda x, y, z, w: None
                
                result = self.domain_service.get_user_domains(user.id)
                assert len(result) == 3
    
    def test_delete_domain_success(self):
        """Test successful domain deletion."""
        with get_session() as session:
            user = User(username=unique_name("owner"), hashed_password="hash")
            session.add(user)
            session.flush()
            
            domain = Domain(
                name=f"{unique_name('test')}.com",
                owner_id=user.id
            )
            session.add(domain)
            session.flush()
            
            # Mock get_db_session to return the test session
            with patch.object(self.domain_service, 'get_db_session') as mock_session:
                mock_session.return_value.__enter__ = lambda x: session
                mock_session.return_value.__exit__ = lambda x, y, z, w: None
                
                result = self.domain_service.delete_domain(
                    domain_id=domain.id,
                    user_id=user.id
                )
                
                assert result is True
                session.refresh(domain)
                assert domain.is_deleted is True
    
    def test_delete_domain_permission_denied(self):
        """Test domain deletion with insufficient permissions."""
        with get_session() as session:
            owner = User(username=unique_name("owner"), hashed_password="hash")
            other_user = User(username=unique_name("other"), hashed_password="hash")
            session.add_all([owner, other_user])
            session.flush()
            
            domain = Domain(
                name=f"{unique_name('test')}.com",
                owner_id=owner.id
            )
            session.add(domain)
            session.flush()
            
            # Mock get_db_session to return the test session
            with patch.object(self.domain_service, 'get_db_session') as mock_session:
                mock_session.return_value.__enter__ = lambda x: session
                mock_session.return_value.__exit__ = lambda x, y, z, w: None
                
                # Other user tries to delete owner's domain
                with pytest.raises(PermissionError):
                    self.domain_service.delete_domain(
                        domain_id=domain.id,
                        user_id=other_user.id
                    )


class TestAliasController:
    """Test cases for AliasController."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.alias_service = AliasController()
    
    def test_create_alias_success(self):
        """Test successful alias creation."""
        with get_session() as session:
            user = User(username=unique_name("owner"), hashed_password="hash")
            session.add(user)
            session.flush()
            
            domain = Domain(
                name=f"{unique_name('test')}.com",
                owner_id=user.id
            )
            session.add(domain)
            session.flush()
            
            # Mock get_db_session to return the test session
            with patch.object(self.alias_service, 'get_db_session') as mock_session:
                mock_session.return_value.__enter__ = lambda x: session
                mock_session.return_value.__exit__ = lambda x, y, z, w: None
                
                alias = self.alias_service.create_alias(
                    local_part="test",
                    targets="target@example.com",
                    domain_id=domain.id,
                    owner_id=user.id
                )
                
                assert alias.local_part == "test"
                assert alias.targets == "target@example.com"
                assert alias.domain_id == domain.id
                assert alias.owner_id == user.id
    
    def test_create_alias_with_expiration(self):
        """Test alias creation with expiration date."""
        with get_session() as session:
            user = User(username=unique_name("owner"), hashed_password="hash")
            session.add(user)
            session.flush()
            
            domain = Domain(
                name=f"{unique_name('test')}.com",
                owner_id=user.id
            )
            session.add(domain)
            session.flush()
            
            # Mock get_db_session to return the test session
            with patch.object(self.alias_service, 'get_db_session') as mock_session:
                mock_session.return_value.__enter__ = lambda x: session
                mock_session.return_value.__exit__ = lambda x, y, z, w: None
                
                expires_at = datetime.utcnow() + timedelta(days=30)
                alias = self.alias_service.create_alias(
                    local_part="temp",
                    targets="target@example.com",
                    domain_id=domain.id,
                    owner_id=user.id,
                    expires_at=expires_at
                )
                
                assert alias.expires_at is not None
                assert alias.expires_at.date() == expires_at.date()
    
    def test_create_alias_invalid_targets(self):
        """Test alias creation with invalid target emails."""
        with get_session() as session:
            user = User(username=unique_name("owner"), hashed_password="hash")
            session.add(user)
            session.flush()
            
            domain = Domain(
                name=f"{unique_name('test')}.com",
                owner_id=user.id
            )
            session.add(domain)
            session.flush()
            
            # Mock get_db_session to return the test session
            with patch.object(self.alias_service, 'get_db_session') as mock_session:
                mock_session.return_value.__enter__ = lambda x: session
                mock_session.return_value.__exit__ = lambda x, y, z, w: None
                
                with pytest.raises(ValidationError):
                    self.alias_service.create_alias(
                        local_part="test",
                        targets="invalid-email",  # Invalid email
                        domain_id=domain.id,
                        owner_id=user.id
                    )
    
    def test_get_expired_aliases(self):
        """Test getting expired aliases."""
        with get_session() as session:
            user = User(username=unique_name("owner"), hashed_password="hash")
            session.add(user)
            session.flush()
            
            domain = Domain(
                name=f"{unique_name('test')}.com",
                owner_id=user.id
            )
            session.add(domain)
            session.flush()
            
            # Create expired alias
            expired_alias = Alias(
                local_part="expired",
                targets="target@example.com",
                domain_id=domain.id,
                owner_id=user.id,
                expires_at=datetime.utcnow() - timedelta(days=1)
            )
            
            # Create active alias
            active_alias = Alias(
                local_part="active",
                targets="target@example.com",
                domain_id=domain.id,
                owner_id=user.id,
                expires_at=datetime.utcnow() + timedelta(days=30)
            )
            
            session.add_all([expired_alias, active_alias])
            session.commit()
            
            expired = self.alias_service.get_expired_aliases()
            expired_ids = [alias.id for alias in expired]
            
            assert expired_alias.id in expired_ids
            assert active_alias.id not in expired_ids
    
    def test_delete_alias_success(self):
        """Test successful alias deletion."""
        with get_session() as session:
            user = User(username=unique_name("owner"), hashed_password="hash")
            session.add(user)
            session.flush()
            
            domain = Domain(
                name=f"{unique_name('test')}.com",
                owner_id=user.id
            )
            session.add(domain)
            session.flush()
            
            alias = Alias(
                local_part="test",
                targets="target@example.com",
                domain_id=domain.id,
                owner_id=user.id
            )
            session.add(alias)
            session.flush()
            
            # Mock get_db_session to return the test session
            with patch.object(self.alias_service, 'get_db_session') as mock_session:
                mock_session.return_value.__enter__ = lambda x: session
                mock_session.return_value.__exit__ = lambda x, y, z, w: None
                
                result = self.alias_service.delete_alias(
                    alias_id=alias.id,
                    user_id=user.id
                )
                
                assert result is True
                session.refresh(alias)
                assert alias.is_deleted is True
    
    def test_delete_alias_permission_denied(self):
        """Test alias deletion with insufficient permissions."""
        with get_session() as session:
            owner = User(username=unique_name("owner"), hashed_password="hash")
            other_user = User(username=unique_name("other"), hashed_password="hash")
            session.add_all([owner, other_user])
            session.flush()
            
            domain = Domain(
                name=f"{unique_name('test')}.com",
                owner_id=owner.id
            )
            session.add(domain)
            session.flush()
            
            alias = Alias(
                local_part="test",
                targets="target@example.com",
                domain_id=domain.id,
                owner_id=owner.id
            )
            session.add(alias)
            session.flush()
            
            # Mock get_db_session to return the test session
            with patch.object(self.alias_service, 'get_db_session') as mock_session:
                mock_session.return_value.__enter__ = lambda x: session
                mock_session.return_value.__exit__ = lambda x, y, z, w: None
                
                # Other user tries to delete owner's alias
                with pytest.raises(PermissionError):
                    self.alias_service.delete_alias(
                        alias_id=alias.id,
                        user_id=other_user.id
                    )