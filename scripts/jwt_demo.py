#!/usr/bin/env python3
"""
JWT Authentication Demo for Event Analytics API.

This script demonstrates that JWT authentication is working correctly.
Run this after starting the API server with: uvicorn app.main:app --reload
"""

import requests
import json
import sys
from uuid import uuid4
from datetime import datetime


def main():
    """Demo JWT authentication functionality."""
    base_url = "http://localhost:8000"
    
    print("🔐 JWT Authentication Demo")
    print("=" * 50)
    
    # Step 1: Try to access protected endpoint without authentication
    print("\n1. Testing protected endpoint without authentication...")
    response = requests.post(
        f"{base_url}/api/v1/events",
        json={
            "events": [{
                "event_id": str(uuid4()),
                "occurred_at": datetime.now().isoformat(),
                "user_id": 1,
                "event_type": "test_event",
                "properties": {"test": True}
            }]
        }
    )
    
    if response.status_code == 403:
        print("✅ Correctly rejected request without authentication")
    else:
        print(f"❌ Expected 403, got {response.status_code}")
        return
    
    # Step 2: Login to get JWT token
    print("\n2. Logging in to get JWT token...")
    login_response = requests.post(
        f"{base_url}/api/v1/auth/login",
        json={
            "username": "admin",
            "password": "admin123"
        }
    )
    
    if login_response.status_code == 200:
        token_data = login_response.json()
        access_token = token_data["access_token"]
        print("✅ Successfully logged in and received JWT token")
        print(f"   Token type: {token_data['token_type']}")
        print(f"   Expires in: {token_data['expires_in']} seconds")
        print(f"   User: {token_data['user']['username']} (admin: {token_data['user']['is_admin']})")
    else:
        print(f"❌ Login failed: {login_response.status_code} - {login_response.text}")
        return
    
    # Step 3: Access protected endpoint with valid token
    print("\n3. Testing protected endpoint with valid JWT token...")
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = requests.post(
        f"{base_url}/api/v1/events",
        json={
            "events": [{
                "event_id": str(uuid4()),
                "occurred_at": datetime.now().isoformat(),
                "user_id": 1,
                "event_type": "auth_demo_event",
                "properties": {"demo": True, "authenticated": True}
            }]
        },
        headers=headers
    )
    
    if response.status_code == 201:
        result = response.json()
        print("✅ Successfully created event with authentication")
        print(f"   Created: {result['created']} events")
    else:
        print(f"❌ Failed to create event: {response.status_code} - {response.text}")
        return
    
    # Step 4: Get current user info
    print("\n4. Getting current user information...")
    response = requests.get(
        f"{base_url}/api/v1/auth/me",
        headers=headers
    )
    
    if response.status_code == 200:
        user_info = response.json()
        print("✅ Successfully retrieved user information")
        print(f"   Username: {user_info['username']}")
        print(f"   Email: {user_info['email']}")
        print(f"   Admin: {user_info['is_admin']}")
        print(f"   Active: {user_info['is_active']}")
    else:
        print(f"❌ Failed to get user info: {response.status_code} - {response.text}")
        return
    
    # Step 5: Test with invalid token
    print("\n5. Testing with invalid JWT token...")
    invalid_headers = {"Authorization": "Bearer invalid_token_12345"}
    
    response = requests.post(
        f"{base_url}/api/v1/events",
        json={
            "events": [{
                "event_id": str(uuid4()),
                "occurred_at": datetime.now().isoformat(),
                "user_id": 1,
                "event_type": "test_event",
                "properties": {"test": True}
            }]
        },
        headers=invalid_headers
    )
    
    if response.status_code == 401:
        print("✅ Correctly rejected request with invalid token")
    else:
        print(f"❌ Expected 401, got {response.status_code}")
        return
    
    print("\n" + "=" * 50)
    print("🎉 JWT Authentication Demo completed successfully!")
    print("\nKey features demonstrated:")
    print("- ✅ Protected endpoints reject unauthenticated requests")
    print("- ✅ User login returns valid JWT tokens")
    print("- ✅ Valid tokens allow access to protected endpoints")
    print("- ✅ User information can be retrieved with valid tokens")
    print("- ✅ Invalid tokens are properly rejected")


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to API server")
        print("Please start the server with: uvicorn app.main:app --reload")
        print("Or run it in background: uvicorn app.main:app --host 0.0.0.0 --port 8000 &")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n❌ Demo cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
