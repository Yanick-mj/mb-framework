---
story_id: STU-F
title: Tool catalog + stage-aware RBAC
priority: high
created: 2026-04-19
plan_ref: docs/plans/2026-04-19-v2.2-tools-skills-memory-inbox-board.md
tasks: [F1, F2, F3, F4, F5]
---

# Tool catalog + stage-aware RBAC

## Why

Today any mb agent can run any tool. At stage=pmf+ that's unsafe: a fe-dev invocation could
accidentally trigger `vercel deploy-prod`. We need explicit permissions, auditable and
stage-aware (permissive in discovery/mvp, strict in pmf/scale).

## Scope

In:
- `tools/_catalog.yaml` inventory
- `memory/permissions.yaml` RBAC config
- `memory/tool-audit.jsonl` append-only log
- `scripts/v2_2/tools.py` + `scripts/v2_2/rbac.py`
- Commands: `/mb:tool list`, `/mb:tool check`, `/mb:tool audit`
- Pre-flight rule wired into be-dev, fe-dev, devops SKILL.md

Out:
- OAuth-style credential management (keep `creds/` pattern v2.1)
- Real-time enforcement (it's advisory — agents CAN disobey, the audit catches them)

## Acceptance criteria

- [ ] `/mb:tool check fe-dev vercel deploy-prod` returns DENIED + audit entry, exit 1
- [ ] `/mb:tool check devops vercel deploy-prod` returns ALLOWED, exit 0
- [ ] `memory/tool-audit.jsonl` shows the 2 entries above
- [ ] be-dev, fe-dev, devops SKILL.md contain the mandatory Pre-flight block
- [ ] `tools/_catalog.yaml` absent → `/mb:tool list` says "🔧 No tools registered"
- [ ] `memory/permissions.yaml` absent → all checks deny by default
- [ ] Stage-keyed actions resolve correctly: same config gives different answers at mvp vs pmf

## Dependencies / blockers

Depends on: Task 0 (scripts/v2_2 scaffold)
Blocks: I (inbox can surface RBAC denials)

## Notes

Not building a UI. Agents invoke `/mb:tool check` as a shell-out; the Decision
dataclass encodes the result. Strict stage resolution: reads `mb-stage.yaml` once
per check (cheap, keeps behavior deterministic).
