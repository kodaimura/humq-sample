DOCKER_COMPOSE := docker compose
ENV ?= dev
PROJECT_NAME ?= $(notdir $(CURDIR))
DOCKER_COMPOSE_FILE := $(if $(filter prod,$(ENV)),-f docker-compose.prod.yml,-f docker-compose.yml)
DOCKER_COMPOSE_CMD := $(DOCKER_COMPOSE) $(DOCKER_COMPOSE_FILE)
E2E_COMPOSE_CMD := $(DOCKER_COMPOSE) -p humq-sample-e2e -f docker-compose.yml -f docker-compose.test.yml
PYTHON_IMAGE := python:3.13-slim
API_DIR := $(CURDIR)
API_SERVICE := api
MIGRATE_SERVICE := migrate

.DEFAULT_GOAL := help

.PHONY: init up build build_no_cache down down_volumes stop exec shell logs ps reup seed demo check test test_e2e smoke routes requirements_compile migrate downgrade history heads current makemigration help

## -----------------------------
## Base Commands
## -----------------------------

init:
	./bin/scaf-init "$(PROJECT_NAME)"

up:
	$(DOCKER_COMPOSE_CMD) up -d

build:
	$(DOCKER_COMPOSE_CMD) build

build_no_cache:
	$(DOCKER_COMPOSE_CMD) build --no-cache

down:
	$(DOCKER_COMPOSE_CMD) down

down_volumes:
	$(DOCKER_COMPOSE_CMD) down -v

stop:
	$(DOCKER_COMPOSE_CMD) stop

exec:
	$(DOCKER_COMPOSE_CMD) exec $(API_SERVICE) /bin/sh

shell:
	$(DOCKER_COMPOSE_CMD) run --rm $(API_SERVICE) /bin/sh

logs:
	$(DOCKER_COMPOSE_CMD) logs -f $(API_SERVICE)

ps:
	$(DOCKER_COMPOSE_CMD) ps

reup: down up

seed: migrate
	$(DOCKER_COMPOSE_CMD) run --rm --no-deps $(API_SERVICE) python -m app.seed

demo:
	$(MAKE) build
	$(MAKE) seed
	$(MAKE) up

check:
	$(DOCKER_COMPOSE_CMD) run --rm --no-deps $(API_SERVICE) sh -c "python -m compileall -q app tests && python -m unittest discover -s tests -v"

test:
	$(DOCKER_COMPOSE_CMD) run --rm --no-deps $(API_SERVICE) python -m unittest discover -s tests -v

test_e2e:
	@set -eu; \
	cleanup() { $(E2E_COMPOSE_CMD) down -v --remove-orphans >/dev/null 2>&1 || true; }; \
	trap cleanup EXIT INT TERM; \
	cleanup; \
	$(E2E_COMPOSE_CMD) --profile tools run --rm --build $(MIGRATE_SERVICE); \
	$(E2E_COMPOSE_CMD) --profile test run --rm --build api-test

smoke:
	$(DOCKER_COMPOSE_CMD) exec -T $(API_SERVICE) python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).read().decode())"

routes:
	$(DOCKER_COMPOSE_CMD) run --rm --no-deps $(API_SERVICE) python -c "from app.main import app; print('\n'.join(sorted(app.openapi().get('paths', {}).keys())))"

requirements_compile:
	docker run --rm -v "$(API_DIR):/app" -w /app $(PYTHON_IMAGE) sh -c "python -m pip install --no-cache-dir pip-tools && pip-compile --strip-extras requirements.in --output-file requirements.txt"

## -----------------------------
## Alembic Migrations
## -----------------------------

# Apply all migrations
migrate:
	$(DOCKER_COMPOSE_CMD) run --rm $(MIGRATE_SERVICE) alembic upgrade head

# Rollback one step
downgrade:
	$(DOCKER_COMPOSE_CMD) run --rm $(MIGRATE_SERVICE) alembic downgrade -1

# Show migration history
history:
	$(DOCKER_COMPOSE_CMD) run --rm $(MIGRATE_SERVICE) alembic history

# Show migration heads
heads:
	$(DOCKER_COMPOSE_CMD) run --rm $(MIGRATE_SERVICE) alembic heads

# Show current revision
current:
	$(DOCKER_COMPOSE_CMD) run --rm $(MIGRATE_SERVICE) alembic current

# Create a new migration (name required: e.g. make makemigration name=add_users)
makemigration:
	@if [ -z "$(name)" ]; then \
		echo "ERROR: Please provide a migration name. Usage: make makemigration name=add_users"; \
		exit 1; \
	fi
	@echo "Creating new migration: $(name)"
	$(DOCKER_COMPOSE_CMD) run --rm $(MIGRATE_SERVICE) alembic revision --autogenerate -m "$(name)"

## -----------------------------
## Help
## -----------------------------

help:
	@echo "Usage: make [target] [ENV=dev|prod]"
	@echo "All targets run through Docker. Local Python/Node is not required."
	@echo ""
	@echo "Targets:"
	@echo "  init            Initialize project identifiers (defaults to directory name)"
	@echo "  up              Start containers (default: dev)"
	@echo "  build           Build containers"
	@echo "  build_no_cache  Build containers without cache"
	@echo "  down            Stop and remove containers and networks"
	@echo "  down_volumes    Stop and remove containers, networks, and volumes"
	@echo "  stop            Stop containers only"
	@echo "  exec            Enter api container shell"
	@echo "  shell           Start a one-off api shell"
	@echo "  logs            Show api logs"
	@echo "  ps              Show container status"
	@echo "  reup            Restart environment (down + up)"
	@echo "  seed            Apply migrations and load demo data (development only)"
	@echo "  demo            Build, seed, and start the demo environment"
	@echo "  check           Compile Python files and run tests"
	@echo "  test            Run unit tests inside the api container"
	@echo "  test_e2e        Run the full HTTP API contract in isolation"
	@echo "  smoke           Call /health from the running api container"
	@echo "  routes          Print FastAPI route paths from the api container"
	@echo "  requirements_compile"
	@echo "                  Compile pinned Python requirements with pip-tools"
	@echo ""
	@echo "Migration commands:"
	@echo "  migrate         Run Alembic upgrade head"
	@echo "  downgrade       Rollback one migration step"
	@echo "  history         Show migration history"
	@echo "  heads           Show migration heads"
	@echo "  current         Show current DB revision"
	@echo "  makemigration   Create new migration (usage: make makemigration name=add_users)"
	@echo ""
	@echo "Examples:"
	@echo "  make migrate ENV=prod"
	@echo "  make downgrade ENV=dev"
	@echo "  make makemigration name=add_user_table"
