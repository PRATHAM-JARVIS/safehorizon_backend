"""add_broadcast_table

Revision ID: 7d50900ec9ff
Revises: bfe053dd8556
Create Date: 2025-10-02 11:34:59.175069

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '7d50900ec9ff'
down_revision = 'bfe053dd8556'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enums using PostgreSQL type
    broadcast_type = postgresql.ENUM('radius', 'zone', 'region', 'all', name='broadcast_type', create_type=False)
    broadcast_severity = postgresql.ENUM('low', 'medium', 'high', 'critical', name='broadcast_severity', create_type=False)
    
    # Try to create the enums, ignore if they exist
    conn = op.get_bind()
    conn.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE broadcast_type AS ENUM ('radius', 'zone', 'region', 'all');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """))
    
    conn.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE broadcast_severity AS ENUM ('low', 'medium', 'high', 'critical');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """))
    
    # Create emergency_broadcasts table
    op.create_table(
        'emergency_broadcasts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('broadcast_id', sa.String(), unique=True, nullable=False),
        sa.Column('broadcast_type', postgresql.ENUM('radius', 'zone', 'region', 'all', name='broadcast_type', create_type=False), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('severity', postgresql.ENUM('low', 'medium', 'high', 'critical', name='broadcast_severity', create_type=False), nullable=False),
        sa.Column('alert_type', sa.String(), nullable=True),
        sa.Column('action_required', sa.String(), nullable=True),
        
        # Radius broadcast fields
        sa.Column('center_latitude', sa.Float(), nullable=True),
        sa.Column('center_longitude', sa.Float(), nullable=True),
        sa.Column('radius_km', sa.Float(), nullable=True),
        
        # Zone broadcast fields
        sa.Column('zone_id', sa.Integer(), nullable=True),
        
        # Region broadcast fields
        sa.Column('region_bounds', sa.Text(), nullable=True),  # JSON
        
        # Metadata
        sa.Column('tourists_notified_count', sa.Integer(), default=0),
        sa.Column('devices_notified_count', sa.Integer(), default=0),
        sa.Column('acknowledgment_count', sa.Integer(), default=0),
        
        # Authority info
        sa.Column('sent_by', sa.String(), sa.ForeignKey('authorities.id'), nullable=False),
        sa.Column('department', sa.String(), nullable=True),
        
        # Timestamps
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['zone_id'], ['restricted_zones.id'], ondelete='SET NULL'),
    )
    
    # Create broadcast acknowledgments table
    op.create_table(
        'broadcast_acknowledgments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('broadcast_id', sa.Integer(), sa.ForeignKey('emergency_broadcasts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tourist_id', sa.String(), sa.ForeignKey('tourists.id', ondelete='CASCADE'), nullable=False),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('status', sa.String(), nullable=True),  # 'safe', 'need_help', 'evacuating'
        sa.Column('location_lat', sa.Float(), nullable=True),
        sa.Column('location_lon', sa.Float(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('broadcast_id', 'tourist_id', name='uq_broadcast_tourist_ack'),
    )
    
    # Create indexes
    op.create_index('idx_broadcasts_broadcast_id', 'emergency_broadcasts', ['broadcast_id'])
    op.create_index('idx_broadcasts_sent_by', 'emergency_broadcasts', ['sent_by'])
    op.create_index('idx_broadcasts_sent_at', 'emergency_broadcasts', ['sent_at'])
    op.create_index('idx_broadcast_acks_broadcast', 'broadcast_acknowledgments', ['broadcast_id'])
    op.create_index('idx_broadcast_acks_tourist', 'broadcast_acknowledgments', ['tourist_id'])


def downgrade() -> None:
    op.drop_index('idx_broadcast_acks_tourist', table_name='broadcast_acknowledgments')
    op.drop_index('idx_broadcast_acks_broadcast', table_name='broadcast_acknowledgments')
    op.drop_index('idx_broadcasts_sent_at', table_name='emergency_broadcasts')
    op.drop_index('idx_broadcasts_sent_by', table_name='emergency_broadcasts')
    op.drop_index('idx_broadcasts_broadcast_id', table_name='emergency_broadcasts')
    
    op.drop_table('broadcast_acknowledgments')
    op.drop_table('emergency_broadcasts')
    
    op.execute('DROP TYPE broadcast_severity')
    op.execute('DROP TYPE broadcast_type')