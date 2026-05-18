.PHONY: help up-prod up-dev down logs logs-backend logs-frontend ps build test clean

help:
	@echo "Dependency Radar - Development Commands"
	@echo ""
	@echo "Production:"
	@echo "  make up-prod      Start production services (docker-compose up -d)"
	@echo "  make build        Build production images"
	@echo ""
	@echo "Development:"
	@echo "  make up-dev       Start dev environment (hot-reload)"
	@echo "  make watch        Watch logs in dev mode"
	@echo ""
	@echo "General:"
	@echo "  make down         Stop all services"
	@echo "  make ps           Show running services"
	@echo "  make logs         Show all logs (tail -f)"
	@echo "  make logs-backend Show backend logs (tail -f)"
	@echo "  make logs-frontend Show frontend logs (tail -f)"
	@echo "  make test         Run backend tests in container"
	@echo "  make clean        Remove containers, volumes, and images"
	@echo "  make shell-backend Open bash in backend container"
	@echo "  make shell-db     Connect to PostgreSQL"
	@echo ""

up-prod:
	docker-compose up -d
	@echo "✅ Production services started"
	@echo "   Frontend: http://localhost:5173"
	@echo "   Backend:  http://localhost:8000"

up-dev:
	docker-compose -f docker-compose.dev.yml up -d
	@echo "✅ Development services started"
	@echo "   Frontend: http://localhost:5173 (with hot-reload)"
	@echo "   Backend:  http://localhost:8000 (with auto-reload)"
	@echo "   pgAdmin:  http://localhost:5050"

build:
	docker-compose build

down:
	docker-compose down

down-dev:
	docker-compose -f docker-compose.dev.yml down

ps:
	docker-compose ps

logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-frontend:
	docker-compose logs -f frontend

watch: up-dev
	docker-compose -f docker-compose.dev.yml logs -f

test:
	docker-compose exec -T backend python -m pytest -v

test-watch:
	docker-compose exec -T backend python -m pytest -v --tb=short --looponfail

shell-backend:
	docker-compose exec backend bash

shell-db:
	docker-compose exec postgres psql -U radar_user -d dependency_radar

migrate:
	docker-compose exec -T backend alembic upgrade head

clean:
	docker-compose down -v
	docker-compose -f docker-compose.dev.yml down -v
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleaned up"

restart:
	docker-compose restart

restart-dev:
	docker-compose -f docker-compose.dev.yml restart

lint:
	docker-compose exec -T backend ruff check src

format:
	docker-compose exec -T backend ruff format src

health:
	@echo "Checking backend..."
	@curl -s http://localhost:8000/api/v1/health | jq . || echo "❌ Backend not responding"
	@echo ""
	@echo "Checking frontend..."
	@curl -s http://localhost:5173 > /dev/null && echo "✅ Frontend OK" || echo "❌ Frontend not responding"
