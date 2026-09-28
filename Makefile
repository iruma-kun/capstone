.PHONY: help install backend-install frontend-install run test docker-build docker-up docker-down clean

# Default target
help:
	@echo "Cloud-Native Automated Compliance and Audit System"
	@echo ""
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@echo "  install          Install all dependencies (backend + frontend)"
	@echo "  backend-install  Install Python dependencies only"
	@echo "  frontend-install Install Node.js dependencies only"
	@echo "  run              Start the full platform (API + Frontend)"
	@echo "  backend-run      Start only the FastAPI backend"
	@echo "  frontend-run     Start only the Next.js frontend"
	@echo "  test             Run backend tests"
	@echo "  docker-build     Build Docker image"
	@echo "  docker-up        Start services with Docker Compose"
	@echo "  docker-down      Stop Docker Compose services"
	@echo "  seed             Seed sample documents into database"
	@echo "  clean            Clean build artifacts and cache"

# Install all dependencies
install: backend-install frontend-install

# Backend dependencies
backend-install:
	@echo "Installing Python dependencies..."
	pip install --upgrade pip
	pip install -r backend/requirements.txt

# Frontend dependencies
frontend-install:
	@echo "Installing Node.js dependencies..."
	cd frontend && npm install

# Run full platform
run:
	@echo "Starting Compliance Audit Platform..."
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"
	@echo "API Docs: http://localhost:8000/docs"
	@./run_platform.sh & cd frontend && npm run dev

# Run only backend
backend-run:
	@echo "Starting FastAPI Backend on http://localhost:8000"
	cd backend && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run only frontend
frontend-run:
	@echo "Starting Next.js Frontend on http://localhost:3000"
	cd frontend && npm run dev

# Run tests
test:
	@echo "Running backend tests..."
	cd backend && python -m pytest -v

# Docker operations
docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

# Seed sample documents
seed:
	@echo "Seeding sample documents..."
	curl -X POST http://localhost:8000/api/seed-samples

# Clean up
clean:
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .coverage htmlcov
	rm -rf frontend/.next frontend/node_modules
	rm -rf venv
	docker-compose down -v 2>/dev/null || true
