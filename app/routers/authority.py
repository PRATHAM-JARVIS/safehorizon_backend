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
        alerts_query = select(Alert, Tourist, Location).join(
            Tourist, Alert.tourist_id == Tourist.id
        ).outerjoin(
            Location, and_(
                Location.tourist_id == Tourist.id,
                Location.timestamp >= time_threshold
            )
        ).where(
            Alert.created_at >= time_threshold
        ).order_by(desc(Alert.created_at))
        
        alerts_result = await db.execute(alerts_query)
        alerts_data = alerts_result.all()
        
        for alert, tourist, location in alerts_data:
            # Use alert location or tourist's last known location
            alert_lat = location.lat if location else tourist.last_location_lat
            alert_lon = location.lon if location else tourist.last_location_lon
            
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
                "type": alert.alert_type.value,
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
                    if not (bounds_south <= location.lat <= bounds_north and 
                           bounds_west <= location.lon <= bounds_east):
                        continue
                
                tourist_locations[tourist.id] = {
                    "id": tourist.id,
                    "name": tourist.name,
                    "safety_score": tourist.safety_score,
                    "location": {
                        "lat": location.lat,
                        "lon": location.lon,
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
    
    alerts_query = select(Alert, Tourist, Location).join(
        Tourist, Alert.tourist_id == Tourist.id
    ).outerjoin(
        Location, and_(
            Location.tourist_id == Tourist.id,
            Location.timestamp >= time_threshold
        )
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
    for alert, tourist, location in alerts_data:
        # Use alert location or tourist's last known location
        alert_lat = location.lat if location else tourist.last_location_lat
        alert_lon = location.lon if location else tourist.last_location_lon
        
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
            "type": alert.alert_type.value,
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
            "weight": _get_alert_weight(alert.severity, alert.alert_type),
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
    )
    
    # Filter by safety score range if specified
    if min_safety_score is not None:
        tourists_query = tourists_query.where(Tourist.safety_score >= min_safety_score)
    if max_safety_score is not None:
        tourists_query = tourists_query.where(Tourist.safety_score <= max_safety_score)
    
    tourists_query = tourists_query.order_by(desc(Location.timestamp))
    tourists_result = await db.execute(tourists_query)
    tourists_data = tourists_result.all()
    
    # Group by tourist to get latest location
    tourist_locations = {}
    for tourist, location in tourists_data:
        if tourist.id not in tourist_locations and location:
            # Apply bounds filter if provided
            if all([bounds_north, bounds_south, bounds_east, bounds_west]):
                if not (bounds_south <= location.lat <= bounds_north and 
                       bounds_west <= location.lon <= bounds_east):
                    continue
            
            tourist_locations[tourist.id] = {
                "id": tourist.id,
                "name": tourist.name,
                "safety_score": tourist.safety_score,
                "location": {
                    "lat": location.lat,
                    "lon": location.lon,
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
