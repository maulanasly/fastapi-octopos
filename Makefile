SHELL := /bin/bash

PYTHON ?= python
PIP ?= pip
UVICORN ?= uvicorn
HOST ?= 127.0.0.1
PORT ?= 8000
RELOAD ?= --reload
MSG ?= update-schema

.PHONY: help install run dev migrate migrate-down makemigration \
	migration-history migration-current lint format check test pre-commit clean

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

format: ## Auto-format code
	black .
	isort . --profile black

test: ## Run test suite
	pytest -q

check: ## Run tests with coverage + compile check
	pytest -q --cov=app --cov-report=term-missing --cov-fail-under=70
	$(PYTHON) -m compileall app alembic

pre-commit: ## Install pre-commit hooks
	pre-commit install

clean: ## Remove Python cache files
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
