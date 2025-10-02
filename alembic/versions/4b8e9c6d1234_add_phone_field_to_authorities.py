"""add phone field to authorities and enhance location tracking

Revision ID: 4b8e9c6d1234
Revises: 3a974320dcc0
Create Date: 2025-10-01 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4b8e9c6d1234'
down_revision = '3a974320dcc0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add phone field to authorities table (for emergency contact)
    op.add_column('authorities', sa.Column('phone', sa.String(), nullable=True))
    
    # Add radius_meters and bounds_json to restricted_zones if not exists
    # (These should already exist from database_models.py, but adding for safety)
    try:
        op.add_column('restricted_zones', sa.Column('radius_meters', sa.Float(), nullable=True))
    except:
        pass  # Column already exists
    
    try:
        op.add_column('restricted_zones', sa.Column('bounds_json', sa.Text(), nullable=True))
    except:
        pass  # Column already exists


def downgrade() -> None:
    op.drop_column('authorities', 'phone')
    # Don't drop restricted_zones columns as they may be in use
