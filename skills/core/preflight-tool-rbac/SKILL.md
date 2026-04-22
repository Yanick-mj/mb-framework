---
name: core/preflight-tool-rbac
description: Mandatory check before using any external tool — stage-aware RBAC via scripts/v2_2/rbac.py
version: 1
used_by: [fe-dev, be-dev, devops, lead-dev, architect, quick-flow, verifier]
---

## Rule

BEFORE any external-tool action (cloud API write, database mutation, deploy,
third-party service call), the agent MUST call the preflight RBAC check.
If the check denies, STOP and escalate to the user — do not proceed.

This skill implements Feature F of v2.2.

## What counts as an "external tool"

- Supabase / Postgres writes (migrations, RLS, edge functions)
- Cloud deploys (Vercel, Netlify, EAS)
- Stripe / billing APIs
- Email / SMS providers (Resend, Twilio)
- Auth providers (Clerk, Auth0)
- Paid AI APIs (OpenAI, Anthropic, etc.)
- Anything that costs money, changes production state, or is hard to undo

NOT external tools: reading the filesystem, running tests, local grep,
static analysis, non-mutating CLI tools.

## Preflight check

At the start of any task that may touch an external tool:

```bash
PYTHONPATH="${MB_DIR:-.claude/mb}" python3 -c "
from scripts.v2_2 import rbac
ok, reason = rbac.check(agent='AGENT_NAME', tool='TOOL_ID', action='ACTION')
if not ok:
    print(f'BLOCKED: {reason}')
    exit(1)
print('OK')
"
```

Agents must include this output in their response under `## Preflight`:

```markdown
## Preflight
- rbac.check(agent='be-dev', tool='supabase', action='migration_apply') → OK
- stage=pmf, tool allowed for be-dev at pmf per memory/permissions.yaml
```

## Stage defaults

| Stage | Default posture |
|-------|-----------------|
| discovery | Almost everything DENIED. Only read operations. |
| mvp | Permissive on local dev tools, DENIED on production. |
| pmf | Stage-aware: be-dev allowed on supabase, devops on deploy tools, others scoped. |
| scale | Strict allow-list. Every tool × action × agent explicitly listed. |

Full matrix lives in `memory/permissions.yaml`. Edit via `/mb:tool` command.

## On DENY

The agent MUST:

1. Write the denial reason into the response
2. NOT retry without user permission
3. Suggest either a permission update (`/mb:tool grant`) or a workaround

Silent retry after a deny is a verifier failure.
