# JWT Authentication Documentation

Event Analytics API використовує JWT (JSON Web Tokens) для аутентифікації та авторизації.

## 🔐 Огляд безпеки

### Аутентифікація
- **JWT Tokens**: Bearer токени з підписом HMAC-SHA256
- **Expiration**: Токени діють 30 хвилин
- **Required**: Всі API endpoints вимагають аутентифікації (крім /docs, /health, /auth/*)

### Авторизація  
- **Admin Users**: Можуть створювати нових користувачів
- **Regular Users**: Можуть тільки створювати події та переглядати дані
- **Role-based**: Перевірка ролей на рівні endpoints

## 🚀 Швидкий старт

### 1. Створення адміністратора
```bash
make create-admin
# або
python scripts/create_admin.py
```

### 2. Запуск API сервера
```bash
uvicorn app.main:app --reload
# або  
make run
```

### 3. Демо аутентифікації
```bash
make jwt-demo
# або
python scripts/jwt_demo.py
```

## 📡 API Endpoints

### Аутентифікація

#### POST /api/v1/auth/signup
Публічна реєстрація нового користувача.

**Request:**
```json
{
  "username": "newuser",
  "email": "user@example.com",
  "password": "securepass123",
  "is_admin": false
}
```

**Response:**
```json
{
  "id": "uuid",
  "username": "newuser",
  "email": "user@example.com",
  "is_admin": false,
  "is_active": true,
  "created_at": "2025-01-01T12:00:00Z",
  "updated_at": "2025-01-01T12:00:00Z"
}
```

#### POST /api/v1/auth/login
Вхід користувача та отримання JWT токена.

**Request:**
```json
{
  "username": "admin", 
  "password": "admin123"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "abc123xyz789secure456refresh789token...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "uuid",
    "username": "admin",
    "email": "admin@example.com", 
    "is_admin": true,
    "is_active": true
  }
}
```

⚠️ **УВАГА**: Тепер логін повертає пару токенів (access + refresh). Refresh токен використовується для оновлення access токенів.

#### GET /api/v1/auth/me
Отримання інформації про поточного користувача.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "id": "uuid",
  "username": "admin", 
  "email": "admin@example.com",
  "is_admin": true,
  "is_active": true,
  "created_at": "2025-01-01T12:00:00Z"
}
```

#### POST /api/v1/auth/refresh
Оновлення токенів за допомогою refresh токена.

**Request:**
```json
{
  "refresh_token": "abc123xyz789secure456refresh789token..."
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJh...",
  "refresh_token": "new789refresh456token123...",
  "token_type": "bearer", 
  "expires_in": 1800,
  "user": {
    "id": "uuid",
    "username": "admin",
    "email": "admin@example.com",
    "is_admin": true,
    "is_active": true
  }
}
```

#### POST /api/v1/auth/logout
Вихід із системи (відкликання refresh токена).

**Request:**
```json
{
  "refresh_token": "abc123xyz789secure456refresh789token..."
}
```

**Response:**
```json
{
  "message": "Successfully logged out",
  "revoked": true
}
```

#### POST /api/v1/auth/logout-all
Вихід із всіх пристроїв (відкликання всіх refresh токенів користувача).

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "message": "Successfully logged out from 3 device(s)",
  "revoked_tokens": 3
}
```

#### POST /api/v1/auth/register (Admin only)
Створення нового користувача (тільки адміністратори).

**Headers:**
```
Authorization: Bearer <admin_jwt_token>
```

**Request:**
```json
{
  "username": "newuser",
  "email": "user@example.com", 
  "password": "securepass123",
  "is_admin": false
}
```

### Захищені endpoints

Всі endpoints для подій вимагають аутентифікації:

#### POST /api/v1/events
**Headers:**
```
Authorization: Bearer <jwt_token>
```

#### GET /api/v1/events  
**Headers:**
```
Authorization: Bearer <jwt_token>
```

## 🔧 Конфігурація

У `.env` файлі:

```bash
# JWT Authentication (REQUIRED)
JWT_SECRET_KEY=your-super-secret-key-at-least-32-characters-long
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

⚠️ **ВАЖЛИВО**: Використовуйте сильний, унікальний JWT_SECRET_KEY в продакшені!

## 🧪 Тестування

### Curl приклади

1. **Логін:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

2. **Створення події:**
```bash
# Спочатку отримайте токен від логіну, потім:
curl -X POST "http://localhost:8000/api/v1/events" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "events": [{
      "event_id": "123e4567-e89b-12d3-a456-426614174000",
      "occurred_at": "2025-01-01T12:00:00Z", 
      "user_id": 1,
      "event_type": "purchase",
      "properties": {"amount": 99.99}
    }]
  }'
```

### Python приклади

```python
import requests

# Логін
response = requests.post("http://localhost:8000/api/v1/auth/login", 
    json={"username": "admin", "password": "admin123"})
token = response.json()["access_token"]

# Створення події
headers = {"Authorization": f"Bearer {token}"}
response = requests.post("http://localhost:8000/api/v1/events",
    json={
        "events": [{
            "event_id": "123e4567-e89b-12d3-a456-426614174000",
            "occurred_at": "2025-01-01T12:00:00Z",
            "user_id": 1, 
            "event_type": "purchase",
            "properties": {"amount": 99.99}
        }]
    },
    headers=headers)
```

## 🔒 Безпека

### Найкращі практики
- ✅ Використовуйте HTTPS в продакшені
- ✅ Ротуйте JWT_SECRET_KEY регулярно  
- ✅ Встановіте короткий час життя токенів
- ✅ Зберігайте токени безпечно (не в localStorage)
- ✅ Логуйте спроби аутентифікації

### Што НЕ робити
- ❌ Не зберігайте JWT_SECRET_KEY в коді
- ❌ Не використовуйте слабкі паролі
- ❌ Не передавайте токени в URL
- ❌ Не довіряйте user input без валідації

## 📊 Моніторинг

API автоматично логує:
- Спроби логіну (успішні/неуспішні)
- Використання недійсних токенів
- Спроби доступу без аутентифікації
- Створення/оновлення користувачів

Перевіряйте логи для виявлення підозрілої активності.

## 🆘 Troubleshooting

### "Could not validate credentials"
- Перевірте, що токен не прострочений
- Переконайтеся, що JWT_SECRET_KEY правильний
- Перевірте формат Authorization header

### "Not enough permissions"
- Користувач не має потрібних прав (admin)
- Перевірте is_admin flag у базі даних

### "User not found" 
- Користувач не існує або неактивний
- Перевірте is_active flag у базі даних
