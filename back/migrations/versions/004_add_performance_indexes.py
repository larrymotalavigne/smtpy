"""Add performance indexes for common queries

Revision ID: 004
Revises: 003
Create Date: 2025-11-05

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    """Add indexes for better query performance."""

    # Messages table indexes
    op.create_index(
        'idx_messages_created_at',
        'messages',
        ['created_at'],
        unique=False
    )

    # Messages don't have a direct user_id column - they're linked via domains
    # Removed idx_messages_user_created index

    op.create_index(
        'idx_messages_domain_created',
        'messages',
        ['domain_id', 'created_at'],
        unique=False
    )

    op.create_index(
        'idx_messages_status',
        'messages',
        ['status'],
        unique=False
    )

    # Domains table indexes
    op.create_index(
        'idx_domains_verified',
        'domains',
        ['verified'],
        unique=False
    )

    op.create_index(
        'idx_domains_user_verified',
        'domains',
        ['user_id', 'verified'],
        unique=False
    )

    op.create_index(
        'idx_domains_organization',
        'domains',
        ['organization_id'],
        unique=False
    )

    # Users table indexes
    op.create_index(
        'idx_users_email',
        'users',
        ['email'],
        unique=True
    )

    op.create_index(
        'idx_users_is_active',
        'users',
        ['is_active'],
        unique=False
    )

    op.create_index(
        'idx_users_organization',
        'users',
        ['organization_id'],
        unique=False
    )

    # Aliases table indexes
    op.create_index(
        'idx_aliases_domain',
        'aliases',
        ['domain_id'],
        unique=False
    )

    op.create_index(
        'idx_aliases_created_at',
        'aliases',
        ['created_at'],
        unique=False
    )

    # Organizations table indexes
    op.create_index(
        'idx_organizations_created_at',
        'organizations',
        ['created_at'],
        unique=False
    )

    # Password reset tokens
    op.create_index(
        'idx_password_reset_tokens_user',
        'password_reset_tokens',
        ['user_id'],
        unique=False
    )

    op.create_index(
        'idx_password_reset_tokens_expires',
        'password_reset_tokens',
        ['expires_at'],
        unique=False
    )

    # Email verification tokens
    op.create_index(
        'idx_email_verification_tokens_user',
        'email_verification_tokens',
        ['user_id'],
        unique=False
    )

    op.create_index(
        'idx_email_verification_tokens_expires',
        'email_verification_tokens',
        ['expires_at'],
        unique=False
    )


def downgrade():
    """Remove performance indexes."""

    # Messages table indexes
    op.drop_index('idx_messages_created_at', table_name='messages')
    # idx_messages_user_created was removed - messages don't have user_id
    op.drop_index('idx_messages_domain_created', table_name='messages')
    op.drop_index('idx_messages_status', table_name='messages')

    # Domains table indexes
    op.drop_index('idx_domains_verified', table_name='domains')
    op.drop_index('idx_domains_user_verified', table_name='domains')
    op.drop_index('idx_domains_organization', table_name='domains')

    # Users table indexes
    op.drop_index('idx_users_email', table_name='users')
    op.drop_index('idx_users_is_active', table_name='users')
    op.drop_index('idx_users_organization', table_name='users')

    # Aliases table indexes
    op.drop_index('idx_aliases_domain', table_name='aliases')
    op.drop_index('idx_aliases_created_at', table_name='aliases')

    # Organizations table indexes
    op.drop_index('idx_organizations_created_at', table_name='organizations')

    # Password reset tokens
    op.drop_index('idx_password_reset_tokens_user', table_name='password_reset_tokens')
    op.drop_index('idx_password_reset_tokens_expires', table_name='password_reset_tokens')

    # Email verification tokens
    op.drop_index('idx_email_verification_tokens_user', table_name='email_verification_tokens')
    op.drop_index('idx_email_verification_tokens_expires', table_name='email_verification_tokens')
