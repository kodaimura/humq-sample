# Local Demo Runbook

This repository supports a local Docker demo. It does not define a production hosting provider, release pipeline, backup system, or production rollback procedure.

## Start

Docker with Compose support is the only prerequisite.

```sh
make demo
```

This builds the development images, applies migrations, loads idempotent demo data, and starts the services.

## Verify

Check container status and the backend health endpoint:

```sh
make ps
make -C api smoke
make -C web smoke
```

The main local endpoints are:

- Web: `http://localhost:3000`
- API health: `http://localhost:8000/health`
- OpenAPI: `http://localhost:8000/docs`
- MailHog: `http://localhost:8025`

Sign in with the demo account documented in `README.md`.

## Diagnose

Inspect service status and logs without deleting data:

```sh
make ps
make logs
```

Use `make logs_api` or `make logs_web` to narrow the output. Stop the environment with `make down`; its database volume is retained.

## Reset local data

`make down_volumes` deletes the local development database volume. Confirm that no needed local data is stored there before running it.

```sh
make down_volumes
make demo
```

The seed command is idempotent, so use `make seed` when a full database reset is unnecessary.

## Production boundary

`make build ENV=prod` validates that production images can be built, but it is not a deployment command. A real deployment must define its target environment, secret management, database backup and migration procedure, health verification, logs, and rollback process outside this sample before any release is attempted.
