"""add_manual_alert_type

Revision ID: 5be080418294
Revises: 4b8e9c6d1234
Create Date: 2025-10-01 21:59:55.504867

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5be080418294'
down_revision = '4b8e9c6d1234'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add 'MANUAL' value to the alerttype enum (uppercase to match existing values)
    op.execute("ALTER TYPE alerttype ADD VALUE IF NOT EXISTS 'MANUAL'")


def downgrade() -> None:
    # Note: PostgreSQL doesn't support removing enum values easily
    # This would require recreating the enum type
    pass