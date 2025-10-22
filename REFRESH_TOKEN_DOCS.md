# 🔄 Refresh Token Documentation

## Overview

This project implements a secure JWT-based authentication system with refresh tokens. The system provides both short-lived access tokens (30 minutes) and longer-lived refresh tokens (7 days) for extended session management while maintaining security.

## 🏗️ Architecture

### Token Types

1. **Access Token** (JWT)
   - Expires in 30 minutes
   - Contains user ID and username
   - Used for API authentication
   - Stateless and self-contained

2. **Refresh Token** (Secure Random)
   - Expires in 7 days
   - Cryptographically secure random string
   - Stored in database (hashed)
   - Used to obtain new access tokens

### Security Features

- ✅ **Token Rotation**: Old refresh tokens are invalidated when new ones are issued
- ✅ **Secure Storage**: Refresh tokens are hashed before database storage
- ✅ **Expiration Handling**: Automatic cleanup of expired tokens
- ✅ **Multi-device Support**: Each device gets its own refresh token
- ✅ **Revocation**: Ability to logout from single device or all devices

## 📋 API Endpoints

### Authentication Endpoints

#### POST `/api/v1/auth/login`
Login with username/password to get token pair.

**Request:**
```json
{
  "username": "user@example.com",
  "password": "secure_password"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1Q...",
  "refresh_token": "abc123xyz789...",
  "expires_in": 1800,
  "user": {
    "id": "user-id",
    "username": "user@example.com",
    "email": "user@example.com",
    "is_active": true,
    "is_admin": false
  }
}
```

#### POST `/api/v1/auth/refresh`
Exchange refresh token for new token pair.

**Request:**
```json
{
  "refresh_token": "abc123xyz789..."
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1Q...",
  "refresh_token": "new_xyz789abc...",
  "expires_in": 1800,
  "user": {
    "id": "user-id",
    "username": "user@example.com",
    "email": "user@example.com",
    "is_active": true,
    "is_admin": false
  }
}
```

#### POST `/api/v1/auth/logout`
Revoke a specific refresh token.

**Request:**
```json
{
  "refresh_token": "abc123xyz789..."
}
```

**Response:**
```json
{
  "message": "Successfully logged out",
  "revoked": true
}
```

#### POST `/api/v1/auth/logout-all`
Revoke all refresh tokens for the user (logout from all devices).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "message": "Successfully logged out from 3 device(s)",
  "revoked_tokens": 3
}
```

#### GET `/api/v1/auth/me`
Get current user information.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "id": "user-id",
  "username": "user@example.com",
  "email": "user@example.com",
  "is_active": true,
  "is_admin": false,
  "created_at": "2025-01-13T10:30:00Z"
}
```

## 🔒 Security Implementation

### Token Hashing
Refresh tokens are hashed using SHA-256 before database storage:

```python
def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
```

### Token Creation
Refresh tokens are generated using cryptographically secure random:

```python
def create_refresh_token() -> str:
    return secrets.token_urlsafe(64)
```

### Database Schema
```sql
CREATE TABLE refresh_tokens (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    token_hash VARCHAR NOT NULL UNIQUE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_revoked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_refresh_tokens_expires ON refresh_tokens(expires_at);
CREATE INDEX idx_refresh_tokens_user ON refresh_tokens(user_id);
```

## 🔄 Token Flow

### 1. Initial Login
```
Client → POST /auth/login → Server
                        ← {access_token, refresh_token}
```

### 2. API Requests
```
Client → GET /api/endpoint → Server
       Authorization: Bearer <access_token>
```

### 3. Token Refresh
```
Client → POST /auth/refresh → Server
       {refresh_token}     ← {new_access_token, new_refresh_token}
```

### 4. Logout
```
Client → POST /auth/logout → Server
       {refresh_token}    ← {success: true}
```

## 🛠️ Usage Examples

### JavaScript/TypeScript Client

```typescript
class AuthClient {
  private accessToken: string | null = null;
  private refreshToken: string | null = null;

  async login(username: string, password: string) {
    const response = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });

    if (response.ok) {
      const data = await response.json();
      this.accessToken = data.access_token;
      this.refreshToken = data.refresh_token;
      
      // Store refresh token securely (e.g., httpOnly cookie)
      localStorage.setItem('refreshToken', this.refreshToken);
    }
  }

  async makeRequest(url: string, options: RequestInit = {}) {
    // Try request with current access token
    let response = await fetch(url, {
      ...options,
      headers: {
        ...options.headers,
        'Authorization': `Bearer ${this.accessToken}`
      }
    });

    // If token expired, refresh and retry
    if (response.status === 401) {
      await this.refreshTokens();
      response = await fetch(url, {
        ...options,
        headers: {
          ...options.headers,
          'Authorization': `Bearer ${this.accessToken}`
        }
      });
    }

    return response;
  }

  async refreshTokens() {
    const response = await fetch('/api/v1/auth/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        refresh_token: this.refreshToken 
      })
    });

    if (response.ok) {
      const data = await response.json();
      this.accessToken = data.access_token;
      this.refreshToken = data.refresh_token;
      localStorage.setItem('refreshToken', this.refreshToken);
    } else {
      // Refresh token expired, redirect to login
      this.logout();
      window.location.href = '/login';
    }
  }

  async logout() {
    if (this.refreshToken) {
      await fetch('/api/v1/auth/logout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          refresh_token: this.refreshToken 
        })
      });
    }

    this.accessToken = null;
    this.refreshToken = null;
    localStorage.removeItem('refreshToken');
  }

  async logoutAllDevices() {
    await fetch('/api/v1/auth/logout-all', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.accessToken}`
      }
    });

    this.logout(); // Clear local tokens
  }
}
```

### Python Client

```python
import requests
import json
from typing import Optional, Dict, Any

class AuthClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.session = requests.Session()

    def login(self, username: str, password: str) -> bool:
        """Login and store tokens."""
        response = self.session.post(
            f"{self.base_url}/api/v1/auth/login",
            json={"username": username, "password": password}
        )
        
        if response.status_code == 200:
            data = response.json()
            self.access_token = data["access_token"]
            self.refresh_token = data["refresh_token"]
            return True
        return False

    def make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Make authenticated request with automatic token refresh."""
        headers = kwargs.get("headers", {})
        headers["Authorization"] = f"Bearer {self.access_token}"
        kwargs["headers"] = headers

        response = self.session.request(method, url, **kwargs)

        # If token expired, refresh and retry
        if response.status_code == 401:
            if self.refresh_tokens():
                headers["Authorization"] = f"Bearer {self.access_token}"
                response = self.session.request(method, url, **kwargs)

        return response

    def refresh_tokens(self) -> bool:
        """Refresh access token using refresh token."""
        if not self.refresh_token:
            return False

        response = self.session.post(
            f"{self.base_url}/api/v1/auth/refresh",
            json={"refresh_token": self.refresh_token}
        )

        if response.status_code == 200:
            data = response.json()
            self.access_token = data["access_token"]
            self.refresh_token = data["refresh_token"]
            return True
        return False

    def logout(self) -> bool:
        """Logout and revoke refresh token."""
        if not self.refresh_token:
            return True

        response = self.session.post(
            f"{self.base_url}/api/v1/auth/logout",
            json={"refresh_token": self.refresh_token}
        )

        self.access_token = None
        self.refresh_token = None
        return response.status_code == 200

    def logout_all_devices(self) -> bool:
        """Logout from all devices."""
        response = self.make_request(
            "POST",
            f"{self.base_url}/api/v1/auth/logout-all"
        )
        
        if response.status_code == 200:
            self.logout()  # Clear local tokens
            return True
        return False
```

## 🧪 Testing

### Running Tests

```bash
# Test refresh token functionality
make test-refresh

# Test complete authentication
make test-auth

# Run all tests
make test
```

### Demo Script

```bash
# Run interactive refresh token demo
make refresh-demo

# The demo will:
# 1. Login to get token pair
# 2. Use access token for API calls
# 3. Refresh tokens
# 4. Test token rotation
# 5. Logout and verify revocation
```

## ⚙️ Configuration

### Environment Variables

```bash
# JWT Settings
JWT_SECRET_KEY=your-super-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
```

### Security Recommendations

1. **Secret Key**: Use a strong, random secret key (at least 32 characters)
2. **HTTPS**: Always use HTTPS in production
3. **Storage**: Store refresh tokens in httpOnly cookies for web apps
4. **Rotation**: Implement automatic token rotation
5. **Monitoring**: Log authentication events for security monitoring
6. **Cleanup**: Run periodic cleanup of expired tokens

## 🚨 Error Handling

### Common Error Responses

#### 401 Unauthorized
```json
{
  "detail": "Invalid or expired refresh token"
}
```

#### 400 Bad Request
```json
{
  "detail": "Invalid request format"
}
```

#### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "refresh_token"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## 🔧 Maintenance

### Database Cleanup

The system automatically cleans up expired tokens, but you can also run manual cleanup:

```python
from app.core.auth import cleanup_expired_tokens
from app.database.connection import get_db

async def cleanup():
    async with get_db() as db:
        count = await cleanup_expired_tokens(db)
        print(f"Cleaned up {count} expired tokens")
```

### Monitoring

Key metrics to monitor:

- Token refresh rate
- Failed authentication attempts
- Active refresh tokens per user
- Token expiration patterns

## 📚 Further Reading

- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [OAuth 2.0 Security Best Current Practice](https://tools.ietf.org/html/draft-ietf-oauth-security-topics)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
