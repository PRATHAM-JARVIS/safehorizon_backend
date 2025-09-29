"""add password hash fields for local auth - simple version

Revision ID: 3aeeb160372a
Revises: 8e1ddfcb01d0
Create Date: 2025-09-28 23:05:13.935534

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3aeeb160372a'
down_revision = '8e1ddfcb01d0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add password hash fields for local authentication
    op.add_column('authorities', sa.Column('password_hash', sa.String(), nullable=True))
    op.add_column('tourists', sa.Column('password_hash', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove password hash fields
    op.drop_column('tourists', 'password_hash')
    op.drop_column('authorities', 'password_hash')