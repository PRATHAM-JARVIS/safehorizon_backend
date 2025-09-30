# 🗺️ SafeHorizon Heatmap API - cURL Examples

**Complete cURL command examples for the new heatmap and geofencing API endpoints**

Base URL: `http://localhost:8000/api` (Development)

---

## 🔐 Authentication Setup

First, get your authentication token:

```bash
# Tourist Login
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "tourist@example.com",
    "password": "password123"
  }'

# Authority Login  
curl -X POST "http://localhost:8000/api/auth/login-authority" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "officer@police.com",
    "password": "police123"
  }'
```

**Export your token for convenience:**
```bash
export TOURIST_TOKEN="your_tourist_token_here"
export AUTHORITY_TOKEN="your_authority_token_here"
```

---

## 🏗️ Zone Management (Authority Only)

### Create Restricted Zone
```bash
curl -X POST "http://localhost:8000/api/zones/create" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTHORITY_TOKEN" \
  -d '{
    "name": "Downtown High Crime Area",
    "description": "Area with increased crime reports - exercise extreme caution",
    "zone_type": "restricted",
    "coordinates": [
      [139.6503, 35.6762],
      [139.6603, 35.6762],
      [139.6603, 35.6862],
      [139.6503, 35.6862],
      [139.6503, 35.6762]
    ]
  }'
```

### Create Risky Zone
```bash
curl -X POST "http://localhost:8000/api/zones/create" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTHORITY_TOKEN" \
  -d '{
    "name": "Night Market Area",
    "description": "Crowded area with pickpocket reports at night",
    "zone_type": "risky",
    "coordinates": [
      [139.6403, 35.6662],
      [139.6503, 35.6662],
      [139.6503, 35.6762],
      [139.6403, 35.6762],
      [139.6403, 35.6662]
    ]
  }'
```

### Create Safe Zone
```bash
curl -X POST "http://localhost:8000/api/zones/create" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTHORITY_TOKEN" \
  -d '{
    "name": "Tourist Information Center",
    "description": "Well-patrolled tourist information area with security",
    "zone_type": "safe",
    "coordinates": [
      [139.6303, 35.6562],
      [139.6403, 35.6562],
      [139.6403, 35.6662],
      [139.6303, 35.6662],
      [139.6303, 35.6562]
    ]
  }'
```

### List All Zones
```bash
curl -X GET "http://localhost:8000/api/zones/manage" \
  -H "Authorization: Bearer $AUTHORITY_TOKEN"
```

### Delete Zone
```bash
curl -X DELETE "http://localhost:8000/api/zones/123" \
  -H "Authorization: Bearer $AUTHORITY_TOKEN"
```

---

## 🗺️ Comprehensive Heatmap Data (Authority Dashboard)

### Get Complete Heatmap Data
Get all heatmap data (zones, alerts, tourists, hotspots) in one call:

```bash
curl -X GET "http://localhost:8000/api/heatmap/data?hours_back=24&include_zones=true&include_alerts=true&include_tourists=true" \
  -H "Authorization: Bearer $AUTHORITY_TOKEN"
```

### Get Heatmap Data for Specific Area (with bounds)
```bash
curl -X GET "http://localhost:8000/api/heatmap/data?bounds_north=35.7&bounds_south=35.6&bounds_east=139.8&bounds_west=139.6&hours_back=12" \
  -H "Authorization: Bearer $AUTHORITY_TOKEN"
```

### Get Heatmap Data for Last Hour (Real-time)
```bash
curl -X GET "http://localhost:8000/api/heatmap/data?hours_back=1&include_zones=true&include_alerts=true&include_tourists=true" \
  -H "Authorization: Bearer $AUTHORITY_TOKEN"
```

---

## 🏢 Zone-Specific Heatmap Data (Authority)

### Get All Zone Types
```bash
curl -X GET "http://localhost:8000/api/heatmap/zones" \
  -H "Authorization: Bearer $AUTHORITY_TOKEN"
```

### Get Only Restricted Zones
```bash
curl -X GET "http://localhost:8000/api/heatmap/zones?zone_type=restricted" \
  -H "Authorization: Bearer $AUTHORITY_TOKEN"
```

### Get Risky Zones in Specific Area
```bash
curl -X GET "http://localhost:8000/api/heatmap/zones?zone_type=risky&bounds_north=35.7&bounds_south=35.6&bounds_east=139.8&bounds_west=139.6" \
  -H "Authorization: Bearer $AUTHORITY_TOKEN"
```

### Get Safe Zones
```bash
curl -X GET "http://localhost:8000/api/heatmap/zones?zone_type=safe" \
  -H "Authorization: Bearer $AUTHORITY_TOKEN"
```

---

## 🚨 Alert Heatmap Data (Authority)

### Get All Recent Alerts
```bash
curl -X GET "http://localhost:8000/api/heatmap/alerts?hours_back=24" \
  -H "Authorization: Bearer $AUTHORITY_TOKEN"
```

### Get Critical Alerts Only
```bash
curl -X GET "http://localhost:8000/api/heatmap/alerts?severity=critical&hours_back=48" \
  -H "Authorization: Bearer $AUTHORITY_TOKEN"
```

### Get SOS Alerts
```bash
curl -X GET "http://localhost:8000/api/heatmap/alerts?alert_type=sos&hours_back=72" \
  -H "Authorization: Bearer $AUTHORITY_TOKEN"
```

### Get Geofence Violations
```bash
curl -X GET "http://localhost:8000/api/heatmap/alerts?alert_type=geofence&hours_back=24" \
  -H "Authorization: Bearer $AUTHORITY_TOKEN"
```

### Get Anomaly Alerts in Specific Area
```bash
curl -X GET "http://localhost:8000/api/heatmap/alerts?alert_type=anomaly&bounds_north=35.7&bounds_south=35.6&bounds_east=139.8&bounds_west=139.6&hours_back=24" \
  -H "Authorization: Bearer $AUTHORITY_TOKEN"
```

### Get High-Severity Alerts in Last 6 Hours
```bash
curl -X GET "http://localhost:8000/api/heatmap/alerts?severity=high&hours_back=6" \
  -H "Authorization: Bearer $AUTHORITY_TOKEN"
```

---

## 👥 Tourist Location Heatmap (Authority)

### Get All Active Tourist Locations
```bash
curl -X GET "http://localhost:8000/api/heatmap/tourists?hours_back=24" \
  -H "Authorization: Bearer $AUTHORITY_TOKEN"
```

### Get High-Risk Tourists (Low Safety Score)
```bash
curl -X GET "http://localhost:8000/api/heatmap/tourists?max_safety_score=50&hours_back=24" \
  -H "Authorization: Bearer $AUTHORITY_TOKEN"
```

### Get Critical Risk Tourists
```bash
curl -X GET "http://localhost:8000/api/heatmap/tourists?max_safety_score=30&hours_back=12" \
  -H "Authorization: Bearer $AUTHORITY_TOKEN"
```

### Get Safe Tourists (High Safety Score)
```bash
curl -X GET "http://localhost:8000/api/heatmap/tourists?min_safety_score=70&hours_back=24" \
  -H "Authorization: Bearer $AUTHORITY_TOKEN"
```

### Get Tourist Locations in Specific Area
```bash
curl -X GET "http://localhost:8000/api/heatmap/tourists?bounds_north=35.7&bounds_south=35.6&bounds_east=139.8&bounds_west=139.6&hours_back=24" \
  -H "Authorization: Bearer $AUTHORITY_TOKEN"
```

### Get Tourist Locations in Last Hour (Real-time)
```bash
curl -X GET "http://localhost:8000/api/heatmap/tourists?hours_back=1" \
  -H "Authorization: Bearer $AUTHORITY_TOKEN"
```

---

## 📱 Tourist-Facing Zone Endpoints

### Get Nearby Zones (for Tourist App)
```bash
curl -X GET "http://localhost:8000/api/zones/nearby?lat=35.6762&lon=139.6503&radius=2000" \
  -H "Authorization: Bearer $TOURIST_TOKEN"
```

### Get All Public Zone Information
```bash
curl -X GET "http://localhost:8000/api/zones/list" \
  -H "Authorization: Bearer $TOURIST_TOKEN"
```

### Get Public Zone Heatmap (Tourist App)
```bash
curl -X GET "http://localhost:8000/api/heatmap/zones/public" \
  -H "Authorization: Bearer $TOURIST_TOKEN"
```

### Get Public Zone Heatmap for Specific Area
```bash
curl -X GET "http://localhost:8000/api/heatmap/zones/public?bounds_north=35.7&bounds_south=35.6&bounds_east=139.8&bounds_west=139.6" \
  -H "Authorization: Bearer $TOURIST_TOKEN"
```

### Get Only Restricted Zones (Tourist App)
```bash
curl -X GET "http://localhost:8000/api/heatmap/zones/public?zone_type=restricted" \
  -H "Authorization: Bearer $TOURIST_TOKEN"
```

---

## 🎯 Geofencing & Real-time Checks

### Check Point Against All Zones
```bash
curl -X POST "http://localhost:8000/api/ai/geofence/check" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOURIST_TOKEN" \
  -d '{
    "lat": 35.6762,
    "lon": 139.6503
  }'
```

### Get Nearby Zones for Geofencing
```bash
curl -X POST "http://localhost:8000/api/ai/geofence/nearby?radius=1000" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOURIST_TOKEN" \
  -d '{
    "lat": 35.6762,
    "lon": 139.6503
  }'
```

---

## 🔄 Real-time Location Updates with Heatmap Integration

### Update Location and Get Safety Analysis
```bash
curl -X POST "http://localhost:8000/api/location/update" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOURIST_TOKEN" \
  -d '{
    "lat": 35.6762,
    "lon": 139.6503,
    "speed": 25.5,
    "altitude": 10.0,
    "accuracy": 5.0,
    "timestamp": "2025-09-30T13:20:00.000000Z"
  }'
```

---

## 📊 Advanced Query Examples

### Monitor High-Risk Areas (Authority Dashboard)
Get comprehensive data for areas with multiple alerts:

```bash
curl -X GET "http://localhost:8000/api/heatmap/data?hours_back=24&include_zones=true&include_alerts=true&include_tourists=true" \
  -H "Authorization: Bearer $AUTHORITY_TOKEN" | jq '.hotspots[] | select(.intensity > 5)'
```

### Get Emergency Response Data
Get critical alerts and nearby zones for emergency response:

```bash
# Get critical alerts
curl -X GET "http://localhost:8000/api/heatmap/alerts?severity=critical&hours_back=6" \
  -H "Authorization: Bearer $AUTHORITY_TOKEN"

# Get all zones for context
curl -X GET "http://localhost:8000/api/heatmap/zones" \
  -H "Authorization: Bearer $AUTHORITY_TOKEN"
```

### Tourist Safety Check
Check if tourist location is safe and get nearby zone information:

```bash
# Check current location against zones
curl -X POST "http://localhost:8000/api/ai/geofence/check" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOURIST_TOKEN" \
  -d '{
    "lat": 35.6762,
    "lon": 139.6503
  }'

# Get nearby zones
curl -X GET "http://localhost:8000/api/zones/nearby?lat=35.6762&lon=139.6503&radius=1000" \
  -H "Authorization: Bearer $TOURIST_TOKEN"
```

---

## 🔔 Response Processing Examples

### Extract High-Risk Tourists
```bash
curl -X GET "http://localhost:8000/api/heatmap/tourists?hours_back=24" \
  -H "Authorization: Bearer $AUTHORITY_TOKEN" | \
  jq '.tourists[] | select(.safety_score < 50) | {id, name, safety_score, location, risk_level}'
```

### Get Zone Coverage Map
```bash
curl -X GET "http://localhost:8000/api/heatmap/zones" \
  -H "Authorization: Bearer $AUTHORITY_TOKEN" | \
  jq '.zones[] | {name, type, center, radius_meters, risk_weight}'
```

### Alert Intensity Analysis
```bash
curl -X GET "http://localhost:8000/api/heatmap/data?hours_back=24" \
  -H "Authorization: Bearer $AUTHORITY_TOKEN" | \
  jq '.hotspots[] | {center, intensity, alert_count, max_severity}'
```

---

## ⚡ Performance Tips

1. **Use bounds filtering** for large datasets:
   ```bash
   ?bounds_north=35.7&bounds_south=35.6&bounds_east=139.8&bounds_west=139.6
   ```

2. **Limit time range** for real-time data:
   ```bash
   ?hours_back=1  # Last hour only
   ```

3. **Filter by specific types** to reduce payload:
   ```bash
   ?zone_type=restricted&alert_type=sos&severity=critical
   ```

4. **Use specific endpoints** instead of comprehensive data:
   - Use `/heatmap/zones` instead of `/heatmap/data` if you only need zones
   - Use `/heatmap/alerts?severity=critical` for emergency monitoring

---

## 🎯 Common Use Cases

### Real-time Emergency Dashboard
```bash
# Get critical alerts in last hour
curl -X GET "http://localhost:8000/api/heatmap/alerts?severity=critical&hours_back=1" \
  -H "Authorization: Bearer $AUTHORITY_TOKEN"

# Get high-risk tourists
curl -X GET "http://localhost:8000/api/heatmap/tourists?max_safety_score=30&hours_back=1" \
  -H "Authorization: Bearer $AUTHORITY_TOKEN"
```

### Tourist Safety App
```bash
# Check current location safety
curl -X POST "http://localhost:8000/api/ai/geofence/check" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOURIST_TOKEN" \
  -d '{"lat": 35.6762, "lon": 139.6503}'

# Get public zone information
curl -X GET "http://localhost:8000/api/heatmap/zones/public" \
  -H "Authorization: Bearer $TOURIST_TOKEN"
```

### Area Risk Assessment
```bash
# Get comprehensive area data
curl -X GET "http://localhost:8000/api/heatmap/data?bounds_north=35.7&bounds_south=35.6&bounds_east=139.8&bounds_west=139.6&hours_back=168" \
  -H "Authorization: Bearer $AUTHORITY_TOKEN"
```

---

**API Version**: 1.0.0  
**Last Updated**: September 30, 2025  
**Status**: ✅ All heatmap endpoints ready for production use  
**Real-time**: ✅ Live data from database with configurable time windows