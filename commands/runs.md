---
name: 'runs'
description: 'Show recent agent runs (default: last 10)'
allowed-tools: ['Bash']
---

# /mb:runs

Display the most recent entries from `memory/runs.jsonl`.

## Usage

```
/mb:runs        # last 10
/mb:runs 25     # last 25
```

## Process

```bash
python3 "${MB_DIR:-.claude/mb}/scripts/v2_1/runs.py" ${1:-10}
```

$ARGUMENTS
