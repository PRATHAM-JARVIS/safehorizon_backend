from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from ..database import get_db
from ..auth.local_auth_utils import get_current_admin, AuthUser
from ..models.database_models import Tourist, Authority, Location, Alert
from ..services.anomaly import train_anomaly_model
from ..services.sequence import train_sequence_model
from ..services.websocket_manager import websocket_manager

router = APIRouter()


class UserSuspendRequest(BaseModel):
    reason: Optional[str] = None


class RetrainRequest(BaseModel):
    model_types: List[str] = ["anomaly", "sequence"]  # Which models to retrain
    days_back: int = 30  # How many days of data to use


async def retrain_models_background(model_types: List[str], days_back: int, db: AsyncSession):
    """Background task to retrain AI models"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        # Get location data for training
        locations_query = select(Location).where(
            Location.timestamp >= cutoff_date
        ).order_by(Location.timestamp)
        
        locations_result = await db.execute(locations_query)
        locations = locations_result.scalars().all()
        
        # Convert to training data format
        training_data = [
            {
                "latitude": loc.latitude,
                "longitude": loc.longitude,
                "speed": loc.speed or 0,
                "timestamp": loc.timestamp.isoformat()
            }
            for loc in locations
        ]
        
        results = {}
        
        # Retrain anomaly model
        if "anomaly" in model_types:
            anomaly_result = await train_anomaly_model(training_data)
            results["anomaly"] = anomaly_result
        
        # Retrain sequence model
        if "sequence" in model_types:
            sequence_result = await train_sequence_model(training_data)
            results["sequence"] = sequence_result
        
        # Broadcast completion status
        await websocket_manager.publish_alert("admin", {
            "type": "retrain_complete",
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        # Broadcast error status
        await websocket_manager.publish_alert("admin", {
            "type": "retrain_error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        })


@router.get("/system/status")
async def get_system_status(
    current_user: AuthUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive system status"""
    # Database stats
    tourists_count_query = select(func.count(Tourist.id))
    tourists_result = await db.execute(tourists_count_query)
    tourists_count = tourists_result.scalar()
    
    authorities_count_query = select(func.count(Authority.id))
    authorities_result = await db.execute(authorities_count_query)
    authorities_count = authorities_result.scalar()
    
    # Active users in last 24 hours
    cutoff_time = datetime.utcnow() - timedelta(hours=24)
    active_tourists_query = select(func.count(Tourist.id)).where(
        Tourist.last_seen >= cutoff_time
    )
    active_tourists_result = await db.execute(active_tourists_query)
    active_tourists_count = active_tourists_result.scalar()
    
    # Recent alerts
    recent_alerts_query = select(func.count(Alert.id)).where(
        Alert.created_at >= cutoff_time
    )
    recent_alerts_result = await db.execute(recent_alerts_query)
    recent_alerts_count = recent_alerts_result.scalar()
    
    # WebSocket connections
    websocket_stats = websocket_manager.get_channel_stats()
    
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "database": {
            "status": "connected",
            "tourists_total": tourists_count,
            "authorities_total": authorities_count,
            "active_tourists_24h": active_tourists_count,
            "recent_alerts_24h": recent_alerts_count
        },
        "websockets": websocket_stats,
        "services": {
            "supabase": "connected",
            "redis": "connected",
            "ai_models": "loaded"
        }
    }


@router.post("/system/retrain-model")
async def retrain_system_models(
    payload: RetrainRequest,
    background_tasks: BackgroundTasks,
    current_user: AuthUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Trigger model retraining in the background"""
    # Validate model types
    valid_models = {"anomaly", "sequence"}
    invalid_models = set(payload.model_types) - valid_models
    
    if invalid_models:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid model types: {list(invalid_models)}. Valid types: {list(valid_models)}"
        )
    
    # Add background task
    background_tasks.add_task(
        retrain_models_background,
        payload.model_types,
        payload.days_back,
        db
    )
    
    return {
        "status": "retrain_started",
        "model_types": payload.model_types,
        "days_back": payload.days_back,
        "started_at": datetime.utcnow().isoformat(),
        "started_by": current_user.id
    }


@router.get("/users/list")
async def list_users(
    user_type: Optional[str] = None,  # "tourist" or "authority"
    limit: int = 100,
    current_user: AuthUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get list of users"""
    users = []
    
    if user_type != "authority":
        # Get tourists
        tourists_query = select(Tourist).order_by(desc(Tourist.created_at)).limit(limit)
        tourists_result = await db.execute(tourists_query)
        tourists = tourists_result.scalars().all()
        
        for tourist in tourists:
            users.append({
                "id": tourist.id,
                "type": "tourist",
                "email": tourist.email,
                "name": tourist.name,
                "phone": tourist.phone,
                "safety_score": tourist.safety_score,
                "is_active": tourist.is_active,
                "last_seen": tourist.last_seen.isoformat() if tourist.last_seen else None,
                "created_at": tourist.created_at.isoformat()
            })
    
    if user_type != "tourist":
        # Get authorities
        authorities_query = select(Authority).order_by(desc(Authority.created_at)).limit(limit)
        authorities_result = await db.execute(authorities_query)
        authorities = authorities_result.scalars().all()
        
        for authority in authorities:
            users.append({
                "id": authority.id,
                "type": "authority",
                "email": authority.email,
                "name": authority.name,
                "badge_number": authority.badge_number,
                "department": authority.department,
                "rank": authority.rank,
                "is_active": authority.is_active,
                "created_at": authority.created_at.isoformat()
            })
    
    return {
        "users": users,
        "total": len(users),
        "filter": user_type or "all"
    }


@router.put("/users/{user_id}/suspend")
async def suspend_user(
    user_id: str,
    payload: UserSuspendRequest,
    current_user: AuthUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Suspend a user (tourist or authority)"""
    # Try to find as tourist first
    tourist_query = select(Tourist).where(Tourist.id == user_id)
    tourist_result = await db.execute(tourist_query)
    tourist = tourist_result.scalar_one_or_none()
    
    if tourist:
        tourist.is_active = False
        await db.commit()
        
        return {
            "id": user_id,
            "type": "tourist",
            "status": "suspended",
            "reason": payload.reason,
            "suspended_by": current_user.id,
            "suspended_at": datetime.utcnow().isoformat()
        }
    
    # Try to find as authority
    authority_query = select(Authority).where(Authority.id == user_id)
    authority_result = await db.execute(authority_query)
    authority = authority_result.scalar_one_or_none()
    
    if authority:
        authority.is_active = False
        await db.commit()
        
        return {
            "id": user_id,
            "type": "authority",
            "status": "suspended",
            "reason": payload.reason,
            "suspended_by": current_user.id,
            "suspended_at": datetime.utcnow().isoformat()
        }
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )


@router.put("/users/{user_id}/activate")
async def activate_user(
    user_id: str,
    current_user: AuthUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Reactivate a suspended user"""
    # Try tourist first
    tourist_query = select(Tourist).where(Tourist.id == user_id)
    tourist_result = await db.execute(tourist_query)
    tourist = tourist_result.scalar_one_or_none()
    
    if tourist:
        tourist.is_active = True
        await db.commit()
        return {"id": user_id, "type": "tourist", "status": "activated"}
    
    # Try authority
    authority_query = select(Authority).where(Authority.id == user_id)
    authority_result = await db.execute(authority_query)
    authority = authority_result.scalar_one_or_none()
    
    if authority:
        authority.is_active = True
        await db.commit()
        return {"id": user_id, "type": "authority", "status": "activated"}
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )


@router.get("/analytics/dashboard")
async def get_analytics_dashboard(
    days: int = 7,
    current_user: AuthUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get analytics dashboard data"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Alert statistics
    alerts_by_type_query = select(
        Alert.type,
        func.count(Alert.id).label("count")
    ).where(
        Alert.created_at >= cutoff_date
    ).group_by(Alert.type)
    
    alerts_by_type_result = await db.execute(alerts_by_type_query)
    alerts_by_type = {row.type.value: row.count for row in alerts_by_type_result}
    
    # Safety score distribution
    safety_scores_query = select(Tourist.safety_score).where(
        Tourist.is_active == True,
        Tourist.safety_score.isnot(None)
    )
    
    safety_scores_result = await db.execute(safety_scores_query)
    safety_scores = [row[0] for row in safety_scores_result]
    
    # Calculate distribution
    score_ranges = {
        "critical": len([s for s in safety_scores if s < 40]),
        "high_risk": len([s for s in safety_scores if 40 <= s < 60]),
        "medium_risk": len([s for s in safety_scores if 60 <= s < 80]),
        "low_risk": len([s for s in safety_scores if s >= 80])
    }
    
    return {
        "period_days": days,
        "alerts_by_type": alerts_by_type,
        "safety_score_distribution": score_ranges,
        "average_safety_score": sum(safety_scores) / len(safety_scores) if safety_scores else 0,
        "total_active_tourists": len(safety_scores),
        "generated_at": datetime.utcnow().isoformat()
    }
