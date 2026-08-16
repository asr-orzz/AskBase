.PHONY: up down build logs migrate test lint clean

# Start all services
up:
	docker compose up -d

# Stop all services
down:
	docker compose down

# Build images
build:
	docker compose build

# View logs
logs:
	docker compose logs -f api celery-worker

# Run database migrations
migrate:
	docker compose exec api alembic upgrade head

# Run backend tests
test:
	cd backend && python -m pytest tests/ -v

# Run linters
lint:
	cd backend && ruff check app/ && ruff format --check app/
	cd frontend && npm run lint

# Infrastructure only (no app services)
infra:
	docker compose up -d postgres redis qdrant minio kafka zookeeper

# Full clean (remove volumes)
clean:
	docker compose down -v --remove-orphans
