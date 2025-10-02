"""
Emergency Broadcast Service

Handles sending location-based emergency alerts to tourists.
"""
import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from math import radians, cos, sin, asin, sqrt

from ..models.database_models import (
    Tourist, Location, UserDevice, EmergencyBroadcast, 
    BroadcastAcknowledgment, RestrictedZone, BroadcastType, BroadcastSeverity
)
from .notifications import notification_service

logger = logging.getLogger(__name__)


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees).
    Returns distance in kilometers.
    """
    # Convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    km = 6371 * c
    return km


def generate_broadcast_id() -> str:
    """Generate unique broadcast ID: BCAST-YYYYMMDD-NNNN"""
    now = datetime.utcnow()
    timestamp = now.strftime("%Y%m%d-%H%M%S")
    return f"BCAST-{timestamp}"


async def find_tourists_in_radius(
    db: AsyncSession,
    center_lat: float,
    center_lon: float,
    radius_km: float
) -> List[Tourist]:
    """Find all active tourists within radius of a point"""
    # Get all active tourists with last known locations
    stmt = select(Tourist).where(
        and_(
            Tourist.is_active == True,
            Tourist.last_location_lat.isnot(None),
            Tourist.last_location_lon.isnot(None)
        )
    )
    result = await db.execute(stmt)
    all_tourists = result.scalars().all()
    
    # Filter by distance
    tourists_in_radius = []
    for tourist in all_tourists:
        distance = haversine_distance(
            center_lat, center_lon,
            tourist.last_location_lat, tourist.last_location_lon
        )
        if distance <= radius_km:
            tourists_in_radius.append(tourist)
    
    return tourists_in_radius


async def find_tourists_in_zone(
    db: AsyncSession,
    zone_id: int
) -> List[Tourist]:
    """Find all active tourists within a restricted zone"""
    # Get zone details
    zone_stmt = select(RestrictedZone).where(RestrictedZone.id == zone_id)
    zone_result = await db.execute(zone_stmt)
    zone = zone_result.scalar_one_or_none()
    
    if not zone or not zone.center_latitude:
        return []
    
    # Use zone's radius or default to 5km
    radius_km = (zone.radius_meters / 1000.0) if zone.radius_meters else 5.0
    
    # Find tourists in zone's radius
    return await find_tourists_in_radius(
        db,
        zone.center_latitude,
        zone.center_longitude,
        radius_km
    )


async def find_tourists_in_region(
    db: AsyncSession,
    min_lat: float,
    max_lat: float,
    min_lon: float,
    max_lon: float
) -> List[Tourist]:
    """Find all active tourists within a geographic region (bounding box)"""
    stmt = select(Tourist).where(
        and_(
            Tourist.is_active == True,
            Tourist.last_location_lat >= min_lat,
            Tourist.last_location_lat <= max_lat,
            Tourist.last_location_lon >= min_lon,
            Tourist.last_location_lon <= max_lon
        )
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_all_active_tourists(db: AsyncSession) -> List[Tourist]:
    """Get all active tourists"""
    stmt = select(Tourist).where(Tourist.is_active == True)
    result = await db.execute(stmt)
    return result.scalars().all()


async def send_broadcast_notifications(
    db: AsyncSession,
    tourists: List[Tourist],
    title: str,
    message: str,
    severity: str,
    broadcast_id: str,
    alert_type: Optional[str] = None,
    action_required: Optional[str] = None,
    location_data: Optional[Dict[str, Any]] = None
) -> Dict[str, int]:
    """Send push notifications to all tourists' devices"""
    
    tourist_ids = [t.id for t in tourists]
    
    # Get all active devices for these tourists
    stmt = select(UserDevice).where(
        and_(
            UserDevice.user_id.in_(tourist_ids),
            UserDevice.is_active == True
        )
    )
    result = await db.execute(stmt)
    devices = result.scalars().all()
    
    if not devices:
        logger.warning(f"No active devices found for broadcast {broadcast_id}")
        return {"tourists": 0, "devices": 0}
    
    # Prepare notification data
    notification_data = {
        "broadcast_id": broadcast_id,
        "alert_type": alert_type or "emergency",
        "severity": severity,
        "action_required": action_required or "none",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Add location data if provided
    if location_data:
        notification_data.update({
            "latitude": str(location_data.get("latitude", "")),
            "longitude": str(location_data.get("longitude", "")),
            "radius_km": str(location_data.get("radius_km", ""))
        })
    
    # Get device tokens
    tokens = [device.device_token for device in devices]
    
    # Send multicast notification
    try:
        result = await notification_service.send_push_to_multiple(
            tokens=tokens,
            title=title,
            body=message,
            data=notification_data
        )
        
        logger.info(f"Broadcast {broadcast_id}: Notified {len(tourists)} tourists on {len(devices)} devices")
        
        return {
            "tourists": len(tourists),
            "devices": len(devices)
        }
        
    except Exception as e:
        logger.error(f"Failed to send broadcast notifications: {e}")
        return {"tourists": 0, "devices": 0}


async def broadcast_radius(
    db: AsyncSession,
    authority_id: str,
    center_lat: float,
    center_lon: float,
    radius_km: float,
    title: str,
    message: str,
    severity: BroadcastSeverity,
    alert_type: Optional[str] = None,
    action_required: Optional[str] = None,
    expires_at: Optional[datetime] = None
) -> Dict[str, Any]:
    """Broadcast emergency message to tourists within radius"""
    
    # Find tourists in radius
    tourists = await find_tourists_in_radius(db, center_lat, center_lon, radius_km)
    
    if not tourists:
        logger.warning(f"No tourists found in {radius_km}km radius of ({center_lat}, {center_lon})")
    
    # Generate broadcast ID
    broadcast_id = generate_broadcast_id()
    
    # Send notifications
    notification_counts = await send_broadcast_notifications(
        db=db,
        tourists=tourists,
        title=title,
        message=message,
        severity=severity.value,
        broadcast_id=broadcast_id,
        alert_type=alert_type,
        action_required=action_required,
        location_data={
            "latitude": center_lat,
            "longitude": center_lon,
            "radius_km": radius_km
        }
    )
    
    # Save broadcast record
    broadcast = EmergencyBroadcast(
        broadcast_id=broadcast_id,
        broadcast_type=BroadcastType.RADIUS,
        title=title,
        message=message,
        severity=severity,
        alert_type=alert_type,
        action_required=action_required,
        center_latitude=center_lat,
        center_longitude=center_lon,
        radius_km=radius_km,
        tourists_notified_count=notification_counts["tourists"],
        devices_notified_count=notification_counts["devices"],
        sent_by=authority_id,
        expires_at=expires_at
    )
    
    db.add(broadcast)
    await db.commit()
    await db.refresh(broadcast)
    
    return {
        "broadcast_id": broadcast_id,
        "status": "success",
        "tourists_notified": notification_counts["tourists"],
        "devices_notified": notification_counts["devices"],
        "area_covered": f"{radius_km}km radius from ({center_lat}, {center_lon})",
        "severity": severity.value,
        "timestamp": broadcast.sent_at.isoformat()
    }


async def broadcast_zone(
    db: AsyncSession,
    authority_id: str,
    zone_id: int,
    title: str,
    message: str,
    severity: BroadcastSeverity,
    alert_type: Optional[str] = None,
    action_required: Optional[str] = None
) -> Dict[str, Any]:
    """Broadcast emergency message to tourists in a specific zone"""
    
    # Get zone details
    zone_stmt = select(RestrictedZone).where(RestrictedZone.id == zone_id)
    zone_result = await db.execute(zone_stmt)
    zone = zone_result.scalar_one_or_none()
    
    if not zone:
        raise ValueError(f"Zone {zone_id} not found")
    
    # Find tourists in zone
    tourists = await find_tourists_in_zone(db, zone_id)
    
    # Generate broadcast ID
    broadcast_id = generate_broadcast_id()
    
    # Send notifications
    notification_counts = await send_broadcast_notifications(
        db=db,
        tourists=tourists,
        title=title,
        message=message,
        severity=severity.value,
        broadcast_id=broadcast_id,
        alert_type=alert_type,
        action_required=action_required,
        location_data={
            "latitude": zone.center_latitude,
            "longitude": zone.center_longitude,
            "radius_km": (zone.radius_meters / 1000.0) if zone.radius_meters else 0
        }
    )
    
    # Save broadcast record
    broadcast = EmergencyBroadcast(
        broadcast_id=broadcast_id,
        broadcast_type=BroadcastType.ZONE,
        title=title,
        message=message,
        severity=severity,
        alert_type=alert_type,
        action_required=action_required,
        zone_id=zone_id,
        tourists_notified_count=notification_counts["tourists"],
        devices_notified_count=notification_counts["devices"],
        sent_by=authority_id
    )
    
    db.add(broadcast)
    await db.commit()
    await db.refresh(broadcast)
    
    return {
        "broadcast_id": broadcast_id,
        "status": "success",
        "zone_name": zone.name,
        "tourists_notified": notification_counts["tourists"],
        "devices_notified": notification_counts["devices"],
        "timestamp": broadcast.sent_at.isoformat()
    }


async def broadcast_region(
    db: AsyncSession,
    authority_id: str,
    min_lat: float,
    max_lat: float,
    min_lon: float,
    max_lon: float,
    title: str,
    message: str,
    severity: BroadcastSeverity,
    alert_type: Optional[str] = None,
    action_required: Optional[str] = None
) -> Dict[str, Any]:
    """Broadcast emergency message to tourists in a region"""
    
    # Find tourists in region
    tourists = await find_tourists_in_region(db, min_lat, max_lat, min_lon, max_lon)
    
    # Generate broadcast ID
    broadcast_id = generate_broadcast_id()
    
    # Send notifications
    notification_counts = await send_broadcast_notifications(
        db=db,
        tourists=tourists,
        title=title,
        message=message,
        severity=severity.value,
        broadcast_id=broadcast_id,
        alert_type=alert_type,
        action_required=action_required
    )
    
    # Save broadcast record
    region_bounds_json = json.dumps({
        "min_lat": min_lat,
        "max_lat": max_lat,
        "min_lon": min_lon,
        "max_lon": max_lon
    })
    
    broadcast = EmergencyBroadcast(
        broadcast_id=broadcast_id,
        broadcast_type=BroadcastType.REGION,
        title=title,
        message=message,
        severity=severity,
        alert_type=alert_type,
        action_required=action_required,
        region_bounds=region_bounds_json,
        tourists_notified_count=notification_counts["tourists"],
        devices_notified_count=notification_counts["devices"],
        sent_by=authority_id
    )
    
    db.add(broadcast)
    await db.commit()
    await db.refresh(broadcast)
    
    return {
        "broadcast_id": broadcast_id,
        "status": "success",
        "region": f"Lat: {min_lat} to {max_lat}, Lon: {min_lon} to {max_lon}",
        "tourists_notified": notification_counts["tourists"],
        "devices_notified": notification_counts["devices"],
        "timestamp": broadcast.sent_at.isoformat()
    }


async def broadcast_all(
    db: AsyncSession,
    authority_id: str,
    title: str,
    message: str,
    severity: BroadcastSeverity,
    alert_type: Optional[str] = None,
    action_required: Optional[str] = None
) -> Dict[str, Any]:
    """Broadcast emergency message to ALL active tourists"""
    
    # Find all active tourists
    tourists = await get_all_active_tourists(db)
    
    # Generate broadcast ID
    broadcast_id = generate_broadcast_id()
    
    # Send notifications
    notification_counts = await send_broadcast_notifications(
        db=db,
        tourists=tourists,
        title=title,
        message=message,
        severity=severity.value,
        broadcast_id=broadcast_id,
        alert_type=alert_type,
        action_required=action_required
    )
    
    # Save broadcast record
    broadcast = EmergencyBroadcast(
        broadcast_id=broadcast_id,
        broadcast_type=BroadcastType.ALL,
        title=title,
        message=message,
        severity=severity,
        alert_type=alert_type,
        action_required=action_required,
        tourists_notified_count=notification_counts["tourists"],
        devices_notified_count=notification_counts["devices"],
        sent_by=authority_id
    )
    
    db.add(broadcast)
    await db.commit()
    await db.refresh(broadcast)
    
    return {
        "broadcast_id": broadcast_id,
        "status": "success",
        "scope": "all_tourists",
        "tourists_notified": notification_counts["tourists"],
        "devices_notified": notification_counts["devices"],
        "timestamp": broadcast.sent_at.isoformat()
    }
