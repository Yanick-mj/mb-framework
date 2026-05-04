---
story_id: STU-D5
title: Inbox page — review + blocked + approvals
priority: high
status: todo
created: 2026-05-04
assignee: fe-dev
parent_story: STU-D1
---

# Inbox page — review + blocked + approvals

## Why

The inbox is the "what needs my attention right now" view. It's the actionable counterpart to the board — instead of showing everything, it shows only what's stuck or waiting.

## Scope

**In:**
- `templates/inbox.html` — 3 sections: in_review, blocked, approvals pending
- `templates/partials/inbox_items.html` — partial for HTMX polling
- `server.py` route: `GET /projects/{name}/inbox`
- `parsers.py`: `get_inbox_data(path)` — wraps `inbox._scan_stories()` + `inbox._scan_approvals()`
- Each row: story_id, title, priority badge, source info
- Rows clickable to open story modal (STU-D6)
- Empty state: "Inbox clear" message

**Out:**
- Actions (approve/reject/unblock) — Phase 2

## Acceptance criteria

- [ ] In Review section shows stories with status=in_review
- [ ] Blocked section shows stories with status=blocked
- [ ] Approvals section shows files from memory/approvals-pending/
- [ ] Each section has icon + count header
- [ ] Empty inbox shows clean empty state message
- [ ] Sidebar badge shows total inbox count

## Technical notes

- Directly reuses `scripts.v2_2.inbox._scan_stories()` and `_scan_approvals()`
- Sidebar inbox badge count = len(in_review) + len(blocked) + len(approvals)
- Badge updates via HTMX polling (STU-D7)

## Testing

- Test with stories in in_review and blocked states
- Test with approval files in memory/approvals-pending/
- Test with empty inbox (no actionable items)
