.PHONY: help build run stop logs clean compose-up compose-down

IMAGE_NAME=smtpy-app
CONTAINER_NAME=smtpy-app

help:
	@echo "Available commands:"
	@echo "  make build         Build the Docker images (docker-compose build)"
	@echo "  make run           Run the app stack in Docker (docker-compose up -d)"
	@echo "  make stop          Stop the running containers (docker-compose down)"
	@echo "  make logs          Show logs from the containers"
	@echo "  make clean         Remove images and containers"
	@echo "  make compose-up    Start with docker-compose (alias for run)"
	@echo "  make compose-down  Stop docker-compose stack (alias for stop)"

build:
	docker-compose build --no-cache

run:
	docker-compose up -d --build

stop:
	docker-compose down

logs:
	docker-compose logs -f

clean: stop
	docker system prune -f

compose-up: run

compose-down: stop 