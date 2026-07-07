# Blueprint Implementation Detail

This document expands every item in `.agents/BLUEPRINT_UPDATE_CHECKLIST.md` into a GitHub issue-ready implementation plan. Each section can be copied into GitHub as an issue body.

## Release Readiness

### Issue: Confirm target deployment environment, hostnames, ports, and LAN access rules

**Summary**
Define the exact production deployment target for SGI Inventory, including host IP, DNS names, exposed ports, and LAN firewall rules.

**Scope**
- Confirm server OS, Docker runtime, host IP, DNS name, and local network range.
- Confirm exposed frontend, API, and database ports.
- Confirm whether API is publicly exposed or reachable only through frontend reverse proxy.

**Implementation Plan**
- Review `DEPLOYMENT.md`, `docker-compose.yaml`, and `front-end/nginx.conf`.
- Document final hostnames and ports in `DEPLOYMENT.md`.
- Add firewall examples for the approved network ranges.
- Confirm whether `HOST_IP` should be a fixed LAN IP or `0.0.0.0`.

**Acceptance Criteria**
- Deployment owner confirms target server and network range.
- Documentation names exact frontend URL and API access path.
- Database is not exposed outside the Docker/private network unless explicitly approved.

**Verification**
- Run `docker compose config`.
- Confirm browser access to frontend from an allowed client.
- Confirm blocked access from a disallowed client if firewall rules are available for testing.

### Issue: Confirm Docker Compose deployment path for MySQL, API, and frontend

**Summary**
Validate and document the intended Docker Compose deployment workflow for all production services.

**Scope**
- MySQL container.
- FastAPI container.
- Frontend Nginx container.
- Named volumes and initialization behavior.

**Implementation Plan**
- Review current `docker-compose.yaml` service definitions.
- Confirm build contexts, health checks, service dependencies, and volume usage.
- Add a clean deployment command sequence to `DEPLOYMENT.md`.
- Add a restart/update procedure for rebuilt containers.

**Acceptance Criteria**
- Fresh deployment can be performed from documented steps.
- API waits for MySQL health before starting.
- Frontend can reach API through internal Docker networking.

**Verification**
- Run `docker compose config`.
- Run a clean local or staging Compose startup.
- Check `/health` and frontend load after startup.

### Issue: Verify production `.env` values are documented and not committed

**Summary**
Ensure all required production environment variables are documented while secrets remain outside source control.

**Scope**
- Root `.env` for Docker Compose.
- Backend settings used by `api/core/config.py`.
- Frontend `VITE_*` build arguments.

**Implementation Plan**
- Create or update a non-secret `.env.example`.
- Cross-check documented variables with `docker-compose.yaml` and `api/core/config.py`.
- Ensure `.gitignore` excludes real `.env` files.
- Document required vs optional variables.

**Acceptance Criteria**
- Production `.env` values are not committed.
- All required variables have descriptions and sample placeholders.
- Deployment docs explain where to place environment files.

**Verification**
- Run `git status --ignored --short` to confirm real `.env` is ignored.
- Run `docker compose config` with a test `.env`.

### Issue: Confirm rollback plan for API, frontend, database schema, and seed/admin data

**Summary**
Create a rollback procedure for application containers, database migrations, seed data, and admin bootstrap behavior.

**Scope**
- API image rollback.
- Frontend image rollback.
- Database backup and restore.
- Migration rollback strategy.
- Admin user bootstrap considerations.

**Implementation Plan**
- Document image/version rollback steps in `DEPLOYMENT.md`.
- Define pre-deploy backup command.
- Define restore command and validation steps.
- Document how migrations are handled if rollback requires database changes.

**Acceptance Criteria**
- Deployment owner can restore the previous working state.
- Database rollback risk is documented.
- Admin bootstrap does not overwrite existing production admin credentials.

**Verification**
- Perform a restore dry run in staging or local Docker environment.
- Confirm app starts after restore.

### Issue: Add final smoke-test checklist for login, dashboard, items, issues, transactions, audit, settings, and QR export

**Summary**
Create a deploy smoke-test checklist covering the workflows that prove the system is usable after release.

**Scope**
- Login and logout.
- Role-based access.
- Dashboard.
- Items, categories, units, locations.
- Issues and issue items.
- Stock transactions.
- Audit sessions and scans.
- Settings and backup action.
- QR generation and PDF export.

**Implementation Plan**
- Add smoke-test section to `DEPLOYMENT.md` or a dedicated docs file.
- Include expected result for each workflow.
- Separate admin, staff, and auditor checks.

**Acceptance Criteria**
- Checklist covers all critical user roles.
- Each smoke-test item has a clear pass/fail outcome.
- Checklist is easy to execute after every deployment.

**Verification**
- Execute checklist against staging or local Compose deployment.

### Issue: Validate that `main` only receives reviewed, intentional merges

**Summary**
Reduce accidental merges into `main` by documenting branch and pull request controls.

**Scope**
- Branch policy.
- Pull request review expectations.
- Merge and revert procedure.

**Implementation Plan**
- Document Git workflow in `.agents/AGENTS.md`.
- Add GitHub branch protection recommendations to deployment or project docs.
- Require PR review for `main`.
- Document safe revert flow using `git revert -m 1`.

**Acceptance Criteria**
- Team has a documented rule for merging into `main`.
- Accidental merge recovery steps are documented.
- `main` remains deployable.

**Verification**
- Confirm GitHub branch protection settings if repository admin access is available.

## Backend Features

### Issue: Finish authentication and authorization hardening

**Summary**
Complete the authentication and authorization hardening work identified during security review.

**Scope**
- Token verification behavior.
- Role guards.
- User directory authorization.
- Error message consistency.
- JWT secret validation.
- Login protection.

**Implementation Plan**
- Review `api/app/dependencies.py`, auth router, user router, and route-level guards.
- Ensure expected auth failures do not become `500`.
- Add tests for missing, invalid, expired, inactive, and unauthorized cases.
- Track remaining hardening items as separate issues.

**Acceptance Criteria**
- Protected endpoints return correct `401` and `403` behavior.
- Role-based routes are explicitly guarded.
- Tests cover core auth failure paths.

**Verification**
- Run backend tests for auth and users.
- Manually test `/auth/me` with missing and invalid tokens.

### Issue: Restrict user directory endpoints to admin-only access

**Summary**
Restrict `GET /users` and `GET /users/{id}` to admin users only.

**Scope**
- Backend user list and detail routes.
- Frontend `/users`, `/users/new`, and `/users/:userId/edit` route guards.

**Implementation Plan**
- Change affected backend routes from `get_current_user` to `require_role(UserRole.ADMIN)`.
- Ensure frontend `PrivateRoute` uses `allowedRoles={['ADMIN']}`.
- Add authorization tests for staff access rejection.

**Acceptance Criteria**
- Staff receives `403` for user list and detail endpoints.
- Admin can still manage users.
- Non-admin direct frontend navigation redirects to dashboard.

**Verification**
- Run users authorization tests.
- Manually test with admin and staff accounts.

### Issue: Decide whether public registration is unsupported permanently or will become a future feature

**Summary**
Make the product decision for self-service registration explicit and keep frontend/backend behavior aligned.

**Scope**
- Public `/register` route.
- Auth context registration call.
- Backend `/auth/register` route decision.
- User onboarding documentation.

**Implementation Plan**
- Confirm account provisioning policy with stakeholders.
- If admin-only, keep public registration removed and document admin provisioning.
- If public registration is desired, create a separate feature issue for secure registration.

**Acceptance Criteria**
- Frontend no longer advertises unsupported registration.
- Backend route behavior matches product decision.
- README or deployment docs explain user provisioning.

**Verification**
- Search frontend for `/auth/register`, `RegisterPage`, and `/register`.
- Test login page messaging.

### Issue: Standardize API error responses across routers

**Summary**
Make API errors consistent across backend routers so clients can handle them predictably.

**Scope**
- Auth, users, items, categories, units, issues, issue items, stock transactions, audit, settings, and locations routes.

**Implementation Plan**
- Inventory current `HTTPException` usage and broad exception handlers.
- Define a standard error response shape.
- Replace expected `500` cases with specific status codes.
- Avoid exposing internal exception details to clients.

**Acceptance Criteria**
- Expected validation and business errors use consistent status codes.
- Unexpected errors return generic `500` messages.
- Frontend can display meaningful error messages.

**Verification**
- Add route/service tests for representative error cases.
- Run API smoke tests.

### Issue: Add request correlation IDs to logs and responses

**Summary**
Enable request correlation so API logs can be traced per request during deployment and support.

**Scope**
- Backend middleware.
- Response headers.
- Structured logs.

**Implementation Plan**
- Review existing `LoggingMiddleware`.
- Enable or improve request ID generation.
- Add `X-Request-ID` to responses.
- Ensure auth and route logs include request ID when available.

**Acceptance Criteria**
- Every API request gets a request ID.
- Logs include request ID.
- Response includes `X-Request-ID`.

**Verification**
- Call `/health` and confirm response header.
- Inspect logs for matching request ID.

### Issue: Review all `500` handling and convert expected validation/business failures to `400`, `401`, `403`, `404`, or `409`

**Summary**
Audit backend exception handling to prevent expected application states from surfacing as server errors.

**Scope**
- Repositories, services, and routers.
- Known paths around create/update/delete and relation linking.

**Implementation Plan**
- Search for `HTTP_500_INTERNAL_SERVER_ERROR`, `except Exception`, and generic `RuntimeError`.
- Classify each expected error path.
- Update services to raise specific `HTTPException` statuses.
- Add regression tests for fixed cases.

**Acceptance Criteria**
- Duplicate records use `409` or `400`.
- Unauthorized actions use `403`.
- Missing resources use `404`.
- Only unexpected failures use `500`.

**Verification**
- Run backend tests.
- Manually exercise key negative paths.

### Issue: Ensure staff ownership rules are consistently enforced for items, issues, stock transactions, and issue items

**Summary**
Verify and complete ownership enforcement for staff users across inventory workflows.

**Scope**
- Items owned by staff.
- Issues requested by staff.
- Issue items linked to owned items and accessible issues.
- Stock transactions involving owned items.

**Implementation Plan**
- Review service-level authorization in item, issue, issue item, and stock services.
- Add tests for staff accessing foreign records.
- Ensure frontend hides controls staff cannot use.

**Acceptance Criteria**
- Staff cannot read or mutate records outside allowed ownership.
- Admin retains full access.
- Tests cover key ownership boundaries.

**Verification**
- Run authorization tests.
- Manual staff/admin workflow test.

### Issue: Add pagination and search consistency across list endpoints

**Summary**
Align list endpoint pagination and search behavior so frontend tables behave consistently.

**Scope**
- Users, items, categories, units, locations, issues, issue items, stock transactions, stock levels, audit sessions.

**Implementation Plan**
- Document current list response shapes.
- Standardize `page`, `page_size`, `search`, and total fields where feasible.
- Update frontend consumers if response shapes change.
- Add tests for page bounds and search filters.

**Acceptance Criteria**
- List endpoints use predictable pagination parameters.
- Search behavior is documented.
- Frontend tables display totals and pages correctly.

**Verification**
- Run endpoint tests for list routes.
- Manual table pagination checks.

### Issue: Review audit-session workflows for permission and state-transition correctness

**Summary**
Ensure audit workflows enforce role access and valid state transitions.

**Scope**
- Audit session create/list/get/close.
- Audit scans.
- Reconciliation.
- Notes and reports.

**Implementation Plan**
- Review audit routes and service rules.
- Define allowed actions for `ADMIN` and `AUDITOR`.
- Validate transitions such as open to closed and blocked actions after close.
- Add tests for invalid transitions.

**Acceptance Criteria**
- Only authorized roles can access audit workflows.
- Closed sessions cannot accept invalid mutations.
- Invalid state transitions return expected status codes.

**Verification**
- Run audit service/route tests.
- Manual audit workflow smoke test.

### Issue: Add API smoke tests for deployment-critical workflows

**Summary**
Create backend smoke tests that validate the API is deployable after changes.

**Scope**
- Health endpoint.
- Login.
- Current user.
- Basic list endpoints.
- Representative create/update workflow if test data is available.

**Implementation Plan**
- Add smoke-test script or pytest suite.
- Keep tests independent from production data.
- Document how to run smoke tests locally and in deployment.

**Acceptance Criteria**
- Smoke tests can run against a fresh local environment.
- Failures clearly identify broken deployment-critical behavior.

**Verification**
- Run smoke tests against local or staging API.

## Frontend Features

### Issue: Ensure every protected route has matching frontend role guards

**Summary**
Align frontend route guards with backend authorization policy.

**Scope**
- Routes in `front-end/src/App.tsx`.
- Sidebar visibility in `Layout.tsx`.
- Direct URL access behavior.

**Implementation Plan**
- Compare frontend routes with backend role requirements.
- Add `allowedRoles` where needed.
- Confirm restricted routes redirect safely.

**Acceptance Criteria**
- Non-admin users cannot open admin-only views.
- Auditor-only routes match backend audit access.
- UI navigation does not advertise unavailable pages.

**Verification**
- Manual route checks with admin, staff, and auditor accounts.
- Frontend build passes.

### Issue: Remove or hide UI controls that backend authorization will reject

**Summary**
Make the UI role-aware so users do not see actions that backend will reject.

**Scope**
- Create/edit/delete buttons.
- Admin-only settings and user controls.
- Unit, location, category, item, issue, transaction, and audit actions.

**Implementation Plan**
- Audit pages for role-dependent controls.
- Hide or disable controls according to backend policy.
- Keep backend enforcement authoritative.

**Acceptance Criteria**
- Staff and auditor users only see appropriate actions.
- Admin-only mutations are not visible to non-admin users.
- Backend still rejects unauthorized direct API calls.

**Verification**
- Manual role-based UI pass.
- Frontend build passes.

### Issue: Confirm login behavior for expired, invalid, inactive, and missing-token sessions

**Summary**
Validate frontend behavior when authentication fails for common token and account states.

**Scope**
- Startup token validation.
- `/auth/me` failure handling.
- Login page errors.
- Logout and redirect behavior.

**Implementation Plan**
- Test missing token, expired token, invalid token, inactive user, and network error cases.
- Improve frontend messages if needed.
- Ensure invalid token clears local session.

**Acceptance Criteria**
- Invalid sessions redirect to login.
- Token is cleared when `/auth/me` fails.
- User sees clear, non-technical messaging.

**Verification**
- Manual browser tests.
- Add frontend tests if a test framework is introduced.

### Issue: Improve user-facing error handling for failed API requests

**Summary**
Standardize frontend error handling so users receive helpful messages for failed API requests.

**Scope**
- Fetch calls across dashboard, items, users, issues, transactions, audit, settings, categories, units, and locations.

**Implementation Plan**
- Inventory repeated fetch error patterns.
- Add a shared helper if it reduces meaningful duplication.
- Prefer backend `detail` when safe and available.
- Add network error fallback messages.

**Acceptance Criteria**
- Common API failures show clear messages.
- Network failures are distinguishable from validation errors.
- No page silently fails without feedback.

**Verification**
- Manual failure testing by stopping API or using invalid payloads.
- Frontend build passes.

### Issue: Confirm item-to-issue linking behavior for create, edit, change, and clear flows

**Summary**
Validate the item form behavior for linking items to issues.

**Scope**
- Item creation with issue selection.
- Item edit with existing issue link.
- Changing issue link.
- Clearing issue link.
- Duplicate link prevention.

**Implementation Plan**
- Review `ItemFormPage.tsx` and issue-item API behavior.
- Add API tests for duplicate and delete behavior.
- Add manual frontend test cases.

**Acceptance Criteria**
- Create with issue creates one issue-item link.
- Edit loads current issue link.
- Changing issue replaces previous link.
- Clearing issue removes existing link.

**Verification**
- Manual item form tests.
- Backend issue-item tests pass.

### Issue: Validate dashboard visibility for admin, staff, and auditor roles

**Summary**
Ensure the dashboard shows data appropriate to each role.

**Scope**
- Dashboard issue lists and stats.
- User name lookups.
- Role-based filtering.

**Implementation Plan**
- Define dashboard data policy per role.
- Review dashboard API calls and frontend filtering.
- Add backend tests where data scoping is service-side.

**Acceptance Criteria**
- Admin sees global dashboard data.
- Staff sees allowed staff-scoped data.
- Auditor sees only intended audit or read-only data.

**Verification**
- Manual dashboard checks for each role.

### Issue: Check mobile usability for main operational workflows

**Summary**
Verify that core workflows are usable on mobile-sized screens.

**Scope**
- Login.
- Dashboard.
- Items.
- Item form.
- Issues.
- Transactions.
- Audit scanning.

**Implementation Plan**
- Test pages at mobile viewport sizes.
- Fix overflowing text, inaccessible buttons, and unusable tables.
- Prioritize workflows used on warehouse or audit devices.

**Acceptance Criteria**
- Main pages render without horizontal layout breakage.
- Forms are usable on mobile.
- Audit scan flow is practical on mobile.

**Verification**
- Browser responsive testing.
- Optional Playwright screenshot checks if available.

### Issue: Confirm QR generation and PDF export behavior for active and inactive items

**Summary**
Validate QR code and PDF export behavior for item states.

**Scope**
- Single item QR generation.
- Bulk QR generation.
- PDF export.
- Active/inactive item filtering.

**Implementation Plan**
- Define whether inactive items should be exportable.
- Test QR payload correctness.
- Test PDF layout with many items.
- Document expected behavior.

**Acceptance Criteria**
- QR payload includes correct item identifiers.
- Bulk export handles expected item counts.
- Inactive item behavior is explicit and consistent.

**Verification**
- Manual QR generation and PDF download.
- Scan generated QR payload.

### Issue: Add frontend build verification to release process

**Summary**
Make `npm run build` a required release verification step.

**Scope**
- Local release checklist.
- CI/CD if available.
- Deployment docs.

**Implementation Plan**
- Add `npm run build` to final release checklist.
- Ensure Vite build uses production API base configuration.
- Document common build failures.

**Acceptance Criteria**
- Release process requires frontend build pass.
- Build command is documented.
- Build artifacts are generated successfully.

**Verification**
- Run `npm run build` in `front-end`.

## Security

### Issue: Require non-empty, strong `JWT_SECRET_KEY` in production

**Summary**
Prevent the API from starting in production with an empty or weak JWT signing key.

**Scope**
- Backend settings validation.
- Deployment docs.
- Production environment variables.

**Implementation Plan**
- Add startup validation for `JWT_SECRET_KEY`.
- Enforce minimum length or entropy guidance.
- Allow relaxed validation only in explicit local development mode if necessary.
- Document key generation.

**Acceptance Criteria**
- Production startup fails without a valid JWT secret.
- Deployment docs describe required secret.
- Tests cover missing secret behavior if feasible.

**Verification**
- Start API with missing secret and confirm failure.
- Start API with valid secret and confirm success.

### Issue: Add login rate limiting or lockout protection

**Summary**
Reduce brute-force risk on the login endpoint.

**Scope**
- `POST /auth/login`.
- Failed login tracking.
- IP or account-based limits.

**Implementation Plan**
- Choose rate limiting approach suitable for Docker deployment.
- Add per-IP and/or per-email throttling.
- Log repeated failed attempts.
- Document operational considerations.

**Acceptance Criteria**
- Repeated failed logins are throttled or temporarily blocked.
- Legitimate users receive clear messaging.
- Admins can identify repeated failures in logs.

**Verification**
- Repeated failed login test.
- Successful login after allowed window.

### Issue: Standardize auth failure messages to avoid account-state leakage

**Summary**
Avoid revealing whether a user exists, password is wrong, or account is inactive through login responses.

**Scope**
- Login service.
- Token verification responses.
- Frontend display messages.

**Implementation Plan**
- Use generic login failure message for invalid credentials and inactive accounts if policy allows.
- Keep detailed reason in server logs only.
- Ensure frontend does not display raw technical auth errors.

**Acceptance Criteria**
- Login failures do not reveal account existence.
- Token failures do not expose JWT library details.
- Logs retain enough diagnostic detail.

**Verification**
- Test invalid email, invalid password, inactive account, and expired token.

### Issue: Decide whether JWT stays in `localStorage` temporarily or moves to secure `HttpOnly` cookies

**Summary**
Make a documented decision on token storage and plan the migration if needed.

**Scope**
- Frontend auth storage.
- Backend auth delivery.
- CSRF considerations if cookies are used.

**Implementation Plan**
- Assess current internal deployment risk.
- Choose short-term and long-term token storage strategy.
- If moving to cookies, design login/logout/session flow.
- Document risk if keeping `localStorage`.

**Acceptance Criteria**
- Token storage strategy is documented.
- Any required migration work is tracked.
- Security tradeoffs are explicit.

**Verification**
- Review with deployment/security owner.

### Issue: Add production security headers intentionally and verify they do not break the app

**Summary**
Add browser security headers for production after validating they are compatible with the app.

**Scope**
- Frontend Nginx config.
- Content Security Policy.
- Frame, content type, referrer, and permissions headers.

**Implementation Plan**
- Define required headers and expected behavior.
- Test with frontend build and runtime API calls.
- Avoid overly strict CSP until all scripts/assets are accounted for.
- Document header decisions.

**Acceptance Criteria**
- Production frontend sends approved security headers.
- App still loads and functions.
- No console CSP violations for normal usage.

**Verification**
- Inspect response headers in browser or curl.
- Run frontend smoke test.

### Issue: Review CORS configuration for exact deployment origins

**Summary**
Lock CORS configuration to approved frontend origins.

**Scope**
- `CORS_ORIGINS` environment variable.
- FastAPI CORS middleware.
- Local and production configs.

**Implementation Plan**
- Document allowed local and production origins.
- Ensure production does not use wildcard origins.
- Test API requests from approved and unapproved origins.

**Acceptance Criteria**
- Production CORS only allows approved frontend origin.
- Local development origin remains documented.
- Browser API calls work from the approved frontend.

**Verification**
- Manual browser test.
- Optional curl/browser origin checks.

### Issue: Confirm Docker network exposure only allows intended public services

**Summary**
Ensure Docker networking exposes only required services to the host/network.

**Scope**
- MySQL service.
- API service.
- Frontend service.
- Docker networks.

**Implementation Plan**
- Review `docker-compose.yaml` ports and networks.
- Confirm MySQL is internal only.
- Decide whether API should be host-exposed or only proxied by frontend.
- Document final exposure model.

**Acceptance Criteria**
- MySQL is not publicly exposed.
- Only intended HTTP services are bound to host ports.
- Docker network design is documented.

**Verification**
- Run `docker compose ps`.
- Test port access from host and another LAN client.

### Issue: Remove tracked Python bytecode files from future commits if possible

**Summary**
Clean up tracked Python bytecode files and prevent future bytecode churn.

**Scope**
- `api/**/__pycache__`.
- `.gitignore`.
- Repository history going forward.

**Implementation Plan**
- Identify tracked `.pyc` files.
- Confirm `.gitignore` excludes bytecode.
- Remove tracked bytecode with `git rm --cached` if approved.
- Ensure future test/build runs do not modify tracked bytecode.

**Acceptance Criteria**
- Bytecode files are not tracked in future commits.
- Running Python tests does not dirty the worktree with `.pyc` changes.

**Verification**
- Run `git ls-files '*.pyc'`.
- Run backend syntax/tests and check `git status`.

### Issue: Review logs to avoid leaking passwords, tokens, or authorization headers

**Summary**
Ensure logging does not expose secrets or sensitive authentication material.

**Scope**
- Middleware request logging.
- Auth/login logging.
- Service error logging.
- Headers and payloads.

**Implementation Plan**
- Search for logging of headers, request bodies, tokens, passwords, and password hashes.
- Redact `Authorization`, cookies, passwords, and secrets.
- Document logging conventions.

**Acceptance Criteria**
- Logs do not contain bearer tokens or passwords.
- Sensitive headers are redacted.
- Debug logs remain useful without secrets.

**Verification**
- Trigger login and protected API calls.
- Inspect logs for leaked secrets.

### Issue: Add backup and restore validation before production use

**Summary**
Prove that backups can be restored before relying on them in production.

**Scope**
- MySQL backup.
- Restore process.
- Backup retention.
- Settings backup action if available.

**Implementation Plan**
- Document backup command.
- Document restore command.
- Run restore into a fresh database/container.
- Verify app behavior after restore.

**Acceptance Criteria**
- Backup can be created.
- Backup can be restored.
- Restored app passes smoke tests.

**Verification**
- Perform backup and restore dry run.

## Data Model And Migrations

### Issue: Treat `api/db/migrations` as the source of truth for schema evolution

**Summary**
Establish migrations as the canonical path for database schema changes.

**Scope**
- Migration files.
- Schema SQL.
- Deployment migration script.

**Implementation Plan**
- Document migration naming and execution rules.
- Ensure deployments run migrations before API startup or as a clear manual step.
- Avoid direct production schema edits outside migrations.

**Acceptance Criteria**
- New schema changes require migration files.
- Deployment docs explain migration execution.
- Team knows where schema truth lives.

**Verification**
- Run migration script against fresh database.

### Issue: Confirm `api/db/schema.sql` and migrations do not diverge

**Summary**
Keep fresh install schema and migration-based schema aligned.

**Scope**
- `api/db/schema.sql`.
- `api/db/migrations`.
- Any database dumps used for local testing.

**Implementation Plan**
- Compare fresh schema with migration result.
- Decide whether `schema.sql` is generated or manually maintained.
- Document update process.

**Acceptance Criteria**
- Fresh database from migrations matches expected schema.
- `schema.sql` purpose is documented.
- Drift is detected before deployment.

**Verification**
- Build two fresh databases and compare table definitions.

### Issue: Add migration tests or dry-run instructions for a fresh database

**Summary**
Provide a reliable way to validate migrations before deployment.

**Scope**
- Local Docker MySQL.
- Migration script.
- Fresh database validation.

**Implementation Plan**
- Add documented dry-run steps.
- Optionally add a test script that creates a temporary database and runs migrations.
- Include verification queries.

**Acceptance Criteria**
- Developer can validate migrations from a clean state.
- Failed migration produces clear output.

**Verification**
- Execute dry-run instructions locally or in CI.

### Issue: Document seed data strategy for categories, units, locations, settings, and admin user

**Summary**
Define which data is seeded automatically and which data is manually administered.

**Scope**
- Settings row.
- Admin bootstrap.
- Categories, units, and locations.
- Sample data.

**Implementation Plan**
- Review current schema defaults and admin script.
- Decide required production seed data.
- Document sample data vs production seed behavior.

**Acceptance Criteria**
- Fresh production database has required settings/admin state.
- Sample data is not accidentally loaded into production.
- Seed process is documented.

**Verification**
- Start fresh database and inspect required rows.

### Issue: Review foreign-key behavior for soft-deleted users, items, categories, units, and issues

**Summary**
Confirm that soft delete behavior preserves history without breaking active workflows.

**Scope**
- Users.
- Items.
- Categories.
- Units.
- Issues.
- Related stock, audit, and issue records.

**Implementation Plan**
- Review foreign keys and delete/deactivate logic.
- Confirm list queries hide inactive/deleted records appropriately.
- Ensure historical records remain readable.
- Add tests for delete/deactivate with dependencies.

**Acceptance Criteria**
- Soft-deleted records do not break historical views.
- Active workflows do not use inactive records unless explicitly allowed.
- Delete/deactivate endpoints return clear dependency warnings.

**Verification**
- Run dependency and soft-delete tests.

### Issue: Decide whether one item can belong to multiple issues or only one issue in the UI

**Summary**
Clarify item-to-issue relationship rules and align frontend behavior with the data model.

**Scope**
- `issue_items` table.
- Item form issue selector.
- Issue detail pages.

**Implementation Plan**
- Confirm business rule with stakeholders.
- If single issue per item in UI, enforce or document the UI limitation.
- If multiple issues are valid, adjust UI to display/manage multiple links.
- Add database constraint only if business rule requires it.

**Acceptance Criteria**
- Business rule is documented.
- UI behavior matches rule.
- Backend prevents invalid state if needed.

**Verification**
- Test item linked to zero, one, and multiple issues according to final policy.

### Issue: Add indexes for high-use filters if performance testing shows slow queries

**Summary**
Improve database performance after measuring real or representative query behavior.

**Scope**
- Item search/filter columns.
- Issue status and requestor filters.
- Stock transaction filters.
- Audit session/scans filters.

**Implementation Plan**
- Identify high-use queries.
- Run `EXPLAIN` on slow queries.
- Add indexes via migration only where justified.
- Document expected performance improvement.

**Acceptance Criteria**
- Slow high-use queries have measured evidence.
- Index migrations are added and tested.
- No unnecessary indexes are added.

**Verification**
- Compare query plans before and after index changes.

## Observability And Operations

### Issue: Define required health checks for API, frontend, and MySQL

**Summary**
Document and validate service health checks used by Docker Compose and operators.

**Scope**
- API `/health`.
- Frontend Nginx health.
- MySQL healthcheck.

**Implementation Plan**
- Review Docker health checks.
- Confirm endpoints and commands are accurate.
- Add troubleshooting steps for unhealthy services.

**Acceptance Criteria**
- Each service has a meaningful health check.
- Health check failures are actionable.
- Deployment docs explain how to inspect health.

**Verification**
- Run `docker compose ps`.
- Force or observe health status changes if practical.

### Issue: Add structured logging conventions for authentication, authorization, writes, and audit activity

**Summary**
Make logs consistent and useful for operational support.

**Scope**
- Auth failures.
- Authorization denials.
- Create/update/delete operations.
- Audit events.

**Implementation Plan**
- Define common log fields.
- Apply conventions in shared dependencies and key services.
- Avoid logging secrets.
- Include request ID when available.

**Acceptance Criteria**
- Logs include actor, action, entity, result, and request ID where applicable.
- Sensitive fields are redacted.
- Log messages are consistent enough to search.

**Verification**
- Exercise representative workflows and inspect logs.

### Issue: Document how to inspect container logs during deployment

**Summary**
Add operator instructions for checking Docker logs.

**Scope**
- API logs.
- Frontend logs.
- MySQL logs.
- Common failure patterns.

**Implementation Plan**
- Add log inspection commands to deployment docs.
- Include examples for startup, health, auth, and database failures.

**Acceptance Criteria**
- Operator can inspect logs for each service.
- Commands are copy-pasteable.
- Common issues have next-step hints.

**Verification**
- Run documented commands in local or staging deployment.

### Issue: Document backup location, retention, restore command, and verification process

**Summary**
Create complete operational documentation for database backups.

**Scope**
- Backup destination.
- Retention period.
- Restore process.
- Verification after restore.

**Implementation Plan**
- Define backup storage location.
- Define retention policy.
- Document backup and restore commands.
- Add post-restore smoke test steps.

**Acceptance Criteria**
- Backup and restore instructions are complete.
- Retention policy is documented.
- Restore verification is required.

**Verification**
- Perform backup and restore dry run.

### Issue: Add monitoring notes for disk usage, database availability, API latency, and failed logins

**Summary**
Document the minimum operational signals needed to run the app safely.

**Scope**
- Host disk usage.
- MySQL availability.
- API latency and errors.
- Failed login counts.
- Container restarts.

**Implementation Plan**
- Define minimum monitoring checklist.
- Add manual commands or tool-agnostic guidance.
- Identify thresholds that require action.

**Acceptance Criteria**
- Deployment owner knows what to monitor.
- Critical failure signals are documented.
- Failed login visibility is included.

**Verification**
- Review monitoring checklist with deployment owner.

## Documentation

### Issue: Keep README local development setup accurate

**Summary**
Maintain README instructions for local developer setup.

**Scope**
- MySQL setup.
- Backend virtual environment.
- Frontend Vite setup.
- Local env files.

**Implementation Plan**
- Review README after setup or dependency changes.
- Update commands and environment examples.
- Keep local and Docker instructions separate.

**Acceptance Criteria**
- New developer can run app locally from README.
- Commands match current codebase.
- Required env vars are documented.

**Verification**
- Follow README from a clean local setup or checklist review.

### Issue: Keep DEPLOYMENT.md production deployment steps accurate

**Summary**
Maintain deployment documentation as the production path evolves.

**Scope**
- Docker Compose.
- Environment variables.
- DNS/hostnames.
- Firewall.
- Migrations.
- Admin bootstrap.
- Smoke tests.

**Implementation Plan**
- Update deployment docs with each deployment-relevant change.
- Keep commands copy-pasteable.
- Add troubleshooting notes as issues are discovered.

**Acceptance Criteria**
- Deployment docs match current Compose and app behavior.
- Production owner can deploy without chat context.

**Verification**
- Execute deployment steps in staging or local production-like environment.

### Issue: Maintain this checklist after every core feature or security change

**Summary**
Keep `.agents/BLUEPRINT_UPDATE_CHECKLIST.md` current as the app evolves.

**Scope**
- Core feature changes.
- Security changes.
- Deployment changes.
- Data model changes.

**Implementation Plan**
- Add checklist updates to PR review expectations.
- Use blueprint-maintainer skill for relevant changes.
- Remove obsolete tasks only with documented decisions.

**Acceptance Criteria**
- Checklist reflects current deploy readiness.
- Completed work is marked only after verification.
- New risks are added promptly.

**Verification**
- Review checklist during release preparation.

### Issue: Record user-visible functional changes in `CHANGELOG_BLUEPRINT.md`

**Summary**
Track meaningful functional changes in a readable changelog.

**Scope**
- Feature additions.
- Behavior changes.
- Security changes.
- Deployment changes.
- Data model changes.

**Implementation Plan**
- Add changelog entry for every core change.
- Include user impact, technical notes, verification, and follow-up.
- Keep entries reverse chronological.

**Acceptance Criteria**
- Changelog explains what changed and why it matters.
- Entries include verification status.
- Deployment owner can review recent changes quickly.

**Verification**
- Review changelog before PR merge or release.

### Issue: Add short troubleshooting notes for common deployment and authentication failures

**Summary**
Document fixes for common failures during deployment and login.

**Scope**
- API cannot connect to database.
- Missing or invalid JWT secret.
- CORS failures.
- Invalid token.
- Inactive user.
- Frontend cannot reach API.

**Implementation Plan**
- Collect known failure modes from recent work.
- Add troubleshooting section to deployment docs.
- Include symptom, likely cause, and fix.

**Acceptance Criteria**
- Common deployment/auth failures are documented.
- Operators can resolve first-line issues without source-code inspection.

**Verification**
- Review troubleshooting notes against known incidents.

## Final Pre-Deploy Gate

### Issue: Backend tests pass

**Summary**
Require backend tests to pass before deployment.

**Scope**
- Pytest suite.
- Auth, authorization, services, and repositories.

**Implementation Plan**
- Confirm test dependencies are documented.
- Run backend tests.
- Fix or document any failing tests.

**Acceptance Criteria**
- Backend test command passes.
- Test failures block deployment unless explicitly waived.

**Verification**
- Run `pytest` from the backend test environment.

### Issue: Frontend build passes

**Summary**
Require frontend production build to pass before deployment.

**Scope**
- TypeScript build.
- Vite production build.

**Implementation Plan**
- Run `npm run build`.
- Fix TypeScript or bundling failures.
- Document known warnings separately.

**Acceptance Criteria**
- Frontend build exits successfully.
- Build artifacts are produced.

**Verification**
- Run `npm run build` in `front-end`.

### Issue: Docker Compose build and startup pass from a clean environment

**Summary**
Validate that the app can build and start cleanly with Docker Compose.

**Scope**
- MySQL.
- API.
- Frontend.
- Volumes and networks.

**Implementation Plan**
- Start from clean or isolated Docker volumes.
- Build images.
- Start services.
- Check health status.

**Acceptance Criteria**
- `docker compose up -d --build` succeeds.
- All services become healthy or operational.
- Frontend and API are reachable.

**Verification**
- Run Docker Compose deployment in local/staging environment.

### Issue: Fresh database migration succeeds

**Summary**
Ensure schema migrations work on a fresh database.

**Scope**
- Migration script.
- Initial schema.
- Required settings row.

**Implementation Plan**
- Create fresh database.
- Run migrations.
- Inspect resulting tables and required seed records.

**Acceptance Criteria**
- Migration completes without errors.
- Required tables and settings exist.
- API can connect to migrated database.

**Verification**
- Run migration dry run or fresh Compose startup.

### Issue: Admin bootstrap succeeds

**Summary**
Confirm the admin bootstrap process creates or preserves the admin user correctly.

**Scope**
- `api/scripts/create_admin.py`.
- Environment variables.
- API container startup.

**Implementation Plan**
- Verify required admin env vars.
- Run bootstrap on fresh database.
- Run bootstrap again to confirm idempotent behavior.

**Acceptance Criteria**
- Admin user exists after startup.
- Re-running bootstrap does not duplicate admin user.
- Missing env vars fail clearly.

**Verification**
- Run create-admin script in local/staging environment.

### Issue: Manual smoke test passes for each role

**Summary**
Execute role-based manual smoke tests before deployment signoff.

**Scope**
- Admin.
- Staff.
- Auditor.

**Implementation Plan**
- Use final smoke-test checklist.
- Log in as each role.
- Verify allowed and denied workflows.

**Acceptance Criteria**
- Admin workflows pass.
- Staff workflows pass with correct restrictions.
- Auditor workflows pass with correct restrictions.

**Verification**
- Complete smoke-test checklist and record result.

### Issue: Backup and restore procedure is verified

**Summary**
Verify backup and restore before production deployment.

**Scope**
- MySQL dump.
- Restore target.
- App validation after restore.

**Implementation Plan**
- Create backup from test/staging database.
- Restore to a fresh database.
- Run smoke tests after restore.

**Acceptance Criteria**
- Backup file is created successfully.
- Restore succeeds.
- Restored app passes smoke tests.

**Verification**
- Execute documented backup and restore commands.

### Issue: Deployment owner signs off on current known risks

**Summary**
Require explicit signoff on unresolved risks before deployment.

**Scope**
- Security risks.
- Operational risks.
- Known bugs.
- Deferred checklist items.

**Implementation Plan**
- Summarize unresolved risks from blueprint checklist and changelog.
- Review with deployment owner.
- Record signoff decision and date.

**Acceptance Criteria**
- Known risks are visible.
- Deployment owner approves release or blocks deployment.
- Signoff is documented.

**Verification**
- Add signoff note to deployment record or release checklist.
