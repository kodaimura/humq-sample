# API E2E tests

These tests verify the public HTTP contract against a real API, PostgreSQL
database, migrations, and MailHog instance. `make test_e2e` creates an isolated
Compose project and removes its containers and volumes after the run.

## Adding feature coverage

- Add one `*.e2e.mjs` file per API domain, such as `projects.e2e.mjs`.
- Make every top-level test independent by creating its own uniquely named data.
- Cover cohesive user-visible behavior instead of framework implementation.
- Include the happy path, authentication boundary, important not-found or
  conflict response, persisted state transition, and security side effects.
- Put protocol helpers and reusable fixtures in `support.mjs`; keep domain rules
  in the domain test file.
- Extend an existing domain only when the endpoint belongs to that domain. Do
  not append unrelated features to an authentication lifecycle.

Run the complete contract with:

```sh
make test_e2e
```
