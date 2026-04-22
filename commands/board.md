---
name: 'board'
description: 'ASCII kanban of all stories, grouped by status'
allowed-tools: ['Bash']
---

# /mb:board

Terminal-friendly kanban visualization.

## Usage

```
/mb:board
```

## Process

```bash
PYTHONPATH="${MB_DIR:-.claude/mb}" python3 -m scripts.v2_2.board
```

## What gets shown

5 canonical columns: BACKLOG, TODO, IN PROG, REVIEW, DONE.

Each column header shows the count of stories in that status.

Stories with a non-canonical status (typo etc.) are silently skipped —
use /mb:tree to see all stories including invalid-status ones.

$ARGUMENTS
