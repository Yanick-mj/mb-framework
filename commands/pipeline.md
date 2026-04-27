---
name: 'pipeline'
description: 'Show mb pipeline state: stage, recent runs, UX GATE status per feature'
allowed-tools: ['Bash']
---

# /mb:pipeline

Diagnostic view of where you are in the mb-framework pipeline. Helps avoid
drift: shows current stage, recent agent activity, artifact gates, and the
canonical routing table.

## Usage

```
/mb:pipeline
```

## Process

```bash
PYTHONPATH="${MB_DIR:-.claude/mb}" python3 -m scripts.v2_1.pipeline_status
```

Show the output verbatim.

## What it reports

- **Active pipeline** (v2.2): detects `memory/session/pipeline-state.yaml` — shows
  pipeline ID, task, progress, and paused status. Suggests `/mb:resume` if paused.
- **Stage**: from `mb-stage.yaml`
- **Recent runs**: last 5 entries from `memory/runs.jsonl` (who did what)
- **UX GATE status per feature**: checks `_discovery/{feature}/` for
  required artifacts, flags blockers
- **Available pipelines**: canonical routing table from orchestrator

## When to use

- You suspect Claude is about to drift (e.g. jumping to `superpowers:*`)
- You want to know what agent should come next
- Before starting a new task — confirm you're at the right starting point
- After a pipeline run — verify all agents produced their artifacts
- After a session interruption — check if a pipeline was left in-progress

$ARGUMENTS
