---
story_id: STU-D8
title: Entry points + install integration
priority: medium
status: todo
created: 2026-05-04
assignee: devops
---

# Entry points + install integration

## Why

The dashboard needs to be launchable both from Claude Code (`/mb:dashboard`) and from a terminal (`mb dashboard`). Without proper entry points, users won't know it exists or how to start it.

## Scope

**In:**
- `commands/dashboard.md` — `/mb:dashboard` command that runs `python3 -m scripts.dashboard`
- Update `scripts/v2_1/mb_shell_helper.sh` — add `dashboard` subcommand
- `scripts/dashboard/__main__.py` — dependency check at startup (fastapi, uvicorn, jinja2)
  - If missing: print `pip install fastapi uvicorn jinja2 markdown` and exit
- Update `README.md` — add dashboard section to commands table
- Update `install.sh` — mention dashboard deps in post-install message (optional, not auto-install)

**Out:**
- Auto-installing pip dependencies (user's choice)
- Dashboard-specific configuration file

## Acceptance criteria

- [ ] `/mb:dashboard` in Claude Code starts the server and prints the URL
- [ ] `mb dashboard` from terminal starts the server and opens the browser
- [ ] Missing deps → clear error message with install command
- [ ] `mb dashboard --port 8080` allows custom port
- [ ] README documents the dashboard command
- [ ] Shell helper `mb dashboard` works after re-sourcing shell

## Technical notes

- `commands/dashboard.md` just runs the bash command, Claude doesn't need to do anything special
- Shell helper: add case `dashboard)` to the existing case statement
- `__main__.py` uses `importlib.util.find_spec()` to check deps before importing
- Default port 5111, overridable via `--port` arg or `MB_DASHBOARD_PORT` env var
- `mb dashboard` should also open browser: `python3 -m webbrowser http://localhost:5111`

## Testing

- Test `/mb:dashboard` in a Claude Code session
- Test `mb dashboard` from terminal
- Test without fastapi installed (should show helpful error)
- Test with custom port
