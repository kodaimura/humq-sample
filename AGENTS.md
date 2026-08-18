# Repository Instructions

## Project Context

- This repository is a medium-scale B2B order, inventory, and fulfillment sample built to demonstrate HUMQ.
- It is a Docker-based monorepo: `api/` contains the FastAPI backend and `web/` contains the React frontend.
- Read `README.md`, the root `Makefile`, and the relevant package-level `Makefile` before changing setup or development workflows.
- Keep `README.md` as the primary English document and update `README.ja.md` with equivalent user-facing changes.

## Architecture

- This project follows [HUMQ](https://github.com/kodaimura/humq).
- Before designing, reviewing, or changing backend application code, read `docs/ARCHITECTURE.md`.
- Preserve the Handler, Usecase, Module, and Query responsibility boundaries and dependency direction.
- Treat `api/tests/test_architecture.py` as executable architecture constraints. Update the implementation, local architecture document, and tests together when an intentional architecture change is made.

## Working Agreements

- Keep changes focused and preserve unrelated work.
- Do not commit secrets, local `.env` files, database volumes, build output, or generated runtime data.
- Add or update tests when behavior changes.
- Use concise English commit subjects with an appropriate prefix such as `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `ci:`, or `chore:`.

## Verification

- Run `make -C api format` after changing Python code.
- Run `make check` for backend unit/architecture tests and frontend lint, tests, type checking, and build.
- Run `make -C api test_e2e` when API behavior, persistence, migrations, or database integration changes.
- Run `make smoke_prod` when container definitions, runtime dependencies, or production configuration changes.
- Run `make -C api routes` when adding or restructuring HTTP endpoints.

## Demo Operations

- Read `docs/RUNBOOK.md` before changing seed, startup, reset, health-check, or local recovery behavior.
- This repository documents a local Docker demo, not a production deployment target. Do not infer deployment authorization or invent a production destination.
