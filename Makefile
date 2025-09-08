.PHONY: up
up:
\tdocker compose -f ops/docker-compose.yml up --build