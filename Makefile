.PHONY: help install run test format lint clean docker-build docker-run import-sample

# Default target
help:
	@echo "Available commands:"
	@echo "  install       - Install dependencies"
	@echo "  run           - Run the application"
	@echo "  test          - Run tests"
	@echo "  format        - Format code with black and isort"
	@echo "  lint          - Run linting with flake8 and mypy"
	@echo "  clean         - Clean up temporary files"
	@echo "  docker-build  - Build Docker image"
	@echo "  docker-run    - Run with Docker Compose"
	@echo "  import-sample - Import sample data from CSV"

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
	docker build -t event-analytics .

docker-run:
	docker-compose up --build

import-sample:
	python -m app.cli.import_events data/events_sample.csv

# Development helpers
dev-setup: install
	cp .env.example .env
	@echo "Development environment set up!"
	@echo "Edit .env file as needed, then run 'make run'"

# Database helpers
init-db:
	python -c "from app.database.connection import init_sync_db; init_sync_db()"

# API testing helpers
test-api:
	@echo "Testing API endpoints..."
	curl -X GET "http://localhost:8000/docs"
	@echo "\nAPI documentation available at: http://localhost:8000/docs"
