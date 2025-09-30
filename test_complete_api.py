#!/usr/bin/env python3
"""
SafeHorizon API Comprehensive Test Suite
========================================

This script tests all API endpoints of the SafeHorizon Tourist Safety Platform.
It systematically tests authentication, user roles, and all endpoint functionality.

Features:
- Complete endpoint coverage
- Authentication flow testing
- User role validation (tourist, authority, admin)
- Real-time response formatting
- Error handling and validation
- WebSocket testing for real-time alerts

Usage:
    python test_complete_api.py

Requirements:
    pip install httpx websockets asyncio rich
"""

import asyncio
import httpx
import json
import time
import websockets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.json import JSON
from rich import print as rprint

# Initialize Rich console for beautiful output
console = Console()

class SafeHorizonAPITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api"
        self.tokens = {}  # Store tokens for different user types
        self.test_users = {}  # Store created test users
        self.test_data = {}  # Store test data (trips, locations, etc.)
        self.results = {
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "endpoints_tested": [],
            "errors": []
        }
    
    async def log_test(self, endpoint: str, method: str, status: str, response_data: Any = None, error: str = None):
        """Log test result with beautiful formatting"""
        status_color = "green" if status == "PASS" else "red" if status == "FAIL" else "yellow"
        
        console.print(f"\n[bold]{method}[/bold] [blue]{endpoint}[/blue] - [bold {status_color}]{status}[/bold {status_color}]")
        
        if response_data:
            # Show formatted JSON response
            if isinstance(response_data, dict):
                console.print("[dim]Response:[/dim]")
                console.print(JSON.from_data(response_data))
            else:
                console.print(f"[dim]Response:[/dim] {response_data}")
        
        if error:
            console.print(f"[red]Error:[/red] {error}")
        
        self.results["endpoints_tested"].append(f"{method} {endpoint}")
        if status == "PASS":
            self.results["passed"] += 1
        elif status == "FAIL":
            self.results["failed"] += 1
            if error:
                self.results["errors"].append(f"{method} {endpoint}: {error}")
        else:
            self.results["skipped"] += 1
    
    async def make_request(self, method: str, endpoint: str, token: str = None, **kwargs) -> tuple:
        """Make HTTP request with error handling"""
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        if "headers" in kwargs:
            headers.update(kwargs["headers"])
            del kwargs["headers"]
        
        url = f"{self.api_base}{endpoint}" if not endpoint.startswith("http") else endpoint
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.request(method, url, headers=headers, **kwargs)
                
                try:
                    response_data = response.json()
                except:
                    response_data = response.text
                
                return response.status_code, response_data
        except Exception as e:
            return 0, {"error": str(e)}
    
    async def test_health_endpoint(self):
        """Test the health endpoint"""
        console.print(Panel("[bold green]Testing Health Endpoint[/bold green]", expand=False))
        
        status_code, response = await self.make_request("GET", f"{self.base_url}/health")
        
        if status_code == 200 and response.get("status") == "ok":
            await self.log_test("/health", "GET", "PASS", response)
        else:
            await self.log_test("/health", "GET", "FAIL", response, f"Expected 200 OK, got {status_code}")
    
    async def test_tourist_authentication(self):
        """Test tourist registration and authentication"""
        console.print(Panel("[bold blue]Testing Tourist Authentication[/bold blue]", expand=False))
        
        # Test Registration
        tourist_data = {
            "email": f"tourist_{int(time.time())}@test.com",
            "password": "testpass123",
            "name": "Test Tourist",
            "phone": "+1234567890",
            "emergency_contact": "Emergency Contact",
            "emergency_phone": "+9876543210"
        }
        
        status_code, response = await self.make_request("POST", "/auth/register", json=tourist_data)
        
        if status_code == 200:
            await self.log_test("/auth/register", "POST", "PASS", response)
            self.test_users["tourist"] = tourist_data
        else:
            await self.log_test("/auth/register", "POST", "FAIL", response, f"Registration failed: {status_code}")
            return
        
        # Test Login
        login_data = {
            "email": tourist_data["email"],
            "password": tourist_data["password"]
        }
        
        status_code, response = await self.make_request("POST", "/auth/login", json=login_data)
        
        if status_code == 200 and "access_token" in response:
            await self.log_test("/auth/login", "POST", "PASS", response)
            self.tokens["tourist"] = response["access_token"]
        else:
            await self.log_test("/auth/login", "POST", "FAIL", response, f"Login failed: {status_code}")
            return
        
        # Test Get Current User
        status_code, response = await self.make_request("GET", "/auth/me", token=self.tokens["tourist"])
        
        if status_code == 200:
            await self.log_test("/auth/me", "GET", "PASS", response)
        else:
            await self.log_test("/auth/me", "GET", "FAIL", response, f"Get user info failed: {status_code}")
    
    async def test_authority_authentication(self):
        """Test authority registration and authentication"""
        console.print(Panel("[bold purple]Testing Authority Authentication[/bold purple]", expand=False))
        
        # Test Authority Registration
        authority_data = {
            "email": f"officer_{int(time.time())}@police.com",
            "password": "policepass123",
            "name": "Test Officer",
            "badge_number": f"BADGE{int(time.time())}",
            "department": "Test Police Department",
            "rank": "Officer"
        }
        
        status_code, response = await self.make_request("POST", "/auth/register-authority", json=authority_data)
        
        if status_code == 200:
            await self.log_test("/auth/register-authority", "POST", "PASS", response)
            self.test_users["authority"] = authority_data
        else:
            await self.log_test("/auth/register-authority", "POST", "FAIL", response, f"Authority registration failed: {status_code}")
            return
        
        # Test Authority Login
        login_data = {
            "email": authority_data["email"],
            "password": authority_data["password"]
        }
        
        status_code, response = await self.make_request("POST", "/auth/login-authority", json=login_data)
        
        if status_code == 200 and "access_token" in response:
            await self.log_test("/auth/login-authority", "POST", "PASS", response)
            self.tokens["authority"] = response["access_token"]
        else:
            await self.log_test("/auth/login-authority", "POST", "FAIL", response, f"Authority login failed: {status_code}")
    
    async def test_admin_authentication(self):
        """Test admin authentication (assuming admin user exists)"""
        console.print(Panel("[bold red]Testing Admin Authentication[/bold red]", expand=False))
        
        # Try to create an admin user (might fail if already exists)
        admin_data = {
            "email": "admin@safehorizon.com",
            "password": "adminpass123",
            "name": "System Admin",
            "badge_number": "ADMIN001",
            "department": "System Administration",
            "rank": "Administrator"
        }
        
        # Try authority registration first (admin is created as authority with admin rank)
        status_code, response = await self.make_request("POST", "/auth/register-authority", json=admin_data)
        
        if status_code == 200:
            await self.log_test("/auth/register-authority (admin)", "POST", "PASS", response)
        else:
            # Admin might already exist, that's OK
            await self.log_test("/auth/register-authority (admin)", "POST", "SKIP", response, "Admin might already exist")
        
        # Test Admin Login
        login_data = {
            "email": admin_data["email"],
            "password": admin_data["password"]
        }
        
        status_code, response = await self.make_request("POST", "/auth/login-authority", json=login_data)
        
        if status_code == 200 and "access_token" in response:
            await self.log_test("/auth/login-authority (admin)", "POST", "PASS", response)
            self.tokens["admin"] = response["access_token"]
            self.test_users["admin"] = admin_data
        else:
            await self.log_test("/auth/login-authority (admin)", "POST", "FAIL", response, f"Admin login failed: {status_code}")
    
    async def test_trip_management(self):
        """Test trip management endpoints"""
        if "tourist" not in self.tokens:
            console.print("[yellow]Skipping trip tests - no tourist token[/yellow]")
            return
        
        console.print(Panel("[bold cyan]Testing Trip Management[/bold cyan]", expand=False))
        
        # Test Start Trip
        trip_data = {
            "destination": "Tokyo, Japan",
            "itinerary": "Visit temples, shopping districts, and cultural sites"
        }
        
        status_code, response = await self.make_request("POST", "/trip/start", token=self.tokens["tourist"], json=trip_data)
        
        if status_code == 200:
            await self.log_test("/trip/start", "POST", "PASS", response)
            self.test_data["trip_id"] = response.get("trip_id")
        else:
            await self.log_test("/trip/start", "POST", "FAIL", response, f"Start trip failed: {status_code}")
        
        # Test Get Trip History
        status_code, response = await self.make_request("GET", "/trip/history", token=self.tokens["tourist"])
        
        if status_code == 200:
            await self.log_test("/trip/history", "GET", "PASS", response)
        else:
            await self.log_test("/trip/history", "GET", "FAIL", response, f"Get trip history failed: {status_code}")
        
        # Test End Trip
        status_code, response = await self.make_request("POST", "/trip/end", token=self.tokens["tourist"])
        
        if status_code == 200:
            await self.log_test("/trip/end", "POST", "PASS", response)
        else:
            await self.log_test("/trip/end", "POST", "FAIL", response, f"End trip failed: {status_code}")
    
    async def test_location_tracking(self):
        """Test location tracking endpoints"""
        if "tourist" not in self.tokens:
            console.print("[yellow]Skipping location tests - no tourist token[/yellow]")
            return
        
        console.print(Panel("[bold green]Testing Location Tracking[/bold green]", expand=False))
        
        # Test Location Update
        location_data = {
            "lat": 35.6762,
            "lon": 139.6503,
            "speed": 30.5,
            "altitude": 15.0,
            "accuracy": 5.0,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        status_code, response = await self.make_request("POST", "/location/update", token=self.tokens["tourist"], json=location_data)
        
        if status_code == 200:
            await self.log_test("/location/update", "POST", "PASS", response)
            self.test_data["location_id"] = response.get("location_id")
        else:
            await self.log_test("/location/update", "POST", "FAIL", response, f"Location update failed: {status_code}")
        
        # Test another location to build history
        location_data2 = {
            "lat": 35.6772,
            "lon": 139.6513,
            "speed": 25.0,
            "altitude": 12.0,
            "accuracy": 4.0,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.make_request("POST", "/location/update", token=self.tokens["tourist"], json=location_data2)
        
        # Test Get Location History
        status_code, response = await self.make_request("GET", "/location/history?limit=10", token=self.tokens["tourist"])
        
        if status_code == 200:
            await self.log_test("/location/history", "GET", "PASS", response)
        else:
            await self.log_test("/location/history", "GET", "FAIL", response, f"Get location history failed: {status_code}")
    
    async def test_safety_endpoints(self):
        """Test safety and scoring endpoints"""
        if "tourist" not in self.tokens:
            console.print("[yellow]Skipping safety tests - no tourist token[/yellow]")
            return
        
        console.print(Panel("[bold orange3]Testing Safety Endpoints[/bold orange3]", expand=False))
        
        # Test Get Safety Score
        status_code, response = await self.make_request("GET", "/safety/score", token=self.tokens["tourist"])
        
        if status_code == 200:
            await self.log_test("/safety/score", "GET", "PASS", response)
        else:
            await self.log_test("/safety/score", "GET", "FAIL", response, f"Get safety score failed: {status_code}")
        
        # Test SOS Trigger
        status_code, response = await self.make_request("POST", "/sos/trigger", token=self.tokens["tourist"])
        
        if status_code == 200:
            await self.log_test("/sos/trigger", "POST", "PASS", response)
            self.test_data["sos_alert_id"] = response.get("alert_id")
        else:
            await self.log_test("/sos/trigger", "POST", "FAIL", response, f"SOS trigger failed: {status_code}")
    
    async def test_ai_endpoints(self):
        """Test AI service endpoints"""
        if "tourist" not in self.tokens:
            console.print("[yellow]Skipping AI tests - no tourist token[/yellow]")
            return
        
        console.print(Panel("[bold magenta]Testing AI Service Endpoints[/bold magenta]", expand=False))
        
        # Test Geofence Check
        geofence_data = {"lat": 35.6762, "lon": 139.6503}
        status_code, response = await self.make_request("POST", "/ai/geofence/check", token=self.tokens["tourist"], json=geofence_data)
        
        if status_code == 200:
            await self.log_test("/ai/geofence/check", "POST", "PASS", response)
        else:
            await self.log_test("/ai/geofence/check", "POST", "FAIL", response, f"Geofence check failed: {status_code}")
        
        # Test Nearby Zones
        status_code, response = await self.make_request("POST", "/ai/geofence/nearby?radius=1000", token=self.tokens["tourist"], json=geofence_data)
        
        if status_code == 200:
            await self.log_test("/ai/geofence/nearby", "POST", "PASS", response)
        else:
            await self.log_test("/ai/geofence/nearby", "POST", "FAIL", response, f"Nearby zones failed: {status_code}")
        
        # Test Point Anomaly Detection
        anomaly_data = {
            "lat": 35.6762,
            "lon": 139.6503,
            "speed": 80.0,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        status_code, response = await self.make_request("POST", "/ai/anomaly/point", token=self.tokens["tourist"], json=anomaly_data)
        
        if status_code == 200:
            await self.log_test("/ai/anomaly/point", "POST", "PASS", response)
        else:
            await self.log_test("/ai/anomaly/point", "POST", "FAIL", response, f"Point anomaly detection failed: {status_code}")
        
        # Test Sequence Anomaly Detection
        sequence_data = {
            "points": [
                {"lat": 35.6762, "lon": 139.6503, "speed": 30.0, "timestamp": datetime.utcnow().isoformat()},
                {"lat": 35.6772, "lon": 139.6513, "speed": 80.0, "timestamp": datetime.utcnow().isoformat()}
            ]
        }
        
        status_code, response = await self.make_request("POST", "/ai/anomaly/sequence", token=self.tokens["tourist"], json=sequence_data)
        
        if status_code == 200:
            await self.log_test("/ai/anomaly/sequence", "POST", "PASS", response)
        else:
            await self.log_test("/ai/anomaly/sequence", "POST", "FAIL", response, f"Sequence anomaly detection failed: {status_code}")
        
        # Test Safety Score Computation
        score_data = {
            "lat": 35.6762,
            "lon": 139.6503,
            "location_history": [
                {"latitude": 35.6762, "longitude": 139.6503, "speed": 30, "timestamp": datetime.utcnow().isoformat()}
            ],
            "current_location_data": {
                "latitude": 35.6762,
                "longitude": 139.6503,
                "speed": 40,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        status_code, response = await self.make_request("POST", "/ai/score/compute", token=self.tokens["tourist"], json=score_data)
        
        if status_code == 200:
            await self.log_test("/ai/score/compute", "POST", "PASS", response)
        else:
            await self.log_test("/ai/score/compute", "POST", "FAIL", response, f"Safety score computation failed: {status_code}")
        
        # Test AI Models Status
        status_code, response = await self.make_request("GET", "/ai/models/status", token=self.tokens["tourist"])
        
        if status_code == 200:
            await self.log_test("/ai/models/status", "GET", "PASS", response)
        else:
            await self.log_test("/ai/models/status", "GET", "FAIL", response, f"AI models status failed: {status_code}")
    
    async def test_authority_endpoints(self):
        """Test authority dashboard endpoints"""
        if "authority" not in self.tokens:
            console.print("[yellow]Skipping authority tests - no authority token[/yellow]")
            return
        
        console.print(Panel("[bold blue]Testing Authority Dashboard Endpoints[/bold blue]", expand=False))
        
        # Test Get Active Tourists
        status_code, response = await self.make_request("GET", "/tourists/active", token=self.tokens["authority"])
        
        if status_code == 200:
            await self.log_test("/tourists/active", "GET", "PASS", response)
        else:
            await self.log_test("/tourists/active", "GET", "FAIL", response, f"Get active tourists failed: {status_code}")
        
        # Test Get Recent Alerts
        status_code, response = await self.make_request("GET", "/alerts/recent", token=self.tokens["authority"])
        
        if status_code == 200:
            await self.log_test("/alerts/recent", "GET", "PASS", response)
        else:
            await self.log_test("/alerts/recent", "GET", "FAIL", response, f"Get recent alerts failed: {status_code}")
        
        # Test Track Specific Tourist (if we have tourist data)
        if "tourist" in self.test_users:
            # First get tourist ID from login response or create one
            login_response = await self.make_request("POST", "/auth/login", json={
                "email": self.test_users["tourist"]["email"],
                "password": self.test_users["tourist"]["password"]
            })
            
            if login_response[0] == 200:
                tourist_id = login_response[1].get("user_id")
                if tourist_id:
                    status_code, response = await self.make_request("GET", f"/tourist/{tourist_id}/track", token=self.tokens["authority"])
                    
                    if status_code == 200:
                        await self.log_test(f"/tourist/{tourist_id}/track", "GET", "PASS", response)
                    else:
                        await self.log_test(f"/tourist/{tourist_id}/track", "GET", "FAIL", response, f"Track tourist failed: {status_code}")
        
        # Test Zone Management
        status_code, response = await self.make_request("GET", "/zones/manage", token=self.tokens["authority"])
        
        if status_code == 200:
            await self.log_test("/zones/manage", "GET", "PASS", response)
        else:
            await self.log_test("/zones/manage", "GET", "FAIL", response, f"Get zones failed: {status_code}")
        
        # Test Create Zone
        zone_data = {
            "name": "Test Restricted Zone",
            "description": "Test zone for API testing",
            "zone_type": "restricted",
            "coordinates": [
                [139.6503, 35.6762],
                [139.6603, 35.6762],
                [139.6603, 35.6862],
                [139.6503, 35.6862]
            ]
        }
        
        status_code, response = await self.make_request("POST", "/zones/create", token=self.tokens["authority"], json=zone_data)
        
        if status_code == 200:
            await self.log_test("/zones/create", "POST", "PASS", response)
            self.test_data["zone_id"] = response.get("id")
        else:
            await self.log_test("/zones/create", "POST", "FAIL", response, f"Create zone failed: {status_code}")
        
        # Test Acknowledge Incident (if we have an alert)
        if "sos_alert_id" in self.test_data:
            acknowledge_data = {
                "alert_id": self.test_data["sos_alert_id"],
                "notes": "Responding to location"
            }
            
            status_code, response = await self.make_request("POST", "/incident/acknowledge", token=self.tokens["authority"], json=acknowledge_data)
            
            if status_code == 200:
                await self.log_test("/incident/acknowledge", "POST", "PASS", response)
            else:
                await self.log_test("/incident/acknowledge", "POST", "FAIL", response, f"Acknowledge incident failed: {status_code}")
    
    async def test_admin_endpoints(self):
        """Test admin endpoints"""
        if "admin" not in self.tokens:
            console.print("[yellow]Skipping admin tests - no admin token[/yellow]")
            return
        
        console.print(Panel("[bold red]Testing Admin Endpoints[/bold red]", expand=False))
        
        # Test System Status
        status_code, response = await self.make_request("GET", "/system/status", token=self.tokens["admin"])
        
        if status_code == 200:
            await self.log_test("/system/status", "GET", "PASS", response)
        else:
            await self.log_test("/system/status", "GET", "FAIL", response, f"System status failed: {status_code}")
        
        # Test List Users
        status_code, response = await self.make_request("GET", "/users/list", token=self.tokens["admin"])
        
        if status_code == 200:
            await self.log_test("/users/list", "GET", "PASS", response)
        else:
            await self.log_test("/users/list", "GET", "FAIL", response, f"List users failed: {status_code}")
        
        # Test Analytics Dashboard
        status_code, response = await self.make_request("GET", "/analytics/dashboard", token=self.tokens["admin"])
        
        if status_code == 200:
            await self.log_test("/analytics/dashboard", "GET", "PASS", response)
        else:
            await self.log_test("/analytics/dashboard", "GET", "FAIL", response, f"Analytics dashboard failed: {status_code}")
        
        # Test Model Retraining (background task)
        retrain_data = {
            "model_types": ["anomaly"],
            "days_back": 7
        }
        
        status_code, response = await self.make_request("POST", "/system/retrain-model", token=self.tokens["admin"], json=retrain_data)
        
        if status_code == 200:
            await self.log_test("/system/retrain-model", "POST", "PASS", response)
        else:
            await self.log_test("/system/retrain-model", "POST", "FAIL", response, f"Model retraining failed: {status_code}")
    
    async def test_notification_endpoints(self):
        """Test notification endpoints"""
        if "authority" not in self.tokens:
            console.print("[yellow]Skipping notification tests - no authority token[/yellow]")
            return
        
        console.print(Panel("[bold yellow]Testing Notification Endpoints[/bold yellow]", expand=False))
        
        # Test SMS Notification
        sms_data = {
            "to_number": "+1234567890",
            "body": "Test SMS from SafeHorizon API"
        }
        
        status_code, response = await self.make_request("POST", "/notify/sms", token=self.tokens["authority"], json=sms_data)
        
        if status_code == 200:
            await self.log_test("/notify/sms", "POST", "PASS", response)
        else:
            await self.log_test("/notify/sms", "POST", "FAIL", response, f"SMS notification failed: {status_code}")
        
        # Test Notification History
        status_code, response = await self.make_request("GET", "/notify/history", token=self.tokens["authority"])
        
        if status_code == 200:
            await self.log_test("/notify/history", "GET", "PASS", response)
        else:
            await self.log_test("/notify/history", "GET", "FAIL", response, f"Notification history failed: {status_code}")
        
        # Test Notification Settings
        status_code, response = await self.make_request("GET", "/notify/settings", token=self.tokens["authority"])
        
        if status_code == 200:
            await self.log_test("/notify/settings", "GET", "PASS", response)
        else:
            await self.log_test("/notify/settings", "GET", "FAIL", response, f"Notification settings failed: {status_code}")
    
    async def test_role_access_control(self):
        """Test role-based access control"""
        console.print(Panel("[bold white]Testing Role-Based Access Control[/bold white]", expand=False))
        
        # Test tourist trying to access authority endpoint
        if "tourist" in self.tokens:
            status_code, response = await self.make_request("GET", "/tourists/active", token=self.tokens["tourist"])
            
            if status_code == 403:
                await self.log_test("/tourists/active (tourist token)", "GET", "PASS", {"message": "Access denied as expected"})
            else:
                await self.log_test("/tourists/active (tourist token)", "GET", "FAIL", response, "Tourist should not access authority endpoints")
        
        # Test authority trying to access admin endpoint
        if "authority" in self.tokens:
            status_code, response = await self.make_request("GET", "/system/status", token=self.tokens["authority"])
            
            if status_code == 403:
                await self.log_test("/system/status (authority token)", "GET", "PASS", {"message": "Access denied as expected"})
            else:
                await self.log_test("/system/status (authority token)", "GET", "FAIL", response, "Authority should not access admin endpoints")
    
    async def test_websocket_connection(self):
        """Test WebSocket connection for real-time alerts"""
        if "authority" not in self.tokens:
            console.print("[yellow]Skipping WebSocket tests - no authority token[/yellow]")
            return
        
        console.print(Panel("[bold cyan]Testing WebSocket Connection[/bold cyan]", expand=False))
        
        try:
            # Test WebSocket connection
            ws_url = f"ws://localhost:8000/api/alerts/subscribe?token={self.tokens['authority']}"
            
            async with websockets.connect(ws_url, extra_headers={
                "Authorization": f"Bearer {self.tokens['authority']}"
            }) as websocket:
                
                # Send ping
                await websocket.send("ping")
                
                # Wait for pong
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                
                if response == "pong":
                    await self.log_test("/alerts/subscribe (WebSocket)", "WS", "PASS", {"response": "pong"})
                else:
                    await self.log_test("/alerts/subscribe (WebSocket)", "WS", "FAIL", {"response": response}, "Expected pong response")
                
        except Exception as e:
            await self.log_test("/alerts/subscribe (WebSocket)", "WS", "FAIL", {}, str(e))
    
    async def cleanup_test_data(self):
        """Clean up test data"""
        console.print(Panel("[bold orange]Cleaning Up Test Data[/bold orange]", expand=False))
        
        # Delete test zone if created
        if "zone_id" in self.test_data and "authority" in self.tokens:
            status_code, response = await self.make_request("DELETE", f"/zones/{self.test_data['zone_id']}", token=self.tokens["authority"])
            
            if status_code == 200:
                console.print("[green]✓ Test zone deleted[/green]")
            else:
                console.print(f"[yellow]⚠ Could not delete test zone: {response}[/yellow]")
    
    def display_final_results(self):
        """Display final test results summary"""
        console.print("\n" + "="*60)
        console.print(Panel("[bold green]SafeHorizon API Test Results Summary[/bold green]", expand=False))
        
        # Results table
        table = Table(title="Test Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="magenta")
        table.add_column("Percentage", style="green")
        
        total_tests = self.results["passed"] + self.results["failed"] + self.results["skipped"]
        
        if total_tests > 0:
            table.add_row("Passed", str(self.results["passed"]), f"{(self.results['passed']/total_tests)*100:.1f}%")
            table.add_row("Failed", str(self.results["failed"]), f"{(self.results['failed']/total_tests)*100:.1f}%")
            table.add_row("Skipped", str(self.results["skipped"]), f"{(self.results['skipped']/total_tests)*100:.1f}%")
            table.add_row("Total", str(total_tests), "100.0%")
        
        console.print(table)
        
        # Endpoints tested
        console.print(f"\n[bold]Endpoints Tested ({len(self.results['endpoints_tested'])}):[/bold]")
        for endpoint in self.results['endpoints_tested']:
            console.print(f"  • {endpoint}")
        
        # Errors
        if self.results['errors']:
            console.print(f"\n[bold red]Errors ({len(self.results['errors'])}):[/bold red]")
            for error in self.results['errors']:
                console.print(f"  • [red]{error}[/red]")
        
        # Overall status
        if self.results["failed"] == 0:
            console.print(f"\n[bold green]🎉 ALL TESTS PASSED! ({self.results['passed']} passed)[/bold green]")
        else:
            console.print(f"\n[bold yellow]⚠ {self.results['failed']} tests failed out of {total_tests}[/bold yellow]")
    
    async def run_all_tests(self):
        """Run all API tests"""
        console.print(Panel("[bold white]SafeHorizon API Comprehensive Test Suite[/bold white]", expand=False))
        console.print("[dim]Testing all API endpoints with authentication and role validation[/dim]\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            # Test sequence
            test_functions = [
                ("Testing Health Endpoint", self.test_health_endpoint),
                ("Testing Tourist Authentication", self.test_tourist_authentication),
                ("Testing Authority Authentication", self.test_authority_authentication),
                ("Testing Admin Authentication", self.test_admin_authentication),
                ("Testing Trip Management", self.test_trip_management),
                ("Testing Location Tracking", self.test_location_tracking),
                ("Testing Safety Endpoints", self.test_safety_endpoints),
                ("Testing AI Endpoints", self.test_ai_endpoints),
                ("Testing Authority Endpoints", self.test_authority_endpoints),
                ("Testing Admin Endpoints", self.test_admin_endpoints),
                ("Testing Notification Endpoints", self.test_notification_endpoints),
                ("Testing Role Access Control", self.test_role_access_control),
                ("Testing WebSocket Connection", self.test_websocket_connection),
                ("Cleaning Up Test Data", self.cleanup_test_data),
            ]
            
            for description, test_func in test_functions:
                task = progress.add_task(description)
                try:
                    await test_func()
                    progress.update(task, completed=100)
                except Exception as e:
                    console.print(f"[red]Error in {description}: {str(e)}[/red]")
                    progress.update(task, completed=100)
                
                # Small delay between test groups
                await asyncio.sleep(0.5)
        
        # Display final results
        self.display_final_results()


async def main():
    """Main function to run the test suite"""
    import argparse
    
    parser = argparse.ArgumentParser(description="SafeHorizon API Comprehensive Test Suite")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL of the API server")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    console.print(Panel(
        "[bold green]SafeHorizon API Test Suite[/bold green]\n"
        f"[dim]Server: {args.url}[/dim]\n"
        f"[dim]Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]",
        expand=False
    ))
    
    tester = SafeHorizonAPITester(args.url)
    await tester.run_all_tests()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Test suite interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Test suite error: {str(e)}[/red]")