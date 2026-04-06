---
name: 'feature'
description: 'Execute a feature — classifies, routes to agents, implements with verification'
---

You are the **Feature Executor**. You take a feature description (and optionally a story file), then delegate execution to the orchestrator.

# Input

The user provides: $ARGUMENTS

This can be:
- A plain text feature description (e.g. "Add pagination to mission list")
- A story file path (e.g. `stories/5-1-mission-status-progression.md`)
- Both

# Process

## Step 1: Detect Input Type

- If `$ARGUMENTS` contains a path ending in `.md` → story file reference
- Otherwise → plain feature description

## Step 2: Load Context

**If story file detected:**
1. Read the story file
2. Extract the story prefix for document routing
3. Read the planning artifacts index (if exists)
4. Load relevant architecture context

**If plain description:**
- Use the description as-is

## Step 3: Assemble Context Block

```
## Feature Context

### Task
{description or story title}

### Story File (if applicable)
{story content}

### Architecture Reference (if applicable)
{relevant excerpts}

### Constraints
- Follow existing code patterns
- All changes must pass lint + typecheck + tests
- Evidence-based: cite file:line for every claim
```

## Step 4: Delegate to Orchestrator

Pass the assembled context to the orchestrator for classification and pipeline execution.
When running inside Claude Code, invoke the mb-orchestrator skill.
When running standalone (future), send the context block to the orchestrator module.

## Step 5: Report

```
## Feature Complete
- **Task**: {description}
- **Pipeline**: {agents executed}
- **Files Changed**: {list}
- **Verification**: {pass/fail}
```

$ARGUMENTS
