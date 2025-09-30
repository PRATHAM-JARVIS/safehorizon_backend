#!/usr/bin/env python3
"""
Debug script to test role-based access control issues
"""
import requests
import json

# Configuration
BASE_URL = "http://localhost:8000/api"

def test_endpoints_with_token(token, user_type="unknown"):
    """Test various endpoints with a given token"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"\n🔍 Testing endpoints with {user_type} token...")
    print(f"Token: {token[:20]}...")
    
    endpoints = [
        ("GET", "/auth/me", "Get user info"),
        ("GET", "/debug/role", "Debug role info"),
        ("GET", "/safety/score", "Tourist safety score"),
        ("GET", "/zones/list", "Tourist zones list"),
        ("GET", "/alerts/recent", "Authority alerts (should fail for tourist)"),
    ]
    
    for method, endpoint, description in endpoints:
        try:
            url = f"{BASE_URL}{endpoint}"
            response = requests.get(url, headers=headers)
            
            status_emoji = "✅" if response.status_code < 400 else "❌"
            print(f"{status_emoji} {method} {endpoint} - {response.status_code} - {description}")
            
            if response.status_code == 403:
                print(f"   📝 Error: {response.json().get('detail', 'No detail')}")
            elif response.status_code == 200:
                data = response.json()
                if endpoint == "/debug/role":
                    print(f"   👤 Role: {data.get('role')}, Email: {data.get('email')}")
                elif endpoint == "/auth/me":
                    print(f"   👤 ID: {data.get('id')}, Email: {data.get('email')}")
                    
        except Exception as e:
            print(f"❌ {method} {endpoint} - ERROR - {str(e)}")

def register_and_test_tourist():
    """Register a new tourist and test endpoints"""
    print("\n🏗️ Registering new tourist...")
    
    # Register tourist
    tourist_data = {
        "email": f"test_tourist_{hash('test') % 10000}@example.com",
        "password": "password123",
        "name": "Test Tourist"
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=tourist_data)
    if response.status_code != 200:
        print(f"❌ Registration failed: {response.status_code} - {response.text}")
        return None
        
    print(f"✅ Tourist registered: {tourist_data['email']}")
    
    # Login
    login_data = {"email": tourist_data["email"], "password": tourist_data["password"]}
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        return None
        
    token_data = response.json()
    token = token_data.get("access_token")
    print(f"✅ Tourist logged in, role: {token_data.get('role')}")
    
    return token

def register_and_test_authority():
    """Register a new authority and test endpoints"""
    print("\n🏗️ Registering new authority...")
    
    # Register authority
    authority_data = {
        "email": f"test_authority_{hash('test') % 10000}@example.com",
        "password": "password123",
        "name": "Test Authority",
        "badge_number": f"BADGE{hash('test') % 10000}",
        "department": "Test Police Dept"
    }
    
    response = requests.post(f"{BASE_URL}/auth/register-authority", json=authority_data)
    if response.status_code != 200:
        print(f"❌ Authority registration failed: {response.status_code} - {response.text}")
        return None
        
    print(f"✅ Authority registered: {authority_data['email']}")
    
    # Login
    login_data = {"email": authority_data["email"], "password": authority_data["password"]}
    response = requests.post(f"{BASE_URL}/auth/login-authority", json=login_data)
    
    if response.status_code != 200:
        print(f"❌ Authority login failed: {response.status_code} - {response.text}")
        return None
        
    token_data = response.json()
    token = token_data.get("access_token")
    print(f"✅ Authority logged in, role: {token_data.get('role')}")
    
    return token

def main():
    print("🔍 SafeHorizon Role-Based Access Control Debug Test")
    print("=" * 60)
    
    # Test with tourist account
    tourist_token = register_and_test_tourist()
    if tourist_token:
        test_endpoints_with_token(tourist_token, "TOURIST")
    
    # Test with authority account  
    authority_token = register_and_test_authority()
    if authority_token:
        test_endpoints_with_token(authority_token, "AUTHORITY")
    
    print("\n" + "=" * 60)
    print("🎯 EXPECTED RESULTS:")
    print("✅ Tourist should access: /auth/me, /debug/role, /safety/score, /zones/list")
    print("❌ Tourist should NOT access: /alerts/recent")
    print("✅ Authority should access: /debug/role, /alerts/recent")
    print("❌ Authority should NOT access: /auth/me, /safety/score")

if __name__ == "__main__":
    main()