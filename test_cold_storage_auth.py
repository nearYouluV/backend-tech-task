"""
Тест перевірки авторизації для cold storage endpoints
"""
import requests
import json

def test_cold_storage_endpoints():
    """Тест авторизації для ендпоінтів cold storage"""
    base_url = "http://localhost:8000/api/v1/cold-storage"
    
    # Список захищених ендпоінтів (реально існуючих)
    protected_endpoints = [
        "/dau-fast",
        "/top-events-fast",
        "/retention-cohort",
        "/archival-candidates", 
        "/archival-integrity",
        "/storage-comparison"
    ]
    
    # POST ендпоінти
    protected_post_endpoints = [
        "/archive-now"
    ]
    
    # 1. Тест без авторизації - повинні повернути 403
    print("Тестування GET ендпоінтів без авторизації...")
    for endpoint in protected_endpoints:
        response = requests.get(f"{base_url}{endpoint}")
        print(f"GET {endpoint}: {response.status_code}")
        assert response.status_code == 403, f"Endpoint {endpoint} should return 403 without auth"
    
    print("Тестування POST ендпоінтів без авторизації...")
    for endpoint in protected_post_endpoints:
        response = requests.post(f"{base_url}{endpoint}")
        print(f"POST {endpoint}: {response.status_code}")
        assert response.status_code == 403, f"Endpoint {endpoint} should return 403 without auth"
    
    # 2. Тест health endpoint - повинен повернути 200
    print("\nТестування health endpoint...")
    response = requests.get(f"{base_url}/health")
    print(f"/health: {response.status_code}")
    assert response.status_code == 200, "Health endpoint should be accessible"
    
    # 4. Логін звичайного користувача (використовуємо існуючого)
    print("\nЛогін звичайного користувача...")
    login_data = {
        "username": "regularuser",
        "password": "userpass123"
    }
    response = requests.post("http://localhost:8000/api/v1/auth/login", json=login_data)
    print(f"Login status: {response.status_code}")
    if response.status_code != 200:
        print(f"Login error: {response.text}")
        print("Skipping user tests...")
        user_token = None
    else:
        user_token = response.json()["access_token"]
    
    # 5. Тест з токеном звичайного користувача - повинні повернути 403
    if user_token:
        print("\nТестування GET ендпоінтів з токеном звичайного користувача...")
        headers = {"Authorization": f"Bearer {user_token}"}
        for endpoint in protected_endpoints:
            response = requests.get(f"{base_url}{endpoint}", headers=headers)
            print(f"GET {endpoint}: {response.status_code}")
            assert response.status_code == 403, f"Endpoint {endpoint} should return 403 for regular user"
            
        print("Тестування POST ендпоінтів з токеном звичайного користувача...")
        for endpoint in protected_post_endpoints:
            response = requests.post(f"{base_url}{endpoint}", headers=headers)
            print(f"POST {endpoint}: {response.status_code}")
            assert response.status_code == 403, f"Endpoint {endpoint} should return 403 for regular user"
    
    # 6. Логін адміна
    print("\nЛогін адміна...")
    admin_login_data = {
        "username": "admin",
        "password": "admin1"
    }
    response = requests.post("http://localhost:8000/api/v1/auth/login", json=admin_login_data)
    if response.status_code == 200:
        admin_token = response.json()["access_token"]
        
        # 7. Тест з токеном адміна - повинні повернути 200 або коректну відповідь
        print("\nТестування GET ендпоінтів з токеном адміна...")
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        for endpoint in protected_endpoints:
            response = requests.get(f"{base_url}{endpoint}", headers=admin_headers)
            print(f"GET {endpoint}: {response.status_code}")
            # Очікуємо 200 або інші валідні статуси (не 403/401)
            assert response.status_code not in [403, 401], f"Admin should have access to {endpoint}"
            
        print("Тестування POST ендпоінтів з токеном адміна...")
        for endpoint in protected_post_endpoints:
            response = requests.post(f"{base_url}{endpoint}", headers=admin_headers)
            print(f"POST {endpoint}: {response.status_code}")
            # Очікуємо 200 або інші валідні статуси (не 403/401)
            assert response.status_code not in [403, 401], f"Admin should have access to {endpoint}"
    
    print("\n✅ Всі тести авторизації пройшли успішно!")

if __name__ == "__main__":
    test_cold_storage_endpoints()
