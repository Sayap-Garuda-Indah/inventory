# Changelog Blueprint

Use this file to record changes to core app features, behavior, data model, security posture, deployment flow, and agent-maintained documentation.

Follow this format for every meaningful change:

```markdown
## YYYY-MM-DD - Short Change Title

Type: Feature | Fix | Security | Data Model | Frontend | Backend | Deployment | Docs | Maintenance
Branch: branch-name
Related PR/Issue: #number or N/A

Summary:
- Concise explanation of what changed.

User Impact:
- What users, admins, or operators will notice.

Technical Notes:
- Important implementation details, migrations, config changes, or compatibility notes.

Verification:
- Commands, tests, builds, or manual checks performed.

Follow-Up:
- Remaining work, risks, or future issue references.
```

## 2026-07-03 - Agent Blueprint Workspace Added

Type: Docs
Branch: chore/add-agents-blueprint-docs
Related PR/Issue: N/A

Summary:
- Added `.agents` documentation for deployment readiness planning, changelog maintenance, blueprint-maintainer skill guidance, and repository-specific agent instructions.

User Impact:
- Developers and agents have a clearer shared process for tracking readiness, security, data model, frontend, backend, and deployment work.

Technical Notes:
- No runtime application code changed.

Verification:
- Documentation files created under `.agents`.

Follow-Up:
- Keep this changelog updated whenever core features or deployment-relevant behavior changes.

## 2026-07-07 - Item Status And Condition Added

Type: Feature | Data Model | Backend | Frontend
Branch: dev
Related PR/Issue: #36

Summary:
- Added operational item `status` and physical `condition` fields across item create/edit/list/detail, stock transactions, and audit reconciliation.
- Added stock transaction before/after status and condition tracking for item-state changes.

User Impact:
- Users can set item status and condition on item forms and optionally update them during stock transactions.
- Auditors can see current item status and condition in scan history and reconciliation/report views.

Technical Notes:
- Added migration `0002_item_status_condition.sql` for existing databases and updated the baseline schema for fresh installs.
- Defaults are `AVAILABLE` status and `GOOD` condition.

Verification:
- Pending local backend tests and frontend build.

Follow-Up:
- Confirm whether status/condition changes need stricter role-specific authorization or reporting filters.

## 2026-07-07 - User Directory Restricted To Admins

Type: Security | Backend | Frontend
Branch: dev
Related PR/Issue: #39

Summary:
- Made user list/detail route dependencies explicitly require the `ADMIN` role.
- Confirmed frontend user-management routes and sidebar visibility are admin-only.
- Added regression coverage for staff rejection and admin access.

User Impact:
- Non-admin users cannot access the full user directory or user detail data.

Technical Notes:
- `GET /users` and `GET /users/{id}` now use `require_role(UserRole.ADMIN)` directly for the request user dependency.

Verification:
- `cd api && $env:DEBUG='false'; ..\.venv\Scripts\python.exe -m pytest test\test_users_authorization.py`
- `cd front-end && npm run build`

Follow-Up:
- If staff identity lookup is needed later, create a separate minimal endpoint with limited fields.

## 2026-07-07 - Token Storage Hardened Away From localStorage

Type: Security | Frontend | Deployment | Documentation
Branch: dev
Related PR/Issue: #41

Summary:
- Changed frontend bearer-token persistence from `localStorage` to `sessionStorage`.
- Added startup cleanup for legacy `localStorage` token values left by older frontend builds.
- Added production Nginx CSP and browser security headers as compensating XSS controls.
- Documented the short-term token-storage tradeoff and long-term `HttpOnly` cookie target.

User Impact:
- Users may need to sign in again when opening a new browser tab/session.
- Token persistence is reduced, lowering exposure from long-lived browser storage.

Technical Notes:
- `sessionStorage` is still JavaScript-accessible and is not equivalent to `HttpOnly` cookies.
- Full cookie-based auth will require backend session delivery, frontend request changes, and CSRF protection.

Verification:
- `rg -n "localStorage|sessionStorage|cacheLocation|Content-Security-Policy|X-Frame-Options|Referrer-Policy|Permissions-Policy" front-end/src front-end/nginx.conf README.md DEPLOYMENT.md .agents`
- `cd front-end && npm run build`

Follow-Up:
- Implement secure `HttpOnly`, `Secure`, `SameSite` cookie-based auth with CSRF protection when the API/frontend auth contract is ready for a broader migration.
- Run browser-level CSP smoke tests before marking production security headers fully complete.
