#!/usr/bin/env python3
"""
Test script for specific user: apple@gmail.com
"""
import requests
import json
import bcrypt

BASE_URL = "http://localhost:8000/api"

def verify_bcrypt_password(password, hash_str):
    """Verify if a password matches the bcrypt hash"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hash_str.encode('utf-8'))
    except Exception as e:
        print(f"❌ Bcrypt verification error: {e}")
        return False

def test_password_hash():
    """Test password against the known bcrypt hash"""
    hash_from_db = "$2b$12$XiownLQkX4tf57WFc.V1ieNuXqJqhDEGNvE46SyTigwLKjWXQ3WQi"
    
    print("🔐 Testing passwords against bcrypt hash...")
    passwords_to_try = ["apple", "password", "123456", "apple123", "password123", "admin", "test"]
    
    for password in passwords_to_try:
        is_match = verify_bcrypt_password(password, hash_from_db)
        status = "✅" if is_match else "❌"
        print(f"{status} Password '{password}': {'MATCH' if is_match else 'no match'}")
        if is_match:
            return password
    
    return None

def test_login_endpoints(email, password):
    """Test both tourist and authority login endpoints"""
    print(f"\n🔐 Testing login endpoints for {email}...")
    
    login_data = {"email": email, "password": password}
    
    # Test tourist login
    print("1️⃣ Testing tourist login (/auth/login)...")
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        token_data = response.json()
        print(f"✅ Tourist login successful!")
        print(f"   Role: {token_data.get('role')}")
        print(f"   User ID: {token_data.get('user_id')}")
        return token_data.get('access_token'), 'tourist'
    else:
        print(f"❌ Tourist login failed: {response.status_code} - {response.text}")
    
    # Test authority login
    print("2️⃣ Testing authority login (/auth/login-authority)...")
    response = requests.post(f"{BASE_URL}/auth/login-authority", json=login_data)
    if response.status_code == 200:
        token_data = response.json()
        print(f"✅ Authority login successful!")
        print(f"   Role: {token_data.get('role')}")
        print(f"   User ID: {token_data.get('user_id')}")
        return token_data.get('access_token'), 'authority'
    else:
        print(f"❌ Authority login failed: {response.status_code} - {response.text}")
    
    return None, None

def test_endpoints_with_token(token, user_type):
    """Test the problematic endpoints with the token"""
    print(f"\n🧪 Testing endpoints with {user_type} token...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test debug endpoint first
    response = requests.get(f"{BASE_URL}/debug/role", headers=headers)
    if response.status_code == 200:
        debug_data = response.json()
        print(f"✅ Debug info:")
        print(f"   🆔 User ID: {debug_data.get('user_id')}")
        print(f"   📧 Email: {debug_data.get('email')}")
        print(f"   👤 Role: {debug_data.get('role')}")
        print(f"   🎯 Expected DB ID: f9c79598ad92dbcfd09ac3cad5026c78")
        print(f"   � ID Match: {debug_data.get('user_id') == 'f9c79598ad92dbcfd09ac3cad5026c78'}")
    else:
        print(f"❌ Debug failed: {response.status_code} - {response.text}")
        return
    
    # Test the problematic endpoints
    endpoints_to_test = [
        ("/safety/score", "Safety Score"),
        ("/zones/list", "Zones List"),
        ("/auth/me", "Auth Me")
    ]
    
    for endpoint, name in endpoints_to_test:
        response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
        status_emoji = "✅" if response.status_code == 200 else "❌"
        print(f"{status_emoji} {name}: {response.status_code}")
        
        if response.status_code == 403:
            error_detail = response.json().get('detail', 'No detail')
            print(f"   📝 Error: {error_detail}")

def main():
    print("🔍 Comprehensive test for apple@gmail.com user")
    print("=" * 60)
    
    # First, find the correct password
    correct_password = test_password_hash()
    
    if not correct_password:
        print("\n❌ Could not find matching password for the bcrypt hash")
        print("💡 Try resetting the user's password or creating a new test user")
        return
    
    print(f"\n✅ Found matching password: '{correct_password}'")
    
    # Test login endpoints
    token, user_type = test_login_endpoints("apple@gmail.com", correct_password)
    
    if token:
        test_endpoints_with_token(token, user_type)
    else:
        print("\n❌ Could not obtain a valid token")
        print("💡 The user might not exist in the database or there's an authentication issue")

if __name__ == "__main__":
    main()