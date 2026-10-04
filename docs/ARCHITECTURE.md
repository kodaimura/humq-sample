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
- Usecases do not call other Usecases. Named internal business processing may hold pure decisions, database-informed decisions, or consistency processing when its business meaning is worth explaining and testing separately.
- Following HUMQ's project-structure guidance, Handler-called flows are placed under the corresponding resource directory and public Usecase files use verb or verb-phrase names.

These are responsibility and dependency rules. HUMQ does not require a particular class suffix, public method name, or one-class-per-file layout.

## humq-sample conventions

This repository adopts the following additional code conventions to make a medium-scale example uniform and mechanically checkable:

- One public Usecase file defines exactly one `*Usecase` class and one Primary Flow through its `execute` method. The file may also contain input types and private helpers used only by that flow.
- Independent flows are separate files even when they act on the same business entity. Internal processing remains part of its calling Usecase's responsibility and is never a second Primary Flow.
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

## Internal business processing

- Decisions and calculations may stay in the Usecase. Extraction is optional, including when only one Usecase calls the processing; an independently meaningful business reason is more useful than a line-count or reuse threshold.
- Extracted processing lives in a private file in the owning usecase domain. `_policies.py` is a useful starting name for business rules, while a specific name such as `organizations/_authorization.py` makes a focused capability easier to find. The filename does not require the processing to be pure.
- This sample's existing `_policies.py` files contain pure calculations. `organizations/_authorization.py` demonstrates database-informed authorization shared by several Usecases: it reads through `OrganizationModule` and `OrganizationMemberModule` using the caller's Session.
- Any extracted processing reads through Modules or Queries and writes through Modules. It does not perform direct ORM/SQL data access, own a Session or transaction boundary, or communicate with external systems. Its caller retains the primary flow, result branches, and failure policy.
- Handlers do not import or call private processing directly, and domain `__init__.py` files do not re-export it. This is part of the Usecase responsibility, not a fifth layer or a required Policy/Operation category.

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

The Architecture Test is a guardrail for mechanically detectable structural violations; passing it does not prove complete HUMQ compliance or semantic correctness. For example, AST checks cannot fully detect writes hidden in dynamic raw SQL, triggers installed outside the migrations, database cascade behavior outside the inspected schema, internal processing that semantically hides a Primary Flow, or whether another-table access is genuinely required. Those concerns still require schema inspection and design review.

When an intentional architecture change is made, update the implementation, this document, and the architecture tests in the same pull request.
