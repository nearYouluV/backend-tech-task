# API Examples / Приклади API

## 🚀 Швидкий тест API

### 1. Перевірка роботи API

```bash
# Отримати всі події
curl -s "http://localhost:8000/api/v1/events" | jq
```

### 2. Додавання нової події

```bash
curl -X POST "http://localhost:8000/api/v1/events" \
  -H "Content-Type: application/json" \
  -d '{
    "events": [
      {
        "event_id": "550e8400-e29b-41d4-a716-446655440000",
        "user_id": 123,
        "event_type": "user_login",
        "occurred_at": "2025-01-13T10:30:00",
        "properties": {
          "browser": "Chrome",
          "ip": "192.168.1.1",
          "location": "Kyiv"
        }
      }
    ]
  }' | jq
```

### 3. Масове додавання подій

```bash
curl -X POST "http://localhost:8000/api/v1/events" \
  -H "Content-Type: application/json" \
  -d '{
    "events": [
      {
        "event_id": "550e8400-e29b-41d4-a716-446655440001",
        "user_id": 123,
        "event_type": "page_view",
        "occurred_at": "2025-01-13T10:31:00",
        "properties": {
          "page": "/dashboard",
          "referrer": "google.com"
        }
      },
      {
        "event_id": "550e8400-e29b-41d4-a716-446655440002",
        "user_id": 124,
        "event_type": "user_login",
        "occurred_at": "2025-01-13T10:32:00",
        "properties": {
          "browser": "Firefox",
          "ip": "192.168.1.2"
        }
      }
    ]
  }' | jq
```

## 🔍 Фільтрація подій

### По користувачу

```bash
curl -s "http://localhost:8000/api/v1/events?user_id=123" | jq
```

### По типу події

```bash
curl -s "http://localhost:8000/api/v1/events?event_type=user_login" | jq
```

### По діапазону дат

```bash
curl -s "http://localhost:8000/api/v1/events?start_date=2025-01-13T00:00:00&end_date=2025-01-13T23:59:59" | jq
```

### Комбінована фільтрація

```bash
curl -s "http://localhost:8000/api/v1/events?user_id=123&event_type=page_view&limit=5" | jq
```

## 📄 Пагінація

```bash
# Перші 10 подій
curl -s "http://localhost:8000/api/v1/events?limit=10&offset=0" | jq

# Наступні 10 подій
curl -s "http://localhost:8000/api/v1/events?limit=10&offset=10" | jq
```

## 🧪 Тестові дані

### Створення тестових подій різних типів

```bash
# E-commerce події
curl -X POST "http://localhost:8000/api/v1/events" \
  -H "Content-Type: application/json" \
  -d '{
    "events": [
      {
        "event_id": "550e8400-e29b-41d4-a716-446655440010",
        "user_id": 200,
        "event_type": "product_view",
        "occurred_at": "2025-01-13T11:00:00",
        "properties": {
          "product_id": "laptop-123",
          "category": "electronics",
          "price": 25000
        }
      },
      {
        "event_id": "550e8400-e29b-41d4-a716-446655440011",
        "user_id": 200,
        "event_type": "add_to_cart",
        "occurred_at": "2025-01-13T11:05:00",
        "properties": {
          "product_id": "laptop-123",
          "quantity": 1,
          "price": 25000
        }
      }
    ]
  }' | jq
```

### Аналітичні події

```bash
curl -X POST "http://localhost:8000/api/v1/events" \
  -H "Content-Type: application/json" \
  -d '{
    "events": [
      {
        "event_id": "550e8400-e29b-41d4-a716-446655440020",
        "user_id": 300,
        "event_type": "feature_usage",
        "occurred_at": "2025-01-13T12:00:00",
        "properties": {
          "feature": "advanced_search",
          "duration_seconds": 45,
          "success": true
        }
      }
    ]
  }' | jq
```

## 📊 Корисні запити

### Підрахунок подій по типах

```bash
# Отримати події та порахувати вручну
curl -s "http://localhost:8000/api/v1/events" | jq '.events | group_by(.event_type) | map({event_type: .[0].event_type, count: length})'
```

### Останні 5 подій

```bash
curl -s "http://localhost:8000/api/v1/events?limit=5" | jq '.events | sort_by(.created_at) | reverse'
```

### Перевірка дублікатів

```bash
# Спроба додати існуючу подію
curl -X POST "http://localhost:8000/api/v1/events" \
  -H "Content-Type: application/json" \
  -d '{
    "events": [
      {
        "event_id": "550e8400-e29b-41d4-a716-446655440000",
        "user_id": 123,
        "event_type": "duplicate_test",
        "occurred_at": "2025-01-13T10:30:00",
        "properties": {}
      }
    ]
  }' | jq
```

## 🔧 Налагодження

### Перевірка логів контейнера

```bash
docker compose logs app -f
```

### Перевірка підключення до БД

```bash
docker compose exec db psql -U postgres -d events -c "SELECT count(*) FROM events;"
```

### Перевірка Redis

```bash
docker compose exec redis redis-cli ping
```

## 📈 Моніторинг

### Статистика бази даних

```bash
docker compose exec db psql -U postgres -d events -c "
SELECT 
  event_type, 
  COUNT(*) as count,
  MIN(occurred_at) as first_event,
  MAX(occurred_at) as last_event
FROM events 
GROUP BY event_type 
ORDER BY count DESC;
"
```
