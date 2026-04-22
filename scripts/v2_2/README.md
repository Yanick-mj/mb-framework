# mb-framework v2.2 helper scripts

Ships 5 structural features: tool RBAC (F), skills registry + 3-layer split (G),
memory layers (H), inbox (I), kanban board (J).

## Running tests

```bash
cd scripts/v2_2
python3 -m venv .venv && source .venv/bin/activate
pip install -r tests/requirements.txt
pytest tests/ -v
```

## Scripts index

| File | Feature | Backs command |
|---|---|---|
| `_paths.py` | shared | path helpers |
| `tools.py` | F — tool catalog | `/mb:tool list` |
| `rbac.py` | F — RBAC checker | `/mb:tool check` |
| `skills.py` | G — skills registry | `/mb:skill list/add/remove` |
| `agent_loader.py` | G — 3-layer composer (AGENT.md + skills → SKILL.md) | install-time |
| `compose_report.py` | G — composed SKILL.md size + rejection monitor | install-time |
| `memory.py` | H — memory layers | internal |
| `migrate_memory.py` | H — v2.1 → v2.2 layout migrator | `python -m ...` |
| `migrate_stories.py` | Pre-I-J — add status: to legacy stories | `python -m ...` |
| `inbox.py` | I — unified blockers | `/mb:inbox` |
| `board.py` | J — ASCII kanban | `/mb:board` |

## 3-layer architecture (v2.2-G)

Agent definition split into 3 distinct concepts:

```
agents/{name}/AGENT.md          # QUI (persona, reporting, budget)
agents/{name}/uses-skills.yaml  # declared skill dependencies
skills/{tier}/{name}/SKILL.md   # COMMENT (reusable capabilities)
references/R-NNN-*.md           # POURQUOI (external sources, v2.3)
```

At install time, `agent_loader.compose_all()` produces the final
`.claude/skills/mb-{name}/SKILL.md` that Claude Code loads via its Skill tool.
Composition is stage-aware — `uses-skills.at_stage.{stage}` filters which
skills are included for the current project stage.

Legacy SKILL.md files (v2.1 and earlier) are preserved and used as fallback
if AGENT.md is absent — no breaking change for existing projects.
