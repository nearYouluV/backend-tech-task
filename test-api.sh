#!/bin/bash
# test-api.sh - Швидкий тест API функціональності

set -e

API_BASE="http://localhost:8000/api/v1"
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Тестування Event Analytics API${NC}"

# Функція для виведення результату
print_result() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
    else
        echo -e "${RED}❌ $1${NC}"
        exit 1
    fi
}

# 1. Перевірка доступності API
echo -e "\n${BLUE}1. Перевірка доступності API${NC}"
curl -s "$API_BASE/events?limit=1" > /dev/null
print_result "API доступне"

# 2. Додавання тестової події
echo -e "\n${BLUE}2. Додавання тестової події${NC}"
TEST_EVENT_ID="$(uuidgen)"
RESPONSE=$(curl -s -X POST "$API_BASE/events" \
  -H "Content-Type: application/json" \
  -d '{
    "events": [
      {
        "event_id": "'$TEST_EVENT_ID'",
        "user_id": 999,
        "event_type": "api_test",
        "occurred_at": "'$(date -u +%Y-%m-%dT%H:%M:%S)'",
        "properties": {
          "test": true,
          "script": "test-api.sh"
        }
      }
    ]
  }')

CREATED=$(echo $RESPONSE | jq -r '.created // 0')
if [ "$CREATED" -eq 1 ]; then
    print_result "Подія успішно створена (ID: $TEST_EVENT_ID)"
else
    echo -e "${RED}❌ Помилка створення події: $RESPONSE${NC}"
    exit 1
fi

# 3. Перевірка отримання події
echo -e "\n${BLUE}3. Перевірка отримання події${NC}"
FOUND_EVENT=$(curl -s "$API_BASE/events?user_id=999&event_type=api_test" | jq -r '.events[0].event_id // "not_found"')
if [ "$FOUND_EVENT" = "$TEST_EVENT_ID" ]; then
    print_result "Подія знайдена в базі даних"
else
    echo -e "${RED}❌ Подія не знайдена: $FOUND_EVENT${NC}"
    exit 1
fi

# 4. Тест фільтрації
echo -e "\n${BLUE}4. Тест фільтрації по користувачу${NC}"
USER_EVENTS=$(curl -s "$API_BASE/events?user_id=999" | jq -r '.count // 0')
if [ "$USER_EVENTS" -gt 0 ]; then
    print_result "Фільтрація працює ($USER_EVENTS подій знайдено)"
else
    echo -e "${RED}❌ Помилка фільтрації${NC}"
    exit 1
fi

# 5. Тест пагінації
echo -e "\n${BLUE}5. Тест пагінації${NC}"
PAGE1=$(curl -s "$API_BASE/events?limit=1&offset=0" | jq -r '.events | length')
if [ "$PAGE1" -eq 1 ]; then
    print_result "Пагінація працює"
else
    echo -e "${RED}❌ Помилка пагінації${NC}"
    exit 1
fi

# 6. Тест дублікатів
echo -e "\n${BLUE}6. Тест обробки дублікатів${NC}"
DUPLICATE_RESPONSE=$(curl -s -X POST "$API_BASE/events" \
  -H "Content-Type: application/json" \
  -d '{
    "events": [
      {
        "event_id": "'$TEST_EVENT_ID'",
        "user_id": 999,
        "event_type": "api_test_duplicate",
        "occurred_at": "'$(date -u +%Y-%m-%dT%H:%M:%S)'",
        "properties": {}
      }
    ]
  }')

DUPLICATES=$(echo $DUPLICATE_RESPONSE | jq -r '.duplicates // 0')
if [ "$DUPLICATES" -eq 1 ]; then
    print_result "Дублікати правильно оброблені"
else
    echo -e "${RED}❌ Помилка обробки дублікатів: $DUPLICATE_RESPONSE${NC}"
    exit 1
fi

# Підсумок
echo -e "\n${GREEN}🎉 Всі тести пройдені успішно!${NC}"
echo -e "${BLUE}📊 Статистика:${NC}"
TOTAL_EVENTS=$(curl -s "$API_BASE/events?limit=1" | jq -r '.count // 0')
echo -e "  Загально подій в БД: $TOTAL_EVENTS"
echo -e "  Тестова подія ID: $TEST_EVENT_ID"
echo -e "  API URL: $API_BASE"
echo -e "  Документація: http://localhost:8000/docs"
