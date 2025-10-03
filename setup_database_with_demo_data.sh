#!/bin/bash

# =============================================================================
# SafeHorizon Database Setup Script with Demo Data
# =============================================================================
# This script creates the complete database schema and populates it with
# comprehensive demo data for testing and development purposes.
# =============================================================================

set -e  # Exit on any error

# Color codes for output formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Database configuration (update these as needed)
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-safehorizon}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD:-apple}"

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}  SafeHorizon Database Setup Script  ${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# Function to print section headers
print_section() {
    echo -e "\n${CYAN}==> $1${NC}"
}

# Function to print success messages
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print error messages
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function to print info messages
print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Check if PostgreSQL is running
print_section "Checking PostgreSQL Connection"
if pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" > /dev/null 2>&1; then
    print_success "PostgreSQL is running and accessible"
else
    print_error "PostgreSQL is not accessible. Please ensure it's running."
    exit 1
fi

# Create database if it doesn't exist
print_section "Setting up Database"
if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
    print_info "Database '$DB_NAME' already exists"
else
    createdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME"
    print_success "Created database '$DB_NAME'"
fi

# Enable PostGIS extension
print_section "Enabling PostGIS Extension"
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "CREATE EXTENSION IF NOT EXISTS postgis;" > /dev/null 2>&1
print_success "PostGIS extension enabled"

# Run Alembic migrations to create schema
print_section "Creating Database Schema"
if [ -f "alembic.ini" ]; then
    print_info "Running Alembic migrations..."
    alembic upgrade head
    print_success "Database schema created successfully"
else
    print_error "alembic.ini not found. Please run this script from the project root directory."
    exit 1
fi

# Function to execute SQL with error handling
execute_sql() {
    local sql="$1"
    local description="$2"
    
    if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "$sql" > /dev/null 2>&1; then
        print_success "$description"
    else
        print_error "Failed: $description"
        return 1
    fi
}

# =============================================================================
# DEMO DATA INSERTION
# =============================================================================

print_section "Populating Demo Data"

# 1. Insert Authorities (Police Officers)
print_info "Inserting authority personnel..."
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" << 'EOF'
INSERT INTO authorities (id, email, name, badge_number, department, rank, phone, password_hash, is_active) VALUES
('auth_001', 'officer.smith@police.gov', 'Officer John Smith', 'PD001', 'Metro Police', 'Sergeant', '+1-555-0101', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeVLq4m7KKH6o.F6e', true),
('auth_002', 'detective.jones@police.gov', 'Detective Sarah Jones', 'PD002', 'Criminal Investigation', 'Detective', '+1-555-0102', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeVLq4m7KKH6o.F6e', true),
('auth_003', 'captain.brown@police.gov', 'Captain Michael Brown', 'PD003', 'Metro Police', 'Captain', '+1-555-0103', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeVLq4m7KKH6o.F6e', true),
('auth_004', 'officer.davis@police.gov', 'Officer Emily Davis', 'PD004', 'Tourist Safety Division', 'Officer', '+1-555-0104', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeVLq4m7KKH6o.F6e', true),
('auth_005', 'supervisor.wilson@police.gov', 'Supervisor David Wilson', 'PD005', 'Emergency Response', 'Supervisor', '+1-555-0105', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeVLq4m7KKH6o.F6e', true);
EOF
print_success "✓ Inserted 5 authority personnel"

# 2. Insert Tourists
print_info "Inserting tourist accounts..."
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" << 'EOF'
INSERT INTO tourists (id, email, name, phone, emergency_contact, emergency_phone, password_hash, safety_score, is_active, last_location_lat, last_location_lon, last_seen) VALUES
('tourist_001', 'alice.johnson@email.com', 'Alice Johnson', '+1-555-1001', 'Bob Johnson', '+1-555-1002', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeVLq4m7KKH6o.F6e', 95, true, 40.7589, -73.9851, NOW() - INTERVAL '5 minutes'),
('tourist_002', 'carlos.rodriguez@email.com', 'Carlos Rodriguez', '+1-555-1003', 'Maria Rodriguez', '+1-555-1004', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeVLq4m7KKH6o.F6e', 88, true, 40.7505, -73.9934, NOW() - INTERVAL '2 minutes'),
('tourist_003', 'priya.patel@email.com', 'Priya Patel', '+91-98765-43210', 'Raj Patel', '+91-98765-43211', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeVLq4m7KKH6o.F6e', 92, true, 40.7614, -73.9776, NOW() - INTERVAL '1 minute'),
('tourist_004', 'james.white@email.com', 'James White', '+44-7700-900123', 'Susan White', '+44-7700-900124', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeVLq4m7KKH6o.F6e', 78, true, 40.7282, -74.0776, NOW() - INTERVAL '15 minutes'),
('tourist_005', 'lisa.chen@email.com', 'Lisa Chen', '+86-138-0013-8000', 'David Chen', '+86-138-0013-8001', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeVLq4m7KKH6o.F6e', 100, true, 40.7484, -73.9857, NOW()),
('tourist_006', 'ahmed.hassan@email.com', 'Ahmed Hassan', '+20-10-1234-5678', 'Fatima Hassan', '+20-10-1234-5679', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeVLq4m7KKH6o.F6e', 85, true, 40.7690, -73.9782, NOW() - INTERVAL '8 minutes'),
('tourist_007', 'emma.thompson@email.com', 'Emma Thompson', '+61-400-123-456', 'Tom Thompson', '+61-400-123-457', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeVLq4m7KKH6o.F6e', 90, true, 40.7549, -73.9840, NOW() - INTERVAL '3 minutes'),
('tourist_008', 'marco.silva@email.com', 'Marco Silva', '+55-11-99999-8888', 'Ana Silva', '+55-11-99999-8889', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeVLq4m7KKH6o.F6e', 82, true, 40.7831, -73.9712, NOW() - INTERVAL '20 minutes'),
('tourist_009', 'yuki.tanaka@email.com', 'Yuki Tanaka', '+81-90-1234-5678', 'Hiroshi Tanaka', '+81-90-1234-5679', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeVLq4m7KKH6o.F6e', 96, true, 40.7411, -74.0028, NOW() - INTERVAL '1 minute'),
('tourist_010', 'sophie.martin@email.com', 'Sophie Martin', '+33-6-12-34-56-78', 'Pierre Martin', '+33-6-12-34-56-79', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeVLq4m7KKH6o.F6e', 87, true, 40.7580, -73.9855, NOW() - INTERVAL '10 minutes');
EOF
print_success "✓ Inserted 10 tourist accounts"

# 3. Insert Trips
print_info "Inserting trip data..."
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" << 'EOF'
INSERT INTO trips (tourist_id, destination, start_date, end_date, status, itinerary) VALUES
('tourist_001', 'Times Square & Broadway', NOW() - INTERVAL '2 days', NOW() + INTERVAL '3 days', 'active', '{"day1": "Times Square exploration", "day2": "Broadway show", "day3": "Central Park"}'),
('tourist_002', 'Central Park Area', NOW() - INTERVAL '1 day', NOW() + INTERVAL '4 days', 'active', '{"day1": "Central Park Zoo", "day2": "Museum visits", "day3": "Shopping"}'),
('tourist_003', 'Financial District', NOW(), NOW() + INTERVAL '2 days', 'active', '{"day1": "Wall Street tour", "day2": "9/11 Memorial"}'),
('tourist_004', 'Brooklyn Bridge Area', NOW() - INTERVAL '3 days', NOW() + INTERVAL '1 day', 'active', '{"day1": "Brooklyn Bridge walk", "day2": "DUMBO exploration"}'),
('tourist_005', 'Manhattan Midtown', NOW() - INTERVAL '1 day', NOW() + INTERVAL '5 days', 'active', '{"day1": "Empire State Building", "day2": "Rockefeller Center"}'),
('tourist_006', 'Upper East Side', NOW(), NOW() + INTERVAL '3 days', 'active', '{"day1": "Met Museum", "day2": "Guggenheim", "day3": "Central Park East"}'),
('tourist_007', 'Chelsea & Meatpacking', NOW() - INTERVAL '2 days', NOW() + INTERVAL '2 days', 'active', '{"day1": "High Line walk", "day2": "Chelsea Market"}'),
('tourist_008', 'SoHo & Village', NOW() - INTERVAL '4 days', NOW() - INTERVAL '1 day', 'completed', '{"day1": "SoHo shopping", "day2": "Greenwich Village", "day3": "Washington Square"}'),
('tourist_009', 'Lower Manhattan', NOW() - INTERVAL '1 day', NOW() + INTERVAL '1 day', 'active', '{"day1": "Battery Park", "day2": "Stone Street"}'),
('tourist_010', 'Midtown West', NOW() - INTERVAL '2 days', NOW() + INTERVAL '3 days', 'active', '{"day1": "Penn Station area", "day2": "Madison Square Garden tour"}');
EOF
print_success "✓ Inserted 10 trip records"

# 4. Insert Restricted Zones
print_info "Inserting restricted zones..."
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" << 'EOF'
INSERT INTO restricted_zones (name, description, zone_type, center_latitude, center_longitude, radius_meters, is_active, created_by) VALUES
('Construction Zone - 42nd St', 'Active construction site with safety hazards', 'restricted', 40.7589, -73.9851, 100, true, 'auth_001'),
('High Crime Area - 125th St', 'Area with elevated crime statistics', 'risky', 40.8176, -73.9482, 500, true, 'auth_002'),
('Safe Tourist Zone - Times Square', 'High security area with constant police presence', 'safe', 40.7580, -73.9855, 200, true, 'auth_003'),
('Private Property - Central Park Zoo', 'Restricted access after hours', 'restricted', 40.7678, -73.9718, 150, true, 'auth_001'),
('Emergency Assembly Point', 'Designated safe area for emergencies', 'safe', 40.7505, -73.9934, 300, true, 'auth_004'),
('Bridge Maintenance Zone', 'Brooklyn Bridge maintenance area', 'restricted', 40.7061, -73.9969, 75, true, 'auth_005'),
('Night Safety Zone - Financial District', 'Increased security during night hours', 'safe', 40.7074, -74.0113, 400, true, 'auth_002'),
('Protest Area - Union Square', 'Area with potential crowd control issues', 'risky', 40.7359, -73.9911, 250, true, 'auth_003'),
('Waterfront Safety Zone', 'Supervised waterfront area', 'safe', 40.7024, -74.0170, 200, true, 'auth_004'),
('Subway Station Buffer - Penn Station', 'High traffic safety buffer zone', 'risky', 40.7505, -73.9934, 150, true, 'auth_001');
EOF
print_success "✓ Inserted 10 restricted zones"

# 5. Insert Location History
print_info "Inserting location tracking data..."
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" << 'EOF'
-- Recent locations for active tourists
INSERT INTO locations (tourist_id, trip_id, latitude, longitude, altitude, speed, accuracy, timestamp, safety_score) VALUES
-- Alice Johnson's path through Times Square
('tourist_001', 1, 40.7589, -73.9851, 10.5, 1.2, 5.0, NOW() - INTERVAL '30 minutes', 95.0),
('tourist_001', 1, 40.7590, -73.9850, 10.8, 1.5, 4.8, NOW() - INTERVAL '25 minutes', 95.5),
('tourist_001', 1, 40.7591, -73.9849, 11.0, 0.8, 5.2, NOW() - INTERVAL '20 minutes', 94.8),
('tourist_001', 1, 40.7592, -73.9848, 11.2, 2.1, 4.5, NOW() - INTERVAL '15 minutes', 95.2),
('tourist_001', 1, 40.7593, -73.9847, 11.5, 1.8, 5.0, NOW() - INTERVAL '10 minutes', 95.0),
('tourist_001', 1, 40.7594, -73.9846, 11.8, 1.0, 4.9, NOW() - INTERVAL '5 minutes', 94.9),

-- Carlos Rodriguez in Central Park
('tourist_002', 2, 40.7505, -73.9934, 25.2, 0.5, 6.1, NOW() - INTERVAL '20 minutes', 88.0),
('tourist_002', 2, 40.7506, -73.9933, 25.5, 0.8, 5.8, NOW() - INTERVAL '15 minutes', 88.5),
('tourist_002', 2, 40.7507, -73.9932, 25.8, 1.2, 5.5, NOW() - INTERVAL '10 minutes', 88.2),
('tourist_002', 2, 40.7508, -73.9931, 26.0, 0.9, 5.9, NOW() - INTERVAL '5 minutes', 88.8),
('tourist_002', 2, 40.7509, -73.9930, 26.2, 0.6, 6.0, NOW() - INTERVAL '2 minutes', 88.9),

-- Priya Patel near Financial District
('tourist_003', 3, 40.7614, -73.9776, 5.2, 2.3, 4.2, NOW() - INTERVAL '15 minutes', 92.0),
('tourist_003', 3, 40.7615, -73.9775, 5.5, 2.8, 4.0, NOW() - INTERVAL '10 minutes', 91.8),
('tourist_003', 3, 40.7616, -73.9774, 5.8, 1.9, 4.5, NOW() - INTERVAL '5 minutes', 92.2),
('tourist_003', 3, 40.7617, -73.9773, 6.0, 1.5, 4.8, NOW() - INTERVAL '1 minute', 92.5),

-- James White near Brooklyn Bridge
('tourist_004', 4, 40.7282, -74.0776, 15.8, 3.2, 3.8, NOW() - INTERVAL '30 minutes', 78.0),
('tourist_004', 4, 40.7283, -74.0775, 16.0, 2.9, 4.1, NOW() - INTERVAL '25 minutes', 78.5),
('tourist_004', 4, 40.7284, -74.0774, 16.2, 2.5, 4.3, NOW() - INTERVAL '20 minutes', 78.8),
('tourist_004', 4, 40.7285, -74.0773, 16.5, 2.1, 4.6, NOW() - INTERVAL '15 minutes', 79.0),

-- Lisa Chen in Midtown
('tourist_005', 5, 40.7484, -73.9857, 12.1, 1.1, 5.5, NOW() - INTERVAL '10 minutes', 100.0),
('tourist_005', 5, 40.7485, -73.9856, 12.3, 1.4, 5.2, NOW() - INTERVAL '5 minutes', 99.8),
('tourist_005', 5, 40.7486, -73.9855, 12.5, 1.0, 5.8, NOW(), 100.0);
EOF
print_success "✓ Inserted 23 location tracking records"

# 6. Insert Alerts
print_info "Inserting alert data..."
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" << 'EOF'
INSERT INTO alerts (tourist_id, location_id, type, severity, title, description, alert_metadata, is_acknowledged, acknowledged_by, acknowledged_at, is_resolved, resolved_by, resolved_at) VALUES
-- Active alerts
('tourist_004', 17, 'panic', 'high', 'Tourist Panic Alert', 'Tourist activated panic button near Brooklyn Bridge area', '{"trigger": "manual", "location_accuracy": 4.6}', true, 'auth_001', NOW() - INTERVAL '10 minutes', false, NULL, NULL),
('tourist_002', 8, 'geofence', 'medium', 'Zone Boundary Alert', 'Tourist entered risky area near 125th Street', '{"zone_id": 2, "zone_name": "High Crime Area - 125th St"}', true, 'auth_002', NOW() - INTERVAL '5 minutes', true, 'auth_002', NOW() - INTERVAL '2 minutes'),
('tourist_008', NULL, 'anomaly', 'low', 'Behavior Anomaly Detected', 'Unusual movement pattern detected in SoHo area', '{"anomaly_score": 0.75, "pattern": "erratic_movement"}', false, NULL, NULL, false, NULL, NULL),
('tourist_006', 20, 'sos', 'critical', 'Emergency SOS Signal', 'Tourist activated emergency SOS in Upper East Side', '{"emergency_type": "medical", "contacts_notified": true}', true, 'auth_004', NOW() - INTERVAL '3 minutes', false, NULL, NULL),
('tourist_007', NULL, 'sequence', 'medium', 'Suspicious Activity Pattern', 'Unusual location sequence detected', '{"sequence_score": 0.68, "duration_minutes": 45}', false, NULL, NULL, false, NULL, NULL),

-- Resolved alerts
('tourist_001', 1, 'geofence', 'low', 'Safe Zone Entry', 'Tourist entered designated safe zone', '{"zone_id": 3, "zone_name": "Safe Tourist Zone - Times Square"}', true, 'auth_003', NOW() - INTERVAL '2 hours', true, 'auth_003', NOW() - INTERVAL '1 hour 45 minutes'),
('tourist_003', 13, 'panic', 'medium', 'False Alarm - Panic Button', 'Accidental panic button activation', '{"trigger": "accidental", "user_confirmed": true}', true, 'auth_001', NOW() - INTERVAL '1 hour 30 minutes', true, 'auth_001', NOW() - INTERVAL '1 hour 20 minutes'),
('tourist_005', 22, 'anomaly', 'low', 'Minor Route Deviation', 'Tourist took unexpected route through Midtown', '{"deviation_distance": 150, "reason": "construction_detour"}', true, 'auth_005', NOW() - INTERVAL '45 minutes', true, 'auth_005', NOW() - INTERVAL '40 minutes'),
('tourist_009', NULL, 'manual', 'medium', 'Tourist Reported Incident', 'Tourist reported suspicious individual', '{"report_type": "suspicious_person", "description": "Individual following tourists"}', true, 'auth_002', NOW() - INTERVAL '3 hours', true, 'auth_002', NOW() - INTERVAL '2 hours 30 minutes'),
('tourist_010', NULL, 'geofence', 'medium', 'Restricted Area Alert', 'Tourist approached restricted construction zone', '{"zone_id": 1, "distance_meters": 25}', true, 'auth_001', NOW() - INTERVAL '4 hours', true, 'auth_001', NOW() - INTERVAL '3 hours 45 minutes');
EOF
print_success "✓ Inserted 10 alert records (5 active, 5 resolved)"

# 7. Insert User Devices
print_info "Inserting user device data..."
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" << 'EOF'
INSERT INTO user_devices (user_id, device_token, device_type, device_name, app_version, is_active, last_used) VALUES
('tourist_001', 'fGcI8r9XQzK1mN2oP3qR4sT5uV6wX7yZ8', 'ios', 'iPhone 14 Pro', '1.2.3', true, NOW() - INTERVAL '5 minutes'),
('tourist_001', 'aB1cD2eF3gH4iJ5kL6mN7oP8qR9sT0uV', 'android', 'Samsung Galaxy Tab', '1.2.3', false, NOW() - INTERVAL '2 days'),
('tourist_002', 'xY9zA0bC1dE2fG3hI4jK5lM6nO7pQ8rS', 'android', 'Google Pixel 7', '1.2.3', true, NOW() - INTERVAL '2 minutes'),
('tourist_003', 'tU9vW0xY1zA2bC3dE4fG5hI6jK7lM8nO', 'ios', 'iPhone 13', '1.2.2', true, NOW() - INTERVAL '1 minute'),
('tourist_004', 'pQ8rS9tU0vW1xY2zA3bC4dE5fG6hI7jK', 'android', 'OnePlus 11', '1.2.3', true, NOW() - INTERVAL '15 minutes'),
('tourist_005', 'lM7nO8pQ9rS0tU1vW2xY3zA4bC5dE6fG', 'ios', 'iPhone 15 Pro Max', '1.2.3', true, NOW()),
('tourist_006', 'hI6jK7lM8nO9pQ0rS1tU2vW3xY4zA5bC', 'android', 'Xiaomi 13 Pro', '1.2.1', true, NOW() - INTERVAL '8 minutes'),
('tourist_007', 'dE5fG6hI7jK8lM9nO0pQ1rS2tU3vW4xY', 'ios', 'iPhone 12 Mini', '1.2.3', true, NOW() - INTERVAL '3 minutes'),
('tourist_008', 'zA4bC5dE6fG7hI8jK9lM0nO1pQ2rS3tU', 'android', 'Samsung Galaxy S23', '1.2.3', false, NOW() - INTERVAL '1 day'),
('tourist_009', 'vW3xY4zA5bC6dE7fG8hI9jK0lM1nO2pQ', 'ios', 'iPhone 14', '1.2.3', true, NOW() - INTERVAL '1 minute'),
('tourist_010', 'rS2tU3vW4xY5zA6bC7dE8fG9hI0jK1lM', 'android', 'Google Pixel 8', '1.2.3', true, NOW() - INTERVAL '10 minutes');
EOF
print_success "✓ Inserted 11 user device records"

# 8. Insert Emergency Broadcasts
print_info "Inserting emergency broadcast data..."
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" << 'EOF'
INSERT INTO emergency_broadcasts (broadcast_id, broadcast_type, title, message, severity, alert_type, action_required, center_latitude, center_longitude, radius_km, tourists_notified_count, devices_notified_count, acknowledgment_count, sent_by, department, expires_at, sent_at) VALUES
('BCAST-20251003-001', 'radius', 'Weather Alert - Heavy Rain', 'Heavy rainfall expected in Midtown Manhattan. Seek indoor shelter and avoid low-lying areas.', 'medium', 'weather', 'seek_shelter', 40.7589, -73.9851, 2.0, 156, 178, 142, 'auth_003', 'Emergency Response', NOW() + INTERVAL '6 hours', NOW() - INTERVAL '2 hours'),
('BCAST-20251003-002', 'zone', 'Security Alert - Times Square', 'Increased security presence in Times Square due to suspicious activity. Remain calm and follow police instructions.', 'high', 'security_threat', 'follow_instructions', NULL, NULL, NULL, 89, 95, 67, 'auth_001', 'Metro Police', NOW() + INTERVAL '4 hours', NOW() - INTERVAL '1 hour'),
('BCAST-20251003-003', 'radius', 'Medical Emergency - Central Park', 'Medical emergency response in progress near Central Park Zoo. Avoid the area and use alternate routes.', 'low', 'medical_emergency', 'avoid_area', 40.7678, -73.9718, 0.5, 45, 52, 38, 'auth_004', 'Emergency Response', NOW() + INTERVAL '2 hours', NOW() - INTERVAL '30 minutes'),
('BCAST-20251002-001', 'all', 'System Maintenance Notice', 'SafeHorizon system will undergo maintenance tonight 11 PM - 2 AM EST. Some features may be temporarily unavailable.', 'low', 'system_maintenance', 'be_aware', NULL, NULL, NULL, 1247, 1389, 892, 'auth_005', 'Technical Operations', NOW() - INTERVAL '12 hours', NOW() - INTERVAL '18 hours'),
('BCAST-20251003-004', 'region', 'Traffic Alert - Brooklyn Bridge', 'Heavy traffic congestion on Brooklyn Bridge due to ongoing construction. Consider alternate routes.', 'low', 'traffic', 'use_alternate_route', NULL, NULL, NULL, 234, 267, 189, 'auth_002', 'Traffic Division', NOW() + INTERVAL '8 hours', NOW() - INTERVAL '45 minutes');
EOF
print_success "✓ Inserted 5 emergency broadcast records"

# 9. Insert Broadcast Acknowledgments
print_info "Inserting broadcast acknowledgment data..."
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" << 'EOF'
INSERT INTO broadcast_acknowledgments (broadcast_id, tourist_id, acknowledged_at, status, location_lat, location_lon, notes) VALUES
-- Weather alert acknowledgments
(1, 'tourist_001', NOW() - INTERVAL '1 hour 45 minutes', 'safe', 40.7589, -73.9851, 'Found shelter in nearby building'),
(1, 'tourist_002', NOW() - INTERVAL '1 hour 30 minutes', 'safe', 40.7505, -73.9934, 'In covered area of Central Park'),
(1, 'tourist_005', NOW() - INTERVAL '1 hour 20 minutes', 'safe', 40.7484, -73.9857, 'Inside shopping center'),
(1, 'tourist_010', NOW() - INTERVAL '1 hour 15 minutes', 'safe', 40.7505, -73.9934, 'Taking shelter in subway station'),

-- Security alert acknowledgments
(2, 'tourist_001', NOW() - INTERVAL '45 minutes', 'safe', 40.7580, -73.9855, 'Following police instructions'),
(2, 'tourist_003', NOW() - INTERVAL '40 minutes', 'safe', 40.7614, -73.9776, 'Moved to safe distance as instructed'),
(2, 'tourist_007', NOW() - INTERVAL '35 minutes', 'safe', 40.7549, -73.9840, 'Complying with security measures'),

-- Medical emergency acknowledgments
(3, 'tourist_006', NOW() - INTERVAL '25 minutes', 'safe', 40.7690, -73.9782, 'Using alternate route as suggested'),
(3, 'tourist_009', NOW() - INTERVAL '20 minutes', 'safe', 40.7411, -74.0028, 'Avoiding the area'),

-- System maintenance acknowledgments
(4, 'tourist_004', NOW() - INTERVAL '12 hours', 'safe', 40.7282, -74.0776, 'Noted - will plan accordingly'),
(4, 'tourist_008', NOW() - INTERVAL '11 hours', 'safe', 40.7831, -73.9712, 'Acknowledged maintenance window'),

-- Traffic alert acknowledgments
(5, 'tourist_004', NOW() - INTERVAL '30 minutes', 'safe', 40.7061, -73.9969, 'Taking Manhattan Bridge instead'),
(5, 'tourist_009', NOW() - INTERVAL '25 minutes', 'safe', 40.7024, -74.0170, 'Using subway as alternative');
EOF
print_success "✓ Inserted 13 broadcast acknowledgment records"

# 10. Insert Incidents
print_info "Inserting incident data..."
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" << 'EOF'
INSERT INTO incidents (alert_id, incident_number, status, priority, assigned_to, response_time, resolution_notes, efir_reference) VALUES
(1, 'INC-20251003-001', 'investigating', 'high', 'auth_001', NOW() - INTERVAL '8 minutes', NULL, NULL),
(2, 'INC-20251003-002', 'resolved', 'medium', 'auth_002', NOW() - INTERVAL '3 minutes', 'Tourist safely exited risky area. No further action required.', NULL),
(4, 'INC-20251003-003', 'urgent', 'critical', 'auth_004', NOW() - INTERVAL '2 minutes', NULL, 'EFIR-20251003-0001'),
(6, 'INC-20251003-004', 'resolved', 'low', 'auth_003', NOW() - INTERVAL '1 hour 30 minutes', 'Confirmed safe zone entry. Alert cleared automatically.', NULL),
(7, 'INC-20251003-005', 'resolved', 'medium', 'auth_001', NOW() - INTERVAL '1 hour 15 minutes', 'False alarm confirmed by tourist. Panic button sensitivity reviewed.', 'EFIR-20251003-0002'),
(9, 'INC-20251003-006', 'resolved', 'medium', 'auth_002', NOW() - INTERVAL '2 hours 15 minutes', 'Suspicious individual reported was actually a tour guide. False alarm.', 'EFIR-20251003-0003');
EOF
print_success "✓ Inserted 6 incident records"

# 11. Insert E-FIR Records
print_info "Inserting E-FIR (Electronic First Information Report) data..."
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" << 'EOF'
INSERT INTO efirs (efir_number, incident_id, alert_id, tourist_id, blockchain_tx_id, block_hash, chain_id, incident_type, severity, description, location_lat, location_lon, location_description, tourist_name, tourist_email, tourist_phone, reported_by, officer_name, officer_badge, officer_department, report_source, witnesses, evidence, officer_notes, is_verified, verification_timestamp, incident_timestamp, additional_data) VALUES
('EFIR-20251003-0001', 3, 4, 'tourist_006', '0x1a2b3c4d5e6f7890abcdef1234567890abcdef1234567890abcdef1234567890', '0x9876543210fedcba0987654321fedcba0987654321fedcba0987654321fedcba', 'ethereum-mainnet', 'medical_emergency', 'critical', 'Tourist activated emergency SOS reporting chest pain and difficulty breathing', 40.7690, -73.9782, 'Upper East Side, near Metropolitan Museum', 'Ahmed Hassan', 'ahmed.hassan@email.com', '+20-10-1234-5678', 'auth_004', 'Officer Emily Davis', 'PD004', 'Tourist Safety Division', 'authority', '[]', '[{"type": "location", "timestamp": "2025-10-03T14:45:00Z", "coordinates": [40.7690, -73.9782]}]', 'Immediate medical response dispatched. Ambulance en route.', true, NOW() - INTERVAL '2 minutes', NOW() - INTERVAL '5 minutes', '{"emergency_contacts_notified": true, "ambulance_eta": "3 minutes"}'),

('EFIR-20251003-0002', 5, 7, 'tourist_003', '0x2b3c4d5e6f7890ab1234567890abcdef1234567890abcdef1234567890abcdef', '0x8765432109fedcba9876543210fedcba9876543210fedcba9876543210fedcba', 'ethereum-mainnet', 'false_alarm', 'medium', 'Accidental panic button activation confirmed by tourist. No emergency present.', 40.7614, -73.9776, 'Financial District, near Wall Street', 'Priya Patel', 'priya.patel@email.com', '+91-98765-43210', 'auth_001', 'Officer John Smith', 'PD001', 'Metro Police', 'authority', '[]', '[{"type": "tourist_confirmation", "timestamp": "2025-10-03T13:15:00Z", "confirmed_false_alarm": true}]', 'Tourist confirmed accidental activation. Reviewed panic button sensitivity settings with tourist.', true, NOW() - INTERVAL '1 hour 10 minutes', NOW() - INTERVAL '1 hour 30 minutes', '{"button_sensitivity_adjusted": true, "tourist_education_provided": true}'),

('EFIR-20251003-0003', 6, 9, 'tourist_009', '0x3c4d5e6f7890ab121234567890abcdef1234567890abcdef1234567890abcdef', '0x7654321098fedcba7654321098fedcba7654321098fedcba7654321098fedcba', 'ethereum-mainnet', 'suspicious_activity', 'medium', 'Tourist reported individual following multiple tourists in Battery Park area', 40.7024, -74.0170, 'Battery Park, near Castle Clinton', 'Yuki Tanaka', 'yuki.tanaka@email.com', '+81-90-1234-5678', 'auth_002', 'Detective Sarah Jones', 'PD002', 'Criminal Investigation', 'tourist', '[{"name": "Tour guide", "contact": "NYC Tours Inc.", "badge_verified": true}]', '[{"type": "witness_statement", "content": "Individual was leading authorized tour group"}]', 'Investigation revealed reported individual was licensed tour guide conducting legitimate tour. No suspicious activity confirmed.', true, NOW() - INTERVAL '2 hours 10 minutes', NOW() - INTERVAL '3 hours', '{"tour_company_verified": true, "guide_license_valid": true}'),

('EFIR-20251003-0004', NULL, NULL, 'tourist_008', '0x4d5e6f7890ab12341234567890abcdef1234567890abcdef1234567890abcdef', '0x6543210987fedcba6543210987fedcba6543210987fedcba6543210987fedcba', 'ethereum-mainnet', 'theft_report', 'high', 'Tourist self-reported theft of backpack containing passport and wallet in SoHo area', 40.7231, -74.0023, 'SoHo, near Spring Street subway station', 'Marco Silva', 'marco.silva@email.com', '+55-11-99999-8888', NULL, NULL, NULL, NULL, 'tourist', '[{"description": "Store clerk who saw incident", "store": "SoHo Electronics", "contact": "store_contact@sohoelectronics.com"}]', '[{"type": "cctv_reference", "location": "Spring St Station", "timestamp": "2025-10-03T11:30:00Z"}]', NULL, true, NOW() - INTERVAL '4 hours', NOW() - INTERVAL '4 hours 15 minutes', '{"embassy_notified": true, "credit_cards_cancelled": true, "police_report_filed": true}'),

('EFIR-20251003-0005', NULL, NULL, 'tourist_005', '0x5e6f7890ab123412341234567890abcdef1234567890abcdef1234567890abcdef', '0x543210987fedcba543210987fedcba543210987fedcba543210987fedcba', 'ethereum-mainnet', 'harassment', 'medium', 'Tourist reported verbal harassment and unwanted following behavior near Times Square', 40.7580, -73.9855, 'Times Square, near TKTS Red Steps', 'Lisa Chen', 'lisa.chen@email.com', '+86-138-0013-8000', NULL, NULL, NULL, NULL, 'tourist', '[{"description": "Security guard who observed incident", "company": "Times Square Security", "badge": "TS-4567"}]', '[{"type": "security_footage", "location": "TKTS area", "timestamp": "2025-10-03T09:45:00Z"}]', NULL, true, NOW() - INTERVAL '6 hours', NOW() - INTERVAL '6 hours 30 minutes', '{"security_notified": true, "area_patrol_increased": true, "tourist_escorted_to_safety": true}');
EOF
print_success "✓ Inserted 5 E-FIR records (3 authority-generated, 2 tourist self-reported)"

print_section "Database Setup Complete!"

# Summary report
echo -e "\n${GREEN}======================================${NC}"
echo -e "${GREEN}     DATABASE SETUP SUMMARY          ${NC}"
echo -e "${GREEN}======================================${NC}"
echo -e "${YELLOW}Database:${NC} $DB_NAME"
echo -e "${YELLOW}Host:${NC} $DB_HOST:$DB_PORT"
echo -e "${YELLOW}User:${NC} $DB_USER"
echo ""
echo -e "${CYAN}Data Inserted:${NC}"
echo -e "  • 5 Authority personnel"
echo -e "  • 10 Tourist accounts"
echo -e "  • 10 Trip records"
echo -e "  • 10 Restricted zones"
echo -e "  • 23 Location tracking records"
echo -e "  • 10 Alert records (5 active, 5 resolved)"
echo -e "  • 11 User device registrations"
echo -e "  • 5 Emergency broadcasts"
echo -e "  • 13 Broadcast acknowledgments"
echo -e "  • 6 Incident records"
echo -e "  • 5 E-FIR records (3 authority, 2 tourist)"
echo ""
echo -e "${GREEN}✓ Total records inserted: 108${NC}"
echo -e "${GREEN}✓ Schema created successfully${NC}"
echo -e "${GREEN}✓ Demo data populated${NC}"
echo ""
echo -e "${PURPLE}Ready for testing and development!${NC}"
echo -e "${BLUE}======================================${NC}"

# Test database connection
print_section "Verifying Database Setup"
RECORD_COUNT=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "
SELECT 
    (SELECT COUNT(*) FROM tourists) + 
    (SELECT COUNT(*) FROM authorities) + 
    (SELECT COUNT(*) FROM trips) + 
    (SELECT COUNT(*) FROM restricted_zones) + 
    (SELECT COUNT(*) FROM locations) + 
    (SELECT COUNT(*) FROM alerts) + 
    (SELECT COUNT(*) FROM user_devices) + 
    (SELECT COUNT(*) FROM emergency_broadcasts) + 
    (SELECT COUNT(*) FROM broadcast_acknowledgments) + 
    (SELECT COUNT(*) FROM incidents) + 
    (SELECT COUNT(*) FROM efirs) AS total_records;
" | tr -d ' ')

if [ "$RECORD_COUNT" -eq 108 ]; then
    print_success "Database verification successful - $RECORD_COUNT records found"
else
    print_error "Database verification failed - Expected 108 records, found $RECORD_COUNT"
fi

echo -e "\n${GREEN}Setup complete! You can now start the SafeHorizon API server.${NC}"
echo -e "${YELLOW}Run:${NC} uvicorn app.main:app --reload"
echo ""