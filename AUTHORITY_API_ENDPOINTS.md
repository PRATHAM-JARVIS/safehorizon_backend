# 👮‍♀️ SafeHorizon Authority API Endpoints

**Complete API Documentation for Authority/Police Features**  
**Generated:** October 3, 2025  
**Base URL:** `http://localhost:8000/api`  
**Authentication:** Bearer JWT Token Required (Authority Role)

---

## 📋 Table of Contents

1. [Authentication Endpoints](#authentication-endpoints)
2. [Dashboard & Overview](#dashboard--overview)
3. [Tourist Monitoring](#tourist-monitoring)
4. [Alert Management](#alert-management)
5. [Zone Management](#zone-management)
6. [Emergency Broadcasting](#emergency-broadcasting)
7. [E-FIR Management](#e-fir-management)
8. [Search & Analytics](#search--analytics)
9. [Heatmap Data](#heatmap-data)
10. [Real-time Features](#real-time-features)

---

## 🔐 Authentication Endpoints

### 1. Register Authority
**POST** `/auth/authority/register`

Register a new authority account.

**Request Body:**
```json
{
  "email": "officer@police.gov",
  "password": "securePassword123",
  "name": "Officer John Smith",
  "phone": "+1234567890",
  "department": "Metropolitan Police",
  "badge_number": "BADGE123456",
  "rank": "Inspector"
}
```

**Response (201):**
```json
{
  "message": "Authority registered successfully",
  "user_id": "auth-uuid-string",
  "email": "officer@police.gov",
  "department": "Metropolitan Police",
  "rank": "Inspector"
}
```

### 2. Login Authority
**POST** `/auth/authority/login`

Authenticate authority and receive JWT token.

**Request Body:**
```json
{
  "email": "officer@police.gov",
  "password": "securePassword123"
}
```

**Response (200):**
```json
{
  "access_token": "jwt-token-here",
  "token_type": "bearer",
  "user_id": "auth-uuid-string",
  "email": "officer@police.gov",
  "role": "authority",
  "department": "Metropolitan Police",
  "rank": "Inspector"
}
```

---

## 📊 Dashboard & Overview

### 3. Get Dashboard Overview
**GET** `/dashboard/overview`

Get comprehensive dashboard statistics and overview.

**Response (200):**
```json
{
  "summary": {
    "total_tourists": 1247,
    "active_tourists": 342,
    "alerts_last_24h": 23,
    "critical_alerts": 3,
    "active_broadcasts": 2,
    "zones_monitored": 15
  },
  "recent_activity": {
    "new_registrations_today": 12,
    "sos_triggers_today": 2,
    "efirs_generated_today": 5,
    "average_safety_score": 78.4
  },
  "statistics": {
    "tourist_distribution": {
      "high_risk_areas": 23,
      "medium_risk_areas": 89,
      "safe_areas": 230
    },
    "alert_types": {
      "anomaly": 15,
      "sos": 5,
      "manual": 3
    }
  },
  "generated_at": "2025-10-03T10:30:00Z"
}
```

### 4. Get System Health
**GET** `/system/health`

Get system health and performance metrics.

**Response (200):**
```json
{
  "status": "healthy",
  "services": {
    "database": {"status": "online", "response_time_ms": 12},
    "redis": {"status": "online", "response_time_ms": 3},
    "ai_services": {"status": "online", "response_time_ms": 45},
    "notification_service": {"status": "online", "response_time_ms": 8}
  },
  "performance": {
    "active_connections": 234,
    "requests_per_minute": 1250,
    "average_response_time_ms": 89
  },
  "timestamp": "2025-10-03T10:30:00Z"
}
```

---

## 👥 Tourist Monitoring

### 5. Get All Tourists
**GET** `/tourists?page=1&limit=20&status=all&sort_by=last_seen&order=desc`

Get list of all tourists with filtering and pagination.

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `limit` (optional): Records per page (default: 20)
- `status` (optional): Filter by status ('active', 'inactive', 'all')
- `sort_by` (optional): Sort field ('name', 'last_seen', 'safety_score', 'registered_at')
- `order` (optional): Sort order ('asc', 'desc')
- `search` (optional): Search by name or email

**Response (200):**
```json
{
  "tourists": [
    {
      "id": "tourist-uuid",
      "name": "John Doe",
      "email": "tourist@example.com",
      "phone": "+1234567890",
      "safety_score": 82.1,
      "last_seen": "2025-10-03T10:25:00Z",
      "is_active": true,
      "current_location": {
        "lat": 40.7589,
        "lon": -73.9851,
        "timestamp": "2025-10-03T10:25:00Z",
        "address": "Central Park, New York"
      },
      "trip_status": "active",
      "registered_at": "2025-10-01T08:00:00Z",
      "emergency_contact": "Jane Doe",
      "emergency_phone": "+0987654321"
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 63,
    "total_records": 1247,
    "records_per_page": 20,
    "has_next": true,
    "has_previous": false
  },
  "filters_applied": {
    "status": "all",
    "sort_by": "last_seen",
    "order": "desc"
  }
}
```

### 6. Get Tourist Details
**GET** `/tourists/{tourist_id}`

Get detailed information about a specific tourist.

**Response (200):**
```json
{
  "tourist": {
    "id": "tourist-uuid",
    "name": "John Doe",
    "email": "tourist@example.com",
    "phone": "+1234567890",
    "safety_score": 82.1,
    "last_seen": "2025-10-03T10:25:00Z",
    "is_active": true,
    "registered_at": "2025-10-01T08:00:00Z",
    "emergency_contact": "Jane Doe",
    "emergency_phone": "+0987654321"
  },
  "current_location": {
    "id": 456,
    "lat": 40.7589,
    "lon": -73.9851,
    "speed": 5.2,
    "altitude": 10.5,
    "accuracy": 3.0,
    "timestamp": "2025-10-03T10:25:00Z",
    "address": "Central Park, New York",
    "safety_score": 78.5
  },
  "recent_activity": {
    "locations_last_24h": 145,
    "alerts_generated": 2,
    "trips_completed": 3,
    "efirs_submitted": 1
  },
  "safety_analysis": {
    "risk_level": "low",
    "recent_scores": [82.1, 79.5, 85.3, 77.8],
    "average_score_7d": 81.2,
    "trend": "stable"
  }
}
```

### 7. Get Tourist Location History
**GET** `/tourists/{tourist_id}/locations?limit=100&hours_back=24`

Get location history for a specific tourist.

**Query Parameters:**
- `limit` (optional): Number of records (default: 100)
- `hours_back` (optional): Hours to look back (default: 24)

**Response (200):**
```json
{
  "tourist_id": "tourist-uuid",
  "tourist_name": "John Doe",
  "locations": [
    {
      "id": 456,
      "lat": 40.7589,
      "lon": -73.9851,
      "speed": 5.2,
      "altitude": 10.5,
      "accuracy": 3.0,
      "timestamp": "2025-10-03T10:25:00Z",
      "safety_score": 78.5,
      "address": "Central Park, New York"
    }
  ],
  "summary": {
    "total_locations": 145,
    "time_range": "24 hours",
    "distance_traveled_km": 12.5,
    "average_speed_kmh": 4.2,
    "unique_areas_visited": 8
  },
  "generated_at": "2025-10-03T10:30:00Z"
}
```

### 8. Get Tourists in Area
**GET** `/tourists/area?lat=40.7589&lon=-73.9851&radius_km=2&include_inactive=false`

Get all tourists within a specific geographic area.

**Query Parameters:**
- `lat`: Center latitude
- `lon`: Center longitude
- `radius_km`: Search radius in kilometers
- `include_inactive` (optional): Include inactive tourists (default: false)

**Response (200):**
```json
{
  "search_area": {
    "center": {"lat": 40.7589, "lon": -73.9851},
    "radius_km": 2.0
  },
  "tourists_found": [
    {
      "id": "tourist-uuid",
      "name": "John Doe",
      "safety_score": 82.1,
      "distance_km": 0.5,
      "last_location": {
        "lat": 40.7550,
        "lon": -73.9800,
        "timestamp": "2025-10-03T10:25:00Z"
      },
      "is_active": true,
      "trip_status": "active"
    }
  ],
  "summary": {
    "total_found": 12,
    "active_tourists": 10,
    "inactive_tourists": 2,
    "average_safety_score": 79.8
  },
  "generated_at": "2025-10-03T10:30:00Z"
}
```

### 9. Search Tourists
**POST** `/tourists/search`

Advanced search for tourists with multiple criteria.

**Request Body:**
```json
{
  "filters": {
    "name": "John",
    "email": "tourist",
    "phone": "+123",
    "safety_score_min": 70.0,
    "safety_score_max": 90.0,
    "last_seen_after": "2025-10-02T00:00:00Z",
    "is_active": true,
    "has_current_trip": true
  },
  "location_filter": {
    "lat": 40.7589,
    "lon": -73.9851,
    "radius_km": 5.0
  },
  "sort": {
    "field": "safety_score",
    "order": "desc"
  },
  "pagination": {
    "page": 1,
    "limit": 20
  }
}
```

**Response (200):**
```json
{
  "results": [
    {
      "id": "tourist-uuid",
      "name": "John Doe",
      "email": "tourist@example.com",
      "safety_score": 82.1,
      "last_seen": "2025-10-03T10:25:00Z",
      "distance_km": 1.2
    }
  ],
  "total_found": 5,
  "pagination": {
    "current_page": 1,
    "total_pages": 1,
    "has_next": false
  },
  "search_criteria": {
    "filters_applied": 6,
    "location_filter": true
  }
}
```

---

## 🚨 Alert Management

### 10. Get All Alerts
**GET** `/alerts?page=1&limit=20&alert_type=all&severity=all&status=all&sort_by=timestamp&order=desc`

Get all alerts with filtering and pagination.

**Query Parameters:**
- `page`, `limit`: Pagination
- `alert_type`: Filter by type ('sos', 'anomaly', 'manual', 'all')
- `severity`: Filter by severity ('low', 'medium', 'high', 'critical', 'all')
- `status`: Filter by status ('active', 'resolved', 'investigating', 'all')
- `sort_by`: Sort field ('timestamp', 'severity', 'type')
- `order`: Sort order ('asc', 'desc')

**Response (200):**
```json
{
  "alerts": [
    {
      "id": 789,
      "alert_type": "sos",
      "severity": "critical",
      "status": "active",
      "title": "SOS Alert Triggered",
      "description": "Emergency SOS triggered by tourist",
      "tourist_id": "tourist-uuid",
      "tourist": {
        "id": "tourist-uuid",
        "name": "John Doe",
        "phone": "+1234567890"
      },
      "location": {
        "lat": 40.7589,
        "lon": -73.9851,
        "address": "Central Park, New York"
      },
      "timestamp": "2025-10-03T10:30:00Z",
      "response_time_minutes": null,
      "resolved_by": null,
      "resolved_at": null,
      "notes": [],
      "attachments": []
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 12,
    "total_records": 234,
    "records_per_page": 20
  },
  "summary": {
    "active_alerts": 23,
    "critical_alerts": 3,
    "high_priority": 8,
    "unresolved": 31
  }
}
```

### 11. Get Alert Details
**GET** `/alerts/{alert_id}`

Get detailed information about a specific alert.

**Response (200):**
```json
{
  "alert": {
    "id": 789,
    "alert_type": "sos",
    "severity": "critical",
    "status": "active",
    "title": "SOS Alert Triggered",
    "description": "Emergency SOS triggered by tourist at Central Park",
    "tourist_id": "tourist-uuid",
    "tourist": {
      "id": "tourist-uuid",
      "name": "John Doe",
      "email": "tourist@example.com",
      "phone": "+1234567890",
      "emergency_contact": "Jane Doe",
      "emergency_phone": "+0987654321",
      "safety_score": 82.1
    },
    "location": {
      "lat": 40.7589,
      "lon": -73.9851,
      "accuracy": 3.0,
      "address": "Central Park, New York",
      "timestamp": "2025-10-03T10:30:00Z"
    },
    "timeline": [
      {
        "timestamp": "2025-10-03T10:30:00Z",
        "event": "alert_created",
        "description": "SOS alert triggered",
        "user": "system"
      },
      {
        "timestamp": "2025-10-03T10:31:00Z",
        "event": "notification_sent",
        "description": "Emergency notifications sent",
        "user": "system"
      }
    ],
    "timestamp": "2025-10-03T10:30:00Z",
    "response_time_minutes": null,
    "resolved_by": null,
    "resolved_at": null,
    "resolution_notes": null,
    "attachments": [],
    "related_alerts": []
  },
  "response_actions": {
    "notifications_sent": 3,
    "authorities_notified": 2,
    "emergency_services_contacted": true,
    "follow_up_required": true
  }
}
```

### 12. Update Alert Status
**PUT** `/alerts/{alert_id}/status`

Update the status of an alert.

**Request Body:**
```json
{
  "status": "investigating",
  "notes": "Units dispatched to location",
  "estimated_arrival": "2025-10-03T10:45:00Z"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Alert status updated successfully",
  "alert": {
    "id": 789,
    "tourist_id": "tourist-uuid",
    "status": "investigating",
    "updated_by": "Officer John Smith",
    "updated_at": "2025-10-03T10:35:00Z",
    "notes": "Units dispatched to location"
  }
}
```

### 13. Resolve Alert
**POST** `/alerts/{alert_id}/resolve`

Mark an alert as resolved.

**Request Body:**
```json
{
  "resolution_notes": "Tourist found safe. False alarm due to accidental SOS trigger.",
  "resolution_type": "false_alarm",
  "follow_up_required": false
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Alert resolved successfully",
  "alert": {
    "id": 789,
    "tourist_id": "tourist-uuid",
    "status": "resolved",
    "resolved_by": "Officer John Smith",
    "resolved_at": "2025-10-03T11:00:00Z",
    "resolution_notes": "Tourist found safe. False alarm due to accidental SOS trigger.",
    "resolution_type": "false_alarm",
    "response_time_minutes": 30
  }
}
```

### 14. Create Manual Alert
**POST** `/alerts/manual`

Create a manual alert for a specific tourist or location.

**Request Body:**
```json
{
  "alert_type": "manual",
  "severity": "medium",
  "title": "Suspicious Activity Reported",
  "description": "Multiple reports of suspicious behavior in the area",
  "tourist_id": "tourist-uuid",
  "location": {
    "lat": 40.7589,
    "lon": -73.9851,
    "address": "Central Park, New York"
  },
  "requires_immediate_attention": false,
  "estimated_risk_level": "medium"
}
```

**Response (201):**
```json
{
  "success": true,
  "message": "Manual alert created successfully",
  "alert": {
    "id": 790,
    "alert_type": "manual",
    "severity": "medium",
    "status": "active",
    "title": "Suspicious Activity Reported",
    "created_by": "Officer John Smith",
    "created_at": "2025-10-03T11:15:00Z",
    "tourist_id": "tourist-uuid",
    "notifications_sent": true
  }
}
```

---

## 🗺️ Zone Management

### 15. Get All Zones
**GET** `/zones?page=1&limit=20&zone_type=all&sort_by=name&order=asc`

Get all safety zones with filtering.

**Query Parameters:**
- `page`, `limit`: Pagination
- `zone_type`: Filter by type ('safe', 'risky', 'restricted', 'all')
- `sort_by`: Sort field ('name', 'created_at', 'type')
- `order`: Sort order ('asc', 'desc')

**Response (200):**
```json
{
  "zones": [
    {
      "id": 101,
      "name": "Central Park Safe Zone",
      "type": "safe",
      "description": "Well-patrolled tourist area with high security presence",
      "center": {
        "lat": 40.7589,
        "lon": -73.9851
      },
      "radius_meters": 1000,
      "coordinates": [[lon, lat], [lon, lat]],
      "created_by": "Officer Smith",
      "created_at": "2025-10-01T08:00:00Z",
      "last_updated": "2025-10-02T14:30:00Z",
      "is_active": true,
      "tourists_inside": 23,
      "recent_alerts": 0
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 3,
    "total_records": 48,
    "records_per_page": 20
  },
  "summary": {
    "safe_zones": 20,
    "risky_zones": 15,
    "restricted_zones": 13,
    "total_zones": 48
  }
}
```

### 16. Get Zone Details
**GET** `/zones/{zone_id}`

Get detailed information about a specific zone.

**Response (200):**
```json
{
  "zone": {
    "id": 101,
    "name": "Central Park Safe Zone",
    "type": "safe",
    "description": "Well-patrolled tourist area with high security presence",
    "center": {
      "lat": 40.7589,
      "lon": -73.9851
    },
    "radius_meters": 1000,
    "coordinates": [[lon, lat], [lon, lat]],
    "created_by": "Officer Smith",
    "created_at": "2025-10-01T08:00:00Z",
    "last_updated": "2025-10-02T14:30:00Z",
    "is_active": true
  },
  "statistics": {
    "tourists_currently_inside": 23,
    "tourists_visited_24h": 156,
    "alerts_last_24h": 0,
    "average_safety_score": 87.5,
    "patrol_frequency": "every_2_hours"
  },
  "recent_activity": [
    {
      "timestamp": "2025-10-03T10:00:00Z",
      "event": "tourist_entered",
      "tourist_name": "John Doe",
      "details": "Tourist entered safe zone"
    }
  ]
}
```

### 17. Create Zone
**POST** `/zones`

Create a new safety zone.

**Request Body:**
```json
{
  "name": "Times Square Safe Zone",
  "type": "safe",
  "description": "High-traffic tourist area with increased security",
  "center": {
    "lat": 40.7580,
    "lon": -73.9855
  },
  "radius_meters": 800,
  "patrol_schedule": "continuous",
  "special_instructions": "Monitor for pickpocketing activities"
}
```

**Response (201):**
```json
{
  "success": true,
  "message": "Zone created successfully",
  "zone": {
    "id": 102,
    "name": "Times Square Safe Zone",
    "type": "safe",
    "center": {"lat": 40.7580, "lon": -73.9855},
    "radius_meters": 800,
    "created_by": "Officer John Smith",
    "created_at": "2025-10-03T11:30:00Z",
    "is_active": true
  }
}
```

### 18. Update Zone
**PUT** `/zones/{zone_id}`

Update an existing zone.

**Request Body:**
```json
{
  "name": "Updated Zone Name",
  "description": "Updated description",
  "radius_meters": 1200,
  "is_active": true,
  "special_instructions": "New patrol instructions"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Zone updated successfully",
  "zone": {
    "id": 101,
    "name": "Updated Zone Name",
    "description": "Updated description",
    "radius_meters": 1200,
    "updated_by": "Officer John Smith",
    "updated_at": "2025-10-03T11:45:00Z"
  }
}
```

### 19. Delete Zone
**DELETE** `/zones/{zone_id}`

Delete a zone (soft delete - marks as inactive).

**Response (200):**
```json
{
  "success": true,
  "message": "Zone deleted successfully",
  "zone_id": 101,
  "deleted_by": "Officer John Smith",
  "deleted_at": "2025-10-03T12:00:00Z"
}
```

### 20. Get Tourists in Zone
**GET** `/zones/{zone_id}/tourists`

Get all tourists currently in a specific zone.

**Response (200):**
```json
{
  "zone": {
    "id": 101,
    "name": "Central Park Safe Zone",
    "type": "safe"
  },
  "tourists_inside": [
    {
      "id": "tourist-uuid",
      "name": "John Doe",
      "safety_score": 82.1,
      "entry_time": "2025-10-03T10:00:00Z",
      "current_location": {
        "lat": 40.7589,
        "lon": -73.9851,
        "timestamp": "2025-10-03T11:30:00Z"
      },
      "time_in_zone_minutes": 90
    }
  ],
  "summary": {
    "total_inside": 23,
    "average_safety_score": 79.8,
    "longest_stay_hours": 4.5,
    "new_entries_last_hour": 5
  },
  "retrieved_at": "2025-10-03T11:30:00Z"
}
```

---

## 📡 Emergency Broadcasting

### 21. Create Broadcast
**POST** `/broadcasts`

Create and send emergency broadcast to tourists.

**Request Body:**
```json
{
  "broadcast_type": "RADIUS",
  "title": "Emergency Weather Alert",
  "message": "Severe thunderstorm warning. Seek indoor shelter immediately. Alert will expire at 6 PM.",
  "severity": "HIGH",
  "alert_type": "weather_warning",
  "action_required": "seek_shelter",
  "expires_at": "2025-10-03T18:00:00Z",
  "target_criteria": {
    "broadcast_type": "RADIUS",
    "center": {
      "lat": 40.7589,
      "lon": -73.9851
    },
    "radius_km": 5.0
  },
  "notification_channels": ["push", "sms"],
  "require_acknowledgment": true
}
```

**Response (201):**
```json
{
  "success": true,
  "message": "Broadcast created and sent successfully",
  "broadcast": {
    "id": 1,
    "broadcast_id": "BCAST-20251003-113000",
    "title": "Emergency Weather Alert",
    "severity": "HIGH",
    "broadcast_type": "RADIUS",
    "sent_at": "2025-10-03T11:30:00Z",
    "expires_at": "2025-10-03T18:00:00Z",
    "sent_by": "Officer John Smith"
  },
  "delivery_stats": {
    "tourists_targeted": 156,
    "push_notifications_sent": 145,
    "sms_sent": 142,
    "failed_deliveries": 11,
    "delivery_rate": 92.3
  }
}
```

### 22. Get All Broadcasts
**GET** `/broadcasts?page=1&limit=20&status=all&severity=all&sort_by=sent_at&order=desc`

Get all broadcasts with filtering.

**Query Parameters:**
- `page`, `limit`: Pagination
- `status`: Filter by status ('active', 'expired', 'cancelled', 'all')
- `severity`: Filter by severity ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', 'all')
- `sort_by`: Sort field ('sent_at', 'severity', 'expires_at')
- `order`: Sort order ('asc', 'desc')

**Response (200):**
```json
{
  "broadcasts": [
    {
      "id": 1,
      "broadcast_id": "BCAST-20251003-113000",
      "title": "Emergency Weather Alert",
      "message": "Severe thunderstorm warning. Seek indoor shelter immediately.",
      "severity": "HIGH",
      "broadcast_type": "RADIUS",
      "sent_at": "2025-10-03T11:30:00Z",
      "expires_at": "2025-10-03T18:00:00Z",
      "is_active": true,
      "sent_by": "Officer John Smith",
      "tourists_notified": 156,
      "acknowledgments": 89,
      "acknowledgment_rate": 57.1
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 8,
    "total_records": 156
  },
  "summary": {
    "active_broadcasts": 3,
    "total_today": 5,
    "high_severity": 2,
    "average_acknowledgment_rate": 62.5
  }
}
```

### 23. Get Broadcast Details
**GET** `/broadcasts/{broadcast_id}`

Get detailed information about a specific broadcast.

**Response (200):**
```json
{
  "broadcast": {
    "id": 1,
    "broadcast_id": "BCAST-20251003-113000",
    "title": "Emergency Weather Alert",
    "message": "Severe thunderstorm warning. Seek indoor shelter immediately.",
    "severity": "HIGH",
    "alert_type": "weather_warning",
    "action_required": "seek_shelter",
    "broadcast_type": "RADIUS",
    "sent_at": "2025-10-03T11:30:00Z",
    "expires_at": "2025-10-03T18:00:00Z",
    "is_active": true,
    "sent_by": "Officer John Smith",
    "require_acknowledgment": true
  },
  "targeting": {
    "broadcast_type": "RADIUS",
    "center": {"lat": 40.7589, "lon": -73.9851},
    "radius_km": 5.0,
    "tourists_in_area": 156
  },
  "delivery_stats": {
    "tourists_targeted": 156,
    "push_notifications": {"sent": 145, "delivered": 142, "failed": 3},
    "sms_notifications": {"sent": 142, "delivered": 138, "failed": 4},
    "total_delivery_rate": 92.3,
    "delivery_time_avg_seconds": 12.5
  },
  "acknowledgments": {
    "total_required": 156,
    "total_received": 89,
    "acknowledgment_rate": 57.1,
    "status_breakdown": {
      "safe": 75,
      "need_help": 8,
      "relocated": 6
    },
    "response_time_avg_minutes": 8.5
  },
  "timeline": [
    {
      "timestamp": "2025-10-03T11:30:00Z",
      "event": "broadcast_created",
      "details": "Broadcast created and queued for delivery"
    },
    {
      "timestamp": "2025-10-03T11:30:15Z",
      "event": "delivery_started",
      "details": "Started sending notifications to 156 tourists"
    },
    {
      "timestamp": "2025-10-03T11:31:00Z",
      "event": "delivery_completed",
      "details": "Notification delivery completed with 92.3% success rate"
    }
  ]
}
```

### 24. Update Broadcast
**PUT** `/broadcasts/{broadcast_id}`

Update an active broadcast.

**Request Body:**
```json
{
  "message": "Updated: Severe thunderstorm warning continues. Shelter remains advised until 6 PM.",
  "expires_at": "2025-10-03T18:30:00Z",
  "severity": "CRITICAL"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Broadcast updated successfully",
  "broadcast": {
    "id": 1,
    "broadcast_id": "BCAST-20251003-113000",
    "message": "Updated: Severe thunderstorm warning continues...",
    "severity": "CRITICAL",
    "expires_at": "2025-10-03T18:30:00Z",
    "updated_by": "Officer John Smith",
    "updated_at": "2025-10-03T12:00:00Z"
  },
  "update_notifications": {
    "tourists_notified": 145,
    "delivery_success": true
  }
}
```

### 25. Cancel Broadcast
**DELETE** `/broadcasts/{broadcast_id}`

Cancel an active broadcast.

**Request Body:**
```json
{
  "cancellation_reason": "Weather alert no longer valid - storm has passed",
  "send_cancellation_notice": true
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Broadcast cancelled successfully",
  "broadcast": {
    "id": 1,
    "broadcast_id": "BCAST-20251003-113000",
    "status": "cancelled",
    "cancelled_by": "Officer John Smith",
    "cancelled_at": "2025-10-03T15:30:00Z",
    "cancellation_reason": "Weather alert no longer valid - storm has passed"
  },
  "cancellation_notice": {
    "sent": true,
    "tourists_notified": 142,
    "delivery_rate": 98.6
  }
}
```

### 26. Get Broadcast Acknowledgments
**GET** `/broadcasts/{broadcast_id}/acknowledgments`

Get all acknowledgments for a specific broadcast.

**Response (200):**
```json
{
  "broadcast": {
    "id": 1,
    "broadcast_id": "BCAST-20251003-113000",
    "title": "Emergency Weather Alert"
  },
  "acknowledgment_summary": {
    "total_required": 156,
    "total_received": 89,
    "acknowledgment_rate": 57.1,
    "pending": 67
  },
  "acknowledgments": [
    {
      "id": 1,
      "tourist": {
        "id": "tourist-uuid",
        "name": "John Doe",
        "phone": "+1234567890"
      },
      "status": "safe",
      "notes": "I am in a safe indoor location",
      "location": {
        "lat": 40.7589,
        "lon": -73.9851,
        "timestamp": "2025-10-03T11:45:00Z"
      },
      "acknowledged_at": "2025-10-03T11:45:00Z",
      "response_time_minutes": 15.0
    }
  ],
  "status_breakdown": {
    "safe": 75,
    "need_help": 8,
    "relocated": 6
  },
  "unacknowledged_tourists": 67,
  "average_response_time_minutes": 8.5
}
```

---

## 📋 E-FIR Management

### 27. Get All E-FIRs
**GET** `/efirs?page=1&limit=20&status=all&sort_by=generated_at&order=desc`

Get all E-FIRs with filtering.

**Query Parameters:**
- `page`, `limit`: Pagination
- `status`: Filter by status ('pending_verification', 'verified', 'rejected', 'all')
- `incident_type`: Filter by type ('theft', 'harassment', 'assault', 'vandalism', 'other', 'all')
- `severity`: Filter by severity ('low', 'medium', 'high', 'critical', 'all')
- `sort_by`: Sort field ('generated_at', 'incident_timestamp', 'severity')
- `order`: Sort order ('asc', 'desc')

**Response (200):**
```json
{
  "efirs": [
    {
      "efir_id": 123,
      "fir_number": "EFIR-20251003-T12345678-1696334400",
      "incident_type": "harassment",
      "severity": "medium",
      "status": "pending_verification",
      "tourist": {
        "id": "tourist-uuid",
        "name": "John Doe",
        "phone": "+1234567890"
      },
      "location": {
        "lat": 40.7589,
        "lon": -73.9851,
        "description": "Central Park, near fountain"
      },
      "incident_timestamp": "2025-10-03T10:30:00Z",
      "generated_at": "2025-10-03T10:35:00Z",
      "blockchain_tx_id": "0x1234567890abcdef...",
      "is_verified": false,
      "requires_followup": true
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 12,
    "total_records": 234
  },
  "summary": {
    "pending_verification": 45,
    "verified": 178,
    "rejected": 11,
    "total": 234,
    "recent_24h": 8
  }
}
```

### 28. Get E-FIR Details
**GET** `/efirs/{efir_id}`

Get detailed information about a specific E-FIR.

**Response (200):**
```json
{
  "efir": {
    "efir_id": 123,
    "fir_number": "EFIR-20251003-T12345678-1696334400",
    "incident_type": "harassment",
    "severity": "medium",
    "status": "pending_verification",
    "description": "Harassment by unknown individual at Central Park",
    "location": {
      "lat": 40.7589,
      "lon": -73.9851,
      "description": "Central Park, near fountain"
    },
    "tourist_info": {
      "id": "tourist-uuid",
      "name": "John Doe",
      "email": "tourist@example.com",
      "phone": "+1234567890"
    },
    "incident_details": {
      "suspect_description": "Male, approximately 30 years old, wearing blue jacket",
      "witness_details": "Two witnesses present",
      "witnesses": ["Witness 1", "Witness 2"],
      "additional_details": "Incident lasted approximately 5 minutes"
    },
    "incident_timestamp": "2025-10-03T10:30:00Z",
    "generated_at": "2025-10-03T10:35:00Z",
    "blockchain": {
      "tx_id": "0x1234567890abcdef...",
      "block_hash": "block_1234567890abcdef...",
      "chain_id": "safehorizon-efir-chain",
      "verification_url": "/api/blockchain/verify/0x1234567890abcdef..."
    },
    "verification_status": {
      "is_verified": false,
      "verified_by": null,
      "verification_timestamp": null,
      "verification_notes": null
    },
    "followup_required": true,
    "assigned_to": null,
    "report_source": "tourist"
  },
  "related_alerts": [
    {
      "alert_id": 789,
      "alert_type": "manual",
      "tourist_id": "tourist-uuid",
      "timestamp": "2025-10-03T10:30:00Z",
      "location": {"lat": 40.7589, "lon": -73.9851}
    }
  ],
  "investigation_timeline": [
    {
      "timestamp": "2025-10-03T10:35:00Z",
      "event": "efir_generated",
      "details": "E-FIR automatically generated from tourist report",
      "user": "system"
    }
  ]
}
```

### 29. Verify E-FIR
**POST** `/efirs/{efir_id}/verify`

Verify an E-FIR after investigation.

**Request Body:**
```json
{
  "verification_status": "verified",
  "verification_notes": "Investigation completed. Incident confirmed with witness statements.",
  "severity_adjustment": "high",
  "follow_up_actions": [
    "case_assigned_to_detective",
    "victim_contacted_for_statement"
  ],
  "case_reference": "CASE-2025-1003-001"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "E-FIR verified successfully",
  "efir": {
    "efir_id": 123,
    "fir_number": "EFIR-20251003-T12345678-1696334400",
    "status": "verified",
    "severity": "high",
    "verified_by": "Officer John Smith",
    "verification_timestamp": "2025-10-03T14:30:00Z",
    "verification_notes": "Investigation completed. Incident confirmed with witness statements.",
    "case_reference": "CASE-2025-1003-001"
  },
  "blockchain_update": {
    "verification_tx_id": "0xabcdef1234567890...",
    "status": "blockchain_updated"
  }
}
```

### 30. Reject E-FIR
**POST** `/efirs/{efir_id}/reject`

Reject an E-FIR if found invalid.

**Request Body:**
```json
{
  "rejection_reason": "insufficient_evidence",
  "rejection_notes": "Unable to verify incident details. No corroborating evidence found.",
  "follow_up_required": false
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "E-FIR rejected",
  "efir": {
    "efir_id": 123,
    "status": "rejected",
    "rejected_by": "Officer John Smith",
    "rejection_timestamp": "2025-10-03T14:30:00Z",
    "rejection_reason": "insufficient_evidence",
    "rejection_notes": "Unable to verify incident details. No corroborating evidence found."
  }
}
```

### 31. Assign E-FIR
**POST** `/efirs/{efir_id}/assign`

Assign an E-FIR to an officer for investigation.

**Request Body:**
```json
{
  "assigned_to": "auth-uuid-officer-2",
  "priority": "high",
  "assignment_notes": "Requires immediate investigation due to severity",
  "deadline": "2025-10-05T17:00:00Z"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "E-FIR assigned successfully",
  "assignment": {
    "efir_id": 123,
    "assigned_to": "Officer Jane Smith",
    "assigned_by": "Officer John Smith",
    "assigned_at": "2025-10-03T15:00:00Z",
    "priority": "high",
    "deadline": "2025-10-05T17:00:00Z"
  }
}
```

---

## 🔍 Search & Analytics

### 32. Advanced Tourist Search
**POST** `/search/tourists/advanced`

Advanced search with multiple criteria and AI-powered filtering.

**Request Body:**
```json
{
  "criteria": {
    "safety_score_range": {"min": 60.0, "max": 90.0},
    "location_area": {
      "center": {"lat": 40.7589, "lon": -73.9851},
      "radius_km": 5.0
    },
    "time_range": {
      "start": "2025-10-03T00:00:00Z",
      "end": "2025-10-03T23:59:59Z"
    },
    "risk_factors": ["low_safety_score", "isolated_location", "after_hours"],
    "alert_history": {"has_alerts": true, "alert_count_min": 1}
  },
  "ai_analysis": {
    "predict_risk": true,
    "anomaly_detection": true,
    "behavioral_analysis": true
  },
  "sort": {
    "primary": "risk_score",
    "secondary": "safety_score",
    "order": "desc"
  }
}
```

**Response (200):**
```json
{
  "search_results": [
    {
      "tourist": {
        "id": "tourist-uuid",
        "name": "John Doe",
        "safety_score": 65.2,
        "risk_level": "medium"
      },
      "ai_analysis": {
        "risk_score": 75.5,
        "risk_factors": ["isolated_location", "below_average_safety_score"],
        "anomalies_detected": ["unusual_movement_pattern"],
        "recommendations": ["increase_monitoring", "send_safety_check"]
      },
      "location": {
        "lat": 40.7500,
        "lon": -73.9800,
        "last_seen": "2025-10-03T14:30:00Z",
        "distance_from_center_km": 1.2
      }
    }
  ],
  "search_metadata": {
    "total_found": 23,
    "high_risk": 5,
    "medium_risk": 12,
    "low_risk": 6,
    "ai_processing_time_ms": 245
  }
}
```

### 33. Get Analytics Dashboard
**GET** `/analytics/dashboard?time_range=24h&include_predictions=true`

Get comprehensive analytics for authority dashboard.

**Query Parameters:**
- `time_range`: Time range for analysis ('1h', '24h', '7d', '30d')
- `include_predictions`: Include AI predictions (default: true)

**Response (200):**
```json
{
  "time_range": "24h",
  "overview": {
    "total_tourists": 1247,
    "active_tourists": 342,
    "safety_alerts": 23,
    "emergency_alerts": 5,
    "zones_monitored": 48,
    "average_safety_score": 78.4
  },
  "trends": {
    "tourist_activity": {
      "current_hour": 342,
      "peak_hour": 456,
      "peak_time": "2025-10-03T15:00:00Z",
      "hourly_breakdown": [/* 24 data points */]
    },
    "safety_scores": {
      "current_average": 78.4,
      "24h_change": -2.1,
      "trend": "declining",
      "score_distribution": {
        "90-100": 123,
        "80-89": 234,
        "70-79": 156,
        "60-69": 89,
        "below_60": 45
      }
    },
    "alert_patterns": {
      "total_24h": 23,
      "by_type": {"sos": 5, "anomaly": 15, "manual": 3},
      "by_severity": {"critical": 2, "high": 8, "medium": 10, "low": 3},
      "hourly_distribution": [/* 24 data points */]
    }
  },
  "geographic_analysis": {
    "hotspots": [
      {
        "area": "Central Park",
        "tourist_count": 89,
        "average_safety_score": 82.1,
        "alert_count": 2,
        "risk_level": "low"
      }
    ],
    "risk_areas": [
      {
        "area": "Construction Zone A",
        "tourist_count": 12,
        "average_safety_score": 58.3,
        "alert_count": 8,
        "risk_level": "high"
      }
    ]
  },
  "ai_insights": {
    "predictions": {
      "next_hour_risk_level": "medium",
      "expected_alert_count": 3,
      "high_risk_tourists": 15
    },
    "recommendations": [
      "Increase patrol frequency in Construction Zone A",
      "Monitor tourists with safety scores below 60",
      "Weather alert may be needed for evening hours"
    ],
    "anomalies_detected": 12
  },
  "generated_at": "2025-10-03T15:30:00Z"
}
```

### 34. Export Report
**POST** `/analytics/export`

Export analytics report in various formats.

**Request Body:**
```json
{
  "report_type": "comprehensive",
  "time_range": {
    "start": "2025-10-01T00:00:00Z",
    "end": "2025-10-03T23:59:59Z"
  },
  "include_sections": [
    "overview",
    "tourist_analytics",
    "alert_analysis",
    "zone_statistics",
    "safety_trends",
    "ai_insights"
  ],
  "format": "pdf",
  "include_charts": true,
  "detail_level": "comprehensive"
}
```

**Response (200):**
```json
{
  "success": true,
  "report": {
    "report_id": "RPT-20251003-153000",
    "format": "pdf",
    "file_size_mb": 12.5,
    "download_url": "/api/reports/download/RPT-20251003-153000",
    "expires_at": "2025-10-10T15:30:00Z"
  },
  "summary": {
    "time_range": "3 days",
    "tourists_analyzed": 1247,
    "alerts_included": 89,
    "zones_covered": 48,
    "pages_generated": 45
  },
  "generated_at": "2025-10-03T15:30:00Z"
}
```

---

## 🗺️ Heatmap Data

### 35. Get Tourist Heatmap
**GET** `/heatmap/tourists?bounds_north=40.8&bounds_south=40.7&bounds_east=-73.9&bounds_west=-74.0&zoom_level=12`

Get tourist location heatmap data.

**Query Parameters:**
- `bounds_north`, `bounds_south`, `bounds_east`, `bounds_west`: Map bounds
- `zoom_level` (optional): Map zoom level for data density
- `time_range` (optional): Time range ('1h', '24h', '7d')

**Response (200):**
```json
{
  "heatmap_data": [
    {
      "lat": 40.7589,
      "lon": -73.9851,
      "density": 25,
      "safety_score_avg": 78.5,
      "tourist_count": 25,
      "risk_level": "low"
    }
  ],
  "bounds": {
    "north": 40.8,
    "south": 40.7,
    "east": -73.9,
    "west": -74.0
  },
  "statistics": {
    "total_points": 156,
    "max_density": 45,
    "avg_safety_score": 77.8,
    "total_tourists": 342
  },
  "generated_at": "2025-10-03T15:30:00Z"
}
```

### 36. Get Safety Heatmap
**GET** `/heatmap/safety?bounds_north=40.8&bounds_south=40.7&bounds_east=-73.9&bounds_west=-74.0`

Get safety score heatmap data.

**Response (200):**
```json
{
  "safety_heatmap": [
    {
      "lat": 40.7589,
      "lon": -73.9851,
      "safety_score": 78.5,
      "risk_level": "low",
      "data_points": 145,
      "confidence": 0.92
    }
  ],
  "risk_zones": [
    {
      "center": {"lat": 40.7500, "lon": -73.9800},
      "radius_meters": 200,
      "risk_level": "high",
      "safety_score": 45.2,
      "alert_count": 15
    }
  ],
  "statistics": {
    "avg_safety_score": 77.8,
    "risk_areas_count": 8,
    "safe_areas_count": 23,
    "data_coverage": 95.2
  }
}
```

### 37. Get Alert Heatmap
**GET** `/heatmap/alerts?time_range=24h&alert_types=all&severity=all`

Get alert density heatmap data.

**Query Parameters:**
- `time_range`: Time range for alerts ('1h', '24h', '7d', '30d')
- `alert_types`: Filter by types ('sos', 'anomaly', 'manual', 'all')
- `severity`: Filter by severity ('low', 'medium', 'high', 'critical', 'all')

**Response (200):**
```json
{
  "alert_heatmap": [
    {
      "lat": 40.7589,
      "lon": -73.9851,
      "alert_count": 8,
      "severity_breakdown": {
        "critical": 1,
        "high": 2,
        "medium": 3,
        "low": 2
      },
      "alert_density": "medium",
      "predominant_type": "anomaly"
    }
  ],
  "hotspots": [
    {
      "center": {"lat": 40.7500, "lon": -73.9800},
      "radius_meters": 300,
      "alert_count": 15,
      "risk_rating": "high",
      "requires_attention": true
    }
  ],
  "time_range": "24h",
  "total_alerts": 89,
  "generated_at": "2025-10-03T15:30:00Z"
}
```

---

## 🔄 Real-time Features

### 38. WebSocket Connection
**WebSocket** `/authority/ws?token=<jwt-token>`

Real-time WebSocket connection for live updates.

**Connection URL:** `ws://localhost:8000/api/authority/ws?token=<jwt-token>`

**Incoming Message Types:**
```json
{
  "type": "new_alert",
  "data": {
    "alert_id": 789,
    "alert_type": "sos",
    "severity": "critical",
    "tourist_id": "tourist-uuid",
    "location": {"lat": 40.7589, "lon": -73.9851},
    "timestamp": "2025-10-03T15:30:00Z"
  }
}

{
  "type": "tourist_location_update",
  "data": {
    "tourist_id": "tourist-uuid",
    "location": {"lat": 40.7589, "lon": -73.9851},
    "safety_score": 78.5,
    "timestamp": "2025-10-03T15:30:00Z"
  }
}

{
  "type": "broadcast_acknowledgment",
  "data": {
    "broadcast_id": "BCAST-20251003-113000",
    "tourist_id": "tourist-uuid",
    "status": "safe",
    "timestamp": "2025-10-03T15:30:00Z"
  }
}
```

### 39. Send Real-time Command
**POST** `/realtime/command`

Send real-time commands through WebSocket.

**Request Body:**
```json
{
  "command_type": "update_patrol_status",
  "target": "all_officers",
  "data": {
    "area": "Central Park",
    "status": "increased_patrol",
    "duration_minutes": 120,
    "priority": "high"
  }
}
```

**Response (200):**
```json
{
  "success": true,
  "command_id": "CMD-20251003-153000",
  "message": "Command sent successfully",
  "targets_reached": 15,
  "delivery_time_ms": 234
}
```

---

## 🔐 Role-based Access Control

All authority endpoints require:
- Valid JWT token with `authority` role
- Proper department authorization for sensitive operations
- Rate limiting: 100 requests per minute for most endpoints

**Authentication Header:**
```
Authorization: Bearer <authority-jwt-token>
```

---

## 📊 Response Codes

- **200 OK**: Request successful
- **201 Created**: Resource created successfully
- **400 Bad Request**: Invalid request data
- **401 Unauthorized**: Authentication required or invalid token
- **403 Forbidden**: Insufficient authority permissions
- **404 Not Found**: Resource not found
- **422 Unprocessable Entity**: Validation error
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server error

---

## 🚀 Performance & Scalability

- **Caching**: Redis-based caching for frequently accessed data
- **Real-time**: WebSocket connections for live updates
- **Pagination**: All list endpoints support pagination
- **Rate Limiting**: Configured per endpoint type
- **Database**: Optimized queries with proper indexing
- **AI Integration**: Background processing for heavy AI operations

---

**🎯 Authority Dashboard Ready**  
All endpoints are optimized for real-time authority monitoring and emergency response operations.