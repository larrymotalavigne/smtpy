"""Initial SMTPy v2 models

Revision ID: 001
Revises: 
Create Date: 2025-09-01 17:57:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create organizations table
    op.create_table('organizations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=320), nullable=False),
        sa.Column('stripe_customer_id', sa.String(length=255), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(length=255), nullable=True),
        sa.Column('subscription_status', sa.Enum('TRIALING', 'ACTIVE', 'PAST_DUE', 'CANCELED', 'UNPAID', 'INCOMPLETE', 'INCOMPLETE_EXPIRED', 'PAUSED', name='subscriptionstatus'), nullable=True),
        sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('plan_price_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('stripe_customer_id'),
        sa.UniqueConstraint('stripe_subscription_id')
    )

    # Create domains table
    op.create_table('domains',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'VERIFIED', 'FAILED', name='domainstatus'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('mx_record_verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('spf_record_verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('dkim_record_verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('dmarc_record_verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('dkim_public_key', sa.Text(), nullable=True),
        sa.Column('verification_token', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create messages table
    op.create_table('messages',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('message_id', sa.String(length=255), nullable=False),
        sa.Column('thread_id', sa.String(length=255), nullable=True),
        sa.Column('domain_id', sa.Integer(), nullable=False),
        sa.Column('sender_email', sa.String(length=320), nullable=False),
        sa.Column('recipient_email', sa.String(length=320), nullable=False),
        sa.Column('forwarded_to', sa.String(length=320), nullable=True),
        sa.Column('subject', sa.String(length=500), nullable=True),
        sa.Column('body_preview', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'PROCESSING', 'DELIVERED', 'FAILED', 'BOUNCED', 'REJECTED', name='messagestatus'), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('size_bytes', sa.Integer(), nullable=True),
        sa.Column('has_attachments', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['domain_id'], ['domains.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('message_id')
    )

    # Create events table
    op.create_table('events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('event_type', sa.Enum('USER_CREATED', 'USER_DELETED', 'DOMAIN_CREATED', 'DOMAIN_VERIFIED', 'DOMAIN_DELETED', 'MESSAGE_FORWARDED', 'MESSAGE_BOUNCED', 'SUBSCRIPTION_CREATED', 'SUBSCRIPTION_UPDATED', 'SUBSCRIPTION_CANCELED', 'PAYMENT_SUCCEEDED', 'PAYMENT_FAILED', name='eventtype'), nullable=False),
        sa.Column('event_data', sa.Text(), nullable=True),
        sa.Column('organization_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.String(length=255), nullable=True),
        sa.Column('resource_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create billing_webhook_events table
    op.create_table('billing_webhook_events',
        sa.Column('event_id', sa.String(length=255), nullable=False),
        sa.Column('received_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=True),
        sa.Column('processed', sa.Boolean(), nullable=False, default=False),
        sa.PrimaryKeyConstraint('event_id')
    )

    # Create indexes for performance
    op.create_index(op.f('ix_domains_organization_id'), 'domains', ['organization_id'], unique=False)
    op.create_index(op.f('ix_domains_status'), 'domains', ['status'], unique=False)
    op.create_index(op.f('ix_messages_domain_id'), 'messages', ['domain_id'], unique=False)
    op.create_index(op.f('ix_messages_status'), 'messages', ['status'], unique=False)
    op.create_index(op.f('ix_messages_created_at'), 'messages', ['created_at'], unique=False)
    op.create_index(op.f('ix_events_organization_id'), 'events', ['organization_id'], unique=False)
    op.create_index(op.f('ix_events_event_type'), 'events', ['event_type'], unique=False)
    op.create_index(op.f('ix_billing_webhook_events_processed'), 'billing_webhook_events', ['processed'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_billing_webhook_events_processed'), table_name='billing_webhook_events')
    op.drop_index(op.f('ix_events_event_type'), table_name='events')
    op.drop_index(op.f('ix_events_organization_id'), table_name='events')
    op.drop_index(op.f('ix_messages_created_at'), table_name='messages')
    op.drop_index(op.f('ix_messages_status'), table_name='messages')
    op.drop_index(op.f('ix_messages_domain_id'), table_name='messages')
    op.drop_index(op.f('ix_domains_status'), table_name='domains')
    op.drop_index(op.f('ix_domains_organization_id'), table_name='domains')

    # Drop tables in reverse order
    op.drop_table('billing_webhook_events')
    op.drop_table('events')
    op.drop_table('messages')
    op.drop_table('domains')
    op.drop_table('organizations')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS subscriptionstatus')
    op.execute('DROP TYPE IF EXISTS domainstatus')
    op.execute('DROP TYPE IF EXISTS messagestatus')
    op.execute('DROP TYPE IF EXISTS eventtype')