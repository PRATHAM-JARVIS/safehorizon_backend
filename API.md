# 📘 SafeHorizon API Documentation for Frontend Developers

**Complete API reference for integrating SafeHorizon tourist safety platform**

---

## 📋 Table of Contents

1. [Getting Started](#-getting-started)
2. [Authentication](#-authentication)
3. [Tourist API](#-tourist-api)
4. [Authority API](#-authority-api)
5. [Admin API](#-admin-api)
6. [WebSocket Real-time Alerts](#-websocket-real-time-alerts)
7. [Error Handling](#-error-handling)
8. [Code Examples](#-code-examples)

---

## 🚀 Getting Started

### Base URL
```
Development: http://localhost:8000
Production:  https://api.safehorizon.com
```

### API Prefix
All endpoints use the `/api` prefix:
```
http://localhost:8000/api/auth/login
```

### Content Type
All POST/PUT requests must use JSON:
```
Content-Type: application/json
```

### Authentication
Most endpoints require JWT token in Authorization header:
```
Authorization: Bearer YOUR_JWT_TOKEN
```

---

## 🔐 Authentication

### 1. Register Tourist

**Endpoint:** `POST /api/auth/register`

**Description:** Create a new tourist account

**Request Body:**
```json
{
  "email": "tourist@example.com",
  "password": "securePassword123",
  "name": "John Doe",
  "phone": "+1234567890",
  "emergency_contact": "+0987654321"
}
```

**Response:** `200 OK`
```json
{
  "message": "Registration successful",
  "user": {
    "id": "abc123",
    "email": "tourist@example.com",
    "name": "John Doe",
    "role": "tourist"
  }
}
```

**JavaScript Example:**
```javascript
async function registerTourist(email, password, name, phone, emergencyContact) {
  const response = await fetch('http://localhost:8000/api/auth/register', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      email,
      password,
      name,
      phone,
      emergency_contact: emergencyContact
    })
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail);
  }
  
  return await response.json();
}
```

---

### 2. Login Tourist

**Endpoint:** `POST /api/auth/login`

**Description:** Authenticate and get JWT token

**Request Body:**
```json
{
  "email": "tourist@example.com",
  "password": "securePassword123"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "abc123",
    "email": "tourist@example.com",
    "name": "John Doe",
    "role": "tourist"
  }
}
```

**JavaScript Example:**
```javascript
async function loginTourist(email, password) {
  const response = await fetch('http://localhost:8000/api/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ email, password })
  });
  
  if (!response.ok) {
    throw new Error('Login failed');
  }
  
  const data = await response.json();
  
  // Store token for future requests
  localStorage.setItem('auth_token', data.access_token);
  localStorage.setItem('user', JSON.stringify(data.user));
  
  return data;
}
```

---

### 3. Register Authority (Police)

**Endpoint:** `POST /api/auth/register-authority`

**Description:** Create a police/authority account

**Request Body:**
```json
{
  "email": "officer@police.gov",
  "password": "securePassword123",
  "name": "Officer Smith",
  "badge_number": "PD-12345",
  "department": "Central Police Station",
  "phone": "+1234567890"
}
```

**Response:** `200 OK`
```json
{
  "message": "Authority registration successful",
  "authority": {
    "id": "xyz789",
    "email": "officer@police.gov",
    "name": "Officer Smith",
    "badge_number": "PD-12345",
    "role": "authority"
  }
}
```

---

### 4. Login Authority

**Endpoint:** `POST /api/auth/login-authority`

**Description:** Authenticate police officer

**Request Body:**
```json
{
  "email": "officer@police.gov",
  "password": "securePassword123"
}
```

**Response:** Same as tourist login with `role: "authority"`

---

### 5. Get Current User

**Endpoint:** `GET /api/auth/me`

**Description:** Get authenticated user details

**Headers:**
```
Authorization: Bearer YOUR_JWT_TOKEN
```

**Response:** `200 OK`
```json
{
  "id": "abc123",
  "email": "tourist@example.com",
  "name": "John Doe",
  "role": "tourist",
  "phone": "+1234567890",
  "safety_score": 85.5,
  "created_at": "2025-10-01T10:00:00"
}
```

**JavaScript Example:**
```javascript
async function getCurrentUser() {
  const token = localStorage.getItem('auth_token');
  
  const response = await fetch('http://localhost:8000/api/auth/me', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  if (!response.ok) {
    throw new Error('Not authenticated');
  }
  
  return await response.json();
}
```

---

## 🧳 Tourist API

### 1. Start Trip

**Endpoint:** `POST /api/trip/start`

**Description:** Begin tracking a tourist trip

**Headers:**
```
Authorization: Bearer YOUR_JWT_TOKEN
```

**Request Body:**
```json
{
  "destination": "Taj Mahal, Agra",
  "expected_duration_hours": 6,
  "itinerary": "Visit Taj Mahal, Agra Fort, local markets"
}
```

**Response:** `200 OK`
```json
{
  "message": "Trip started successfully",
  "trip": {
    "id": "abc123",
    "tourist_id": "xyz789",
    "destination": "Taj Mahal, Agra",
    "start_time": "2025-10-01T10:00:00",
    "status": "active",
    "expected_end_time": "2025-10-01T16:00:00"
  }
}
```

---

### 2. End Trip

**Endpoint:** `POST /api/trip/end`

**Description:** End the current trip

**Headers:**
```
Authorization: Bearer YOUR_JWT_TOKEN
```

**Response:** `200 OK`
```json
{
  "message": "Trip ended successfully",
  "trip": {
    "id": "abc123",
    "end_time": "2025-10-01T15:30:00",
    "status": "completed",
    "duration_hours": 5.5
  }
}
```

---

### 3. Update Location

**Endpoint:** `POST /api/location/update`

**Description:** Send current GPS location (called every 30-60 seconds while tracking)

**Headers:**
```
Authorization: Bearer YOUR_JWT_TOKEN
```

**Request Body:**
```json
{
  "latitude": 27.1751,
  "longitude": 78.0421,
  "accuracy": 10.5,
  "altitude": 171.0,
  "speed": 5.2,
  "heading": 180.0
}
```

**Response:** `200 OK`
```json
{
  "message": "Location updated successfully",
  "location_id": "loc123",
  "safety_score": 87.5,
  "alerts": [],
  "in_restricted_zone": false
}
```

**JavaScript Example (Mobile App):**
```javascript
async function updateLocation() {
  if (!navigator.geolocation) {
    console.error('Geolocation not supported');
    return;
  }
  
  navigator.geolocation.getCurrentPosition(async (position) => {
    const token = localStorage.getItem('auth_token');
    
    const response = await fetch('http://localhost:8000/api/location/update', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
        accuracy: position.coords.accuracy,
        altitude: position.coords.altitude,
        speed: position.coords.speed,
        heading: position.coords.heading
      })
    });
    
    const data = await response.json();
    
    // Update UI with safety score
    updateSafetyScore(data.safety_score);
    
    // Show alerts if any
    if (data.alerts && data.alerts.length > 0) {
      showAlerts(data.alerts);
    }
  });
}

// Call every 30 seconds
setInterval(updateLocation, 30000);
```

---

### 4. Get Location History

**Endpoint:** `GET /api/location/history`

**Description:** Retrieve location tracking history

**Headers:**
```
Authorization: Bearer YOUR_JWT_TOKEN
```

**Query Parameters:**
- `limit` (optional): Number of records (default: 100)
- `offset` (optional): Pagination offset (default: 0)

**Request:**
```
GET /api/location/history?limit=50&offset=0
```

**Response:** `200 OK`
```json
{
  "total": 150,
  "locations": [
    {
      "id": "loc123",
      "latitude": 27.1751,
      "longitude": 78.0421,
      "timestamp": "2025-10-01T10:30:00",
      "speed": 5.2,
      "safety_score": 87.5
    },
    {
      "id": "loc124",
      "latitude": 27.1755,
      "longitude": 78.0425,
      "timestamp": "2025-10-01T10:31:00",
      "speed": 4.8,
      "safety_score": 88.0
    }
  ]
}
```

---

### 5. Get Trip History

**Endpoint:** `GET /api/trip/history`

**Description:** Get all past trips

**Headers:**
```
Authorization: Bearer YOUR_JWT_TOKEN
```

**Response:** `200 OK`
```json
{
  "trips": [
    {
      "id": "trip123",
      "destination": "Taj Mahal, Agra",
      "start_time": "2025-10-01T10:00:00",
      "end_time": "2025-10-01T15:30:00",
      "status": "completed",
      "duration_hours": 5.5,
      "avg_safety_score": 86.3
    },
    {
      "id": "trip124",
      "destination": "Red Fort, Delhi",
      "start_time": "2025-09-30T09:00:00",
      "end_time": "2025-09-30T14:00:00",
      "status": "completed",
      "duration_hours": 5.0,
      "avg_safety_score": 92.1
    }
  ]
}
```

---

### 6. Get Safety Score

**Endpoint:** `GET /api/safety/score`

**Description:** Get current safety score and analysis

**Headers:**
```
Authorization: Bearer YOUR_JWT_TOKEN
```

**Response:** `200 OK`
```json
{
  "tourist_id": "abc123",
  "safety_score": 87.5,
  "score_breakdown": {
    "geofence_score": 90.0,
    "anomaly_score": 85.0,
    "sequence_score": 88.0
  },
  "risk_level": "low",
  "last_updated": "2025-10-01T10:30:00",
  "recommendations": [
    "Stay in well-lit areas",
    "Keep emergency contacts handy"
  ]
}
```

---

### 7. Trigger SOS Alert

**Endpoint:** `POST /api/sos/trigger`

**Description:** Send emergency SOS alert (panic button)

**Headers:**
```
Authorization: Bearer YOUR_JWT_TOKEN
```

**Request Body:**
```json
{
  "latitude": 27.1751,
  "longitude": 78.0421,
  "message": "Need immediate help!"
}
```

**Response:** `200 OK`
```json
{
  "message": "SOS alert sent successfully",
  "alert_id": "alert123",
  "timestamp": "2025-10-01T10:30:00",
  "authorities_notified": 5,
  "emergency_services_contacted": true
}
```

**JavaScript Example (Panic Button):**
```javascript
async function triggerSOS(message = "Emergency!") {
  const token = localStorage.getItem('auth_token');
  
  // Get current location
  navigator.geolocation.getCurrentPosition(async (position) => {
    const response = await fetch('http://localhost:8000/api/sos/trigger', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
        message
      })
    });
    
    if (response.ok) {
      alert('SOS alert sent! Help is on the way.');
    } else {
      alert('Failed to send SOS. Please call emergency services.');
    }
  }, (error) => {
    // Fallback: send SOS without location
    fetch('http://localhost:8000/api/sos/trigger', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ message })
    });
  });
}

// Attach to panic button
document.getElementById('panic-button').addEventListener('click', () => {
  triggerSOS('Emergency! Need immediate assistance!');
});
```

---

## 👮 Authority API

### 1. Get Active Tourists

**Endpoint:** `GET /api/tourists/active`

**Description:** List all tourists currently being tracked

**Headers:**
```
Authorization: Bearer YOUR_AUTHORITY_TOKEN
```

**Response:** `200 OK`
```json
{
  "total": 15,
  "tourists": [
    {
      "id": "tourist123",
      "name": "John Doe",
      "email": "john@example.com",
      "phone": "+1234567890",
      "current_location": {
        "latitude": 27.1751,
        "longitude": 78.0421,
        "last_updated": "2025-10-01T10:30:00"
      },
      "safety_score": 87.5,
      "trip_status": "active",
      "destination": "Taj Mahal"
    }
  ]
}
```

---

### 2. Track Specific Tourist

**Endpoint:** `GET /api/tourist/{tourist_id}/track`

**Description:** Get real-time tracking data for a specific tourist

**Headers:**
```
Authorization: Bearer YOUR_AUTHORITY_TOKEN
```

**Response:** `200 OK`
```json
{
  "tourist": {
    "id": "tourist123",
    "name": "John Doe",
    "phone": "+1234567890",
    "safety_score": 87.5
  },
  "current_location": {
    "latitude": 27.1751,
    "longitude": 78.0421,
    "timestamp": "2025-10-01T10:30:00",
    "accuracy": 10.5
  },
  "recent_locations": [
    {
      "latitude": 27.1750,
      "longitude": 78.0420,
      "timestamp": "2025-10-01T10:29:00"
    }
  ],
  "active_trip": {
    "destination": "Taj Mahal",
    "start_time": "2025-10-01T09:00:00",
    "expected_end_time": "2025-10-01T15:00:00"
  }
}
```

---

### 3. Get Tourist Alerts

**Endpoint:** `GET /api/tourist/{tourist_id}/alerts`

**Description:** Get all alerts for a specific tourist

**Headers:**
```
Authorization: Bearer YOUR_AUTHORITY_TOKEN
```

**Response:** `200 OK`
```json
{
  "tourist_id": "tourist123",
  "alerts": [
    {
      "id": "alert123",
      "type": "sos_alert",
      "severity": "critical",
      "message": "Emergency! Need immediate help!",
      "location": {
        "latitude": 27.1751,
        "longitude": 78.0421
      },
      "timestamp": "2025-10-01T10:30:00",
      "status": "active"
    },
    {
      "id": "alert124",
      "type": "geofence_violation",
      "severity": "high",
      "message": "Entered restricted zone",
      "timestamp": "2025-10-01T10:25:00",
      "status": "acknowledged"
    }
  ]
}
```

---

### 4. Get Recent Alerts

**Endpoint:** `GET /api/alerts/recent`

**Description:** Get all recent alerts (last 24 hours)

**Headers:**
```
Authorization: Bearer YOUR_AUTHORITY_TOKEN
```

**Query Parameters:**
- `severity` (optional): Filter by severity (critical, high, medium, low)
- `limit` (optional): Number of alerts (default: 50)

**Response:** `200 OK`
```json
{
  "total": 12,
  "alerts": [
    {
      "id": "alert123",
      "tourist_id": "tourist123",
      "tourist_name": "John Doe",
      "type": "sos_alert",
      "severity": "critical",
      "location": {
        "latitude": 27.1751,
        "longitude": 78.0421
      },
      "timestamp": "2025-10-01T10:30:00",
      "status": "active"
    }
  ]
}
```

---

### 5. Acknowledge Alert

**Endpoint:** `POST /api/incident/acknowledge`

**Description:** Acknowledge that an alert has been received

**Headers:**
```
Authorization: Bearer YOUR_AUTHORITY_TOKEN
```

**Request Body:**
```json
{
  "alert_id": "alert123",
  "notes": "Dispatching patrol unit to location"
}
```

**Response:** `200 OK`
```json
{
  "message": "Alert acknowledged",
  "alert_id": "alert123",
  "acknowledged_by": "Officer Smith",
  "acknowledged_at": "2025-10-01T10:31:00"
}
```

---

### 6. Close Incident

**Endpoint:** `POST /api/incident/close`

**Description:** Mark an incident as resolved

**Headers:**
```
Authorization: Bearer YOUR_AUTHORITY_TOKEN
```

**Request Body:**
```json
{
  "alert_id": "alert123",
  "resolution": "Tourist found safe, false alarm",
  "action_taken": "On-site verification completed"
}
```

**Response:** `200 OK`
```json
{
  "message": "Incident closed successfully",
  "alert_id": "alert123",
  "closed_by": "Officer Smith",
  "closed_at": "2025-10-01T10:45:00"
}
```

---

### 7. Generate E-FIR

**Endpoint:** `POST /api/efir/generate`

**Description:** Generate electronic First Information Report

**Headers:**
```
Authorization: Bearer YOUR_AUTHORITY_TOKEN
```

**Request Body:**
```json
{
  "alert_id": "alert123",
  "tourist_id": "tourist123",
  "incident_type": "theft",
  "description": "Mobile phone stolen at tourist location",
  "location": {
    "latitude": 27.1751,
    "longitude": 78.0421
  },
  "witnesses": ["witness1@example.com"],
  "evidence": ["photo1.jpg", "photo2.jpg"]
}
```

**Response:** `200 OK`
```json
{
  "message": "E-FIR generated successfully",
  "efir_id": "FIR123456",
  "blockchain_tx_id": "tx_abc123",
  "status": "submitted",
  "timestamp": "2025-10-01T10:50:00"
}
```

---

### 8. Get Safety Zones

**Endpoint:** `GET /api/zones/list`

**Description:** Get all defined safety/restricted zones

**Headers:**
```
Authorization: Bearer YOUR_AUTHORITY_TOKEN
```

**Response:** `200 OK`
```json
{
  "zones": [
    {
      "id": "zone123",
      "name": "Tourist Area - Safe",
      "type": "safe",
      "coordinates": [
        [27.1750, 78.0420],
        [27.1755, 78.0420],
        [27.1755, 78.0425],
        [27.1750, 78.0425]
      ],
      "description": "Well-lit tourist area with police presence"
    },
    {
      "id": "zone124",
      "name": "Restricted Area",
      "type": "restricted",
      "coordinates": [
        [27.1800, 78.0500],
        [27.1805, 78.0500],
        [27.1805, 78.0505],
        [27.1800, 78.0505]
      ],
      "description": "High crime area - avoid after dark"
    }
  ]
}
```

---

### 9. Create Safety Zone

**Endpoint:** `POST /api/zones/create`

**Description:** Define a new safety or restricted zone

**Headers:**
```
Authorization: Bearer YOUR_AUTHORITY_TOKEN
```

**Request Body:**
```json
{
  "name": "New Tourist Zone",
  "type": "safe",
  "coordinates": [
    [27.1750, 78.0420],
    [27.1755, 78.0420],
    [27.1755, 78.0425],
    [27.1750, 78.0425]
  ],
  "description": "Newly developed tourist area"
}
```

**Response:** `200 OK`
```json
{
  "message": "Zone created successfully",
  "zone": {
    "id": "zone125",
    "name": "New Tourist Zone",
    "type": "safe",
    "created_at": "2025-10-01T11:00:00"
  }
}
```

---

### 10. Delete Safety Zone

**Endpoint:** `DELETE /api/zones/{zone_id}`

**Description:** Remove a safety zone

**Headers:**
```
Authorization: Bearer YOUR_AUTHORITY_TOKEN
```

**Response:** `200 OK`
```json
{
  "message": "Zone deleted successfully",
  "zone_id": "zone125"
}
```

---

## 📡 WebSocket Real-time Alerts

### Connection

**WebSocket URL:**
```
ws://localhost:8000/api/alerts/subscribe?token=YOUR_JWT_TOKEN
```

**Requirements:**
- Must be authenticated as `authority` or `admin` role
- Token passed as query parameter (not headers)

### JavaScript Example

```javascript
class AlertsWebSocket {
  constructor(token) {
    this.token = token;
    this.ws = null;
    this.reconnectAttempts = 0;
  }
  
  connect() {
    const wsUrl = `ws://localhost:8000/api/alerts/subscribe?token=${this.token}`;
    this.ws = new WebSocket(wsUrl);
    
    this.ws.onopen = () => {
      console.log('✅ Connected to alerts');
      this.reconnectAttempts = 0;
      this.startHeartbeat();
    };
    
    this.ws.onmessage = (event) => {
      if (event.data === 'pong') {
        console.log('💗 Heartbeat OK');
        return;
      }
      
      try {
        const alert = JSON.parse(event.data);
        this.handleAlert(alert);
      } catch (e) {
        console.error('Failed to parse alert:', e);
      }
    };
    
    this.ws.onclose = (event) => {
      console.log(`Connection closed: ${event.code}`);
      this.stopHeartbeat();
      
      // Reconnect if not auth error
      if (event.code !== 1008) {
        this.reconnect();
      }
    };
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }
  
  handleAlert(alert) {
    console.log('🚨 New alert:', alert);
    
    // Show notification
    if (Notification.permission === 'granted') {
      new Notification('SafeHorizon Alert', {
        body: `${alert.type} - ${alert.tourist_name}`,
        icon: '/icon.png',
        tag: alert.alert_id
      });
    }
    
    // Update UI
    this.displayAlert(alert);
    
    // Play sound
    this.playAlertSound(alert.severity);
  }
  
  displayAlert(alert) {
    const alertElement = document.createElement('div');
    alertElement.className = `alert alert-${alert.severity}`;
    alertElement.innerHTML = `
      <h3>${alert.type}</h3>
      <p><strong>Tourist:</strong> ${alert.tourist_name}</p>
      <p><strong>Time:</strong> ${new Date(alert.timestamp).toLocaleString()}</p>
      <button onclick="acknowledgeAlert('${alert.alert_id}')">Acknowledge</button>
    `;
    
    document.getElementById('alerts-container').prepend(alertElement);
  }
  
  startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      if (this.ws.readyState === WebSocket.OPEN) {
        this.ws.send('ping');
      }
    }, 30000);
  }
  
  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
    }
  }
  
  reconnect() {
    this.reconnectAttempts++;
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
    
    console.log(`Reconnecting in ${delay/1000}s...`);
    setTimeout(() => this.connect(), delay);
  }
  
  disconnect() {
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.close(1000);
    }
  }
}

// Usage
const token = localStorage.getItem('auth_token');
const alertsWS = new AlertsWebSocket(token);
alertsWS.connect();
```

### Alert Message Format

```json
{
  "type": "sos_alert",
  "alert_id": 21,
  "tourist_id": "abc123",
  "tourist_name": "John Doe",
  "severity": "critical",
  "location": {
    "latitude": 27.1751,
    "longitude": 78.0421
  },
  "timestamp": "2025-10-01T10:30:00"
}
```

### Alert Types
- `sos_alert` - Emergency SOS triggered
- `geofence_violation` - Entered restricted zone
- `anomaly_detected` - Unusual behavior detected
- `low_safety_score` - Safety score dropped below threshold

### Severity Levels
- `critical` - Immediate action required (SOS)
- `high` - Urgent attention needed
- `medium` - Monitor situation
- `low` - Information only

---

## ⚠️ Error Handling

### HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | Request completed successfully |
| 201 | Created | Resource created |
| 400 | Bad Request | Invalid input data |
| 401 | Unauthorized | Missing or invalid token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 422 | Validation Error | Input validation failed |
| 500 | Server Error | Internal server error |

### Error Response Format

```json
{
  "detail": "Error message here"
}
```

### Validation Error Format

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### JavaScript Error Handling Example

```javascript
async function apiRequest(url, options = {}) {
  try {
    const token = localStorage.getItem('auth_token');
    
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : '',
        ...options.headers
      }
    });
    
    // Handle HTTP errors
    if (!response.ok) {
      const error = await response.json();
      
      switch (response.status) {
        case 401:
          // Redirect to login
          localStorage.removeItem('auth_token');
          window.location.href = '/login';
          break;
          
        case 403:
          throw new Error('You do not have permission to perform this action');
          
        case 404:
          throw new Error('Resource not found');
          
        case 422:
          // Validation error
          const errors = error.detail.map(e => e.msg).join(', ');
          throw new Error(`Validation failed: ${errors}`);
          
        default:
          throw new Error(error.detail || 'An error occurred');
      }
    }
    
    return await response.json();
    
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
}

// Usage
try {
  const data = await apiRequest('http://localhost:8000/api/auth/me');
  console.log('User:', data);
} catch (error) {
  alert(error.message);
}
```

---

## 💻 Code Examples

### Complete React Integration

```javascript
import React, { useState, useEffect } from 'react';

function SafeHorizonApp() {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('auth_token'));
  const [safetyScore, setSafetyScore] = useState(0);
  const [tracking, setTracking] = useState(false);
  
  // Login
  const login = async (email, password) => {
    const response = await fetch('http://localhost:8000/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    
    const data = await response.json();
    setToken(data.access_token);
    setUser(data.user);
    localStorage.setItem('auth_token', data.access_token);
  };
  
  // Start tracking
  const startTrip = async (destination) => {
    await fetch('http://localhost:8000/api/trip/start', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ destination })
    });
    
    setTracking(true);
  };
  
  // Update location
  useEffect(() => {
    if (!tracking) return;
    
    const updateLocation = () => {
      navigator.geolocation.getCurrentPosition(async (position) => {
        const response = await fetch('http://localhost:8000/api/location/update', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy
          })
        });
        
        const data = await response.json();
        setSafetyScore(data.safety_score);
      });
    };
    
    const interval = setInterval(updateLocation, 30000);
    return () => clearInterval(interval);
  }, [tracking, token]);
  
  // SOS Button
  const triggerSOS = async () => {
    navigator.geolocation.getCurrentPosition(async (position) => {
      await fetch('http://localhost:8000/api/sos/trigger', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          message: 'Emergency!'
        })
      });
      
      alert('SOS sent! Help is on the way.');
    });
  };
  
  return (
    <div>
      {!user ? (
        <LoginForm onLogin={login} />
      ) : (
        <div>
          <h2>Safety Score: {safetyScore.toFixed(1)}</h2>
          {!tracking ? (
            <button onClick={() => startTrip('Taj Mahal')}>Start Trip</button>
          ) : (
            <button onClick={triggerSOS} className="sos-button">
              🆘 SOS
            </button>
          )}
        </div>
      )}
    </div>
  );
}
```

---

### Police Dashboard Example

```javascript
import React, { useState, useEffect } from 'react';

function PoliceDashboard() {
  const [alerts, setAlerts] = useState([]);
  const [tourists, setTourists] = useState([]);
  const token = localStorage.getItem('auth_token');
  
  // Load active tourists
  useEffect(() => {
    loadActiveTourists();
  }, []);
  
  const loadActiveTourists = async () => {
    const response = await fetch('http://localhost:8000/api/tourists/active', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await response.json();
    setTourists(data.tourists);
  };
  
  // WebSocket for real-time alerts
  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/api/alerts/subscribe?token=${token}`);
    
    ws.onmessage = (event) => {
      if (event.data === 'pong') return;
      
      const alert = JSON.parse(event.data);
      setAlerts(prev => [alert, ...prev]);
      
      // Play sound
      new Audio('/alert.mp3').play();
    };
    
    return () => ws.close();
  }, [token]);
  
  const acknowledgeAlert = async (alertId) => {
    await fetch('http://localhost:8000/api/incident/acknowledge', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        alert_id: alertId,
        notes: 'Responding to incident'
      })
    });
  };
  
  return (
    <div className="dashboard">
      <h1>Police Dashboard</h1>
      
      <div className="alerts">
        <h2>Active Alerts ({alerts.length})</h2>
        {alerts.map(alert => (
          <div key={alert.alert_id} className={`alert alert-${alert.severity}`}>
            <h3>{alert.type}</h3>
            <p>Tourist: {alert.tourist_name}</p>
            <p>Time: {new Date(alert.timestamp).toLocaleString()}</p>
            <button onClick={() => acknowledgeAlert(alert.alert_id)}>
              Acknowledge
            </button>
          </div>
        ))}
      </div>
      
      <div className="tourists">
        <h2>Active Tourists ({tourists.length})</h2>
        {tourists.map(tourist => (
          <div key={tourist.id} className="tourist-card">
            <h3>{tourist.name}</h3>
            <p>Safety Score: {tourist.safety_score}</p>
            <p>Destination: {tourist.destination}</p>
            <button onClick={() => window.location.href = `/track/${tourist.id}`}>
              Track
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## 🔍 Testing the API

### Using Postman

1. **Create Environment:**
   - Variable: `base_url` = `http://localhost:8000`
   - Variable: `token` = (set after login)

2. **Login Request:**
   ```
   POST {{base_url}}/api/auth/login
   Body: {"email": "user@example.com", "password": "password"}
   ```

3. **Set Token:**
   In Tests tab:
   ```javascript
   pm.environment.set("token", pm.response.json().access_token);
   ```

4. **Use Token:**
   In Authorization tab: Bearer Token → `{{token}}`

### Using cURL

```bash
# Login
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}' \
  | jq -r '.access_token')

# Use token
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

---

## 📞 Support

- **API Documentation:** http://localhost:8000/docs (Swagger UI)
- **Alternative Docs:** http://localhost:8000/redoc (ReDoc)
- **Health Check:** http://localhost:8000/health

---

**Happy Coding! 🚀**