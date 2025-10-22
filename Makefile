.PHONY: help install run test format lint clean docker-build docker-run import-sample

# Default target
help:
	@echo "Available commands:"
	@echo ""
	@echo "Local Development:"
	@echo "  install         - Install dependencies"
	@echo "  run             - Run the application locally"
	@echo "  test            - Run tests locally"
	@echo "  security-audit  - Run security audit for hardcoded secrets"
	@echo "  create-admin    - Create admin user for JWT authentication"
	@echo "  jwt-demo        - Demonstrate JWT authentication (requires running server)"
	@echo "  format          - Format code with black and isort"
	@echo "  lint            - Run linting with flake8 and mypy"
	@echo "  clean           - Clean up temporary files"
	@echo "  import-sample   - Import sample data from CSV"
	@echo ""
	@echo "Docker Development:"
	@echo "  docker-build    - Build Docker image"
	@echo "  docker-run      - Run with Docker Compose"
	@echo "  docker-dev      - Start development environment"
	@echo "  docker-prod     - Start production environment"
	@echo "  docker-down     - Stop and remove services"
	@echo "  docker-restart  - Restart all services"
	@echo "  docker-logs     - Show logs from all services"
	@echo "  docker-shell    - Open shell in app container"
	@echo "  docker-test     - Run tests in Docker container"
	@echo "  docker-clean    - Remove containers, networks, and volumes"
	@echo "  docker-status   - Show container status"
	@echo ""
	@echo "Database & Redis:"
	@echo "  docker-db-shell   - Connect to PostgreSQL database"
	@echo "  docker-redis-cli  - Connect to Redis CLI"

install:
	pip install -r requirements.txt

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

test:
	pytest tests/ -v --tb=short

format:
	black app/ tests/
	isort app/ tests/

lint:
	flake8 app/ tests/
	mypy app/

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.db" -delete
	find . -type f -name "test.db" -delete

docker-build:
	docker compose build

docker-run:
	docker compose up --build

# Docker development environment
docker-dev:
	docker compose up -d
	@echo "Development environment started!"
	@echo "Application: http://localhost:$${APP_EXTERNAL_PORT:-8000}"
	@echo "PostgreSQL: localhost:$${POSTGRES_EXTERNAL_PORT:-5433}"
	@echo "Redis: localhost:$${REDIS_EXTERNAL_PORT:-6379}"

# Docker production environment
docker-prod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
	@echo "Production environment started!"

# Docker management
docker-down:
	docker compose down

docker-restart:
	docker compose restart

docker-logs:
	docker compose logs -f

docker-shell:
	docker compose exec app /bin/bash

docker-test:
	docker compose exec app python -m pytest tests/ -v

docker-clean:
	docker compose down -v --remove-orphans
	docker system prune -f

# Database helpers for Docker
docker-db-shell:
	docker compose exec db psql -U $${POSTGRES_USER:-events_user} -d $${POSTGRES_DB:-events}

docker-redis-cli:
	docker compose exec redis redis-cli

docker-status:
	docker compose ps

import-sample:
	python -m app.cli.import_events data/events_sample.csv

# Development helpers
dev-setup: install
	cp .env.example .env
	@echo "Development environment set up!"
	@echo "Edit .env file as needed, then run 'make run'"

# Security & Authentication
security-audit:
	python scripts/security_audit.py

create-admin:
	python scripts/create_admin.py

jwt-demo:
	@echo "Starting JWT authentication demo..."
	@echo "Make sure the API server is running on localhost:8000"
	python scripts/jwt_demo.py

refresh-demo:
	@echo "Starting refresh token demo..."
	@echo "Make sure the API server is running on localhost:8000"
	python scripts/refresh_token_demo.py

# Testing targets
test-refresh:
	@echo "Testing refresh token functionality..."
	python -m pytest tests/test_refresh_tokens.py -v

test-auth:
	@echo "Testing complete authentication system..."
	python -m pytest tests/test_auth_complete.py tests/test_refresh_tokens.py -v

# Database helpers  
init-db:
	python -c "from app.database.connection import init_sync_db; init_sync_db()"

# API testing helpers
test-api:
	@echo "Testing API endpoints..."
	curl -X GET "http://localhost:8000/docs"
	@echo "\nAPI documentation available at: http://localhost:8000/docs"
