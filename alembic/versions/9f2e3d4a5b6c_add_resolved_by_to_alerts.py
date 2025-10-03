"""add resolved_by to alerts

Revision ID: 9f2e3d4a5b6c
Revises: bfe053dd8556
Create Date: 2025-10-03 05:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9f2e3d4a5b6c'
down_revision = '232b256a2f48'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add resolved_by column to alerts table
    op.add_column('alerts', sa.Column('resolved_by', sa.String(), nullable=True))
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_alerts_resolved_by_authorities',
        'alerts', 'authorities',
        ['resolved_by'], ['id']
    )


def downgrade() -> None:
    # Drop foreign key constraint
    op.drop_constraint('fk_alerts_resolved_by_authorities', 'alerts', type_='foreignkey')
    
    # Drop column
    op.drop_column('alerts', 'resolved_by')
