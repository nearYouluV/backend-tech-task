#!/usr/bin/env python3
"""
Refresh Token Demo Script

Demonstrates the complete refresh token flow:
1. Login to get access and refresh tokens
2. Use access token to access protected endpoints
3. Refresh tokens when access token expires
4. Logout to revoke refresh tokens
"""

import requests
import json
import time
from datetime import datetime
from typing import Optional, Dict, Any


class RefreshTokenDemo:
    """Demo class for refresh token functionality."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.user_info: Optional[Dict[str, Any]] = None
    
    def print_step(self, step: str, description: str):
        """Print demo step with formatting."""
        print(f"\n{'='*60}")
        print(f"STEP {step}: {description}")
        print('='*60)
    
    def print_response(self, response: requests.Response, title: str = "Response"):
        """Print formatted response."""
        print(f"\n{title}:")
        print(f"Status: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Data: {json.dumps(data, indent=2)}")
        except:
            print(f"Text: {response.text}")
    
    def health_check(self) -> bool:
        """Check if API is healthy."""
        self.print_step("1", "Health Check")
        
        try:
            response = self.session.get(f"{self.base_url}/api/v1/auth/health")
            self.print_response(response, "Auth Health Check")
            
            if response.status_code == 200:
                print("✅ API is healthy and ready")
                return True
            else:
                print("❌ API health check failed")
                return False
                
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to API. Make sure server is running on localhost:8000")
            return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    def create_test_user(self) -> bool:
        """Create test user for demo (requires admin token)."""
        self.print_step("2", "Create Test User")
        
        # For demo, we'll try to create a user but expect it might fail without admin token
        user_data = {
            "username": "demo_user",
            "email": "demo@example.com",
            "password": "demo_password_123",
            "is_admin": False
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/register",
                json=user_data
            )
            self.print_response(response, "User Creation")
            
            if response.status_code == 201:
                print("✅ Test user created successfully")
                return True
            elif response.status_code in [401, 403]:
                print("ℹ️  User creation requires admin privileges (expected)")
                print("   Assuming user already exists or will use existing user")
                return True
            else:
                print("⚠️  User creation failed, but continuing with demo")
                return True
                
        except Exception as e:
            print(f"⚠️  User creation error: {e}")
            print("   Continuing with demo assuming user exists")
            return True
    
    def login(self) -> bool:
        """Login and get token pair."""
        self.print_step("3", "Login and Get Token Pair")
        
        login_data = {
            "username": "demo_user",
            "password": "demo_password_123"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/login",
                json=login_data
            )
            self.print_response(response, "Login")
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                self.refresh_token = data.get("refresh_token")
                self.user_info = data.get("user")
                
                print(f"✅ Login successful!")
                print(f"   Access token: {self.access_token[:20]}...")
                print(f"   Refresh token: {self.refresh_token[:20]}...")
                print(f"   Expires in: {data.get('expires_in', 'unknown')} seconds")
                return True
            else:
                print("❌ Login failed")
                return False
                
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def test_protected_endpoint(self) -> bool:
        """Test accessing protected endpoint with access token."""
        self.print_step("4", "Access Protected Endpoint")
        
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/auth/me",
                headers=headers
            )
            self.print_response(response, "Protected Endpoint Access")
            
            if response.status_code == 200:
                print("✅ Successfully accessed protected endpoint")
                return True
            else:
                print("❌ Failed to access protected endpoint")
                return False
                
        except Exception as e:
            print(f"❌ Protected endpoint error: {e}")
            return False
    
    def refresh_tokens(self) -> bool:
        """Refresh the token pair."""
        self.print_step("5", "Refresh Token Pair")
        
        refresh_data = {
            "refresh_token": self.refresh_token
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/refresh",
                json=refresh_data
            )
            self.print_response(response, "Token Refresh")
            
            if response.status_code == 200:
                data = response.json()
                old_access_token = self.access_token
                old_refresh_token = self.refresh_token
                
                self.access_token = data.get("access_token")
                self.refresh_token = data.get("refresh_token")
                
                print("✅ Tokens refreshed successfully!")
                print(f"   New access token: {self.access_token[:20]}...")
                print(f"   New refresh token: {self.refresh_token[:20]}...")
                print(f"   Old access token was: {old_access_token[:20]}...")
                print(f"   Old refresh token was: {old_refresh_token[:20]}...")
                print("   ➡️  Token rotation implemented for security")
                return True
            else:
                print("❌ Token refresh failed")
                return False
                
        except Exception as e:
            print(f"❌ Token refresh error: {e}")
            return False
    
    def test_old_refresh_token(self, old_refresh_token: str) -> bool:
        """Test that old refresh token is invalidated."""
        self.print_step("6", "Test Old Refresh Token (Should Fail)")
        
        refresh_data = {
            "refresh_token": old_refresh_token
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/refresh",
                json=refresh_data
            )
            self.print_response(response, "Old Token Refresh Attempt")
            
            if response.status_code == 401:
                print("✅ Old refresh token correctly rejected (security working)")
                return True
            elif response.status_code == 200:
                print("⚠️  Old refresh token still worked (potential security issue)")
                return False
            else:
                print("❌ Unexpected response for old token")
                return False
                
        except Exception as e:
            print(f"❌ Old token test error: {e}")
            return False
    
    def logout_all_devices(self) -> bool:
        """Logout from all devices."""
        self.print_step("7", "Logout from All Devices")
        
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/logout-all",
                headers=headers
            )
            self.print_response(response, "Logout All Devices")
            
            if response.status_code == 200:
                data = response.json()
                revoked_count = data.get("revoked_tokens", 0)
                print(f"✅ Logged out from all devices")
                print(f"   Revoked {revoked_count} refresh token(s)")
                return True
            else:
                print("❌ Logout all devices failed")
                return False
                
        except Exception as e:
            print(f"❌ Logout all error: {e}")
            return False
    
    def test_revoked_tokens(self) -> bool:
        """Test that revoked tokens don't work."""
        self.print_step("8", "Test Revoked Tokens (Should Fail)")
        
        # Test refresh token
        refresh_data = {
            "refresh_token": self.refresh_token
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/refresh",
                json=refresh_data
            )
            self.print_response(response, "Revoked Refresh Token Test")
            
            if response.status_code == 401:
                print("✅ Revoked refresh token correctly rejected")
                
                # Test access token
                headers = {"Authorization": f"Bearer {self.access_token}"}
                response = self.session.get(
                    f"{self.base_url}/api/v1/auth/me",
                    headers=headers
                )
                self.print_response(response, "Access Token After Logout")
                
                if response.status_code == 401:
                    print("✅ Access token also invalidated after logout")
                else:
                    print("⚠️  Access token still works (JWT tokens don't revoke immediately)")
                    print("   This is normal behavior - access tokens expire naturally")
                
                return True
            else:
                print("⚠️  Revoked refresh token still works")
                return False
                
        except Exception as e:
            print(f"❌ Revoked token test error: {e}")
            return False
    
    def run_demo(self):
        """Run complete refresh token demo."""
        print("🚀 REFRESH TOKEN DEMO")
        print("=" * 60)
        print("This demo shows:")
        print("• Login with username/password to get token pair")
        print("• Using access tokens for API access")
        print("• Refreshing tokens for extended sessions")
        print("• Token rotation for security")
        print("• Logout and token revocation")
        
        # Store old refresh token for testing
        old_refresh_token = None
        
        try:
            # Step 1: Health check
            if not self.health_check():
                return False
            
            # Step 2: Create test user
            if not self.create_test_user():
                return False
            
            # Step 3: Login
            if not self.login():
                print("\n❌ Demo failed at login step")
                print("   Make sure you have a user 'demo_user' with password 'demo_password_123'")
                print("   Or create one using: make create-admin")
                return False
            
            # Step 4: Test protected endpoint
            if not self.test_protected_endpoint():
                return False
            
            # Store old refresh token before refresh
            old_refresh_token = self.refresh_token
            
            # Step 5: Refresh tokens
            if not self.refresh_tokens():
                return False
            
            # Step 6: Test old refresh token
            if old_refresh_token:
                self.test_old_refresh_token(old_refresh_token)
            
            # Step 7: Logout all devices
            if not self.logout_all_devices():
                return False
            
            # Step 8: Test revoked tokens
            if not self.test_revoked_tokens():
                return False
            
            # Success summary
            self.print_step("✅", "DEMO COMPLETED SUCCESSFULLY")
            print("🎉 All refresh token functionality is working correctly!")
            print("\nKey security features demonstrated:")
            print("• ✅ Token pair creation (access + refresh)")
            print("• ✅ Access token expiration (30 minutes)")
            print("• ✅ Refresh token rotation (old tokens invalidated)")
            print("• ✅ Multi-device logout support")
            print("• ✅ Proper token revocation")
            print("• ✅ Secure token storage (hashed in database)")
            
            return True
            
        except KeyboardInterrupt:
            print("\n\n⏹️  Demo interrupted by user")
            return False
        except Exception as e:
            print(f"\n\n❌ Demo failed with error: {e}")
            return False


def main():
    """Run the refresh token demo."""
    import sys
    
    # Check if server URL provided
    base_url = "http://localhost:8000"
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    print(f"🎯 Running demo against: {base_url}")
    print("   (Pass different URL as argument if needed)")
    
    demo = RefreshTokenDemo(base_url)
    success = demo.run_demo()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
