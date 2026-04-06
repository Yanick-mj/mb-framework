# mb-framework

Portable, markdown-only AI agent framework for Claude Code. Zero code dependencies.

Replaces complex AI agent infrastructure (embeddings, vector stores, message buses) with structured markdown files that Claude Code natively understands.

## Quick Start

```bash
# Add as submodule to your project
cd your-project
git submodule add git@github.com:Yanick-mj/mb-framework.git .claude/mb

# Install (creates symlinks)
bash .claude/mb/install.sh

# Initialize (scans your project)
# Then in Claude Code:
/mb:init
```

## What's Inside

| Folder | Purpose |
|--------|---------|
| `agents/` | 12 agent personas (orchestrator, dev, be-dev, fe-dev, devops, architect, verifier, tea, pm, sm, quick-flow, tech-writer) |
| `commands/` | Entry points: `/mb:feature`, `/mb:sprint`, `/mb:fix`, `/mb:review`, `/mb:init` |
| `skills/` | Injectable domain knowledge (ux-design, project-specific) |
| `templates/` | Code scaffolding, validation checklists, stack conventions |
| `tools/` | External tool catalog + permissions |
| `creds/` | Credentials (.gitignored) |
| `memory/` | Persistent project memory + ephemeral session state |

## Commands

| Command | Description |
|---------|-------------|
| `/mb:feature "description"` | Classify task, route to agent pipeline, implement |
| `/mb:sprint` | Pick next ready-for-dev story, execute pipeline |
| `/mb:fix "bug"` | Debug and fix a bug |
| `/mb:review` | Code review current changes |
| `/mb:init` | Scan project, generate codebase index + memory |

## How It Works

```
/mb:feature "add pagination"
  → orchestrator classifies (feature_frontend, medium)
  → reads mb-config.yaml + codebase-index.md
  → pipeline: architect → fe-dev → verifier
  → each agent reads/writes memory/_session/handoff.md
  → verifier runs lint + tsc + tests
  → cost logged to memory/cost-log.md
```

## Configuration

Edit `mb-config.yaml` to toggle agents, pipeline behavior, and tracking.

## Adding Project-Specific Skills

After `/mb:init`, add domain knowledge to `project-skills/`:

```
project-skills/
└── my-api/SKILL.md     # API patterns, conventions, gotchas
```

## License

MIT
