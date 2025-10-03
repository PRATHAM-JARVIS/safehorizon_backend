"""
Comprehensive API Testing Suite for SafeHorizon Backend
Tests all API endpoints with various scenarios
"""

import requests
import json
from datetime import datetime
from typing import Dict, Optional
import time

# Configuration
BASE_URL = "http://localhost:8000/api"
HEALTH_URL = "http://localhost:8000/health"

# Test data storage
test_data = {
    "tourist_token": None,
    "authority_token": None,
    "tourist_id": None,
    "authority_id": None,
    "trip_id": None,
    "alert_id": None,
    "zone_id": None,
    "efir_id": None,
    "broadcast_id": None,
    "device_token": None,
}

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^80}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.ENDC}\n")

def print_test(test_name: str, success: bool, details: str = ""):
    status = f"{Colors.GREEN}✓ PASS{Colors.ENDC}" if success else f"{Colors.RED}✗ FAIL{Colors.ENDC}"
    print(f"{status} | {test_name}")
    if details:
        print(f"       {Colors.YELLOW}{details}{Colors.ENDC}")

def make_request(method: str, endpoint: str, token: Optional[str] = None, 
                 data: Optional[Dict] = None, params: Optional[Dict] = None) -> tuple:
    """Make HTTP request and return (success, response, status_code)"""
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=params, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=10)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=10)
        else:
            return False, None, 0
        
        return response.status_code < 400, response, response.status_code
    except Exception as e:
        print(f"       {Colors.RED}Request failed: {str(e)}{Colors.ENDC}")
        return False, None, 0


# ============================================================================
# HEALTH CHECK
# ============================================================================
def test_health_check():
    print_header("HEALTH CHECK")
    
    try:
        response = requests.get(HEALTH_URL, timeout=5)
        success = response.status_code == 200 and response.json().get("status") == "ok"
        print_test("Health endpoint", success, f"Status: {response.status_code}")
        return success
    except Exception as e:
        print_test("Health endpoint", False, str(e))
        return False


# ============================================================================
# AUTHENTICATION TESTS
# ============================================================================
def test_authentication():
    print_header("AUTHENTICATION TESTS")
    
    # Test 1: Register Tourist
    tourist_data = {
        "email": f"tourist_test_{int(time.time())}@example.com",
        "password": "TestPass123!",
        "name": "Test Tourist",
        "phone_number": "+1234567890",
        "nationality": "India"
    }
    
    success, response, status = make_request("POST", "/auth/register", data=tourist_data)
    if success:
        test_data["tourist_id"] = response.json().get("user_id")
    print_test("Tourist Registration", success, f"Status: {status}")
    
    # Test 2: Login Tourist
    login_data = {
        "email": tourist_data["email"],
        "password": tourist_data["password"]
    }
    
    success, response, status = make_request("POST", "/auth/login", data=login_data)
    if success:
        test_data["tourist_token"] = response.json().get("access_token")
    print_test("Tourist Login", success, f"Status: {status}")
    
    # Test 3: Register Authority
    authority_data = {
        "email": f"authority_test_{int(time.time())}@police.gov",
        "password": "AuthPass123!",
        "name": "Test Authority",
        "badge_number": f"BADGE{int(time.time())}",
        "department": "Test Police Department",
        "rank": "Inspector"
    }
    
    success, response, status = make_request("POST", "/auth/register-authority", data=authority_data)
    if success:
        test_data["authority_id"] = response.json().get("user_id")
    print_test("Authority Registration", success, f"Status: {status}")
    
    # Test 4: Login Authority
    auth_login_data = {
        "email": authority_data["email"],
        "password": authority_data["password"]
    }
    
    success, response, status = make_request("POST", "/auth/login-authority", data=auth_login_data)
    if success:
        test_data["authority_token"] = response.json().get("access_token")
    print_test("Authority Login", success, f"Status: {status}")
    
    # Test 5: Get Current User
    success, response, status = make_request("GET", "/auth/me", token=test_data["tourist_token"])
    print_test("Get Current User (Tourist)", success, f"Status: {status}")


# ============================================================================
# TOURIST TRIP MANAGEMENT
# ============================================================================
def test_trip_management():
    print_header("TRIP MANAGEMENT TESTS")
    
    if not test_data["tourist_token"]:
        print_test("Skip Trip Tests", False, "No tourist token available")
        return
    
    # Test 1: Start Trip
    trip_data = {
        "destination": "Mumbai, India",
        "itinerary": "Visit Gateway of India, Marine Drive"
    }
    
    success, response, status = make_request("POST", "/trip/start", 
                                             token=test_data["tourist_token"], data=trip_data)
    if success:
        test_data["trip_id"] = response.json().get("trip_id")
    print_test("Start Trip", success, f"Status: {status}")
    
    # Test 2: Get Trip History
    success, response, status = make_request("GET", "/trip/history", token=test_data["tourist_token"])
    print_test("Get Trip History", success, f"Status: {status}")


# ============================================================================
# LOCATION TESTS
# ============================================================================
def test_location_services():
    print_header("LOCATION SERVICE TESTS")
    
    if not test_data["tourist_token"]:
        print_test("Skip Location Tests", False, "No tourist token available")
        return
    
    # Test 1: Update Location
    location_data = {
        "latitude": 19.0760,
        "longitude": 72.8777,
        "accuracy": 10.5,
        "altitude": 14.0,
        "speed": 5.2,
        "heading": 180.0
    }
    
    success, response, status = make_request("POST", "/location/update", 
                                             token=test_data["tourist_token"], data=location_data)
    print_test("Update Location", success, f"Status: {status}")
    
    # Test 2: Get Location History
    success, response, status = make_request("GET", "/location/history", 
                                             token=test_data["tourist_token"])
    print_test("Get Location History", success, f"Status: {status}")
    
    # Test 3: Get Safety Trend
    success, response, status = make_request("GET", "/location/safety-trend", 
                                             token=test_data["tourist_token"])
    print_test("Get Safety Trend", success, f"Status: {status}")
    
    # Test 4: Get Safety Analysis
    success, response, status = make_request("GET", "/location/safety-analysis", 
                                             token=test_data["tourist_token"])
    print_test("Get Safety Analysis", success, f"Status: {status}")
    
    # Test 5: Get Nearby Risks
    success, response, status = make_request("GET", "/location/nearby-risks", 
                                             token=test_data["tourist_token"])
    print_test("Get Nearby Risks", success, f"Status: {status}")


# ============================================================================
# SAFETY & ALERT TESTS
# ============================================================================
def test_safety_and_alerts():
    print_header("SAFETY & ALERT TESTS")
    
    if not test_data["tourist_token"]:
        print_test("Skip Safety Tests", False, "No tourist token available")
        return
    
    # Test 1: Get Safety Score
    success, response, status = make_request("GET", "/safety/score", 
                                             token=test_data["tourist_token"])
    print_test("Get Safety Score", success, f"Status: {status}")
    
    # Test 2: Trigger SOS
    sos_data = {
        "latitude": 19.0760,
        "longitude": 72.8777,
        "message": "Test Emergency"
    }
    
    success, response, status = make_request("POST", "/sos/trigger", 
                                             token=test_data["tourist_token"], data=sos_data)
    if success:
        test_data["alert_id"] = response.json().get("alert_id")
    print_test("Trigger SOS Alert", success, f"Status: {status}")


# ============================================================================
# ZONE MANAGEMENT TESTS
# ============================================================================
def test_zone_management():
    print_header("ZONE MANAGEMENT TESTS")
    
    # Test 1: List Zones (Tourist)
    if test_data["tourist_token"]:
        success, response, status = make_request("GET", "/zones/list", 
                                                 token=test_data["tourist_token"])
        print_test("List Zones (Tourist)", success, f"Status: {status}")
    
    # Test 2: Get Nearby Zones
    if test_data["tourist_token"]:
        params = {"latitude": 19.0760, "longitude": 72.8777, "radius_km": 5}
        success, response, status = make_request("GET", "/zones/nearby", 
                                                 token=test_data["tourist_token"], params=params)
        print_test("Get Nearby Zones", success, f"Status: {status}")
    
    # Test 3: Create Zone (Authority)
    if test_data["authority_token"]:
        zone_data = {
            "name": "Test Restricted Zone",
            "description": "Test zone for API testing",
            "zone_type": "restricted",
            "coordinates": [
                [72.8777, 19.0760],
                [72.8780, 19.0760],
                [72.8780, 19.0763],
                [72.8777, 19.0763],
                [72.8777, 19.0760]
            ]
        }
        
        success, response, status = make_request("POST", "/zones/create", 
                                                 token=test_data["authority_token"], data=zone_data)
        if success:
            test_data["zone_id"] = response.json().get("zone_id")
        print_test("Create Zone (Authority)", success, f"Status: {status}")
    
    # Test 4: Manage Zones (Authority)
    if test_data["authority_token"]:
        success, response, status = make_request("GET", "/zones/manage", 
                                                 token=test_data["authority_token"])
        print_test("Manage Zones (Authority)", success, f"Status: {status}")


# ============================================================================
# AUTHORITY MONITORING TESTS
# ============================================================================
def test_authority_monitoring():
    print_header("AUTHORITY MONITORING TESTS")
    
    if not test_data["authority_token"]:
        print_test("Skip Authority Tests", False, "No authority token available")
        return
    
    # Test 1: Get Active Tourists
    success, response, status = make_request("GET", "/tourists/active", 
                                             token=test_data["authority_token"])
    print_test("Get Active Tourists", success, f"Status: {status}")
    
    # Test 2: Get Recent Alerts
    success, response, status = make_request("GET", "/alerts/recent", 
                                             token=test_data["authority_token"])
    print_test("Get Recent Alerts", success, f"Status: {status}")
    
    # Test 3: Get Heatmap Data
    success, response, status = make_request("GET", "/heatmap/data", 
                                             token=test_data["authority_token"])
    print_test("Get Heatmap Data", success, f"Status: {status}")
    
    # Test 4: Get Heatmap Zones
    success, response, status = make_request("GET", "/heatmap/zones", 
                                             token=test_data["authority_token"])
    print_test("Get Heatmap Zones", success, f"Status: {status}")
    
    # Test 5: Get Heatmap Alerts
    success, response, status = make_request("GET", "/heatmap/alerts", 
                                             token=test_data["authority_token"])
    print_test("Get Heatmap Alerts", success, f"Status: {status}")
    
    # Test 6: Get Heatmap Tourists
    success, response, status = make_request("GET", "/heatmap/tourists", 
                                             token=test_data["authority_token"])
    print_test("Get Heatmap Tourists", success, f"Status: {status}")


# ============================================================================
# ALERT RESOLUTION TESTS
# ============================================================================
def test_alert_resolution():
    print_header("ALERT RESOLUTION TESTS")
    
    if not test_data["authority_token"] or not test_data["alert_id"]:
        print_test("Skip Alert Resolution", False, "Missing authority token or alert ID")
        return
    
    # Test 1: Acknowledge Alert
    ack_data = {
        "alert_id": test_data["alert_id"]
    }
    
    success, response, status = make_request("POST", "/incident/acknowledge", 
                                             token=test_data["authority_token"], data=ack_data)
    print_test("Acknowledge Alert", success, f"Status: {status}")
    
    # Test 2: Resolve Alert
    resolve_data = {
        "alert_id": test_data["alert_id"],
        "resolution_notes": "Test resolution"
    }
    
    success, response, status = make_request("POST", "/authority/alert/resolve", 
                                             token=test_data["authority_token"], data=resolve_data)
    print_test("Resolve Alert", success, f"Status: {status}")


# ============================================================================
# PUBLIC API TESTS
# ============================================================================
def test_public_apis():
    print_header("PUBLIC API TESTS (No Auth Required)")
    
    # Test 1: Get Public Panic Alerts (unresolved only)
    success, response, status = make_request("GET", "/public/panic-alerts")
    print_test("Get Public Panic Alerts (Unresolved)", success, f"Status: {status}")
    
    # Test 2: Get Public Panic Alerts (including resolved)
    params = {"show_resolved": True, "hours_back": 48, "limit": 20}
    success, response, status = make_request("GET", "/public/panic-alerts", params=params)
    print_test("Get Public Panic Alerts (All)", success, f"Status: {status}")
    
    # Test 3: Get Public Heatmap Zones
    if test_data["tourist_token"]:
        success, response, status = make_request("GET", "/heatmap/zones/public", 
                                                 token=test_data["tourist_token"])
        print_test("Get Public Heatmap Zones", success, f"Status: {status}")


# ============================================================================
# EFIR TESTS
# ============================================================================
def test_efir_system():
    print_header("EFIR (Emergency FIR) TESTS")
    
    # Test 1: Generate EFIR (Tourist)
    if test_data["tourist_token"] and test_data["alert_id"]:
        efir_data = {
            "alert_id": test_data["alert_id"],
            "incident_description": "Test incident for API testing",
            "suspect_description": "No suspects",
            "witness_details": "Self-reported"
        }
        
        success, response, status = make_request("POST", "/tourist/efir/generate", 
                                                 token=test_data["tourist_token"], data=efir_data)
        if success:
            test_data["efir_id"] = response.json().get("efir_id")
        print_test("Generate EFIR (Tourist)", success, f"Status: {status}")
    
    # Test 2: Get My EFIRs
    if test_data["tourist_token"]:
        success, response, status = make_request("GET", "/efir/my-reports", 
                                                 token=test_data["tourist_token"])
        print_test("Get My EFIRs", success, f"Status: {status}")
    
    # Test 3: List EFIRs (Authority)
    if test_data["authority_token"]:
        success, response, status = make_request("GET", "/authority/efir/list", 
                                                 token=test_data["authority_token"])
        print_test("List EFIRs (Authority)", success, f"Status: {status}")


# ============================================================================
# DEVICE MANAGEMENT TESTS
# ============================================================================
def test_device_management():
    print_header("DEVICE MANAGEMENT TESTS")
    
    if not test_data["tourist_token"]:
        print_test("Skip Device Tests", False, "No tourist token available")
        return
    
    # Test 1: Register Device
    device_data = {
        "device_token": f"test_device_token_{int(time.time())}",
        "device_type": "android",
        "device_name": "Test Android Device"
    }
    test_data["device_token"] = device_data["device_token"]
    
    success, response, status = make_request("POST", "/device/register", 
                                             token=test_data["tourist_token"], data=device_data)
    print_test("Register Device", success, f"Status: {status}")
    
    # Test 2: List Devices
    success, response, status = make_request("GET", "/device/list", 
                                             token=test_data["tourist_token"])
    print_test("List Devices", success, f"Status: {status}")


# ============================================================================
# BROADCAST TESTS
# ============================================================================
def test_broadcast_system():
    print_header("BROADCAST SYSTEM TESTS")
    
    # Test 1: Broadcast to All (Authority)
    if test_data["authority_token"]:
        broadcast_data = {
            "title": "Test Broadcast",
            "body": "This is a test broadcast message",
            "data": {"test": "true"}
        }
        
        success, response, status = make_request("POST", "/broadcast/all", 
                                                 token=test_data["authority_token"], data=broadcast_data)
        if success:
            test_data["broadcast_id"] = response.json().get("broadcast_id")
        print_test("Broadcast to All", success, f"Status: {status}")
    
    # Test 2: Get Broadcast History (Authority)
    if test_data["authority_token"]:
        success, response, status = make_request("GET", "/broadcast/history", 
                                                 token=test_data["authority_token"])
        print_test("Get Broadcast History (Authority)", success, f"Status: {status}")
    
    # Test 3: Get Active Broadcasts (Tourist)
    if test_data["tourist_token"]:
        success, response, status = make_request("GET", "/broadcasts/active", 
                                                 token=test_data["tourist_token"])
        print_test("Get Active Broadcasts (Tourist)", success, f"Status: {status}")
    
    # Test 4: Get Broadcast History (Tourist)
    if test_data["tourist_token"]:
        success, response, status = make_request("GET", "/broadcasts/history", 
                                                 token=test_data["tourist_token"])
        print_test("Get Broadcast History (Tourist)", success, f"Status: {status}")


# ============================================================================
# AI SERVICE TESTS
# ============================================================================
def test_ai_services():
    print_header("AI SERVICE TESTS")
    
    if not test_data["tourist_token"]:
        print_test("Skip AI Tests", False, "No tourist token available")
        return
    
    # Test 1: Geofence Check
    geofence_data = {
        "lat": 19.0760,
        "lon": 72.8777
    }
    
    success, response, status = make_request("POST", "/ai/geofence/check", 
                                             token=test_data["tourist_token"], data=geofence_data)
    print_test("Geofence Check", success, f"Status: {status}")
    
    # Test 2: Nearby Geofence
    success, response, status = make_request("POST", "/ai/geofence/nearby", 
                                             token=test_data["tourist_token"], data=geofence_data)
    print_test("Nearby Geofence", success, f"Status: {status}")
    
    # Test 3: Point Anomaly Detection
    anomaly_data = {
        "lat": 19.0760,
        "lon": 72.8777,
        "speed": 5.2,
        "time_of_day": 14
    }
    
    success, response, status = make_request("POST", "/ai/anomaly/point", 
                                             token=test_data["tourist_token"], data=anomaly_data)
    print_test("Point Anomaly Detection", success, f"Status: {status}")
    
    # Test 4: Safety Score Computation
    safety_data = {
        "lat": 19.0760,
        "lon": 72.8777,
        "time_of_day": 14,
        "day_of_week": 3
    }
    
    success, response, status = make_request("POST", "/ai/score/compute", 
                                             token=test_data["tourist_token"], data=safety_data)
    print_test("Safety Score Computation", success, f"Status: {status}")
    
    # Test 5: Models Status
    success, response, status = make_request("GET", "/ai/models/status", 
                                             token=test_data["tourist_token"])
    print_test("AI Models Status", success, f"Status: {status}")


# ============================================================================
# ADMIN TESTS
# ============================================================================
def test_admin_services():
    print_header("ADMIN SERVICE TESTS")
    
    if not test_data["authority_token"]:
        print_test("Skip Admin Tests", False, "No authority token available")
        return
    
    # Test 1: System Status
    success, response, status = make_request("GET", "/system/status", 
                                             token=test_data["authority_token"])
    print_test("System Status", success, f"Status: {status}")
    
    # Test 2: Users List
    success, response, status = make_request("GET", "/users/list", 
                                             token=test_data["authority_token"])
    print_test("Users List", success, f"Status: {status}")
    
    # Test 3: Analytics Dashboard
    success, response, status = make_request("GET", "/analytics/dashboard", 
                                             token=test_data["authority_token"])
    print_test("Analytics Dashboard", success, f"Status: {status}")


# ============================================================================
# CLEANUP TESTS
# ============================================================================
def test_cleanup():
    print_header("CLEANUP OPERATIONS")
    
    # Test 1: End Trip
    if test_data["tourist_token"]:
        success, response, status = make_request("POST", "/trip/end", 
                                                 token=test_data["tourist_token"])
        print_test("End Trip", success, f"Status: {status}")
    
    # Test 2: Unregister Device
    if test_data["tourist_token"] and test_data["device_token"]:
        params = {"device_token": test_data["device_token"]}
        success, response, status = make_request("DELETE", "/device/unregister", 
                                                 token=test_data["tourist_token"], params=params)
        print_test("Unregister Device", success, f"Status: {status}")
    
    # Test 3: Delete Zone
    if test_data["authority_token"] and test_data["zone_id"]:
        success, response, status = make_request("DELETE", f"/zones/{test_data['zone_id']}", 
                                                 token=test_data["authority_token"])
        print_test("Delete Zone", success, f"Status: {status}")


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================
def run_all_tests():
    """Run all API tests in sequence"""
    start_time = time.time()
    
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║                   SafeHorizon API Test Suite                              ║")
    print("║                   Comprehensive Endpoint Testing                          ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}\n")
    
    print(f"Base URL: {BASE_URL}")
    print(f"Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Run all test suites
    tests = [
        ("Health Check", test_health_check),
        ("Authentication", test_authentication),
        ("Trip Management", test_trip_management),
        ("Location Services", test_location_services),
        ("Safety & Alerts", test_safety_and_alerts),
        ("Zone Management", test_zone_management),
        ("Authority Monitoring", test_authority_monitoring),
        ("Alert Resolution", test_alert_resolution),
        ("Public APIs", test_public_apis),
        ("EFIR System", test_efir_system),
        ("Device Management", test_device_management),
        ("Broadcast System", test_broadcast_system),
        ("AI Services", test_ai_services),
        ("Admin Services", test_admin_services),
        ("Cleanup", test_cleanup),
    ]
    
    for test_name, test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"\n{Colors.RED}Error in {test_name}: {str(e)}{Colors.ENDC}")
    
    # Summary
    elapsed_time = time.time() - start_time
    
    print_header("TEST SUMMARY")
    print(f"Total Time: {elapsed_time:.2f} seconds")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print(f"\n{Colors.BOLD}Test Data Generated:{Colors.ENDC}")
    for key, value in test_data.items():
        if value:
            print(f"  {key}: {value}")
    
    print(f"\n{Colors.BOLD}{Colors.GREEN}All tests completed!{Colors.ENDC}\n")


if __name__ == "__main__":
    print(f"\n{Colors.YELLOW}Starting API tests...{Colors.ENDC}")
    print(f"{Colors.YELLOW}Make sure the server is running at {BASE_URL}{Colors.ENDC}\n")
    
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.RED}Tests interrupted by user{Colors.ENDC}\n")
    except Exception as e:
        print(f"\n\n{Colors.RED}Test suite failed: {str(e)}{Colors.ENDC}\n")
