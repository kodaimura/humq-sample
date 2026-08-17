ENV ?= dev
PROJECT_NAME ?= $(notdir $(CURDIR))
WEB_PORT ?= 3000
SMOKE_BASE_URL ?= http://127.0.0.1:$(WEB_PORT)
DOCKER_COMPOSE = docker compose
DOCKER_COMPOSE_FILE = $(if $(filter prod,$(ENV)),-f docker-compose.prod.yml,-f docker-compose.yml)
DOCKER_COMPOSE_CMD = $(DOCKER_COMPOSE) $(DOCKER_COMPOSE_FILE)
RUN_WEB = $(DOCKER_COMPOSE_CMD) run --rm web

.PHONY: init up build build_no_cache down down_volumes stop in log logs ps reup restart install lint typecheck test check format format_check smoke audit audit_all outdated preview help

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

in:
	$(DOCKER_COMPOSE_CMD) exec web sh

log:
	$(DOCKER_COMPOSE_CMD) logs -f web

logs: log

ps:
	$(DOCKER_COMPOSE_CMD) ps

reup: down up

restart:
	$(DOCKER_COMPOSE_CMD) restart web

install:
	$(RUN_WEB) npm install

lint:
	$(RUN_WEB) npm run lint

typecheck:
	$(RUN_WEB) npm run typecheck

test:
	$(RUN_WEB) npm run test

check:
	$(RUN_WEB) npm run check

format:
	$(RUN_WEB) npm run format

format_check:
	$(RUN_WEB) npm run format:check

smoke:
	sh scripts/smoke.sh "$(SMOKE_BASE_URL)"

audit:
	$(RUN_WEB) npm audit --omit=dev

audit_all:
	$(RUN_WEB) npm audit

outdated:
	$(RUN_WEB) npm outdated

preview:
	$(RUN_WEB) npm run preview -- --host 0.0.0.0 --port 3000

help:
	@echo "Usage: make [target] [ENV=dev|prod]"
	@echo ""
	@echo "Targets:"
	@echo "  init      Initialize project identifiers (defaults to directory name)"
	@echo "  up        Start containers in the specified environment (default: dev)"
	@echo "  build     Build containers"
	@echo "  build_no_cache Build containers without cache"
	@echo "  down      Stop and remove containers and networks"
	@echo "  down_volumes Stop and remove containers, networks, and volumes"
	@echo "  stop      Stop containers"
	@echo "  in        Access web container via sh"
	@echo "  log       Show logs for the web container"
	@echo "  ps        Show status for containers"
	@echo "  reup      Re-up containers"
	@echo "  restart   Restart web container"
	@echo "  install   Install npm dependencies in Docker"
	@echo "  lint      Run ESLint in Docker"
	@echo "  typecheck Run TypeScript check in Docker"
	@echo "  test      Run unit tests in Docker"
	@echo "  check     Run lint, tests, and production build in Docker"
	@echo "  format    Format files with Prettier in Docker"
	@echo "  smoke     Check key routes on the running app"
	@echo "  audit     Run production dependency audit in Docker"
	@echo "  audit_all Run full dependency audit in Docker"
	@echo "  outdated  Check outdated dependencies in Docker"
	@echo "  preview   Run Vite preview in Docker"
