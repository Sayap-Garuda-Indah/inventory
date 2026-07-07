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
