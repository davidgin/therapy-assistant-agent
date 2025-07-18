# Makefile for therapy-assistant-agent development tasks

.PHONY: help install install-dev lint format type-check security test test-unit test-integration test-cov clean build run dev docs pre-commit setup-hooks

# Default target
help:
	@echo "🏥 Therapy Assistant Agent - Development Commands"
	@echo "=================================================="
	@echo ""
	@echo "Setup Commands:"
	@echo "  install        Install production dependencies"
	@echo "  install-dev    Install development dependencies"
	@echo "  setup-hooks    Setup pre-commit hooks"
	@echo ""
	@echo "Code Quality Commands:"
	@echo "  lint           Run all linting tools"
	@echo "  format         Format code with black and isort"
	@echo "  type-check     Run type checking with mypy"
	@echo "  security       Run security analysis"
	@echo "  optimize       Run full optimization analysis"
	@echo ""
	@echo "Testing Commands:"
	@echo "  test           Run all tests"
	@echo "  test-unit      Run unit tests only"
	@echo "  test-integration Run integration tests only"
	@echo "  test-cov       Run tests with coverage report"
	@echo "  test-watch     Run tests in watch mode"
	@echo ""
	@echo "Development Commands:"
	@echo "  run            Run the application"
	@echo "  dev            Run in development mode"
	@echo "  migrate        Run database migrations"
	@echo "  seed           Seed database with test data"
	@echo ""
	@echo "Maintenance Commands:"
	@echo "  clean          Clean build artifacts"
	@echo "  build          Build the application"
	@echo "  docs           Generate documentation"

# Installation
install:
	@echo "📦 Installing production dependencies..."
	pip install -e .

install-dev:
	@echo "📦 Installing development dependencies..."
	pip install -e ".[dev,test,docs]"
	pip install pre-commit radon

setup-hooks:
	@echo "🔧 Setting up pre-commit hooks..."
	pre-commit install
	pre-commit install --hook-type commit-msg

# Code Quality
lint: 
	@echo "🧹 Running linting tools..."
	python -m flake8 app tests scripts
	python -m bandit -r app -x "*/tests/*"

format:
	@echo "🎨 Formatting code..."
	python -m autoflake --remove-all-unused-imports --remove-unused-variables --remove-duplicate-keys --expand-star-imports --in-place --recursive app tests scripts
	python -m isort app tests scripts
	python -m black app tests scripts

type-check:
	@echo "🔍 Running type checking..."
	python -m mypy app

security:
	@echo "🔒 Running security analysis..."
	python -m bandit -r app -f json -o bandit-report.json || true
	python -m safety check --json --output safety-report.json || true
	@echo "Security reports generated: bandit-report.json, safety-report.json"

optimize:
	@echo "⚡ Running full optimization analysis..."
	python scripts/lint_and_optimize.py --output optimization-report.json

# Testing
test:
	@echo "🧪 Running all tests..."
	python -m pytest

test-unit:
	@echo "🧪 Running unit tests..."
	python -m pytest tests/unit/ -m unit

test-integration:
	@echo "🧪 Running integration tests..."
	python -m pytest tests/integration/ -m integration

test-cov:
	@echo "🧪 Running tests with coverage..."
	python -m pytest --cov=app --cov-report=html --cov-report=term-missing --cov-report=xml

test-watch:
	@echo "🧪 Running tests in watch mode..."
	python -m pytest --tb=short -q --disable-warnings --no-header -x --lf

test-security:
	@echo "🧪 Running security tests..."
	python -m pytest -m security

test-performance:
	@echo "🧪 Running performance tests..."
	python -m pytest -m performance

# Development
run:
	@echo "🚀 Starting application..."
	python -m uvicorn app.main_auth_async:app --reload --host 0.0.0.0 --port 8000

dev:
	@echo "🔧 Starting development server..."
	python -m uvicorn app.main_auth_async:app --reload --host 0.0.0.0 --port 8000 --log-level debug

run-web:
	@echo "🌐 Starting web server..."
	python -m uvicorn app.main_web:app --reload --host 0.0.0.0 --port 8001

migrate:
	@echo "🗃️  Running database migrations..."
	alembic upgrade head

migrate-auto:
	@echo "🗃️  Generating automatic migration..."
	alembic revision --autogenerate -m "Auto migration"

migrate-rollback:
	@echo "🗃️  Rolling back last migration..."
	alembic downgrade -1

seed:
	@echo "🌱 Seeding database with test data..."
	python scripts/seed_database.py

# Maintenance
clean:
	@echo "🧹 Cleaning build artifacts..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -f *.log

build:
	@echo "📦 Building application..."
	python -m build

docs:
	@echo "📚 Generating documentation..."
	mkdocs build

docs-serve:
	@echo "📚 Serving documentation locally..."
	mkdocs serve

# Database utilities
db-reset:
	@echo "⚠️  Resetting database (WARNING: This will delete all data)..."
	@read -p "Are you sure? Type 'yes' to continue: " confirm && [ "$$confirm" = "yes" ]
	python -c "from app.core.database import db_manager; import asyncio; asyncio.run(db_manager.drop_tables())"
	alembic upgrade head

db-shell:
	@echo "🗃️  Opening database shell..."
	python -c "from app.core.database import db_manager; print('Database URL:', db_manager._get_database_url())"

# Quality gates
check-all: format type-check lint security test
	@echo "✅ All quality checks passed!"

fix-all: format
	@echo "🔧 Auto-fixing code issues..."
	python scripts/lint_and_optimize.py --fix

# Docker commands
docker-build:
	@echo "🐳 Building Docker image..."
	docker build -t therapy-assistant-agent .

docker-run:
	@echo "🐳 Running Docker container..."
	docker run -p 8000:8000 therapy-assistant-agent

docker-dev:
	@echo "🐳 Running Docker in development mode..."
	docker-compose up --build

# Monitoring
monitor-logs:
	@echo "📊 Monitoring application logs..."
	tail -f app.log

monitor-metrics:
	@echo "📊 Checking application metrics..."
	python -c "from app.core.database import db_metrics; print(db_metrics.get_metrics())"

# Deployment
deploy-staging:
	@echo "🚀 Deploying to staging..."
	# Add staging deployment commands here

deploy-prod:
	@echo "🚀 Deploying to production..."
	@echo "⚠️  Production deployment requires manual approval"
	# Add production deployment commands here

# Environment setup
env-setup:
	@echo "🔧 Setting up environment..."
	cp .env.example .env
	@echo "Please edit .env file with your configuration"

env-check:
	@echo "🔍 Checking environment configuration..."
	python -c "from app.core.config import get_settings; s = get_settings(); print('Environment OK' if s.SECRET_KEY != 'your-secret-key-change-in-production' else 'WARNING: Change SECRET_KEY')"

# Performance
profile:
	@echo "📊 Running performance profiling..."
	python -m cProfile -o profile.stats -m uvicorn app.main_auth_async:app --host 127.0.0.1 --port 8000 &
	sleep 10
	curl http://localhost:8000/health
	pkill -f uvicorn
	python -c "import pstats; pstats.Stats('profile.stats').sort_stats('cumulative').print_stats(20)"

benchmark:
	@echo "🏃 Running benchmarks..."
	python -m pytest tests/ -m performance --benchmark-only

# Git hooks
pre-commit-all:
	@echo "🔧 Running pre-commit on all files..."
	pre-commit run --all-files

# Help for specific commands
help-test:
	@echo "Testing Help:"
	@echo "  test           - Run all tests with default settings"
	@echo "  test-unit      - Run only unit tests (faster)"
	@echo "  test-integration - Run integration tests (slower)"
	@echo "  test-cov       - Generate coverage reports"
	@echo "  test-watch     - Continuously run tests on file changes"

help-quality:
	@echo "Code Quality Help:"
	@echo "  format         - Auto-format code (black, isort, autoflake)"
	@echo "  lint           - Check code style and potential issues"
	@echo "  type-check     - Verify type annotations"
	@echo "  security       - Scan for security vulnerabilities"
	@echo "  optimize       - Full analysis with recommendations"