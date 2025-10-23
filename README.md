# Event Analytics API

Високопродуктивний Event Analytics API з гарячим/холодним сховищем даних на базі PostgreSQL та ClickHouse.

## 🚀 Швидкий старт

### Як запустити

1. **Клонування репозиторію:**
   ```bash
   git clone <repository_url>
   cd backend-tech-task
   ```

2. **Автоматичний запуск усіх сервісів:**
   ```bash
   docker compose up -d
   ```
   
   Ця команда автоматично:
   - Запустить PostgreSQL та ClickHouse
   - Дочекається готовності всіх сервісів
   - Ініціалізує структуру баз даних
   - Створить адміністратора з логіном `admin` та паролем `admin1`
   - Запустить API сервер

3. **Перевірка роботи:**
   ```bash
   curl http://localhost:8000/health
   ```

API буде доступний за адресою: http://localhost:8000

### Дані адміністратора

Система автоматично створює адміністратора:
- **Логін**: `admin`
- **Пароль**: `admin1`
- **Роль**: `admin` (має доступ до всіх ендпоінтів, включаючи ClickHouse аналітику)

### Авторизація адміністратора

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"admin1"}'
```



### Бенчмарк продуктивності

```bash
# Запуск бенчмарку
python benchmark_fixed.py
```

### Ручне тестування

1. **Створення користувача:**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/auth/signup" \
        -H "Content-Type: application/json" \
        -d '{"username":"testuser","email":"test@example.com","password":"testpass123"}'
   ```

2. **Авторизація:**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"username":"testuser","password":"testpass123"}'
   ```

3. **Відправка подій:**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/events" \
        -H "Authorization: Bearer YOUR_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"events":[{"event_id":"12345","user_id":"user1","event_type":"login","occurred_at":"2023-12-01T10:00:00Z","properties":{"session_id":"abc123"}}]}'
   ```

## 📊 Результати вимірювань

### Продуктивність інгестії даних

| Обсяг подій | Пропускна здатність | Час обробки |
|------------|--------------------|-----------:|
| 100 подій  | 1,328 подій/сек    | 0.08 сек   |
| 1,000 подій| 1,840 подій/сек    | 0.54 сек   |
| 5,000 подій| 1,812 подій/сек    | 2.76 сек   |
| 10,000 подій| 1,782 подій/сек   | 5.61 сек   |

**Ключові показники:**
- 🚀 **Пік продуктивності**: 1,840 подій/сек
- 📊 **Середня продуктивність**: 1,691 подій/сек
- 📈 **Загалом протестовано**: 16,100 подій
- ✅ **Успішність**: 100% (4/4 тести)

### Продуктивність аналітики

| Запит | Середній час відповіді |
|-------|----------------------:|
| Health Check | 2-3 мс |
| API Health | 1 мс |
| Cold Storage Health | 6-7 мс |
| Events Health | 1 мс |

### Архітектура сховища

- **Гаряче сховище (PostgreSQL)**: Зберігання останніх 7 днів для швидкого доступу
- **Холодне сховище (ClickHouse)**: Довгострокове зберігання з матеріалізованими представленнями для аналітики
- **Автоматичне архівування**: Перенесення старих даних з гарячого в холодне сховище

## 🏗 Архітектура

### Компоненти системи

1. **FastAPI Application**: HTTP API сервер
2. **PostgreSQL**: Гаряче сховище реляційних даних
3. **ClickHouse**: Холодне сховище для аналітики
4. **Docker Compose**: Оркестрація контейнерів

### Схема даних

#### Гаряче сховище (PostgreSQL)
- `users` - Користувачі системи
- `events` - Події останніх 7 днів
- `refresh_tokens` - JWT токени

#### Холодне сховище (ClickHouse)
- `events_archive` - Архівні події
- `daily_active_users_mv` - Матеріалізоване представлення DAU
- `event_counts_mv` - Матеріалізоване представлення підрахунків подій

### API Endpoints

#### Загальнодоступні

- `POST /api/v1/events` - Інгестія подій (до 1000 за запит)
- `GET /api/v1/stats/dau` - Денно активні користувачі
- `GET /api/v1/stats/top-events` - Топ подій
- `GET /api/v1/stats/retention` - Аналіз утримання

#### Тільки для адміністраторів

- `GET /api/v1/cold-storage/*` - Аналітика холодного сховища (ClickHouse)
  - `GET /api/v1/cold-storage/events` - Архівні події
  - `GET /api/v1/cold-storage/dau` - DAU за період
  - `GET /api/v1/cold-storage/top-events` - Топ подій за період
  - `GET /api/v1/cold-storage/retention` - Аналіз утримання користувачів
  - `GET /api/v1/cold-storage/health` - Статус ClickHouse

## 🔧 Налаштування

### Змінні середовища

Основні налаштування в `.env`:

```env
# Database
POSTGRES_DB=events
POSTGRES_USER=events_user
POSTGRES_PASSWORD=events_password

# JWT
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production-min-32-chars

# ClickHouse
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=8123
CLICKHOUSE_DB=events_analytics
```

### Налаштування продуктивності

- **Batch розмір**: максимум 1000 подій за запит
- **Rate limiting**: 1000 запитів на хвилину
- **Connection pooling**: 20 з'єднань до PostgreSQL
- **ClickHouse**: HTTP інтерфейс для оптимальної продуктивності

## 📈 Висновки

### Переваги архітектури

1. **Висока пропускна здатність**: Досягнуто 1,840 подій/сек при стабільній роботі
2. **Масштабованість**: Розподіл навантаження між гарячим і холодним сховищем
3. **Швидка аналітика**: ClickHouse забезпечує швидкі аналітичні запити
4. **Надійність**: Ідемпотентність, валідація даних, обробка помилок

### Оптимізації

1. **Батчінг**: Автоматичне розбиття великих запитів на батчі по 1000 подій
2. **Матеріалізовані представлення**: Попередньо агреговані дані в ClickHouse
3. **Асинхронна обробка**: Використання async/await для всіх I/O операцій
4. **Валідація даних**: Pydantic схеми для перевірки вхідних даних

### Можливості розвитку

1. **Горизонтальне масштабування**: Шардінг ClickHouse для обробки терабайтів даних
2. **Кешування**: Redis для часто запитуваних метрик
3. **Stream processing**: Kafka для реал-тайм обробки подій
4. **Моніторинг**: Prometheus + Grafana для спостереження за системою

## 🛠 Розробка

### Структура проекту

```
.
├── app/                    # Основний код застосунку
│   ├── api/               # API endpoints
│   ├── core/              # Конфігурація та залежності
│   ├── models/            # Моделі даних та схеми
│   ├── services/          # Бізнес логіка
│   └── database/          # Робота з базами даних
├── tests/                 # Тести
├── scripts/               # Допоміжні скрипти
├── init-db/              # Ініціалізація баз даних
├── init-clickhouse/      # Ініціалізація ClickHouse
└── data/                 # Зразки даних
```

### Зависності

- **FastAPI**: Веб фреймворк
- **SQLAlchemy**: ORM для PostgreSQL
- **ClickHouse-connect**: Клієнт для ClickHouse
- **Pydantic**: Валідація даних
- **Pytest**: Тестування

Див. `requirements.txt` для повного списку залежностей.

---

**Версія**: 1.0.0  
**Автор**: Backend Tech Task  
**Ліцензія**: MIT
