from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..auth.local_auth_utils import get_current_user, AuthUser
from ..services.geofence import check_point, get_nearby_zones
from ..services.anomaly import score_point
from ..services.sequence import score_sequence
from ..services.scoring import compute_safety_score, get_risk_level

router = APIRouter()


class GeoFenceCheck(BaseModel):
    lat: float
    lon: float


class AnomalyPoint(BaseModel):
    lat: float
    lon: float
    speed: Optional[float] = None
    timestamp: Optional[str] = None


class SequenceSample(BaseModel):
    points: List[AnomalyPoint]


class SafetyScoreRequest(BaseModel):
    lat: float
    lon: float
    location_history: List[Dict[str, Any]] = []
    current_location_data: Dict[str, Any] = {}
    manual_adjustment: float = 0


@router.post("/ai/geofence/check")
async def ai_geofence_check(
    payload: GeoFenceCheck,
    current_user: AuthUser = Depends(get_current_user)
):
    """Check if coordinates are within restricted zones"""
    try:
        result = await check_point(payload.lat, payload.lon)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Geofence check failed: {str(e)}"
        )


@router.post("/ai/geofence/nearby")
async def ai_geofence_nearby(
    payload: GeoFenceCheck,
    radius: int = 1000,
    current_user: AuthUser = Depends(get_current_user)
):
    """Get nearby zones within specified radius"""
    try:
        zones = await get_nearby_zones(payload.lat, payload.lon, radius)
        return {
            "nearby_zones": zones,
            "radius_meters": radius,
            "center": {"lat": payload.lat, "lon": payload.lon}
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Nearby zones check failed: {str(e)}"
        )


@router.post("/ai/anomaly/point")
async def ai_anomaly_point(
    payload: AnomalyPoint,
    current_user: AuthUser = Depends(get_current_user)
):
    """Score single location point for anomaly detection"""
    try:
        # Prepare location data
        location_data = {
            "latitude": payload.lat,
            "longitude": payload.lon,
            "speed": payload.speed or 0,
            "timestamp": payload.timestamp or datetime.utcnow().isoformat()
        }
        
        score = await score_point(location_data)
        
        return {
            "anomaly_score": score,
            "risk_level": "high" if score > 0.7 else "medium" if score > 0.4 else "low",
            "location": {"lat": payload.lat, "lon": payload.lon},
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Anomaly detection failed: {str(e)}"
        )


@router.post("/ai/anomaly/sequence")
async def ai_anomaly_sequence(
    payload: SequenceSample,
    current_user: AuthUser = Depends(get_current_user)
):
    """Score sequence of location points for anomaly detection"""
    try:
        # Convert points to required format
        points_data = [
            {
                "latitude": point.lat,
                "longitude": point.lon,
                "speed": point.speed or 0,
                "timestamp": point.timestamp or datetime.utcnow().isoformat()
            }
            for point in payload.points
        ]
        
        score = await score_sequence(points_data)
        
        return {
            "sequence_anomaly_score": score,
            "risk_level": "high" if score > 0.7 else "medium" if score > 0.4 else "low",
            "sequence_length": len(payload.points),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sequence anomaly detection failed: {str(e)}"
        )


@router.post("/ai/score/compute")
async def ai_score_compute(
    payload: SafetyScoreRequest,
    current_user: AuthUser = Depends(get_current_user)
):
    """Compute comprehensive safety score"""
    try:
        # Prepare context for safety scoring
        context = {
            "lat": payload.lat,
            "lon": payload.lon,
            "location_history": payload.location_history,
            "current_location_data": payload.current_location_data or {
                "latitude": payload.lat,
                "longitude": payload.lon,
                "timestamp": datetime.utcnow().isoformat()
            },
            "manual_adjustment": payload.manual_adjustment
        }
        
        safety_score = await compute_safety_score(context)
        
        return {
            "safety_score": safety_score,
            "risk_level": get_risk_level(safety_score),
            "components": {
                "geofence": "evaluated",
                "anomaly": "evaluated",
                "sequence": "evaluated" if len(payload.location_history) >= 5 else "insufficient_data",
                "manual_adjustment": payload.manual_adjustment
            },
            "location": {"lat": payload.lat, "lon": payload.lon},
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Safety score computation failed: {str(e)}"
        )


@router.post("/ai/classify/alert")
async def ai_classify_alert(
    payload: Dict[str, Any],
    current_user: AuthUser = Depends(get_current_user)
):
    """Classify alert severity (placeholder for future ML classifier)"""
    try:
        # Extract features from payload
        safety_score = payload.get("safety_score", 50)
        alert_type = payload.get("alert_type", "unknown")
        location_data = payload.get("location_data", {})
        
        # Simple rule-based classification (replace with ML model later)
        if safety_score < 30:
            label = "critical"
            confidence = 0.9
        elif safety_score < 50:
            label = "high"
            confidence = 0.8
        elif safety_score < 70:
            label = "medium"
            confidence = 0.7
        else:
            label = "low"
            confidence = 0.6
        
        # Boost confidence for certain alert types
        if alert_type == "sos":
            label = "critical"
            confidence = 1.0
        elif alert_type == "panic":
            label = "high"
            confidence = 0.95
        
        return {
            "classification": {
                "label": label,
                "confidence": confidence
            },
            "features": {
                "safety_score": safety_score,
                "alert_type": alert_type,
                "location_available": bool(location_data)
            },
            "model_info": {
                "type": "rule_based",
                "note": "ML classifier to be implemented"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Alert classification failed: {str(e)}"
        )


@router.get("/ai/models/status")
async def ai_models_status(
    current_user: AuthUser = Depends(get_current_user)
):
    """Get status of AI models"""
    return {
        "models": {
            "isolation_forest": {
                "status": "loaded",
                "type": "anomaly_detection",
                "last_trained": "placeholder"
            },
            "lstm_autoencoder": {
                "status": "loaded",
                "type": "sequence_analysis",
                "last_trained": "placeholder"
            },
            "geofence": {
                "status": "active",
                "type": "rule_based",
                "zones_count": "dynamic"
            },
            "safety_scorer": {
                "status": "active",
                "type": "composite",
                "components": ["geofence", "anomaly", "sequence"]
            }
        },
        "timestamp": datetime.utcnow().isoformat()
    }
