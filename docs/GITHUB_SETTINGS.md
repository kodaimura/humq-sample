# GitHub Repository Settings

GitHub repository settings are not stored in Git. A repository owner or administrator should complete this checklist after the initial push and first successful CI run.

## Repository details

Suggested description:

> A medium-scale B2B order, inventory, and fulfillment sample demonstrating HUMQ with FastAPI, React, and PostgreSQL.

Suggested topics:

- `humq`
- `fastapi`
- `react`
- `postgresql`
- `sqlalchemy`
- `b2b`
- `inventory-management`
- `order-management`
- `sample-application`

## Pull request settings

Open **Settings > General > Pull Requests** and configure the repository to:

- Enable squash merging.
- Disable merge commits.
- Disable rebase merging.
- Automatically delete head branches after merging.

## Main branch ruleset

Open **Settings > Rules > Rulesets**, create a branch ruleset targeting `main`, and enable these rules:

- Require a pull request before merging.
- Require the `Quality`, `E2E`, and `Build` checks from the `CI` workflow to pass.
- Require conversation resolution before merging.
- Restrict branch deletion.
- Block force pushes.

Use zero required approvals for solo development. Require at least one approval when other developers can merge changes. Set the ruleset to **Active** after reviewing its target and bypass permissions.

## Security and dependency alerts

- Enable private vulnerability reporting when it is available for the repository.
- Enable Dependabot alerts and the dependency graph.
- Review automatic Dependabot security updates separately before enabling them for this sample.
