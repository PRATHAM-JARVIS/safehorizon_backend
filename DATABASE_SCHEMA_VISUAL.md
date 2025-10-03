# SafeHorizon Database Schema - Visual Reference

## Complete Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         SAFEHORIZON DATABASE SCHEMA                             │
│                              11 Tables, 30+ Fields                              │
└─────────────────────────────────────────────────────────────────────────────────┘


┌──────────────────────────────┐
│         TOURISTS             │ ◄─────────────┐
├──────────────────────────────┤               │
│ PK  id (VARCHAR)             │               │
│ UK  email                    │               │
│     name                     │               │
│     phone                    │               │
│     emergency_contact        │               │
│     emergency_phone          │               │
│     password_hash            │               │
│     safety_score (0-100)     │               │
│     is_active                │               │
│     last_location_lat        │               │
│     last_location_lon        │               │
│     last_seen                │               │
│     created_at               │               │
│     updated_at               │               │
└──────────────────────────────┘               │
         │ │ │ │                               │
         │ │ │ └─────────────────┐             │
         │ │ │                   │             │
         │ │ └──────────┐        │             │
         │ │            │        │             │
         │ └────┐       │        │             │
         │      │       │        │             │
         │      │       │        │             │
┌────────▼──────┴───┐  │        │             │
│      TRIPS         │  │        │             │
├────────────────────┤  │        │             │
│ PK  id (SERIAL)    │  │        │             │
│ FK  tourist_id     │  │        │             │
│     destination    │  │        │             │
│     start_date     │  │        │             │
│     end_date       │  │        │             │
│     status         │◄─┼────────┼─────────┐   │
│     itinerary      │  │        │         │   │
│     created_at     │  │        │         │   │
│     updated_at     │  │        │         │   │
└────────────────────┘  │        │         │   │
         │              │        │         │   │
         │              │        │         │   │
         │              │        │         │   │
┌────────▼──────────────▼─────┐  │         │   │
│       LOCATIONS             │  │         │   │
├─────────────────────────────┤  │         │   │
│ PK  id (SERIAL)             │  │         │   │
│ FK  tourist_id              │  │         │   │
│ FK  trip_id (nullable)      │  │         │   │
│ IDX latitude                │  │         │   │
│ IDX longitude               │  │         │   │
│     altitude                │  │         │   │
│     speed                   │  │         │   │
│     accuracy                │  │         │   │
│     timestamp               │◄─┼─────────┼───┼───────┐
│     created_at              │  │         │   │       │
│ AI  safety_score (0-100)    │  │         │   │       │
│     safety_score_updated_at │  │         │   │       │
└─────────────────────────────┘  │         │   │       │
         │                       │         │   │       │
         │                       │         │   │       │
┌────────▼───────────────────────▼─────┐   │   │       │
│            ALERTS                    │   │   │       │
├──────────────────────────────────────┤   │   │       │
│ PK  id (SERIAL)                      │   │   │       │
│ FK  tourist_id                       │   │   │       │
│ FK  location_id (nullable)           │   │   │       │
│ FK  acknowledged_by (authorities.id) │───┼───┼───┐   │
│     type (ENUM)                      │   │   │   │   │
│     severity (ENUM)                  │   │   │   │   │
│     title                            │   │   │   │   │
│     description                      │   │   │   │   │
│     alert_metadata (JSON)            │   │   │   │   │
│ IDX is_acknowledged                  │   │   │   │   │
│ IDX is_resolved                      │   │   │   │   │
│     acknowledged_at                  │   │   │   │   │
│     resolved_at                      │   │   │   │   │
│     created_at                       │   │   │   │   │
│     updated_at                       │   │   │   │   │
└──────────────────────────────────────┘   │   │   │   │
         │                                 │   │   │   │
         │                                 │   │   │   │
┌────────▼─────────────────────────────┐   │   │   │   │
│          INCIDENTS                   │   │   │   │   │
├──────────────────────────────────────┤   │   │   │   │
│ PK  id (SERIAL)                      │   │   │   │   │
│ UK  incident_number                  │   │   │   │   │
│ FK  alert_id                         │   │   │   │   │
│ FK  assigned_to (authorities.id)     │───┼───┼───┤   │
│     status (open/resolved)           │   │   │   │   │
│     priority                         │   │   │   │   │
│     response_time                    │   │   │   │   │
│     resolution_notes                 │   │   │   │   │
│     efir_reference                   │───┐   │   │   │
│     created_at                       │   │   │   │   │
│     updated_at                       │   │   │   │   │
└──────────────────────────────────────┘   │   │   │   │
         │                                 │   │   │   │
         │                                 │   │   │   │
┌────────▼─────────────────────────────────▼───┐   │   │
│              EFIRS                           │   │   │
│    (Electronic First Information Report)    │   │   │
├──────────────────────────────────────────────┤   │   │
│ PK  id (SERIAL)                              │   │   │
│ UK  efir_number (EFIR-YYYYMMDD-NNNN)         │   │   │
│ UK  blockchain_tx_id                         │   │   │
│ FK  incident_id (nullable)                   │   │   │
│ FK  alert_id                                 │   │   │
│ FK  tourist_id                               │───┘   │
│ FK  reported_by (authorities.id, nullable)   │───────┤
│     block_hash                               │       │
│     chain_id                                 │       │
│     incident_type                            │       │
│     severity                                 │       │
│     description                              │       │
│     location_lat                             │       │
│     location_lon                             │       │
│     location_description                     │       │
│     tourist_name (snapshot)                  │       │
│     tourist_email (snapshot)                 │       │
│     tourist_phone (snapshot)                 │       │
│     officer_name                             │       │
│     officer_badge                            │       │
│     officer_department                       │       │
│     report_source (tourist/authority)        │       │
│     witnesses (JSON)                         │       │
│     evidence (JSON)                          │       │
│     officer_notes                            │       │
│     is_verified                              │       │
│     verification_timestamp                   │       │
│     incident_timestamp (IMMUTABLE)           │       │
│     generated_at (IMMUTABLE)                 │       │
│     additional_data (JSON)                   │       │
└──────────────────────────────────────────────┘       │
                                                       │
┌──────────────────────────────────────────────────────▼──┐
│                    AUTHORITIES                          │
├─────────────────────────────────────────────────────────┤
│ PK  id (VARCHAR)                                        │
│ UK  email                                               │
│ UK  badge_number                                        │
│     name                                                │
│     department                                          │
│     rank                                                │
│     phone                                               │
│     password_hash                                       │
│     is_active                                           │
│     created_at                                          │
│     updated_at                                          │
└─────────────────────────────────────────────────────────┘
         │  │
         │  │
         │  └──────────────────────────────┐
         │                                 │
         │                                 │
┌────────▼─────────────────────┐  ┌────────▼───────────────────────────┐
│   RESTRICTED_ZONES           │  │   EMERGENCY_BROADCASTS             │
├──────────────────────────────┤  ├────────────────────────────────────┤
│ PK  id (SERIAL)              │  │ PK  id (SERIAL)                    │
│     name                     │  │ UK  broadcast_id (BCAST-...)       │
│     description              │  │     broadcast_type (ENUM)          │
│     zone_type (ENUM)         │  │     title                          │
│ IDX center_latitude          │  │     message                        │
│ IDX center_longitude         │  │     severity (ENUM)                │
│     radius_meters            │  │     alert_type                     │
│     bounds_json (polygon)    │  │     action_required                │
│     is_active                │  │     center_latitude                │
│ FK  created_by (authorities) │  │     center_longitude               │
│     created_at               │  │     radius_km                      │
│     updated_at               │  │ FK  zone_id (nullable)             │
└──────────────────────────────┘  │     region_bounds (JSON)           │
         │                        │     tourists_notified_count        │
         │                        │     devices_notified_count         │
         └────────────────────────┤     acknowledgment_count           │
                                  │ FK  sent_by (authorities.id)       │
                                  │     department                     │
                                  │     expires_at                     │
                                  │     sent_at                        │
                                  │     created_at                     │
                                  └────────────────────────────────────┘
                                           │
                                           │
                        ┌──────────────────▼─────────────────────┐
                        │  BROADCAST_ACKNOWLEDGMENTS             │
                        ├────────────────────────────────────────┤
                        │ PK  id (SERIAL)                        │
                        │ FK  broadcast_id                       │
                        │ FK  tourist_id                         │
                        │     acknowledged_at                    │
                        │     status (safe/need_help/evacuating) │
                        │     location_lat                       │
                        │     location_lon                       │
                        │     notes                              │
                        └────────────────────────────────────────┘


┌──────────────────────────────────┐
│       USER_DEVICES               │
│   (Push Notification Tokens)    │
├──────────────────────────────────┤
│ PK  id (SERIAL)                  │
│ FK  user_id (tourists.id)        │
│ UK  device_token (FCM)           │
│     device_type (ios/android)    │
│     device_name                  │
│     app_version                  │
│     is_active                    │
│     last_used                    │
│     created_at                   │
│     updated_at                   │
└──────────────────────────────────┘
```

---

## Enums Reference

### AlertType
```
GEOFENCE  - Entered restricted zone
ANOMALY   - AI detected unusual behavior
PANIC     - Panic button pressed
SOS       - Emergency SOS activated
SEQUENCE  - Suspicious movement pattern
MANUAL    - Tourist-reported incident
```

### AlertSeverity
```
LOW      - Minor concern (green)
MEDIUM   - Moderate risk (yellow)
HIGH     - Serious risk (orange)
CRITICAL - Immediate danger (red)
```

### TripStatus
```
PLANNED    - Trip scheduled but not started
ACTIVE     - Currently on trip
COMPLETED  - Trip finished successfully
CANCELLED  - Trip cancelled
```

### ZoneType
```
SAFE       - Low-risk area (tourist spots)
RISKY      - Medium-risk area (caution advised)
RESTRICTED - High-risk area (entry prohibited)
```

### BroadcastType
```
RADIUS  - Circular area notification
ZONE    - Specific restricted zone
REGION  - Bounding box area
ALL     - System-wide broadcast
```

### BroadcastSeverity
```
LOW      - Informational
MEDIUM   - Advisory
HIGH     - Warning
CRITICAL - Emergency evacuation
```

---

## Key Relationships

### One-to-Many Relationships

1. **TOURISTS → TRIPS**
   - One tourist can have multiple trips
   - `trips.tourist_id → tourists.id`

2. **TOURISTS → LOCATIONS**
   - One tourist has many location points
   - `locations.tourist_id → tourists.id`

3. **TOURISTS → ALERTS**
   - One tourist can trigger multiple alerts
   - `alerts.tourist_id → tourists.id`

4. **TOURISTS → USER_DEVICES**
   - One tourist can have multiple devices
   - `user_devices.user_id → tourists.id`

5. **TOURISTS → BROADCAST_ACKNOWLEDGMENTS**
   - One tourist can acknowledge multiple broadcasts
   - `broadcast_acknowledgments.tourist_id → tourists.id`

6. **TRIPS → LOCATIONS**
   - One trip contains many location points
   - `locations.trip_id → trips.id`

7. **AUTHORITIES → RESTRICTED_ZONES**
   - One authority can create multiple zones
   - `restricted_zones.created_by → authorities.id`

8. **AUTHORITIES → INCIDENTS**
   - One authority can handle multiple incidents
   - `incidents.assigned_to → authorities.id`

9. **AUTHORITIES → EFIRS**
   - One authority can file multiple E-FIRs
   - `efirs.reported_by → authorities.id`

10. **AUTHORITIES → EMERGENCY_BROADCASTS**
    - One authority can send multiple broadcasts
    - `emergency_broadcasts.sent_by → authorities.id`

11. **RESTRICTED_ZONES → EMERGENCY_BROADCASTS**
    - One zone can have multiple broadcasts
    - `emergency_broadcasts.zone_id → restricted_zones.id`

12. **EMERGENCY_BROADCASTS → BROADCAST_ACKNOWLEDGMENTS**
    - One broadcast receives many acknowledgments
    - `broadcast_acknowledgments.broadcast_id → emergency_broadcasts.id`

### One-to-One Relationships

1. **ALERTS → INCIDENTS**
   - One alert can create one incident
   - `incidents.alert_id → alerts.id`

2. **INCIDENTS → EFIRS**
   - One incident generates one E-FIR
   - `efirs.incident_id → incidents.id`

3. **ALERTS → EFIRS**
   - One alert can generate one E-FIR (direct filing)
   - `efirs.alert_id → alerts.id`

---

## Critical Indexes

### Spatial Queries
```sql
CREATE INDEX idx_locations_coords 
ON locations (latitude, longitude);

CREATE INDEX idx_restricted_zones_center 
ON restricted_zones (center_latitude, center_longitude);
```

### Temporal Queries
```sql
CREATE INDEX idx_locations_timestamp 
ON locations (timestamp);

CREATE INDEX idx_alerts_created_at 
ON alerts (created_at);
```

### Composite Indexes
```sql
CREATE INDEX idx_locations_tourist_time 
ON locations (tourist_id, timestamp);

CREATE INDEX idx_alerts_tourist_resolved 
ON alerts (tourist_id, is_resolved);
```

### Unique Constraints
```sql
-- Tourists
UNIQUE (email)

-- Authorities
UNIQUE (email)
UNIQUE (badge_number)

-- EFIR
UNIQUE (efir_number)
UNIQUE (blockchain_tx_id)

-- Incidents
UNIQUE (incident_number)

-- Broadcasts
UNIQUE (broadcast_id)

-- User Devices
UNIQUE (device_token)
```

---

## Data Volume Estimates

Assuming **1,000 active tourists** tracked over **1 month**:

| Table | Estimated Rows | Growth Rate | Storage |
|-------|----------------|-------------|---------|
| tourists | 1,000 | Slow (100/month) | 1 MB |
| authorities | 50 | Very slow (5/month) | 50 KB |
| trips | 1,500 | Medium (500/month) | 500 KB |
| **locations** | **25,920,000** | **Very high** (30/min/tourist) | **5 GB** |
| alerts | 5,000 | Medium (100/day) | 2 MB |
| restricted_zones | 200 | Slow (20/month) | 100 KB |
| incidents | 1,000 | Medium (30/day) | 500 KB |
| efirs | 800 | Medium (25/day) | 1 MB |
| user_devices | 2,000 | Medium (50/week) | 200 KB |
| emergency_broadcasts | 50 | Slow (1-2/day) | 50 KB |
| broadcast_acknowledgments | 10,000 | Medium (200/broadcast) | 1 MB |

**Total Estimated Storage (1 month):** ~5.2 GB (mostly locations table)

---

## Query Patterns

### Most Frequent Queries

1. **Get Active Tourists**
```sql
SELECT * FROM tourists 
WHERE last_seen > NOW() - INTERVAL '24 hours'
ORDER BY last_seen DESC;
```

2. **Get Recent Locations for Tourist**
```sql
SELECT * FROM locations 
WHERE tourist_id = ? 
  AND timestamp > NOW() - INTERVAL '6 hours'
ORDER BY timestamp DESC;
```

3. **Get Unresolved Alerts**
```sql
SELECT * FROM alerts 
WHERE is_resolved = FALSE 
ORDER BY severity DESC, created_at DESC;
```

4. **Find Tourists in Zone**
```sql
SELECT DISTINCT t.* 
FROM tourists t
JOIN locations l ON l.tourist_id = t.id
WHERE l.timestamp = (
    SELECT MAX(timestamp) 
    FROM locations 
    WHERE tourist_id = t.id
)
AND SQRT(
    POW(l.latitude - ?, 2) + POW(l.longitude - ?, 2)
) * 111 < ?;  -- radius in km
```

5. **Get Public Panic Alerts**
```sql
SELECT a.id, a.type, a.severity, a.title, 
       a.created_at, a.is_resolved, a.resolved_at,
       l.latitude, l.longitude, l.timestamp
FROM alerts a
LEFT JOIN locations l ON l.id = a.location_id
WHERE a.type IN ('panic', 'sos')
  AND a.created_at > NOW() - INTERVAL '24 hours'
  AND (a.is_resolved = FALSE OR show_resolved = TRUE)
ORDER BY a.created_at DESC
LIMIT 50;
```

---

## Database Maintenance

### Archival Strategy

**High-Volume Tables:**
- **locations:** Archive records > 90 days to cold storage
- **alerts:** Archive resolved alerts > 1 year
- **broadcast_acknowledgments:** Archive > 6 months

### Backup Strategy
- **Full backup:** Daily at 2 AM UTC
- **Incremental backup:** Every 4 hours
- **Point-in-time recovery:** 30 days retention
- **Critical tables:** Real-time replication (tourists, alerts, efirs)

### Performance Monitoring
- **Slow query log:** Queries > 1 second
- **Connection pool:** Monitor active connections
- **Table bloat:** Vacuum analyze weekly
- **Index usage:** Review unused indexes monthly

---

## Security Considerations

### Sensitive Data
- **password_hash:** Bcrypt hashed, never exposed in API
- **blockchain_tx_id:** Public but immutable
- **device_token:** Encrypted at rest
- **tourist contact info:** Redacted in public APIs

### Audit Trail
- **EFIR:** Immutable once created
- **Alerts:** Track who acknowledged/resolved
- **Incidents:** Track assigned officer and resolution
- **Broadcasts:** Track who sent and acknowledgments

### Access Control
- **Tourists:** Can only access own data
- **Authorities:** Can view all tourists in jurisdiction
- **Admin:** Full system access

---

**End of Database Schema Documentation**
