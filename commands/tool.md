---
name: 'tool'
description: 'Manage external tool catalog + RBAC (list, check, audit)'
allowed-tools: ['Bash', 'Read']
---

# /mb:tool

Three subcommands for mb's stage-aware tool governance.

## Usage

```
/mb:tool list                           # list tools in tools/_catalog.yaml
/mb:tool check <agent> <tool> <action>  # permission check (exit 0 if allowed)
/mb:tool audit [N]                      # last N audit decisions (default 10)
```

## Process

Parse the first arg from `$ARGUMENTS` as the subcommand. Remaining args pass
as positional arguments to the helper.

### list

```bash
PYTHONPATH="${MB_DIR:-.claude/mb}" python3 -m scripts.v2_2.tools
```

Output shows each registered tool with its allowed actions. If the catalog
is absent, a 🔧 placeholder suggests creating one from
`templates/tool-definition.md`.

### check

```bash
PYTHONPATH="${MB_DIR:-.claude/mb}" python3 -m scripts.v2_2.rbac check <agent> <tool> <action>
```

Exit code:
- `0` → ALLOWED (safe to proceed)
- `1` → DENIED (HALT, report, do NOT attempt the action)

Audit entry is written automatically to `memory/tool-audit.jsonl` in both
cases — the denial is recorded, no stealth.

### audit

```bash
PYTHONPATH="${MB_DIR:-.claude/mb}" python3 -m scripts.v2_2.rbac
```

Shows the last 10 decisions (newest first). Pass an integer as the second
arg to change the limit.

## When to use

- **Agents** should call `check` BEFORE invoking any external tool action
  that mutates state (deploys, DB writes, charges, merges, etc.). See the
  per-agent `skills/core/preflight-tool-rbac/SKILL.md` rule (v2.2-G).
- **Operators** use `list` to verify the catalog is current.
- **Operators** use `audit` for post-mortem ("who deployed what yesterday?").

## Stage-aware behavior

When `memory/permissions.yaml` is absent:
- `discovery`, `mvp` → all checks ALLOW (permissive default)
- `pmf`, `scale` → all checks DENY (strict default)

Once `permissions.yaml` exists, it's enforced strictly at every stage —
the file being present is the opt-in to enforcement.

$ARGUMENTS
