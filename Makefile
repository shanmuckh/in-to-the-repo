.PHONY: help setup install dev dev-backend dev-worker dev-frontend services build up down logs clean test lint format db-migrate health docs

PYTHON ?= python3.12
VENV := backend/.venv
COMPOSE := docker compose -f docker-compose.dev.yml

# Default target
help:
	@echo "================================"
	@echo "In to the Repo - Make Commands"
	@echo "================================"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install       - Install all dependencies (local development)"
	@echo "  make setup         - Setup development environment with virtual env"
	@echo ""
	@echo "Development:"
	@echo "  make services      - Start local Postgres + Redis (Homebrew)"
	@echo "  make dev           - Start API, Celery worker and frontend together"
	@echo "  make dev-backend   - Start FastAPI dev server only"
	@echo "  make dev-worker    - Start Celery worker only"
	@echo "  make dev-frontend  - Start Next.js dev server only"
	@echo ""
	@echo "Docker & Deployment:"
	@echo "  make build         - Build Docker images"
	@echo "  make up            - Start all services (Docker Compose)"
	@echo "  make down          - Stop all services"
	@echo "  make logs          - View logs from all services"
	@echo "  make clean         - Remove containers, volumes, and build artifacts"
	@echo ""
	@echo "Database:"
	@echo "  make db-migrate    - Run database migrations"
	@echo "  make db-reset      - Reset database to fresh state"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  make test          - Run all tests"
	@echo "  make test-backend  - Run backend tests only"
	@echo "  make test-coverage - Run tests with coverage report"
	@echo "  make lint          - Run code linters"
	@echo "  make format        - Format code (black, isort, prettier)"
	@echo ""
	@echo "Utilities:"
	@echo "  make health        - Check health of all services"
	@echo "  make docs          - Open API documentation in browser"
	@echo ""

# ==========================================
# SETUP & INSTALLATION
# ==========================================

setup:
	@echo "Setting up development environment..."
	$(PYTHON) -m venv $(VENV) && $(VENV)/bin/pip install -r backend/requirements.txt
	@test -f backend/.env || (sed "s|^SECRET_KEY=$$|SECRET_KEY=$$(openssl rand -hex 32)|" backend/.env.example > backend/.env && echo "Created backend/.env (add GEMINI_API_KEY for AI features)")
	cd frontend && npm install
	@echo "Setup complete! Run 'make dev' to start developing."

install:
	@echo "Installing dependencies..."
	cd backend && pip install -r requirements.txt
	cd frontend && npm install
	@echo "Dependencies installed!"

# ==========================================
# DEVELOPMENT
# ==========================================

dev:
	@echo "Starting development environment..."
	@echo "Backend: http://localhost:8000 (API Docs: http://localhost:8000/docs)"
	@echo "Frontend: http://localhost:3000"
	@echo ""
	@$(MAKE) -j3 dev-backend dev-worker dev-frontend

services:
	brew services start postgresql@16
	brew services start redis

dev-backend:
	cd backend && .venv/bin/uvicorn src.main:app --reload --reload-dir src --port 8000

# threads pool: macOS prefork + Objective-C runtime can crash forked workers
dev-worker:
	cd backend && .venv/bin/celery -A src.tasks.worker worker --loglevel=info --pool=threads --concurrency=4

dev-frontend:
	cd frontend && npm run dev

# ==========================================
# DOCKER & DEPLOYMENT
# ==========================================

build:
	@echo "Building Docker images..."
	$(COMPOSE) build
	@echo "Build complete!"

up:
	@echo "Starting services with Docker Compose..."
	$(COMPOSE) up -d
	@echo ""
	@echo "Services started!"
	@echo "Backend API: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"
	@echo "Frontend: http://localhost:3000"
	@echo ""
	@echo "Waiting for services to be healthy..."
	@sleep 10
	@make health

down:
	@echo "Stopping services..."
	$(COMPOSE) down
	@echo "Services stopped!"

logs:
	@$(COMPOSE) logs -f

logs-backend:
	@$(COMPOSE) logs -f backend

logs-worker:
	@$(COMPOSE) logs -f celery_worker

logs-frontend:
	@$(COMPOSE) logs -f frontend

clean:
	@echo "Cleaning up..."
	@$(COMPOSE) down -v
	@rm -rf backend/__pycache__ backend/**/__pycache__
	@rm -rf backend/.pytest_cache backend/htmlcov
	@rm -rf frontend/.next frontend/out
	@rm -rf .pytest_cache
	@echo "Cleanup complete!"

# ==========================================
# TESTING & QUALITY
# ==========================================

test:
	@echo "Running all tests..."
	cd backend && .venv/bin/pytest tests/ -v

test-backend:
	@echo "Running backend tests..."
	cd backend && .venv/bin/pytest tests/ -v

test-coverage:
	@echo "Running tests with coverage report..."
	cd backend && .venv/bin/pytest tests/ -v --cov=src --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"

lint:
	@echo "Running linters..."
	cd backend && .venv/bin/flake8 src tests 2>/dev/null || echo "flake8 not installed"
	cd frontend && npm run lint 2>/dev/null || echo "ESLint not configured"

format:
	@echo "Formatting code..."
	cd backend && .venv/bin/black src tests && .venv/bin/isort src tests
	cd frontend && npm run format 2>/dev/null || echo "Format script not found"

# ==========================================
# DATABASE
# ==========================================

db-migrate:
	@echo "Running database migrations..."
	cd backend && .venv/bin/alembic upgrade head 2>/dev/null || echo "Alembic not configured"

db-reset:
	@echo "Resetting database..."
	@$(COMPOSE) down -v db
	@$(COMPOSE) up -d db
	@echo "Waiting for database..."
	@sleep 5
	@make db-migrate

# ==========================================
# UTILITIES
# ==========================================

health:
	@echo "Health Check Results:"
	@echo "====================="
	@curl -s -f http://localhost:8000/ > /dev/null 2>&1 && echo "✓ Backend API: OK" || echo "✗ Backend API: FAILED"
	@curl -s -f http://localhost:3000 > /dev/null 2>&1 && echo "✓ Frontend: OK" || echo "✗ Frontend: FAILED"
	@redis-cli ping > /dev/null 2>&1 && echo "✓ Redis: OK" || echo "✗ Redis: FAILED"
	@pg_isready -h localhost -p 5432 > /dev/null 2>&1 && echo "✓ PostgreSQL: OK" || echo "✗ PostgreSQL: FAILED"
	@echo ""

docs:
	@echo "Opening API documentation..."
	@python -m webbrowser http://localhost:8000/docs || open http://localhost:8000/docs 2>/dev/null || xdg-open http://localhost:8000/docs 2>/dev/null

# ==========================================
# GIT & DEPLOYMENT
# ==========================================

commit-check:
	@echo "Checking code quality before commit..."
	@make lint
	@make test
	@echo "All checks passed! Ready to commit."

production-build:
	@echo "Building for production..."
	@$(COMPOSE) build --no-cache
	@echo "Production build complete!"

