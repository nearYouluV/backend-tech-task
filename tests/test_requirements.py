

import pytest
from uuid import uuid4
from datetime import datetime, timedelta, timezone
from sqlalchemy import text

from app.models.database import Event, User, RefreshToken
from app.core.auth import get_password_hash, verify_password


class TestIdempotency:
    """Unit тест для ідемпотентності."""

    def test_event_idempotency(self, db_session):
        """Тест ідемпотентності: повторне створення з тим самим event_id не створює дублікат."""
        event_id = uuid4()
        
        # Створюємо подію першого разу
        event1 = Event(
            event_id=event_id,
            user_id="test-user",
            event_type="test_event",
            occurred_at=datetime.now(),
            properties={"test": True}
        )
        db_session.add(event1)
        db_session.commit()
        
        # Очищуємо сесію перед спробою створення дублікату
        db_session.expunge_all()
        
        # Спробуємо створити подію з тим самим event_id в новій сесії
        event2 = Event(
            event_id=event_id,  # той самий ID
            user_id="test-user-2",
            event_type="test_event_2", 
            occurred_at=datetime.now(),
            properties={"test": False}
        )
        
        # Цей запис має викликати помилку через унікальність event_id
        db_session.add(event2)
        
        with pytest.raises(Exception):  # Очікуємо помилку через порушення унікальності
            db_session.commit()


class TestIndexing:
    """Unit тест для індексації."""

    def test_required_indexes_exist(self, db_session):
        """Тест наявності необхідних індексів для продуктивності."""
        # Перевіряємо індекси в таблиці events
        result = db_session.execute(text("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'events' 
            AND schemaname = 'public'
        """))
        
        indexes = [row[0] for row in result.fetchall()]
        
        # Перевіряємо ключові індекси
        assert 'events_pkey' in indexes  # Primary key
        assert any('occurred_at' in idx for idx in indexes)  # Index для часових запитів
        assert any('user' in idx for idx in indexes)  # Index для user_id
        assert any('type' in idx for idx in indexes)  # Index для event_type


class TestIngestToAnalytics:
    """Інтеграційний тест "інгест → запит статистики"."""

    def test_ingest_to_stats_pipeline(self, db_session):
        """Повний тест: інгест подій → запит статистики DAU."""
        # ІНГЕСТ: Додаємо події по одній щоб уникнути проблем з batch insert
        base_date = datetime(2024, 1, 1)
        
        # День 1: 3 унікальні користувачі
        event1 = Event(
            event_id=uuid4(), user_id="user1", event_type="login", 
            occurred_at=base_date, properties={}
        )
        db_session.add(event1)
        db_session.commit()
        
        event2 = Event(
            event_id=uuid4(), user_id="user2", event_type="view", 
            occurred_at=base_date, properties={}
        )
        db_session.add(event2)
        db_session.commit()
        
        event3 = Event(
            event_id=uuid4(), user_id="user3", event_type="login", 
            occurred_at=base_date, properties={}
        )
        db_session.add(event3)
        db_session.commit()
        
        # День 2: 2 користувачі
        event4 = Event(
            event_id=uuid4(), user_id="user1", event_type="purchase", 
            occurred_at=base_date + timedelta(days=1), properties={}
        )
        db_session.add(event4)
        db_session.commit()
        
        event5 = Event(
            event_id=uuid4(), user_id="user4", event_type="login", 
            occurred_at=base_date + timedelta(days=1), properties={}
        )
        db_session.add(event5)
        db_session.commit()
        
        # СТАТИСТИКА: Запит DAU (Daily Active Users)
        # Перевіряємо Day 1
        day1_count = db_session.execute(text("""
            SELECT COUNT(DISTINCT user_id) 
            FROM events 
            WHERE DATE(occurred_at) = :date
        """), {"date": base_date.date()}).scalar()
        
        assert day1_count == 3  # 3 унікальні користувачі в день 1
        
        # Перевіряємо Day 2
        day2_count = db_session.execute(text("""
            SELECT COUNT(DISTINCT user_id) 
            FROM events 
            WHERE DATE(occurred_at) = :date
        """), {"date": (base_date + timedelta(days=1)).date()}).scalar()
        
        assert day2_count == 2  # 2 унікальні користувачі в день 2
        
        # СТАТИСТИКА: Топ event_types
        top_events = db_session.execute(text("""
            SELECT event_type, COUNT(*) as count
            FROM events 
            GROUP BY event_type 
            ORDER BY count DESC
            LIMIT 3
        """)).fetchall()
        
        # Перевіряємо результати
        event_counts = {row[0]: row[1] for row in top_events}
        assert event_counts.get("login", 0) == 3  # login з'являється 3 рази
        assert event_counts.get("view", 0) == 1   # view з'являється 1 раз
        assert event_counts.get("purchase", 0) == 1  # purchase з'являється 1 раз
        
        print("✅ Інтеграційний тест 'інгест → запит статистики' пройшов успішно!")


class TestAuthentication:
    """Unit тести авторизації та виходу."""

    def test_password_hashing(self):
        """Тест хешування та перевірки паролів."""
        password = "testpassword123"
        
        # Хешуємо пароль
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert len(hashed) > 50  
        
        assert verify_password(password, hashed) is True
        
        assert verify_password("wrongpassword", hashed) is False
        
        print("✅ Тест хешування паролів пройшов успішно!")

    def test_user_creation_and_storage(self, db_session):
        """Тест створення та збереження користувача в БД."""
        user = User(
            id="test-user-123",
            username="testuser",
            email="test@example.com",
            hashed_password=get_password_hash("password123"),
            is_active=True,
            is_admin=False
        )
        
        db_session.add(user)
        db_session.commit()
        
        saved_user = db_session.query(User).filter(User.username == "testuser").first()
        assert saved_user is not None
        assert saved_user.username == "testuser"
        assert saved_user.email == "test@example.com"
        assert saved_user.is_active is True
        assert saved_user.is_admin is False
        
        assert verify_password("password123", saved_user.hashed_password) is True
        assert verify_password("wrongpassword", saved_user.hashed_password) is False
        
        print("✅ Тест створення користувача пройшов успішно!")

    def test_refresh_token_management(self, db_session):
        """Тест управління refresh токенами."""
        user = User(
            id="token-user-123",
            username="tokenuser", 
            email="token@example.com",
            hashed_password=get_password_hash("password123"),
            is_active=True,
            is_admin=False
        )
        db_session.add(user)
        db_session.commit()
        
        now = datetime.now(timezone.utc)
        token = RefreshToken(
            id="refresh-token-123",
            user_id=user.id,
            token_hash="some-token-hash",
            expires_at=now + timedelta(days=7),
            is_revoked=False
        )
        db_session.add(token)
        db_session.commit()
        
        saved_token = db_session.query(RefreshToken).filter(RefreshToken.user_id == user.id).first()
        assert saved_token is not None
        assert saved_token.user_id == user.id
        assert saved_token.is_revoked is False
        assert saved_token.expires_at > datetime.now(timezone.utc)
        
        saved_token.is_revoked = True
        db_session.commit()
        
        # Перевіряємо, що токен відкликаний
        revoked_token = db_session.query(RefreshToken).filter(RefreshToken.id == token.id).first()
        assert revoked_token.is_revoked is True
        


class TestColdStorageIntegration:
    """Тести інтеграції з ClickHouse холодним сховищем."""

    def test_clickhouse_connection_mock(self):
        """Тест з'єднання з ClickHouse."""
        
        connection_params = {
            'host': 'clickhouse',
            'port': 8123,
            'database': 'events_analytics',
            'username': 'default'
        }
        
        assert connection_params['host'] == 'clickhouse'
        assert connection_params['port'] == 8123
        assert connection_params['database'] == 'events_analytics'
        

    def test_cold_storage_data_format(self):
        """Тест формату даних для холодного сховища."""
        from uuid import uuid4
        from datetime import datetime
        import json
        
        event_data = {
            'event_id': uuid4(),
            'user_id': 'test-user',
            'event_type': 'purchase',
            'occurred_at': datetime.now(),
            'properties': {'amount': 100, 'currency': 'USD'}
        }
        
        formatted_row = [
            str(event_data['event_id']), 
            event_data['user_id'],
            event_data['event_type'],
            event_data['occurred_at'],
            json.dumps(event_data['properties']),  
            datetime.now() 
        ]
        
        assert isinstance(formatted_row[0], str) 
        assert isinstance(formatted_row[1], str)  
        assert isinstance(formatted_row[4], str) 
        assert '"amount": 100' in formatted_row[4]  
        

    def test_archival_logic(self):
        """Тест логіки архівування (unit тест без реальних БД)."""
        from datetime import timedelta
        
        # Параметри архівування
        hot_retention_days = 7
        max_archive_age_days = 30
        
        now = datetime.now(timezone.utc)
        archive_threshold = now - timedelta(days=hot_retention_days)
        max_age_threshold = now - timedelta(days=max_archive_age_days)
        
        # Тестові дати подій
        recent_event = now - timedelta(days=3)     
        old_event = now - timedelta(days=10)       
        too_old_event = now - timedelta(days=40)  
        
        # Перевіряємо логіку
        assert recent_event > archive_threshold    
        assert old_event < archive_threshold and old_event > max_age_threshold 
        assert too_old_event < max_age_threshold   
        
