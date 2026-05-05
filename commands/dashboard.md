---
name: 'dashboard'
description: 'Launch the mb-dashboard browser UI on localhost:5111'
allowed-tools: ['Bash']
---

# /mb:dashboard

Launch the browser-based dashboard.

## Usage

```
/mb:dashboard
/mb:dashboard --port 8080
```

## Process

```bash
PYTHONPATH="${MB_DIR:-.claude/mb}" python3 -m scripts.dashboard "$@"
```
