"""make_efir_fields_nullable_for_tourist_reports

Revision ID: f555f22c4c4d
Revises: 6c7d8e9f0abc
Create Date: 2025-10-02 00:55:46.341249

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f555f22c4c4d'
down_revision = '6c7d8e9f0abc'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Make incident_id nullable (tourist reports don't have incidents initially)
    op.alter_column('efirs', 'incident_id',
                    existing_type=sa.INTEGER(),
                    nullable=True)
    
    # Make authority fields nullable (tourist self-reports don't have officer info)
    op.alter_column('efirs', 'reported_by',
                    existing_type=sa.String(),
                    nullable=True)
    
    op.alter_column('efirs', 'officer_name',
                    existing_type=sa.String(),
                    nullable=True)
    
    op.alter_column('efirs', 'officer_badge',
                    existing_type=sa.String(),
                    nullable=True)
    
    op.alter_column('efirs', 'officer_department',
                    existing_type=sa.String(),
                    nullable=True)
    
    # Add report_source column to distinguish tourist vs authority reports
    op.add_column('efirs', sa.Column('report_source', sa.String(), nullable=True))
    
    # Update existing records to have report_source = 'authority'
    op.execute("UPDATE efirs SET report_source = 'authority' WHERE report_source IS NULL")


def downgrade() -> None:
    # Remove report_source column
    op.drop_column('efirs', 'report_source')
    
    # Revert nullable changes
    op.alter_column('efirs', 'officer_department',
                    existing_type=sa.String(),
                    nullable=False)
    
    op.alter_column('efirs', 'officer_badge',
                    existing_type=sa.String(),
                    nullable=False)
    
    op.alter_column('efirs', 'officer_name',
                    existing_type=sa.String(),
                    nullable=False)
    
    op.alter_column('efirs', 'reported_by',
                    existing_type=sa.String(),
                    nullable=False)
    
    op.alter_column('efirs', 'incident_id',
                    existing_type=sa.INTEGER(),
                    nullable=False)