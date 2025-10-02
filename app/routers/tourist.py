from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, validator
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
import logging
import traceback

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
from ..services.blockchain import generate_efir

logger = logging.getLogger(__name__)
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


class EFIRRequest(BaseModel):
    incident_description: str
    incident_type: str
    location: Optional[str] = None
    timestamp: Optional[datetime] = None
    witnesses: Optional[List[str]] = None
    additional_details: Optional[str] = None
    
    @validator('timestamp', pre=True, always=True)
    def set_timestamp(cls, v):
        return v or datetime.utcnow()


@router.post("/auth/register")
async def register_user(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new tourist user"""
    try:
        logger.info(f"Attempting to register tourist: {payload.email}")
        
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
        
        logger.info(f"Tourist registered successfully: {payload.email} (ID: {user_id})")
        
        return {
            "message": "Tourist registered successfully",
            "user_id": user_id,
            "email": payload.email
        }
        
    except HTTPException as he:
        # Re-raise HTTP exceptions as-is
        logger.error(f"HTTP exception during registration: {he.detail}")
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}\n{traceback.format_exc()}")
        try:
            await db.rollback()
        except:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/auth/login")
async def login_user(payload: LoginRequest):
    """Login tourist user"""
    try:
        logger.info(f"Login attempt for tourist: {payload.email}")
        auth_response = await authenticate_user(payload.email, payload.password, role="tourist")
        logger.info(f"Tourist logged in successfully: {payload.email}")
        return auth_response  # This already contains access_token, token_type, user_id, email, role
    except HTTPException as he:
        # Re-raise HTTP exceptions as-is
        logger.warning(f"Login failed for {payload.email}: {he.detail}")
        raise
    except Exception as e:
        logger.error(f"Login error for {payload.email}: {str(e)}\n{traceback.format_exc()}")
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
    # Find active trip - use limit(1) to handle multiple active trips
    query = select(Trip).where(
        Trip.tourist_id == current_user.id,
        Trip.status == TripStatus.ACTIVE
    ).order_by(desc(Trip.start_date)).limit(1)
    
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
    await db.refresh(trip)  # Refresh to ensure trip object is up to date
    
    return {
        "trip_id": trip.id,
        "status": trip.status.value if hasattr(trip.status, 'value') else str(trip.status),
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
    try:
        logger.info(f"Location update for tourist {current_user.id}: lat={location.lat}, lon={location.lon}")
        
        # Get current active trip
        trip_query = select(Trip).where(
            Trip.tourist_id == current_user.id,
            Trip.status == TripStatus.ACTIVE
        ).order_by(desc(Trip.start_date)).limit(1)
        
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
        
        logger.info(f"Location updated successfully for tourist {current_user.id}, safety_score={safety_score}")
        
        return {
            "status": "location_updated",
            "location_id": location_record.id,
            "safety_score": safety_score,
            "risk_level": get_risk_level(safety_score),
            "lat": location.lat,
            "lon": location.lon,
            "timestamp": location.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Location update error for tourist {current_user.id}: {str(e)}\n{traceback.format_exc()}")
        try:
            await db.rollback()
        except:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update location: {str(e)}"
        )
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


@router.post("/tourist/efir/generate")
async def generate_efir_report(
    payload: EFIRRequest,
    current_user: Tourist = Depends(get_current_tourist),
    db: AsyncSession = Depends(get_db)
):
    """Generate E-FIR (Electronic First Information Report) for tourist-reported incidents"""
    import json
    from ..models.database_models import EFIR
    
    # Get tourist data
    tourist_query = select(Tourist).where(Tourist.id == current_user.id)
    tourist_result = await db.execute(tourist_query)
    tourist = tourist_result.scalar_one_or_none()
    
    if not tourist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tourist not found"
        )
    
    # Generate a unique FIR number for tourist-reported incidents
    fir_number = f"EFIR-{datetime.utcnow().strftime('%Y%m%d')}-T{tourist.id[:8]}-{int(datetime.utcnow().timestamp())}"
    
    # Parse location
    location_lat = None
    location_lon = None
    location_desc = payload.location
    
    if not payload.location and tourist.last_location_lat and tourist.last_location_lon:
        location_lat = tourist.last_location_lat
        location_lon = tourist.last_location_lon
        location_desc = f"{location_lat}, {location_lon}"
    
    # Prepare E-FIR data for blockchain
    efir_data = {
        "fir_number": fir_number,
        "incident_type": payload.incident_type,
        "incident_description": payload.incident_description,
        "tourist_id": tourist.id,
        "tourist_name": tourist.name or tourist.email,
        "tourist_email": tourist.email,
        "tourist_phone": tourist.phone,
        "location": location_desc or "Location not provided",
        "location_lat": location_lat,
        "location_lon": location_lon,
        "reported_by": "tourist_self_report",
        "report_source": "tourist",
        "timestamp": payload.timestamp.isoformat(),
        "witnesses": payload.witnesses or [],
        "additional_details": payload.additional_details,
        "emergency_contact": tourist.emergency_contact,
        "emergency_phone": tourist.emergency_phone
    }
    
    # Generate E-FIR on blockchain
    try:
        blockchain_result = await generate_efir(efir_data)
        
        # Create an alert for tracking (linked to E-FIR)
        alert = Alert(
            tourist_id=current_user.id,
            type=AlertType.MANUAL,
            severity=AlertSeverity.MEDIUM,
            title=f"E-FIR: {payload.incident_type}",
            description=f"Tourist-reported incident via E-FIR: {payload.incident_description[:100]}..."
        )
        
        db.add(alert)
        await db.flush()  # Get alert.id without committing
        
        # Create E-FIR record in database
        efir_record = EFIR(
            efir_number=fir_number,
            incident_id=None,  # No incident yet (tourist report)
            alert_id=alert.id,
            tourist_id=tourist.id,
            blockchain_tx_id=blockchain_result.get("tx_id"),
            block_hash=blockchain_result.get("block_hash"),
            chain_id=blockchain_result.get("chain_id", "safehorizon-efir-chain"),
            incident_type=payload.incident_type,
            severity="medium",  # Default severity for tourist reports
            description=payload.incident_description,
            location_lat=location_lat,
            location_lon=location_lon,
            location_description=location_desc or "Location not provided",
            tourist_name=tourist.name or tourist.email,
            tourist_email=tourist.email,
            tourist_phone=tourist.phone,
            reported_by=None,  # No authority (tourist self-report)
            officer_name=None,
            officer_badge=None,
            officer_department=None,
            report_source="tourist",
            witnesses=json.dumps(payload.witnesses) if payload.witnesses else None,
            evidence=None,
            officer_notes=None,
            is_verified=False,  # Tourist reports need verification
            verification_timestamp=None,
            incident_timestamp=payload.timestamp,
            additional_data=json.dumps({
                "additional_details": payload.additional_details,
                "emergency_contact": tourist.emergency_contact,
                "emergency_phone": tourist.emergency_phone
            }) if payload.additional_details else None
        )
        
        db.add(efir_record)
        await db.commit()
        await db.refresh(alert)
        await db.refresh(efir_record)
        
        # Notify authorities via WebSocket about the E-FIR
        websocket_alert = {
            "type": "efir_generated",
            "efir_id": efir_record.id,
            "fir_number": fir_number,
            "tourist_id": current_user.id,
            "tourist_name": tourist.name or tourist.email,
            "incident_type": payload.incident_type,
            "location": location_desc or "Location not provided",
            "timestamp": datetime.utcnow().isoformat(),
            "alert_id": alert.id,
            "report_source": "tourist"
        }
        
        await websocket_manager.publish_alert("authority", websocket_alert)
        
        return {
            "success": True,
            "message": "E-FIR generated and stored successfully",
            "efir_id": efir_record.id,
            "fir_number": fir_number,
            "blockchain_tx_id": blockchain_result.get("tx_id"),
            "timestamp": payload.timestamp.isoformat(),
            "verification_url": blockchain_result.get("verification_url"),
            "status": "submitted",
            "alert_id": alert.id
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate E-FIR: {str(e)}"
        )


@router.get("/debug/role")
async def debug_user_role(
    current_user: AuthUser = Depends(get_current_user)
):
    """Debug endpoint to check user role and permissions"""
    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "is_tourist": current_user.role in ["tourist", "admin"],
        "is_authority": current_user.role in ["authority", "admin"],
        "is_admin": current_user.role == "admin"
    }


@router.get("/zones/list")
async def list_zones_for_all_users(
    current_user: AuthUser = Depends(get_current_user)
):
    """Get list of all safety zones (accessible to all authenticated users)"""
    return await get_all_zones()


@router.get("/zones/nearby")
async def get_nearby_zones_for_tourist(
    lat: float,
    lon: float,
    radius: int = 5000,  # 5km default radius
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get zones near tourist's current location"""
    from ..services.geofence import get_nearby_zones
    
    nearby_zones = await get_nearby_zones(lat, lon, radius)
    
    return {
        "nearby_zones": nearby_zones,
        "center": {"lat": lat, "lon": lon},
        "radius_meters": radius,
        "total": len(nearby_zones),
        "generated_at": datetime.utcnow().isoformat()
    }


@router.get("/heatmap/zones/public")
async def get_public_zone_heatmap(
    bounds_north: Optional[float] = None,
    bounds_south: Optional[float] = None,
    bounds_east: Optional[float] = None,
    bounds_west: Optional[float] = None,
    zone_type: Optional[str] = None,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get public zone heatmap data for tourist app"""
    from ..models.database_models import RestrictedZone, ZoneType
    from sqlalchemy import and_
    
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
        # Only show essential info to tourists (no internal details)
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
            "safety_recommendation": _get_zone_safety_recommendation(zone.zone_type)
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
        "generated_at": datetime.utcnow().isoformat(),
        "note": "Public zone information for tourist safety awareness"
    }


def _get_zone_safety_recommendation(zone_type) -> str:
    """Get safety recommendation for zone type"""
    from ..models.database_models import ZoneType
    
    recommendations = {
        ZoneType.SAFE: "Safe area - normal precautions apply",
        ZoneType.RISKY: "Exercise increased caution - stay alert",
        ZoneType.RESTRICTED: "Avoid this area - high risk zone"
    }
    return recommendations.get(zone_type, "Exercise normal caution")


@router.get("/efir/my-reports")
async def get_my_efirs(
    limit: int = 50,
    current_user: Tourist = Depends(get_current_tourist),
    db: AsyncSession = Depends(get_db)
):
    """Get all E-FIRs submitted by the current tourist"""
    import json
    from ..models.database_models import EFIR
    
    # Query E-FIRs for this tourist
    efirs_query = select(EFIR).where(
        EFIR.tourist_id == current_user.id,
        EFIR.report_source == "tourist"
    ).order_by(desc(EFIR.generated_at)).limit(limit)
    
    efirs_result = await db.execute(efirs_query)
    efirs = efirs_result.scalars().all()
    
    efirs_list = []
    for efir in efirs:
        efir_data = {
            "efir_id": efir.id,
            "fir_number": efir.efir_number,
            "incident_type": efir.incident_type,
            "severity": efir.severity,
            "description": efir.description,
            "location": {
                "lat": efir.location_lat,
                "lon": efir.location_lon,
                "description": efir.location_description
            },
            "incident_timestamp": efir.incident_timestamp.isoformat(),
            "generated_at": efir.generated_at.isoformat(),
            "blockchain_tx_id": efir.blockchain_tx_id,
            "is_verified": efir.is_verified,
            "verification_timestamp": efir.verification_timestamp.isoformat() if efir.verification_timestamp else None,
            "witnesses": json.loads(efir.witnesses) if efir.witnesses else [],
            "status": "verified" if efir.is_verified else "pending_verification"
        }
        efirs_list.append(efir_data)
    
    return {
        "success": True,
        "total": len(efirs_list),
        "efirs": efirs_list,
        "generated_at": datetime.utcnow().isoformat()
    }


@router.get("/efir/{efir_id}")
async def get_efir_details(
    efir_id: int,
    current_user: Tourist = Depends(get_current_tourist),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a specific E-FIR"""
    import json
    from ..models.database_models import EFIR
    
    # Query E-FIR
    efir_query = select(EFIR).where(EFIR.id == efir_id)
    efir_result = await db.execute(efir_query)
    efir = efir_result.scalar_one_or_none()
    
    if not efir:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="E-FIR not found"
        )
    
    # Check if tourist owns this E-FIR
    if efir.tourist_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You can only view your own E-FIRs"
        )
    
    # Parse additional data
    additional_data = {}
    if efir.additional_data:
        try:
            additional_data = json.loads(efir.additional_data)
        except:
            pass
    
    return {
        "success": True,
        "efir": {
            "efir_id": efir.id,
            "fir_number": efir.efir_number,
            "incident_type": efir.incident_type,
            "severity": efir.severity,
            "description": efir.description,
            "location": {
                "lat": efir.location_lat,
                "lon": efir.location_lon,
                "description": efir.location_description
            },
            "tourist_info": {
                "name": efir.tourist_name,
                "email": efir.tourist_email,
                "phone": efir.tourist_phone
            },
            "incident_timestamp": efir.incident_timestamp.isoformat(),
            "generated_at": efir.generated_at.isoformat(),
            "blockchain": {
                "tx_id": efir.blockchain_tx_id,
                "block_hash": efir.block_hash,
                "chain_id": efir.chain_id
            },
            "is_verified": efir.is_verified,
            "verification_timestamp": efir.verification_timestamp.isoformat() if efir.verification_timestamp else None,
            "witnesses": json.loads(efir.witnesses) if efir.witnesses else [],
            "additional_details": additional_data.get("additional_details"),
            "report_source": efir.report_source,
            "status": "verified" if efir.is_verified else "pending_verification"
        }
    }


# ========================================
# Device Management for Push Notifications
# ========================================

class DeviceRegisterRequest(BaseModel):
    device_token: str
    device_type: str  # 'ios' or 'android'
    device_name: Optional[str] = None
    app_version: Optional[str] = None


@router.post("/device/register")
async def register_device(
    req: DeviceRegisterRequest,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Register or update device token for push notifications (tourists only)"""
    from ..models.database_models import UserDevice
    
    try:
        # Only tourists can register devices (not authorities)
        if current_user.role != "tourist":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only tourists can register devices for push notifications"
            )
        
        # Verify tourist exists in database
        tourist_stmt = select(Tourist).where(Tourist.id == current_user.id)
        tourist_result = await db.execute(tourist_stmt)
        tourist = tourist_result.scalar_one_or_none()
        
        if not tourist:
            logger.error(f"Tourist not found in database: {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tourist account not found. Please register first."
            )
        
        # Check if device token already exists
        stmt = select(UserDevice).where(
            UserDevice.device_token == req.device_token
        )
        result = await db.execute(stmt)
        existing_device = result.scalar_one_or_none()
        
        if existing_device:
            # Update existing device only if it belongs to a different user
            # or if we're updating the same user's device
            existing_device.user_id = current_user.id
            existing_device.device_type = req.device_type
            existing_device.device_name = req.device_name
            existing_device.app_version = req.app_version
            existing_device.is_active = True
            existing_device.last_used = datetime.utcnow()
            logger.info(f"Updated device token for user {current_user.id}")
        else:
            # Create new device
            device = UserDevice(
                user_id=current_user.id,
                device_token=req.device_token,
                device_type=req.device_type,
                device_name=req.device_name,
                app_version=req.app_version,
                is_active=True,
                last_used=datetime.utcnow()
            )
            db.add(device)
            logger.info(f"Registered new device for user {current_user.id}")
        
        await db.commit()
        
        return {
            "status": "success",
            "message": "Device registered successfully",
            "device_token": req.device_token,
            "device_type": req.device_type
        }
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to register device: {str(e)}")
        logger.error(f"User ID: {current_user.id}, Role: {current_user.role}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register device: {str(e)}"
        )


@router.delete("/device/unregister")
async def unregister_device(
    device_token: str,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Unregister device (on logout or app uninstall)"""
    from ..models.database_models import UserDevice
    
    try:
        stmt = select(UserDevice).where(
            UserDevice.device_token == device_token,
            UserDevice.user_id == current_user.id
        )
        result = await db.execute(stmt)
        device = result.scalar_one_or_none()
        
        if device:
            device.is_active = False
            await db.commit()
            logger.info(f"Unregistered device for user {current_user.id}")
            return {"status": "success", "message": "Device unregistered"}
        
        logger.warning(f"Device not found for user {current_user.id}")
        return {"status": "not_found", "message": "Device not found"}
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to unregister device: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unregister device: {str(e)}"
        )


@router.get("/device/list")
async def list_devices(
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all registered devices for current user"""
    from ..models.database_models import UserDevice
    
    try:
        stmt = select(UserDevice).where(
            UserDevice.user_id == current_user.id
        ).order_by(desc(UserDevice.last_used))
        
        result = await db.execute(stmt)
        devices = result.scalars().all()
        
        return {
            "status": "success",
            "count": len(devices),
            "devices": [
                {
                    "id": device.id,
                    "device_type": device.device_type,
                    "device_name": device.device_name,
                    "app_version": device.app_version,
                    "is_active": device.is_active,
                    "last_used": device.last_used.isoformat() if device.last_used else None,
                    "created_at": device.created_at.isoformat()
                }
                for device in devices
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to list devices: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list devices: {str(e)}"
        )


# ============================================================================
# BROADCAST NOTIFICATIONS (Emergency Alerts from Police)
# ============================================================================

@router.get("/broadcasts/active")
async def get_active_broadcasts(
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    current_user: AuthUser = Depends(get_current_tourist),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all active emergency broadcasts relevant to the tourist's location.
    
    Broadcasts can be:
    - RADIUS: Within specified radius from a point
    - ZONE: Within a specific safety zone
    - REGION: Within a geographic region
    - ALL: Sent to all tourists
    """
    try:
        from ..models.database_models import EmergencyBroadcast, BroadcastAcknowledgment, BroadcastType, Authority
        from datetime import datetime, timezone
        
        # Get current time
        now = datetime.now(timezone.utc)
        
        # Base query: get all active broadcasts (not expired)
        stmt = select(EmergencyBroadcast).where(
            (EmergencyBroadcast.expires_at.is_(None)) | (EmergencyBroadcast.expires_at > now)
        ).order_by(desc(EmergencyBroadcast.sent_at))
        
        result = await db.execute(stmt)
        all_broadcasts = result.scalars().all()
        
        # Check which broadcasts the tourist has acknowledged
        ack_stmt = select(BroadcastAcknowledgment).where(
            BroadcastAcknowledgment.tourist_id == current_user.id
        )
        ack_result = await db.execute(ack_stmt)
        acknowledgments = ack_result.scalars().all()
        acknowledged_ids = {ack.broadcast_id for ack in acknowledgments}
        
        # Filter broadcasts based on type and location
        relevant_broadcasts = []
        
        for broadcast in all_broadcasts:
            is_relevant = False
            distance_km = None
            
            # Type: ALL - always relevant
            if broadcast.broadcast_type == BroadcastType.ALL:
                is_relevant = True
            
            # Type: RADIUS - check if tourist is within radius
            elif broadcast.broadcast_type == BroadcastType.RADIUS and lat and lon:
                if broadcast.center_latitude and broadcast.center_longitude and broadcast.radius_km:
                    # Calculate distance using Haversine formula
                    from math import radians, cos, sin, asin, sqrt
                    
                    lon1, lat1, lon2, lat2 = map(radians, [
                        broadcast.center_longitude,
                        broadcast.center_latitude,
                        lon,
                        lat
                    ])
                    
                    dlon = lon2 - lon1
                    dlat = lat2 - lat1
                    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                    c = 2 * asin(sqrt(a))
                    distance_km = 6371 * c  # Radius of earth in kilometers
                    
                    if distance_km <= broadcast.radius_km:
                        is_relevant = True
            
            # Type: ZONE - check if tourist is in the zone (simplified - always show for now)
            elif broadcast.broadcast_type == BroadcastType.ZONE:
                is_relevant = True  # TODO: Implement actual zone checking
            
            # Type: REGION - check if tourist is in region (simplified - always show for now)
            elif broadcast.broadcast_type == BroadcastType.REGION:
                is_relevant = True  # TODO: Implement actual region checking
            
            if is_relevant:
                # Get authority info
                auth_stmt = select(Authority).where(Authority.id == broadcast.sent_by)
                auth_result = await db.execute(auth_stmt)
                authority = auth_result.scalar_one_or_none()
                
                broadcast_data = {
                    "id": broadcast.id,
                    "broadcast_id": broadcast.broadcast_id,
                    "broadcast_type": broadcast.broadcast_type.name,
                    "title": broadcast.title,
                    "message": broadcast.message,
                    "severity": broadcast.severity.name,
                    "alert_type": broadcast.alert_type,
                    "action_required": broadcast.action_required,
                    "sent_by": {
                        "id": authority.id if authority else None,
                        "name": authority.name if authority else "Unknown",
                        "department": authority.department if authority else None
                    },
                    "sent_at": broadcast.sent_at.isoformat(),
                    "expires_at": broadcast.expires_at.isoformat() if broadcast.expires_at else None,
                    "tourists_notified": broadcast.tourists_notified_count,
                    "acknowledgments": broadcast.acknowledgment_count,
                    "is_acknowledged": broadcast.id in acknowledged_ids
                }
                
                # Add location data if RADIUS type
                if broadcast.broadcast_type == BroadcastType.RADIUS:
                    broadcast_data["center"] = {
                        "lat": broadcast.center_latitude,
                        "lon": broadcast.center_longitude
                    }
                    broadcast_data["radius_km"] = broadcast.radius_km
                    if distance_km is not None:
                        broadcast_data["distance_km"] = round(distance_km, 2)
                
                relevant_broadcasts.append(broadcast_data)
        
        return {
            "active_broadcasts": relevant_broadcasts,
            "total": len(relevant_broadcasts),
            "retrieved_at": now.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get active broadcasts: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get broadcasts: {str(e)}"
        )


@router.get("/broadcasts/history")
async def get_broadcast_history(
    limit: int = 20,
    include_expired: bool = True,
    current_user: AuthUser = Depends(get_current_tourist),
    db: AsyncSession = Depends(get_db)
):
    """
    Get broadcast history (active + expired broadcasts).
    """
    try:
        from ..models.database_models import EmergencyBroadcast, BroadcastAcknowledgment
        from datetime import datetime, timezone
        
        now = datetime.now(timezone.utc)
        
        # Build query
        stmt = select(EmergencyBroadcast)
        
        if not include_expired:
            stmt = stmt.where(
                (EmergencyBroadcast.expires_at.is_(None)) | (EmergencyBroadcast.expires_at > now)
            )
        
        stmt = stmt.order_by(desc(EmergencyBroadcast.sent_at)).limit(limit)
        
        result = await db.execute(stmt)
        broadcasts = result.scalars().all()
        
        # Check acknowledgments
        ack_stmt = select(BroadcastAcknowledgment).where(
            BroadcastAcknowledgment.tourist_id == current_user.id
        )
        ack_result = await db.execute(ack_stmt)
        acknowledgments = ack_result.scalars().all()
        acknowledged_ids = {ack.broadcast_id for ack in acknowledgments}
        
        broadcast_list = []
        for broadcast in broadcasts:
            is_active = (broadcast.expires_at is None) or (broadcast.expires_at > now)
            
            broadcast_list.append({
                "id": broadcast.id,
                "broadcast_id": broadcast.broadcast_id,
                "title": broadcast.title,
                "message": broadcast.message,
                "severity": broadcast.severity.name,
                "broadcast_type": broadcast.broadcast_type.name,
                "sent_at": broadcast.sent_at.isoformat(),
                "expires_at": broadcast.expires_at.isoformat() if broadcast.expires_at else None,
                "is_active": is_active,
                "is_acknowledged": broadcast.id in acknowledged_ids
            })
        
        return {
            "broadcasts": broadcast_list,
            "total": len(broadcast_list),
            "retrieved_at": now.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get broadcast history: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get broadcast history: {str(e)}"
        )


class BroadcastAcknowledgmentRequest(BaseModel):
    status: Optional[str] = "received"  # safe, need_help, evacuating, received
    notes: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None


@router.post("/broadcasts/{broadcast_id}/acknowledge")
async def acknowledge_broadcast(
    broadcast_id: str,
    ack_data: BroadcastAcknowledgmentRequest,
    current_user: AuthUser = Depends(get_current_tourist),
    db: AsyncSession = Depends(get_db)
):
    """
    Acknowledge a broadcast notification.
    
    If status is 'need_help', an alert will be automatically sent to police dashboard.
    """
    try:
        from ..models.database_models import EmergencyBroadcast, BroadcastAcknowledgment as DBBroadcastAck, Alert, AlertType, AlertSeverity
        from datetime import datetime, timezone
        
        # Find the broadcast
        stmt = select(EmergencyBroadcast).where(
            EmergencyBroadcast.broadcast_id == broadcast_id
        )
        result = await db.execute(stmt)
        broadcast = result.scalar_one_or_none()
        
        if not broadcast:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Broadcast not found or expired"
            )
        
        # Check if already acknowledged
        check_stmt = select(DBBroadcastAck).where(
            DBBroadcastAck.broadcast_id == broadcast.id,
            DBBroadcastAck.tourist_id == current_user.id
        )
        check_result = await db.execute(check_stmt)
        existing_ack = check_result.scalar_one_or_none()
        
        if existing_ack:
            # Update existing acknowledgment
            existing_ack.status = ack_data.status
            existing_ack.notes = ack_data.notes
            existing_ack.location_lat = ack_data.lat
            existing_ack.location_lon = ack_data.lon
            existing_ack.acknowledged_at = datetime.now(timezone.utc)
        else:
            # Create new acknowledgment
            new_ack = DBBroadcastAck(
                broadcast_id=broadcast.id,
                tourist_id=current_user.id,
                status=ack_data.status,
                notes=ack_data.notes,
                location_lat=ack_data.lat,
                location_lon=ack_data.lon
            )
            db.add(new_ack)
            
            # Increment acknowledgment count
            broadcast.acknowledgment_count += 1
        
        await db.commit()
        
        # If status is 'need_help', create an alert for police
        if ack_data.status == "need_help":
            # First create location if lat/lon provided
            location_id = None
            if ack_data.lat and ack_data.lon:
                from ..models.database_models import Location
                location = Location(
                    tourist_id=current_user.id,
                    latitude=ack_data.lat,
                    longitude=ack_data.lon,
                    timestamp=datetime.now(timezone.utc)
                )
                db.add(location)
                await db.commit()
                await db.refresh(location)
                location_id = location.id
            
            alert = Alert(
                tourist_id=current_user.id,
                location_id=location_id,
                type=AlertType.MANUAL,
                severity=AlertSeverity.HIGH,
                title=f"Tourist Needs Help - Broadcast Response",
                description=f"Tourist responded 'need_help' to broadcast: {broadcast.title}. Notes: {ack_data.notes or 'None'}"
            )
            db.add(alert)
            await db.commit()
            await db.refresh(alert)
            
            # Broadcast to police dashboard via WebSocket
            await websocket_manager.publish_alert(
                channel="police_dashboard",
                alert_data={
                    "type": "alert",
                    "alert_id": alert.id,
                    "tourist_id": current_user.id,
                    "tourist_name": current_user.name,
                    "alert_type": "broadcast_help_request",
                    "severity": "high",
                    "title": alert.title,
                    "description": alert.description,
                    "location": {
                        "lat": ack_data.lat,
                        "lon": ack_data.lon
                    } if ack_data.lat and ack_data.lon else None,
                    "timestamp": alert.created_at.isoformat()
                }
            )
        
        return {
            "success": True,
            "message": "Broadcast acknowledged successfully",
            "acknowledgment_id": existing_ack.id if existing_ack else new_ack.id,
            "broadcast_id": broadcast_id,
            "status": ack_data.status,
            "acknowledged_at": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to acknowledge broadcast: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to acknowledge broadcast: {str(e)}"
        )
