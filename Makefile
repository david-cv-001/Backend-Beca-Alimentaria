.PHONY: help doctor env up-infra down up rebuild-app migrate seed test lint typecheck coverage smoke clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

doctor: ## Check prerequisites
	@echo "Checking prerequisites..."
	@command -v uv >/dev/null 2>&1 && echo "uv: OK" || echo "uv: MISSING"
	@command -v docker >/dev/null 2>&1 && echo "docker: OK" || (command -v podman >/dev/null 2>&1 && echo "podman: OK" || echo "container runtime: MISSING")
	@python3 --version

env: ## Create .env from .env.example if absent
	@test -f .env || (cp .env.example .env && echo "Created .env from .env.example")

up-infra: env ## Start dependencies only (postgres + pgvector)
	docker compose up -d postgres
	@echo "Waiting for postgres..."
	@sleep 5

down: ## Stop stack
	docker compose down

up: env ## Start everything
	docker compose up -d

rebuild-app: ## Rebuild app image
	docker compose up -d --build api

migrate: env ## Apply database migrations
	uv run alembic upgrade head

seed: ## Create the first superadmin (idempotent)
	uv run python scripts/seed_superadmin.py

install: ## Install dependencies with uv
	uv sync --extra dev

install-bio: ## Install with biometrics extras
	uv sync --extra dev --extra biometrics

lint: ## Run ruff
	uv run ruff check .

format: ## Run ruff format
	uv run ruff format .

typecheck: ## Run mypy
	uv run mypy app

test: ## Run tests
	uv run pytest

coverage: ## Run tests with coverage
	uv run coverage run -m pytest && uv run coverage report

smoke: ## Basic smoke test (requires running app)
	@echo "TODO: implement smoke test against running API"

clean: ## Clean caches
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
