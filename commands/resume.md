---
name: 'resume'
description: 'Resume a paused mb pipeline — detects checkpoint, loads context, continues execution'
allowed-tools: ['Read', 'Bash', 'Agent']
---

# /mb:resume

Detect a paused pipeline, display its status, and re-invoke the orchestrator
to continue from where it left off.

## Usage

```
/mb:resume
```

## Process

1. Check for active pipeline state:

```bash
PYTHONPATH="${MB_DIR:-.claude/mb}" python3 -c \
  "from scripts.v2_2.pipeline_checkpoint import render_status; print(render_status())"
```

2. If no paused pipeline exists, report:

```
No paused pipeline found. Use /mb:feature to start a new one.
```

3. If a paused pipeline is found:

   a. Display the pipeline status (from `render_status()` output)
   b. Unpause the pipeline:
   ```bash
   PYTHONPATH="${MB_DIR:-.claude/mb}" python3 -c \
     "from scripts.v2_2.pipeline_checkpoint import unpause; unpause()"
   ```
   c. Re-read `memory/session/subagent-preamble.md` (it persists across sessions)
   d. Invoke the orchestrator skill (`mb-orchestrator`) — Step 0.7 will detect
      the resumed pipeline and skip classification, jumping directly to Step 3
      at `current_step`.

## When to use

- After a pipeline was paused due to chunk budget (context preservation)
- After a session was interrupted mid-pipeline
- After an agent failure — to retry or skip the failed agent

$ARGUMENTS
