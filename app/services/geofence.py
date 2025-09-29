import math
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, func
from ..models.database_models import RestrictedZone, ZoneType
from ..database import AsyncSessionLocal


def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance between two points on earth in meters"""
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of earth in meters
    r = 6371000
    return c * r


async def check_point(lat: float, lon: float) -> Dict[str, Any]:
    """Check if a point is inside any restricted zones using simple distance calculation"""
    async with AsyncSessionLocal() as session:
        # Query all active zones
        query = select(RestrictedZone).where(RestrictedZone.is_active == True)
        
        result = await session.execute(query)
        zones = result.scalars().all()
        
        matching_zones = []
        
        # Check each zone using simple distance calculation
        for zone in zones:
            # Calculate distance from point to zone center
            distance = _haversine_distance(
                lat, lon, 
                zone.center_latitude, zone.center_longitude
            )
            
            # Check if point is within zone radius (default 1km if not specified)
            zone_radius = zone.radius_meters or 1000
            if distance <= zone_radius:
                matching_zones.append(zone)
        
        if not matching_zones:
            return {
                "inside_restricted": False,
                "zones": [],
                "risk_level": "safe"
            }
        
        # Determine the highest risk level
        zone_data = []
        max_risk = "safe"
        
        for zone in matching_zones:
            zone_info = {
                "id": zone.id,
                "name": zone.name,
                "type": zone.zone_type.value,
                "description": zone.description
            }
            zone_data.append(zone_info)
            
            # Update max risk level
            if zone.zone_type == ZoneType.RESTRICTED:
                max_risk = "restricted"
            elif zone.zone_type == ZoneType.RISKY and max_risk != "restricted":
                max_risk = "risky"
        
        return {
            "inside_restricted": len(matching_zones) > 0,
            "zones": zone_data,
            "risk_level": max_risk,
            "zone_count": len(matching_zones)
        }


async def get_nearby_zones(lat: float, lon: float, radius_meters: int = 1000) -> List[Dict[str, Any]]:
    """Get zones within a specified radius of a point"""
    async with AsyncSessionLocal() as session:
        # Query all active zones
        query = select(RestrictedZone).where(RestrictedZone.is_active == True)
        result = await session.execute(query)
        zones = result.scalars().all()
        
        zone_data = []
        for zone in zones:
            # Calculate distance from point to zone center
            distance = _haversine_distance(
                lat, lon, 
                zone.center_latitude, zone.center_longitude
            )
            
            # Include zones within the specified radius
            if distance <= radius_meters:
                zone_info = {
                    "id": zone.id,
                    "name": zone.name,
                    "type": zone.zone_type.value,
                    "description": zone.description,
                    "distance_meters": round(distance, 2)
                }
                zone_data.append(zone_info)
        
        return zone_data


async def create_zone(
    name: str,
    description: str,
    zone_type: str,  # Use string and convert to enum
    coordinates: List[List[float]],  # List of [lon, lat] pairs
    created_by: Optional[str] = None,
    radius_meters: Optional[float] = None
) -> Dict[str, Any]:
    """Create a new restricted zone from coordinates"""
    async with AsyncSessionLocal() as session:
        # Calculate center point from coordinates
        if coordinates:
            center_lat = sum(coord[1] for coord in coordinates) / len(coordinates)
            center_lon = sum(coord[0] for coord in coordinates) / len(coordinates)
        else:
            raise ValueError("Coordinates are required")
        
        # Use provided radius or calculate approximate radius from coordinates
        if radius_meters is None:
            # Calculate approximate radius as distance from center to farthest point
            max_distance = 0
            for coord in coordinates:
                distance = _haversine_distance(center_lat, center_lon, coord[1], coord[0])
                max_distance = max(max_distance, distance)
            radius_meters = max_distance or 1000  # Default 1km if no distance
        
        # Convert string to ZoneType enum
        try:
            if isinstance(zone_type, str):
                zone_type_enum = ZoneType(zone_type.lower())
            else:
                zone_type_enum = zone_type
        except ValueError:
            raise ValueError(f"Invalid zone type: {zone_type}. Must be one of: safe, risky, restricted")
        
        zone = RestrictedZone(
            name=name,
            description=description,
            zone_type=zone_type_enum,
            center_latitude=center_lat,
            center_longitude=center_lon,
            radius_meters=radius_meters,
            bounds_json=str(coordinates),  # Store original coordinates as JSON string
            created_by=created_by
        )
        
        session.add(zone)
        await session.commit()
        await session.refresh(zone)
        
        return {
            "id": zone.id,
            "name": zone.name,
            "type": zone.zone_type.value,
            "description": zone.description,
            "center": {"lat": center_lat, "lon": center_lon},
            "radius_meters": radius_meters,
            "created_at": zone.created_at.isoformat()
        }


async def get_all_zones() -> List[Dict[str, Any]]:
    """Get all active zones"""
    async with AsyncSessionLocal() as session:
        query = select(RestrictedZone).where(RestrictedZone.is_active == True)
        result = await session.execute(query)
        zones = result.scalars().all()
        
        zone_data = []
        for zone in zones:
            zone_info = {
                "id": zone.id,
                "name": zone.name,
                "type": zone.zone_type.value,
                "description": zone.description,
                "is_active": zone.is_active,
                "created_at": zone.created_at.isoformat()
            }
            zone_data.append(zone_info)
        
        return zone_data


async def delete_zone(zone_id: int) -> bool:
    """Soft delete a zone by setting is_active to False"""
    async with AsyncSessionLocal() as session:
        query = select(RestrictedZone).where(RestrictedZone.id == zone_id)
        result = await session.execute(query)
        zone = result.scalar_one_or_none()
        
        if not zone:
            return False
        
        zone.is_active = False
        await session.commit()
        return True
