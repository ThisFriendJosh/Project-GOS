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
