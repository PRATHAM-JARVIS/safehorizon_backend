# SafeHorizon API - Quick Reference Card

**For Frontend Developers** | **Version 1.0.0** | **Status: ✅ All Systems Operational**

---

## 🚀 Quick Start (3 Steps)

### 1. Register & Login
```javascript
// Register
POST /api/auth/register
Body: { email, password, name, phone, emergency_contact, emergency_phone }
Response: { user_id, email }

// Login
POST /api/auth/login
Body: { email, password }
Response: { access_token, token_type: "bearer", user_id, role }

// Save token
localStorage.setItem('token', response.access_token);
```

### 2. Authenticated Requests
```javascript
// Include in all requests
headers: {
  'Authorization': 'Bearer YOUR_TOKEN_HERE',
  'Content-Type': 'application/json'
}
```

### 3. Update Location
```javascript
POST /api/location/update
Body: { lat, lon, speed, altitude, accuracy, timestamp }
Response: { safety_score, risk_level, location_id }
```

---

## 📍 Core Endpoints

### Tourist Endpoints

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/auth/register` | POST | Register tourist | ❌ |
| `/auth/login` | POST | Login tourist | ❌ |
| `/auth/me` | GET | Get current user | ✅ |
| `/trip/start` | POST | Start new trip | ✅ |
| `/trip/end` | POST | End current trip | ✅ |
| `/trip/history` | GET | Get trip history | ✅ |
| `/location/update` | POST | Update location | ✅ |
| `/location/history` | GET | Get location history | ✅ |
| `/safety/score` | GET | Get safety score | ✅ |
| `/sos/trigger` | POST | Trigger emergency SOS | ✅ |
| `/zones/list` | GET | List all zones | ✅ |
| `/zones/nearby` | GET | Get nearby zones | ✅ |
| `/efir/generate` | POST | Generate E-FIR | ✅ |
| `/efir/my-reports` | GET | Get my E-FIRs | ✅ |
| `/broadcasts/active` | GET | Get active broadcasts | ✅ |
| `/broadcasts/history` | GET | Get broadcast history | ✅ |
| `/device/register` | POST | Register FCM device | ✅ |

### Authority Endpoints

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/auth/register-authority` | POST | Register authority | ❌ |
| `/auth/login-authority` | POST | Login authority | ❌ |
| `/tourists/active` | GET | Get active tourists | ✅ |
| `/tourist/{id}/track` | GET | Track specific tourist | ✅ |
| `/tourist/{id}/profile` | GET | Get tourist profile | ✅ |
| `/tourist/{id}/location/current` | GET | Get current location | ✅ |
| `/tourist/{id}/location/history` | GET | Get location history | ✅ |
| `/tourist/{id}/alerts` | GET | Get tourist alerts | ✅ |
| `/alerts/recent` | GET | Get recent alerts | ✅ |
| `/alerts/subscribe` | WS | Subscribe to real-time alerts | ✅ |
| `/heatmap/data` | GET | Get all heatmap data | ✅ |
| `/heatmap/zones` | GET | Get heatmap zones | ✅ |
| `/heatmap/alerts` | GET | Get heatmap alerts | ✅ |
| `/heatmap/tourists` | GET | Get heatmap tourists | ✅ |
| `/zones/manage` | GET | List zones (management) | ✅ |
| `/zones/create` | POST | Create new zone | ✅ |
| `/zones/{id}` | DELETE | Delete zone | ✅ |
| `/broadcast/radius` | POST | Broadcast to radius | ✅ |
| `/broadcast/zone` | POST | Broadcast to zone | ✅ |
| `/efir/list` | GET | List E-FIR records | ✅ |

---

## 🎨 UI Components Data Models

### Safety Score Display
```typescript
interface SafetyScore {
  safety_score: number;        // 0-100
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  last_updated: string;        // ISO timestamp
}

// Color mapping
const colors = {
  low: '#00ff00',      // Green (80-100)
  medium: '#ffaa00',   // Yellow (60-79)
  high: '#ff6600',     // Orange (40-59)
  critical: '#ff0000'  // Red (0-39)
};
```

### Location Status Indicator
```typescript
interface LocationStatus {
  status: 'live' | 'recent' | 'stale';
  minutes_ago: number;
  is_recent: boolean;
  timestamp: string;
}

// Status colors
const statusColors = {
  live: '#00ff00',    // < 5 min - Green dot
  recent: '#ffaa00',  // 5-30 min - Yellow dot
  stale: '#808080'    // > 30 min - Gray dot
};
```

### Tourist Card
```typescript
interface TouristCard {
  id: string;
  name: string;
  safety_score: number;
  last_seen: string;
  location: {
    latitude: number;
    longitude: number;
    status: 'live' | 'recent' | 'stale';
  };
  risk_level: string;
}
```

### Alert Notification
```typescript
interface Alert {
  id: number;
  type: 'anomaly' | 'geofence' | 'sos' | 'safety_drop' | 'manual';
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  tourist: {
    id: string;
    name: string;
  };
  location: {
    lat: number;
    lon: number;
  };
  created_at: string;
  is_acknowledged: boolean;
}
```

---

## 🗺️ Map Integration

### Leaflet.js Setup
```javascript
import L from 'leaflet';

// Initialize map
const map = L.map('map').setView([28.6139, 77.2090], 12);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

// Add tourist marker
const marker = L.circleMarker([lat, lon], {
  radius: 8,
  fillColor: getRiskColor(risk_level),
  color: '#fff',
  weight: 2,
  fillOpacity: 0.8
}).addTo(map);

// Add popup
marker.bindPopup(`
  <b>${name}</b><br>
  Safety Score: ${safety_score}<br>
  Last Seen: ${new Date(last_seen).toLocaleString()}
`);
```

### Google Maps Setup
```javascript
// Initialize map
const map = new google.maps.Map(document.getElementById('map'), {
  center: { lat: 28.6139, lng: 77.2090 },
  zoom: 12
});

// Add tourist marker
const marker = new google.maps.Marker({
  position: { lat, lng: lon },
  map: map,
  icon: {
    path: google.maps.SymbolPath.CIRCLE,
    scale: 10,
    fillColor: getRiskColor(risk_level),
    fillOpacity: 0.8,
    strokeColor: '#fff',
    strokeWeight: 2
  }
});

// Add info window
const infoWindow = new google.maps.InfoWindow({
  content: `
    <b>${name}</b><br>
    Safety Score: ${safety_score}<br>
    Last Seen: ${new Date(last_seen).toLocaleString()}
  `
});

marker.addListener('click', () => {
  infoWindow.open(map, marker);
});
```

---

## 🔔 WebSocket Connection

### Real-time Alerts (Authority Dashboard)
```javascript
const token = localStorage.getItem('token');
const ws = new WebSocket(
  `ws://localhost:8000/api/authority/alerts/subscribe?token=${token}`
);

ws.onopen = () => {
  console.log('Connected to alert stream');
};

ws.onmessage = (event) => {
  const alert = JSON.parse(event.data);
  
  // Handle different alert types
  switch (alert.type) {
    case 'sos_alert':
      showEmergencyAlert(alert);
      playAlertSound();
      break;
    case 'safety_alert':
      showSafetyNotification(alert);
      break;
    case 'efir_generated':
      updateEFIRList();
      break;
  }
};

// Keep connection alive
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send('ping');
  }
}, 30000);

// Reconnect on disconnect
ws.onclose = () => {
  setTimeout(() => connectWebSocket(), 5000);
};
```

---

## ⚡ Performance Tips

### 1. Debounce Location Updates
```javascript
import { debounce } from 'lodash';

const updateLocation = debounce(async (lat, lon) => {
  await fetch('/api/location/update', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: JSON.stringify({ lat, lon, timestamp: new Date().toISOString() })
  });
}, 10000); // Max once per 10 seconds
```

### 2. Cache Static Data
```javascript
let zonesCache = null;
let cacheTimestamp = 0;
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

async function getZones() {
  if (zonesCache && Date.now() - cacheTimestamp < CACHE_DURATION) {
    return zonesCache;
  }
  
  zonesCache = await api.get('/zones/list');
  cacheTimestamp = Date.now();
  return zonesCache;
}
```

### 3. Use Bounds for Heatmap
```javascript
// Only fetch data for visible map area
const bounds = map.getBounds();
const url = `/heatmap/data?` +
  `bounds_north=${bounds.getNorth()}&` +
  `bounds_south=${bounds.getSouth()}&` +
  `bounds_east=${bounds.getEast()}&` +
  `bounds_west=${bounds.getWest()}`;

const data = await fetch(url);
```

### 4. Batch Requests
```javascript
// Good: Single combined request
const heatmapData = await api.get('/heatmap/data');

// Bad: Multiple individual requests
const zones = await api.get('/heatmap/zones');
const alerts = await api.get('/heatmap/alerts');
const tourists = await api.get('/heatmap/tourists');
```

---

## 🔐 Error Handling

### Standard Error Response
```typescript
interface APIError {
  detail: string;
}

// Example
{
  "detail": "Tourist not found"
}
```

### HTTP Status Codes
```javascript
switch (response.status) {
  case 400:
    // Bad request - check your data
    console.error('Invalid request data');
    break;
  case 401:
    // Unauthorized - token expired/invalid
    redirectToLogin();
    break;
  case 403:
    // Forbidden - insufficient permissions
    showError('Access denied');
    break;
  case 404:
    // Not found
    showError('Resource not found');
    break;
  case 429:
    // Rate limited
    showError('Too many requests, please wait');
    break;
  case 500:
    // Server error
    showError('Server error, please try again');
    break;
}
```

### Network Error Detection
```javascript
try {
  const response = await fetch(url, options);
  const data = await response.json();
} catch (error) {
  if (error.message === 'Failed to fetch') {
    showError('Network connection lost');
  } else {
    showError(error.message);
  }
}
```

---

## 📱 Mobile App Integration

### React Native Location Tracking
```javascript
import Geolocation from '@react-native-community/geolocation';

Geolocation.watchPosition(
  async (position) => {
    const { latitude, longitude, speed, altitude, accuracy } = position.coords;
    
    await fetch('http://api.safehorizon.app/api/location/update', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        lat: latitude,
        lon: longitude,
        speed: speed || 0,
        altitude: altitude || 0,
        accuracy,
        timestamp: new Date().toISOString()
      })
    });
  },
  (error) => console.error(error),
  {
    enableHighAccuracy: true,
    distanceFilter: 10, // Update every 10 meters
    interval: 10000     // Or every 10 seconds
  }
);
```

### Flutter Location Tracking
```dart
import 'package:geolocator/geolocator.dart';
import 'package:http/http.dart' as http;

StreamSubscription<Position> positionStream = Geolocator.getPositionStream(
  locationSettings: LocationSettings(
    accuracy: LocationAccuracy.high,
    distanceFilter: 10,
  ),
).listen((Position position) async {
  final response = await http.post(
    Uri.parse('http://api.safehorizon.app/api/location/update'),
    headers: {
      'Authorization': 'Bearer $token',
      'Content-Type': 'application/json',
    },
    body: jsonEncode({
      'lat': position.latitude,
      'lon': position.longitude,
      'speed': position.speed,
      'altitude': position.altitude,
      'accuracy': position.accuracy,
      'timestamp': DateTime.now().toIso8601String(),
    }),
  );
});
```

---

## 🧪 Testing Your Integration

### Test Credentials
```javascript
// Use these for testing (development only)
const testTourist = {
  email: 'test_tourist_' + Date.now() + '@example.com',
  password: 'TestPassword123!',
  name: 'Test Tourist'
};

const testAuthority = {
  email: 'test_officer_' + Date.now() + '@police.gov',
  password: 'TestPassword123!',
  badge_number: 'BADGE' + Date.now()
};
```

### Health Check
```javascript
// Check API status
fetch('http://localhost:8000/health')
  .then(res => res.json())
  .then(data => console.log('API Status:', data.status));
// Expected: { status: "healthy" }
```

---

## 📊 Common Query Parameters

### Pagination
```
?limit=20&offset=0
```

### Filtering by Time
```
?hours_back=24
```

### Map Bounds
```
?bounds_north=28.7&bounds_south=28.5&bounds_east=77.3&bounds_west=77.1
```

### Filtering by Severity
```
?severity=high
```

### Including Related Data
```
?include_trip_info=true
```

---

## 🎯 Best Practices

### ✅ DO
- Store JWT token securely (httpOnly cookies in web, secure storage in mobile)
- Handle token expiration gracefully
- Debounce location updates (10-30 seconds)
- Cache static data (zones, broadcasts)
- Use map bounds to limit data fetched
- Show loading states
- Handle network errors
- Implement retry logic with exponential backoff

### ❌ DON'T
- Store passwords in localStorage
- Update location every second (rate limits!)
- Fetch all data without bounds
- Ignore error responses
- Hardcode API URLs
- Expose tokens in URLs
- Poll frequently without debouncing

---

## 🔗 Useful Resources

- **Full API Docs:** `docs/API_DOCUMENTATION.md`
- **Changelog:** `docs/API_CHANGELOG.md`
- **Test Suite:** `test_endpoints.py`
- **Base URL (Dev):** `http://localhost:8000/api`
- **Base URL (Prod):** `https://api.safehorizon.app/api`

---

## 📞 Support

- **Issues:** File on GitHub
- **Questions:** support@safehorizon.app
- **Status:** ✅ 100% operational (34/34 tests passing)

---

**Last Updated:** October 2, 2025  
**Print this for quick reference! 📄**
