from typing import Optional, Dict, Any, List
import asyncio
import json
import os
import logging
from datetime import datetime

# Firebase Admin SDK
try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    logging.warning("Firebase Admin SDK not available")

# Twilio SDK
try:
    from twilio.rest import Client as TwilioClient
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    logging.warning("Twilio SDK not available")

from ..config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class NotificationService:
    def __init__(self):
        self.firebase_app = None
        self.twilio_client = None
        self._initialize_firebase()
        self._initialize_twilio()
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        if not FIREBASE_AVAILABLE:
            return
        
        if not settings.firebase_credentials_json_path:
            logger.warning("Firebase credentials path not configured")
            return
        
        if not os.path.exists(settings.firebase_credentials_json_path):
            logger.warning(f"Firebase credentials file not found: {settings.firebase_credentials_json_path}")
            return
        
        try:
            if not firebase_admin._apps:  # Check if Firebase is already initialized
                cred = credentials.Certificate(settings.firebase_credentials_json_path)
                self.firebase_app = firebase_admin.initialize_app(cred)
            else:
                self.firebase_app = firebase_admin.get_app()
            logger.info("Firebase Admin SDK initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
    
    def _initialize_twilio(self):
        """Initialize Twilio client"""
        if not TWILIO_AVAILABLE:
            return
        
        if not settings.twilio_account_sid or not settings.twilio_auth_token:
            logger.warning("Twilio credentials not configured")
            return
        
        try:
            self.twilio_client = TwilioClient(
                settings.twilio_account_sid,
                settings.twilio_auth_token
            )
            logger.info("Twilio client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Twilio: {e}")
    
    async def send_push_notification(
        self, 
        token: str, 
        title: str, 
        body: str, 
        data: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Send push notification via Firebase"""
        if not self.firebase_app or not FIREBASE_AVAILABLE:
            return {
                "success": False,
                "error": "Firebase not available or configured"
            }
        
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data or {},
                token=token,
            )
            
            # Send the message
            response = messaging.send(message)
            
            return {
                "success": True,
                "message_id": response,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Failed to send push notification: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_push_to_multiple(
        self, 
        tokens: List[str], 
        title: str, 
        body: str, 
        data: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Send push notification to multiple devices"""
        if not self.firebase_app or not FIREBASE_AVAILABLE:
            return {
                "success": False,
                "error": "Firebase not available or configured"
            }
        
        try:
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data or {},
                tokens=tokens,
            )
            
            response = messaging.send_multicast(message)
            
            return {
                "success": True,
                "success_count": response.success_count,
                "failure_count": response.failure_count,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Failed to send multicast push notification: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_sms(self, to_number: str, body: str) -> Dict[str, Any]:
        """Send SMS via Twilio"""
        if not self.twilio_client or not TWILIO_AVAILABLE:
            return {
                "success": False,
                "error": "Twilio not available or configured"
            }
        
        if not settings.twilio_from_number:
            return {
                "success": False,
                "error": "Twilio from number not configured"
            }
        
        try:
            # Format phone number if needed
            if not to_number.startswith('+'):
                to_number = f"+{to_number}"
            
            message = self.twilio_client.messages.create(
                body=body,
                from_=settings.twilio_from_number,
                to=to_number
            )
            
            return {
                "success": True,
                "message_sid": message.sid,
                "status": message.status,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_emergency_notifications(
        self, 
        user_data: Dict[str, Any], 
        alert_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send emergency notifications via multiple channels"""
        results = {
            "push": None,
            "sms": None,
            "emergency_contacts": []
        }
        
        # Prepare notification content
        title = f"🚨 {alert_data.get('type', 'EMERGENCY').upper()} Alert"
        body = f"Emergency alert for {user_data.get('name', 'tourist')}. Location: {alert_data.get('location', 'Unknown')}"
        
        # Send push notification if device token available
        if user_data.get('device_token'):
            push_result = await self.send_push_notification(
                token=user_data['device_token'],
                title=title,
                body=body,
                data={
                    "alert_id": str(alert_data.get('id', '')),
                    "type": "emergency",
                    "severity": alert_data.get('severity', 'high')
                }
            )
            results["push"] = push_result
        
        # Send SMS to user if phone available
        if user_data.get('phone'):
            sms_result = await self.send_sms(
                to_number=user_data['phone'],
                body=f"{title}: {body}"
            )
            results["sms"] = sms_result
        
        # Send SMS to emergency contacts
        emergency_contacts = user_data.get('emergency_contacts', [])
        for contact in emergency_contacts:
            if contact.get('phone'):
                emergency_body = f"Emergency: {user_data.get('name', 'A tourist')} needs help. {body}"
                contact_result = await self.send_sms(
                    to_number=contact['phone'],
                    body=emergency_body
                )
                results["emergency_contacts"].append({
                    "name": contact.get('name', 'Unknown'),
                    "phone": contact['phone'],
                    "result": contact_result
                })
        
        return results


# Global instance
notification_service = NotificationService()


async def send_push(user_id: str, title: str, body: str, token: Optional[str] = None) -> bool:
    """Send push notification to user"""
    if not token:
        return False
    
    result = await notification_service.send_push_notification(token, title, body)
    return result["success"]


async def send_sms(to_number: str, body: str) -> bool:
    """Send SMS to phone number"""
    result = await notification_service.send_sms(to_number, body)
    return result["success"]


async def send_emergency_alert(user_data: Dict[str, Any], alert_data: Dict[str, Any]) -> Dict[str, Any]:
    """Send emergency alert via all available channels"""
    return await notification_service.send_emergency_notifications(user_data, alert_data)


async def send_push_to_multiple(tokens: List[str], title: str, body: str) -> Dict[str, Any]:
    """Send push notification to multiple devices"""
    return await notification_service.send_push_to_multiple(tokens, title, body)
