# Agent Instructions For SGI Inventory

These instructions apply to agents working in this repository.

## Project Context

SGI Inventory is an internal inventory management system with:

- FastAPI backend in `api`
- React/Vite frontend in `front-end`
- MySQL 8 database
- Docker Compose deployment
- JWT authentication and role-based authorization

Primary roles are `ADMIN`, `STAFF`, and `AUDITOR`.

## Working Rules

- Read the relevant code before changing behavior.
- Prefer existing project patterns over new abstractions.
- Keep edits scoped to the requested issue.
- Do not revert user work or unrelated changes.
- Do not commit secrets, real production `.env` values, tokens, dumps, or generated credentials.
- Use `rg` for searching and `git status --short --branch` before and after work.
- Use focused tests for backend authorization, authentication, and service behavior.
- Run `npm run build` in `front-end` for frontend changes when feasible.
- Record meaningful core app changes in `.agents/CHANGELOG_BLUEPRINT.md`.
- Update `.agents/BLUEPRINT_UPDATE_CHECKLIST.md` when readiness assumptions change.

## Branching

- Create a dedicated branch for each logical change.
- Prefer branch names like:
  - `fix/auth-error-status-codes`
  - `security/restrict-user-directory`
  - `docs/update-deployment-blueprint`
  - `feature/audit-report-export`
- Keep `main` deployable.
- Avoid force-pushing shared branches unless explicitly approved.

## Backend Guidelines

- Keep route-level authorization explicit.
- Enforce business authorization in services where data ownership matters.
- Expected failures should not become `500`.
- Use `401` for invalid or missing authentication.
- Use `403` for authenticated users without permission.
- Use `404` when a resource is unavailable or intentionally hidden.
- Use `409` for conflicts such as uniqueness or duplicate relation errors.
- Do not expose passwords, password hashes, JWTs, or raw token verification details in responses or logs.
- Add or update tests for auth, ownership, and state transitions.

## Frontend Guidelines

- Keep frontend route guards aligned with backend authorization.
- Hide controls that the current role cannot use.
- Preserve the operational dashboard style already used by the app.
- Prefer clear, compact workflow UI over decorative pages.
- Avoid adding public flows that the backend does not support.
- Use existing UI components from `front-end/src/components/UI` when possible.

## Database And Migrations

- Treat migrations as the source of truth for schema evolution.
- Keep schema files and migration docs in sync.
- Avoid destructive schema changes without a rollback or migration strategy.
- Preserve historical references where soft delete is used.

## Deployment Notes

- Docker Compose is the expected deployment path.
- Production configuration belongs in environment variables, not committed files.
- Verify API health, frontend load, database connectivity, admin bootstrap, and role-based login before deployment signoff.

## Documentation Responsibilities

- `BLUEPRINT_UPDATE_CHECKLIST.md` tracks readiness work.
- `CHANGELOG_BLUEPRINT.md` records meaningful feature, security, data, deployment, and behavior changes.
- `docs/ISSUE_IMPLEMENTATION_PROMPT_TEMPLATE.md` provides the reusable prompt for implementing one GitHub issue at a time.
- `skills/blueprint-maintainer/SKILL.md` describes how an agent should maintain these files.
