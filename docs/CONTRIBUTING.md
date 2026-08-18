# Contributing

Keep changes focused, reviewable, and covered by tests. Never commit credentials, tokens, personal data, a local `.env` file, or generated runtime data.

Read [ARCHITECTURE.md](ARCHITECTURE.md) before changing backend responsibilities or dependencies. User-facing documentation is English-first in `README.md`; keep `README.ja.md` equivalent when shared behavior or setup changes.

## Before opening a pull request

Format Python changes with Ruff:

```sh
make -C api format
```

Run the same checks used by CI:

```sh
make check
make -C api test_e2e
make smoke_prod
```

The production Compose file requires `api/.env` when it is started. Use `api/.env.example` only as a local non-production starting point, and never use the example secrets in a deployed environment.

When behavior changes, add or update tests at the same level as the change. Update the relevant `.env.example` and documentation when configuration changes. Include an Alembic migration for database schema changes and verify both the migration and application behavior.

Use concise English commit subjects with an appropriate prefix, for example:

```text
feat: add shipment exception handling
fix: prevent duplicate inventory allocation
docs: clarify demo startup
refactor: isolate invoice eligibility policy
```

## Pull requests

- Explain the reason for the change, not only the implementation.
- Keep unrelated changes in separate pull requests.
- Describe API, UI, database, seed, configuration, and architecture impact.
- Resolve review comments and make sure CI passes before merging.
- Complete the relevant items in the pull request template.

Report vulnerabilities privately by following [SECURITY.md](SECURITY.md), not through a public issue or pull request.
