#!/usr/bin/env python3
"""
Security audit script for the Event Analytics API.
Checks for hardcoded secrets and configuration issues.
"""

import os
import re
import sys
from pathlib import Path

def check_hardcoded_secrets():
    """Check for hardcoded secrets in Python files."""
    print("🔍 Checking for hardcoded secrets...")
    
    # Patterns that might indicate hardcoded secrets
    secret_patterns = [
        r'password\s*=\s*["\'][^"\']*["\']',
        r'secret\s*=\s*["\'][^"\']*["\']',
        r'key\s*=\s*["\'][^"\']*["\']',
        r'postgresql://[^:]+:[^@]+@',
        r'postgres://[^:]+:[^@]+@',
    ]
    
    issues = []
    python_files = Path('.').rglob('*.py')
    
    for file_path in python_files:
        # Skip virtual environments and migrations
        if any(part in str(file_path) for part in ['.venv', 'venv', 'env', '__pycache__']):
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            for line_num, line in enumerate(content.split('\n'), 1):
                # Skip comments and safe patterns
                if line.strip().startswith('#'):
                    continue
                if 'your_secure_password' in line or 'your_password_here' in line:
                    continue
                if 'Field(...' in line:  # Pydantic required fields
                    continue
                    
                for pattern in secret_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        # Skip regex patterns in security script itself
                        if 'security_audit.py' in str(file_path) and line.strip().startswith('r\''):
                            continue
                        # Skip template URLs in tests that use variables
                        if 'f"postgresql://' in line and '{' in line:
                            continue
                        issues.append(f"{file_path}:{line_num}: {line.strip()}")
                        
        except Exception as e:
            print(f"Warning: Could not read {file_path}: {e}")
    
    if issues:
        print("❌ Found potential hardcoded secrets:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("✅ No hardcoded secrets found")
        return True

def check_env_file():
    """Check .env file configuration."""
    print("\n🔍 Checking .env file...")
    
    if not os.path.exists('.env'):
        print("❌ .env file not found! Copy from .env.example")
        return False
    
    # Check for default passwords
    with open('.env', 'r') as f:
        env_content = f.read()
    
    dangerous_defaults = [
        'changeme',
        '123456',
        'admin',
        'root',
        'qwerty'
    ]
    
    issues = []
    for line_num, line in enumerate(env_content.split('\n'), 1):
        if '=' in line and not line.strip().startswith('#'):
            key, value = line.split('=', 1)
            if 'PASSWORD' in key.upper():
                for default in dangerous_defaults:
                    if default.lower() in value.lower():
                        issues.append(f"Line {line_num}: Using default/weak password")
    
    if issues:
        print("⚠️  Found potential security issues in .env:")
        for issue in issues:
            print(f"  - {issue}")
        print("  Please use strong, unique passwords!")
        return False
    else:
        print("✅ .env file looks secure")
        return True

def check_gitignore():
    """Check if .env is in .gitignore."""
    print("\n🔍 Checking .gitignore...")
    
    if not os.path.exists('.gitignore'):
        print("❌ .gitignore file not found!")
        return False
    
    with open('.gitignore', 'r') as f:
        gitignore_content = f.read()
    
    if '.env' in gitignore_content:
        print("✅ .env is properly ignored by git")
        return True
    else:
        print("❌ .env is NOT in .gitignore! This is dangerous!")
        return False

def check_config_loading():
    """Check if configuration loads properly."""
    print("\n🔍 Testing configuration loading...")
    
    try:
        sys.path.insert(0, '.')
        from app.core.config import settings
        
        # Test that required fields are loaded
        required_fields = ['POSTGRES_USER', 'POSTGRES_PASSWORD', 'POSTGRES_DB', 'JWT_SECRET_KEY']
        
        for field in required_fields:
            value = getattr(settings, field, None)
            if not value:
                print(f"❌ Required field {field} is not set")
                return False
                
        # Check JWT secret key strength
        jwt_key = getattr(settings, 'JWT_SECRET_KEY', '')
        if len(jwt_key) < 32:
            print("❌ JWT_SECRET_KEY should be at least 32 characters long")
            return False
        
        print("✅ Configuration loads successfully")
        print(f"  - Database: {settings.POSTGRES_DB}")
        print(f"  - Host: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}")
        print(f"  - User: {settings.POSTGRES_USER}")
        return True
        
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        return False

def main():
    """Run security audit."""
    print("🔐 Event Analytics API - Security Audit")
    print("=" * 50)
    
    checks = [
        check_hardcoded_secrets,
        check_env_file,
        check_gitignore,
        check_config_loading
    ]
    
    results = []
    for check in checks:
        results.append(check())
    
    print("\n" + "=" * 50)
    if all(results):
        print("🎉 Security audit PASSED!")
        print("Your configuration is secure.")
        sys.exit(0)
    else:
        print("⚠️  Security audit FAILED!")
        print("Please fix the issues above before deploying.")
        sys.exit(1)


if __name__ == "__main__":
    main()
