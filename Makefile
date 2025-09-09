REPO_ROOT := $(shell git rev-parse --show-toplevel)
COMPOSE_FILE := $(REPO_ROOT)/ops/docker-compose.yml

.PHONY: up
up:
	docker compose -f $(COMPOSE_FILE) up --build

