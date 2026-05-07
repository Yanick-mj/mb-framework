---
name: 'deliverables'
description: 'List typed deliverables for a story'
allowed-tools: ['Bash', 'Read']
---

# /mb:deliverables

List all typed, versioned artifacts for a given story.

## Usage

```
/mb:deliverables STU-46
```

## Process

Take the first argument as story_id. Execute:

```bash
python3 "${MB_DIR:-.claude/mb}/scripts/v2_1/deliverables.py" $ARGUMENTS
```

If `$ARGUMENTS` is empty, the script prints a usage error — remind the
user the command takes a story_id: `/mb:deliverables STU-46`.

Output shows each TYPE group (PLAN, IMPL, REVIEW, DOC) with its revisions.
Click-to-open hints: suggest `Read _mb-output/deliverables/<story_id>/<filename>` to inspect.

$ARGUMENTS
