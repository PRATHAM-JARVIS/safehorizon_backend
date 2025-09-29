# 🚀 SafeHorizon API Endpoints Documentation

**Complete API Reference for SafeHorizon Tourist Safety Platform**

Base URL: `http://localhost:8000/api` (Development) | `https://your-domain.com/api` (Production)

---

## 📋 Table of Contents

- [Authentication](#authentication)
- [Tourist Mobile App Endpoints](#tourist-mobile-app-endpoints)
- [Authority Dashboard Endpoints](#authority-dashboard-endpoints)
- [AI Services Endpoints](#ai-services-endpoints)
- [Notification Endpoints](#notification-endpoints)
- [Admin Endpoints](#admin-endpoints)
- [WebSocket Endpoints](#websocket-endpoints)
- [Response Formats](#response-formats)
- [Error Handling](#error-handling)

---

## 🔐 Authentication

All authenticated endpoints require a Bearer token in the Authorization header:
```
Authorization: Bearer <access_token>
```

### User Roles Hierarchy
- **Tourist**: Basic user access
- **Authority**: Police dashboard access + Tourist access
- **Admin**: Full system access + Authority + Tourist access

---

## 👤 Tourist Mobile App Endpoints

### Authentication

#### `POST /auth/register` - Register Tourist
Register a new tourist user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "name": "John Doe",
  "phone": "+1234567890",
  "emergency_contact": "Jane Doe",
  "emergency_phone": "+0987654321"
}
```

**Response (200):**
```json
{
  "message": "Tourist registered successfully",
  "user_id": "abc123...",
  "email": "user@example.com"
}
```

#### `POST /auth/login` - Tourist Login
Authenticate tourist user and get access token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user_id": "abc123...",
  "email": "user@example.com",
  "role": "tourist"
}
```

#### `GET /auth/me` - Get Current User Info
Get current authenticated user information.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "id": "abc123...",
  "email": "user@example.com",
  "name": "John Doe",
  "phone": "+1234567890",
  "safety_score": 85,
  "last_seen": "2025-09-29T10:24:51.832307+00:00"
}
```

### Trip Management

#### `POST /trip/start` - Start Trip
Start a new tracking trip.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "destination": "Tokyo, Japan",
  "itinerary": "Visit temples, shopping districts"
}
```

**Response (200):**
```json
{
  "trip_id": 10,
  "destination": "Tokyo, Japan",
  "status": "active",
  "start_date": "2025-09-29T04:54:51.581963+00:00"
}
```

#### `POST /trip/end` - End Current Trip
End the currently active trip.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "trip_id": 10,
  "status": "completed",
  "end_date": "2025-09-29T10:24:51.711747+00:00"
}
```

#### `GET /trip/history` - Get Trip History
Get user's trip history.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
[
  {
    "id": 10,
    "destination": "Tokyo, Japan",
    "status": "completed",
    "start_date": "2025-09-29T04:54:51.581963+00:00",
    "end_date": "2025-09-29T10:24:51.711747+00:00",
    "created_at": "2025-09-29T04:54:51.581963+00:00"
  }
]
```

### Location Tracking

#### `POST /location/update` - Update Location
Send real-time GPS location update with AI safety analysis.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "lat": 35.6762,
  "lon": 139.6503,
  "speed": 30.5,
  "altitude": 15.0,
  "accuracy": 5.0,
  "timestamp": "2025-09-29T10:24:51.720256+00:00"
}
```

**Response (200):**
```json
{
  "status": "location_updated",
  "location_id": 406,
  "safety_score": 85,
  "risk_level": "low",
  "lat": 35.6762,
  "lon": 139.6503,
  "timestamp": "2025-09-29T10:24:51.720256+00:00"
}
```

#### `GET /location/history` - Get Location History
Get user's location history.

**Headers:** `Authorization: Bearer <token>`
**Query Parameters:**
- `limit` (optional): Number of locations to return (default: 100)

**Response (200):**
```json
[
  {
    "id": 406,
    "lat": 35.6762,
    "lon": 139.6503,
    "speed": 30.5,
    "altitude": 15.0,
    "accuracy": 5.0,
    "timestamp": "2025-09-29T10:24:51.720256+00:00"
  }
]
```

### Safety & Emergency

#### `GET /safety/score` - Get Safety Score
Get current AI-computed safety score.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "safety_score": 85,
  "risk_level": "low",
  "last_updated": "2025-09-29T04:54:51.832307+00:00"
}
```

#### `POST /sos/trigger` - Emergency SOS
Trigger emergency SOS alert.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "status": "sos_triggered",
  "alert_id": 123,
  "timestamp": "2025-09-29T10:24:51.720256+00:00",
  "emergency_contacts_notified": true,
  "authorities_notified": true
}
```

---

## 👮 Authority Dashboard Endpoints

### Authentication

#### `POST /auth/register-authority` - Register Authority
Register a new police authority user.

**Request Body:**
```json
{
  "email": "officer@police.com",
  "password": "police123",
  "name": "Officer Smith",
  "badge_number": "12345",
  "department": "City Police Department",
  "rank": "Officer"
}
```

**Response (200):**
```json
{
  "message": "Authority registered successfully",
  "user_id": "def456...",
  "badge_number": "12345",
  "department": "City Police Department"
}
```

#### `POST /auth/login-authority` - Authority Login
Authenticate authority user.

**Request Body:**
```json
{
  "email": "officer@police.com",
  "password": "police123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user_id": "def456...",
  "email": "officer@police.com",
  "role": "authority"
}
```

### Tourist Monitoring

#### `GET /tourists/active` - Get Active Tourists
Get list of tourists active in the last 24 hours.

**Headers:** `Authorization: Bearer <authority_token>`

**Response (200):**
```json
[
  {
    "id": "abc123...",
    "name": "John Doe",
    "email": "user@example.com",
    "safety_score": 85,
    "last_location": {
      "lat": 35.6762,
      "lon": 139.6503
    },
    "last_seen": "2025-09-29T04:54:51.832307+00:00"
  }
]
```

#### `GET /tourist/{tourist_id}/track` - Track Specific Tourist
Get detailed tracking information for a specific tourist.

**Headers:** `Authorization: Bearer <authority_token>`

**Response (200):**
```json
{
  "tourist": {
    "id": "abc123...",
    "name": "John Doe",
    "email": "user@example.com",
    "phone": "+1234567890",
    "safety_score": 85,
    "last_seen": "2025-09-29T04:54:51.832307+00:00"
  },
  "locations": [
    {
      "id": 406,
      "lat": 35.6762,
      "lon": 139.6503,
      "speed": 30.5,
      "altitude": 15.0,
      "timestamp": "2025-09-29T10:24:51.720256+00:00"
    }
  ],
  "recent_alerts": [
    {
      "id": 123,
      "type": "geofence",
      "severity": "medium",
      "title": "Entered restricted zone",
      "description": "Tourist entered restricted area",
      "is_acknowledged": false,
      "created_at": "2025-09-29T10:24:51.720256+00:00"
    }
  ]
}
```

#### `GET /tourist/{tourist_id}/alerts` - Get Tourist Alerts
Get alerts for a specific tourist.

**Headers:** `Authorization: Bearer <authority_token>`

**Response (200):**
```json
[
  {
    "id": 123,
    "type": "sos",
    "severity": "critical",
    "title": "Emergency SOS Alert",
    "description": "Emergency SOS triggered by John Doe",
    "is_acknowledged": false,
    "is_resolved": false,
    "created_at": "2025-09-29T10:24:51.720256+00:00"
  }
]
```

### Alert Management

#### `GET /alerts/recent` - Get Recent Alerts
Get recent system alerts.

**Headers:** `Authorization: Bearer <authority_token>`
**Query Parameters:**
- `limit` (optional): Number of alerts (default: 50)
- `severity` (optional): Filter by severity (low, medium, high, critical)

**Response (200):**
```json
[
  {
    "id": 123,
    "tourist_id": "abc123...",
    "tourist_name": "John Doe",
    "type": "sos",
    "severity": "critical",
    "title": "Emergency SOS Alert",
    "description": "Emergency SOS triggered by John Doe",
    "location": {
      "lat": 35.6762,
      "lon": 139.6503
    },
    "is_acknowledged": false,
    "is_resolved": false,
    "created_at": "2025-09-29T10:24:51.720256+00:00"
  }
]
```

#### `POST /incident/acknowledge` - Acknowledge Alert
Acknowledge an alert/incident.

**Headers:** `Authorization: Bearer <authority_token>`

**Request Body:**
```json
{
  "alert_id": 123,
  "notes": "Responding to location"
}
```

**Response (200):**
```json
{
  "status": "acknowledged",
  "alert_id": 123,
  "acknowledged_by": "Officer Smith",
  "acknowledged_at": "2025-09-29T10:24:51.720256+00:00"
}
```

#### `POST /incident/close` - Close Incident
Close/resolve an incident.

**Headers:** `Authorization: Bearer <authority_token>`

**Request Body:**
```json
{
  "alert_id": 123,
  "notes": "Incident resolved, tourist safe"
}
```

**Response (200):**
```json
{
  "status": "closed",
  "alert_id": 123,
  "closed_by": "Officer Smith",
  "closed_at": "2025-09-29T10:24:51.720256+00:00"
}
```

### Zone Management

#### `GET /zones/list` - List All Zones
Get all restricted zones.

**Headers:** `Authorization: Bearer <authority_token>`

**Response (200):**
```json
[
  {
    "id": 7,
    "name": "Restricted Area Downtown",
    "type": "restricted",
    "description": "High-crime area",
    "center": {
      "lat": 35.6762,
      "lon": 139.6503
    },
    "radius_meters": 1000,
    "is_active": true,
    "created_at": "2025-09-29T10:24:51.720256+00:00"
  }
]
```

#### `POST /zones/create` - Create Zone
Create a new restricted zone.

**Headers:** `Authorization: Bearer <authority_token>`

**Request Body:**
```json
{
  "name": "New Restricted Zone",
  "description": "Temporary restricted area",
  "zone_type": "restricted",
  "coordinates": [
    [139.6503, 35.6762],
    [139.6603, 35.6762],
    [139.6603, 35.6862],
    [139.6503, 35.6862]
  ]
}
```

**Response (200):**
```json
{
  "id": 8,
  "name": "New Restricted Zone",
  "type": "restricted",
  "description": "Temporary restricted area",
  "center": {
    "lat": 35.681200000000004,
    "lon": 139.6553
  },
  "radius_meters": 1000,
  "created_at": "2025-09-29T10:24:30.296553+00:00"
}
```

#### `DELETE /zones/{zone_id}` - Delete Zone
Delete a restricted zone.

**Headers:** `Authorization: Bearer <authority_token>`

**Response (200):**
```json
{
  "status": "deleted",
  "zone_id": 8,
  "message": "Zone deleted successfully"
}
```

#### `POST /efir/generate` - Generate E-FIR
Generate electronic First Information Report.

**Headers:** `Authorization: Bearer <authority_token>`

**Request Body:**
```json
{
  "alert_id": 123,
  "incident_details": "Tourist found safe after SOS alert",
  "location": "Downtown Tokyo area"
}
```

**Response (200):**
```json
{
  "efir_id": "EFIR2025092901",
  "blockchain_hash": "0x1234567890abcdef...",
  "status": "generated",
  "created_at": "2025-09-29T10:24:51.720256+00:00"
}
```

---

## 🤖 AI Services Endpoints

### Geofencing

#### `POST /ai/geofence/check` - Check Point in Zones
Check if coordinates are within restricted zones.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "lat": 35.6762,
  "lon": 139.6503
}
```

**Response (200):**
```json
{
  "inside_restricted": true,
  "zones": [
    {
      "id": 7,
      "name": "Restricted Area Downtown",
      "type": "restricted",
      "description": "High-crime area"
    }
  ],
  "risk_level": "restricted",
  "zone_count": 1
}
```

#### `POST /ai/geofence/nearby` - Get Nearby Zones
Get zones within specified radius.

**Headers:** `Authorization: Bearer <token>`
**Query Parameters:**
- `radius` (optional): Radius in meters (default: 1000)

**Request Body:**
```json
{
  "lat": 35.6762,
  "lon": 139.6503
}
```

**Response (200):**
```json
{
  "nearby_zones": [
    {
      "id": 7,
      "name": "Restricted Area Downtown",
      "type": "restricted",
      "description": "High-crime area",
      "distance_meters": 250.75
    }
  ],
  "radius_meters": 1000,
  "center": {
    "lat": 35.6762,
    "lon": 139.6503
  }
}
```

### Anomaly Detection

#### `POST /ai/anomaly/point` - Single Point Anomaly Check
Score single location point for anomaly detection.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "lat": 35.6762,
  "lon": 139.6503,
  "speed": 80.0,
  "timestamp": "2025-09-29T10:24:51.720256+00:00"
}
```

**Response (200):**
```json
{
  "anomaly_score": 0.75,
  "risk_level": "high",
  "location": {
    "lat": 35.6762,
    "lon": 139.6503
  },
  "timestamp": "2025-09-29T10:24:52.065912+00:00"
}
```

#### `POST /ai/anomaly/sequence` - Sequence Anomaly Check
Score sequence of locations for pattern anomalies.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "points": [
    {
      "lat": 35.6762,
      "lon": 139.6503,
      "speed": 30.0,
      "timestamp": "2025-09-29T10:20:00.000000+00:00"
    },
    {
      "lat": 35.6772,
      "lon": 139.6513,
      "speed": 80.0,
      "timestamp": "2025-09-29T10:21:00.000000+00:00"
    }
  ]
}
```

**Response (200):**
```json
{
  "sequence_anomaly_score": 0.85,
  "risk_level": "high",
  "analysis": "Unusual speed pattern detected",
  "timestamp": "2025-09-29T10:24:52.065912+00:00"
}
```

### Safety Scoring

#### `POST /ai/score/compute` - Compute Safety Score
Compute comprehensive safety score.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "lat": 35.6762,
  "lon": 139.6503,
  "location_history": [
    {
      "latitude": 35.6762,
      "longitude": 139.6503,
      "speed": 30,
      "timestamp": "2025-09-29T10:20:00.000000+00:00"
    }
  ],
  "current_location_data": {
    "latitude": 35.6762,
    "longitude": 139.6503,
    "speed": 40,
    "timestamp": "2025-09-29T10:24:00.000000+00:00"
  },
  "manual_adjustment": 0
}
```

**Response (200):**
```json
{
  "safety_score": 75,
  "risk_level": "low",
  "components": {
    "geofence_risk": 0.2,
    "anomaly_risk": 0.1,
    "sequence_risk": 0.0,
    "manual_adjustment": 0.0
  },
  "timestamp": "2025-09-29T10:24:52.065912+00:00"
}
```

---

## 🔔 Notification Endpoints

#### `POST /notify/push` - Send Push Notification
Send Firebase push notification.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "tourist_id": "abc123...",
  "title": "Safety Alert",
  "message": "You have entered a restricted area",
  "data": {
    "alert_type": "geofence",
    "severity": "medium"
  }
}
```

**Response (200):**
```json
{
  "status": "sent",
  "notification_id": "notif_123",
  "timestamp": "2025-09-29T10:24:52.065912+00:00"
}
```

#### `POST /notify/sms` - Send SMS Alert
Send Twilio SMS alert.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "phone": "+1234567890",
  "message": "Emergency: Your family member has triggered an SOS alert"
}
```

**Response (200):**
```json
{
  "status": "sent",
  "sms_id": "sms_123",
  "to": "+1234567890",
  "timestamp": "2025-09-29T10:24:52.065912+00:00"
}
```

#### `POST /notify/broadcast` - Broadcast Notification
Broadcast notification to multiple channels.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "channels": ["push", "sms", "email"],
  "tourist_id": "abc123...",
  "title": "Emergency Alert",
  "message": "Critical safety alert",
  "priority": "high"
}
```

**Response (200):**
```json
{
  "status": "broadcast_queued",
  "channels_notified": 3,
  "broadcast_id": "broadcast_123",
  "timestamp": "2025-09-29T10:24:52.065912+00:00"
}
```

#### `GET /notify/history` - Get Notification History
Get notification history for user.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
[
  {
    "id": "notif_123",
    "type": "push",
    "title": "Safety Alert",
    "message": "You have entered a restricted area",
    "status": "delivered",
    "created_at": "2025-09-29T10:24:52.065912+00:00"
  }
]
```

---

## ⚙️ Admin Endpoints

#### `GET /system/status` - System Status
Get system health and status.

**Headers:** `Authorization: Bearer <admin_token>`

**Response (200):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": "72h 15m 30s",
  "active_users": 156,
  "database_status": "connected",
  "redis_status": "connected",
  "ai_models_loaded": true,
  "last_updated": "2025-09-29T10:24:52.065912+00:00"
}
```

#### `POST /system/retrain-model` - Retrain AI Models
Trigger AI model retraining.

**Headers:** `Authorization: Bearer <admin_token>`

**Request Body:**
```json
{
  "model_types": ["anomaly", "sequence"],
  "data_window_days": 30
}
```

**Response (200):**
```json
{
  "status": "retraining_started",
  "job_id": "retrain_123",
  "estimated_completion": "2025-09-29T11:24:52.065912+00:00",
  "models": ["anomaly", "sequence"]
}
```

#### `GET /users/list` - List Users
Get list of system users.

**Headers:** `Authorization: Bearer <admin_token>`
**Query Parameters:**
- `role` (optional): Filter by role (tourist, authority, admin)
- `limit` (optional): Number of users (default: 100)

**Response (200):**
```json
[
  {
    "id": "abc123...",
    "email": "user@example.com",
    "name": "John Doe",
    "role": "tourist",
    "is_active": true,
    "last_seen": "2025-09-29T04:54:51.832307+00:00",
    "created_at": "2025-09-29T04:54:51.832307+00:00"
  }
]
```

#### `PUT /users/{user_id}/suspend` - Suspend User
Suspend or activate user account.

**Headers:** `Authorization: Bearer <admin_token>`

**Request Body:**
```json
{
  "is_active": false,
  "reason": "Suspicious activity detected"
}
```

**Response (200):**
```json
{
  "status": "suspended",
  "user_id": "abc123...",
  "is_active": false,
  "updated_at": "2025-09-29T10:24:52.065912+00:00"
}
```

---

## 🌐 WebSocket Endpoints

### Real-time Alert Subscription

#### `WS /alerts/subscribe` - Subscribe to Real-time Alerts
WebSocket connection for real-time alerts (Authority Dashboard).

**Connection URL:** `ws://localhost:8000/api/alerts/subscribe`
**Headers:** `Authorization: Bearer <authority_token>`

**Message Format (Received):**
```json
{
  "type": "safety_alert",
  "alert_id": 123,
  "tourist_id": "abc123...",
  "severity": "high",
  "safety_score": 45,
  "location": {
    "lat": 35.6762,
    "lon": 139.6503
  },
  "timestamp": "2025-09-29T10:24:52.065912+00:00"
}
```

**Connection Management:**
```javascript
const ws = new WebSocket('ws://localhost:8000/api/alerts/subscribe', [], {
  headers: {
    'Authorization': 'Bearer ' + authToken
  }
});

ws.onmessage = (event) => {
  const alertData = JSON.parse(event.data);
  console.log('New alert:', alertData);
};
```

---

## 📊 Response Formats

### Success Response
```json
{
  "status": "success",
  "data": { ... },
  "message": "Operation completed successfully",
  "timestamp": "2025-09-29T10:24:52.065912+00:00"
}
```

### Error Response
```json
{
  "detail": "Error description",
  "error_code": "VALIDATION_ERROR",
  "timestamp": "2025-09-29T10:24:52.065912+00:00"
}
```

### Pagination (where applicable)
```json
{
  "items": [ ... ],
  "total": 156,
  "page": 1,
  "per_page": 50,
  "total_pages": 4
}
```

---

## ❌ Error Handling

### HTTP Status Codes
- `200` - Success
- `201` - Created
- `400` - Bad Request (validation error)
- `401` - Unauthorized (invalid/missing token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `422` - Unprocessable Entity
- `500` - Internal Server Error

### Common Error Messages
```json
{
  "detail": "Invalid authentication credentials"
}
```

```json
{
  "detail": "Tourist access required"
}
```

```json
{
  "detail": "Registration failed: User already exists"
}
```

---

## 🔧 SDK & Integration Examples

### JavaScript/TypeScript Example
```typescript
const API_BASE = 'http://localhost:8000/api';
let authToken = '';

// Login
const login = async (email: string, password: string) => {
  const response = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  
  const data = await response.json();
  if (response.ok) {
    authToken = data.access_token;
    return data;
  }
  throw new Error(data.detail);
};

// Update Location
const updateLocation = async (lat: number, lon: number) => {
  const response = await fetch(`${API_BASE}/location/update`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${authToken}`
    },
    body: JSON.stringify({ 
      lat, lon, 
      timestamp: new Date().toISOString() 
    })
  });
  
  return response.json();
};
```

### Python Example
```python
import httpx
import asyncio

class SafeHorizonAPI:
    def __init__(self, base_url: str = "http://localhost:8000/api"):
        self.base_url = base_url
        self.token = None
        
    async def login(self, email: str, password: str):
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.base_url}/auth/login", 
                json={"email": email, "password": password})
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                return data
            raise Exception(response.json()["detail"])
    
    def get_headers(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}
    
    async def update_location(self, lat: float, lon: float):
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.base_url}/location/update",
                json={"lat": lat, "lon": lon},
                headers=self.get_headers())
            return response.json()

# Usage
api = SafeHorizonAPI()
await api.login("user@example.com", "password123")
result = await api.update_location(35.6762, 139.6503)
```

### cURL Examples
```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'

# Update Location (with token)
curl -X POST http://localhost:8000/api/location/update \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"lat":35.6762,"lon":139.6503}'

# Get Safety Score
curl -X GET http://localhost:8000/api/safety/score \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🎯 Quick Start Checklist

1. **Server Setup**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

2. **Test Health Endpoint**
   ```bash
   curl http://localhost:8000/health
   ```

3. **Register & Login User**
   ```bash
   # Register
   curl -X POST http://localhost:8000/api/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"test123"}'
   
   # Login
   curl -X POST http://localhost:8000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"test123"}'
   ```

4. **Start Using API**
   - Store the `access_token` from login response
   - Include token in all authenticated requests
   - Check endpoint documentation above for request/response formats

---

## 📞 Support & Contact

**Development Server:** `http://localhost:8000`  
**API Documentation:** `http://localhost:8000/docs` (Swagger UI)  
**Health Check:** `http://localhost:8000/health`

For integration support or questions, refer to the test scripts:
- `test_api_endpoints.py` - Complete API testing examples
- `test_curl_endpoints.py` - Simple cURL-based examples
- `TESTING_README.md` - Testing documentation

---

**Last Updated:** September 29, 2025  
**API Version:** 1.0.0  
**Status:** ✅ All endpoints tested and operational