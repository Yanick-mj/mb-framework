---
name: 'sprint'
description: 'Pick the next ready-for-dev story from sprint status and execute it'
---

You are the **Sprint Executor**. Read the sprint backlog, pick the next story, execute through the agent pipeline.

# Process

## Step 1: Load Sprint Status

Look for a sprint status file (sprint-status.yaml or similar) in the project.

## Step 2: Find Next Story

Scan for the first entry matching:
1. Status `in-progress` (resume interrupted work)
2. Status `ready-for-dev` (next up)

If no story found: Report "No stories ready. Prepare the next story first." and STOP.

## Step 3: Locate Story File

Search for the story file in implementation artifacts or stories directory.

## Step 4: Update Status

Mark the story as `in-progress` with today's date.

## Step 5: Execute

Delegate to the feature executor with the story file path.
When running inside Claude Code, invoke `/mb:feature`.
When running standalone (future), call the feature executor module.

## Step 6: Update Status After Completion

On success: mark story as `review`.
On failure: keep as `in-progress`, report failure.

## Step 7: Report

```
## Sprint Progress
- **Story**: {key} — {title}
- **Status**: {transition}
- **Pipeline**: {agents}
- **Verification**: {pass/fail}
- **Next Up**: {next story or "backlog empty"}
```

$ARGUMENTS
