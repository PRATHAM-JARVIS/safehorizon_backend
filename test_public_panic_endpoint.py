"""
Test script for the public panic alerts endpoint
This endpoint should work WITHOUT authentication
"""
import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_public_panic_alerts():
    """Test the public panic alerts endpoint (no auth required)"""
    print("\n" + "="*60)
    print("Testing Public Panic Alerts Endpoint")
    print("="*60 + "\n")
    
    endpoint = f"{BASE_URL}/notify/public/panic-alerts"
    
    # Test 1: Default parameters
    print("Test 1: Get panic alerts with default parameters")
    print(f"GET {endpoint}")
    response = requests.get(endpoint)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ SUCCESS!")
        print(f"Total Alerts: {data['total_alerts']}")
        print(f"Active Count: {data['active_count']}")
        print(f"Hours Back: {data['hours_back']}")
        print(f"\nAlerts:")
        for alert in data['alerts'][:3]:  # Show first 3
            print(f"  - {alert['type'].upper()}: {alert['title']}")
            print(f"    Severity: {alert['severity']}")
            print(f"    Status: {alert['status']}")
            if alert['location']:
                print(f"    Location: ({alert['location']['lat']}, {alert['location']['lon']})")
            print(f"    Time ago: {alert['time_ago']}")
            print()
    else:
        print(f"❌ FAILED!")
        print(f"Response: {response.text}")
    
    print("\n" + "-"*60 + "\n")
    
    # Test 2: Custom parameters
    print("Test 2: Get panic alerts with custom parameters (limit=10, hours_back=6)")
    params = {"limit": 10, "hours_back": 6}
    print(f"GET {endpoint}?limit=10&hours_back=6")
    response = requests.get(endpoint, params=params)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ SUCCESS!")
        print(f"Total Alerts: {data['total_alerts']}")
        print(f"Active Count: {data['active_count']}")
        print(f"Hours Back: {data['hours_back']}")
    else:
        print(f"❌ FAILED!")
        print(f"Response: {response.text}")
    
    print("\n" + "-"*60 + "\n")
    
    # Test 3: Verify no authentication required
    print("Test 3: Verify endpoint works WITHOUT authentication")
    print(f"GET {endpoint} (no Authorization header)")
    response = requests.get(endpoint)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print(f"✅ SUCCESS! Public endpoint works without auth")
    elif response.status_code == 401:
        print(f"❌ FAILED! Endpoint requires authentication (should be public)")
    else:
        print(f"⚠️  Unexpected status code")
    
    print("\n" + "="*60)
    print("Testing Complete!")
    print("="*60 + "\n")

if __name__ == "__main__":
    try:
        test_public_panic_alerts()
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to server.")
        print("Make sure the server is running at http://localhost:8000")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
