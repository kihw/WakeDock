# WakeDock Makefile
# Build automation and development tasks

.PHONY: help setup install start stop restart clean build test lint format security docs

# Configuration
PYTHON := python3
PIP := pip
NODE := node
NPM := npm
DOCKER := docker
COMPOSE := docker-compose

# Directories
SRC_DIR := src
TEST_DIR := tests
DASHBOARD_DIR := dashboard
DOCS_DIR := docs
BUILD_DIR := build
DIST_DIR := dist

# Colors for output
RESET := \033[0m
RED := \033[31m
GREEN := \033[32m
YELLOW := \033[33m
BLUE := \033[34m
MAGENTA := \033[35m
CYAN := \033[36m

# Default target
help: ## Show this help message
	@echo "$(CYAN)WakeDock Build System$(RESET)"
	@echo "===================="
	@echo ""
	@echo "$(YELLOW)Available targets:$(RESET)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-20s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(YELLOW)Examples:$(RESET)"
	@echo "  make setup          # Initial project setup"
	@echo "  make dev            # Start development environment"
	@echo "  make test-all       # Run all tests"
	@echo "  make build-prod     # Build production images"

# Setup and Installation
setup: ## Initial project setup
	@echo "$(BLUE)Setting up WakeDock development environment...$(RESET)"
	@mkdir -p data logs caddy/data caddy/config backups temp
	@cp -n config/config.example.yml config/config.yml || true
	@cp -n .env.example .env || true
	@$(MAKE) install-python
	@$(MAKE) install-node
	@$(MAKE) install-hooks
	@echo "$(GREEN)Setup complete!$(RESET)"

install: install-python install-node  ## Install all dependencies

install-python: ## Install Python dependencies
	@echo "$(BLUE)Installing Python dependencies...$(RESET)"
	@$(PYTHON) -m venv venv || true
	@. venv/bin/activate && $(PIP) install --upgrade pip
	@. venv/bin/activate && $(PIP) install -r requirements.txt
	@. venv/bin/activate && $(PIP) install -r requirements-dev.txt
	@echo "$(GREEN)Python dependencies installed$(RESET)"

install-node: ## Install Node.js dependencies
	@echo "$(BLUE)Installing Node.js dependencies...$(RESET)"
	@if [ -d "$(DASHBOARD_DIR)" ]; then \
		cd $(DASHBOARD_DIR) && $(NPM) install; \
		echo "$(GREEN)Node.js dependencies installed$(RESET)"; \
	else \
		echo "$(YELLOW)Dashboard directory not found$(RESET)"; \
	fi

install-hooks: ## Install development hooks
	@echo "$(BLUE)Installing development hooks...$(RESET)"
	@if [ -f ".pre-commit-config.yaml" ]; then \
		. venv/bin/activate && pre-commit install; \
		echo "$(GREEN)Pre-commit hooks installed$(RESET)"; \
	else \
		echo "$(YELLOW)Pre-commit config not found$(RESET)"; \
	fi

# Service Management
start: ## Start all services
	@echo "$(BLUE)Starting WakeDock services...$(RESET)"
	@$(DOCKER) network create wakedock-network 2>/dev/null || true
	@$(COMPOSE) up -d
	@echo "$(GREEN)Services started!$(RESET)"
	@echo "$(CYAN)Dashboard: http://admin.localhost$(RESET)"
	@echo "$(CYAN)API: http://localhost:8000$(RESET)"

stop: ## Stop all services
	@echo "$(BLUE)Stopping WakeDock services...$(RESET)"
	@$(COMPOSE) down
	@echo "$(GREEN)Services stopped$(RESET)"

restart: stop start ## Restart all services

dev: ## Start development environment
	@echo "$(BLUE)Starting development environment...$(RESET)"
	@export WAKEDOCK_DEBUG=true && \
	 export WAKEDOCK_LOG_LEVEL=DEBUG && \
	 $(DOCKER) network create wakedock-network 2>/dev/null || true
	@if [ -f "docker-compose.dev.yml" ]; then \
		$(COMPOSE) -f docker-compose.yml -f docker-compose.dev.yml up -d; \
	else \
		$(COMPOSE) up -d; \
	fi
	@echo "$(GREEN)Development environment started!$(RESET)"

logs: ## Show service logs
	@$(COMPOSE) logs -f

shell: ## Access container shell (use CONTAINER=name to specify)
	@$(COMPOSE) exec $(or $(CONTAINER),wakedock-backend) /bin/bash

# Build Targets
build: ## Build Docker images
	@echo "$(BLUE)Building Docker images...$(RESET)"
	@$(COMPOSE) build
	@echo "$(GREEN)Build complete$(RESET)"

build-prod: ## Build production Docker images
	@echo "$(BLUE)Building production Docker images...$(RESET)"
	@$(COMPOSE) -f docker-compose.prod.yml build --no-cache
	@echo "$(GREEN)Production build complete$(RESET)"

build-backend: ## Build backend Docker image
	@echo "$(BLUE)Building backend image...$(RESET)"
	@$(DOCKER) build -t wakedock/backend:latest -f Dockerfile .
	@echo "$(GREEN)Backend build complete$(RESET)"

build-dashboard: ## Build dashboard Docker image
	@echo "$(BLUE)Building dashboard image...$(RESET)"
	@$(DOCKER) build -t wakedock/dashboard:latest -f $(DASHBOARD_DIR)/Dockerfile $(DASHBOARD_DIR)
	@echo "$(GREEN)Dashboard build complete$(RESET)"

# Testing
test: test-python test-javascript ## Run all tests

test-python: ## Run Python tests
	@echo "$(BLUE)Running Python tests...$(RESET)"
	@. venv/bin/activate && python -m pytest $(TEST_DIR)/ -v
	@echo "$(GREEN)Python tests complete$(RESET)"

test-javascript: ## Run JavaScript tests
	@echo "$(BLUE)Running JavaScript tests...$(RESET)"
	@if [ -d "$(DASHBOARD_DIR)" ]; then \
		cd $(DASHBOARD_DIR) && $(NPM) test; \
		echo "$(GREEN)JavaScript tests complete$(RESET)"; \
	else \
		echo "$(YELLOW)Dashboard directory not found$(RESET)"; \
	fi

test-integration: ## Run integration tests
	@echo "$(BLUE)Running integration tests...$(RESET)"
	@. venv/bin/activate && python -m pytest $(TEST_DIR)/integration/ -v
	@echo "$(GREEN)Integration tests complete$(RESET)"

test-e2e: ## Run end-to-end tests
	@echo "$(BLUE)Running end-to-end tests...$(RESET)"
	@if [ -d "$(DASHBOARD_DIR)" ]; then \
		cd $(DASHBOARD_DIR) && $(NPM) run test:e2e; \
		echo "$(GREEN)E2E tests complete$(RESET)"; \
	else \
		echo "$(YELLOW)Dashboard directory not found$(RESET)"; \
	fi

coverage: ## Generate test coverage report
	@echo "$(BLUE)Generating coverage report...$(RESET)"
	@. venv/bin/activate && python -m pytest $(TEST_DIR)/ --cov=$(SRC_DIR) --cov-report=html --cov-report=term
	@echo "$(GREEN)Coverage report generated in htmlcov/$(RESET)"

# Code Quality
lint: lint-python lint-javascript ## Run all linters

lint-python: ## Run Python linters
	@echo "$(BLUE)Running Python linters...$(RESET)"
	@. venv/bin/activate && flake8 $(SRC_DIR)/ $(TEST_DIR)/ --max-line-length=88 --extend-ignore=E203,W503
	@. venv/bin/activate && pylint $(SRC_DIR)/ --disable=C0114,C0115,C0116 --max-line-length=88
	@. venv/bin/activate && mypy $(SRC_DIR)/ --ignore-missing-imports
	@echo "$(GREEN)Python linting complete$(RESET)"

lint-javascript: ## Run JavaScript linters
	@echo "$(BLUE)Running JavaScript linters...$(RESET)"
	@if [ -d "$(DASHBOARD_DIR)" ]; then \
		cd $(DASHBOARD_DIR) && $(NPM) run lint; \
		echo "$(GREEN)JavaScript linting complete$(RESET)"; \
	else \
		echo "$(YELLOW)Dashboard directory not found$(RESET)"; \
	fi

format: format-python format-javascript ## Format all code

format-python: ## Format Python code
	@echo "$(BLUE)Formatting Python code...$(RESET)"
	@. venv/bin/activate && black $(SRC_DIR)/ $(TEST_DIR)/ --line-length=88
	@. venv/bin/activate && isort $(SRC_DIR)/ $(TEST_DIR)/ --profile black
	@echo "$(GREEN)Python formatting complete$(RESET)"

format-javascript: ## Format JavaScript code
	@echo "$(BLUE)Formatting JavaScript code...$(RESET)"
	@if [ -d "$(DASHBOARD_DIR)" ]; then \
		cd $(DASHBOARD_DIR) && $(NPM) run format; \
		echo "$(GREEN)JavaScript formatting complete$(RESET)"; \
	else \
		echo "$(YELLOW)Dashboard directory not found$(RESET)"; \
	fi

type-check: ## Run type checking
	@echo "$(BLUE)Running type checking...$(RESET)"
	@. venv/bin/activate && mypy $(SRC_DIR)/ --ignore-missing-imports
	@if [ -d "$(DASHBOARD_DIR)" ]; then \
		cd $(DASHBOARD_DIR) && $(NPM) run type-check; \
	fi
	@echo "$(GREEN)Type checking complete$(RESET)"

# Security
security: security-python security-javascript security-docker ## Run all security checks

security-python: ## Run Python security checks
	@echo "$(BLUE)Running Python security checks...$(RESET)"
	@. venv/bin/activate && bandit -r $(SRC_DIR)/
	@. venv/bin/activate && safety check
	@echo "$(GREEN)Python security checks complete$(RESET)"

security-javascript: ## Run JavaScript security checks
	@echo "$(BLUE)Running JavaScript security checks...$(RESET)"
	@if [ -d "$(DASHBOARD_DIR)" ]; then \
		cd $(DASHBOARD_DIR) && $(NPM) audit; \
		echo "$(GREEN)JavaScript security checks complete$(RESET)"; \
	else \
		echo "$(YELLOW)Dashboard directory not found$(RESET)"; \
	fi

security-docker: ## Run Docker security checks
	@echo "$(BLUE)Running Docker security checks...$(RESET)"
	@if command -v hadolint >/dev/null 2>&1; then \
		hadolint Dockerfile; \
		hadolint Dockerfile.prod; \
		echo "$(GREEN)Docker security checks complete$(RESET)"; \
	else \
		echo "$(YELLOW)Hadolint not installed$(RESET)"; \
	fi

# Database
db-migrate: ## Run database migrations
	@echo "$(BLUE)Running database migrations...$(RESET)"
	@$(COMPOSE) exec wakedock-backend python -m alembic upgrade head
	@echo "$(GREEN)Database migrations complete$(RESET)"

db-reset: ## Reset database
	@echo "$(RED)This will destroy all data!$(RESET)"
	@read -p "Continue? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo ""; \
		$(COMPOSE) down; \
		$(DOCKER) volume rm wakedock_postgres_data 2>/dev/null || true; \
		$(COMPOSE) up -d postgres; \
		sleep 10; \
		$(MAKE) db-migrate; \
		echo "$(GREEN)Database reset complete$(RESET)"; \
	else \
		echo ""; \
		echo "$(YELLOW)Database reset cancelled$(RESET)"; \
	fi

db-seed: ## Seed database with test data
	@echo "$(BLUE)Seeding database...$(RESET)"
	@$(COMPOSE) exec wakedock-backend python -m scripts.seed_db
	@echo "$(GREEN)Database seeded$(RESET)"

db-backup: ## Create database backup
	@echo "$(BLUE)Creating database backup...$(RESET)"
	@$(COMPOSE) exec postgres pg_dump -U wakedock wakedock > backups/backup-$$(date +%Y%m%d-%H%M%S).sql
	@echo "$(GREEN)Database backup created$(RESET)"

# Documentation
docs: ## Generate documentation
	@echo "$(BLUE)Generating documentation...$(RESET)"
	@mkdir -p $(DOCS_DIR)/build
	@. venv/bin/activate && python -c "import pydoc; pydoc.writedocs('$(SRC_DIR)')" || true
	@if command -v sphinx-build >/dev/null 2>&1; then \
		sphinx-build -b html $(DOCS_DIR)/source $(DOCS_DIR)/build/html; \
	fi
	@echo "$(GREEN)Documentation generated$(RESET)"

docs-serve: ## Serve documentation locally
	@echo "$(BLUE)Serving documentation at http://localhost:8080$(RESET)"
	@cd $(DOCS_DIR)/build/html && python -m http.server 8080

# Cleanup
clean: ## Clean build artifacts
	@echo "$(BLUE)Cleaning build artifacts...$(RESET)"
	@rm -rf $(BUILD_DIR)/ $(DIST_DIR)/ .pytest_cache/ .coverage htmlcov/
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)Cleanup complete$(RESET)"

clean-docker: ## Clean Docker resources
	@echo "$(BLUE)Cleaning Docker resources...$(RESET)"
	@read -p "Remove containers and volumes? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo ""; \
		$(COMPOSE) down -v; \
		$(DOCKER) system prune -f; \
		echo "$(GREEN)Docker cleanup complete$(RESET)"; \
	else \
		echo ""; \
		echo "$(YELLOW)Docker cleanup cancelled$(RESET)"; \
	fi

clean-all: clean clean-docker ## Clean everything

# Utility targets
check: ## Check development environment
	@echo "$(BLUE)Checking development environment...$(RESET)"
	@command -v $(PYTHON) >/dev/null 2>&1 || (echo "$(RED)Python not found$(RESET)" && exit 1)
	@command -v $(NODE) >/dev/null 2>&1 || (echo "$(RED)Node.js not found$(RESET)" && exit 1)
	@command -v $(DOCKER) >/dev/null 2>&1 || (echo "$(RED)Docker not found$(RESET)" && exit 1)
	@$(DOCKER) info >/dev/null 2>&1 || (echo "$(RED)Docker not running$(RESET)" && exit 1)
	@echo "$(GREEN)Environment check passed$(RESET)"

version: ## Show version information
	@echo "$(CYAN)WakeDock Development Environment$(RESET)"
	@echo "================================"
	@echo "Python: $$($(PYTHON) --version)"
	@echo "Node.js: $$($(NODE) --version)"
	@echo "Docker: $$($(DOCKER) --version)"
	@echo "Docker Compose: $$($(COMPOSE) --version)"

# Continuous Integration targets
ci-setup: ## Setup for CI environment
	@$(MAKE) install-python
	@$(MAKE) install-node

ci-test: ## Run CI tests
	@$(MAKE) lint
	@$(MAKE) security
	@$(MAKE) test
	@$(MAKE) coverage

ci-build: ## Build for CI
	@$(MAKE) build-prod

# Development workflow targets
quick-test: ## Quick test (unit tests only)
	@. venv/bin/activate && python -m pytest $(TEST_DIR)/unit/ -v

full-check: ## Full development check
	@$(MAKE) format
	@$(MAKE) lint
	@$(MAKE) type-check
	@$(MAKE) security
	@$(MAKE) test
	@$(MAKE) coverage

release-prep: ## Prepare for release
	@$(MAKE) full-check
	@$(MAKE) build-prod
	@$(MAKE) docs
	@echo "$(GREEN)Release preparation complete$(RESET)"

# Watch targets (requires entr or similar)
watch-test: ## Watch and run tests on changes
	@if command -v entr >/dev/null 2>&1; then \
		find $(SRC_DIR) $(TEST_DIR) -name "*.py" | entr -c make test-python; \
	else \
		echo "$(YELLOW)entr not installed. Install with: apt-get install entr$(RESET)"; \
	fi

watch-lint: ## Watch and run linting on changes
	@if command -v entr >/dev/null 2>&1; then \
		find $(SRC_DIR) -name "*.py" | entr -c make lint-python; \
	else \
		echo "$(YELLOW)entr not installed. Install with: apt-get install entr$(RESET)"; \
	fi
