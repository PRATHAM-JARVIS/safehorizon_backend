from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, and_

from ..database import get_db
from ..auth.local_auth_utils import (
    authenticate_user, create_user_account, get_current_authority, AuthUser
)
from ..models.database_models import (
    Tourist, Location, Alert, RestrictedZone, Authority, Incident, EFIR,
    AlertType, AlertSeverity, ZoneType, Trip, TripStatus
)
from ..services.websocket_manager import websocket_manager
from ..services.geofence import create_zone, get_all_zones, delete_zone
from ..services.blockchain import generate_efir

router = APIRouter()


class AuthorityRegisterRequest(BaseModel):
    email: str
    password: str
    name: str
    badge_number: str
    department: str
    rank: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class IncidentRequest(BaseModel):
    alert_id: int
    notes: Optional[str] = None


class ZoneCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    zone_type: str  # "safe", "risky", "restricted"
    coordinates: List[List[float]]  # [[lon, lat], [lon, lat], ...]


class HeatmapRequest(BaseModel):
    bounds: Optional[Dict[str, float]] = None  # {"north": 35.7, "south": 35.6, "east": 139.8, "west": 139.6}
    hours_back: Optional[int] = 24
    include_zones: Optional[bool] = True
    include_alerts: Optional[bool] = True
    include_tourists: Optional[bool] = True


@router.post("/auth/register-authority")
async def register_authority(
    payload: AuthorityRegisterRequest, 
    db: AsyncSession = Depends(get_db)
):
    """Register a new police authority"""
    try:
        # Create authority account with all fields
        auth_response = await create_user_account(
            email=payload.email,
            password=payload.password,
            role="authority",
            name=payload.name,
            badge_number=payload.badge_number,
            department=payload.department,
            rank=payload.rank
        )
        
        user_id = auth_response["user"]["id"]
        
        return {
            "message": "Authority registered successfully",
            "user_id": user_id,
            "badge_number": payload.badge_number,
            "department": payload.department
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/auth/login-authority")
async def login_authority(payload: LoginRequest):
    """Login authority user"""
    try:
        auth_response = await authenticate_user(payload.email, payload.password, role="authority")
        return {
            "access_token": auth_response["access_token"],
            "token_type": "bearer",
            "user_id": auth_response["user_id"],
            "email": auth_response["email"],
            "role": auth_response["role"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )


@router.get("/tourists/active")
async def get_active_tourists(
    current_user: Authority = Depends(get_current_authority),
    db: AsyncSession = Depends(get_db)
):
    """Get list of active tourists"""
    # Get tourists who have been active in the last 24 hours
    cutoff_time = datetime.utcnow() - timedelta(hours=24)
    
    query = select(Tourist).where(
        Tourist.is_active == True,
        Tourist.last_seen >= cutoff_time
    ).order_by(desc(Tourist.last_seen))
    
    result = await db.execute(query)
    tourists = result.scalars().all()
    
    return [
        {
            "id": tourist.id,
            "name": tourist.name or tourist.email,
            "email": tourist.email,
            "safety_score": tourist.safety_score,
            "last_location": {
                "lat": tourist.last_location_lat,
                "lon": tourist.last_location_lon
            } if tourist.last_location_lat else None,
            "last_seen": tourist.last_seen.isoformat() if tourist.last_seen else None
        }
        for tourist in tourists
    ]


@router.get("/tourist/{tourist_id}/track")
async def track_tourist(
    tourist_id: str,
    current_user: Authority = Depends(get_current_authority),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed tracking information for a specific tourist"""
    # Get tourist info
    tourist_query = select(Tourist).where(Tourist.id == tourist_id)
    tourist_result = await db.execute(tourist_query)
    tourist = tourist_result.scalar_one_or_none()
    
    if not tourist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tourist not found"
        )
    
    # Get recent locations (last 6 hours)
    cutoff_time = datetime.utcnow() - timedelta(hours=6)
    locations_query = select(Location).where(
        Location.tourist_id == tourist_id,
        Location.timestamp >= cutoff_time
    ).order_by(desc(Location.timestamp)).limit(50)
    
    locations_result = await db.execute(locations_query)
    locations = locations_result.scalars().all()
    
    # Get recent alerts
    alerts_query = select(Alert).where(
        Alert.tourist_id == tourist_id,
        Alert.created_at >= cutoff_time
    ).order_by(desc(Alert.created_at))
    
    alerts_result = await db.execute(alerts_query)
    alerts = alerts_result.scalars().all()
    
    return {
        "tourist": {
            "id": tourist.id,
            "name": tourist.name or tourist.email,
            "email": tourist.email,
            "phone": tourist.phone,
            "safety_score": tourist.safety_score,
            "last_seen": tourist.last_seen.isoformat() if tourist.last_seen else None
        },
        "locations": [
            {
                "id": loc.id,
                "lat": loc.latitude,
                "lon": loc.longitude,
                "speed": loc.speed,
                "altitude": loc.altitude,
                "timestamp": loc.timestamp.isoformat()
            }
            for loc in locations
        ],
        "recent_alerts": [
            {
                "id": alert.id,
                "type": alert.type.value,
                "severity": alert.severity.value,
                "title": alert.title,
                "description": alert.description,
                "is_acknowledged": alert.is_acknowledged,
                "created_at": alert.created_at.isoformat()
            }
            for alert in alerts
        ]
    }


@router.get("/tourist/{tourist_id}/alerts")
async def get_tourist_alerts(
    tourist_id: str,
    current_user: Authority = Depends(get_current_authority),
    db: AsyncSession = Depends(get_db)
):
    """Get all alerts for a specific tourist"""
    query = select(Alert).where(
        Alert.tourist_id == tourist_id
    ).order_by(desc(Alert.created_at))
    
    result = await db.execute(query)
    alerts = result.scalars().all()
    
    return [
        {
            "id": alert.id,
            "type": alert.type.value,
            "severity": alert.severity.value,
            "title": alert.title,
            "description": alert.description,
            "is_acknowledged": alert.is_acknowledged,
            "acknowledged_by": alert.acknowledged_by,
            "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
            "is_resolved": alert.is_resolved,
            "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
            "created_at": alert.created_at.isoformat()
        }
        for alert in alerts
    ]


@router.get("/tourist/{tourist_id}/profile")
async def get_tourist_profile(
    tourist_id: str,
    current_user: Authority = Depends(get_current_authority),
    db: AsyncSession = Depends(get_db)
):
    """Get complete tourist profile with all details for police monitoring"""
    # Get tourist
    tourist_query = select(Tourist).where(Tourist.id == tourist_id)
    tourist_result = await db.execute(tourist_query)
    tourist = tourist_result.scalar_one_or_none()
    
    if not tourist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tourist not found"
        )
    
    # Get active trip
    active_trip_query = select(Trip).where(
        Trip.tourist_id == tourist_id,
        Trip.status == TripStatus.ACTIVE
    ).order_by(desc(Trip.start_date))
    
    active_trip_result = await db.execute(active_trip_query)
    active_trip = active_trip_result.scalar_one_or_none()
    
    # Get total trips count
    trips_count_query = select(func.count(Trip.id)).where(Trip.tourist_id == tourist_id)
    trips_count_result = await db.execute(trips_count_query)
    trips_count = trips_count_result.scalar() or 0
    
    # Get total alerts count
    alerts_count_query = select(func.count(Alert.id)).where(Alert.tourist_id == tourist_id)
    alerts_count_result = await db.execute(alerts_count_query)
    alerts_count = alerts_count_result.scalar() or 0
    
    # Get unresolved alerts count
    unresolved_alerts_query = select(func.count(Alert.id)).where(
        Alert.tourist_id == tourist_id,
        Alert.is_resolved == False
    )
    unresolved_alerts_result = await db.execute(unresolved_alerts_query)
    unresolved_alerts_count = unresolved_alerts_result.scalar() or 0
    
    return {
        "tourist": {
            "id": tourist.id,
            "email": tourist.email,
            "name": tourist.name,
            "phone": tourist.phone,
            "emergency_contact": tourist.emergency_contact,
            "emergency_phone": tourist.emergency_phone,
            "safety_score": tourist.safety_score,
            "is_active": tourist.is_active,
            "last_location": {
                "lat": tourist.last_location_lat,
                "lon": tourist.last_location_lon
            } if tourist.last_location_lat else None,
            "last_seen": tourist.last_seen.isoformat() if tourist.last_seen else None,
            "created_at": tourist.created_at.isoformat(),
            "member_since_days": (datetime.utcnow() - tourist.created_at.replace(tzinfo=None)).days if tourist.created_at else 0
        },
        "current_trip": {
            "id": active_trip.id,
            "destination": active_trip.destination,
            "start_date": active_trip.start_date.isoformat() if active_trip.start_date else None,
            "itinerary": active_trip.itinerary,
            "duration_hours": (datetime.utcnow() - active_trip.start_date).total_seconds() / 3600 if active_trip.start_date else 0
        } if active_trip else None,
        "statistics": {
            "total_trips": trips_count,
            "total_alerts": alerts_count,
            "unresolved_alerts": unresolved_alerts_count,
            "safety_rating": "safe" if tourist.safety_score >= 70 else "caution" if tourist.safety_score >= 50 else "danger"
        }
    }


@router.get("/tourist/{tourist_id}/location/current")
async def get_tourist_current_location(
    tourist_id: str,
    current_user: Authority = Depends(get_current_authority),
    db: AsyncSession = Depends(get_db)
):
    """Get tourist's most recent/current location with real-time details"""
    # Get tourist
    tourist_query = select(Tourist).where(Tourist.id == tourist_id)
    tourist_result = await db.execute(tourist_query)
    tourist = tourist_result.scalar_one_or_none()
    
    if not tourist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tourist not found"
        )
    
    # Get most recent location
    location_query = select(Location).where(
        Location.tourist_id == tourist_id
    ).order_by(desc(Location.timestamp)).limit(1)
    
    location_result = await db.execute(location_query)
    location = location_result.scalar_one_or_none()
    
    if not location:
        return {
            "tourist_id": tourist_id,
            "tourist_name": tourist.name or tourist.email,
            "location": None,
            "message": "No location data available"
        }
    
    # Calculate time since last update
    time_diff = datetime.utcnow() - location.timestamp.replace(tzinfo=None)
    minutes_ago = int(time_diff.total_seconds() / 60)
    
    # Check if location is in restricted zone
    from ..services.geofence import check_point
    zone_check = await check_point(location.latitude, location.longitude)
    
    return {
        "tourist_id": tourist_id,
        "tourist_name": tourist.name or tourist.email,
        "safety_score": tourist.safety_score,
        "location": {
            "id": location.id,
            "latitude": location.latitude,
            "longitude": location.longitude,
            "altitude": location.altitude,
            "speed": location.speed,
            "accuracy": location.accuracy,
            "timestamp": location.timestamp.isoformat(),
            "minutes_ago": minutes_ago,
            "is_recent": minutes_ago < 10,
            "status": "live" if minutes_ago < 5 else "recent" if minutes_ago < 30 else "stale"
        },
        "zone_status": {
            "inside_restricted": zone_check.get("inside_restricted"),
            "risk_level": zone_check.get("risk_level"),
            "zones": zone_check.get("zones", [])
        },
        "last_seen": tourist.last_seen.isoformat() if tourist.last_seen else None
    }


@router.get("/tourist/{tourist_id}/location/history")
async def get_tourist_location_history(
    tourist_id: str,
    hours_back: int = 24,
    limit: int = 100,
    include_trip_info: bool = False,
    current_user: Authority = Depends(get_current_authority),
    db: AsyncSession = Depends(get_db)
):
    """Get tourist's location history with comprehensive filtering options"""
    # Verify tourist exists
    tourist_query = select(Tourist).where(Tourist.id == tourist_id)
    tourist_result = await db.execute(tourist_query)
    tourist = tourist_result.scalar_one_or_none()
    
    if not tourist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tourist not found"
        )
    
    # Calculate time threshold
    time_threshold = datetime.now(timezone.utc) - timedelta(hours=hours_back)
    
    # Build query
    if include_trip_info:
        locations_query = select(Location, Trip).outerjoin(
            Trip, Location.trip_id == Trip.id
        ).where(
            Location.tourist_id == tourist_id,
            Location.timestamp >= time_threshold
        ).order_by(desc(Location.timestamp)).limit(limit)
        
        locations_result = await db.execute(locations_query)
        locations_data = locations_result.all()
        
        locations_list = []
        for location, trip in locations_data:
            loc_data = {
                "id": location.id,
                "latitude": location.latitude,
                "longitude": location.longitude,
                "altitude": location.altitude,
                "speed": location.speed,
                "accuracy": location.accuracy,
                "timestamp": location.timestamp.isoformat(),
                "trip": {
                    "id": trip.id,
                    "destination": trip.destination,
                    "status": trip.status.value
                } if trip else None
            }
            locations_list.append(loc_data)
    else:
        locations_query = select(Location).where(
            Location.tourist_id == tourist_id,
            Location.timestamp >= time_threshold
        ).order_by(desc(Location.timestamp)).limit(limit)
        
        locations_result = await db.execute(locations_query)
        locations = locations_result.scalars().all()
        
        locations_list = [
            {
                "id": loc.id,
                "latitude": loc.latitude,
                "longitude": loc.longitude,
                "altitude": loc.altitude,
                "speed": loc.speed,
                "accuracy": loc.accuracy,
                "timestamp": loc.timestamp.isoformat()
            }
            for loc in locations
        ]
    
    # Calculate movement statistics
    total_distance = 0
    if len(locations_list) > 1:
        from ..services.geofence import _haversine_distance
        for i in range(len(locations_list) - 1):
            lat1 = locations_list[i]["latitude"]
            lon1 = locations_list[i]["longitude"]
            lat2 = locations_list[i + 1]["latitude"]
            lon2 = locations_list[i + 1]["longitude"]
            total_distance += _haversine_distance(lat1, lon1, lat2, lon2)
    
    return {
        "tourist_id": tourist_id,
        "tourist_name": tourist.name or tourist.email,
        "filter": {
            "hours_back": hours_back,
            "limit": limit,
            "time_from": time_threshold.isoformat(),
            "time_to": datetime.utcnow().isoformat()
        },
        "locations": locations_list,
        "statistics": {
            "total_points": len(locations_list),
            "distance_traveled_meters": round(total_distance, 2),
            "distance_traveled_km": round(total_distance / 1000, 2),
            "time_span_hours": hours_back
        }
    }


@router.get("/tourist/{tourist_id}/movement-analysis")
async def get_tourist_movement_analysis(
    tourist_id: str,
    hours_back: int = 24,
    current_user: Authority = Depends(get_current_authority),
    db: AsyncSession = Depends(get_db)
):
    """Analyze tourist's movement patterns for police assessment"""
    # Verify tourist exists
    tourist_query = select(Tourist).where(Tourist.id == tourist_id)
    tourist_result = await db.execute(tourist_query)
    tourist = tourist_result.scalar_one_or_none()
    
    if not tourist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tourist not found"
        )
    
    # Get locations
    time_threshold = datetime.utcnow() - timedelta(hours=hours_back)
    locations_query = select(Location).where(
        Location.tourist_id == tourist_id,
        Location.timestamp >= time_threshold
    ).order_by(Location.timestamp)
    
    locations_result = await db.execute(locations_query)
    locations = locations_result.scalars().all()
    
    if len(locations) < 2:
        return {
            "tourist_id": tourist_id,
            "message": "Insufficient location data for analysis",
            "data_points": len(locations)
        }
    
    # Calculate movement metrics
    from ..services.geofence import _haversine_distance
    
    speeds = []
    distances = []
    stationary_periods = 0
    
    for i in range(len(locations) - 1):
        loc1 = locations[i]
        loc2 = locations[i + 1]
        
        distance = _haversine_distance(
            loc1.latitude, loc1.longitude,
            loc2.latitude, loc2.longitude
        )
        distances.append(distance)
        
        time_diff = (loc2.timestamp - loc1.timestamp).total_seconds()
        if time_diff > 0:
            speed_mps = distance / time_diff
            speed_kmh = speed_mps * 3.6
            speeds.append(speed_kmh)
            
            # Check if stationary (moved less than 50m in 5+ minutes)
            if distance < 50 and time_diff > 300:
                stationary_periods += 1
    
    avg_speed = sum(speeds) / len(speeds) if speeds else 0
    max_speed = max(speeds) if speeds else 0
    total_distance = sum(distances)
    
    # Determine movement pattern
    if avg_speed < 5:
        movement_type = "mostly_stationary"
    elif avg_speed < 15:
        movement_type = "walking"
    elif avg_speed < 50:
        movement_type = "vehicle_city"
    else:
        movement_type = "vehicle_highway"
    
    return {
        "tourist_id": tourist_id,
        "tourist_name": tourist.name or tourist.email,
        "analysis_period": {
            "hours": hours_back,
            "from": time_threshold.isoformat(),
            "to": datetime.utcnow().isoformat()
        },
        "movement_metrics": {
            "total_distance_km": round(total_distance / 1000, 2),
            "average_speed_kmh": round(avg_speed, 2),
            "max_speed_kmh": round(max_speed, 2),
            "movement_type": movement_type,
            "data_points": len(locations),
            "stationary_periods": stationary_periods
        },
        "behavior_assessment": {
            "is_moving": avg_speed > 1,
            "unusual_speed": max_speed > 120,
            "mostly_stationary": stationary_periods > len(locations) * 0.3,
            "activity_level": "high" if len(locations) > 50 else "moderate" if len(locations) > 20 else "low"
        }
    }


@router.get("/tourist/{tourist_id}/safety-timeline")
async def get_tourist_safety_timeline(
    tourist_id: str,
    hours_back: int = 24,
    current_user: Authority = Depends(get_current_authority),
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive safety timeline including alerts, locations, and trips"""
    # Verify tourist exists
    tourist_query = select(Tourist).where(Tourist.id == tourist_id)
    tourist_result = await db.execute(tourist_query)
    tourist = tourist_result.scalar_one_or_none()
    
    if not tourist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tourist not found"
        )
    
    time_threshold = datetime.utcnow() - timedelta(hours=hours_back)
    
    # Get all alerts in timeframe
    alerts_query = select(Alert).where(
        Alert.tourist_id == tourist_id,
        Alert.created_at >= time_threshold
    ).order_by(Alert.created_at)
    
    alerts_result = await db.execute(alerts_query)
    alerts = alerts_result.scalars().all()
    
    # Get trips started/ended in timeframe
    trips_query = select(Trip).where(
        Trip.tourist_id == tourist_id,
        Trip.updated_at >= time_threshold
    ).order_by(Trip.updated_at)
    
    trips_result = await db.execute(trips_query)
    trips = trips_result.scalars().all()
    
    # Build timeline events
    timeline = []
    
    for alert in alerts:
        timeline.append({
            "timestamp": alert.created_at.isoformat(),
            "type": "alert",
            "event": alert.type.value,
            "severity": alert.severity.value,
            "title": alert.title,
            "description": alert.description,
            "is_resolved": alert.is_resolved
        })
    
    for trip in trips:
        if trip.start_date and trip.start_date >= time_threshold:
            timeline.append({
                "timestamp": trip.start_date.isoformat(),
                "type": "trip_start",
                "event": "trip_started",
                "destination": trip.destination,
                "trip_id": trip.id
            })
        
        if trip.end_date and trip.end_date >= time_threshold:
            timeline.append({
                "timestamp": trip.end_date.isoformat(),
                "type": "trip_end",
                "event": "trip_completed",
                "destination": trip.destination,
                "trip_id": trip.id
            })
    
    # Sort timeline by timestamp
    timeline.sort(key=lambda x: x["timestamp"])
    
    return {
        "tourist_id": tourist_id,
        "tourist_name": tourist.name or tourist.email,
        "current_safety_score": tourist.safety_score,
        "period": {
            "hours": hours_back,
            "from": time_threshold.isoformat(),
            "to": datetime.utcnow().isoformat()
        },
        "timeline": timeline,
        "summary": {
            "total_events": len(timeline),
            "alerts_count": len(alerts),
            "critical_alerts": sum(1 for a in alerts if a.severity == AlertSeverity.CRITICAL),
            "trips_count": len(trips),
            "unresolved_alerts": sum(1 for a in alerts if not a.is_resolved)
        }
    }


@router.get("/tourist/{tourist_id}/emergency-contacts")
async def get_tourist_emergency_contacts(
    tourist_id: str,
    current_user: Authority = Depends(get_current_authority),
    db: AsyncSession = Depends(get_db)
):
    """Get tourist's emergency contact information for police use"""
    # Get tourist
    tourist_query = select(Tourist).where(Tourist.id == tourist_id)
    tourist_result = await db.execute(tourist_query)
    tourist = tourist_result.scalar_one_or_none()
    
    if not tourist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tourist not found"
        )
    
    return {
        "tourist": {
            "id": tourist.id,
            "name": tourist.name,
            "email": tourist.email,
            "phone": tourist.phone
        },
        "emergency_contacts": [
            {
                "name": tourist.emergency_contact,
                "phone": tourist.emergency_phone,
                "relationship": "emergency_contact"
            }
        ] if tourist.emergency_contact and tourist.emergency_phone else [],
        "note": "This information should only be used in emergency situations"
    }


@router.get("/alerts/recent")
async def get_recent_alerts(
    hours: int = 24,
    current_user: Authority = Depends(get_current_authority),
    db: AsyncSession = Depends(get_db)
):
    """Get recent alerts across all tourists"""
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    query = select(Alert, Tourist).join(
        Tourist, Alert.tourist_id == Tourist.id
    ).where(
        Alert.created_at >= cutoff_time
    ).order_by(desc(Alert.created_at))
    
    result = await db.execute(query)
    alert_tourist_pairs = result.all()
    
    return [
        {
            "id": alert.id,
            "tourist": {
                "id": tourist.id,
                "name": tourist.name or tourist.email,
                "email": tourist.email
            },
            "type": alert.type.value,
            "severity": alert.severity.value,
            "title": alert.title,
            "description": alert.description,
            "is_acknowledged": alert.is_acknowledged,
            "is_resolved": alert.is_resolved,
            "created_at": alert.created_at.isoformat()
        }
        for alert, tourist in alert_tourist_pairs
    ]


@router.websocket("/alerts/subscribe")
async def alerts_subscribe(websocket: WebSocket, token: str):
    """Subscribe to real-time alerts via WebSocket"""
    try:
        # Manually verify JWT token (dependency injection doesn't work well with WebSockets)
        from ..auth.local_auth import local_auth
        from ..database import AsyncSessionLocal
        
        try:
            # Verify the token
            payload = local_auth.verify_token(token)
            user_id = payload.get("sub")
            email = payload.get("email")
            role = payload.get("role", "tourist")
            
            if not user_id or not email:
                await websocket.close(code=1008, reason="Invalid token payload")
                return
            
            # Check if user has authority permissions
            if role not in ["authority", "admin"]:
                await websocket.close(code=1008, reason="Access denied: Authority role required")
                return
            
        except ValueError as e:
            # Invalid token
            await websocket.close(code=1008, reason=f"Invalid token: {str(e)}")
            return
        except Exception as e:
            # Other authentication errors
            await websocket.close(code=1008, reason=f"Authentication failed: {str(e)}")
            return
        
        # Verify user exists in database
        async with AsyncSessionLocal() as db:
            if role == "authority":
                result = await db.execute(select(Authority).where(Authority.id == user_id))
                user_record = result.scalar_one_or_none()
                if not user_record:
                    # Accept connection first, then close with proper message
                    await websocket.accept()
                    await websocket.close(code=1008, reason="Authority not found")
                    return
            # Admin users don't need to be in Authority table
            
            user_data = {
                "user_id": user_id,
                "email": email,
                "role": role
            }
            
            # Let websocket_manager handle the accept and connection management
            await websocket_manager.connect(websocket, "authority", user_data)
            
            # Keep connection alive
            while True:
                # Receive heartbeat or other messages
                data = await websocket.receive_text()
                
                # Echo heartbeat back
                if data == "ping":
                    await websocket.send_text("pong")
                
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)


@router.post("/incident/acknowledge")
async def acknowledge_incident(
    payload: IncidentRequest,
    current_user: Authority = Depends(get_current_authority),
    db: AsyncSession = Depends(get_db)
):
    """Acknowledge an incident/alert"""
    # Get the alert
    alert_query = select(Alert).where(Alert.id == payload.alert_id)
    alert_result = await db.execute(alert_query)
    alert = alert_result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    # Update alert acknowledgment
    alert.is_acknowledged = True
    alert.acknowledged_by = current_user.id
    alert.acknowledged_at = datetime.utcnow()
    
    # Create or update incident record
    incident_query = select(Incident).where(Incident.alert_id == payload.alert_id)
    incident_result = await db.execute(incident_query)
    incident = incident_result.scalar_one_or_none()
    
    if not incident:
        # Generate incident number
        incident_number = f"INC-{datetime.utcnow().strftime('%Y%m%d')}-{payload.alert_id:06d}"
        
        incident = Incident(
            alert_id=payload.alert_id,
            incident_number=incident_number,
            assigned_to=current_user.id,
            response_time=datetime.utcnow()
        )
        db.add(incident)
    else:
        incident.assigned_to = current_user.id
        incident.response_time = datetime.utcnow()
    
    if payload.notes:
        incident.resolution_notes = payload.notes
    
    await db.commit()
    
    return {
        "status": "acknowledged",
        "alert_id": payload.alert_id,
        "incident_number": incident.incident_number,
        "acknowledged_by": current_user.id,
        "acknowledged_at": alert.acknowledged_at.isoformat()
    }


@router.post("/incident/close")
async def close_incident(
    payload: IncidentRequest,
    current_user: Authority = Depends(get_current_authority),
    db: AsyncSession = Depends(get_db)
):
    """Close an incident"""
    # Get incident
    incident_query = select(Incident).where(Incident.alert_id == payload.alert_id)
    incident_result = await db.execute(incident_query)
    incident = incident_result.scalar_one_or_none()
    
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found"
        )
    
    # Update incident
    incident.status = "closed"
    if payload.notes:
        incident.resolution_notes = payload.notes
    
    # Update associated alert
    alert_query = select(Alert).where(Alert.id == payload.alert_id)
    alert_result = await db.execute(alert_query)
    alert = alert_result.scalar_one_or_none()
    
    if alert:
        alert.is_resolved = True
        alert.resolved_at = datetime.utcnow()
    
    await db.commit()
    
    return {
        "status": "closed",
        "incident_number": incident.incident_number,
        "closed_at": datetime.utcnow().isoformat()
    }


@router.post("/authority/efir/generate")
async def generate_efir_record(
    payload: IncidentRequest,
    current_user: Authority = Depends(get_current_authority),
    db: AsyncSession = Depends(get_db)
):
    """Generate E-FIR (Electronic First Information Report) on blockchain"""
    # Get incident details
    incident_query = select(Incident, Alert, Tourist).join(
        Alert, Incident.alert_id == Alert.id
    ).join(
        Tourist, Alert.tourist_id == Tourist.id
    ).where(Incident.alert_id == payload.alert_id)
    
    incident_result = await db.execute(incident_query)
    result = incident_result.first()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found"
        )
    
    incident, alert, tourist = result
    
    # Check if E-FIR already exists for this incident
    existing_efir = await db.execute(
        select(EFIR).where(EFIR.incident_id == incident.id)
    )
    if existing_efir.scalar():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="E-FIR already exists for this incident"
        )
    
    # Prepare E-FIR data for blockchain
    efir_data = {
        "incident_number": incident.incident_number,
        "alert_type": alert.type.value,
        "severity": alert.severity.value,
        "tourist_id": tourist.id,
        "tourist_name": tourist.name or tourist.email,
        "location": {
            "lat": tourist.last_location_lat,
            "lon": tourist.last_location_lon
        } if tourist.last_location_lat else None,
        "reported_by": current_user.id,
        "timestamp": datetime.utcnow().isoformat(),
        "description": alert.description,
        "resolution_notes": incident.resolution_notes
    }
    
    # Generate E-FIR on blockchain
    blockchain_result = await generate_efir(efir_data)
    tx_id = blockchain_result.get("tx_id")
    block_hash = blockchain_result.get("block_hash")
    
    # Generate E-FIR number
    now = datetime.utcnow()
    efir_count = await db.execute(
        select(func.count(EFIR.id)).where(
            func.date(EFIR.generated_at) == now.date()
        )
    )
    daily_count = efir_count.scalar() or 0
    efir_number = f"EFIR-{now.strftime('%Y%m%d')}-{daily_count + 1:05d}"
    
    # Create E-FIR record in database
    new_efir = EFIR(
        efir_number=efir_number,
        incident_id=incident.id,
        alert_id=alert.id,
        tourist_id=tourist.id,
        blockchain_tx_id=tx_id,
        block_hash=block_hash,
        chain_id="safehorizon-efir-chain",
        incident_type=alert.type.value,
        severity=alert.severity.value,
        description=alert.description or "No description provided",
        location_lat=tourist.last_location_lat,
        location_lon=tourist.last_location_lon,
        tourist_name=tourist.name or "Unknown",
        tourist_email=tourist.email,
        tourist_phone=tourist.phone,
        reported_by=current_user.id,
        officer_name=current_user.name,
        officer_badge=current_user.badge_number,
        officer_department=current_user.department,
        officer_notes=payload.notes,
        incident_timestamp=alert.created_at,
        is_verified=True,
        verification_timestamp=datetime.utcnow()
    )
    
    db.add(new_efir)
    
    # Also update incident with blockchain reference (backward compatibility)
    incident.efir_reference = tx_id
    
    await db.commit()
    await db.refresh(new_efir)
    
    return {
        "status": "efir_generated",
        "efir_number": efir_number,
        "efir_id": new_efir.id,
        "incident_number": incident.incident_number,
        "blockchain_tx": tx_id,
        "block_hash": block_hash,
        "efir_data": efir_data,
        "generated_at": new_efir.generated_at.isoformat()
    }


@router.get("/authority/efir/list")
async def list_efir_records(
    limit: int = 100,
    offset: int = 0,
    report_source: Optional[str] = None,  # 'tourist' or 'authority'
    status: Optional[str] = None,
    is_verified: Optional[bool] = None,
    current_user: Authority = Depends(get_current_authority),
    db: AsyncSession = Depends(get_db)
):
    """Get list of all E-FIR records with filtering options"""
    import json
    
    # Build query - join with incident only if incident_id is not null
    query = select(EFIR).outerjoin(
        Incident, EFIR.incident_id == Incident.id
    )
    
    # Apply filters
    if report_source:
        query = query.where(EFIR.report_source == report_source)
    
    if is_verified is not None:
        query = query.where(EFIR.is_verified == is_verified)
    
    if status:
        query = query.where(Incident.status == status)
    
    # Add ordering and pagination
    query = query.order_by(desc(EFIR.generated_at)).offset(offset).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    efirs = result.scalars().all()
    
    # Get total count for pagination
    count_query = select(func.count(EFIR.id))
    if report_source:
        count_query = count_query.where(EFIR.report_source == report_source)
    if is_verified is not None:
        count_query = count_query.where(EFIR.is_verified == is_verified)
    if status:
        count_query = count_query.join(Incident, EFIR.incident_id == Incident.id).where(Incident.status == status)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Format response
    efir_list = []
    for efir in efirs:
        # Get incident info if exists
        incident_info = None
        if efir.incident_id:
            incident_query = select(Incident).where(Incident.id == efir.incident_id)
            incident_result = await db.execute(incident_query)
            incident = incident_result.scalar_one_or_none()
            if incident:
                incident_info = {
                    "incident_number": incident.incident_number,
                    "incident_id": incident.id,
                    "status": incident.status,
                    "priority": incident.priority,
                    "assigned_to": incident.assigned_to,
                    "response_time": incident.response_time.isoformat() if incident.response_time else None,
                    "resolution_notes": incident.resolution_notes,
                    "created_at": incident.created_at.isoformat(),
                    "updated_at": incident.updated_at.isoformat() if incident.updated_at else None
                }
        
        efir_data = {
            "efir_id": efir.id,
            "fir_number": efir.efir_number,
            "blockchain_tx_id": efir.blockchain_tx_id,
            "block_hash": efir.block_hash,
            "chain_id": efir.chain_id,
            "report_source": efir.report_source,
            "alert_id": efir.alert_id,
            "incident_type": efir.incident_type,
            "severity": efir.severity,
            "description": efir.description,
            "tourist": {
                "id": efir.tourist_id,
                "name": efir.tourist_name,
                "email": efir.tourist_email,
                "phone": efir.tourist_phone
            },
            "location": {
                "lat": efir.location_lat,
                "lon": efir.location_lon,
                "description": efir.location_description
            } if efir.location_lat or efir.location_description else None,
            "officer": {
                "id": efir.reported_by,
                "name": efir.officer_name,
                "badge": efir.officer_badge,
                "department": efir.officer_department
            } if efir.reported_by else None,
            "officer_notes": efir.officer_notes,
            "witnesses": json.loads(efir.witnesses) if efir.witnesses else [],
            "evidence": json.loads(efir.evidence) if efir.evidence else [],
            "is_verified": efir.is_verified,
            "verification_timestamp": efir.verification_timestamp.isoformat() if efir.verification_timestamp else None,
            "incident_timestamp": efir.incident_timestamp.isoformat(),
            "generated_at": efir.generated_at.isoformat(),
            "incident": incident_info
        }
        efir_list.append(efir_data)
    
    return {
        "success": True,
        "efir_records": efir_list,
        "pagination": {
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total
        },
        "filters": {
            "report_source": report_source,
            "status": status,
            "is_verified": is_verified
        }
    }


@router.get("/zones/manage")
async def list_zones_for_management(
    current_user: AuthUser = Depends(get_current_authority)
):
    """Get list of all restricted zones for management"""
    return await get_all_zones()


@router.post("/zones/create")
async def create_restricted_zone(
    payload: ZoneCreateRequest,
    current_user: Authority = Depends(get_current_authority)
):
    """Create a new restricted zone"""
    # Validate zone type
    if payload.zone_type.lower() not in ['safe', 'risky', 'restricted']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid zone type. Must be 'safe', 'risky', or 'restricted'"
        )
    
    result = await create_zone(
        name=payload.name,
        description=payload.description or "",
        zone_type=payload.zone_type.lower(),  # Pass as string
        coordinates=payload.coordinates,
        created_by=current_user.id
    )
    
    return result


@router.delete("/zones/{zone_id}")
async def delete_restricted_zone(
    zone_id: int,
    current_user: Authority = Depends(get_current_authority)
):
    """Delete a restricted zone"""
    success = await delete_zone(zone_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zone not found"
        )
    
    return {"status": "zone_deleted", "id": zone_id}


@router.get("/heatmap/data")
async def get_heatmap_data(
    bounds_north: Optional[float] = None,
    bounds_south: Optional[float] = None,
    bounds_east: Optional[float] = None,
    bounds_west: Optional[float] = None,
    hours_back: int = 24,
    include_zones: bool = True,
    include_alerts: bool = True,
    include_tourists: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: Authority = Depends(get_current_authority)
):
    """Get heatmap data including zones, alerts, and tourist locations"""
    
    # Calculate time threshold
    time_threshold = datetime.utcnow() - timedelta(hours=hours_back)
    
    heatmap_data = {
        "metadata": {
            "bounds": {
                "north": bounds_north,
                "south": bounds_south,
                "east": bounds_east,
                "west": bounds_west
            } if all([bounds_north, bounds_south, bounds_east, bounds_west]) else None,
            "hours_back": hours_back,
            "generated_at": datetime.utcnow().isoformat(),
            "data_types": []
        },
        "zones": [],
        "alerts": [],
        "tourists": [],
        "hotspots": []
    }
    
    # Get restricted zones
    if include_zones:
        heatmap_data["metadata"]["data_types"].append("zones")
        zones_query = select(RestrictedZone).where(RestrictedZone.is_active == True)
        
        # Apply bounds filter if provided
        if all([bounds_north, bounds_south, bounds_east, bounds_west]):
            zones_query = zones_query.where(
                and_(
                    RestrictedZone.center_latitude <= bounds_north,
                    RestrictedZone.center_latitude >= bounds_south,
                    RestrictedZone.center_longitude <= bounds_east,
                    RestrictedZone.center_longitude >= bounds_west
                )
            )
        
        zones_result = await db.execute(zones_query)
        zones = zones_result.scalars().all()
        
        for zone in zones:
            zone_data = {
                "id": zone.id,
                "name": zone.name,
                "type": zone.zone_type.value,
                "center": {
                    "lat": zone.center_latitude,
                    "lon": zone.center_longitude
                },
                "radius_meters": zone.radius_meters or 1000,
                "description": zone.description,
                "risk_level": zone.zone_type.value,
                "created_at": zone.created_at.isoformat()
            }
            heatmap_data["zones"].append(zone_data)
    
    # Get recent alerts
    if include_alerts:
        heatmap_data["metadata"]["data_types"].append("alerts")
        alerts_query = select(Alert, Tourist).join(
            Tourist, Alert.tourist_id == Tourist.id
        ).where(
            Alert.created_at >= time_threshold
        ).order_by(desc(Alert.created_at))
        
        alerts_result = await db.execute(alerts_query)
        alerts_data = alerts_result.all()
        
        for alert, tourist in alerts_data:
            # Use tourist's last known location
            alert_lat = tourist.last_location_lat
            alert_lon = tourist.last_location_lon
            
            # Skip alerts without location data
            if not alert_lat or not alert_lon:
                continue
            
            # Apply bounds filter if provided
            if all([bounds_north, bounds_south, bounds_east, bounds_west]):
                if not (bounds_south <= alert_lat <= bounds_north and 
                       bounds_west <= alert_lon <= bounds_east):
                    continue
            
            alert_data = {
                "id": alert.id,
                "type": alert.type.value,
                "severity": alert.severity.value,
                "location": {
                    "lat": alert_lat,
                    "lon": alert_lon
                },
                "tourist": {
                    "id": tourist.id,
                    "name": tourist.name,
                    "safety_score": tourist.safety_score
                },
                "title": alert.title,
                "description": alert.description,
                "is_acknowledged": alert.is_acknowledged,
                "created_at": alert.created_at.isoformat()
            }
            heatmap_data["alerts"].append(alert_data)
    
    # Get active tourists with recent locations
    if include_tourists:
        heatmap_data["metadata"]["data_types"].append("tourists")
        tourists_query = select(Tourist, Location).outerjoin(
            Location, and_(
                Location.tourist_id == Tourist.id,
                Location.timestamp >= time_threshold
            )
        ).where(
            and_(
                Tourist.is_active == True,
                Tourist.last_seen >= time_threshold
            )
        ).order_by(desc(Location.timestamp))
        
        tourists_result = await db.execute(tourists_query)
        tourists_data = tourists_result.all()
        
        # Group by tourist to get latest location
        tourist_locations = {}
        for tourist, location in tourists_data:
            if tourist.id not in tourist_locations and location:
                # Apply bounds filter if provided
                if all([bounds_north, bounds_south, bounds_east, bounds_west]):
                    if not (bounds_south <= location.latitude <= bounds_north and 
                           bounds_west <= location.longitude <= bounds_east):
                        continue
                
                tourist_locations[tourist.id] = {
                    "id": tourist.id,
                    "name": tourist.name,
                    "safety_score": tourist.safety_score,
                    "location": {
                        "lat": location.latitude,
                        "lon": location.longitude,
                        "speed": location.speed,
                        "timestamp": location.timestamp.isoformat()
                    },
                    "last_seen": tourist.last_seen.isoformat(),
                    "risk_level": "critical" if tourist.safety_score < 30 else 
                                 "high" if tourist.safety_score < 50 else
                                 "medium" if tourist.safety_score < 70 else "low"
                }
        
        heatmap_data["tourists"] = list(tourist_locations.values())
    
    # Generate hotspots based on alert density
    if include_alerts and heatmap_data["alerts"]:
        hotspots = _generate_hotspots(heatmap_data["alerts"])
        heatmap_data["hotspots"] = hotspots
        heatmap_data["metadata"]["data_types"].append("hotspots")
    
    # Add summary statistics
    heatmap_data["metadata"]["summary"] = {
        "zones_count": len(heatmap_data["zones"]),
        "alerts_count": len(heatmap_data["alerts"]),
        "tourists_count": len(heatmap_data["tourists"]),
        "hotspots_count": len(heatmap_data["hotspots"])
    }
    
    return heatmap_data


@router.get("/heatmap/zones")
async def get_heatmap_zones(
    zone_type: Optional[str] = None,  # "safe", "risky", "restricted", or "all"
    bounds_north: Optional[float] = None,
    bounds_south: Optional[float] = None,
    bounds_east: Optional[float] = None,
    bounds_west: Optional[float] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Authority = Depends(get_current_authority)
):
    """Get zones for heatmap visualization"""
    
    zones_query = select(RestrictedZone).where(RestrictedZone.is_active == True)
    
    # Filter by zone type if specified
    if zone_type and zone_type != "all":
        try:
            zone_type_enum = ZoneType(zone_type.lower())
            zones_query = zones_query.where(RestrictedZone.zone_type == zone_type_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid zone type: {zone_type}. Must be 'safe', 'risky', 'restricted', or 'all'"
            )
    
    # Apply bounds filter if provided
    if all([bounds_north, bounds_south, bounds_east, bounds_west]):
        zones_query = zones_query.where(
            and_(
                RestrictedZone.center_latitude <= bounds_north,
                RestrictedZone.center_latitude >= bounds_south,
                RestrictedZone.center_longitude <= bounds_east,
                RestrictedZone.center_longitude >= bounds_west
            )
        )
    
    zones_result = await db.execute(zones_query)
    zones = zones_result.scalars().all()
    
    zones_data = []
    for zone in zones:
        zone_data = {
            "id": zone.id,
            "name": zone.name,
            "type": zone.zone_type.value,
            "center": {
                "lat": zone.center_latitude,
                "lon": zone.center_longitude
            },
            "radius_meters": zone.radius_meters or 1000,
            "description": zone.description,
            "bounds_json": zone.bounds_json,
            "risk_weight": _get_zone_risk_weight(zone.zone_type),
            "created_at": zone.created_at.isoformat()
        }
        zones_data.append(zone_data)
    
    return {
        "zones": zones_data,
        "total": len(zones_data),
        "filter": {
            "zone_type": zone_type or "all",
            "bounds": {
                "north": bounds_north,
                "south": bounds_south,
                "east": bounds_east,
                "west": bounds_west
            } if all([bounds_north, bounds_south, bounds_east, bounds_west]) else None
        },
        "generated_at": datetime.utcnow().isoformat()
    }


@router.get("/heatmap/alerts")
async def get_heatmap_alerts(
    alert_type: Optional[str] = None,  # "geofence", "anomaly", "panic", "sos", "sequence"
    severity: Optional[str] = None,    # "low", "medium", "high", "critical"
    hours_back: int = 24,
    bounds_north: Optional[float] = None,
    bounds_south: Optional[float] = None,
    bounds_east: Optional[float] = None,
    bounds_west: Optional[float] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Authority = Depends(get_current_authority)
):
    """Get alerts for heatmap visualization"""
    
    time_threshold = datetime.utcnow() - timedelta(hours=hours_back)
    
    alerts_query = select(Alert, Tourist).join(
        Tourist, Alert.tourist_id == Tourist.id
    ).where(
        Alert.created_at >= time_threshold
    )
    
    # Filter by alert type if specified
    if alert_type:
        try:
            alert_type_enum = AlertType(alert_type.lower())
            alerts_query = alerts_query.where(Alert.alert_type == alert_type_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid alert type: {alert_type}"
            )
    
    # Filter by severity if specified
    if severity:
        try:
            severity_enum = AlertSeverity(severity.lower())
            alerts_query = alerts_query.where(Alert.severity == severity_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid severity: {severity}"
            )
    
    alerts_query = alerts_query.order_by(desc(Alert.created_at))
    alerts_result = await db.execute(alerts_query)
    alerts_data = alerts_result.all()
    
    alerts_list = []
    for alert, tourist in alerts_data:
        # Use tourist's last known location
        alert_lat = tourist.last_location_lat
        alert_lon = tourist.last_location_lon
        
        # Skip alerts without location data
        if not alert_lat or not alert_lon:
            continue
        
        # Apply bounds filter if provided
        if all([bounds_north, bounds_south, bounds_east, bounds_west]):
            if not (bounds_south <= alert_lat <= bounds_north and 
                   bounds_west <= alert_lon <= bounds_east):
                continue
        
        alert_data = {
            "id": alert.id,
            "type": alert.type.value,
            "severity": alert.severity.value,
            "location": {
                "lat": alert_lat,
                "lon": alert_lon
            },
            "tourist": {
                "id": tourist.id,
                "name": tourist.name,
                "safety_score": tourist.safety_score
            },
            "title": alert.title,
            "description": alert.description,
            "is_acknowledged": alert.is_acknowledged,
            "weight": _get_alert_weight(alert.severity, alert.type),
            "created_at": alert.created_at.isoformat()
        }
        alerts_list.append(alert_data)
    
    return {
        "alerts": alerts_list,
        "total": len(alerts_list),
        "filter": {
            "alert_type": alert_type,
            "severity": severity,
            "hours_back": hours_back,
            "bounds": {
                "north": bounds_north,
                "south": bounds_south,
                "east": bounds_east,
                "west": bounds_west
            } if all([bounds_north, bounds_south, bounds_east, bounds_west]) else None
        },
        "generated_at": datetime.utcnow().isoformat()
    }


@router.get("/heatmap/tourists")
async def get_heatmap_tourists(
    hours_back: int = 24,
    min_safety_score: Optional[int] = None,
    max_safety_score: Optional[int] = None,
    bounds_north: Optional[float] = None,
    bounds_south: Optional[float] = None,
    bounds_east: Optional[float] = None,
    bounds_west: Optional[float] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Authority = Depends(get_current_authority)
):
    """Get tourist locations for heatmap visualization"""
    
    time_threshold = datetime.utcnow() - timedelta(hours=hours_back)
    
    # First, get all active tourists matching criteria
    tourists_query = select(Tourist).where(
        and_(
            Tourist.is_active == True,
            Tourist.last_seen >= time_threshold
        )
    )
    
    # Filter by safety score range if specified
    if min_safety_score is not None:
        tourists_query = tourists_query.where(Tourist.safety_score >= min_safety_score)
    if max_safety_score is not None:
        tourists_query = tourists_query.where(Tourist.safety_score <= max_safety_score)
    
    tourists_result = await db.execute(tourists_query)
    tourists = tourists_result.scalars().all()
    
    # Now get latest location for each tourist
    tourist_locations = {}
    for tourist in tourists:
        # Get most recent location for this tourist
        location_query = select(Location).where(
            and_(
                Location.tourist_id == tourist.id,
                Location.timestamp >= time_threshold
            )
        ).order_by(desc(Location.timestamp)).limit(1)
        location_result = await db.execute(location_query)
        location = location_result.scalar_one_or_none()
        
        if location:
            # Apply bounds filter if provided
            if all([bounds_north, bounds_south, bounds_east, bounds_west]):
                if not (bounds_south <= location.latitude <= bounds_north and 
                       bounds_west <= location.longitude <= bounds_east):
                    continue
            
            tourist_locations[tourist.id] = {
                "id": tourist.id,
                "name": tourist.name,
                "safety_score": tourist.safety_score,
                "location": {
                    "lat": location.latitude,
                    "lon": location.longitude,
                    "speed": location.speed,
                    "accuracy": location.accuracy,
                    "timestamp": location.timestamp.isoformat()
                },
                "last_seen": tourist.last_seen.isoformat(),
                "risk_level": _get_risk_level_from_score(tourist.safety_score),
                "weight": _get_tourist_weight(tourist.safety_score)
            }
    
    return {
        "tourists": list(tourist_locations.values()),
        "total": len(tourist_locations),
        "filter": {
            "hours_back": hours_back,
            "min_safety_score": min_safety_score,
            "max_safety_score": max_safety_score,
            "bounds": {
                "north": bounds_north,
                "south": bounds_south,
                "east": bounds_east,
                "west": bounds_west
            } if all([bounds_north, bounds_south, bounds_east, bounds_west]) else None
        },
        "generated_at": datetime.utcnow().isoformat()
    }


def _generate_hotspots(alerts: List[Dict]) -> List[Dict]:
    """Generate hotspots based on alert density"""
    if not alerts:
        return []
    
    # Simple hotspot generation - group alerts by proximity
    hotspots = []
    processed_alerts = set()
    
    for i, alert in enumerate(alerts):
        if i in processed_alerts:
            continue
        
        alert_lat = alert["location"]["lat"]
        alert_lon = alert["location"]["lon"]
        
        # Find nearby alerts (within ~500m)
        nearby_alerts = [alert]
        processed_alerts.add(i)
        
        for j, other_alert in enumerate(alerts[i+1:], i+1):
            if j in processed_alerts:
                continue
            
            other_lat = other_alert["location"]["lat"]
            other_lon = other_alert["location"]["lon"]
            
            # Simple distance calculation (approximate)
            lat_diff = abs(alert_lat - other_lat)
            lon_diff = abs(alert_lon - other_lon)
            
            # Rough approximation: 0.01 degrees ≈ 1km
            if lat_diff < 0.005 and lon_diff < 0.005:  # ~500m radius
                nearby_alerts.append(other_alert)
                processed_alerts.add(j)
        
        # Create hotspot if multiple alerts in area
        if len(nearby_alerts) >= 2:
            # Calculate center of alerts
            center_lat = sum(a["location"]["lat"] for a in nearby_alerts) / len(nearby_alerts)
            center_lon = sum(a["location"]["lon"] for a in nearby_alerts) / len(nearby_alerts)
            
            # Calculate intensity based on alert count and severity
            intensity = 0
            for a in nearby_alerts:
                severity_weight = {"low": 1, "medium": 2, "high": 3, "critical": 4}
                intensity += severity_weight.get(a["severity"], 1)
            
            hotspot = {
                "center": {
                    "lat": center_lat,
                    "lon": center_lon
                },
                "intensity": intensity,
                "alert_count": len(nearby_alerts),
                "radius_meters": 500,
                "alert_types": list(set(a["type"] for a in nearby_alerts)),
                "max_severity": max(nearby_alerts, key=lambda x: {"low": 1, "medium": 2, "high": 3, "critical": 4}[x["severity"]])["severity"]
            }
            hotspots.append(hotspot)
    
    return hotspots


def _get_zone_risk_weight(zone_type: ZoneType) -> float:
    """Get risk weight for zone type"""
    weights = {
        ZoneType.SAFE: 0.1,
        ZoneType.RISKY: 0.6,
        ZoneType.RESTRICTED: 1.0
    }
    return weights.get(zone_type, 0.5)


def _get_alert_weight(severity: AlertSeverity, alert_type: AlertType) -> float:
    """Get weight for alert based on severity and type"""
    severity_weights = {
        AlertSeverity.LOW: 0.25,
        AlertSeverity.MEDIUM: 0.5,
        AlertSeverity.HIGH: 0.75,
        AlertSeverity.CRITICAL: 1.0
    }
    
    type_weights = {
        AlertType.SOS: 1.0,
        AlertType.PANIC: 0.9,
        AlertType.ANOMALY: 0.6,
        AlertType.GEOFENCE: 0.4,
        AlertType.SEQUENCE: 0.5
    }
    
    return severity_weights.get(severity, 0.5) * type_weights.get(alert_type, 0.5)


def _get_tourist_weight(safety_score: int) -> float:
    """Get weight for tourist based on safety score"""
    if safety_score < 30:
        return 1.0  # Critical
    elif safety_score < 50:
        return 0.75  # High risk
    elif safety_score < 70:
        return 0.5   # Medium risk
    else:
        return 0.25  # Low risk


def _get_risk_level_from_score(safety_score: int) -> str:
    """Get risk level string from safety score"""
    if safety_score < 30:
        return "critical"
    elif safety_score < 50:
        return "high"
    elif safety_score < 70:
        return "medium"
    else:
        return "low"


# ========================================
# Emergency Broadcast Endpoints
# ========================================

class BroadcastRadiusRequest(BaseModel):
    center_latitude: float
    center_longitude: float
    radius_km: float
    title: str
    message: str
    severity: str  # "low", "medium", "high", "critical"
    alert_type: Optional[str] = None
    action_required: Optional[str] = None
    expires_at: Optional[datetime] = None


class BroadcastZoneRequest(BaseModel):
    zone_id: int
    title: str
    message: str
    severity: str
    alert_type: Optional[str] = None
    action_required: Optional[str] = None


class BroadcastRegionRequest(BaseModel):
    region_bounds: Dict[str, float]  # {"min_lat": ..., "max_lat": ..., "min_lon": ..., "max_lon": ...}
    title: str
    message: str
    severity: str
    alert_type: Optional[str] = None
    action_required: Optional[str] = None


class BroadcastAllRequest(BaseModel):
    title: str
    message: str
    severity: str
    alert_type: Optional[str] = None
    action_required: Optional[str] = None


@router.post("/broadcast/radius")
async def broadcast_radius_area(
    req: BroadcastRadiusRequest,
    current_user: AuthUser = Depends(get_current_authority),
    db: AsyncSession = Depends(get_db)
):
    """Broadcast emergency message to tourists within radius of a point"""
    from ..services.broadcast import broadcast_radius
    from ..models.database_models import BroadcastSeverity
    
    try:
        # Convert severity string to enum
        severity = BroadcastSeverity[req.severity.upper()]
        
        # Send broadcast
        result = await broadcast_radius(
            db=db,
            authority_id=current_user.id,
            center_lat=req.center_latitude,
            center_lon=req.center_longitude,
            radius_km=req.radius_km,
            title=req.title,
            message=req.message,
            severity=severity,
            alert_type=req.alert_type,
            action_required=req.action_required,
            expires_at=req.expires_at
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to broadcast: {str(e)}"
        )


@router.post("/broadcast/zone")
async def broadcast_zone_area(
    req: BroadcastZoneRequest,
    current_user: AuthUser = Depends(get_current_authority),
    db: AsyncSession = Depends(get_db)
):
    """Broadcast emergency message to tourists in a specific zone"""
    from ..services.broadcast import broadcast_zone
    from ..models.database_models import BroadcastSeverity
    
    try:
        severity = BroadcastSeverity[req.severity.upper()]
        
        result = await broadcast_zone(
            db=db,
            authority_id=current_user.id,
            zone_id=req.zone_id,
            title=req.title,
            message=req.message,
            severity=severity,
            alert_type=req.alert_type,
            action_required=req.action_required
        )
        
        return result
        
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to broadcast: {str(e)}"
        )


@router.post("/broadcast/region")
async def broadcast_region_area(
    req: BroadcastRegionRequest,
    current_user: AuthUser = Depends(get_current_authority),
    db: AsyncSession = Depends(get_db)
):
    """Broadcast emergency message to tourists in a geographic region"""
    from ..services.broadcast import broadcast_region
    from ..models.database_models import BroadcastSeverity
    
    try:
        severity = BroadcastSeverity[req.severity.upper()]
        
        result = await broadcast_region(
            db=db,
            authority_id=current_user.id,
            min_lat=req.region_bounds["min_lat"],
            max_lat=req.region_bounds["max_lat"],
            min_lon=req.region_bounds["min_lon"],
            max_lon=req.region_bounds["max_lon"],
            title=req.title,
            message=req.message,
            severity=severity,
            alert_type=req.alert_type,
            action_required=req.action_required
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to broadcast: {str(e)}"
        )


@router.post("/broadcast/all")
async def broadcast_all_tourists(
    req: BroadcastAllRequest,
    current_user: AuthUser = Depends(get_current_authority),
    db: AsyncSession = Depends(get_db)
):
    """Broadcast emergency message to ALL active tourists"""
    from ..services.broadcast import broadcast_all
    from ..models.database_models import BroadcastSeverity
    
    try:
        severity = BroadcastSeverity[req.severity.upper()]
        
        result = await broadcast_all(
            db=db,
            authority_id=current_user.id,
            title=req.title,
            message=req.message,
            severity=severity,
            alert_type=req.alert_type,
            action_required=req.action_required
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to broadcast: {str(e)}"
        )


@router.get("/broadcast/history")
async def get_broadcast_history(
    current_user: AuthUser = Depends(get_current_authority),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0
):
    """Get broadcast history for current authority"""
    from ..models.database_models import EmergencyBroadcast
    
    try:
        stmt = select(EmergencyBroadcast).where(
            EmergencyBroadcast.sent_by == current_user.id
        ).order_by(desc(EmergencyBroadcast.sent_at)).limit(limit).offset(offset)
        
        result = await db.execute(stmt)
        broadcasts = result.scalars().all()
        
        return {
            "broadcasts": [
                {
                    "broadcast_id": b.broadcast_id,
                    "type": b.broadcast_type.value,
                    "title": b.title,
                    "severity": b.severity.value,
                    "tourists_notified": b.tourists_notified_count,
                    "devices_notified": b.devices_notified_count,
                    "acknowledgments": b.acknowledgment_count,
                    "sent_at": b.sent_at.isoformat()
                }
                for b in broadcasts
            ],
            "total": len(broadcasts)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get broadcast history: {str(e)}"
        )


@router.get("/broadcast/{broadcast_id}")
async def get_broadcast_details(
    broadcast_id: str,
    current_user: AuthUser = Depends(get_current_authority),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a specific broadcast"""
    from ..models.database_models import EmergencyBroadcast, BroadcastAcknowledgment
    
    try:
        stmt = select(EmergencyBroadcast).where(
            EmergencyBroadcast.broadcast_id == broadcast_id
        )
        result = await db.execute(stmt)
        broadcast = result.scalar_one_or_none()
        
        if not broadcast:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Broadcast not found"
            )
        
        # Get acknowledgments
        ack_stmt = select(BroadcastAcknowledgment).where(
            BroadcastAcknowledgment.broadcast_id == broadcast.id
        )
        ack_result = await db.execute(ack_stmt)
        acknowledgments = ack_result.scalars().all()
        
        return {
            "broadcast_id": broadcast.broadcast_id,
            "type": broadcast.broadcast_type.value,
            "title": broadcast.title,
            "message": broadcast.message,
            "severity": broadcast.severity.value,
            "alert_type": broadcast.alert_type,
            "action_required": broadcast.action_required,
            "tourists_notified": broadcast.tourists_notified_count,
            "devices_notified": broadcast.devices_notified_count,
            "acknowledgment_count": len(acknowledgments),
            "acknowledgment_rate": f"{(len(acknowledgments) / broadcast.tourists_notified_count * 100) if broadcast.tourists_notified_count > 0 else 0:.1f}%",
            "sent_at": broadcast.sent_at.isoformat(),
            "expires_at": broadcast.expires_at.isoformat() if broadcast.expires_at else None,
            "acknowledgments": [
                {
                    "tourist_id": ack.tourist_id,
                    "status": ack.status,
                    "acknowledged_at": ack.acknowledged_at.isoformat(),
                    "location": {"lat": ack.location_lat, "lon": ack.location_lon} if ack.location_lat else None,
                    "notes": ack.notes
                }
                for ack in acknowledgments
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get broadcast details: {str(e)}"
        )
