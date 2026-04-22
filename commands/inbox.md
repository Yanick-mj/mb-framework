---
name: 'inbox'
description: 'Unified view of blockers: in_review, blocked, approvals pending'
allowed-tools: ['Bash']
---

# /mb:inbox

Morning standup in 30 seconds. Shows every story that needs your attention
and any approval waiting on you.

## Usage

```
/mb:inbox
```

## Process

```bash
PYTHONPATH="${MB_DIR:-.claude/mb}" python3 -m scripts.v2_2.inbox
```

Output sections:
- 🟡 In Review — stories the verifier flagged; you must approve or revise
- 🚧 Blocked  — stories blocked by another story or external dep
- ⏳ Approvals pending — files in memory/approvals-pending/

$ARGUMENTS
