# Event Analytics API

Високопродуктивний сервіс для збору подій (events) та аналітики на базі FastAPI з PostgreSQL та асинхронним обробкою.

## 🚀 Особливості

- **Асинхронна архітектура**: Повністю асинхронна обробка з AsyncIO та SQLAlchemy 2.0
- **Швидкий збір подій**: Високопродуктивна обробка подій з масовими операціями
- **JWT Аутентифікація**: Безпечна аутентифікація з Bearer токенами та role-based доступом
- **Безпека**: Захищені змінні оточення, аудит безпеки, захищені API endpoints
- **Валідація даних**: Комплексна валідація з використанням Pydantic
- **Чиста архітектура**: Багаторівнева архітектура з розділенням відповідальності
- **Автодокументація**: Інтерактивні API документи з Swagger UI
- **Production-ready**: Повна контейнеризація з Docker Compose, health checks
- **Моніторинг**: Структуроване логування, Redis кешування

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


### 🐳 Docker Compose

```bash
# Розробка
make docker-dev

# Продакшн
make docker-prod

# Переглянути статус
make docker-status

# Переглянути логи
make docker-logs

# Зупинити сервіси
make docker-down
```

### 📋 Ручне налаштування

1. **Налаштування змінних оточення:**
   ```bash
   cp .env.example .env
   ```

2. **Запуск Docker:**
   ```bash
   docker compose up -d
   ```

3. **API доступне за адресою:**
   - 🚀 API: http://localhost:8000
   - 📚 Документація: http://localhost:8000/docs  
   - 🐘 PostgreSQL: localhost:5433
   - 🔴 Redis: localhost:6379

### ⚡ Локальна розробка

```bash
# 1. Створити віртуальне середовище
python3 -m venv venv
source venv/bin/activate

# 2. Встановити залежності
pip install -r requirements.txt

# 3. Налаштувати змінні оточення
cp .env.example .env

# 4. Запустити міграції
alembic upgrade head

# 5. Запустити сервер
make run
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

## ⚙️ Конфігурація змінних оточення

### 🔐 Конфігурація та безпека

Основні змінні оточення:

```bash
# База даних PostgreSQL (ОБОВ'ЯЗКОВІ)
POSTGRES_USER=your_db_username
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=events
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# JWT Authentication (REQUIRED FOR SECURITY)
JWT_SECRET_KEY=generate-a-secure-random-key-at-least-32-characters-long
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Налаштування додатку
DEBUG=false
LOG_LEVEL=INFO
RATE_LIMIT_PER_MINUTE=1000

# Порти для Docker
POSTGRES_EXTERNAL_PORT=5433
APP_EXTERNAL_PORT=8000
```

⚠️ **Ніколи не коммітьте .env файл в git!** Він уже додано в .gitignore.

### 🔐 JWT Аутентифікація

API використовує JWT токени для захисту endpoints:

```bash
# Створити адміністратора
make create-admin

# Демо аутентифікації (запустіть сервер спочатку)
make jwt-demo

# Ручний тест
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your_password"}'
```

**Захищені endpoints:**
- `POST /api/v1/events` - створення подій
- `GET /api/v1/events` - отримання подій  


## 🧪 Тестування

```bash
# Автоматичний запуск тестів
./deploy.sh test

# Ручний запуск
make test

# З покриттям коду
make test-coverage

# Docker тести
make docker-test

# Конкретний тестовий файл
pytest tests/test_events.py -v
```

## 🔧 Розробка

### Команди Makefile

```bash
make run              # Запустити додаток локально
make test            # Запустити тести
make test-coverage   # Тести з покриттям
make lint            # Перевірка коду
make format          # Форматування коду
make docker-dev      # Docker розробка
make docker-prod     # Docker продакшн
make docker-shell    # Доступ до контейнера
make docker-db-shell # Доступ до БД
```


### Якість коду

```bash
# Лінтинг
make lint

# Форматування
make format

# Перевірка типів
make type-check
```

## 🔒 Безпека

- **Змінні оточення**: Всі чутливі дані в `.env` файлах
- **Docker security**: Ізольовані мережі та обмежені привілеї
- **Health checks**: Моніторинг стану сервісів
- **Production ready**: Оптимізація для продакшн середовища

## 📊 Моніторинг

- **Health Check**: `GET /health`
- **Документація**: `/docs` та `/redoc`
- **Структуровані логи**: JSON формат з рівнями
- **Метрики**: Redis кешування та PostgreSQL оптимізації
- **Service Discovery**: Docker health checks
