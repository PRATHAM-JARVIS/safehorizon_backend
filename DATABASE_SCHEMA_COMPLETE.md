# SafeHorizon Database Schema Documentation

## Overview

This document provides a comprehensive understanding of the SafeHorizon database schema, including all tables, relationships, constraints, and usage instructions for the database creation script.

## Database Schema Summary

The SafeHorizon system uses **PostgreSQL** as the primary database with **11 core tables** designed to handle tourist safety management, emergency alerts, location tracking, and incident reporting.

### Key Features
- ✅ **11 Database Tables** with proper relationships
- ✅ **7 Enum Types** for data consistency  
- ✅ **Geospatial Support** with latitude/longitude coordinates
- ✅ **Blockchain Integration** for E-FIR immutability
- ✅ **Real-time Notifications** via device tokens
- ✅ **Role-based Access Control** (Tourist, Authority, Admin)
- ✅ **Comprehensive Indexing** for performance
- ✅ **Data Integrity** with constraints and triggers

---

## Database Tables

### 1. **tourists** - Tourist User Accounts
Primary table for tourist users and their profiles.

```sql
CREATE TABLE tourists (
    id VARCHAR(36) PRIMARY KEY,           -- UUID primary key
    email VARCHAR(255) UNIQUE NOT NULL,   -- Login email
    name VARCHAR(255),                    -- Full name
    phone VARCHAR(50),                    -- Contact number
    emergency_contact VARCHAR(255),       -- Emergency contact name
    emergency_phone VARCHAR(50),          -- Emergency contact phone
    password_hash VARCHAR(255),           -- Hashed password
    safety_score INTEGER DEFAULT 100,     -- AI-calculated safety score (0-100)
    is_active BOOLEAN DEFAULT TRUE,       -- Account status
    last_location_lat DECIMAL(10, 8),     -- Last known latitude
    last_location_lon DECIMAL(11, 8),     -- Last known longitude
    last_seen TIMESTAMPTZ,               -- Last activity timestamp
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Key Features:**
- UUID-based primary keys for security
- Safety score calculated by AI algorithms
- Emergency contact information for crisis situations
- Location tracking for real-time monitoring

### 2. **authorities** - Police/Authority Users
Table for law enforcement and authority personnel.

```sql
CREATE TABLE authorities (
    id VARCHAR(36) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    badge_number VARCHAR(100) UNIQUE NOT NULL,  -- Unique badge identifier
    department VARCHAR(255) NOT NULL,           -- Police department
    rank VARCHAR(100),                          -- Officer rank
    phone VARCHAR(50),
    password_hash VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Key Features:**
- Badge number validation for authenticity
- Department and rank tracking
- Role-based access control

### 3. **trips** - Tourist Trip Management
Tracks tourist trips and itineraries.

```sql
CREATE TABLE trips (
    id SERIAL PRIMARY KEY,
    tourist_id VARCHAR(36) NOT NULL REFERENCES tourists(id),
    destination VARCHAR(255) NOT NULL,
    start_date TIMESTAMPTZ,
    end_date TIMESTAMPTZ,
    status trip_status_enum DEFAULT 'planned',  -- planned|active|completed|cancelled
    itinerary JSONB,                           -- Flexible trip details
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Key Features:**
- Trip status tracking with enum validation
- JSON-based itinerary for flexible data storage
- Automatic foreign key relationships

### 4. **locations** - Real-time Location Tracking
Stores GPS coordinates and location data.

```sql
CREATE TABLE locations (
    id SERIAL PRIMARY KEY,
    tourist_id VARCHAR(36) NOT NULL REFERENCES tourists(id),
    trip_id INTEGER REFERENCES trips(id),
    latitude DECIMAL(10, 8) NOT NULL,          -- GPS latitude
    longitude DECIMAL(11, 8) NOT NULL,         -- GPS longitude  
    altitude DECIMAL(8, 2),                    -- Elevation
    speed DECIMAL(6, 2),                       -- Movement speed
    accuracy DECIMAL(6, 2),                    -- GPS accuracy
    timestamp TIMESTAMPTZ NOT NULL,            -- Location timestamp
    safety_score DECIMAL(5, 2) DEFAULT 100.0, -- Location-specific safety
    safety_score_updated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Key Features:**
- High-precision coordinate storage
- Real-time safety scoring per location
- Performance optimized with spatial indexing

### 5. **alerts** - Emergency Alert System
Central table for all types of alerts and emergencies.

```sql
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    tourist_id VARCHAR(36) NOT NULL REFERENCES tourists(id),
    location_id INTEGER REFERENCES locations(id),
    type alert_type_enum NOT NULL,           -- geofence|anomaly|panic|sos|sequence|manual
    severity alert_severity_enum NOT NULL,   -- low|medium|high|critical
    title VARCHAR(255) NOT NULL,
    description TEXT,
    alert_metadata JSONB,                    -- Additional alert data
    is_acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by VARCHAR(36) REFERENCES authorities(id),
    acknowledged_at TIMESTAMPTZ,
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_by VARCHAR(36) REFERENCES authorities(id),
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Key Features:**
- Multiple alert types (panic, SOS, geofence violations)
- Severity-based prioritization
- Full alert lifecycle tracking (creation → acknowledgment → resolution)
- Authority assignment for response management

### 6. **restricted_zones** - Geofenced Safety Zones
Defines geographical boundaries and safety zones.

```sql
CREATE TABLE restricted_zones (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    zone_type zone_type_enum NOT NULL,       -- safe|risky|restricted
    center_latitude DECIMAL(10, 8) NOT NULL,
    center_longitude DECIMAL(11, 8) NOT NULL,
    radius_meters DECIMAL(10, 2),            -- Circular zone radius
    bounds_json JSONB,                       -- Complex polygon boundaries
    is_active BOOLEAN DEFAULT TRUE,
    created_by VARCHAR(36) REFERENCES authorities(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Key Features:**
- Circular and polygon zone support
- Zone type classification for different safety levels
- Authority-managed zone creation

### 7. **incidents** - Incident Management
Formal incident reports linked to alerts.

```sql
CREATE TABLE incidents (
    id SERIAL PRIMARY KEY,
    alert_id INTEGER NOT NULL REFERENCES alerts(id),
    incident_number VARCHAR(50) UNIQUE NOT NULL,
    status VARCHAR(50) DEFAULT 'open',
    priority VARCHAR(20),
    assigned_to VARCHAR(36) REFERENCES authorities(id),
    response_time TIMESTAMPTZ,
    resolution_notes TEXT,
    efir_reference VARCHAR(255),             -- Blockchain reference
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 8. **efirs** - Electronic First Information Report (Blockchain)
Immutable incident reports with blockchain verification.

```sql
CREATE TABLE efirs (
    id SERIAL PRIMARY KEY,
    efir_number VARCHAR(50) UNIQUE NOT NULL,
    blockchain_tx_id VARCHAR(255) UNIQUE NOT NULL,  -- Blockchain transaction
    block_hash VARCHAR(255),
    chain_id VARCHAR(100),
    
    -- Immutable incident data
    incident_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    description TEXT NOT NULL,
    location_lat DECIMAL(10, 8),
    location_lon DECIMAL(11, 8),
    
    -- Stakeholder information
    tourist_id VARCHAR(36) NOT NULL REFERENCES tourists(id),
    tourist_name VARCHAR(255) NOT NULL,     -- Snapshot data
    tourist_email VARCHAR(255) NOT NULL,
    reported_by VARCHAR(36) REFERENCES authorities(id),
    
    -- Evidence and verification
    witnesses JSONB,
    evidence JSONB,
    is_verified BOOLEAN DEFAULT TRUE,
    
    -- Immutable timestamps
    incident_timestamp TIMESTAMPTZ NOT NULL,
    generated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
```

**Key Features:**
- **Blockchain Integration**: Cryptographic verification with transaction IDs
- **Immutable Records**: Cannot be modified after creation
- **Legal Compliance**: Formal incident documentation
- **Evidence Storage**: JSON-based witness and evidence tracking

### 9. **user_devices** - Push Notification Devices
Manages device tokens for mobile push notifications.

```sql
CREATE TABLE user_devices (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES tourists(id),
    device_token VARCHAR(500) UNIQUE NOT NULL,  -- FCM/APNS token
    device_type VARCHAR(20) NOT NULL,           -- ios|android
    device_name VARCHAR(255),                   -- Device model
    app_version VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    last_used TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 10. **emergency_broadcasts** - Mass Emergency Notifications
System for broadcasting emergency messages to tourists in specific areas.

```sql
CREATE TABLE emergency_broadcasts (
    id SERIAL PRIMARY KEY,
    broadcast_id VARCHAR(50) UNIQUE NOT NULL,
    broadcast_type broadcast_type_enum NOT NULL,  -- radius|zone|region|all
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    severity broadcast_severity_enum NOT NULL,
    
    -- Location-based targeting
    center_latitude DECIMAL(10, 8),           -- For radius broadcasts
    center_longitude DECIMAL(11, 8),
    radius_km DECIMAL(8, 2),
    zone_id INTEGER REFERENCES restricted_zones(id),  -- For zone broadcasts
    region_bounds JSONB,                      -- For region broadcasts
    
    -- Analytics
    tourists_notified_count INTEGER DEFAULT 0,
    acknowledgment_count INTEGER DEFAULT 0,
    
    sent_by VARCHAR(36) NOT NULL REFERENCES authorities(id),
    expires_at TIMESTAMPTZ,
    sent_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 11. **broadcast_acknowledgments** - Emergency Response Tracking
Tracks tourist responses to emergency broadcasts.

```sql
CREATE TABLE broadcast_acknowledgments (
    id SERIAL PRIMARY KEY,
    broadcast_id INTEGER NOT NULL REFERENCES emergency_broadcasts(id),
    tourist_id VARCHAR(36) NOT NULL REFERENCES tourists(id),
    acknowledged_at TIMESTAMPTZ DEFAULT NOW(),
    status VARCHAR(20),                       -- safe|need_help|evacuating
    location_lat DECIMAL(10, 8),              -- Response location
    location_lon DECIMAL(11, 8),
    notes TEXT,
    
    UNIQUE(broadcast_id, tourist_id)          -- One response per broadcast
);
```

---

## Database Enums

The system uses 7 enum types for data consistency:

```sql
-- User roles
CREATE TYPE user_role_enum AS ENUM ('tourist', 'authority', 'admin');

-- Trip status
CREATE TYPE trip_status_enum AS ENUM ('planned', 'active', 'completed', 'cancelled');

-- Alert classification  
CREATE TYPE alert_type_enum AS ENUM ('geofence', 'anomaly', 'panic', 'sos', 'sequence', 'manual');
CREATE TYPE alert_severity_enum AS ENUM ('low', 'medium', 'high', 'critical');

-- Zone types
CREATE TYPE zone_type_enum AS ENUM ('safe', 'risky', 'restricted');

-- Broadcast system
CREATE TYPE broadcast_type_enum AS ENUM ('radius', 'zone', 'region', 'all');
CREATE TYPE broadcast_severity_enum AS ENUM ('low', 'medium', 'high', 'critical');
```

---

## Database Relationships

### Primary Relationships:
1. **tourists** ← **trips** (One-to-Many)
2. **tourists** ← **locations** (One-to-Many)  
3. **tourists** ← **alerts** (One-to-Many)
4. **alerts** ← **incidents** (One-to-One)
5. **incidents** ← **efirs** (One-to-One)
6. **authorities** ← **restricted_zones** (One-to-Many)
7. **tourists** ← **user_devices** (One-to-Many)

### Cross-References:
- **alerts** ↔ **locations** (Alert can reference specific location)
- **alerts** ↔ **authorities** (Acknowledgment and resolution tracking)
- **emergency_broadcasts** ↔ **restricted_zones** (Zone-based broadcasts)
- **broadcast_acknowledgments** connects broadcasts and tourists

---

## Performance Optimization

### Critical Indexes:
```sql
-- Location queries (most frequent)
CREATE INDEX idx_locations_tourist_time ON locations(tourist_id, timestamp DESC);
CREATE INDEX idx_locations_coords ON locations(latitude, longitude);

-- Real-time alert monitoring
CREATE INDEX idx_alerts_unresolved ON alerts(is_resolved, created_at DESC) 
WHERE is_resolved = FALSE;

-- Geospatial zone queries
CREATE INDEX idx_zones_center ON restricted_zones(center_latitude, center_longitude);

-- Emergency broadcast targeting
CREATE INDEX idx_broadcasts_location ON emergency_broadcasts(center_latitude, center_longitude) 
WHERE broadcast_type = 'radius';
```

### Query Optimization:
- **Partial indexes** on active records only
- **Compound indexes** for common query patterns
- **JSONB indexing** for metadata searches
- **Spatial indexing** for location-based queries

---

## Usage Instructions

### 1. **Setup Requirements**
```bash
# Install dependencies
pip install psycopg2-binary python-dotenv

# Set environment variables
export DATABASE_URL="postgresql://user:password@localhost:5432/safehorizon"
# OR set individual variables:
export DB_HOST="localhost"
export DB_PORT="5432"
export DB_NAME="safehorizon"
export DB_USER="postgres"
export DB_PASSWORD="your_password"
```

### 2. **Create Complete Schema**
```bash
# Create everything (recommended for new installations)
python database_schema_creator.py --create-all

# This will create:
# - PostgreSQL extensions (uuid-ossp, postgis, btree_gin)
# - All enum types
# - All 11 tables with proper relationships
# - Performance indexes
# - Data integrity constraints
# - Automatic update triggers
```

### 3. **Individual Operations**
```bash
# Create only tables
python database_schema_creator.py --create-tables

# Create only indexes (after tables exist)
python database_schema_creator.py --create-indexes

# Insert sample data for testing
python database_schema_creator.py --seed-data

# View schema information
python database_schema_creator.py --show-info
```

### 4. **Custom Database Connection**
```bash
# Specify connection details manually
python database_schema_creator.py --create-all \
  --host "your-db-host.com" \
  --port 5432 \
  --database "safehorizon_prod" \
  --user "postgres" \
  --password "secure_password"
```

### 5. **Dangerous Operations**
```bash
# Drop all tables (BE CAREFUL!)
python database_schema_creator.py --drop-all
# Will prompt for confirmation before proceeding
```

---

## Data Validation & Constraints

### Built-in Validations:
```sql
-- Coordinate validation
CHECK (latitude >= -90 AND latitude <= 90)
CHECK (longitude >= -180 AND longitude <= 180)

-- Email format validation  
CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$')

-- Safety score limits
CHECK (safety_score >= 0 AND safety_score <= 100)

-- Alert resolution logic
CHECK ((is_resolved = FALSE) OR (resolved_by IS NOT NULL AND resolved_at IS NOT NULL))

-- Broadcast type validation
CHECK ((broadcast_type != 'radius') OR (center_latitude IS NOT NULL AND radius_km IS NOT NULL))
```

### Automatic Triggers:
- **Auto-update timestamps**: `updated_at` columns automatically updated
- **Data integrity**: Foreign key cascades properly configured
- **Unique constraints**: Email addresses, badge numbers, device tokens

---

## Security Features

### 1. **Data Protection**
- UUID primary keys prevent enumeration attacks
- Password hashing (handled by application layer)
- Email validation prevents invalid data entry

### 2. **Access Control**
- Role-based enum validation
- Foreign key constraints ensure data consistency
- Soft deletes via `is_active` flags where appropriate

### 3. **Audit Trail**
- Immutable E-FIR records with blockchain verification
- Comprehensive timestamping (`created_at`, `updated_at`)
- Alert acknowledgment and resolution tracking

---

## Integration Points

### 1. **FastAPI Application**
```python
# Use with SQLAlchemy models
from app.models.database_models import Tourist, Alert, Location

# Or direct SQL queries
cursor.execute("SELECT * FROM alerts WHERE is_resolved = FALSE")
```

### 2. **Mobile Applications**
- Device token management for push notifications
- Real-time location updates
- Emergency alert triggering

### 3. **External Services**
- Firebase integration via `user_devices` table
- Blockchain services via `efirs` table
- SMS notifications via tourist/authority phone numbers

---

## Monitoring & Analytics

### Key Metrics Queries:
```sql
-- Active tourists by location
SELECT COUNT(*) FROM tourists WHERE is_active = TRUE AND last_seen > NOW() - INTERVAL '1 hour';

-- Unresolved alerts by severity
SELECT severity, COUNT(*) FROM alerts WHERE is_resolved = FALSE GROUP BY severity;

-- Emergency broadcast effectiveness
SELECT b.title, b.tourists_notified_count, b.acknowledgment_count,
       (b.acknowledgment_count::float / NULLIF(b.tourists_notified_count, 0) * 100) as response_rate
FROM emergency_broadcasts b WHERE b.sent_at > NOW() - INTERVAL '24 hours';

-- Safety score distribution
SELECT 
  CASE 
    WHEN safety_score >= 80 THEN 'Safe (80-100)'
    WHEN safety_score >= 60 THEN 'Moderate (60-79)'
    ELSE 'At Risk (<60)'
  END as risk_level,
  COUNT(*) as tourist_count
FROM tourists WHERE is_active = TRUE GROUP BY 1;
```

---

## Backup & Recovery

### Database Backup:
```bash
# Full database backup
pg_dump -h localhost -U postgres -d safehorizon > safehorizon_backup.sql

# Schema-only backup
pg_dump -h localhost -U postgres -d safehorizon --schema-only > schema_backup.sql

# Data-only backup
pg_dump -h localhost -U postgres -d safehorizon --data-only > data_backup.sql
```

### Recovery:
```bash
# Restore complete database
psql -h localhost -U postgres -d safehorizon < safehorizon_backup.sql

# Recreate schema from script
python database_schema_creator.py --create-all
```

---

## Troubleshooting

### Common Issues:

1. **Connection Failed**
   ```
   Error: psycopg2.OperationalError: could not connect to server
   ```
   **Solution**: Check DATABASE_URL or connection parameters

2. **Permission Denied**
   ```
   Error: permission denied for relation tourists
   ```
   **Solution**: Ensure database user has proper privileges

3. **Extension Not Found**
   ```
   Error: extension "postgis" is not available
   ```
   **Solution**: Install PostGIS or skip optional extensions

4. **Foreign Key Violations**
   ```
   Error: violates foreign key constraint
   ```
   **Solution**: Create tables in dependency order (authorities before zones, tourists before trips)

### Debug Mode:
The script provides detailed logging for troubleshooting:
```python
# Enable verbose SQL logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## Production Deployment

### Recommended Settings:
```sql
-- Connection pooling
max_connections = 200
shared_buffers = 256MB

-- Performance tuning  
work_mem = 4MB
maintenance_work_mem = 64MB
effective_cache_size = 1GB

-- Logging
log_statement = 'mod'
log_min_duration_statement = 1000
```

### Monitoring:
- Set up alerts for unresolved emergency alerts
- Monitor location update frequency
- Track database performance metrics
- Monitor safety score trends

---

This comprehensive database schema supports the complete SafeHorizon tourist safety ecosystem with robust data integrity, performance optimization, and scalability features.