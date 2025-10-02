"""add_user_devices_table

Revision ID: bfe053dd8556
Revises: f555f22c4c4d
Create Date: 2025-10-02 11:27:28.263045

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bfe053dd8556'
down_revision = 'f555f22c4c4d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create user_devices table
    op.create_table(
        'user_devices',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('device_token', sa.String(), nullable=False),
        sa.Column('device_type', sa.String(), nullable=False),  # 'ios', 'android'
        sa.Column('device_name', sa.String(), nullable=True),
        sa.Column('app_version', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('last_used', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['tourists.id'], ondelete='CASCADE'),
    )
    
    # Create indexes
    op.create_index('idx_user_devices_user_id', 'user_devices', ['user_id'])
    op.create_index('idx_user_devices_token', 'user_devices', ['device_token'], unique=True)
    op.create_index('idx_user_devices_active', 'user_devices', ['is_active'])


def downgrade() -> None:
    op.drop_index('idx_user_devices_active', table_name='user_devices')
    op.drop_index('idx_user_devices_token', table_name='user_devices')
    op.drop_index('idx_user_devices_user_id', table_name='user_devices')
    op.drop_table('user_devices')