---
story_id: STU-G
title: Skills registry + namespacing (core/project/community)
priority: medium
created: 2026-04-19
plan_ref: docs/plans/2026-04-19-v2.2-tools-skills-memory-inbox-board.md
tasks: [G1, G2]
---

# Skills registry + namespacing

## Why

Paperclip observation: agents auto-discover runtime skills. mb v2.1 requires each
agent to declare its skills statically in frontmatter `allowed-tools`. That makes
sharing + adding community skills painful. A registry fixes it without adding a
daemon.

## Scope

In:
- `skills/{core,project,community}/<name>/SKILL.md` layout
- `memory/skills-registry.yaml` — only registered skills are discoverable
- `scripts/v2_2/skills.py` with register/unregister/list
- Commands: `/mb:skill list/add/remove`
- Template: `templates/skill-definition.md`

Out:
- Auto-clone of `git:...` sources in v2.2 (document the URL, let user clone manually)
- Skills marketplace / community directory (maybe v3)
- Automatic `used_by` tracking (updated manually for now)

## Acceptance criteria

- [ ] `skills/project/foo/SKILL.md` exists + `/mb:skill add project/foo` registers it
- [ ] `memory/skills-registry.yaml` reflects the registration
- [ ] `/mb:skill remove project/foo` unregisters but keeps files on disk
- [ ] `/mb:skill add project/nonexistent` raises (skill must exist on disk first)
- [ ] `/mb:skill list` empty state: "📦 No skills registered"
- [ ] Valid tiers strictly enforced: `spaceship` → ValueError

## Dependencies / blockers

Depends on: Task 0 (scaffold)
Blocks: none in v2.2 (I and J don't require it)

## Notes

Scope is narrow on purpose: discovery + lifecycle. Injection-at-runtime
(agents reading the registry before acting) is a separate concern for v2.3
if it proves useful.
