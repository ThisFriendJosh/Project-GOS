REPO_ROOT := $(shell git rev-parse --show-toplevel)
COMPOSE_FILE := $(REPO_ROOT)/ops/docker-compose.yml

.PHONY: up
up:
	docker compose -f $(COMPOSE_FILE) up --build

.PHONY: up down fmt test migrate

up:
	docker compose up --build

down:
	docker compose down

fmt:
	black api

test:
	pytest

migrate:
	docker compose run --rm api alembic upgrade head
