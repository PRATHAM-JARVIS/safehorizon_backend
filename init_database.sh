#!/bin/bash

##############################################################################
#                SafeHorizon Database Initialization Script                  #
#                    Complete Database Schema Creation                       #
##############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Configuration
DB_NAME="safehorizon"
DB_USER="postgres"
DB_PASSWORD="${1:-safehorizon_prod_2025}"
DB_HOST="${2:-localhost}"
DB_PORT="${3:-5432}"

print_header() {
    echo -e "\n${BOLD}${BLUE}========================================${NC}"
    echo -e "${BOLD}${BLUE}$1${NC}"
    echo -e "${BOLD}${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ $1${NC}"
}

print_header "SafeHorizon Database Initialization"

# Wait for PostgreSQL to be ready
print_info "Waiting for PostgreSQL to be ready..."
for i in {1..30}; do
    if PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -p $DB_PORT -c '\q' 2>/dev/null; then
        print_success "PostgreSQL is ready!"
        break
    fi
    sleep 2
done

# Create database if not exists
print_info "Creating database '$DB_NAME'..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -p $DB_PORT << EOF
SELECT 'CREATE DATABASE $DB_NAME'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME')\gexec
EOF
print_success "Database '$DB_NAME' ready!"

# Enable PostGIS extension
print_info "Enabling PostGIS extension..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -p $DB_PORT -d $DB_NAME << 'EOF'
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
EOF
print_success "PostGIS enabled!"

# Create ENUM types
print_info "Creating ENUM types..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -p $DB_PORT -d $DB_NAME << 'EOF'
-- Drop existing types if they exist
DROP TYPE IF EXISTS userrole CASCADE;
DROP TYPE IF EXISTS tripstatus CASCADE;
DROP TYPE IF EXISTS alerttype CASCADE;
DROP TYPE IF EXISTS alertseverity CASCADE;
DROP TYPE IF EXISTS zonetype CASCADE;
DROP TYPE IF EXISTS broadcast_type CASCADE;
DROP TYPE IF EXISTS broadcast_severity CASCADE;

-- Create ENUM types (using UPPERCASE as per SQLAlchemy models)
CREATE TYPE userrole AS ENUM ('TOURIST', 'AUTHORITY', 'ADMIN');
CREATE TYPE tripstatus AS ENUM ('PLANNED', 'ACTIVE', 'COMPLETED', 'CANCELLED');
CREATE TYPE alerttype AS ENUM ('GEOFENCE', 'ANOMALY', 'PANIC', 'SOS', 'SEQUENCE', 'MANUAL');
CREATE TYPE alertseverity AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL');
CREATE TYPE zonetype AS ENUM ('SAFE', 'RISKY', 'RESTRICTED');
CREATE TYPE broadcast_type AS ENUM ('RADIUS', 'ZONE', 'REGION', 'ALL');
CREATE TYPE broadcast_severity AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL');
EOF
print_success "ENUM types created!"

# Create tables
print_info "Creating database tables..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -p $DB_PORT -d $DB_NAME << 'EOF'

-- Drop existing tables
DROP TABLE IF EXISTS broadcast_acknowledgments CASCADE;
DROP TABLE IF EXISTS emergency_broadcasts CASCADE;
DROP TABLE IF EXISTS user_devices CASCADE;
DROP TABLE IF EXISTS efirs CASCADE;
DROP TABLE IF EXISTS incidents CASCADE;
DROP TABLE IF EXISTS restricted_zones CASCADE;
DROP TABLE IF EXISTS alerts CASCADE;
DROP TABLE IF EXISTS locations CASCADE;
DROP TABLE IF EXISTS trips CASCADE;
DROP TABLE IF EXISTS authorities CASCADE;
DROP TABLE IF EXISTS tourists CASCADE;

-- 1. Tourists Table
CREATE TABLE tourists (
    id VARCHAR PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    name VARCHAR,
    phone VARCHAR,
    emergency_contact VARCHAR,
    emergency_phone VARCHAR,
    password_hash VARCHAR,
    safety_score INTEGER DEFAULT 100,
    is_active BOOLEAN DEFAULT TRUE,
    last_location_lat DOUBLE PRECISION,
    last_location_lon DOUBLE PRECISION,
    last_seen TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

-- 2. Authorities Table
CREATE TABLE authorities (
    id VARCHAR PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    name VARCHAR NOT NULL,
    badge_number VARCHAR UNIQUE NOT NULL,
    department VARCHAR NOT NULL,
    rank VARCHAR,
    phone VARCHAR,
    password_hash VARCHAR,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

-- 3. Trips Table
CREATE TABLE trips (
    id SERIAL PRIMARY KEY,
    tourist_id VARCHAR NOT NULL REFERENCES tourists(id) ON DELETE CASCADE,
    destination VARCHAR NOT NULL,
    start_date TIMESTAMPTZ,
    end_date TIMESTAMPTZ,
    status tripstatus DEFAULT 'PLANNED',
    itinerary TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

-- 4. Locations Table
CREATE TABLE locations (
    id SERIAL PRIMARY KEY,
    tourist_id VARCHAR NOT NULL REFERENCES tourists(id) ON DELETE CASCADE,
    trip_id INTEGER REFERENCES trips(id) ON DELETE SET NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    altitude DOUBLE PRECISION,
    speed DOUBLE PRECISION,
    accuracy DOUBLE PRECISION,
    timestamp TIMESTAMPTZ NOT NULL,
    safety_score DOUBLE PRECISION DEFAULT 100.0,
    safety_score_updated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Alerts Table
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    tourist_id VARCHAR NOT NULL REFERENCES tourists(id) ON DELETE CASCADE,
    location_id INTEGER REFERENCES locations(id) ON DELETE SET NULL,
    type alerttype NOT NULL,
    severity alertseverity NOT NULL,
    title VARCHAR NOT NULL,
    description TEXT,
    alert_metadata TEXT,
    is_acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by VARCHAR REFERENCES authorities(id) ON DELETE SET NULL,
    acknowledged_at TIMESTAMPTZ,
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

-- 6. Restricted Zones Table
CREATE TABLE restricted_zones (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    description TEXT,
    zone_type zonetype NOT NULL,
    center_latitude DOUBLE PRECISION NOT NULL,
    center_longitude DOUBLE PRECISION NOT NULL,
    radius_meters DOUBLE PRECISION,
    bounds_json TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_by VARCHAR REFERENCES authorities(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

-- 7. Incidents Table
CREATE TABLE incidents (
    id SERIAL PRIMARY KEY,
    alert_id INTEGER NOT NULL REFERENCES alerts(id) ON DELETE CASCADE,
    incident_number VARCHAR UNIQUE NOT NULL,
    status VARCHAR DEFAULT 'open',
    priority VARCHAR,
    assigned_to VARCHAR REFERENCES authorities(id) ON DELETE SET NULL,
    response_time TIMESTAMPTZ,
    resolution_notes TEXT,
    efir_reference VARCHAR,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

-- 8. E-FIR Table
CREATE TABLE efirs (
    id SERIAL PRIMARY KEY,
    efir_number VARCHAR UNIQUE NOT NULL,
    incident_id INTEGER REFERENCES incidents(id) ON DELETE SET NULL,
    alert_id INTEGER NOT NULL REFERENCES alerts(id) ON DELETE CASCADE,
    tourist_id VARCHAR NOT NULL REFERENCES tourists(id) ON DELETE CASCADE,
    blockchain_tx_id VARCHAR UNIQUE NOT NULL,
    block_hash VARCHAR,
    chain_id VARCHAR,
    incident_type VARCHAR NOT NULL,
    severity VARCHAR NOT NULL,
    description TEXT NOT NULL,
    location_lat DOUBLE PRECISION,
    location_lon DOUBLE PRECISION,
    location_description VARCHAR,
    tourist_name VARCHAR NOT NULL,
    tourist_email VARCHAR NOT NULL,
    tourist_phone VARCHAR,
    reported_by VARCHAR REFERENCES authorities(id) ON DELETE SET NULL,
    officer_name VARCHAR,
    officer_badge VARCHAR,
    officer_department VARCHAR,
    report_source VARCHAR,
    witnesses TEXT,
    evidence TEXT,
    officer_notes TEXT,
    is_verified BOOLEAN DEFAULT TRUE,
    verification_timestamp TIMESTAMPTZ,
    incident_timestamp TIMESTAMPTZ NOT NULL,
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    additional_data TEXT
);

-- 9. User Devices Table
CREATE TABLE user_devices (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR NOT NULL REFERENCES tourists(id) ON DELETE CASCADE,
    device_token VARCHAR UNIQUE NOT NULL,
    device_type VARCHAR NOT NULL,
    device_name VARCHAR,
    app_version VARCHAR,
    is_active BOOLEAN DEFAULT TRUE,
    last_used TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

-- 10. Emergency Broadcasts Table
CREATE TABLE emergency_broadcasts (
    id SERIAL PRIMARY KEY,
    broadcast_id VARCHAR UNIQUE NOT NULL,
    broadcast_type broadcast_type NOT NULL,
    title VARCHAR NOT NULL,
    message TEXT NOT NULL,
    severity broadcast_severity NOT NULL,
    alert_type VARCHAR,
    action_required VARCHAR,
    center_latitude DOUBLE PRECISION,
    center_longitude DOUBLE PRECISION,
    radius_km DOUBLE PRECISION,
    zone_id INTEGER REFERENCES restricted_zones(id) ON DELETE SET NULL,
    region_bounds TEXT,
    tourists_notified_count INTEGER DEFAULT 0,
    devices_notified_count INTEGER DEFAULT 0,
    acknowledgment_count INTEGER DEFAULT 0,
    sent_by VARCHAR NOT NULL REFERENCES authorities(id) ON DELETE CASCADE,
    department VARCHAR,
    expires_at TIMESTAMPTZ,
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 11. Broadcast Acknowledgments Table
CREATE TABLE broadcast_acknowledgments (
    id SERIAL PRIMARY KEY,
    broadcast_id INTEGER NOT NULL REFERENCES emergency_broadcasts(id) ON DELETE CASCADE,
    tourist_id VARCHAR NOT NULL REFERENCES tourists(id) ON DELETE CASCADE,
    acknowledged_at TIMESTAMPTZ DEFAULT NOW(),
    status VARCHAR,
    location_lat DOUBLE PRECISION,
    location_lon DOUBLE PRECISION,
    notes TEXT,
    UNIQUE(broadcast_id, tourist_id)
);

EOF
print_success "Database tables created!"

# Create indexes
print_info "Creating indexes..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -p $DB_PORT -d $DB_NAME << 'EOF'

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_tourists_email ON tourists(email);
CREATE INDEX IF NOT EXISTS idx_tourists_last_seen ON tourists(last_seen);
CREATE INDEX IF NOT EXISTS idx_tourists_location ON tourists(last_location_lat, last_location_lon);

CREATE INDEX IF NOT EXISTS idx_authorities_email ON authorities(email);
CREATE INDEX IF NOT EXISTS idx_authorities_badge ON authorities(badge_number);

CREATE INDEX IF NOT EXISTS idx_trips_tourist ON trips(tourist_id);
CREATE INDEX IF NOT EXISTS idx_trips_status ON trips(status);
CREATE INDEX IF NOT EXISTS idx_trips_dates ON trips(start_date, end_date);

CREATE INDEX IF NOT EXISTS idx_locations_tourist ON locations(tourist_id);
CREATE INDEX IF NOT EXISTS idx_locations_trip ON locations(trip_id);
CREATE INDEX IF NOT EXISTS idx_locations_timestamp ON locations(timestamp);
CREATE INDEX IF NOT EXISTS idx_locations_coords ON locations(latitude, longitude);

CREATE INDEX IF NOT EXISTS idx_alerts_tourist ON alerts(tourist_id);
CREATE INDEX IF NOT EXISTS idx_alerts_type ON alerts(type);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(is_acknowledged, is_resolved);
CREATE INDEX IF NOT EXISTS idx_alerts_created ON alerts(created_at);

CREATE INDEX IF NOT EXISTS idx_zones_type ON restricted_zones(zone_type);
CREATE INDEX IF NOT EXISTS idx_zones_active ON restricted_zones(is_active);
CREATE INDEX IF NOT EXISTS idx_zones_coords ON restricted_zones(center_latitude, center_longitude);

CREATE INDEX IF NOT EXISTS idx_incidents_alert ON incidents(alert_id);
CREATE INDEX IF NOT EXISTS idx_incidents_number ON incidents(incident_number);

CREATE INDEX IF NOT EXISTS idx_efirs_number ON efirs(efir_number);
CREATE INDEX IF NOT EXISTS idx_efirs_tourist ON efirs(tourist_id);
CREATE INDEX IF NOT EXISTS idx_efirs_blockchain ON efirs(blockchain_tx_id);

CREATE INDEX IF NOT EXISTS idx_devices_user ON user_devices(user_id);
CREATE INDEX IF NOT EXISTS idx_devices_token ON user_devices(device_token);
CREATE INDEX IF NOT EXISTS idx_devices_active ON user_devices(is_active);

CREATE INDEX IF NOT EXISTS idx_broadcasts_id ON emergency_broadcasts(broadcast_id);
CREATE INDEX IF NOT EXISTS idx_broadcasts_sent_by ON emergency_broadcasts(sent_by);
CREATE INDEX IF NOT EXISTS idx_broadcasts_type ON emergency_broadcasts(broadcast_type);
CREATE INDEX IF NOT EXISTS idx_broadcasts_sent_at ON emergency_broadcasts(sent_at);

CREATE INDEX IF NOT EXISTS idx_acks_broadcast ON broadcast_acknowledgments(broadcast_id);
CREATE INDEX IF NOT EXISTS idx_acks_tourist ON broadcast_acknowledgments(tourist_id);

EOF
print_success "Indexes created!"

# Grant permissions
print_info "Setting permissions..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -p $DB_PORT -d $DB_NAME << EOF
-- Grant all privileges to postgres user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $DB_USER;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $DB_USER;
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
EOF
print_success "Permissions set!"

# Verify tables
print_info "Verifying database schema..."
TABLE_COUNT=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -p $DB_PORT -d $DB_NAME -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';")
print_success "Created $TABLE_COUNT tables successfully!"

print_header "Database Initialization Complete!"

cat << EOF
${BOLD}Database Details:${NC}
  • Host:     $DB_HOST
  • Port:     $DB_PORT
  • Database: $DB_NAME
  • User:     $DB_USER
  • Tables:   $TABLE_COUNT

${BOLD}Tables Created:${NC}
  1. tourists
  2. authorities
  3. trips
  4. locations
  5. alerts
  6. restricted_zones
  7. incidents
  8. efirs
  9. user_devices
  10. emergency_broadcasts
  11. broadcast_acknowledgments

${BOLD}ENUM Types:${NC}
  • userrole, tripstatus, alerttype
  • alertseverity, zonetype
  • broadcasttype, broadcastseverity

${BOLD}Extensions:${NC}
  • PostGIS (for geospatial data)
  • PostGIS Topology

${GREEN}✓ Database ready for SafeHorizon application!${NC}
EOF
