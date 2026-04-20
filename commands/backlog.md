---
name: 'backlog'
description: 'Show priority-sorted backlog stories from _backlog/ directory'
allowed-tools: ['Bash', 'Read']
---

# /mb:backlog

Display all pending backlog stories found in `{project-root}/_backlog/`,
sorted by priority (critical → high → medium → low).

## Usage

```
/mb:backlog
```

## Process

Run:

```bash
python3 "${MB_DIR:-.claude/mb}/scripts/v2_1/backlog.py" backlog
```

Show the output verbatim. If output indicates no stories, suggest:
> Create a story from the template at `.claude/mb/templates/backlog-story.md`
> and save it to `_backlog/STU-<id>-<slug>.md`.

## What counts as a backlog story

- Lives in `_backlog/*.md`
- Has YAML frontmatter with `story_id:` (required)
- Optional: `title`, `priority` (defaults to `medium`), `created`

Malformed frontmatter or missing `story_id` → silently skipped.

$ARGUMENTS
