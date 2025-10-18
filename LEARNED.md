# Досвід розробки

## Що нового вивчив

### Structlog для логування
**Що це:** Бібліотека для структурованого логування в Python  
**Навіщо:** Замість звичайних текстових логів використовується JSON формат

**Приклад використання:**
```python
import structlog

logger = structlog.get_logger(__name__)

logger.info(
    "Event created", 
    event_id=str(event.id),
    user_id=event.user_id,
    event_type=event.event_type
)
```

**Переваги:**
- Логи легко парсити автоматично
- Можна додавати довільні поля
- Готовість до ELK stack або інших log aggregation систем
- Легко фільтрувати та шукати по структурованих даних

**Результат в логах:**
```json
{
  "event": "Event created",
  "event_id": "123e4567-e89b-12d3-a456-426614174000", 
  "user_id": 1,
  "event_type": "view_item",
  "logger": "app.services.event_service",
  "level": "info",
  "timestamp": "2025-10-18T14:42:03.653218Z"
}
```

## Корисні insights

1. **PostgreSQL + JSON** - ідеальне поєднання для event-driven систем
2. **FastAPI автодокументація** - економить багато часу на написання документації
3. **Pydantic валідація** - ловить помилки на етапі розробки, а не в продакшені
4. **Layered архітектура** - спрощує тестування та підтримку коду

## Що б зробив по-іншому

- Відразу б налаштував async PostgreSQL з asyncpg
- Додав би більше індексів для аналітичних запитів  
- Використав би Alembic для міграцій БД
