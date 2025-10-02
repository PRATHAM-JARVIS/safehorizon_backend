"""Create EFIR table

Revision ID: 6c7d8e9f0abc
Revises: 5be080418294
Create Date: 2025-10-01 17:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6c7d8e9f0abc'
down_revision: Union[str, None] = '5be080418294'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create efirs table
    op.create_table('efirs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('efir_number', sa.String(), nullable=False),
        sa.Column('incident_id', sa.Integer(), nullable=False),
        sa.Column('alert_id', sa.Integer(), nullable=False),
        sa.Column('tourist_id', sa.String(), nullable=False),
        
        # Blockchain data
        sa.Column('blockchain_tx_id', sa.String(), nullable=False),
        sa.Column('block_hash', sa.String(), nullable=True),
        sa.Column('chain_id', sa.String(), nullable=True),
        
        # E-FIR content
        sa.Column('incident_type', sa.String(), nullable=False),
        sa.Column('severity', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('location_lat', sa.Float(), nullable=True),
        sa.Column('location_lon', sa.Float(), nullable=True),
        sa.Column('location_description', sa.String(), nullable=True),
        
        # Tourist information
        sa.Column('tourist_name', sa.String(), nullable=False),
        sa.Column('tourist_email', sa.String(), nullable=False),
        sa.Column('tourist_phone', sa.String(), nullable=True),
        
        # Authority information
        sa.Column('reported_by', sa.String(), nullable=False),
        sa.Column('officer_name', sa.String(), nullable=False),
        sa.Column('officer_badge', sa.String(), nullable=False),
        sa.Column('officer_department', sa.String(), nullable=False),
        
        # Additional details
        sa.Column('witnesses', sa.Text(), nullable=True),
        sa.Column('evidence', sa.Text(), nullable=True),
        sa.Column('officer_notes', sa.Text(), nullable=True),
        
        # Status
        sa.Column('is_verified', sa.Boolean(), default=True),
        sa.Column('verification_timestamp', sa.DateTime(timezone=True), nullable=True),
        
        # Timestamps
        sa.Column('incident_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        
        # Additional metadata
        sa.Column('additional_data', sa.Text(), nullable=True),
        
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('efir_number'),
        sa.UniqueConstraint('blockchain_tx_id'),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ),
        sa.ForeignKeyConstraint(['alert_id'], ['alerts.id'], ),
        sa.ForeignKeyConstraint(['tourist_id'], ['tourists.id'], ),
        sa.ForeignKeyConstraint(['reported_by'], ['authorities.id'], ),
    )
    op.create_index(op.f('ix_efirs_incident_id'), 'efirs', ['incident_id'], unique=False)
    op.create_index(op.f('ix_efirs_tourist_id'), 'efirs', ['tourist_id'], unique=False)
    op.create_index(op.f('ix_efirs_reported_by'), 'efirs', ['reported_by'], unique=False)
    op.create_index(op.f('ix_efirs_generated_at'), 'efirs', ['generated_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_efirs_generated_at'), table_name='efirs')
    op.drop_index(op.f('ix_efirs_reported_by'), table_name='efirs')
    op.drop_index(op.f('ix_efirs_tourist_id'), table_name='efirs')
    op.drop_index(op.f('ix_efirs_incident_id'), table_name='efirs')
    op.drop_table('efirs')
