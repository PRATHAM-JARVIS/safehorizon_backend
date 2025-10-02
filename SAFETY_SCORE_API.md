# Safety Score API Documentation

## Overview

The SafeHorizon platform now includes an AI-driven location safety scoring system that provides real-time safety assessments for tourists. The system uses a multi-factor weighted analysis to calculate safety scores ranging from 0-100 (higher = safer).

## Risk Levels

| Risk Level | Score Range | Description |
|------------|-------------|-------------|
| **Low** | 80-100 | Safe conditions, minimal risk |
| **Medium** | 60-79 | Moderate caution advised |
| **High** | 40-59 | Significant risk present |
| **Critical** | 0-39 | Immediate danger, avoid area |

## AI Calculation Factors

The safety score is calculated using 6 weighted factors:

1. **Nearby Alerts (30%)** - Recent incidents within 2km radius (6-hour window)
2. **Zone Risk (25%)** - Proximity to safe/restricted/risky zones
3. **Time of Day (15%)** - Risk patterns by hour (higher at night)
4. **Crowd Density (10%)** - Safety in numbers (more tourists = safer)
5. **Speed Anomaly (10%)** - Unusual movement patterns detection
6. **Historical Risk (10%)** - 30-day incident history in area

---

## Endpoints

### 1. Update Location with Safety Score

**POST** `/location/update`

Updates tourist's location and calculates AI-driven safety score in real-time.

#### Authentication
- **Required**: Bearer Token (Tourist role)

#### Request Body
```json
{
  "lat": 40.7128,
  "lon": -74.0060,
  "altitude": 10.5,
  "speed": 1.2,
  "accuracy": 15.0,
  "timestamp": "2025-10-02T14:30:00Z"
}
```

#### Response
```json
{
  "status": "success",
  "location_id": 12345,
  "location_safety_score": 72.5,
  "tourist_safety_score": 75.3,
  "risk_level": "medium",
  "ai_analysis": {
    "factors": [
      {
        "name": "nearby_alerts",
        "score": 85.2,
        "weight": 0.30,
        "contribution": 25.56,
        "details": "2 moderate alerts within 2km in last 6 hours"
      },
      {
        "name": "zone_risk",
        "score": 60.0,
        "weight": 0.25,
        "contribution": 15.00,
        "details": "0.8km from restricted zone"
      },
      {
        "name": "time_of_day",
        "score": 85.0,
        "weight": 0.15,
        "contribution": 12.75,
        "details": "Daytime (14:30) - safer period"
      },
      {
        "name": "crowd_density",
        "score": 70.0,
        "weight": 0.10,
        "contribution": 7.00,
        "details": "8 tourists within 1km"
      },
      {
        "name": "speed_anomaly",
        "score": 95.0,
        "weight": 0.10,
        "contribution": 9.50,
        "details": "Normal movement speed"
      },
      {
        "name": "historical_risk",
        "score": 75.0,
        "weight": 0.10,
        "contribution": 7.50,
        "details": "3 incidents in last 30 days within 1km"
      }
    ],
    "recommendations": [
      "Avoid moving closer to the restricted zone 800m to the east",
      "Stay in well-populated tourist areas",
      "Keep emergency contacts readily accessible"
    ]
  },
  "alert_triggered": true,
  "alert_id": 789
}
```

#### Notes
- Safety score is calculated using real-time AI analysis
- `location_safety_score`: Safety of this specific location
- `tourist_safety_score`: Blended score (70% location + 30% tourist's historical average)
- Alerts are automatically triggered for critical/high risk levels (score < 50)
- Recommendations are AI-generated based on identified risk factors

---

### 2. Get Location History with Safety Scores

**GET** `/location/history?limit=100`

Retrieves tourist's location history with safety scores.

#### Authentication
- **Required**: Bearer Token (Tourist role)

#### Query Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 100 | Maximum number of locations to return |

#### Response
```json
[
  {
    "id": 12345,
    "lat": 40.7128,
    "lon": -74.0060,
    "speed": 1.2,
    "altitude": 10.5,
    "accuracy": 15.0,
    "timestamp": "2025-10-02T14:30:00Z",
    "safety_score": 72.5,
    "safety_score_updated_at": "2025-10-02T14:30:05Z"
  },
  {
    "id": 12344,
    "lat": 40.7129,
    "lon": -74.0061,
    "speed": 1.5,
    "altitude": 10.2,
    "accuracy": 12.0,
    "timestamp": "2025-10-02T14:25:00Z",
    "safety_score": 78.3,
    "safety_score_updated_at": "2025-10-02T14:25:04Z"
  }
]
```

#### Use Cases
- Display historical safety trends on map
- Analyze tourist's movement through safe/risky areas
- Identify patterns in safety score changes

---

### 3. Get Safety Score Trend

**GET** `/location/safety-trend?hours_back=24`

Returns time-series safety score data with statistical analysis.

#### Authentication
- **Required**: Bearer Token (Tourist role)

#### Query Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `hours_back` | integer | 24 | Number of hours to look back |

#### Response
```json
{
  "hours_back": 24,
  "data_points": 48,
  "trend": [
    {
      "timestamp": "2025-10-01T14:30:00Z",
      "safety_score": 85.2,
      "risk_level": "low",
      "location": {
        "lat": 40.7128,
        "lon": -74.0060
      }
    },
    {
      "timestamp": "2025-10-01T15:00:00Z",
      "safety_score": 72.5,
      "risk_level": "medium",
      "location": {
        "lat": 40.7130,
        "lon": -74.0062
      }
    }
  ],
  "statistics": {
    "average_score": 77.8,
    "min_score": 62.5,
    "max_score": 92.3,
    "current_score": 75.3,
    "score_volatility": 29.8
  }
}
```

#### Use Cases
- Display safety score chart over time
- Identify risky time periods
- Track safety improvements/deteriorations
- Alert users to increasing risk patterns

---

### 4. Get Detailed Safety Analysis

**GET** `/location/safety-analysis`

Returns comprehensive AI analysis of tourist's current location.

#### Authentication
- **Required**: Bearer Token (Tourist role)

#### Response
```json
{
  "location": {
    "id": 12345,
    "lat": 40.7128,
    "lon": -74.0060,
    "timestamp": "2025-10-02T14:30:00Z"
  },
  "safety_score": 72.5,
  "risk_level": "medium",
  "factors": [
    {
      "name": "nearby_alerts",
      "score": 85.2,
      "weight": 0.30,
      "contribution": 25.56,
      "details": "2 moderate alerts within 2km in last 6 hours"
    },
    {
      "name": "zone_risk",
      "score": 60.0,
      "weight": 0.25,
      "contribution": 15.00,
      "details": "0.8km from restricted zone"
    },
    {
      "name": "time_of_day",
      "score": 85.0,
      "weight": 0.15,
      "contribution": 12.75,
      "details": "Daytime (14:30) - safer period"
    },
    {
      "name": "crowd_density",
      "score": 70.0,
      "weight": 0.10,
      "contribution": 7.00,
      "details": "8 tourists within 1km"
    },
    {
      "name": "speed_anomaly",
      "score": 95.0,
      "weight": 0.10,
      "contribution": 9.50,
      "details": "Normal movement speed"
    },
    {
      "name": "historical_risk",
      "score": 75.0,
      "weight": 0.10,
      "contribution": 7.50,
      "details": "3 incidents in last 30 days within 1km"
    }
  ],
  "recommendations": [
    "Avoid moving closer to the restricted zone 800m to the east",
    "Stay in well-populated tourist areas",
    "Keep emergency contacts readily accessible",
    "Consider alternative routes away from recent alert locations"
  ],
  "tourist_profile": {
    "id": 456,
    "overall_safety_score": 75.3,
    "last_seen": "2025-10-02T14:30:00Z"
  }
}
```

#### Use Cases
- Display detailed safety breakdown to user
- Show why a location is risky
- Provide actionable safety recommendations
- Help users understand AI reasoning

---

### 5. Get Nearby Risks

**GET** `/location/nearby-risks?radius_km=2.0`

Returns all nearby safety risks, alerts, and dangerous zones.

#### Authentication
- **Required**: Bearer Token (Tourist role)

#### Query Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `radius_km` | float | 2.0 | Search radius in kilometers |

#### Response
```json
{
  "current_location": {
    "lat": 40.7128,
    "lon": -74.0060,
    "safety_score": 72.5,
    "timestamp": "2025-10-02T14:30:00Z"
  },
  "search_radius_km": 2.0,
  "nearby_alerts": [
    {
      "alert_id": 789,
      "type": "anomaly",
      "severity": "high",
      "title": "Safety Alert - Score: 35",
      "description": "Safety score dropped to 35. Risk level: high",
      "distance_km": 0.85,
      "location": {
        "lat": 40.7135,
        "lon": -74.0070
      },
      "timestamp": "2025-10-02T13:45:00Z"
    },
    {
      "alert_id": 788,
      "type": "sos",
      "severity": "critical",
      "title": "Emergency SOS Alert",
      "description": "Tourist in distress",
      "distance_km": 1.2,
      "location": {
        "lat": 40.7140,
        "lon": -74.0075
      },
      "timestamp": "2025-10-02T12:30:00Z"
    }
  ],
  "nearby_risky_zones": [
    {
      "zone_id": 123,
      "name": "Restricted Area - Construction Site",
      "type": "restricted",
      "distance_km": 0.8,
      "radius_km": 0.5,
      "center": {
        "lat": 40.7132,
        "lon": -74.0068
      },
      "is_inside": false
    },
    {
      "zone_id": 124,
      "name": "High Crime Area",
      "type": "risky",
      "distance_km": 1.5,
      "radius_km": 1.0,
      "center": {
        "lat": 40.7145,
        "lon": -74.0080
      },
      "is_inside": false
    }
  ],
  "risk_summary": {
    "total_alerts": 2,
    "critical_alerts": 1,
    "high_alerts": 1,
    "risky_zones_nearby": 2,
    "inside_risky_zone": false
  }
}
```

#### Use Cases
- Display nearby dangers on map
- Show alert markers with distances
- Highlight dangerous zones
- Help tourists avoid risky areas
- Provide situational awareness

---

### 6. Get Current Safety Score

**GET** `/safety/score`

Returns tourist's current overall safety score.

#### Authentication
- **Required**: Bearer Token (Tourist role)

#### Response
```json
{
  "safety_score": 75.3,
  "risk_level": "medium",
  "last_updated": "2025-10-02T14:30:00Z"
}
```

#### Use Cases
- Display safety score badge in app header
- Quick safety status check
- Simple API for lightweight clients

---

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 404 Not Found
```json
{
  "detail": "No location data found"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "lat"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Integration Examples

### Frontend - Display Safety Score

```javascript
// Update location and get safety analysis
const response = await fetch('/location/update', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    lat: position.coords.latitude,
    lon: position.coords.longitude,
    speed: position.coords.speed || 0,
    altitude: position.coords.altitude || 0,
    accuracy: position.coords.accuracy,
    timestamp: new Date().toISOString()
  })
});

const data = await response.json();

// Display safety score with color coding
const scoreColor = 
  data.risk_level === 'critical' ? 'red' :
  data.risk_level === 'high' ? 'orange' :
  data.risk_level === 'medium' ? 'yellow' : 'green';

// Show AI recommendations
data.ai_analysis.recommendations.forEach(rec => {
  console.log(`💡 ${rec}`);
});
```

### Frontend - Safety Trend Chart

```javascript
// Fetch 24-hour safety trend
const trendData = await fetch('/location/safety-trend?hours_back=24', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());

// Render chart
const chartData = trendData.trend.map(point => ({
  x: new Date(point.timestamp),
  y: point.safety_score,
  color: getRiskColor(point.risk_level)
}));

// Display statistics
console.log(`Average Safety: ${trendData.statistics.average_score}`);
console.log(`Volatility: ${trendData.statistics.score_volatility}`);
```

### Frontend - Nearby Risks Map

```javascript
// Get nearby risks
const risks = await fetch('/location/nearby-risks?radius_km=2.0', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());

// Add alert markers to map
risks.nearby_alerts.forEach(alert => {
  addMarker(map, {
    position: [alert.location.lat, alert.location.lon],
    icon: getSeverityIcon(alert.severity),
    popup: `${alert.title} - ${alert.distance_km}km away`
  });
});

// Draw danger zones
risks.nearby_risky_zones.forEach(zone => {
  addCircle(map, {
    center: [zone.center.lat, zone.center.lon],
    radius: zone.radius_km * 1000, // Convert to meters
    color: zone.type === 'restricted' ? 'orange' : 'red',
    fillOpacity: 0.2
  });
});

// Show warning if inside risky zone
if (risks.risk_summary.inside_risky_zone) {
  showWarning('⚠️ You are currently inside a dangerous zone!');
}
```

---

## Background Processing

The system includes a background task function that can be scheduled to update safety scores for all recent locations:

```python
from app.services.location_safety import update_location_safety_scores

# Run every 5-10 minutes via cron or task scheduler
async def scheduled_safety_update():
    async with get_db_session() as db:
        await update_location_safety_scores(db, hours_back=1)
```

This ensures safety scores stay current even when tourists aren't actively updating their location.

---

## Performance Considerations

- **Indexes**: Database indexes on `safety_score` and `safety_score_updated_at` for fast queries
- **Caching**: Consider caching zone data and historical statistics
- **Batch Updates**: Background task updates up to 1000 locations per run
- **Real-time**: Location update endpoint calculates score in < 200ms typically

---

## Security Notes

- All endpoints require authentication (Bearer token)
- Tourist users can only access their own data
- Authority users have separate endpoints for monitoring all tourists
- Location data is privacy-sensitive - handle according to regulations

---

## Future Enhancements

- Machine learning model training on historical incident data
- Weather integration (storms, natural disasters)
- News/events integration (protests, celebrations)
- Predictive risk forecasting
- Personalized risk profiles based on tourist behavior
- Multi-language AI recommendations

---

**Version**: 1.0.0  
**Last Updated**: October 2, 2025  
**Contact**: support@safehorizon.com
