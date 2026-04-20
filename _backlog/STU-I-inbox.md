---
story_id: STU-I
title: /mb:inbox unified blocker view
priority: medium
created: 2026-04-19
plan_ref: docs/plans/2026-04-19-v2.2-tools-skills-memory-inbox-board.md
parent_story: STU-H
tasks: [I1, I2]
---

# /mb:inbox

## Why

Morning question: "What's waiting on me?" Currently requires checking 3 places:
story frontmatter (in_review), story blockers (blocked), approvals-pending dir.
One command, 30 seconds.

## Scope

In:
- `scripts/v2_2/inbox.py` aggregating stories in_review + blocked + approvals pending
- Command `/mb:inbox`
- Emoji-led grouped output (🟡 review / 🚧 blocked / ⏳ approvals)

Out:
- Filtering/sorting (N items per group max already, keep simple)
- Bulk actions from inbox (approve/reject in-CLI → v2.3)
- RBAC denial surface (could be a bonus later; keep scope narrow)

## Acceptance criteria

- [ ] Empty state: "📥 Inbox: nothing to review." — does not error
- [ ] Stories with status=in_review appear in 🟡 group
- [ ] Stories with status=blocked appear in 🚧 group
- [ ] Files in `memory/approvals-pending/*.md` appear in ⏳ group
- [ ] Header shows total count of items
- [ ] Stories with status=done or status=todo are NOT shown

## Dependencies / blockers

Depends on: Task 0, H (stories_root path helper)
Blocks: none

## Notes

Reads only, writes nothing. No mutation risk. Fastest command to implement
once H1 (memory.py) exists.
