.PHONY: help build run stop logs clean compose-up compose-down up down logs build test

IMAGE_NAME=smtpy-app
CONTAINER_NAME=smtpy-app

help:
	@echo "Available commands:"
	@echo "  make build         Build the Docker images (docker-compose build)"
	@echo "  make run           Run the app stack in Docker (docker-compose up -d)"
	@echo "  make stop          Stop the running containers (docker-compose down)"
	@echo "  make logs          Show logs from the containers"
	@echo "  make test          Run the test suite with pytest"
	@echo "  make clean         Remove images and containers"
	@echo "  make compose-up    Start with docker-compose (alias for run)"
	@echo "  make compose-down  Stop docker-compose stack (alias for stop)"

build:
	docker compose -f docker-compose.dev.yml build

run:
	docker compose up -d --build

stop:
	docker compose down

logs:
	docker compose -f docker-compose.dev.yml logs -f

clean: stop
	docker system prune -f

compose-up: run

compose-down: stop

test:
	python -m pytest tests/ -v