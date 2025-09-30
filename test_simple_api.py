#!/usr/bin/env python3
"""
SafeHorizon API Simple Test Suite
================================

A simple test script that tests all API endpoints without external dependencies.
Uses only built-in Python libraries for maximum compatibility.

Usage:
    python test_simple_api.py

Requirements:
    Python 3.7+ (no additional packages required)
"""

import asyncio
import json
import time
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List


class SimpleAPITester:
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
    
    def log_test(self, endpoint: str, method: str, status: str, response_data: Any = None, error: str = None):
        """Log test result"""
        print(f"\n{'='*60}")
        print(f"{method} {endpoint} - {status}")
        print(f"{'='*60}")
        
        if response_data:
            if isinstance(response_data, dict) or isinstance(response_data, list):
                print("Response:")
                print(json.dumps(response_data, indent=2, default=str))
            else:
                print(f"Response: {response_data}")
        
        if error:
            print(f"Error: {error}")
        
        self.results["endpoints_tested"].append(f"{method} {endpoint}")
        if status == "PASS":
            self.results["passed"] += 1
        elif status == "FAIL":
            self.results["failed"] += 1
            if error:
                self.results["errors"].append(f"{method} {endpoint}: {error}")
        else:
            self.results["skipped"] += 1
        
        print(f"{'='*60}")
    
    def make_request(self, method: str, endpoint: str, token: str = None, data: dict = None) -> tuple:
        """Make HTTP request using urllib"""
        url = f"{self.api_base}{endpoint}" if not endpoint.startswith("http") else endpoint
        
        # Prepare headers
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'SafeHorizon-API-Tester/1.0'
        }
        
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        # Prepare data
        json_data = None
        if data:
            json_data = json.dumps(data).encode('utf-8')
        
        try:
            # Create request
            req = urllib.request.Request(url, data=json_data, headers=headers, method=method)
            
            # Make request
            with urllib.request.urlopen(req, timeout=30) as response:
                response_text = response.read().decode('utf-8')
                try:
                    response_data = json.loads(response_text)
                except json.JSONDecodeError:
                    response_data = response_text
                
                return response.status, response_data
        
        except urllib.error.HTTPError as e:
            try:
                error_text = e.read().decode('utf-8')
                error_data = json.loads(error_text)
            except:
                error_data = {"error": str(e)}
            return e.code, error_data
        
        except Exception as e:
            return 0, {"error": str(e)}
    
    def test_health_endpoint(self):
        """Test the health endpoint"""
        print("\n🏥 TESTING HEALTH ENDPOINT")
        print("="*40)
        
        status_code, response = self.make_request("GET", f"{self.base_url}/health")
        
        if status_code == 200 and response.get("status") == "ok":
            self.log_test("/health", "GET", "PASS", response)
        else:
            self.log_test("/health", "GET", "FAIL", response, f"Expected 200 OK, got {status_code}")
    
    def test_tourist_authentication(self):
        """Test tourist registration and authentication"""
        print("\n👤 TESTING TOURIST AUTHENTICATION")
        print("="*40)
        
        # Test Registration
        tourist_data = {
            "email": f"tourist_{int(time.time())}@test.com",
            "password": "testpass123",
            "name": "Test Tourist",
            "phone": "+1234567890",
            "emergency_contact": "Emergency Contact",
            "emergency_phone": "+9876543210"
        }
        
        status_code, response = self.make_request("POST", "/auth/register", data=tourist_data)
        
        if status_code == 200:
            self.log_test("/auth/register", "POST", "PASS", response)
            self.test_users["tourist"] = tourist_data
        else:
            self.log_test("/auth/register", "POST", "FAIL", response, f"Registration failed: {status_code}")
            return
        
        # Test Login
        login_data = {
            "email": tourist_data["email"],
            "password": tourist_data["password"]
        }
        
        status_code, response = self.make_request("POST", "/auth/login", data=login_data)
        
        if status_code == 200 and "access_token" in response:
            self.log_test("/auth/login", "POST", "PASS", response)
            self.tokens["tourist"] = response["access_token"]
        else:
            self.log_test("/auth/login", "POST", "FAIL", response, f"Login failed: {status_code}")
            return
        
        # Test Get Current User
        status_code, response = self.make_request("GET", "/auth/me", token=self.tokens["tourist"])
        
        if status_code == 200:
            self.log_test("/auth/me", "GET", "PASS", response)
        else:
            self.log_test("/auth/me", "GET", "FAIL", response, f"Get user info failed: {status_code}")
    
    def test_authority_authentication(self):
        """Test authority registration and authentication"""
        print("\n👮 TESTING AUTHORITY AUTHENTICATION")
        print("="*40)
        
        # Test Authority Registration
        authority_data = {
            "email": f"officer_{int(time.time())}@police.com",
            "password": "policepass123",
            "name": "Test Officer",
            "badge_number": f"BADGE{int(time.time())}",
            "department": "Test Police Department",
            "rank": "Officer"
        }
        
        status_code, response = self.make_request("POST", "/auth/register-authority", data=authority_data)
        
        if status_code == 200:
            self.log_test("/auth/register-authority", "POST", "PASS", response)
            self.test_users["authority"] = authority_data
        else:
            self.log_test("/auth/register-authority", "POST", "FAIL", response, f"Authority registration failed: {status_code}")
            return
        
        # Test Authority Login
        login_data = {
            "email": authority_data["email"],
            "password": authority_data["password"]
        }
        
        status_code, response = self.make_request("POST", "/auth/login-authority", data=login_data)
        
        if status_code == 200 and "access_token" in response:
            self.log_test("/auth/login-authority", "POST", "PASS", response)
            self.tokens["authority"] = response["access_token"]
        else:
            self.log_test("/auth/login-authority", "POST", "FAIL", response, f"Authority login failed: {status_code}")
    
    def test_trip_management(self):
        """Test trip management endpoints"""
        if "tourist" not in self.tokens:
            print("\n⚠️  Skipping trip tests - no tourist token")
            return
        
        print("\n🧳 TESTING TRIP MANAGEMENT")
        print("="*40)
        
        # Test Start Trip
        trip_data = {
            "destination": "Tokyo, Japan",
            "itinerary": "Visit temples, shopping districts, and cultural sites"
        }
        
        status_code, response = self.make_request("POST", "/trip/start", token=self.tokens["tourist"], data=trip_data)
        
        if status_code == 200:
            self.log_test("/trip/start", "POST", "PASS", response)
            self.test_data["trip_id"] = response.get("trip_id")
        else:
            self.log_test("/trip/start", "POST", "FAIL", response, f"Start trip failed: {status_code}")
        
        # Test Get Trip History
        status_code, response = self.make_request("GET", "/trip/history", token=self.tokens["tourist"])
        
        if status_code == 200:
            self.log_test("/trip/history", "GET", "PASS", response)
        else:
            self.log_test("/trip/history", "GET", "FAIL", response, f"Get trip history failed: {status_code}")
        
        # Test End Trip
        status_code, response = self.make_request("POST", "/trip/end", token=self.tokens["tourist"])
        
        if status_code == 200:
            self.log_test("/trip/end", "POST", "PASS", response)
        else:
            self.log_test("/trip/end", "POST", "FAIL", response, f"End trip failed: {status_code}")
    
    def test_location_tracking(self):
        """Test location tracking endpoints"""
        if "tourist" not in self.tokens:
            print("\n⚠️  Skipping location tests - no tourist token")
            return
        
        print("\n📍 TESTING LOCATION TRACKING")
        print("="*40)
        
        # Test Location Update
        location_data = {
            "lat": 35.6762,
            "lon": 139.6503,
            "speed": 30.5,
            "altitude": 15.0,
            "accuracy": 5.0,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        status_code, response = self.make_request("POST", "/location/update", token=self.tokens["tourist"], data=location_data)
        
        if status_code == 200:
            self.log_test("/location/update", "POST", "PASS", response)
            self.test_data["location_id"] = response.get("location_id")
        else:
            self.log_test("/location/update", "POST", "FAIL", response, f"Location update failed: {status_code}")
        
        # Test another location to build history
        location_data2 = {
            "lat": 35.6772,
            "lon": 139.6513,
            "speed": 25.0,
            "altitude": 12.0,
            "accuracy": 4.0,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.make_request("POST", "/location/update", token=self.tokens["tourist"], data=location_data2)
        
        # Test Get Location History
        status_code, response = self.make_request("GET", "/location/history?limit=10", token=self.tokens["tourist"])
        
        if status_code == 200:
            self.log_test("/location/history", "GET", "PASS", response)
        else:
            self.log_test("/location/history", "GET", "FAIL", response, f"Get location history failed: {status_code}")
    
    def test_safety_endpoints(self):
        """Test safety and scoring endpoints"""
        if "tourist" not in self.tokens:
            print("\n⚠️  Skipping safety tests - no tourist token")
            return
        
        print("\n🛡️  TESTING SAFETY ENDPOINTS")
        print("="*40)
        
        # Test Get Safety Score
        status_code, response = self.make_request("GET", "/safety/score", token=self.tokens["tourist"])
        
        if status_code == 200:
            self.log_test("/safety/score", "GET", "PASS", response)
        else:
            self.log_test("/safety/score", "GET", "FAIL", response, f"Get safety score failed: {status_code}")
        
        # Test SOS Trigger
        status_code, response = self.make_request("POST", "/sos/trigger", token=self.tokens["tourist"])
        
        if status_code == 200:
            self.log_test("/sos/trigger", "POST", "PASS", response)
            self.test_data["sos_alert_id"] = response.get("alert_id")
        else:
            self.log_test("/sos/trigger", "POST", "FAIL", response, f"SOS trigger failed: {status_code}")
    
    def test_ai_endpoints(self):
        """Test AI service endpoints"""
        if "tourist" not in self.tokens:
            print("\n⚠️  Skipping AI tests - no tourist token")
            return
        
        print("\n🤖 TESTING AI SERVICE ENDPOINTS")
        print("="*40)
        
        # Test Geofence Check
        geofence_data = {"lat": 35.6762, "lon": 139.6503}
        status_code, response = self.make_request("POST", "/ai/geofence/check", token=self.tokens["tourist"], data=geofence_data)
        
        if status_code == 200:
            self.log_test("/ai/geofence/check", "POST", "PASS", response)
        else:
            self.log_test("/ai/geofence/check", "POST", "FAIL", response, f"Geofence check failed: {status_code}")
        
        # Test Point Anomaly Detection
        anomaly_data = {
            "lat": 35.6762,
            "lon": 139.6503,
            "speed": 80.0,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        status_code, response = self.make_request("POST", "/ai/anomaly/point", token=self.tokens["tourist"], data=anomaly_data)
        
        if status_code == 200:
            self.log_test("/ai/anomaly/point", "POST", "PASS", response)
        else:
            self.log_test("/ai/anomaly/point", "POST", "FAIL", response, f"Point anomaly detection failed: {status_code}")
        
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
        
        status_code, response = self.make_request("POST", "/ai/score/compute", token=self.tokens["tourist"], data=score_data)
        
        if status_code == 200:
            self.log_test("/ai/score/compute", "POST", "PASS", response)
        else:
            self.log_test("/ai/score/compute", "POST", "FAIL", response, f"Safety score computation failed: {status_code}")
    
    def test_authority_endpoints(self):
        """Test authority dashboard endpoints"""
        if "authority" not in self.tokens:
            print("\n⚠️  Skipping authority tests - no authority token")
            return
        
        print("\n👮‍♂️ TESTING AUTHORITY DASHBOARD ENDPOINTS")
        print("="*40)
        
        # Test Get Active Tourists
        status_code, response = self.make_request("GET", "/tourists/active", token=self.tokens["authority"])
        
        if status_code == 200:
            self.log_test("/tourists/active", "GET", "PASS", response)
        else:
            self.log_test("/tourists/active", "GET", "FAIL", response, f"Get active tourists failed: {status_code}")
        
        # Test Get Recent Alerts
        status_code, response = self.make_request("GET", "/alerts/recent", token=self.tokens["authority"])
        
        if status_code == 200:
            self.log_test("/alerts/recent", "GET", "PASS", response)
        else:
            self.log_test("/alerts/recent", "GET", "FAIL", response, f"Get recent alerts failed: {status_code}")
        
        # Test Zone Management
        status_code, response = self.make_request("GET", "/zones/manage", token=self.tokens["authority"])
        
        if status_code == 200:
            self.log_test("/zones/manage", "GET", "PASS", response)
        else:
            self.log_test("/zones/manage", "GET", "FAIL", response, f"Get zones failed: {status_code}")
        
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
        
        status_code, response = self.make_request("POST", "/zones/create", token=self.tokens["authority"], data=zone_data)
        
        if status_code == 200:
            self.log_test("/zones/create", "POST", "PASS", response)
            self.test_data["zone_id"] = response.get("id")
        else:
            self.log_test("/zones/create", "POST", "FAIL", response, f"Create zone failed: {status_code}")
    
    def test_notification_endpoints(self):
        """Test notification endpoints"""
        if "authority" not in self.tokens:
            print("\n⚠️  Skipping notification tests - no authority token")
            return
        
        print("\n🔔 TESTING NOTIFICATION ENDPOINTS")
        print("="*40)
        
        # Test Notification History
        status_code, response = self.make_request("GET", "/notify/history", token=self.tokens["authority"])
        
        if status_code == 200:
            self.log_test("/notify/history", "GET", "PASS", response)
        else:
            self.log_test("/notify/history", "GET", "FAIL", response, f"Notification history failed: {status_code}")
        
        # Test Notification Settings
        status_code, response = self.make_request("GET", "/notify/settings", token=self.tokens["authority"])
        
        if status_code == 200:
            self.log_test("/notify/settings", "GET", "PASS", response)
        else:
            self.log_test("/notify/settings", "GET", "FAIL", response, f"Notification settings failed: {status_code}")
    
    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n🧹 CLEANING UP TEST DATA")
        print("="*40)
        
        # Delete test zone if created
        if "zone_id" in self.test_data and "authority" in self.tokens:
            status_code, response = self.make_request("DELETE", f"/zones/{self.test_data['zone_id']}", token=self.tokens["authority"])
            
            if status_code == 200:
                print("✅ Test zone deleted successfully")
            else:
                print(f"⚠️  Could not delete test zone: {response}")
    
    def display_final_results(self):
        """Display final test results summary"""
        print("\n" + "="*80)
        print("🎯 SAFEHORIZON API TEST RESULTS SUMMARY")
        print("="*80)
        
        total_tests = self.results["passed"] + self.results["failed"] + self.results["skipped"]
        
        print(f"\nTest Results:")
        print(f"  ✅ Passed:  {self.results['passed']}")
        print(f"  ❌ Failed:  {self.results['failed']}")
        print(f"  ⏭️  Skipped: {self.results['skipped']}")
        print(f"  📊 Total:   {total_tests}")
        
        if total_tests > 0:
            success_rate = (self.results['passed'] / total_tests) * 100
            print(f"  🎯 Success Rate: {success_rate:.1f}%")
        
        print(f"\nEndpoints Tested ({len(self.results['endpoints_tested'])}):")
        for i, endpoint in enumerate(self.results['endpoints_tested'], 1):
            print(f"  {i:2d}. {endpoint}")
        
        if self.results['errors']:
            print(f"\nErrors ({len(self.results['errors'])}):")
            for i, error in enumerate(self.results['errors'], 1):
                print(f"  {i:2d}. {error}")
        
        print("\n" + "="*80)
        if self.results["failed"] == 0:
            print("🎉 ALL TESTS PASSED! SafeHorizon API is working correctly!")
        else:
            print(f"⚠️  {self.results['failed']} tests failed. Please check the errors above.")
        print("="*80)
    
    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 SAFEHORIZON API COMPREHENSIVE TEST SUITE")
        print("="*80)
        print(f"📅 Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌐 Server URL: {self.base_url}")
        print("="*80)
        
        # Test sequence
        test_functions = [
            ("Health Endpoint", self.test_health_endpoint),
            ("Tourist Authentication", self.test_tourist_authentication),
            ("Authority Authentication", self.test_authority_authentication),
            ("Trip Management", self.test_trip_management),
            ("Location Tracking", self.test_location_tracking),
            ("Safety Endpoints", self.test_safety_endpoints),
            ("AI Endpoints", self.test_ai_endpoints),
            ("Authority Endpoints", self.test_authority_endpoints),
            ("Notification Endpoints", self.test_notification_endpoints),
            ("Cleanup", self.cleanup_test_data),
        ]
        
        for description, test_func in test_functions:
            print(f"\n⏳ Starting: {description}")
            try:
                test_func()
                print(f"✅ Completed: {description}")
            except Exception as e:
                print(f"❌ Error in {description}: {str(e)}")
                self.results["errors"].append(f"{description}: {str(e)}")
            
            # Small delay between test groups
            time.sleep(0.5)
        
        # Display final results
        self.display_final_results()


def main():
    """Main function to run the test suite"""
    import sys
    
    # Parse command line arguments
    base_url = "http://localhost:8000"
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    print("🏁 SafeHorizon API Simple Test Suite")
    print(f"📡 Server: {base_url}")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tester = SimpleAPITester(base_url)
    tester.run_all_tests()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️  Test suite interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite error: {str(e)}")