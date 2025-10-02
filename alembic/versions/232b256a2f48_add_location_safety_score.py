"""add_location_safety_score

Revision ID: 232b256a2f48
Revises: 7d50900ec9ff
Create Date: 2025-10-02 21:47:59.798157

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '232b256a2f48'
down_revision = '7d50900ec9ff'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add safety_score column to locations table
    op.add_column('locations', sa.Column('safety_score', sa.Float, nullable=True, server_default='100.0'))
    
    # Add index for faster queries
    op.create_index('idx_location_safety_score', 'locations', ['safety_score'])
    
    # Add timestamp for when safety score was last calculated
    op.add_column('locations', sa.Column('safety_score_updated_at', sa.DateTime(timezone=True), nullable=True))
    
    # Add index for combined queries
    op.create_index('idx_location_safety_timestamp', 'locations', ['tourist_id', 'safety_score', 'timestamp'])


def downgrade() -> None:
    # Remove indexes
    op.drop_index('idx_location_safety_timestamp', table_name='locations')
    op.drop_index('idx_location_safety_score', table_name='locations')
    
    # Remove columns
    op.drop_column('locations', 'safety_score_updated_at')
    op.drop_column('locations', 'safety_score')