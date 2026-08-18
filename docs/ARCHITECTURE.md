# Application Architecture

This document records how this sample applies [HUMQ](https://github.com/kodaimura/humq). The upstream repository is the source for HUMQ's rationale and general rules; this document is the local implementation contract for paths, naming, and automated checks.

## Backend mapping

| Responsibility | Local path | Role |
| --- | --- | --- |
| Handler | `api/app/handler/` | HTTP translation, authentication context, dependency wiring, and response mapping |
| Usecase | `api/app/usecase/` | Business flow, authorization decisions, transaction ownership, and orchestration |
| Module | `api/app/module/<table>/` | Persistence and behavior for one table |
| Query | `api/app/query/` | Read-only joins, projections, dashboards, and search |

The normal dependency direction is:

```text
Handler -> Usecase -> Module
                   -> Query (read only)
```

Handlers enter business behavior through Usecases. Modules do not depend on Usecases or Queries, and Queries do not depend on Usecases.

## Transactions and persistence

- A Usecase owns the business transaction and shares its SQLAlchemy `Session` with participating Modules and Queries.
- Modules may flush changes needed by the current flow but do not begin, commit, or roll back transactions.
- Queries are read-only and never mutate ORM entities or issue write statements.
- Usecases delegate ORM persistence to Modules instead of writing directly through the session.
- Cross-table invariants and state transitions stay visible in the coordinating Usecase.

## Policies and operations

- A pure decision used by only one Usecase stays in that Usecase.
- Pure business decisions shared within a usecase domain live in that domain's `_policies.py`.
- Only domain-independent pure decisions shared across the application live in `api/app/usecase/_policies.py`.
- Policies do not access the database, network, mailer, clock, or transaction lifecycle.
- Database-backed processing genuinely shared by multiple Usecases may live in the business capability's owning domain under `_operations.py`. It may use Modules and Queries while participating in the caller's transaction.
- Operation classes end in `Operation`, expose `run`, do not commit or roll back, and do not call other Operations.
- Policies and Operations are private implementation details. Handlers never import them directly, and there is no public `policy` or `operations` layer.

## Frontend boundary

The React application under `web/` consumes the HTTP API. Business state transitions belong to backend Usecases; the frontend owns presentation state, input handling, and API result rendering.

## Architecture verification

`api/tests/test_architecture.py` enforces the dependency, transaction, persistence, policy, and operation rules. Run it with the complete backend suite:

```sh
make -C api check
```

When an intentional architecture change is made, update the implementation, this document, and the architecture tests in the same pull request.
