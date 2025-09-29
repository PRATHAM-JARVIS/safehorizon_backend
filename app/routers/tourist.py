from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, validator
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from ..database import get_db
from ..auth.local_auth_utils import (
    authenticate_user, create_user_account, get_current_tourist, AuthUser, get_current_user
)
from ..models.database_models import (
    Tourist, Trip, Location, Alert, AlertType, AlertSeverity, TripStatus
)
from ..services.scoring import compute_safety_score, should_trigger_alert, get_risk_level
from ..services.notifications import send_emergency_alert
from ..services.websocket_manager import websocket_manager
from ..services.geofence import get_all_zones

router = APIRouter()


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: Optional[str] = None
    phone: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class TripStartRequest(BaseModel):
    destination: str
    itinerary: Optional[str] = None


class LocationUpdate(BaseModel):
    lat: float
    lon: float
    speed: Optional[float] = None
    altitude: Optional[float] = None
    accuracy: Optional[float] = None
    timestamp: Optional[datetime] = None
    
    @validator('timestamp', pre=True, always=True)
    def set_timestamp(cls, v):
        return v or datetime.utcnow()


@router.post("/auth/register")
async def register_user(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new tourist user"""
    try:
        # Create user account locally (this also creates the tourist record)
        auth_response = await create_user_account(
            email=payload.email,
            password=payload.password,
            role="tourist",
            name=payload.name,
            phone=payload.phone,
            emergency_contact=payload.emergency_contact,
            emergency_phone=payload.emergency_phone
        )
        
        user_id = auth_response["user"]["id"]
        
        return {
            "message": "Tourist registered successfully",
            "user_id": user_id,
            "email": payload.email
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/auth/login")
async def login_user(payload: LoginRequest):
    """Login tourist user"""
    try:
        auth_response = await authenticate_user(payload.email, payload.password, role="tourist")
        return auth_response  # This already contains access_token, token_type, user_id, email, role
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )


@router.get("/auth/me")
async def get_current_user_info(
    current_tourist: Tourist = Depends(get_current_tourist)
):
    """Get current user information"""
    return {
        "id": current_tourist.id,
        "email": current_tourist.email,
        "name": current_tourist.name,
        "phone": current_tourist.phone,
        "safety_score": current_tourist.safety_score,
        "last_seen": current_tourist.last_seen.isoformat() if current_tourist.last_seen else None
    }


@router.post("/trip/start")
async def start_trip(
    payload: TripStartRequest,
    current_user: Tourist = Depends(get_current_tourist),
    db: AsyncSession = Depends(get_db)
):
    """Start a new trip"""
    trip = Trip(
        tourist_id=current_user.id,
        destination=payload.destination,
        start_date=datetime.utcnow(),
        status=TripStatus.ACTIVE,
        itinerary=payload.itinerary
    )
    
    db.add(trip)
    await db.commit()
    await db.refresh(trip)
    
    return {
        "trip_id": trip.id,
        "destination": trip.destination,
        "status": trip.status.value,
        "start_date": trip.start_date.isoformat()
    }


@router.post("/trip/end")
async def end_trip(
    current_user: Tourist = Depends(get_current_tourist),
    db: AsyncSession = Depends(get_db)
):
    """End the current active trip"""
    # Find active trip
    query = select(Trip).where(
        Trip.tourist_id == current_user.id,
        Trip.status == TripStatus.ACTIVE
    ).order_by(desc(Trip.start_date))
    
    result = await db.execute(query)
    trip = result.scalar_one_or_none()
    
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active trip found"
        )
    
    trip.status = TripStatus.COMPLETED
    trip.end_date = datetime.utcnow()
    
    await db.commit()
    
    return {
        "trip_id": trip.id,
        "status": trip.status.value,
        "end_date": trip.end_date.isoformat()
    }


@router.get("/trip/history")
async def get_trip_history(
    current_tourist: Tourist = Depends(get_current_tourist),
    db: AsyncSession = Depends(get_db)
):
    """Get user's trip history"""
    query = select(Trip).where(
        Trip.tourist_id == current_tourist.id
    ).order_by(desc(Trip.created_at))
    
    result = await db.execute(query)
    trips = result.scalars().all()
    
    return [
        {
            "id": trip.id,
            "destination": trip.destination,
            "status": trip.status.value,
            "start_date": trip.start_date.isoformat() if trip.start_date else None,
            "end_date": trip.end_date.isoformat() if trip.end_date else None,
            "created_at": trip.created_at.isoformat()
        }
        for trip in trips
    ]


@router.post("/location/update")
async def update_location(
    location: LocationUpdate,
    current_user: Tourist = Depends(get_current_tourist),
    db: AsyncSession = Depends(get_db)
):
    """Update user location and run AI safety analysis"""
    # Get current active trip
    trip_query = select(Trip).where(
        Trip.tourist_id == current_user.id,
        Trip.status == TripStatus.ACTIVE
    ).order_by(desc(Trip.start_date))
    
    trip_result = await db.execute(trip_query)
    current_trip = trip_result.scalar_one_or_none()
    
    # Create location record
    location_record = Location(
        tourist_id=current_user.id,
        trip_id=current_trip.id if current_trip else None,
        latitude=location.lat,
        longitude=location.lon,
        altitude=location.altitude,
        speed=location.speed,
        accuracy=location.accuracy,
        timestamp=location.timestamp
    )
    
    db.add(location_record)
    
    # Get recent locations for sequence analysis
    recent_locations_query = select(Location).where(
        Location.tourist_id == current_user.id,
        Location.timestamp >= datetime.utcnow() - timedelta(hours=2)
    ).order_by(desc(Location.timestamp)).limit(20)
    
    recent_result = await db.execute(recent_locations_query)
    recent_locations = recent_result.scalars().all()
    
    # Prepare context for safety scoring
    location_history = [
        {
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "speed": loc.speed or 0,
            "timestamp": loc.timestamp.isoformat()
        }
        for loc in recent_locations
    ]
    
    current_location_data = {
        "latitude": location.lat,
        "longitude": location.lon,
        "speed": location.speed or 0,
        "timestamp": location.timestamp.isoformat()
    }
    
    # Compute safety score
    safety_context = {
        "lat": location.lat,
        "lon": location.lon,
        "location_history": location_history,
        "current_location_data": current_location_data
    }
    
    safety_score = await compute_safety_score(safety_context)
    
    # Update tourist's safety score and location
    tourist_query = select(Tourist).where(Tourist.id == current_user.id)
    tourist_result = await db.execute(tourist_query)
    tourist = tourist_result.scalar_one_or_none()
    
    if tourist:
        tourist.safety_score = safety_score
        tourist.last_location_lat = location.lat
        tourist.last_location_lon = location.lon
        tourist.last_seen = datetime.utcnow()
    
    # Check if alert should be triggered
    if should_trigger_alert(safety_score):
        alert = Alert(
            tourist_id=current_user.id,
            location_id=location_record.id,
            type=AlertType.ANOMALY,
            severity=AlertSeverity.HIGH if safety_score < 40 else AlertSeverity.MEDIUM,
            title=f"Safety Alert - Score: {safety_score}",
            description=f"Safety score dropped to {safety_score}. Risk level: {get_risk_level(safety_score)}"
        )
        
        db.add(alert)
        await db.commit()
        await db.refresh(alert)
        
        # Broadcast alert to police dashboard
        alert_data = {
            "type": "safety_alert",
            "alert_id": alert.id,
            "tourist_id": current_user.id,
            "severity": alert.severity.value,
            "safety_score": safety_score,
            "location": {"lat": location.lat, "lon": location.lon},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await websocket_manager.publish_alert("authority", alert_data)
    else:
        await db.commit()
    
    return {
        "status": "location_updated",
        "location_id": location_record.id,
        "safety_score": safety_score,
        "risk_level": get_risk_level(safety_score),
        "lat": location.lat,
        "lon": location.lon,
        "timestamp": location.timestamp.isoformat()
    }


@router.get("/location/history")
async def get_location_history(
    limit: int = 100,
    current_user: Tourist = Depends(get_current_tourist),
    db: AsyncSession = Depends(get_db)
):
    """Get user's location history"""
    query = select(Location).where(
        Location.tourist_id == current_user.id
    ).order_by(desc(Location.timestamp)).limit(limit)
    
    result = await db.execute(query)
    locations = result.scalars().all()
    
    return [
        {
            "id": loc.id,
            "lat": loc.latitude,
            "lon": loc.longitude,
            "speed": loc.speed,
            "altitude": loc.altitude,
            "accuracy": loc.accuracy,
            "timestamp": loc.timestamp.isoformat()
        }
        for loc in locations
    ]


@router.get("/safety/score")
async def get_safety_score(
    current_tourist: Tourist = Depends(get_current_tourist)
):
    """Get current safety score"""
    return {
        "safety_score": current_tourist.safety_score,
        "risk_level": get_risk_level(current_tourist.safety_score),
        "last_updated": current_tourist.last_seen.isoformat() if current_tourist.last_seen else None
    }


@router.post("/sos/trigger")
async def trigger_sos(
    current_user: Tourist = Depends(get_current_tourist),
    db: AsyncSession = Depends(get_db)
):
    """Trigger SOS emergency alert"""
    # Get tourist data
    tourist_query = select(Tourist).where(Tourist.id == current_user.id)
    tourist_result = await db.execute(tourist_query)
    tourist = tourist_result.scalar_one_or_none()
    
    if not tourist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tourist not found"
        )
    
    # Create SOS alert
    alert = Alert(
        tourist_id=current_user.id,
        type=AlertType.SOS,
        severity=AlertSeverity.CRITICAL,
        title="🚨 SOS Emergency Alert",
        description=f"Emergency SOS triggered by {tourist.name or tourist.email}"
    )
    
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    
    # Prepare user and alert data for notifications
    user_data = {
        "name": tourist.name,
        "email": tourist.email,
        "phone": tourist.phone,
        "emergency_contacts": [
            {
                "name": tourist.emergency_contact,
                "phone": tourist.emergency_phone
            }
        ] if tourist.emergency_contact and tourist.emergency_phone else []
    }
    
    alert_data = {
        "id": alert.id,
        "type": "SOS",
        "severity": "critical",
        "location": f"{tourist.last_location_lat}, {tourist.last_location_lon}" if tourist.last_location_lat else "Unknown"
    }
    
    # Send emergency notifications
    notification_results = await send_emergency_alert(user_data, alert_data)
    
    # Broadcast to police dashboard
    websocket_alert = {
        "type": "sos_alert",
        "alert_id": alert.id,
        "tourist_id": current_user.id,
        "tourist_name": tourist.name or tourist.email,
        "severity": "critical",
        "location": {
            "lat": tourist.last_location_lat,
            "lon": tourist.last_location_lon
        } if tourist.last_location_lat else None,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await websocket_manager.publish_alert("authority", websocket_alert)
    
    return {
        "status": "sos_triggered",
        "alert_id": alert.id,
        "notifications_sent": notification_results,
        "timestamp": alert.created_at.isoformat()
    }


@router.get("/zones/list")
async def list_zones_for_all_users(
    current_user: AuthUser = Depends(get_current_user)
):
    """Get list of all safety zones (accessible to all authenticated users)"""
    return await get_all_zones()
