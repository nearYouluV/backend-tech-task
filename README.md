# Event Analytics API

Високопродуктивний сервіс для збору подій (events) та аналітики на базі FastAPI з PostgreSQL.

## 🚀 Особливості

- **Швидкий збір подій**: Високопродуктивна обробка подій з масовими операціями
- **Аналітика в реальному часі**: Отримання аналітики з ваших даних
- **Валідація даних**: Комплексна валідація з використанням Pydantic
- **Чиста архітектура**: Багаторівнева архітектура з розділенням відповідальності
- **Автодокументація**: Інтерактивні API документи з Swagger UI
- **Docker готовий**: Повна контейнеризація з Docker Compose
- **Моніторинг**: Структуроване логування та health checks

## 🏗️ Архітектура

```
app/
├── api/v1/            # API ендпоінти
├── core/              # Основні налаштування
├── models/            # Моделі даних та БД
├── services/          # Бізнес-логіка
└── tests/             # Тести
```

## 🚀 Швидкий старт

### Docker (Рекомендовано)

```bash
# 1. Запустити всі сервіси
docker compose up -d

# 2. API доступне за адресою:
# - API: http://localhost:8000
# - Документація: http://localhost:8000/docs
# - PostgreSQL: localhost:5433
# - Redis: localhost:6379
```

### Локальна розробка

```bash
# 1. Встановити залежності
pip install -r requirements.txt

# 2. Налаштувати змінні оточення
cp .env.example .env

# 3. Запустити міграції
alembic upgrade head

# 4. Запустити сервер
uvicorn app.main:app --reload
```

## 📖 Використання API

### Додавання подій

```bash
curl -X POST "http://localhost:8000/api/v1/events" 
  -H "Content-Type: application/json" 
  -d '{
    "events": [
      {
        "event_id": "550e8400-e29b-41d4-a716-446655440000",
        "user_id": 123,
        "event_type": "user_login",
        "occurred_at": "2025-01-13T10:30:00",
        "properties": {
          "browser": "Chrome",
          "ip": "192.168.1.1"
        }
      }
    ]
  }'
```

### Отримання подій

```bash
# Всі події
curl "http://localhost:8000/api/v1/events"

# Фільтрація по користувачу
curl "http://localhost:8000/api/v1/events?user_id=123"

# Фільтрація по типу події
curl "http://localhost:8000/api/v1/events?event_type=user_login"

# Пагінація
curl "http://localhost:8000/api/v1/events?limit=10&offset=20"
```

## 🧪 Тестування

```bash
# Запустити всі тести
pytest

# З покриттям коду
pytest --cov=app tests/

# Конкретний тестовий файл
pytest tests/test_events.py -v
```

## 🔧 Розробка

### Міграції БД

```bash
# Створити нову міграцію
alembic revision --autogenerate -m "Description"

# Застосувати міграції
alembic upgrade head
```

### Якість коду

```bash
# Лінтинг
flake8 app/

# Форматування
black app/
```

##  Моніторинг

- **Health Check**: `GET /health`
- **Документація**: `/docs` та `/redoc`
- **Структуровані логи**: JSON формат
