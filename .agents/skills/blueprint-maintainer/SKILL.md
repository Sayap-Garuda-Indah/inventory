# Blueprint Maintainer Skill

Use this skill when maintaining SGI Inventory planning, readiness, changelog, deployment, or agent instruction documents.

## Purpose

The blueprint maintainer keeps project planning artifacts accurate as the codebase changes. The goal is to prevent deployment readiness, security risks, data model decisions, and core workflow changes from living only in chat or commit messages.

## When To Use

Use this skill when:

- A backend or frontend core workflow changes.
- Authentication, authorization, security headers, CORS, token handling, or secrets policy changes.
- Database schema, migrations, seed data, or soft-delete behavior changes.
- Deployment, Docker Compose, environment variables, or operational procedures change.
- A new known risk or deploy blocker is discovered.
- A deploy-readiness task is completed or added.

## Responsibilities

- Update `.agents/BLUEPRINT_UPDATE_CHECKLIST.md` when project readiness changes.
- Update `.agents/CHANGELOG_BLUEPRINT.md` for meaningful functional or operational changes.
- Keep `.agents/AGENTS.md` aligned with repository practices.
- Prefer concise, actionable checklist entries over vague notes.
- Include verification details whenever a changelog entry records a completed change.
- Preserve historical changelog entries.

## Maintenance Workflow

1. Inspect the changed files and identify whether the change affects behavior, security, data model, deployment, or documentation.
2. Add or update checklist items if the change creates new readiness work or closes existing work.
3. Add a changelog entry for core app functionality, security posture, data model, deployment flow, or operational behavior.
4. Include branch name, related issue or PR if known, user impact, technical notes, verification, and follow-up.
5. Keep language clear enough for both developers and deployment owners.

## Changelog Entry Rules

- Use reverse chronological order.
- Use dates in `YYYY-MM-DD` format.
- Keep each entry focused on one logical change.
- Mention migrations, environment variables, or deployment steps if they are required.
- If verification was not run, say so plainly.

## Checklist Rules

- Do not mark items complete unless the work is actually done and verified.
- Split broad work into smaller checkable tasks.
- Keep security and deployment blockers visible.
- Remove obsolete items only when the decision is documented elsewhere.

## Style

- Use English.
- Prefer direct engineering language.
- Avoid marketing language.
- Avoid vague phrases such as "improve system" unless followed by a concrete action.
- Keep documents useful for the next person who opens the repository without chat context.
