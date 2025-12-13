"""Add security events table

Revision ID: 008
Revises: 007
Create Date: 2025-12-13 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '008'
down_revision: Union[str, None] = '007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create security_events table
    op.create_table('security_events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False, server_default='medium'),
        sa.Column('ip_address', sa.String(length=45), nullable=False),
        sa.Column('port', sa.Integer(), nullable=True),
        sa.Column('service', sa.String(length=50), nullable=False, server_default='postfix'),
        sa.Column('details', sa.Text(), nullable=False),
        sa.Column('event_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('action_taken', sa.String(length=100), nullable=True),
        sa.Column('event_metadata', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for common queries
    op.create_index('idx_security_events_timestamp', 'security_events', ['event_timestamp'], unique=False)
    op.create_index('idx_security_events_ip_type', 'security_events', ['ip_address', 'event_type'], unique=False)
    op.create_index('idx_security_events_severity_timestamp', 'security_events', ['severity', 'event_timestamp'], unique=False)
    op.create_index(op.f('ix_security_events_event_type'), 'security_events', ['event_type'], unique=False)
    op.create_index(op.f('ix_security_events_ip_address'), 'security_events', ['ip_address'], unique=False)
    op.create_index(op.f('ix_security_events_severity'), 'security_events', ['severity'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_security_events_severity'), table_name='security_events')
    op.drop_index(op.f('ix_security_events_ip_address'), table_name='security_events')
    op.drop_index(op.f('ix_security_events_event_type'), table_name='security_events')
    op.drop_index('idx_security_events_severity_timestamp', table_name='security_events')
    op.drop_index('idx_security_events_ip_type', table_name='security_events')
    op.drop_index('idx_security_events_timestamp', table_name='security_events')

    # Drop table
    op.drop_table('security_events')
