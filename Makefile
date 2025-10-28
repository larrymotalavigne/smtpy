.PHONY: help install run stop logs clean compose-up compose-down up down build test lint format

IMAGE_NAME=smtpy-app
CONTAINER_NAME=smtpy-app

help:
	@echo "Available commands:"
	@echo "  make install       Install dependencies and sync the environment (uv sync)"
	@echo "  make build         Build the Docker images (docker-compose build)"
	@echo "  make run           Run the app stack in Docker (docker-compose up -d)"
	@echo "  make stop          Stop the running containers (docker-compose down)"
	@echo "  make logs          Show logs from the containers"
	@echo "  make test          Run the test suite with pytest"
	@echo "  make lint          Run ruff linter on the codebase"
	@echo "  make format        Format code with ruff"
	@echo "  make clean         Remove images and containers"
	@echo "  make compose-up    Start with docker-compose (alias for run)"
	@echo "  make compose-down  Stop docker-compose stack (alias for stop)"


install:
	pip install -U pip uv
	uv sync --active --all-extras --compile-bytecode --frozen --no-install-project

build:
	docker compose -f docker-compose.dev.yml build

test:
	uv run --active --all-extras --frozen pytest -c pyproject.toml $(PYTEST_EXTRA_ARGS)

run:
	docker compose -f docker-compose.dev.yml up -d --build

stop:
	docker compose -f docker-compose.dev.yml down

logs:
	docker compose -f docker-compose.dev.yml logs -f

clean: stop
	docker system prune -f

compose-up: run

compose-down: stop

lint:
	uv run ruff check back/

format:
	uv run ruff check --fix back/
	uv run ruff format back/

