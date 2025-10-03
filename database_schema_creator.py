#!/usr/bin/env python3
"""
SafeHorizon Database Schema Creator

This script creates the complete SafeHorizon database schema directly in PostgreSQL
without using SQLAlchemy ORM. It includes all tables, relationships, constraints,
indexes, and enums as defined in the original models.

Usage:
    python database_schema_creator.py --create-all
    python database_schema_creator.py --create-tables
    python database_schema_creator.py --create-indexes
    python database_schema_creator.py --seed-data
    python database_schema_creator.py --drop-all

Requirements:
    pip install psycopg2-binary python-dotenv

Environment Variables:
    DATABASE_URL or individual DB connection params:
    - DB_HOST
    - DB_PORT
    - DB_NAME
    - DB_USER
    - DB_PASSWORD
"""

import os
import sys
import argparse
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from psycopg2 import sql
from datetime import datetime, timezone
import uuid
import json
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DatabaseSchemaCreator:
    """Complete SafeHorizon database schema creator"""
    
    def __init__(self, connection_params: Optional[Dict[str, Any]] = None):
        """Initialize with database connection parameters"""
        if connection_params:
            self.connection_params = connection_params
        else:
            # Try to get from DATABASE_URL first
            database_url = os.getenv('DATABASE_URL') or os.getenv('SYNC_DATABASE_URL')
            if database_url:
                self.connection_params = self._parse_database_url(database_url)
            else:
                # Fall back to individual environment variables
                self.connection_params = {
                    'host': os.getenv('DB_HOST', 'localhost'),
                    'port': int(os.getenv('DB_PORT', 5432)),
                    'database': os.getenv('DB_NAME', 'safehorizon'),
                    'user': os.getenv('DB_USER', 'postgres'),
                    'password': os.getenv('DB_PASSWORD', 'postgres')
                }
        
        self.conn = None
        print(f"🔗 Database connection params: {self.connection_params['host']}:{self.connection_params['port']}/{self.connection_params['database']}")
    
    def _parse_database_url(self, database_url: str) -> Dict[str, Any]:
        """Parse PostgreSQL connection URL"""
        # Remove postgresql:// or postgres:// prefix
        if database_url.startswith('postgresql://'):
            url = database_url[13:]
        elif database_url.startswith('postgres://'):
            url = database_url[11:]
        else:
            raise ValueError("Invalid database URL format")
        
        # Parse user:password@host:port/database
        if '@' in url:
            auth_part, host_part = url.split('@', 1)
            if ':' in auth_part:
                user, password = auth_part.split(':', 1)
            else:
                user, password = auth_part, ''
        else:
            user, password = 'postgres', ''
            host_part = url
        
        if '/' in host_part:
            host_port, database = host_part.split('/', 1)
        else:
            host_port, database = host_part, 'safehorizon'
        
        if ':' in host_port:
            host, port = host_port.split(':', 1)
            port = int(port)
        else:
            host, port = host_port, 5432
        
        return {
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password
        }
    
    def connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(**self.connection_params)
            self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            print("✅ Connected to PostgreSQL database")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to database: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            print("🔌 Disconnected from database")
    
    def execute_sql(self, query: str, params=None, fetch=False):
        """Execute SQL query"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, params)
                if fetch:
                    return cursor.fetchall()
                return True
        except Exception as e:
            print(f"❌ SQL Error: {e}")
            print(f"   Query: {query}")
            return False
    
    def create_enums(self):
        """Create all enum types"""
        print("📋 Creating enum types...")
        
        enums = [
            ("user_role_enum", ["tourist", "authority", "admin"]),
            ("trip_status_enum", ["planned", "active", "completed", "cancelled"]),
            ("alert_type_enum", ["geofence", "anomaly", "panic", "sos", "sequence", "manual"]),
            ("alert_severity_enum", ["low", "medium", "high", "critical"]),
            ("zone_type_enum", ["safe", "risky", "restricted"]),
            ("broadcast_type_enum", ["radius", "zone", "region", "all"]),
            ("broadcast_severity_enum", ["low", "medium", "high", "critical"])
        ]
        
        for enum_name, values in enums:
            # Drop if exists
            self.execute_sql(f"DROP TYPE IF EXISTS {enum_name} CASCADE")
            
            # Create enum
            values_str = "', '".join(values)
            self.execute_sql(f"CREATE TYPE {enum_name} AS ENUM ('{values_str}')")
            print(f"   ✅ Created enum: {enum_name}")
    
    def create_extensions(self):
        """Create required PostgreSQL extensions"""
        print("🧩 Creating database extensions...")
        
        extensions = [
            "uuid-ossp",    # For UUID generation
            "postgis",      # For geospatial data (optional)
            "btree_gin",    # For better indexing
        ]
        
        for ext in extensions:
            try:
                self.execute_sql(f"CREATE EXTENSION IF NOT EXISTS \"{ext}\"")
                print(f"   ✅ Created extension: {ext}")
            except Exception as e:
                print(f"   ⚠️  Extension {ext} failed (optional): {e}")
    
    def create_tables(self):
        """Create all database tables"""
        print("🏗️  Creating database tables...")
        
        # 1. Tourists table (independent)
        tourists_sql = """
        CREATE TABLE IF NOT EXISTS tourists (
            id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
            email VARCHAR(255) UNIQUE NOT NULL,
            name VARCHAR(255),
            phone VARCHAR(50),
            emergency_contact VARCHAR(255),
            emergency_phone VARCHAR(50),
            password_hash VARCHAR(255),
            safety_score INTEGER DEFAULT 100 CHECK (safety_score >= 0 AND safety_score <= 100),
            is_active BOOLEAN DEFAULT TRUE,
            last_location_lat DECIMAL(10, 8),
            last_location_lon DECIMAL(11, 8),
            last_seen TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
        """
        self.execute_sql(tourists_sql)
        print("   ✅ Created table: tourists")
        
        # 2. Authorities table (independent)
        authorities_sql = """
        CREATE TABLE IF NOT EXISTS authorities (
            id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
            email VARCHAR(255) UNIQUE NOT NULL,
            name VARCHAR(255) NOT NULL,
            badge_number VARCHAR(100) UNIQUE NOT NULL,
            department VARCHAR(255) NOT NULL,
            rank VARCHAR(100),
            phone VARCHAR(50),
            password_hash VARCHAR(255),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
        """
        self.execute_sql(authorities_sql)
        print("   ✅ Created table: authorities")
        
        # 3. Restricted Zones table (depends on authorities)
        zones_sql = """
        CREATE TABLE IF NOT EXISTS restricted_zones (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            zone_type zone_type_enum NOT NULL,
            center_latitude DECIMAL(10, 8) NOT NULL,
            center_longitude DECIMAL(11, 8) NOT NULL,
            radius_meters DECIMAL(10, 2),
            bounds_json JSONB,
            is_active BOOLEAN DEFAULT TRUE,
            created_by VARCHAR(36) REFERENCES authorities(id) ON DELETE SET NULL,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
        """
        self.execute_sql(zones_sql)
        print("   ✅ Created table: restricted_zones")
        
        # 4. Trips table (depends on tourists)
        trips_sql = """
        CREATE TABLE IF NOT EXISTS trips (
            id SERIAL PRIMARY KEY,
            tourist_id VARCHAR(36) NOT NULL REFERENCES tourists(id) ON DELETE CASCADE,
            destination VARCHAR(255) NOT NULL,
            start_date TIMESTAMPTZ,
            end_date TIMESTAMPTZ,
            status trip_status_enum DEFAULT 'planned',
            itinerary JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
        """
        self.execute_sql(trips_sql)
        print("   ✅ Created table: trips")
        
        # 5. Locations table (depends on tourists and trips)
        locations_sql = """
        CREATE TABLE IF NOT EXISTS locations (
            id SERIAL PRIMARY KEY,
            tourist_id VARCHAR(36) NOT NULL REFERENCES tourists(id) ON DELETE CASCADE,
            trip_id INTEGER REFERENCES trips(id) ON DELETE SET NULL,
            latitude DECIMAL(10, 8) NOT NULL,
            longitude DECIMAL(11, 8) NOT NULL,
            altitude DECIMAL(8, 2),
            speed DECIMAL(6, 2),
            accuracy DECIMAL(6, 2),
            timestamp TIMESTAMPTZ NOT NULL,
            safety_score DECIMAL(5, 2) DEFAULT 100.0 CHECK (safety_score >= 0 AND safety_score <= 100),
            safety_score_updated_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
        """
        self.execute_sql(locations_sql)
        print("   ✅ Created table: locations")
        
        # 6. Alerts table (depends on tourists, locations, authorities)
        alerts_sql = """
        CREATE TABLE IF NOT EXISTS alerts (
            id SERIAL PRIMARY KEY,
            tourist_id VARCHAR(36) NOT NULL REFERENCES tourists(id) ON DELETE CASCADE,
            location_id INTEGER REFERENCES locations(id) ON DELETE SET NULL,
            type alert_type_enum NOT NULL,
            severity alert_severity_enum NOT NULL,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            alert_metadata JSONB,
            is_acknowledged BOOLEAN DEFAULT FALSE,
            acknowledged_by VARCHAR(36) REFERENCES authorities(id) ON DELETE SET NULL,
            acknowledged_at TIMESTAMPTZ,
            is_resolved BOOLEAN DEFAULT FALSE,
            resolved_by VARCHAR(36) REFERENCES authorities(id) ON DELETE SET NULL,
            resolved_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
        """
        self.execute_sql(alerts_sql)
        print("   ✅ Created table: alerts")
        
        # 7. Incidents table (depends on alerts and authorities)
        incidents_sql = """
        CREATE TABLE IF NOT EXISTS incidents (
            id SERIAL PRIMARY KEY,
            alert_id INTEGER NOT NULL REFERENCES alerts(id) ON DELETE CASCADE,
            incident_number VARCHAR(50) UNIQUE NOT NULL,
            status VARCHAR(50) DEFAULT 'open',
            priority VARCHAR(20),
            assigned_to VARCHAR(36) REFERENCES authorities(id) ON DELETE SET NULL,
            response_time TIMESTAMPTZ,
            resolution_notes TEXT,
            efir_reference VARCHAR(255),
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
        """
        self.execute_sql(incidents_sql)
        print("   ✅ Created table: incidents")
        
        # 8. EFIR table (Electronic First Information Report)
        efir_sql = """
        CREATE TABLE IF NOT EXISTS efirs (
            id SERIAL PRIMARY KEY,
            efir_number VARCHAR(50) UNIQUE NOT NULL,
            incident_id INTEGER REFERENCES incidents(id) ON DELETE SET NULL,
            alert_id INTEGER NOT NULL REFERENCES alerts(id) ON DELETE CASCADE,
            tourist_id VARCHAR(36) NOT NULL REFERENCES tourists(id) ON DELETE CASCADE,
            
            -- Blockchain data
            blockchain_tx_id VARCHAR(255) UNIQUE NOT NULL,
            block_hash VARCHAR(255),
            chain_id VARCHAR(100),
            
            -- E-FIR content (immutable)
            incident_type VARCHAR(100) NOT NULL,
            severity VARCHAR(20) NOT NULL,
            description TEXT NOT NULL,
            location_lat DECIMAL(10, 8),
            location_lon DECIMAL(11, 8),
            location_description VARCHAR(500),
            
            -- Tourist information (snapshot)
            tourist_name VARCHAR(255) NOT NULL,
            tourist_email VARCHAR(255) NOT NULL,
            tourist_phone VARCHAR(50),
            
            -- Authority information
            reported_by VARCHAR(36) REFERENCES authorities(id) ON DELETE SET NULL,
            officer_name VARCHAR(255),
            officer_badge VARCHAR(100),
            officer_department VARCHAR(255),
            report_source VARCHAR(20) CHECK (report_source IN ('tourist', 'authority')),
            
            -- Additional details
            witnesses JSONB,
            evidence JSONB,
            officer_notes TEXT,
            
            -- Status
            is_verified BOOLEAN DEFAULT TRUE,
            verification_timestamp TIMESTAMPTZ,
            
            -- Timestamps (immutable)
            incident_timestamp TIMESTAMPTZ NOT NULL,
            generated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
            
            -- Additional metadata
            additional_data JSONB
        )
        """
        self.execute_sql(efir_sql)
        print("   ✅ Created table: efirs")
        
        # 9. User Devices table (for push notifications)
        devices_sql = """
        CREATE TABLE IF NOT EXISTS user_devices (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(36) NOT NULL REFERENCES tourists(id) ON DELETE CASCADE,
            device_token VARCHAR(500) UNIQUE NOT NULL,
            device_type VARCHAR(20) NOT NULL CHECK (device_type IN ('ios', 'android')),
            device_name VARCHAR(255),
            app_version VARCHAR(20),
            is_active BOOLEAN DEFAULT TRUE,
            last_used TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
        """
        self.execute_sql(devices_sql)
        print("   ✅ Created table: user_devices")
        
        # 10. Emergency Broadcasts table
        broadcasts_sql = """
        CREATE TABLE IF NOT EXISTS emergency_broadcasts (
            id SERIAL PRIMARY KEY,
            broadcast_id VARCHAR(50) UNIQUE NOT NULL,
            broadcast_type broadcast_type_enum NOT NULL,
            title VARCHAR(255) NOT NULL,
            message TEXT NOT NULL,
            severity broadcast_severity_enum NOT NULL,
            alert_type VARCHAR(100),
            action_required VARCHAR(100),
            
            -- Radius broadcast fields
            center_latitude DECIMAL(10, 8),
            center_longitude DECIMAL(11, 8),
            radius_km DECIMAL(8, 2),
            
            -- Zone broadcast fields
            zone_id INTEGER REFERENCES restricted_zones(id) ON DELETE SET NULL,
            
            -- Region broadcast fields
            region_bounds JSONB,
            
            -- Metadata
            tourists_notified_count INTEGER DEFAULT 0,
            devices_notified_count INTEGER DEFAULT 0,
            acknowledgment_count INTEGER DEFAULT 0,
            
            -- Authority info
            sent_by VARCHAR(36) NOT NULL REFERENCES authorities(id) ON DELETE CASCADE,
            department VARCHAR(255),
            
            -- Timestamps
            expires_at TIMESTAMPTZ,
            sent_at TIMESTAMPTZ DEFAULT NOW(),
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
        """
        self.execute_sql(broadcasts_sql)
        print("   ✅ Created table: emergency_broadcasts")
        
        # 11. Broadcast Acknowledgments table
        ack_sql = """
        CREATE TABLE IF NOT EXISTS broadcast_acknowledgments (
            id SERIAL PRIMARY KEY,
            broadcast_id INTEGER NOT NULL REFERENCES emergency_broadcasts(id) ON DELETE CASCADE,
            tourist_id VARCHAR(36) NOT NULL REFERENCES tourists(id) ON DELETE CASCADE,
            acknowledged_at TIMESTAMPTZ DEFAULT NOW(),
            status VARCHAR(20) CHECK (status IN ('safe', 'need_help', 'evacuating')),
            location_lat DECIMAL(10, 8),
            location_lon DECIMAL(11, 8),
            notes TEXT,
            
            UNIQUE(broadcast_id, tourist_id)
        )
        """
        self.execute_sql(ack_sql)
        print("   ✅ Created table: broadcast_acknowledgments")
    
    def create_indexes(self):
        """Create all database indexes for performance"""
        print("📊 Creating database indexes...")
        
        indexes = [
            # Tourist indexes
            "CREATE INDEX IF NOT EXISTS idx_tourists_email ON tourists(email)",
            "CREATE INDEX IF NOT EXISTS idx_tourists_active ON tourists(is_active) WHERE is_active = TRUE",
            "CREATE INDEX IF NOT EXISTS idx_tourists_location ON tourists(last_location_lat, last_location_lon) WHERE last_location_lat IS NOT NULL",
            
            # Authority indexes
            "CREATE INDEX IF NOT EXISTS idx_authorities_email ON authorities(email)",
            "CREATE INDEX IF NOT EXISTS idx_authorities_badge ON authorities(badge_number)",
            "CREATE INDEX IF NOT EXISTS idx_authorities_department ON authorities(department)",
            
            # Location indexes (very important for performance)
            "CREATE INDEX IF NOT EXISTS idx_locations_tourist_time ON locations(tourist_id, timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_locations_coords ON locations(latitude, longitude)",
            "CREATE INDEX IF NOT EXISTS idx_locations_timestamp ON locations(timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_locations_safety_score ON locations(safety_score) WHERE safety_score < 80",
            
            # Alert indexes
            "CREATE INDEX IF NOT EXISTS idx_alerts_tourist_time ON alerts(tourist_id, created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_alerts_type_severity ON alerts(type, severity)",
            "CREATE INDEX IF NOT EXISTS idx_alerts_unresolved ON alerts(is_resolved, created_at DESC) WHERE is_resolved = FALSE",
            "CREATE INDEX IF NOT EXISTS idx_alerts_unacknowledged ON alerts(is_acknowledged, created_at DESC) WHERE is_acknowledged = FALSE",
            
            # Trip indexes
            "CREATE INDEX IF NOT EXISTS idx_trips_tourist_status ON trips(tourist_id, status)",
            "CREATE INDEX IF NOT EXISTS idx_trips_active ON trips(status, start_date) WHERE status = 'active'",
            
            # Zone indexes
            "CREATE INDEX IF NOT EXISTS idx_zones_center ON restricted_zones(center_latitude, center_longitude)",
            "CREATE INDEX IF NOT EXISTS idx_zones_type_active ON restricted_zones(zone_type, is_active) WHERE is_active = TRUE",
            
            # EFIR indexes
            "CREATE INDEX IF NOT EXISTS idx_efir_number ON efirs(efir_number)",
            "CREATE INDEX IF NOT EXISTS idx_efir_tourist_time ON efirs(tourist_id, generated_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_efir_blockchain_tx ON efirs(blockchain_tx_id)",
            "CREATE INDEX IF NOT EXISTS idx_efir_incident_timestamp ON efirs(incident_timestamp DESC)",
            
            # Device indexes
            "CREATE INDEX IF NOT EXISTS idx_devices_user_active ON user_devices(user_id, is_active) WHERE is_active = TRUE",
            "CREATE INDEX IF NOT EXISTS idx_devices_token ON user_devices(device_token)",
            
            # Broadcast indexes
            "CREATE INDEX IF NOT EXISTS idx_broadcasts_time ON emergency_broadcasts(sent_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_broadcasts_active ON emergency_broadcasts(expires_at) WHERE expires_at > NOW()",
            "CREATE INDEX IF NOT EXISTS idx_broadcasts_location ON emergency_broadcasts(center_latitude, center_longitude) WHERE broadcast_type = 'radius'",
            
            # Acknowledgment indexes
            "CREATE INDEX IF NOT EXISTS idx_ack_broadcast ON broadcast_acknowledgments(broadcast_id, acknowledged_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_ack_tourist ON broadcast_acknowledgments(tourist_id, acknowledged_at DESC)",
        ]
        
        for index_sql in indexes:
            self.execute_sql(index_sql)
            index_name = index_sql.split("idx_")[1].split(" ")[0] if "idx_" in index_sql else "unnamed"
            print(f"   ✅ Created index: idx_{index_name}")
    
    def create_triggers(self):
        """Create database triggers for automatic updates"""
        print("⚡ Creating database triggers...")
        
        # Update updated_at trigger function
        trigger_function = """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        """
        self.execute_sql(trigger_function)
        
        # Apply trigger to tables with updated_at column
        tables_with_updated_at = [
            "tourists", "authorities", "trips", "alerts", 
            "incidents", "restricted_zones", "user_devices"
        ]
        
        for table in tables_with_updated_at:
            trigger_sql = f"""
            DROP TRIGGER IF EXISTS update_{table}_updated_at ON {table};
            CREATE TRIGGER update_{table}_updated_at
                BEFORE UPDATE ON {table}
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
            """
            self.execute_sql(trigger_sql)
            print(f"   ✅ Created trigger for: {table}")
    
    def create_constraints(self):
        """Create additional constraints and rules"""
        print("🔒 Creating additional constraints...")
        
        constraints = [
            # Location coordinate validation
            "ALTER TABLE locations ADD CONSTRAINT check_latitude CHECK (latitude >= -90 AND latitude <= 90)",
            "ALTER TABLE locations ADD CONSTRAINT check_longitude CHECK (longitude >= -180 AND longitude <= 180)",
            "ALTER TABLE restricted_zones ADD CONSTRAINT check_center_latitude CHECK (center_latitude >= -90 AND center_latitude <= 90)",
            "ALTER TABLE restricted_zones ADD CONSTRAINT check_center_longitude CHECK (center_longitude >= -180 AND center_longitude <= 180)",
            
            # Email format validation
            "ALTER TABLE tourists ADD CONSTRAINT check_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}$')",
            "ALTER TABLE authorities ADD CONSTRAINT check_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}$')",
            
            # Alert resolution logic
            "ALTER TABLE alerts ADD CONSTRAINT check_resolution_logic CHECK ((is_resolved = FALSE) OR (is_resolved = TRUE AND resolved_by IS NOT NULL AND resolved_at IS NOT NULL))",
            "ALTER TABLE alerts ADD CONSTRAINT check_acknowledgment_logic CHECK ((is_acknowledged = FALSE) OR (is_acknowledged = TRUE AND acknowledged_by IS NOT NULL AND acknowledged_at IS NOT NULL))",
            
            # Broadcast constraints
            "ALTER TABLE emergency_broadcasts ADD CONSTRAINT check_radius_broadcast CHECK ((broadcast_type != 'radius') OR (center_latitude IS NOT NULL AND center_longitude IS NOT NULL AND radius_km IS NOT NULL))",
            "ALTER TABLE emergency_broadcasts ADD CONSTRAINT check_zone_broadcast CHECK ((broadcast_type != 'zone') OR (zone_id IS NOT NULL))",
        ]
        
        for constraint_sql in constraints:
            try:
                self.execute_sql(constraint_sql)
                constraint_name = constraint_sql.split("ADD CONSTRAINT ")[1].split(" ")[0] if "ADD CONSTRAINT" in constraint_sql else "unnamed"
                print(f"   ✅ Added constraint: {constraint_name}")
            except Exception as e:
                print(f"   ⚠️  Constraint failed (may already exist): {e}")
    
    def seed_sample_data(self):
        """Insert sample data for testing"""
        print("🌱 Seeding sample data...")
        
        # Sample tourist
        tourist_id = str(uuid.uuid4())
        tourist_sql = """
        INSERT INTO tourists (id, email, name, phone, emergency_contact, emergency_phone, safety_score)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (email) DO NOTHING
        """
        self.execute_sql(tourist_sql, (
            tourist_id, 'john.doe@example.com', 'John Doe', '+1234567890', 
            'Jane Doe', '+0987654321', 85
        ))
        
        # Sample authority
        authority_id = str(uuid.uuid4())
        authority_sql = """
        INSERT INTO authorities (id, email, name, badge_number, department, rank)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (email) DO NOTHING
        """
        self.execute_sql(authority_sql, (
            authority_id, 'officer.smith@police.gov', 'Officer Smith', 
            'BADGE001', 'Metropolitan Police', 'Sergeant'
        ))
        
        # Sample zone
        zone_sql = """
        INSERT INTO restricted_zones (name, description, zone_type, center_latitude, center_longitude, radius_meters, created_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        self.execute_sql(zone_sql, (
            'City Center Safe Zone', 'Main tourist area with high security', 'safe',
            40.7128, -74.0060, 1000.0, authority_id
        ))
        
        print("   ✅ Sample data inserted")
    
    def drop_all_tables(self):
        """Drop all tables (careful!)"""
        print("🗑️  Dropping all tables...")
        
        # Drop in reverse order due to foreign key constraints
        tables = [
            "broadcast_acknowledgments",
            "emergency_broadcasts", 
            "user_devices",
            "efirs",
            "incidents",
            "alerts",
            "locations",
            "trips",
            "restricted_zones",
            "authorities",
            "tourists"
        ]
        
        for table in tables:
            self.execute_sql(f"DROP TABLE IF EXISTS {table} CASCADE")
            print(f"   ✅ Dropped table: {table}")
        
        # Drop enums
        enums = [
            "broadcast_severity_enum", "broadcast_type_enum", "zone_type_enum",
            "alert_severity_enum", "alert_type_enum", "trip_status_enum", "user_role_enum"
        ]
        
        for enum in enums:
            self.execute_sql(f"DROP TYPE IF EXISTS {enum} CASCADE")
            print(f"   ✅ Dropped enum: {enum}")
    
    def show_schema_info(self):
        """Display schema information"""
        print("📊 Database Schema Information")
        print("=" * 50)
        
        # Get table info
        table_info = self.execute_sql("""
        SELECT table_name, 
               (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
        FROM information_schema.tables t
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        ORDER BY table_name
        """, fetch=True)
        
        if table_info:
            print(f"📋 Tables: {len(table_info)}")
            for table_name, col_count in table_info:
                print(f"   • {table_name} ({col_count} columns)")
        
        # Get enum info
        enum_info = self.execute_sql("""
        SELECT t.typname, array_agg(e.enumlabel ORDER BY e.enumsortorder) as values
        FROM pg_type t 
        JOIN pg_enum e ON t.oid = e.enumtypid  
        GROUP BY t.typname
        ORDER BY t.typname
        """, fetch=True)
        
        if enum_info:
            print(f"\n🏷️  Enums: {len(enum_info)}")
            for enum_name, values in enum_info:
                values_str = "', '".join(values)
                print(f"   • {enum_name}: ['{values_str}']")
        
        # Get index info
        index_info = self.execute_sql("""
        SELECT schemaname, tablename, indexname, indexdef 
        FROM pg_indexes 
        WHERE schemaname = 'public' AND indexname LIKE 'idx_%'
        ORDER BY tablename, indexname
        """, fetch=True)
        
        if index_info:
            print(f"\n📊 Custom Indexes: {len(index_info)}")
            for schema, table, index_name, index_def in index_info:
                print(f"   • {table}.{index_name}")


def main():
    """Main function with command-line interface"""
    parser = argparse.ArgumentParser(description='SafeHorizon Database Schema Creator')
    parser.add_argument('--create-all', action='store_true', help='Create complete schema')
    parser.add_argument('--create-tables', action='store_true', help='Create tables only')
    parser.add_argument('--create-indexes', action='store_true', help='Create indexes only')
    parser.add_argument('--seed-data', action='store_true', help='Insert sample data')
    parser.add_argument('--drop-all', action='store_true', help='Drop all tables (dangerous!)')
    parser.add_argument('--show-info', action='store_true', help='Show schema information')
    
    # Database connection options
    parser.add_argument('--host', default='localhost', help='Database host')
    parser.add_argument('--port', type=int, default=5432, help='Database port')
    parser.add_argument('--database', default='safehorizon', help='Database name')
    parser.add_argument('--user', default='postgres', help='Database user')
    parser.add_argument('--password', help='Database password')
    
    args = parser.parse_args()
    
    # Prepare connection params
    connection_params = None
    if args.password:
        connection_params = {
            'host': args.host,
            'port': args.port,
            'database': args.database,
            'user': args.user,
            'password': args.password
        }
    
    # Create schema creator instance
    creator = DatabaseSchemaCreator(connection_params)
    
    if not creator.connect():
        sys.exit(1)
    
    try:
        if args.drop_all:
            confirm = input("⚠️  Are you sure you want to drop all tables? (yes/no): ")
            if confirm.lower() == 'yes':
                creator.drop_all_tables()
            else:
                print("❌ Operation cancelled")
                return
        
        if args.create_all:
            print("🚀 Creating complete SafeHorizon database schema...")
            creator.create_extensions()
            creator.create_enums()
            creator.create_tables()
            creator.create_indexes()
            creator.create_triggers()
            creator.create_constraints()
            print("✅ Complete schema created successfully!")
        
        if args.create_tables:
            creator.create_extensions()
            creator.create_enums()
            creator.create_tables()
        
        if args.create_indexes:
            creator.create_indexes()
        
        if args.seed_data:
            creator.seed_sample_data()
        
        if args.show_info:
            creator.show_schema_info()
        
        if not any([args.create_all, args.create_tables, args.create_indexes, 
                   args.seed_data, args.drop_all, args.show_info]):
            print("No action specified. Use --help for options.")
            creator.show_schema_info()
    
    finally:
        creator.disconnect()


if __name__ == "__main__":
    main()