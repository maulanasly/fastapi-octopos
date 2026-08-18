SHELL := /bin/bash

PYTHON ?= python
PIP ?= pip
UVICORN ?= uvicorn
HOST ?= 127.0.0.1
PORT ?= 8000
RELOAD ?= --reload
MSG ?= update-schema
FLUTTER ?= flutter
CLIENT_WEB_PORT ?= 3001
DOCKER ?= docker
DOCKER_COMPOSE ?= docker compose
IMG_NAME ?= octopos-backend

.PHONY: help install run dev migrate migrate-down makemigration \
	migration-history migration-current lint format check test pre-commit clean \
	client client-run client-test client-analyze 	docker-build docker-up docker-down docker-logs docker-ps 	docker-migrate docker-shell

help: ## Show available commands
	@echo "FastAPI OctoPOS - Make targets"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

install: ## Install project dependencies
	$(PIP) install -r requirements.txt

run: ## Run API server (reload enabled by default)
	$(UVICORN) app.main:app --host $(HOST) --port $(PORT) $(RELOAD)

dev: run ## Alias for run

migrate: ## Apply all migrations
	alembic upgrade head

migrate-down: ## Roll back one migration
	alembic downgrade -1

makemigration: ## Create new migration (use MSG="your-message")
	alembic revision --autogenerate -m "$(MSG)"

migration-history: ## Show migration history
	alembic history

migration-current: ## Show current migration version
	alembic current

lint: ## Run lint checks
	pre-commit run --all-files

format: ## Auto-fix and format code with ruff
	ruff check --fix .
	ruff format .

test: ## Run test suite
	pytest -q

check: ## Run tests with coverage + compile check
	pytest -q --cov=app --cov-report=term-missing --cov-fail-under=75
	$(PYTHON) -m compileall app alembic

pre-commit: ## Install pre-commit hooks
	pre-commit install

clean: ## Remove Python cache files
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

client: ## Run Flutter client (web, fixed port for CORS)
	cd client && $(FLUTTER) run -d chrome --web-port=$(CLIENT_WEB_PORT)

client-run: client ## Alias for client

client-test: ## Run Flutter tests
	cd client && $(FLUTTER) test

client-analyze: ## Run Flutter static analysis
	cd client && $(FLUTTER) analyze

docker-build: ## Build the backend image
	$(DOCKER) build -t $(IMG_NAME) .

docker-up: ## Build & start the stack (db + backend)
	$(DOCKER_COMPOSE) up -d --build

docker-down: ## Stop the stack
	$(DOCKER_COMPOSE) down

docker-logs: ## Follow backend logs
	$(DOCKER_COMPOSE) logs -f backend

docker-ps: ## Show running services
	$(DOCKER_COMPOSE) ps

docker-migrate: ## Run alembic upgrade head in the backend container
	$(DOCKER_COMPOSE) exec backend alembic upgrade head

docker-shell: ## Open a shell in the backend container
	$(DOCKER_COMPOSE) exec backend sh

docker-dev: ## Start the dev stack (source mounted, uvicorn --reload)
	$(DOCKER_COMPOSE) -f docker-compose.yml -f docker-compose.dev.yml up -d --build

docker-dev-down: ## Stop the dev stack
	$(DOCKER_COMPOSE) -f docker-compose.yml -f docker-compose.dev.yml down

docker-dev-logs: ## Follow backend logs (dev)
	$(DOCKER_COMPOSE) -f docker-compose.yml -f docker-compose.dev.yml logs -f backend
