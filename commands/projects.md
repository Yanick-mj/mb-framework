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

Try, in order:

1. If `$MB_FRAMEWORK_PATH` is set (standard when mb shell helper is installed):
   ```bash
   python3 "$MB_FRAMEWORK_PATH/scripts/v2_1/projects.py"
   ```
2. Else, use the submodule path if this project has mb installed:
   ```bash
   python3 "${MB_DIR:-.claude/mb}/scripts/v2_1/projects.py"
   ```

Show the output verbatim.

If neither path works (mb-framework not installed here), tell the user:
> mb-framework is not installed in this project.
> Either `git submodule add git@github.com:Yanick-mj/mb-framework.git .claude/mb`
> then `bash .claude/mb/install.sh`, or set `MB_FRAMEWORK_PATH` to an existing
> mb-framework clone.

If output includes "No mb projects registered", remind the user:
> Run `bash .claude/mb/install.sh` inside a project directory to register it.

$ARGUMENTS
