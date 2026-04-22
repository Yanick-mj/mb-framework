---
name: 'roadmap'
description: 'Show the project _roadmap.md at project root'
allowed-tools: ['Bash', 'Read']
---

# /mb:roadmap

Display the strategic roadmap for the current project.

## Usage

```
/mb:roadmap
```

## Process

Run:

```bash
python3 "${MB_DIR:-.claude/mb}/scripts/v2_1/backlog.py" roadmap
```

If the output reports no `_roadmap.md`, offer to scaffold one from the
template:

```bash
cp "${MB_DIR:-.claude/mb}/templates/roadmap.md" _roadmap.md
```

Ask the user to confirm before creating.

$ARGUMENTS
