# Issue Implementation Prompt Template

Use this template when asking an agent to implement one GitHub issue from the blueprint issue set. Replace every placeholder before starting work.

```markdown
# Task

Implement GitHub issue `<ISSUE_NUMBER>`: `<ISSUE_TITLE>`.

Issue URL: `<ISSUE_URL>`

## Goal

Complete the issue end-to-end in this repository while keeping the change scoped, tested, and ready for review.

## Required Context

- Read the full GitHub issue body, labels, acceptance criteria, implementation sequence, dependencies, and related issues.
- Read `.agents/AGENTS.md`.
- Read `.agents/BLUEPRINT_UPDATE_CHECKLIST.md`.
- If the issue came from the blueprint, read the matching section in `.agents/docs/BLUEPRINT_IMPLEMENTATION_DETAIL.md`.
- For security, authentication, authorization, data model, or deployment changes, inspect related existing code and documentation before editing.

## Scope

Implement only the behavior required by this issue.

In scope:

- Tests or verification needed for the acceptance criteria.
- Documentation or blueprint updates only when the implementation changes behavior, deployment assumptions, or readiness status.

Out of scope:

- Unrelated refactors.
- Cosmetic changes unrelated to the issue.
- Reverting existing user work.
- Adding unsupported product behavior not requested by the issue.

## Implementation Rules

- Start by checking `git status --short --branch`.
- Search with `rg` before changing code.
- Follow the existing backend/frontend patterns in this repository.
- Keep route-level authorization explicit.
- Keep frontend route guards aligned with backend authorization.
- Do not commit secrets, credentials, production `.env` values, tokens, or dumps.
- Preserve existing public API behavior unless the issue explicitly changes it.
- For expected backend failures, return specific `400`, `401`, `403`, `404`, or `409` responses instead of generic `500`.
- Update `.agents/CHANGELOG_BLUEPRINT.md` for meaningful user-visible, security, data, deployment, or core behavior changes.
- Update `.agents/BLUEPRINT_UPDATE_CHECKLIST.md` only if this issue changes readiness assumptions or completes a checklist item.

## Expected Deliverables

- Code changes implementing the issue.
- Tests or clear manual verification steps.
- Any required docs or blueprint updates.
- A concise final summary with changed areas and verification results.

## Suggested Workflow

1. Confirm current branch and working tree status.
2. Read the GitHub issue and related blueprint section.
3. Inspect the affected code paths.
4. Identify the smallest safe implementation plan.
5. Make focused changes.
6. Run relevant tests or build commands.
7. Update docs/checklists/changelog if needed.
8. Re-check `git status --short --branch`.
9. Summarize what changed, what was verified, and any remaining risk.

## Verification Expectations

Run the most relevant commands for the changed area:

- Backend: `<BACKEND_TEST_COMMAND_OR_N/A>`
- Frontend: `<FRONTEND_BUILD_OR_TEST_COMMAND_OR_N/A>`
- Database/migrations: `<MIGRATION_VERIFICATION_OR_N/A>`
- Manual smoke test: `<MANUAL_STEPS_OR_N/A>`

If a verification command cannot be run, explain why and describe the remaining risk.

## Completion Criteria

The issue is complete only when:

- All acceptance criteria are satisfied.
- The implementation is scoped to this issue.
- Relevant tests or verification steps pass.
- Documentation/checklist/changelog updates are made when required.
- No unrelated work is included.
```

## Optional PR Prompt

Use this shorter prompt after implementation if the user asks for a commit and PR.

```markdown
Commit the completed implementation for GitHub issue `<ISSUE_NUMBER>` and create a pull request.

Before committing:

- Show `git status --short --branch`.
- Review the diff for unrelated changes.
- Use a focused commit message referencing the issue.
- Push the current branch.
- Create a PR that links the issue and includes summary, verification, and risks.

Do not include unrelated local changes.
```
