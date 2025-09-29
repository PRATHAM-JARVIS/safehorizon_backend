from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, and_

from ..database import get_db
from ..auth.local_auth_utils import (
    authenticate_user, create_user_account, get_current_authority, AuthUser
)
from ..models.database_models import (
    Tourist, Location, Alert, RestrictedZone, Authority, Incident, 
    AlertType, AlertSeverity, ZoneType
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
async def alerts_subscribe(
    websocket: WebSocket,
    token: str,
    current_user: Authority = Depends(get_current_authority)
):
    """Subscribe to real-time alerts via WebSocket"""
    try:
        user_data = {
            "user_id": current_user.id,
            "role": current_user.role
        }
        
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


@router.post("/efir/generate")
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
    
    # Prepare E-FIR data
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
    
    # Update incident with blockchain reference
    incident.efir_reference = blockchain_result.get("tx_id")
    await db.commit()
    
    return {
        "status": "efir_generated",
        "incident_number": incident.incident_number,
        "blockchain_tx": blockchain_result.get("tx_id"),
        "efir_data": efir_data
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
