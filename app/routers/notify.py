from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from ..database import get_db
from ..auth.local_auth_utils import get_current_user, get_current_authority, AuthUser
from ..models.database_models import Tourist, Alert, Authority
from ..services.notifications import (
    send_push, send_sms, send_emergency_alert, send_push_to_multiple
)

router = APIRouter()


class PushRequest(BaseModel):
    user_id: Optional[str] = None
    title: str
    body: str
    token: Optional[str] = None
    data: Optional[Dict[str, str]] = None


class SmsRequest(BaseModel):
    to_number: str
    body: str


class EmergencyAlertRequest(BaseModel):
    tourist_id: str
    alert_type: str
    location: Optional[Dict[str, float]] = None
    message: Optional[str] = None


class BroadcastRequest(BaseModel):
    title: str
    body: str
    target_group: str = "all"  # "all", "tourists", "authorities"
    data: Optional[Dict[str, str]] = None


@router.post("/notify/push")
async def send_push_notification(
    req: PushRequest,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send push notification to specific user or device token"""
    try:
        if req.token:
            # Direct token notification
            result = await send_push(
                user_id=req.user_id or current_user.id,
                title=req.title,
                body=req.body,
                token=req.token
            )
        else:
            # Need to get user's device token from database
            # This would typically be stored in a user_devices table
            # For now, return an error
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Device token required or user device token lookup not implemented"
            )
        
        if result:
            return {
                "status": "push_sent",
                "user_id": req.user_id or current_user.id,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send push notification"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Push notification failed: {str(e)}"
        )


@router.post("/notify/sms")
async def send_sms_notification(
    req: SmsRequest,
    current_user: AuthUser = Depends(get_current_user)
):
    """Send SMS notification"""
    try:
        result = await send_sms(req.to_number, req.body)
        
        if result:
            return {
                "status": "sms_sent",
                "to": req.to_number,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send SMS"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SMS sending failed: {str(e)}"
        )


@router.post("/notify/emergency")
async def send_emergency_notification(
    req: EmergencyAlertRequest,
    current_user: Authority = Depends(get_current_authority),
    db: AsyncSession = Depends(get_db)
):
    """Send emergency notification for a tourist"""
    try:
        # Get tourist data
        tourist_query = select(Tourist).where(Tourist.id == req.tourist_id)
        tourist_result = await db.execute(tourist_query)
        tourist = tourist_result.scalar_one_or_none()
        
        if not tourist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tourist not found"
            )
        
        # Prepare user data
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
        
        # Prepare alert data
        alert_data = {
            "type": req.alert_type,
            "location": req.location or {
                "lat": tourist.last_location_lat,
                "lon": tourist.last_location_lon
            } if tourist.last_location_lat else None,
            "message": req.message or f"Emergency alert for {tourist.name or tourist.email}"
        }
        
        # Send emergency notifications
        results = await send_emergency_alert(user_data, alert_data)
        
        return {
            "status": "emergency_sent",
            "tourist_id": req.tourist_id,
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Emergency notification failed: {str(e)}"
        )


@router.post("/notify/broadcast")
async def broadcast_notification(
    req: BroadcastRequest,
    current_user: Authority = Depends(get_current_authority),
    db: AsyncSession = Depends(get_db)
):
    """Broadcast notification to multiple users"""
    try:
        # This would typically require a user_devices table to store FCM tokens
        # For now, we'll return a placeholder response
        
        target_count = 0
        if req.target_group == "all":
            # Count all active users
            tourists_query = select(Tourist).where(Tourist.is_active == True)
            tourists_result = await db.execute(tourists_query)
            target_count = len(tourists_result.scalars().all())
        elif req.target_group == "tourists":
            tourists_query = select(Tourist).where(Tourist.is_active == True)
            tourists_result = await db.execute(tourists_query)
            target_count = len(tourists_result.scalars().all())
        
        # In a real implementation, you would:
        # 1. Get device tokens from user_devices table
        # 2. Call send_push_to_multiple with the tokens
        
        return {
            "status": "broadcast_queued",
            "target_group": req.target_group,
            "estimated_recipients": target_count,
            "title": req.title,
            "timestamp": datetime.utcnow().isoformat(),
            "note": "Broadcast functionality requires device token storage implementation"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Broadcast failed: {str(e)}"
        )


@router.get("/notify/history")
async def get_notification_history(
    hours: int = 24,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get notification history (placeholder - would need notification_log table)"""
    try:
        # This would typically query a notification_log table
        # For now, we'll return recent alerts as a proxy
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        if current_user.role == "tourist":
            # Tourist sees their own notifications
            alerts_query = select(Alert).where(
                Alert.tourist_id == current_user.id,
                Alert.created_at >= cutoff_time
            ).order_by(desc(Alert.created_at))
        else:
            # Authority/admin sees all notifications
            alerts_query = select(Alert).where(
                Alert.created_at >= cutoff_time
            ).order_by(desc(Alert.created_at)).limit(50)
        
        alerts_result = await db.execute(alerts_query)
        alerts = alerts_result.scalars().all()
        
        notifications = [
            {
                "id": alert.id,
                "type": "alert_notification",
                "title": alert.title,
                "body": alert.description,
                "severity": alert.severity.value,
                "alert_type": alert.type.value,
                "tourist_id": alert.tourist_id,
                "created_at": alert.created_at.isoformat(),
                "acknowledged": alert.is_acknowledged
            }
            for alert in alerts
        ]
        
        return {
            "notifications": notifications,
            "period_hours": hours,
            "total": len(notifications),
            "note": "Showing alerts as notification proxy. Full notification logging to be implemented."
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get notification history: {str(e)}"
        )


@router.get("/notify/settings")
async def get_notification_settings(
    current_user: AuthUser = Depends(get_current_user)
):
    """Get notification settings for current user"""
    # This would typically come from a user_settings table
    return {
        "user_id": current_user.id,
        "push_enabled": True,
        "sms_enabled": True,
        "email_enabled": True,
        "emergency_contacts_enabled": True,
        "notification_types": {
            "safety_alerts": True,
            "geofence_warnings": True,
            "system_updates": True,
            "emergency_alerts": True
        },
        "note": "Settings are hardcoded. User preferences table to be implemented."
    }


@router.put("/notify/settings")
async def update_notification_settings(
    settings: Dict[str, Any],
    current_user: AuthUser = Depends(get_current_user)
):
    """Update notification settings for current user"""
    # This would typically update a user_settings table
    return {
        "user_id": current_user.id,
        "updated_settings": settings,
        "timestamp": datetime.utcnow().isoformat(),
        "note": "Settings update is placeholder. User preferences table to be implemented."
    }
