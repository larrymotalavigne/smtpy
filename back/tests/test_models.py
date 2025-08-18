import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from back.api.database.models import User, Domain, Alias, ForwardingRule, ActivityLog, Invitation
from back.core.utils.db import get_db


def unique_name(prefix="test"):
    """Generate a unique name for testing."""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


class TestUserModel:
    """Test cases for User model."""

    def test_user_creation(self):
        """Test basic user creation."""
        with get_db() as session:
            username = unique_name("testuser")
            email = f"{unique_name('test')}@example.com"
            user = User(
                username=username, hashed_password="hashed_password_123", email=email, role="user"
            )
            session.add(user)
            session.commit()

            assert user.id is not None
            assert user.username == username
            assert user.email == email
            assert user.role == "user"
            assert user.is_active is True
            assert user.email_verified is False
            assert user.is_deleted is False
            assert user.created_at is not None
            assert user.updated_at is not None

    def test_user_unique_username(self):
        """Test that usernames must be unique."""
        with get_db() as session:
            duplicate_name = unique_name("duplicate")
            user1 = User(username=duplicate_name, hashed_password="hash1")
            user2 = User(username=duplicate_name, hashed_password="hash2")

            session.add(user1)
            session.commit()

            session.add(user2)
            with pytest.raises(IntegrityError):
                session.commit()

    def test_user_soft_delete(self):
        """Test user soft delete functionality."""
        with get_db() as session:
            user = User(username=unique_name("softdelete"), hashed_password="hash")
            session.add(user)
            session.commit()

            # Soft delete
            user.is_deleted = True
            user.deleted_at = datetime.utcnow()
            session.commit()

            assert user.is_deleted is True
            assert user.deleted_at is not None

    def test_user_admin_role(self):
        """Test user with admin role."""
        with get_db() as session:
            admin = User(
                username=unique_name("admin"),
                hashed_password="admin_hash",
                role="admin",
                email_verified=True,
            )
            session.add(admin)
            session.commit()

            assert admin.role == "admin"
            assert admin.email_verified is True


class TestDomainModel:
    """Test cases for Domain model."""

    def test_domain_creation(self):
        """Test basic domain creation."""
        with get_db() as session:
            # Create owner first
            user = User(username=unique_name("domainowner"), hashed_password="hash")
            session.add(user)
            session.flush()  # Get user.id

            domain_name = f"{unique_name('example')}.com"
            catch_all = f"catchall@{unique_name('example')}.com"
            domain = Domain(name=domain_name, owner_id=user.id, catch_all=catch_all)
            session.add(domain)
            session.commit()

            assert domain.id is not None
            assert domain.name == domain_name
            assert domain.catch_all == catch_all
            assert domain.owner_id == user.id
            assert domain.is_deleted is False
            assert domain.created_at is not None

    def test_domain_unique_name(self):
        """Test that domain names must be unique."""
        with get_db() as session:
            user = User(username=unique_name("owner"), hashed_password="hash")
            session.add(user)
            session.flush()

            duplicate_domain = f"{unique_name('duplicate')}.com"
            domain1 = Domain(name=duplicate_domain, owner_id=user.id)
            domain2 = Domain(name=duplicate_domain, owner_id=user.id)

            session.add(domain1)
            session.commit()

            session.add(domain2)
            with pytest.raises(IntegrityError):
                session.commit()

    def test_domain_owner_relationship(self):
        """Test domain-owner relationship."""
        with get_db() as session:
            username = unique_name("owner")
            domain_name = f"{unique_name('test')}.com"
            user = User(username=username, hashed_password="hash")
            session.add(user)
            session.flush()  # Get user.id

            domain = Domain(name=domain_name, owner_id=user.id)
            session.add(domain)
            session.commit()

            # Refresh to load relationships
            session.refresh(user)
            session.refresh(domain)

            assert len(user.domains) == 1
            assert user.domains[0].name == domain_name
            assert domain.owner.username == username


class TestAliasModel:
    """Test cases for Alias model."""

    def test_alias_creation(self):
        """Test basic alias creation."""
        with get_db() as session:
            # Create user and domain first
            user = User(username=unique_name("aliasowner"), hashed_password="hash")
            session.add(user)
            session.flush()

            domain = Domain(name=f"{unique_name('alias')}.com", owner_id=user.id)
            session.add(domain)
            session.flush()

            alias = Alias(
                local_part="test",
                targets="target1@example.com,target2@example.com",
                domain_id=domain.id,
                owner_id=user.id,
                expires_at=datetime.utcnow() + timedelta(days=30),
            )
            session.add(alias)
            session.commit()

            assert alias.id is not None
            assert alias.local_part == "test"
            assert "target1@example.com" in alias.targets
            assert "target2@example.com" in alias.targets
            assert alias.expires_at is not None
            assert alias.is_deleted is False

    def test_alias_relationships(self):
        """Test alias relationships with domain and owner."""
        with get_db() as session:
            username = unique_name("owner")
            domain_name = f"{unique_name('test')}.com"
            user = User(username=username, hashed_password="hash")
            session.add(user)
            session.flush()  # Get user.id

            domain = Domain(name=domain_name, owner_id=user.id)
            session.add(domain)
            session.flush()  # Get domain.id

            alias = Alias(
                local_part="test", targets="test@example.com", domain_id=domain.id, owner_id=user.id
            )
            session.add(alias)
            session.commit()

            # Refresh to load relationships
            session.refresh(user)
            session.refresh(domain)
            session.refresh(alias)

            assert alias.domain.name == domain_name
            assert alias.owner.username == username
            assert len(domain.aliases) == 1
            assert len(user.aliases) == 1

    def test_alias_expiration(self):
        """Test alias with expiration date."""
        with get_db() as session:
            user = User(username=unique_name("owner"), hashed_password="hash")
            session.add(user)
            session.flush()

            domain = Domain(name=f"{unique_name('expire')}.com", owner_id=user.id)
            session.add(domain)
            session.flush()

            # Expired alias
            expired_alias = Alias(
                local_part="expired",
                targets="test@example.com",
                domain_id=domain.id,
                owner_id=user.id,
                expires_at=datetime.utcnow() - timedelta(days=1),
            )

            # Non-expired alias
            active_alias = Alias(
                local_part="active",
                targets="test@example.com",
                domain_id=domain.id,
                owner_id=user.id,
                expires_at=datetime.utcnow() + timedelta(days=30),
            )

            session.add_all([expired_alias, active_alias])
            session.commit()

            assert expired_alias.expires_at < datetime.utcnow()
            assert active_alias.expires_at > datetime.utcnow()


class TestForwardingRuleModel:
    """Test cases for ForwardingRule model."""

    def test_forwarding_rule_creation(self):
        """Test basic forwarding rule creation."""
        with get_db() as session:
            user = User(username=unique_name("owner"), hashed_password="hash")
            session.add(user)
            session.flush()

            domain_name = f"{unique_name('forward')}.com"
            domain = Domain(name=domain_name, owner_id=user.id)
            session.add(domain)
            session.flush()

            rule = ForwardingRule(
                pattern=f"*@{domain_name}", target="catchall@example.com", domain_id=domain.id
            )
            session.add(rule)
            session.commit()

            assert rule.id is not None
            assert rule.pattern == f"*@{domain_name}"
            assert rule.target == "catchall@example.com"
            assert rule.domain_id == domain.id
            assert rule.created_at is not None

    def test_forwarding_rule_domain_relationship(self):
        """Test forwarding rule relationship with domain."""
        with get_db() as session:
            user = User(username=unique_name("owner"), hashed_password="hash")
            session.add(user)
            session.flush()  # Get user.id

            domain_name = f"{unique_name('test')}.com"
            domain = Domain(name=domain_name, owner_id=user.id)
            session.add(domain)
            session.flush()  # Get domain.id

            rule = ForwardingRule(
                pattern=f"*@{domain_name}", target=f"admin@{domain_name}", domain_id=domain.id
            )
            session.add(rule)
            session.commit()

            # Refresh to load relationships
            session.refresh(domain)
            session.refresh(rule)

            assert rule.domain.name == domain_name
            assert len(domain.forwarding_rules) == 1


class TestActivityLogModel:
    """Test cases for ActivityLog model."""

    def test_activity_log_creation(self):
        """Test basic activity log creation."""
        with get_db() as session:
            log = ActivityLog(
                event_type="forward",
                sender="sender@example.com",
                recipient="recipient@example.com",
                subject="Test Email",
                status="success",
                message="Email forwarded successfully",
            )
            session.add(log)
            session.commit()

            assert log.id is not None
            assert log.event_type == "forward"
            assert log.sender == "sender@example.com"
            assert log.recipient == "recipient@example.com"
            assert log.subject == "Test Email"
            assert log.status == "success"
            assert log.message == "Email forwarded successfully"
            assert log.timestamp is not None

    def test_activity_log_error_event(self):
        """Test activity log for error events."""
        with get_db() as session:
            error_log = ActivityLog(
                event_type="error",
                sender="sender@example.com",
                recipient="invalid@example.com",
                subject="Failed Email",
                status="failed",
                message="Invalid recipient address",
            )
            session.add(error_log)
            session.commit()

            assert error_log.event_type == "error"
            assert error_log.status == "failed"
            assert "Invalid recipient" in error_log.message


class TestInvitationModel:
    """Test cases for Invitation model."""

    def test_invitation_creation(self):
        """Test basic invitation creation."""
        with get_db() as session:
            inviter = User(username=unique_name("inviter"), hashed_password="hash", role="admin")
            session.add(inviter)
            session.flush()

            invitation = Invitation(
                email=f"{unique_name('newuser')}@example.com",
                token=unique_name("invitation_token"),
                expires_at=datetime.utcnow() + timedelta(days=7),
                invited_by=inviter.id,
            )
            session.add(invitation)
            session.commit()

            assert invitation.id is not None
            assert "@example.com" in invitation.email
            assert invitation.expires_at > datetime.utcnow()
            assert invitation.invited_by == inviter.id
            assert invitation.created_at is not None

    def test_invitation_unique_token(self):
        """Test that invitation tokens must be unique."""
        with get_db() as session:
            inviter = User(username=unique_name("inviter"), hashed_password="hash")
            session.add(inviter)
            session.flush()

            duplicate_token = unique_name("duplicate_token")
            inv1 = Invitation(
                email=f"{unique_name('user1')}@example.com",
                token=duplicate_token,
                expires_at=datetime.utcnow() + timedelta(days=7),
                invited_by=inviter.id,
            )
            inv2 = Invitation(
                email=f"{unique_name('user2')}@example.com",
                token=duplicate_token,
                expires_at=datetime.utcnow() + timedelta(days=7),
                invited_by=inviter.id,
            )

            session.add(inv1)
            session.commit()

            session.add(inv2)
            with pytest.raises(IntegrityError):
                session.commit()

    def test_invitation_inviter_relationship(self):
        """Test invitation relationship with inviter."""
        with get_db() as session:
            admin_username = unique_name("admin")
            inviter = User(username=admin_username, hashed_password="hash", role="admin")
            session.add(inviter)
            session.flush()  # Get inviter.id

            invitation = Invitation(
                email=f"{unique_name('newuser')}@example.com",
                token=unique_name("token"),
                expires_at=datetime.utcnow() + timedelta(days=7),
                invited_by=inviter.id,
            )
            session.add(invitation)
            session.commit()

            # Refresh to load relationships
            session.refresh(inviter)
            session.refresh(invitation)

            assert invitation.inviter.username == admin_username
            assert len(inviter.invitations) == 1
            assert "@example.com" in inviter.invitations[0].email
