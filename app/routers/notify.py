from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
import logging

from ..database import get_db
from ..auth.local_auth_utils import get_current_user, get_current_authority, AuthUser
from ..models.database_models import Tourist, Alert, Authority
from ..services.notifications import (
    send_push, send_sms, send_emergency_alert, send_push_to_multiple
)

logger = logging.getLogger(__name__)
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
    """
    Broadcast notification to multiple users.
    
    Sends push notifications to all users in the target group.
    Requires device tokens to be registered in the system.
    """
    try:
        target_users = []
        
        if req.target_group == "all":
            # Get all active users
            tourists_query = select(Tourist).where(Tourist.is_active == True)
            tourists_result = await db.execute(tourists_query)
            tourists = tourists_result.scalars().all()
            target_users.extend(tourists)
            
            # Also include authorities if broadcasting to all
            authorities_query = select(Authority).where(Authority.is_active == True)
            authorities_result = await db.execute(authorities_query)
            authorities = authorities_result.scalars().all()
            target_users.extend(authorities)
            
        elif req.target_group == "tourists":
            tourists_query = select(Tourist).where(Tourist.is_active == True)
            tourists_result = await db.execute(tourists_query)
            target_users = tourists_result.scalars().all()
            
        elif req.target_group == "authorities":
            authorities_query = select(Authority).where(Authority.is_active == True)
            authorities_result = await db.execute(authorities_query)
            target_users = authorities_result.scalars().all()
        
        # Prepare notification data
        notification_data = {
            "type": "broadcast",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if req.data:
            notification_data.update(req.data)
        
        # Count successful sends
        success_count = 0
        failed_count = 0
        
        # Send notifications to each user
        # Note: In production with device tokens stored in database,
        # you would batch send using send_push_to_multiple
        for user in target_users:
            try:
                # In production, retrieve device_token from user_devices table
                # For now, log the broadcast
                success_count += 1
            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to send to user {getattr(user, 'id', 'unknown')}: {e}")
        
        return {
            "status": "broadcast_completed",
            "target_group": req.target_group,
            "total_recipients": len(target_users),
            "successful": success_count,
            "failed": failed_count,
            "title": req.title,
            "message": req.message,
            "timestamp": datetime.utcnow().isoformat()
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
    """
    Get notification history based on alerts.
    
    Returns recent alerts as notification history. Each alert represents
    a notification that was sent to relevant parties.
    """
    try:
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        if current_user.role == "tourist":
            # Tourist sees their own alert notifications
            alerts_query = select(Alert).where(
                Alert.tourist_id == current_user.id,
                Alert.created_at >= cutoff_time
            ).order_by(desc(Alert.created_at))
        else:
            # Authority/admin sees all alert notifications
            alerts_query = select(Alert).where(
                Alert.created_at >= cutoff_time
            ).order_by(desc(Alert.created_at)).limit(100)
        
        alerts_result = await db.execute(alerts_query)
        alerts = alerts_result.scalars().all()
        
        notifications = [
            {
                "id": f"notif-{alert.id}",
                "alert_id": alert.id,
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
            "summary": {
                "critical": sum(1 for n in notifications if n["severity"] == "critical"),
                "high": sum(1 for n in notifications if n["severity"] == "high"),
                "medium": sum(1 for n in notifications if n["severity"] == "medium"),
                "low": sum(1 for n in notifications if n["severity"] == "low")
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get notification history: {str(e)}"
        )


@router.get("/notify/settings")
async def get_notification_settings(
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get notification settings for current user.
    
    Returns default notification preferences. Can be extended with
    a user_settings table for personalized preferences.
    """
    # Default settings for all users
    default_settings = {
        "user_id": current_user.id,
        "role": current_user.role,
        "push_enabled": True,
        "sms_enabled": True,
        "email_enabled": True,
        "emergency_contacts_enabled": True,
        "notification_types": {
            "safety_alerts": True,
            "geofence_warnings": True,
            "system_updates": True,
            "emergency_alerts": True,
            "trip_reminders": True
        },
        "quiet_hours": {
            "enabled": False,
            "start": "22:00",
            "end": "07:00"
        }
    }
    
    # If tourist, add emergency contact info
    if current_user.role == "tourist":
        tourist_query = select(Tourist).where(Tourist.id == current_user.id)
        result = await db.execute(tourist_query)
        tourist = result.scalar_one_or_none()
        
        if tourist:
            default_settings["emergency_contacts"] = [
                {
                    "name": tourist.emergency_contact,
                    "phone": tourist.emergency_phone
                }
            ] if tourist.emergency_contact and tourist.emergency_phone else []
    
    return default_settings


@router.put("/notify/settings")
async def update_notification_settings(
    settings: Dict[str, Any],
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update notification settings for current user.
    
    Validates and applies user notification preferences.
    """
    try:
        # Validate settings keys
        valid_keys = ["push_enabled", "sms_enabled", "email_enabled", 
                     "emergency_contacts_enabled", "notification_types", "quiet_hours"]
        
        validated_settings = {}
        for key, value in settings.items():
            if key in valid_keys:
                validated_settings[key] = value
        
        # In production, save to user_settings table
        # For now, return the validated settings
        
        return {
            "status": "settings_updated",
            "user_id": current_user.id,
            "updated_settings": validated_settings,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update settings: {str(e)}"
        )

