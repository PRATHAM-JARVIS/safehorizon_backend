"""Fix broadcast enum types to match Python enums (uppercase)"""
import asyncio
from sqlalchemy import text
from app.database import engine

async def fix_enum_types():
    """Drop and recreate enum types with uppercase values"""
    async with engine.begin() as conn:
        # Drop existing enum types (will cascade to tables)
        print("Dropping existing broadcast tables and enums...")
        await conn.execute(text("DROP TABLE IF EXISTS broadcast_acknowledgments CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS emergency_broadcasts CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS broadcast_type CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS broadcast_severity CASCADE"))
        
        # Recreate with uppercase values
        print("Creating new enum types with uppercase values...")
        await conn.execute(text("""
            CREATE TYPE broadcast_type AS ENUM ('RADIUS', 'ZONE', 'REGION', 'ALL')
        """))
        
        await conn.execute(text("""
            CREATE TYPE broadcast_severity AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')
        """))
        
        # Recreate tables
        print("Recreating broadcast tables...")
        await conn.execute(text("""
            CREATE TABLE emergency_broadcasts (
                id SERIAL PRIMARY KEY,
                broadcast_id VARCHAR UNIQUE NOT NULL,
                broadcast_type broadcast_type NOT NULL,
                title VARCHAR NOT NULL,
                message TEXT NOT NULL,
                severity broadcast_severity NOT NULL,
                alert_type VARCHAR,
                action_required VARCHAR,
                center_latitude FLOAT,
                center_longitude FLOAT,
                radius_km FLOAT,
                zone_id INTEGER REFERENCES restricted_zones(id) ON DELETE SET NULL,
                region_bounds TEXT,
                tourists_notified_count INTEGER DEFAULT 0,
                devices_notified_count INTEGER DEFAULT 0,
                acknowledgment_count INTEGER DEFAULT 0,
                sent_by VARCHAR REFERENCES authorities(id) NOT NULL,
                department VARCHAR,
                expires_at TIMESTAMPTZ,
                sent_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
            )
        """))
        
        await conn.execute(text("""
            CREATE TABLE broadcast_acknowledgments (
                id SERIAL PRIMARY KEY,
                broadcast_id INTEGER REFERENCES emergency_broadcasts(id) ON DELETE CASCADE NOT NULL,
                tourist_id VARCHAR REFERENCES tourists(id) ON DELETE CASCADE NOT NULL,
                acknowledged_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
                status VARCHAR,
                location_lat FLOAT,
                location_lon FLOAT,
                notes TEXT,
                UNIQUE(broadcast_id, tourist_id)
            )
        """))
        
        # Create indexes
        print("Creating indexes...")
        await conn.execute(text("CREATE INDEX idx_broadcasts_broadcast_id ON emergency_broadcasts(broadcast_id)"))
        await conn.execute(text("CREATE INDEX idx_broadcasts_sent_by ON emergency_broadcasts(sent_by)"))
        await conn.execute(text("CREATE INDEX idx_broadcasts_sent_at ON emergency_broadcasts(sent_at)"))
        await conn.execute(text("CREATE INDEX idx_broadcast_acks_broadcast ON broadcast_acknowledgments(broadcast_id)"))
        await conn.execute(text("CREATE INDEX idx_broadcast_acks_tourist ON broadcast_acknowledgments(tourist_id)"))
        
        print("✅ Successfully fixed broadcast enum types!")

if __name__ == "__main__":
    asyncio.run(fix_enum_types())
