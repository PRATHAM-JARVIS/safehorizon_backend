"""
Comprehensive API Endpoint Testing Script for SafeHorizon
Tests all endpoints documented in API_DOCUMENTATION.md
"""

import httpx
import asyncio
import json
from typing import Dict, List, Optional
from datetime import datetime
import time

# Configuration
BASE_URL = "http://localhost:8000/api"
HEALTH_URL = "http://localhost:8000/health"

# Test credentials
TOURIST_CREDENTIALS = {
    "email": f"test_tourist_{int(time.time())}@example.com",
    "password": "TestPassword123!",
    "name": "Test Tourist",
    "phone": "+1234567890",
    "emergency_contact": "Emergency Contact",
    "emergency_phone": "+1234567891"
}

AUTHORITY_CREDENTIALS = {
    "email": f"test_officer_{int(time.time())}@police.gov",
    "password": "TestPassword123!",
    "name": "Test Officer",
    "badge_number": f"BADGE{int(time.time())}",
    "department": "Test Department",
    "rank": "Inspector"
}

# Test results storage
test_results = {
    "passed": 0,
    "failed": 0,
    "skipped": 0,
    "total": 0,
    "details": []
}

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_section(title: str):
    """Print a section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title.center(80)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}\n")


def print_test(name: str, status: str, message: str = ""):
    """Print test result"""
    test_results["total"] += 1
    
    if status == "PASS":
        test_results["passed"] += 1
        print(f"{Colors.GREEN}✓ PASS{Colors.RESET} - {name}")
        if message:
            print(f"  └─ {message}")
    elif status == "FAIL":
        test_results["failed"] += 1
        print(f"{Colors.RED}✗ FAIL{Colors.RESET} - {name}")
        if message:
            print(f"  └─ {Colors.RED}{message}{Colors.RESET}")
    elif status == "SKIP":
        test_results["skipped"] += 1
        print(f"{Colors.YELLOW}⊘ SKIP{Colors.RESET} - {name}")
        if message:
            print(f"  └─ {message}")
    
    test_results["details"].append({
        "name": name,
        "status": status,
        "message": message,
        "timestamp": datetime.now().isoformat()
    })


async def test_health_check(client: httpx.AsyncClient):
    """Test health check endpoint"""
    print_section("HEALTH CHECK")
    
    try:
        response = await client.get(HEALTH_URL)
        if response.status_code == 200:
            data = response.json()
            print_test("Health Check", "PASS", f"Status: {data.get('status', 'unknown')}")
        else:
            print_test("Health Check", "FAIL", f"Status code: {response.status_code}")
    except Exception as e:
        print_test("Health Check", "FAIL", f"Error: {str(e)}")


async def test_tourist_auth(client: httpx.AsyncClient) -> Optional[str]:
    """Test tourist authentication endpoints"""
    print_section("TOURIST AUTHENTICATION")
    
    token = None
    
    # Test registration
    try:
        response = await client.post(f"{BASE_URL}/auth/register", json=TOURIST_CREDENTIALS)
        if response.status_code == 200:
            data = response.json()
            print_test("Tourist Registration", "PASS", f"User ID: {data.get('user_id', 'N/A')}")
        else:
            print_test("Tourist Registration", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
            return None
    except Exception as e:
        print_test("Tourist Registration", "FAIL", f"Error: {str(e)}")
        return None
    
    # Test login
    try:
        login_data = {
            "email": TOURIST_CREDENTIALS["email"],
            "password": TOURIST_CREDENTIALS["password"]
        }
        response = await client.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print_test("Tourist Login", "PASS", f"Token received: {token[:20]}..." if token else "No token")
        else:
            print_test("Tourist Login", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
            return None
    except Exception as e:
        print_test("Tourist Login", "FAIL", f"Error: {str(e)}")
        return None
    
    # Test get current user
    if token:
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = await client.get(f"{BASE_URL}/auth/me", headers=headers)
            if response.status_code == 200:
                data = response.json()
                print_test("Get Current User Info", "PASS", f"User: {data.get('name', 'N/A')}")
            else:
                print_test("Get Current User Info", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            print_test("Get Current User Info", "FAIL", f"Error: {str(e)}")
    
    return token


async def test_authority_auth(client: httpx.AsyncClient) -> Optional[str]:
    """Test authority authentication endpoints"""
    print_section("AUTHORITY AUTHENTICATION")
    
    token = None
    
    # Test registration
    try:
        response = await client.post(f"{BASE_URL}/auth/register-authority", json=AUTHORITY_CREDENTIALS)
        if response.status_code == 200:
            data = response.json()
            print_test("Authority Registration", "PASS", f"Badge: {data.get('badge_number', 'N/A')}")
        else:
            print_test("Authority Registration", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
            return None
    except Exception as e:
        print_test("Authority Registration", "FAIL", f"Error: {str(e)}")
        return None
    
    # Test login
    try:
        login_data = {
            "email": AUTHORITY_CREDENTIALS["email"],
            "password": AUTHORITY_CREDENTIALS["password"]
        }
        response = await client.post(f"{BASE_URL}/auth/login-authority", json=login_data)
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print_test("Authority Login", "PASS", f"Token received: {token[:20]}..." if token else "No token")
        else:
            print_test("Authority Login", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
            return None
    except Exception as e:
        print_test("Authority Login", "FAIL", f"Error: {str(e)}")
        return None
    
    return token


async def test_tourist_endpoints(client: httpx.AsyncClient, token: str, tourist_id: str):
    """Test all tourist endpoints"""
    print_section("TOURIST ENDPOINTS - TRIPS")
    
    headers = {"Authorization": f"Bearer {token}"}
    trip_id = None
    
    # Start trip
    try:
        trip_data = {
            "destination": "Test Destination",
            "itinerary": "Test itinerary details"
        }
        response = await client.post(f"{BASE_URL}/trip/start", json=trip_data, headers=headers)
        if response.status_code == 200:
            data = response.json()
            trip_id = data.get("trip_id")
            print_test("Start Trip", "PASS", f"Trip ID: {trip_id}")
        else:
            print_test("Start Trip", "FAIL", f"Status: {response.status_code}")
    except Exception as e:
        print_test("Start Trip", "FAIL", f"Error: {str(e)}")
    
    # Get trip history
    try:
        response = await client.get(f"{BASE_URL}/trip/history", headers=headers)
        if response.status_code == 200:
            trips = response.json()
            print_test("Get Trip History", "PASS", f"Found {len(trips)} trip(s)")
        else:
            print_test("Get Trip History", "FAIL", f"Status: {response.status_code}")
    except Exception as e:
        print_test("Get Trip History", "FAIL", f"Error: {str(e)}")
    
    print_section("TOURIST ENDPOINTS - LOCATION")
    
    # Update location
    try:
        location_data = {
            "lat": 28.6139,
            "lon": 77.2090,
            "speed": 15.5,
            "altitude": 200.0,
            "accuracy": 10.0,
            "timestamp": datetime.now().isoformat()
        }
        response = await client.post(f"{BASE_URL}/location/update", json=location_data, headers=headers)
        if response.status_code == 200:
            data = response.json()
            print_test("Update Location", "PASS", f"Safety Score: {data.get('safety_score', 'N/A')}")
        else:
            print_test("Update Location", "FAIL", f"Status: {response.status_code}")
    except Exception as e:
        print_test("Update Location", "FAIL", f"Error: {str(e)}")
    
    # Get location history
    try:
        response = await client.get(f"{BASE_URL}/location/history?limit=10", headers=headers)
        if response.status_code == 200:
            locations = response.json()
            print_test("Get Location History", "PASS", f"Found {len(locations)} location(s)")
        else:
            print_test("Get Location History", "FAIL", f"Status: {response.status_code}")
    except Exception as e:
        print_test("Get Location History", "FAIL", f"Error: {str(e)}")
    
    print_section("TOURIST ENDPOINTS - SAFETY")
    
    # Get safety score
    try:
        response = await client.get(f"{BASE_URL}/safety/score", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print_test("Get Safety Score", "PASS", f"Score: {data.get('safety_score', 'N/A')}")
        else:
            print_test("Get Safety Score", "FAIL", f"Status: {response.status_code}")
    except Exception as e:
        print_test("Get Safety Score", "FAIL", f"Error: {str(e)}")
    
    print_section("TOURIST ENDPOINTS - ZONES")
    
    # List zones
    try:
        response = await client.get(f"{BASE_URL}/zones/list", headers=headers)
        if response.status_code == 200:
            zones = response.json()
            print_test("List Zones", "PASS", f"Found {len(zones)} zone(s)")
        else:
            print_test("List Zones", "FAIL", f"Status: {response.status_code}")
    except Exception as e:
        print_test("List Zones", "FAIL", f"Error: {str(e)}")
    
    # Get nearby zones
    try:
        response = await client.get(f"{BASE_URL}/zones/nearby?lat=28.6139&lon=77.2090&radius=5000", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print_test("Get Nearby Zones", "PASS", f"Found {len(data.get('nearby_zones', []))} zone(s)")
        else:
            print_test("Get Nearby Zones", "FAIL", f"Status: {response.status_code}")
    except Exception as e:
        print_test("Get Nearby Zones", "FAIL", f"Error: {str(e)}")
    
    print_section("TOURIST ENDPOINTS - DEVICES")
    
    # List devices
    try:
        response = await client.get(f"{BASE_URL}/device/list", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print_test("List Devices", "PASS", f"Found {data.get('count', 0)} device(s)")
        else:
            print_test("List Devices", "FAIL", f"Status: {response.status_code}")
    except Exception as e:
        print_test("List Devices", "FAIL", f"Error: {str(e)}")
    
    print_section("TOURIST ENDPOINTS - BROADCASTS")
    
    # Get active broadcasts
    try:
        response = await client.get(f"{BASE_URL}/broadcasts/active?lat=28.6139&lon=77.2090", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print_test("Get Active Broadcasts", "PASS", f"Found {len(data.get('active_broadcasts', []))} broadcast(s)")
        else:
            print_test("Get Active Broadcasts", "FAIL", f"Status: {response.status_code}")
    except Exception as e:
        print_test("Get Active Broadcasts", "FAIL", f"Error: {str(e)}")
    
    # Get broadcast history
    try:
        response = await client.get(f"{BASE_URL}/broadcasts/history?limit=20", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print_test("Get Broadcast History", "PASS", f"Found {len(data.get('broadcasts', []))} broadcast(s)")
        else:
            print_test("Get Broadcast History", "FAIL", f"Status: {response.status_code}")
    except Exception as e:
        print_test("Get Broadcast History", "FAIL", f"Error: {str(e)}")
    
    print_section("TOURIST ENDPOINTS - E-FIR")
    
    # Get my E-FIRs
    try:
        response = await client.get(f"{BASE_URL}/efir/my-reports?limit=50", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print_test("Get My E-FIRs", "PASS", f"Found {data.get('total', 0)} E-FIR(s)")
        else:
            print_test("Get My E-FIRs", "FAIL", f"Status: {response.status_code}")
    except Exception as e:
        print_test("Get My E-FIRs", "FAIL", f"Error: {str(e)}")
    
    print_section("TOURIST ENDPOINTS - DEBUG")
    
    # Debug role
    try:
        response = await client.get(f"{BASE_URL}/debug/role", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print_test("Debug Role", "PASS", f"Role: {data.get('role', 'N/A')}")
        else:
            print_test("Debug Role", "FAIL", f"Status: {response.status_code}")
    except Exception as e:
        print_test("Debug Role", "FAIL", f"Error: {str(e)}")
    
    # End trip
    if trip_id:
        try:
            response = await client.post(f"{BASE_URL}/trip/end", headers=headers)
            if response.status_code == 200:
                print_test("End Trip", "PASS", "Trip ended successfully")
            else:
                print_test("End Trip", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            print_test("End Trip", "FAIL", f"Error: {str(e)}")


async def test_authority_endpoints(client: httpx.AsyncClient, token: str, tourist_id: str):
    """Test all authority endpoints"""
    print_section("AUTHORITY ENDPOINTS - MONITORING")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get active tourists
    try:
        response = await client.get(f"{BASE_URL}/tourists/active", headers=headers)
        if response.status_code == 200:
            tourists = response.json()
            print_test("Get Active Tourists", "PASS", f"Found {len(tourists)} tourist(s)")
        else:
            print_test("Get Active Tourists", "FAIL", f"Status: {response.status_code}")
    except Exception as e:
        print_test("Get Active Tourists", "FAIL", f"Error: {str(e)}")
    
    # Track specific tourist
    if tourist_id:
        try:
            response = await client.get(f"{BASE_URL}/tourist/{tourist_id}/track", headers=headers)
            if response.status_code == 200:
                data = response.json()
                print_test("Track Tourist", "PASS", f"Tourist: {data.get('tourist', {}).get('name', 'N/A')}")
            else:
                print_test("Track Tourist", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            print_test("Track Tourist", "FAIL", f"Error: {str(e)}")
        
        # Get tourist alerts
        try:
            response = await client.get(f"{BASE_URL}/tourist/{tourist_id}/alerts", headers=headers)
            if response.status_code == 200:
                alerts = response.json()
                print_test("Get Tourist Alerts", "PASS", f"Found {len(alerts)} alert(s)")
            else:
                print_test("Get Tourist Alerts", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            print_test("Get Tourist Alerts", "FAIL", f"Error: {str(e)}")
        
        # Get tourist profile
        try:
            response = await client.get(f"{BASE_URL}/tourist/{tourist_id}/profile", headers=headers)
            if response.status_code == 200:
                data = response.json()
                print_test("Get Tourist Profile", "PASS", f"Tourist: {data.get('tourist', {}).get('name', 'N/A')}")
            else:
                print_test("Get Tourist Profile", "FAIL", f"Status: {response.status_code}, Error: {response.text[:200]}")
        except Exception as e:
            print_test("Get Tourist Profile", "FAIL", f"Error: {str(e)}")
        
        # Get tourist current location
        try:
            response = await client.get(f"{BASE_URL}/tourist/{tourist_id}/location/current", headers=headers)
            if response.status_code == 200:
                data = response.json()
                print_test("Get Tourist Current Location", "PASS", f"Status: {data.get('location', {}).get('status', 'N/A')}")
            else:
                print_test("Get Tourist Current Location", "FAIL", f"Status: {response.status_code}, Error: {response.text[:200]}")
        except Exception as e:
            print_test("Get Tourist Current Location", "FAIL", f"Error: {str(e)}")
        
        # Get tourist location history
        try:
            response = await client.get(f"{BASE_URL}/tourist/{tourist_id}/location/history?hours_back=24&limit=10", headers=headers)
            if response.status_code == 200:
                data = response.json()
                print_test("Get Tourist Location History", "PASS", f"Found {len(data.get('locations', []))} location(s)")
            else:
                print_test("Get Tourist Location History", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            print_test("Get Tourist Location History", "FAIL", f"Error: {str(e)}")
    
    print_section("AUTHORITY ENDPOINTS - ALERTS")
    
    # Get recent alerts
    try:
        response = await client.get(f"{BASE_URL}/alerts/recent?hours=24", headers=headers)
        if response.status_code == 200:
            alerts = response.json()
            print_test("Get Recent Alerts", "PASS", f"Found {len(alerts)} alert(s)")
        else:
            print_test("Get Recent Alerts", "FAIL", f"Status: {response.status_code}")
    except Exception as e:
        print_test("Get Recent Alerts", "FAIL", f"Error: {str(e)}")
    
    print_section("AUTHORITY ENDPOINTS - ZONES")
    
    # List zones for management
    try:
        response = await client.get(f"{BASE_URL}/zones/manage", headers=headers)
        if response.status_code == 200:
            zones = response.json()
            print_test("List Zones (Management)", "PASS", f"Found {len(zones)} zone(s)")
        else:
            print_test("List Zones (Management)", "FAIL", f"Status: {response.status_code}")
    except Exception as e:
        print_test("List Zones (Management)", "FAIL", f"Error: {str(e)}")
    
    print_section("AUTHORITY ENDPOINTS - HEATMAP")
    
    # Get heatmap data
    try:
        response = await client.get(f"{BASE_URL}/heatmap/data?hours_back=24", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print_test("Get Heatmap Data", "PASS", f"Summary: {data.get('metadata', {}).get('summary', {})}")
        else:
            print_test("Get Heatmap Data", "FAIL", f"Status: {response.status_code}, Error: {response.text[:300]}")
    except Exception as e:
        print_test("Get Heatmap Data", "FAIL", f"Error: {str(e)}")
    
    # Get heatmap zones
    try:
        response = await client.get(f"{BASE_URL}/heatmap/zones?zone_type=all", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print_test("Get Heatmap Zones", "PASS", f"Found {data.get('total', 0)} zone(s)")
        else:
            print_test("Get Heatmap Zones", "FAIL", f"Status: {response.status_code}")
    except Exception as e:
        print_test("Get Heatmap Zones", "FAIL", f"Error: {str(e)}")
    
    # Get heatmap alerts
    try:
        response = await client.get(f"{BASE_URL}/heatmap/alerts?hours_back=24", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print_test("Get Heatmap Alerts", "PASS", f"Found {data.get('total', 0)} alert(s)")
        else:
            print_test("Get Heatmap Alerts", "FAIL", f"Status: {response.status_code}, Error: {response.text[:300]}")
    except Exception as e:
        print_test("Get Heatmap Alerts", "FAIL", f"Error: {str(e)}")
    
    # Get heatmap tourists
    try:
        response = await client.get(f"{BASE_URL}/heatmap/tourists?hours_back=24", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print_test("Get Heatmap Tourists", "PASS", f"Found {data.get('total', 0)} tourist(s)")
        else:
            print_test("Get Heatmap Tourists", "FAIL", f"Status: {response.status_code}, Error: {response.text[:300]}")
    except Exception as e:
        print_test("Get Heatmap Tourists", "FAIL", f"Error: {str(e)}")
    
    print_section("AUTHORITY ENDPOINTS - E-FIR")
    
    # List E-FIR records
    try:
        response = await client.get(f"{BASE_URL}/authority/efir/list?limit=100", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print_test("List E-FIR Records", "PASS", f"Found {data.get('pagination', {}).get('total', 0)} E-FIR(s)")
        else:
            print_test("List E-FIR Records", "FAIL", f"Status: {response.status_code}")
    except Exception as e:
        print_test("List E-FIR Records", "FAIL", f"Error: {str(e)}")
    
    print_section("AUTHORITY ENDPOINTS - BROADCASTS")
    
    # Get broadcast history
    try:
        response = await client.get(f"{BASE_URL}/broadcast/history?limit=50", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print_test("Get Broadcast History (Authority)", "PASS", f"Found {data.get('total', 0)} broadcast(s)")
        else:
            print_test("Get Broadcast History (Authority)", "FAIL", f"Status: {response.status_code}")
    except Exception as e:
        print_test("Get Broadcast History (Authority)", "FAIL", f"Error: {str(e)}")


async def test_admin_endpoints(client: httpx.AsyncClient, token: str):
    """Test admin endpoints (if accessible)"""
    print_section("ADMIN ENDPOINTS")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Most admin endpoints would require admin role, so we'll skip them
    print_test("Admin Endpoints", "SKIP", "Requires admin role - skipping admin tests")


async def test_ai_endpoints(client: httpx.AsyncClient, token: str):
    """Test AI service endpoints"""
    print_section("AI SERVICE ENDPOINTS")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get AI model status
    try:
        response = await client.get(f"{BASE_URL}/ai/models/status", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print_test("Get AI Model Status", "PASS", f"Models loaded")
        else:
            print_test("Get AI Model Status", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
        print_test("Get AI Model Status", "FAIL", f"Error: {str(e)}")


def print_summary():
    """Print test summary"""
    print_section("TEST SUMMARY")
    
    total = test_results["total"]
    passed = test_results["passed"]
    failed = test_results["failed"]
    skipped = test_results["skipped"]
    
    pass_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"{Colors.BOLD}Total Tests:{Colors.RESET} {total}")
    print(f"{Colors.GREEN}Passed:{Colors.RESET} {passed} ({pass_rate:.1f}%)")
    print(f"{Colors.RED}Failed:{Colors.RESET} {failed}")
    print(f"{Colors.YELLOW}Skipped:{Colors.RESET} {skipped}")
    
    if failed > 0:
        print(f"\n{Colors.RED}{Colors.BOLD}Some tests failed. Check the output above for details.{Colors.RESET}")
    elif passed > 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}All tests passed! 🎉{Colors.RESET}")
    
    # Save results to file
    with open("test_results.json", "w") as f:
        json.dump(test_results, f, indent=2)
    print(f"\n{Colors.BLUE}Detailed results saved to test_results.json{Colors.RESET}")


async def main():
    """Main test runner"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║                    SafeHorizon API Endpoint Testing                          ║")
    print("║                          Comprehensive Test Suite                            ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.RESET}\n")
    
    print(f"{Colors.BOLD}Configuration:{Colors.RESET}")
    print(f"  Base URL: {BASE_URL}")
    print(f"  Health URL: {HEALTH_URL}")
    print(f"  Timeout: 30 seconds\n")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test health check
        await test_health_check(client)
        
        # Test tourist authentication and get token
        tourist_token = await test_tourist_auth(client)
        
        # Extract tourist ID from token (you'll need to decode JWT or get from /auth/me)
        tourist_id = None
        if tourist_token:
            try:
                headers = {"Authorization": f"Bearer {tourist_token}"}
                response = await client.get(f"{BASE_URL}/auth/me", headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    tourist_id = data.get("id")
            except:
                pass
        
        # Test authority authentication and get token
        authority_token = await test_authority_auth(client)
        
        # Test tourist endpoints
        if tourist_token:
            await test_tourist_endpoints(client, tourist_token, tourist_id)
        else:
            print_test("Tourist Endpoints", "SKIP", "No tourist token available")
        
        # Test authority endpoints
        if authority_token and tourist_id:
            await test_authority_endpoints(client, authority_token, tourist_id)
        else:
            print_test("Authority Endpoints", "SKIP", "No authority token or tourist ID available")
        
        # Test AI endpoints
        if tourist_token:
            await test_ai_endpoints(client, tourist_token)
        else:
            print_test("AI Endpoints", "SKIP", "No token available")
    
    # Print summary
    print_summary()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Tests interrupted by user{Colors.RESET}")
    except Exception as e:
        print(f"\n\n{Colors.RED}Fatal error: {str(e)}{Colors.RESET}")
        import traceback
        traceback.print_exc()
