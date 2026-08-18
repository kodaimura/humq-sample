DOCKER_COMPOSE := docker compose
ENV ?= dev
DOCKER_COMPOSE_FILE := $(if $(filter prod,$(ENV)),-f docker-compose.prod.yml,-f docker-compose.yml)
DOCKER_COMPOSE_CMD := $(DOCKER_COMPOSE) $(DOCKER_COMPOSE_FILE)

.DEFAULT_GOAL := help

.PHONY: up build build_no_cache build_prod smoke_prod down down_volumes stop logs logs_api logs_web ps reup migrate seed demo check check_api check_web help

up:
	$(DOCKER_COMPOSE_CMD) up -d

build:
	$(DOCKER_COMPOSE_CMD) build

build_no_cache:
	$(DOCKER_COMPOSE_CMD) build --no-cache

build_prod:
	$(MAKE) build ENV=prod

smoke_prod:
	$(MAKE) -C api smoke_prod PROJECT_NAME=humq-sample
	$(MAKE) -C web build ENV=prod

down:
	$(DOCKER_COMPOSE_CMD) down

down_volumes:
	$(DOCKER_COMPOSE_CMD) down -v

stop:
	$(DOCKER_COMPOSE_CMD) stop

logs:
	$(DOCKER_COMPOSE_CMD) logs -f

logs_api:
	$(DOCKER_COMPOSE_CMD) logs -f api

logs_web:
	$(DOCKER_COMPOSE_CMD) logs -f web

ps:
	$(DOCKER_COMPOSE_CMD) ps

reup: down up

migrate:
	$(DOCKER_COMPOSE_CMD) --profile tools run --rm migrate

seed: migrate
	$(DOCKER_COMPOSE_CMD) run --rm --no-deps api python -m app.seed

demo:
	$(MAKE) build
	$(MAKE) seed
	$(MAKE) up

check: check_api check_web

check_api:
	$(MAKE) -C api check ENV=$(ENV)

check_web:
	$(MAKE) -C web check ENV=$(ENV)

help:
	@echo "Usage: make [target] [ENV=dev|prod]"
	@echo ""
	@echo "Targets:"
	@echo "  up              Start the application"
	@echo "  build           Build application images"
	@echo "  build_no_cache  Build images without cache"
	@echo "  build_prod      Build production application images"
	@echo "  smoke_prod      Build production images and smoke test the API runtime"
	@echo "  down            Stop and remove containers"
	@echo "  down_volumes    Stop containers and remove volumes"
	@echo "  stop            Stop containers"
	@echo "  logs            Follow all logs"
	@echo "  logs_api        Follow API logs"
	@echo "  logs_web        Follow web logs"
	@echo "  ps              Show container status"
	@echo "  reup            Restart the application"
	@echo "  migrate         Apply backend database migrations"
	@echo "  seed            Apply migrations and load demo data (development only)"
	@echo "  demo            Build, seed, and start the complete demo environment"
	@echo "  check           Run backend and frontend checks"
