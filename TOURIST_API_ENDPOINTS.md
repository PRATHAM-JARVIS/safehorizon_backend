# 🏃‍♂️ SafeHorizon Tourist API Endpoints

**Complete API Documentation for Tourist Features**  
**Generated:** October 3, 2025  
**Base URL:** `http://localhost:8000/api`  
**Authentication:** Bearer JWT Token Required (except for registration/login)

---

## 📋 Table of Contents

1. [Authentication Endpoints](#authentication-endpoints)
2. [Trip Management](#trip-management)
3. [Location Tracking](#location-tracking)
4. [Safety & Scoring](#safety--scoring)
5. [Emergency Features](#emergency-features)
6. [E-FIR (Electronic First Information Report)](#e-fir-electronic-first-information-report)
7. [Device Management](#device-management)
8. [Emergency Broadcasts](#emergency-broadcasts)
9. [Zone Information](#zone-information)
10. [Public Endpoints](#public-endpoints)

---

## 🔐 Authentication Endpoints

### 1. Register Tourist
**POST** `/auth/register`

Register a new tourist account.

**Request Body:**
```json
{
  "email": "tourist@example.com",
  "password": "securePassword123",
  "name": "John Doe",
  "phone": "+1234567890",
  "emergency_contact": "Jane Doe",
  "emergency_phone": "+0987654321"
}
```

**Response (201):**
```json
{
  "message": "Tourist registered successfully",
  "user_id": "uuid-string",
  "email": "tourist@example.com"
}
```

### 2. Login Tourist
**POST** `/auth/login`

Authenticate tourist and receive JWT token.

**Request Body:**
```json
{
  "email": "tourist@example.com",
  "password": "securePassword123"
}
```

**Response (200):**
```json
{
  "access_token": "jwt-token-here",
  "token_type": "bearer",
  "user_id": "uuid-string",
  "email": "tourist@example.com",
  "role": "tourist"
}
```

### 3. Get Current User Info
**GET** `/auth/me`

Get current authenticated user information.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "id": "uuid-string",
  "email": "tourist@example.com",
  "name": "John Doe",
  "phone": "+1234567890",
  "safety_score": 85.2,
  "last_seen": "2025-10-03T10:30:00Z"
}
```

---

## 🧳 Trip Management

### 4. Start Trip
**POST** `/trip/start`

Start a new trip.

**Request Body:**
```json
{
  "destination": "New York City",
  "itinerary": "Visit Central Park, Times Square, etc."
}
```

**Response (200):**
```json
{
  "trip_id": 123,
  "destination": "New York City",
  "status": "active",
  "start_date": "2025-10-03T10:30:00Z"
}
```

### 5. End Trip
**POST** `/trip/end`

End the current active trip.

**Response (200):**
```json
{
  "trip_id": 123,
  "status": "completed",
  "end_date": "2025-10-03T18:30:00Z"
}
```

### 6. Get Trip History
**GET** `/trip/history`

Get all past trips for the current user.

**Response (200):**
```json
[
  {
    "id": 123,
    "destination": "New York City",
    "status": "completed",
    "start_date": "2025-10-03T10:30:00Z",
    "end_date": "2025-10-03T18:30:00Z",
    "created_at": "2025-10-03T09:00:00Z"
  }
]
```

---

## 📍 Location Tracking

### 7. Update Location
**POST** `/location/update`

Update current location with comprehensive AI safety analysis.

**Request Body:**
```json
{
  "lat": 40.7589,
  "lon": -73.9851,
  "speed": 5.2,
  "altitude": 10.5,
  "accuracy": 3.0,
  "timestamp": "2025-10-03T10:30:00Z"
}
```

**Response (200):**
```json
{
  "status": "location_updated",
  "action": "created",
  "location_id": 456,
  "is_same_location": false,
  "location_safety_score": 78.5,
  "tourist_safety_score": 82.1,
  "risk_level": "low",
  "lat": 40.7589,
  "lon": -73.9851,
  "timestamp": "2025-10-03T10:30:00Z",
  "ai_analysis": {
    "factors": {
      "nearby_alerts": {
        "score": 85.0,
        "weight": 0.3,
        "contribution": 25.5
      },
      "zone_risk": {
        "score": 90.0,
        "weight": 0.25,
        "contribution": 22.5
      },
      "time_of_day": {
        "score": 75.0,
        "weight": 0.15,
        "contribution": 11.25
      },
      "crowd_density": {
        "score": 80.0,
        "weight": 0.1,
        "contribution": 8.0
      },
      "speed_anomaly": {
        "score": 95.0,
        "weight": 0.1,
        "contribution": 9.5
      },
      "historical_risk": {
        "score": 70.0,
        "weight": 0.1,
        "contribution": 7.0
      }
    },
    "recommendations": [
      "Area appears safe with normal activity patterns",
      "Continue monitoring speed and movement patterns",
      "Stay aware of surroundings"
    ]
  }
}
```

### 8. Get Location History
**GET** `/location/history?limit=100`

Get location history with safety scores.

**Query Parameters:**
- `limit` (optional): Number of records to return (default: 100)

**Response (200):**
```json
[
  {
    "id": 456,
    "lat": 40.7589,
    "lon": -73.9851,
    "speed": 5.2,
    "altitude": 10.5,
    "accuracy": 3.0,
    "timestamp": "2025-10-03T10:30:00Z",
    "safety_score": 78.5,
    "safety_score_updated_at": "2025-10-03T10:30:00Z"
  }
]
```

### 9. Get Location Safety Trend
**GET** `/location/safety-trend?hours_back=24`

Get safety score trend over time.

**Query Parameters:**
- `hours_back` (optional): Hours to look back (default: 24)

**Response (200):**
```json
{
  "hours_back": 24,
  "data_points": 15,
  "trend": [
    {
      "timestamp": "2025-10-03T10:30:00Z",
      "safety_score": 78.5,
      "risk_level": "low",
      "location": {"lat": 40.7589, "lon": -73.9851}
    }
  ],
  "statistics": {
    "average_score": 79.2,
    "min_score": 65.0,
    "max_score": 92.0,
    "current_score": 82.1,
    "score_volatility": 27.0
  }
}
```

### 10. Get Location Safety Analysis
**GET** `/location/safety-analysis`

Get detailed AI safety analysis for current location.

**Response (200):**
```json
{
  "location": {
    "id": 456,
    "lat": 40.7589,
    "lon": -73.9851,
    "timestamp": "2025-10-03T10:30:00Z"
  },
  "safety_score": 78.5,
  "risk_level": "low",
  "factors": {
    "nearby_alerts": {
      "score": 85.0,
      "weight": 0.3,
      "contribution": 25.5
    }
  },
  "recommendations": [
    "Area appears safe with normal activity patterns",
    "Continue monitoring speed and movement patterns"
  ],
  "tourist_profile": {
    "id": "uuid-string",
    "overall_safety_score": 82.1,
    "last_seen": "2025-10-03T10:30:00Z"
  }
}
```

### 11. Get Nearby Risks
**GET** `/location/nearby-risks?radius_km=2.0`

Get nearby safety risks and alerts around current location.

**Query Parameters:**
- `radius_km` (optional): Search radius in kilometers (default: 2.0)

**Response (200):**
```json
{
  "current_location": {
    "lat": 40.7589,
    "lon": -73.9851,
    "safety_score": 78.5,
    "timestamp": "2025-10-03T10:30:00Z"
  },
  "search_radius_km": 2.0,
  "nearby_alerts": [
    {
      "alert_id": 789,
      "type": "anomaly",
      "severity": "medium",
      "title": "Unusual Activity Detected",
      "description": "AI detected unusual movement patterns",
      "distance_km": 1.2,
      "location": {"lat": 40.7500, "lon": -73.9800},
      "timestamp": "2025-10-03T09:15:00Z"
    }
  ],
  "nearby_risky_zones": [
    {
      "zone_id": 101,
      "name": "Construction Area",
      "type": "risky",
      "distance_km": 0.8,
      "radius_km": 0.5,
      "center": {"lat": 40.7550, "lon": -73.9900},
      "is_inside": false
    }
  ],
  "risk_summary": {
    "total_alerts": 1,
    "critical_alerts": 0,
    "high_alerts": 0,
    "risky_zones_nearby": 1,
    "inside_risky_zone": false
  }
}
```

---

## 🛡️ Safety & Scoring

### 12. Get Safety Score
**GET** `/safety/score`

Get current safety score.

**Response (200):**
```json
{
  "safety_score": 82.1,
  "risk_level": "low",
  "last_updated": "2025-10-03T10:30:00Z"
}
```

---

## 🚨 Emergency Features

### 13. Trigger SOS
**POST** `/sos/trigger`

Trigger emergency SOS alert.

**Response (200):**
```json
{
  "status": "sos_triggered",
  "alert_id": 789,
  "notifications_sent": {
    "push_notifications": true,
    "sms_sent": true,
    "emergency_contacts_notified": 1
  },
  "timestamp": "2025-10-03T10:30:00Z"
}
```

---

## 📋 E-FIR (Electronic First Information Report)

### 14. Generate E-FIR
**POST** `/tourist/efir/generate`

Generate E-FIR for tourist-reported incidents.

**Request Body:**
```json
{
  "alert_id": 789,
  "incident_description": "Harassment by unknown individual",
  "incident_type": "harassment",
  "suspect_description": "Male, approximately 30 years old, wearing blue jacket",
  "witness_details": "Two witnesses present",
  "location": "Central Park, near fountain",
  "timestamp": "2025-10-03T10:30:00Z",
  "witnesses": ["Witness 1", "Witness 2"],
  "additional_details": "Incident lasted approximately 5 minutes"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "E-FIR generated and stored successfully",
  "efir_id": 123,
  "fir_number": "EFIR-20251003-T12345678-1696334400",
  "blockchain_tx_id": "0x1234567890abcdef...",
  "timestamp": "2025-10-03T10:30:00Z",
  "verification_url": "/api/blockchain/verify/0x1234567890abcdef...",
  "status": "submitted",
  "alert_id": 789
}
```

### 15. Get My E-FIRs
**GET** `/efir/my-reports?limit=50`

Get all E-FIRs submitted by current tourist.

**Query Parameters:**
- `limit` (optional): Number of records to return (default: 50)

**Response (200):**
```json
{
  "success": true,
  "total": 2,
  "efirs": [
    {
      "efir_id": 123,
      "fir_number": "EFIR-20251003-T12345678-1696334400",
      "incident_type": "harassment",
      "severity": "medium",
      "description": "Harassment by unknown individual",
      "location": {
        "lat": 40.7589,
        "lon": -73.9851,
        "description": "Central Park, near fountain"
      },
      "incident_timestamp": "2025-10-03T10:30:00Z",
      "generated_at": "2025-10-03T10:35:00Z",
      "blockchain_tx_id": "0x1234567890abcdef...",
      "is_verified": false,
      "verification_timestamp": null,
      "witnesses": ["Witness 1", "Witness 2"],
      "status": "pending_verification"
    }
  ],
  "generated_at": "2025-10-03T11:00:00Z"
}
```

### 16. Get E-FIR Details
**GET** `/efir/{efir_id}`

Get detailed information about a specific E-FIR.

**Response (200):**
```json
{
  "success": true,
  "efir": {
    "efir_id": 123,
    "fir_number": "EFIR-20251003-T12345678-1696334400",
    "incident_type": "harassment",
    "severity": "medium",
    "description": "Harassment by unknown individual",
    "location": {
      "lat": 40.7589,
      "lon": -73.9851,
      "description": "Central Park, near fountain"
    },
    "tourist_info": {
      "name": "John Doe",
      "email": "tourist@example.com",
      "phone": "+1234567890"
    },
    "incident_timestamp": "2025-10-03T10:30:00Z",
    "generated_at": "2025-10-03T10:35:00Z",
    "blockchain": {
      "tx_id": "0x1234567890abcdef...",
      "block_hash": "block_1234567890abcdef...",
      "chain_id": "safehorizon-efir-chain"
    },
    "is_verified": false,
    "verification_timestamp": null,
    "witnesses": ["Witness 1", "Witness 2"],
    "additional_details": "Incident lasted approximately 5 minutes",
    "report_source": "tourist",
    "status": "pending_verification"
  }
}
```

---

## 📱 Device Management

### 17. Register Device
**POST** `/device/register`

Register device token for push notifications.

**Request Body:**
```json
{
  "device_token": "fcm-token-here",
  "device_type": "android",
  "device_name": "Samsung Galaxy S21",
  "app_version": "1.0.0"
}
```

**Response (200):**
```json
{
  "status": "success",
  "message": "Device registered successfully",
  "device_token": "fcm-token-here",
  "device_type": "android"
}
```

### 18. Unregister Device
**DELETE** `/device/unregister?device_token=fcm-token-here`

Unregister device (on logout or app uninstall).

**Query Parameters:**
- `device_token`: FCM token to unregister

**Response (200):**
```json
{
  "status": "success",
  "message": "Device unregistered"
}
```

### 19. List Devices
**GET** `/device/list`

List all registered devices for current user.

**Response (200):**
```json
{
  "status": "success",
  "count": 2,
  "devices": [
    {
      "id": 1,
      "device_type": "android",
      "device_name": "Samsung Galaxy S21",
      "app_version": "1.0.0",
      "is_active": true,
      "last_used": "2025-10-03T10:30:00Z",
      "created_at": "2025-10-01T08:00:00Z"
    }
  ]
}
```

---

## 📡 Emergency Broadcasts

### 20. Get Active Broadcasts
**GET** `/broadcasts/active?lat=40.7589&lon=-73.9851`

Get all active emergency broadcasts relevant to tourist's location.

**Query Parameters:**
- `lat` (optional): Current latitude
- `lon` (optional): Current longitude

**Response (200):**
```json
{
  "active_broadcasts": [
    {
      "id": 1,
      "broadcast_id": "BCAST-20251003-103000",
      "broadcast_type": "RADIUS",
      "title": "Emergency Alert",
      "message": "Severe weather warning in your area. Seek shelter immediately.",
      "severity": "HIGH",
      "alert_type": "weather_warning",
      "action_required": "seek_shelter",
      "sent_by": {
        "id": "auth-uuid",
        "name": "Emergency Services",
        "department": "Weather Service"
      },
      "sent_at": "2025-10-03T10:30:00Z",
      "expires_at": "2025-10-03T18:00:00Z",
      "tourists_notified": 150,
      "acknowledgments": 75,
      "is_acknowledged": false,
      "center": {
        "lat": 40.7500,
        "lon": -73.9800
      },
      "radius_km": 5.0,
      "distance_km": 1.2
    }
  ],
  "total": 1,
  "retrieved_at": "2025-10-03T10:45:00Z"
}
```

### 21. Get Broadcast History
**GET** `/broadcasts/history?limit=20&include_expired=true`

Get broadcast history (active + expired broadcasts).

**Query Parameters:**
- `limit` (optional): Number of records to return (default: 20)
- `include_expired` (optional): Include expired broadcasts (default: true)

**Response (200):**
```json
{
  "broadcasts": [
    {
      "id": 1,
      "broadcast_id": "BCAST-20251003-103000",
      "title": "Emergency Alert",
      "message": "Severe weather warning in your area.",
      "severity": "HIGH",
      "broadcast_type": "RADIUS",
      "sent_at": "2025-10-03T10:30:00Z",
      "expires_at": "2025-10-03T18:00:00Z",
      "is_active": true,
      "is_acknowledged": false
    }
  ],
  "total": 1,
  "retrieved_at": "2025-10-03T10:45:00Z"
}
```

### 22. Acknowledge Broadcast
**POST** `/broadcasts/{broadcast_id}/acknowledge`

Acknowledge a broadcast notification.

**Request Body:**
```json
{
  "status": "safe",
  "notes": "I am in a safe location",
  "lat": 40.7589,
  "lon": -73.9851
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Broadcast acknowledged successfully",
  "acknowledgment_id": 123,
  "broadcast_id": "BCAST-20251003-103000",
  "status": "safe",
  "acknowledged_at": "2025-10-03T10:45:00Z"
}
```

---

## 🗺️ Zone Information

### 23. List Zones
**GET** `/zones/list`

Get list of all safety zones.

**Response (200):**
```json
[
  {
    "id": 101,
    "name": "Central Park Safe Zone",
    "type": "safe",
    "center": {
      "lat": 40.7589,
      "lon": -73.9851
    },
    "radius_meters": 1000,
    "description": "Well-patrolled tourist area"
  }
]
```

### 24. Get Nearby Zones
**GET** `/zones/nearby?lat=40.7589&lon=-73.9851&radius_km=5`

Get zones near tourist's current location.

**Query Parameters:**
- `lat`: Current latitude
- `lon`: Current longitude
- `radius` or `radius_km` (optional): Search radius (default: 5000m or 5km)

**Response (200):**
```json
{
  "nearby_zones": [
    {
      "id": 101,
      "name": "Central Park Safe Zone",
      "type": "safe",
      "center": {"lat": 40.7589, "lon": -73.9851},
      "radius_meters": 1000,
      "description": "Well-patrolled tourist area",
      "distance_meters": 250.5,
      "coordinates": [[lon, lat], [lon, lat]]
    }
  ],
  "center": {"lat": 40.7589, "lon": -73.9851},
  "radius_meters": 5000,
  "total": 1,
  "generated_at": "2025-10-03T10:45:00Z"
}
```

### 25. Get Public Zone Heatmap
**GET** `/heatmap/zones/public?zone_type=all`

Get public zone heatmap data for tourist app.

**Query Parameters:**
- `bounds_north`, `bounds_south`, `bounds_east`, `bounds_west` (optional): Bounding box
- `zone_type` (optional): Filter by zone type ('safe', 'risky', 'restricted', 'all')

**Response (200):**
```json
{
  "zones": [
    {
      "id": 101,
      "name": "Central Park Safe Zone",
      "type": "safe",
      "center": {"lat": 40.7589, "lon": -73.9851},
      "radius_meters": 1000,
      "description": "Well-patrolled tourist area",
      "risk_level": "safe",
      "safety_recommendation": "Safe area - normal precautions apply"
    }
  ],
  "total": 1,
  "filter": {
    "zone_type": "all",
    "bounds": null
  },
  "generated_at": "2025-10-03T10:45:00Z",
  "note": "Public zone information for tourist safety awareness"
}
```

---

## 🌐 Public Endpoints

### 26. Debug User Role
**GET** `/debug/role`

Debug endpoint to check user role and permissions.

**Response (200):**
```json
{
  "user_id": "uuid-string",
  "email": "tourist@example.com",
  "role": "tourist",
  "is_tourist": true,
  "is_authority": false,
  "is_admin": false
}
```

---

## 🔗 Common Response Codes

- **200 OK**: Request successful
- **201 Created**: Resource created successfully
- **400 Bad Request**: Invalid request data
- **401 Unauthorized**: Authentication required or invalid token
- **403 Forbidden**: Access denied for current role
- **404 Not Found**: Resource not found
- **422 Unprocessable Entity**: Validation error
- **500 Internal Server Error**: Server error

---

## 🛡️ Authentication

All endpoints (except registration and login) require a JWT token:

```
Authorization: Bearer <your-jwt-token>
```

Get the token from the login endpoint and include it in all subsequent requests.

---

## 📊 Rate Limiting

- Location updates: Max 10 requests per minute
- E-FIR generation: Max 5 requests per hour
- SOS trigger: Max 3 requests per hour

---

## 🔄 Real-Time Features

The system supports real-time communication via WebSocket for:
- Safety alerts
- Emergency broadcasts
- Location updates
- System notifications

Connect to: `ws://localhost:8000/api/tourist/ws?token=<your-jwt-token>`

---

**📱 Mobile App Integration Ready**  
All endpoints are optimized for mobile app integration with proper error handling, validation, and response structures.