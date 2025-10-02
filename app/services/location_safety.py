"""
AI-Driven Location Safety Score Service

This service calculates dynamic safety scores for locations based on:
- Nearby recent alerts (temporal and spatial proximity)
- Zone risk levels (geofence data)
- Historical incident patterns
- Crowd density
- Time of day risk patterns
- Speed anomalies
- Distance from safe zones
"""

import math
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from ..models.database_models import Location, Alert, RestrictedZone, Tourist, AlertType, AlertSeverity
from ..services.geofence import _haversine_distance


class LocationSafetyScoreCalculator:
    """
    Advanced AI-driven safety score calculator for locations.
    Considers multiple factors to determine real-time safety.
    """
    
    # Configuration constants
    ALERT_RADIUS_KM = 2.0  # Consider alerts within 2km
    ALERT_TIME_WINDOW_HOURS = 6  # Consider alerts from last 6 hours
    SAFE_ZONE_RADIUS_KM = 1.0  # Consider safe zones within 1km
    
    # Weight factors for different components
    WEIGHTS = {
        'nearby_alerts': 0.30,      # 30% - Recent incidents nearby
        'zone_risk': 0.25,          # 25% - Area risk level
        'time_of_day': 0.15,        # 15% - Time-based risk
        'crowd_density': 0.10,      # 10% - Number of tourists nearby
        'speed_anomaly': 0.10,      # 10% - Unusual speed patterns
        'historical_risk': 0.10     # 10% - Historical incident data
    }
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def calculate_safety_score(
        self,
        latitude: float,
        longitude: float,
        tourist_id: str,
        speed: Optional[float] = None,
        timestamp: Optional[datetime] = None
    ) -> Dict:
        """
        Calculate comprehensive safety score for a location.
        
        Returns:
            Dict containing:
            - safety_score: 0-100 (100 = safest)
            - risk_level: critical/high/medium/low
            - factors: breakdown of all contributing factors
            - recommendations: AI-generated safety recommendations
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        # Calculate all safety factors
        nearby_alerts_score = await self._calculate_nearby_alerts_score(latitude, longitude, timestamp)
        zone_risk_score = await self._calculate_zone_risk_score(latitude, longitude)
        time_risk_score = self._calculate_time_of_day_score(timestamp)
        crowd_density_score = await self._calculate_crowd_density_score(latitude, longitude, timestamp)
        speed_anomaly_score = await self._calculate_speed_anomaly_score(speed, tourist_id)
        historical_risk_score = await self._calculate_historical_risk_score(latitude, longitude)
        
        # Weighted composite score
        composite_score = (
            nearby_alerts_score * self.WEIGHTS['nearby_alerts'] +
            zone_risk_score * self.WEIGHTS['zone_risk'] +
            time_risk_score * self.WEIGHTS['time_of_day'] +
            crowd_density_score * self.WEIGHTS['crowd_density'] +
            speed_anomaly_score * self.WEIGHTS['speed_anomaly'] +
            historical_risk_score * self.WEIGHTS['historical_risk']
        )
        
        # Ensure score is within bounds
        final_score = max(0.0, min(100.0, composite_score))
        
        # Determine risk level
        risk_level = self._get_risk_level(final_score)
        
        # Generate AI recommendations
        recommendations = self._generate_recommendations(
            final_score,
            nearby_alerts_score,
            zone_risk_score,
            time_risk_score,
            crowd_density_score
        )
        
        return {
            'safety_score': round(final_score, 2),
            'risk_level': risk_level,
            'factors': {
                'nearby_alerts': {
                    'score': round(nearby_alerts_score, 2),
                    'weight': self.WEIGHTS['nearby_alerts'],
                    'contribution': round(nearby_alerts_score * self.WEIGHTS['nearby_alerts'], 2)
                },
                'zone_risk': {
                    'score': round(zone_risk_score, 2),
                    'weight': self.WEIGHTS['zone_risk'],
                    'contribution': round(zone_risk_score * self.WEIGHTS['zone_risk'], 2)
                },
                'time_of_day': {
                    'score': round(time_risk_score, 2),
                    'weight': self.WEIGHTS['time_of_day'],
                    'contribution': round(time_risk_score * self.WEIGHTS['time_of_day'], 2)
                },
                'crowd_density': {
                    'score': round(crowd_density_score, 2),
                    'weight': self.WEIGHTS['crowd_density'],
                    'contribution': round(crowd_density_score * self.WEIGHTS['crowd_density'], 2)
                },
                'speed_anomaly': {
                    'score': round(speed_anomaly_score, 2),
                    'weight': self.WEIGHTS['speed_anomaly'],
                    'contribution': round(speed_anomaly_score * self.WEIGHTS['speed_anomaly'], 2)
                },
                'historical_risk': {
                    'score': round(historical_risk_score, 2),
                    'weight': self.WEIGHTS['historical_risk'],
                    'contribution': round(historical_risk_score * self.WEIGHTS['historical_risk'], 2)
                }
            },
            'recommendations': recommendations,
            'calculated_at': timestamp.isoformat()
        }
    
    async def _calculate_nearby_alerts_score(
        self, 
        latitude: float, 
        longitude: float,
        timestamp: datetime
    ) -> float:
        """
        Calculate safety score based on nearby recent alerts.
        Lower score = more nearby alerts = less safe.
        """
        time_threshold = timestamp - timedelta(hours=self.ALERT_TIME_WINDOW_HOURS)
        
        # Get all recent alerts with locations
        query = select(Alert).where(
            and_(
                Alert.created_at >= time_threshold,
                Alert.location_id.isnot(None)
            )
        )
        result = await self.db.execute(query)
        alerts = result.scalars().all()
        
        if not alerts:
            return 100.0
        
        # Fetch locations for alerts
        location_ids = [a.location_id for a in alerts if a.location_id]
        if not location_ids:
            return 100.0
        
        locations_query = select(Location).where(Location.id.in_(location_ids))
        locations_result = await self.db.execute(locations_query)
        locations = {loc.id: loc for loc in locations_result.scalars().all()}
        
        # Calculate impact of each alert
        total_impact = 0.0
        nearby_alerts = 0
        
        for alert in alerts:
            if alert.location_id not in locations:
                continue
            
            alert_loc = locations[alert.location_id]
            distance_km = _haversine_distance(
                latitude, longitude,
                alert_loc.latitude, alert_loc.longitude
            )
            
            if distance_km <= self.ALERT_RADIUS_KM:
                nearby_alerts += 1
                
                # Distance decay factor (closer = more impact)
                distance_factor = max(0, 1 - (distance_km / self.ALERT_RADIUS_KM))
                
                # Time decay factor (recent = more impact)
                hours_ago = (timestamp - alert.created_at).total_seconds() / 3600
                time_factor = max(0, 1 - (hours_ago / self.ALERT_TIME_WINDOW_HOURS))
                
                # Severity factor
                severity_weights = {
                    AlertSeverity.critical: 1.0,
                    AlertSeverity.high: 0.7,
                    AlertSeverity.medium: 0.4,
                    AlertSeverity.low: 0.2
                }
                severity_factor = severity_weights.get(alert.severity, 0.4)
                
                # Combined impact
                impact = distance_factor * time_factor * severity_factor * 20
                total_impact += impact
        
        # Calculate final score (more impact = lower score)
        score = max(0, 100 - total_impact)
        return score
    
    async def _calculate_zone_risk_score(self, latitude: float, longitude: float) -> float:
        """
        Calculate safety score based on zone types.
        Safe zones increase score, restricted/risky zones decrease it.
        """
        # Get all zones
        query = select(RestrictedZone).where(RestrictedZone.is_active == True)
        result = await self.db.execute(query)
        zones = result.scalars().all()
        
        base_score = 70.0  # Neutral score for unknown areas
        
        for zone in zones:
            center_lat = zone.center_latitude
            center_lon = zone.center_longitude
            radius_km = zone.radius_meters / 1000.0
            
            distance_km = _haversine_distance(latitude, longitude, center_lat, center_lon)
            
            # Check if location is within or near the zone
            if distance_km <= radius_km:
                # Inside zone
                if zone.zone_type == "safe":
                    return 95.0  # High score for safe zones
                elif zone.zone_type == "restricted":
                    return 20.0  # Very low score for restricted zones
                elif zone.zone_type == "risky":
                    return 40.0  # Low score for risky zones
            elif distance_km <= radius_km + self.SAFE_ZONE_RADIUS_KM:
                # Near zone - partial effect
                proximity_factor = 1 - ((distance_km - radius_km) / self.SAFE_ZONE_RADIUS_KM)
                
                if zone.zone_type == "safe":
                    base_score = max(base_score, 70 + (25 * proximity_factor))
                elif zone.zone_type == "restricted":
                    base_score = min(base_score, 70 - (50 * proximity_factor))
                elif zone.zone_type == "risky":
                    base_score = min(base_score, 70 - (30 * proximity_factor))
        
        return base_score
    
    def _calculate_time_of_day_score(self, timestamp: datetime) -> float:
        """
        Calculate risk based on time of day.
        Late night hours are riskier than daytime.
        """
        hour = timestamp.hour
        
        # Risk patterns (24-hour format)
        if 6 <= hour < 9:  # Early morning
            return 75.0
        elif 9 <= hour < 18:  # Daytime
            return 85.0
        elif 18 <= hour < 21:  # Evening
            return 70.0
        elif 21 <= hour < 24:  # Night
            return 50.0
        else:  # Late night (0-6)
            return 40.0
    
    async def _calculate_crowd_density_score(
        self,
        latitude: float,
        longitude: float,
        timestamp: datetime
    ) -> float:
        """
        Calculate safety based on crowd density.
        More tourists nearby = safer (safety in numbers).
        """
        # Get recent locations within radius
        time_threshold = timestamp - timedelta(minutes=30)
        
        # Count nearby tourists
        query = select(func.count(Location.id)).where(
            and_(
                Location.timestamp >= time_threshold,
                Location.latitude.between(latitude - 0.02, latitude + 0.02),  # ~2km approx
                Location.longitude.between(longitude - 0.02, longitude + 0.02)
            )
        )
        result = await self.db.execute(query)
        nearby_count = result.scalar() or 0
        
        # More people = safer (up to a point)
        if nearby_count == 0:
            return 50.0  # Isolated location
        elif nearby_count <= 3:
            return 65.0
        elif nearby_count <= 10:
            return 80.0
        elif nearby_count <= 20:
            return 90.0
        else:
            return 85.0  # Too crowded might be slightly risky
    
    async def _calculate_speed_anomaly_score(
        self,
        current_speed: Optional[float],
        tourist_id: str
    ) -> float:
        """
        Detect unusual speed patterns that might indicate danger.
        Very high speed might indicate emergency/panic.
        """
        if current_speed is None:
            return 85.0  # Neutral score if no speed data
        
        # Get tourist's historical speed data
        query = select(Location.speed).where(
            and_(
                Location.tourist_id == tourist_id,
                Location.speed.isnot(None)
            )
        ).order_by(Location.timestamp.desc()).limit(50)
        
        result = await self.db.execute(query)
        historical_speeds = [s for s in result.scalars().all() if s is not None]
        
        if not historical_speeds:
            return 85.0
        
        # Calculate average and std deviation
        avg_speed = sum(historical_speeds) / len(historical_speeds)
        variance = sum((s - avg_speed) ** 2 for s in historical_speeds) / len(historical_speeds)
        std_dev = math.sqrt(variance) if variance > 0 else 1.0
        
        # Check if current speed is anomalous
        if std_dev > 0:
            z_score = abs(current_speed - avg_speed) / std_dev
        else:
            z_score = 0
        
        # High z-score = anomalous = potential risk
        if z_score > 3:  # Very anomalous
            return 40.0
        elif z_score > 2:  # Moderately anomalous
            return 60.0
        elif z_score > 1:  # Slightly anomalous
            return 75.0
        else:
            return 90.0  # Normal pattern
    
    async def _calculate_historical_risk_score(
        self,
        latitude: float,
        longitude: float
    ) -> float:
        """
        Calculate risk based on historical incident data in this area.
        Areas with more past incidents are riskier.
        """
        # Look at incidents in the past 30 days
        time_threshold = datetime.now(timezone.utc) - timedelta(days=30)
        
        # Count alerts in nearby area
        query = select(func.count(Alert.id)).where(
            Alert.created_at >= time_threshold
        )
        result = await self.db.execute(query)
        total_alerts = result.scalar() or 0
        
        if total_alerts == 0:
            return 90.0
        
        # Get locations for these alerts
        alerts_query = select(Alert).where(
            and_(
                Alert.created_at >= time_threshold,
                Alert.location_id.isnot(None)
            )
        )
        alerts_result = await self.db.execute(alerts_query)
        alerts = alerts_result.scalars().all()
        
        # Count alerts near this location
        nearby_historical_alerts = 0
        
        for alert in alerts:
            if alert.location_id:
                loc_query = select(Location).where(Location.id == alert.location_id)
                loc_result = await self.db.execute(loc_query)
                alert_location = loc_result.scalar_one_or_none()
                
                if alert_location:
                    distance = _haversine_distance(
                        latitude, longitude,
                        alert_location.latitude, alert_location.longitude
                    )
                    
                    if distance <= 1.0:  # Within 1km
                        nearby_historical_alerts += 1
        
        # More historical alerts = lower score
        if nearby_historical_alerts == 0:
            return 90.0
        elif nearby_historical_alerts <= 2:
            return 75.0
        elif nearby_historical_alerts <= 5:
            return 60.0
        elif nearby_historical_alerts <= 10:
            return 45.0
        else:
            return 30.0
    
    def _get_risk_level(self, score: float) -> str:
        """Convert numeric score to risk level category."""
        if score >= 80:
            return "low"
        elif score >= 60:
            return "medium"
        elif score >= 40:
            return "high"
        else:
            return "critical"
    
    def _generate_recommendations(
        self,
        final_score: float,
        nearby_alerts_score: float,
        zone_risk_score: float,
        time_risk_score: float,
        crowd_density_score: float
    ) -> List[str]:
        """Generate AI-driven safety recommendations based on scores."""
        recommendations = []
        
        if final_score < 40:
            recommendations.append("⚠️ CRITICAL: Leave this area immediately and contact authorities")
        elif final_score < 60:
            recommendations.append("⚠️ HIGH RISK: Consider moving to a safer location")
        
        if nearby_alerts_score < 50:
            recommendations.append("🚨 Multiple recent incidents reported nearby - stay alert")
        
        if zone_risk_score < 50:
            recommendations.append("⛔ You are in or near a restricted/risky zone - relocate to safe area")
        
        if time_risk_score < 60:
            recommendations.append("🌙 Late hours increase risk - avoid isolated areas")
        
        if crowd_density_score < 60:
            recommendations.append("👥 Low crowd density - try to move to more populated areas")
        
        if final_score >= 80:
            recommendations.append("✅ Location appears safe - continue enjoying your trip")
        
        if not recommendations:
            recommendations.append("ℹ️ Maintain normal safety precautions")
        
        return recommendations


async def update_location_safety_scores(db: AsyncSession, hours_back: int = 1):
    """
    Background task to recalculate safety scores for recent locations.
    Should be run periodically (every 5-10 minutes).
    """
    calculator = LocationSafetyScoreCalculator(db)
    time_threshold = datetime.now(timezone.utc) - timedelta(hours=hours_back)
    
    # Get all recent locations that need updating
    query = select(Location).where(
        or_(
            Location.safety_score_updated_at.is_(None),
            Location.safety_score_updated_at < time_threshold,
            Location.timestamp >= time_threshold
        )
    ).order_by(Location.timestamp.desc()).limit(1000)
    
    result = await db.execute(query)
    locations = result.scalars().all()
    
    updated_count = 0
    
    for location in locations:
        try:
            # Calculate new safety score
            safety_data = await calculator.calculate_safety_score(
                latitude=location.latitude,
                longitude=location.longitude,
                tourist_id=location.tourist_id,
                speed=location.speed,
                timestamp=location.timestamp
            )
            
            # Update location
            location.safety_score = safety_data['safety_score']
            location.safety_score_updated_at = datetime.now(timezone.utc)
            
            updated_count += 1
            
        except Exception as e:
            print(f"Error updating safety score for location {location.id}: {e}")
            continue
    
    await db.commit()
    
    return {
        'updated_count': updated_count,
        'total_processed': len(locations),
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
