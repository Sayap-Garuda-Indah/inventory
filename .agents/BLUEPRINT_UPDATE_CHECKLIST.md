# Blueprint Update Checklist

This checklist tracks the remaining work needed to make SGI Inventory ready for a confident deployment. Keep it current whenever core behavior, deployment assumptions, or security posture changes.

## Release Readiness

- [ ] Confirm target deployment environment, hostnames, ports, and LAN access rules.
- [ ] Confirm Docker Compose deployment path for MySQL, API, and frontend.
- [ ] Verify production `.env` values are documented and not committed.
- [ ] Confirm rollback plan for API, frontend, database schema, and seed/admin data.
- [ ] Add a final smoke-test checklist for login, dashboard, items, issues, transactions, audit, settings, and QR export.
- [ ] Validate that `main` only receives reviewed, intentional merges.

## Backend Features

- [ ] Finish authentication and authorization hardening.
- [x] Restrict user directory endpoints to admin-only access.
- [x] Decide whether public registration is unsupported permanently or will become a future feature.
- [ ] Standardize API error responses across routers.
- [ ] Add request correlation IDs to logs and responses.
- [ ] Review all `500` handling and convert expected validation/business failures to `400`, `401`, `403`, `404`, or `409`.
- [ ] Ensure staff ownership rules are consistently enforced for items, issues, stock transactions, and issue items.
- [ ] Add pagination and search consistency across list endpoints.
- [ ] Review audit-session workflows for permission and state-transition correctness.
- [ ] Add API smoke tests for deployment-critical workflows.

## Frontend Features

- [ ] Ensure every protected route has matching frontend role guards.
- [ ] Remove or hide UI controls that backend authorization will reject.
- [ ] Confirm login behavior for expired, invalid, inactive, and missing-token sessions.
- [ ] Improve user-facing error handling for failed API requests.
- [ ] Confirm item-to-issue linking behavior for create, edit, change, and clear flows.
- [ ] Validate dashboard visibility for admin, staff, and auditor roles.
- [ ] Check mobile usability for main operational workflows.
- [ ] Confirm QR generation and PDF export behavior for active and inactive items.
- [ ] Add frontend build verification to release process.

## Security

- [ ] Require non-empty, strong `JWT_SECRET_KEY` in production.
- [ ] Add login rate limiting or lockout protection.
- [ ] Standardize auth failure messages to avoid account-state leakage.
- [x] Decide whether JWT stays in `localStorage` temporarily or moves to secure `HttpOnly` cookies.
- [ ] Add production security headers intentionally and verify they do not break the app.
- [ ] Review CORS configuration for exact deployment origins.
- [ ] Confirm Docker network exposure only allows intended public services.
- [ ] Remove tracked Python bytecode files from future commits if possible.
- [ ] Review logs to avoid leaking passwords, tokens, or authorization headers.
- [ ] Add backup and restore validation before production use.

## Data Model And Migrations

- [ ] Treat `api/db/migrations` as the source of truth for schema evolution.
- [ ] Confirm `api/db/schema.sql` and migrations do not diverge.
- [ ] Add migration tests or dry-run instructions for a fresh database.
- [ ] Document seed data strategy for categories, units, locations, settings, and admin user.
- [ ] Review foreign-key behavior for soft-deleted users, items, categories, units, and issues.
- [ ] Decide whether one item can belong to multiple issues or only one issue in the UI.
- [ ] Add indexes for high-use filters if performance testing shows slow queries.

## Observability And Operations

- [ ] Define required health checks for API, frontend, and MySQL.
- [ ] Add structured logging conventions for authentication, authorization, writes, and audit activity.
- [ ] Document how to inspect container logs during deployment.
- [ ] Document backup location, retention, restore command, and verification process.
- [ ] Add monitoring notes for disk usage, database availability, API latency, and failed logins.

## Documentation

- [ ] Keep README local development setup accurate.
- [ ] Keep DEPLOYMENT.md production deployment steps accurate.
- [ ] Maintain this checklist after every core feature or security change.
- [ ] Record user-visible functional changes in `CHANGELOG_BLUEPRINT.md`.
- [ ] Add short troubleshooting notes for common deployment and authentication failures.

## Final Pre-Deploy Gate

- [ ] Backend tests pass.
- [ ] Frontend build passes.
- [ ] Docker Compose build and startup pass from a clean environment.
- [ ] Fresh database migration succeeds.
- [ ] Admin bootstrap succeeds.
- [ ] Manual smoke test passes for each role.
- [ ] Backup and restore procedure is verified.
- [ ] Deployment owner signs off on current known risks.
