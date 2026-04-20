---
name: 'projects'
description: 'List all mb-registered projects (stage, path, last activity)'
allowed-tools: ['Bash', 'Read']
---

# /mb:projects

Lists every project registered in `~/.mb/projects.yaml` with its current stage
and optionally its last modified mb-stage.yaml date.

## Usage

```
/mb:projects
```

## Process

Execute this command:

```bash
python3 "${MB_DIR:-.claude/mb}/scripts/v2_1/projects.py"
```

If that fails (mb-framework not installed as submodule in this project),
fall back to:

```bash
python3 "$HOME/code/Yanick-mj/mb-framework/scripts/v2_1/projects.py"
```

Show the output verbatim.

If output includes "No mb projects registered", remind the user:
> Run `bash .claude/mb/install.sh` inside a project directory to register it.

$ARGUMENTS
