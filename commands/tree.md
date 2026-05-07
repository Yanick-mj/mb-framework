---
name: 'tree'
description: 'Show story hierarchy as ASCII tree (optional: focus on one story)'
allowed-tools: ['Bash']
---

# /mb:tree

Display the story parent/child hierarchy in the current mb project.

## Usage

```
/mb:tree            # Render full tree
/mb:tree STU-46     # Render with STU-46 marked as "← me"
```

## Process

```bash
python3 "${MB_DIR:-.claude/mb}/scripts/v2_1/tree.py" $ARGUMENTS
```

Show the output verbatim. If output is "No stories found.", remind the user
that stories live in `_mb-output/implementation-artifacts/stories/`.

$ARGUMENTS
