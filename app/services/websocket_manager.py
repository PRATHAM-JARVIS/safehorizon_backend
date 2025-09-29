import asyncio
import json
import logging
from typing import Dict, List, Set, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect
import aioredis

from ..config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class WebSocketManager:
    def __init__(self):
        # Active connections organized by channel
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.connection_data: Dict[WebSocket, Dict[str, Any]] = {}
        self.redis_client: Optional[aioredis.Redis] = None
        self.redis_pubsub: Optional[aioredis.client.PubSub] = None
        self.redis_listener_task: Optional[asyncio.Task] = None
        
    async def initialize_redis(self):
        """Initialize Redis connection for pub/sub"""
        try:
            self.redis_client = aioredis.from_url(settings.redis_url)
            self.redis_pubsub = self.redis_client.pubsub()
            
            # Subscribe to all alert channels
            await self.redis_pubsub.subscribe("alerts:*")
            
            # Start listening for Redis messages
            self.redis_listener_task = asyncio.create_task(self._redis_listener())
            logger.info("Redis pub/sub initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
    
    async def _redis_listener(self):
        """Listen for Redis pub/sub messages and broadcast to WebSocket clients"""
        if not self.redis_pubsub:
            return
            
        try:
            async for message in self.redis_pubsub.listen():
                if message["type"] == "message":
                    channel = message["channel"].decode()
                    data = json.loads(message["data"].decode())
                    
                    # Extract channel type (e.g., "alerts:authority" -> "authority")
                    channel_type = channel.split(":", 1)[1] if ":" in channel else channel
                    
                    # Broadcast to appropriate WebSocket connections
                    await self._broadcast_to_channel(channel_type, data)
                    
        except Exception as e:
            logger.error(f"Redis listener error: {e}")
    
    async def connect(self, websocket: WebSocket, channel: str, user_data: Dict[str, Any]):
        """Accept a WebSocket connection and add to channel"""
        await websocket.accept()
        
        # Add to channel
        if channel not in self.active_connections:
            self.active_connections[channel] = set()
        self.active_connections[channel].add(websocket)
        
        # Store connection metadata
        self.connection_data[websocket] = {
            "channel": channel,
            "user_id": user_data.get("user_id"),
            "role": user_data.get("role"),
            "connected_at": asyncio.get_event_loop().time()
        }
        
        logger.info(f"WebSocket connected to channel '{channel}' for user {user_data.get('user_id')}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.connection_data:
            channel = self.connection_data[websocket]["channel"]
            user_id = self.connection_data[websocket].get("user_id")
            
            # Remove from channel
            if channel in self.active_connections:
                self.active_connections[channel].discard(websocket)
                
                # Clean up empty channels
                if not self.active_connections[channel]:
                    del self.active_connections[channel]
            
            # Remove connection data
            del self.connection_data[websocket]
            
            logger.info(f"WebSocket disconnected from channel '{channel}' for user {user_id}")
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send message to specific WebSocket connection"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast_to_channel(self, channel: str, message: Dict[str, Any]):
        """Broadcast message to all connections in a channel"""
        await self._broadcast_to_channel(channel, message)
    
    async def _broadcast_to_channel(self, channel: str, message: Dict[str, Any]):
        """Internal method to broadcast to channel"""
        if channel not in self.active_connections:
            return
        
        # Create a copy of connections to avoid modification during iteration
        connections = list(self.active_connections[channel])
        
        if not connections:
            return
        
        # Send message to all connections
        tasks = []
        for connection in connections:
            tasks.append(self._safe_send(connection, message))
        
        # Execute all sends concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Clean up failed connections
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.disconnect(connections[i])
    
    async def _safe_send(self, websocket: WebSocket, message: Dict[str, Any]):
        """Safely send message to WebSocket with error handling"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send message to WebSocket: {e}")
            raise e
    
    async def publish_alert(self, channel: str, alert_data: Dict[str, Any]):
        """Publish alert to Redis for broadcasting"""
        if not self.redis_client:
            # Fallback to direct WebSocket broadcast if Redis unavailable
            await self.broadcast_to_channel(channel, alert_data)
            return
        
        try:
            redis_channel = f"alerts:{channel}"
            await self.redis_client.publish(redis_channel, json.dumps(alert_data))
        except Exception as e:
            logger.error(f"Failed to publish to Redis: {e}")
            # Fallback to direct broadcast
            await self.broadcast_to_channel(channel, alert_data)
    
    def get_channel_stats(self) -> Dict[str, Any]:
        """Get statistics about active connections"""
        stats = {
            "total_connections": sum(len(connections) for connections in self.active_connections.values()),
            "channels": {}
        }
        
        for channel, connections in self.active_connections.items():
            user_roles = {}
            for conn in connections:
                if conn in self.connection_data:
                    role = self.connection_data[conn].get("role", "unknown")
                    user_roles[role] = user_roles.get(role, 0) + 1
            
            stats["channels"][channel] = {
                "connection_count": len(connections),
                "user_roles": user_roles
            }
        
        return stats
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.redis_listener_task:
            self.redis_listener_task.cancel()
            try:
                await self.redis_listener_task
            except asyncio.CancelledError:
                pass
        
        if self.redis_pubsub:
            await self.redis_pubsub.unsubscribe()
            await self.redis_pubsub.close()
        
        if self.redis_client:
            await self.redis_client.close()


# Global WebSocket manager instance
websocket_manager = WebSocketManager()


async def initialize_websocket_manager():
    """Initialize the WebSocket manager with Redis"""
    await websocket_manager.initialize_redis()


async def cleanup_websocket_manager():
    """Cleanup WebSocket manager resources"""
    await websocket_manager.cleanup()