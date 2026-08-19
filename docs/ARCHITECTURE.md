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

## Core HUMQ rules applied here

- Handlers translate transport concerns and enter business behavior through Usecases.
- Each Usecase exposes one explainable Primary Flow and owns its business transaction.
- Modules own persistence and behavior for their table; cross-table writes remain coordinated by Usecases.
- Queries provide read-only joins and projections.
- Usecases do not call other Usecases. Pure shared decisions and limited shared database-backed processing follow the Policy and Operation rules below.
- Following HUMQ's project-structure guidance, Handler-called flows are placed under the corresponding resource directory and public Usecase files use verb or verb-phrase names.

These are responsibility and dependency rules. HUMQ does not require a particular class suffix, public method name, or one-class-per-file layout.

## humq-sample conventions

This repository adopts the following additional code conventions to make a medium-scale example uniform and mechanically checkable:

- One public Usecase file defines exactly one `*Usecase` class and one Primary Flow through its `execute` method. The file may also contain input types and private helpers used only by that flow.
- Independent flows are separate files even when they act on the same business entity. Shared pure decisions and shared database-backed processing follow the Policy and Operation rules below instead of being represented as additional Primary Flows in the same file.
- A state-changing Usecase stores its Session as `self.db` and marks `execute()` with `@transactional`. Read-only Usecases do neither.

The `*Usecase` suffix, `execute()` entry point, one Usecase class per file, and `@transactional` marker are conventions of this sample. They demonstrate one consistent way to implement HUMQ but are not mandatory HUMQ syntax.

## Transactions and persistence

- A Usecase owns the business transaction and shares its SQLAlchemy `Session` with participating Modules and Queries.
- `@transactional` makes the complete `execute()` Primary Flow the unit of work: it commits after a successful return and rolls back whenever the flow or commit raises an exception.
- Modules may flush changes needed by the current flow but do not begin, commit, or roll back transactions.
- Queries are read-only and never mutate ORM entities or issue write statements.
- Usecases delegate ORM persistence to Modules instead of writing directly through the session.
- Cross-table invariants and state transitions stay visible in the coordinating Usecase.
- `SessionLocal` uses `expire_on_commit=False`. ORM objects returned by a committed Usecase therefore remain loaded while the Handler maps them to response DTOs, avoiding implicit post-commit SELECTs from the Handler boundary.

## Policies and operations

- A pure decision used by only one Usecase stays in that Usecase.
- Pure business decisions shared within a usecase domain live in that domain's `_policies.py`.
- Only domain-independent pure decisions shared across the application live in `api/app/usecase/_policies.py`.
- Policies do not access the database, network, mailer, clock, or transaction lifecycle.
- Database-backed processing genuinely shared by multiple Usecases may live in the business capability's owning domain under `_operations.py`. It may use Modules and Queries while participating in the caller's transaction.
- Operation classes end in `Operation`, expose `run`, do not commit or roll back, and do not call other Operations.
- Policies and Operations are private implementation details. Handlers never import them directly, and there is no public `policy` or `operations` layer.

## Implicit database writes

The current model and migration definitions contain no application-defined database triggers, `ON DELETE CASCADE`, `ON UPDATE CASCADE`, or ORM delete cascades. Models use explicit foreign-key columns without ORM relationships, so multi-table state changes in the supported business flows remain visible as Module calls from their coordinating Usecase.

Future triggers or cascades must either be replaced by explicit Usecase-to-Module coordination or documented as a necessary database constraint with its rationale and affected flows. Ordinary foreign keys that enforce referential integrity without causing hidden state changes remain acceptable.

## Frontend boundary

The React application under `web/` consumes the HTTP API. Business state transitions belong to backend Usecases; the frontend owns presentation state, input handling, and API result rendering.

## Architecture verification

`api/tests/test_architecture.py` separates `CoreHumqRulesTest` from `HumqSampleConventionsTest`. It enforces common structural violations as well as this repository's chosen naming, Primary Flow, transaction-marker, and no-`assert` conventions. Run it with the complete backend suite:

```sh
make -C api check
```

The Architecture Test is a guardrail for mechanically detectable structural violations; passing it does not prove complete HUMQ compliance or semantic correctness. For example, AST checks cannot fully detect writes hidden in dynamic raw SQL, triggers installed outside the migrations, database cascade behavior outside the inspected schema, an Operation that semantically hides a Primary Flow, or whether another-table access is genuinely required. Those concerns still require schema inspection and design review.

When an intentional architecture change is made, update the implementation, this document, and the architecture tests in the same pull request.
