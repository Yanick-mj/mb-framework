---
name: 'skill'
description: 'Manage the project skill registry (list/add/remove)'
allowed-tools: ['Bash', 'Read', 'Edit']
---

# /mb:skill

Register, list, or remove skills from the project's skill registry.

## Usage

```
/mb:skill list                              # list registered skills
/mb:skill add <tier>/<key> [source]         # register a skill
/mb:skill remove <tier>/<key>               # unregister (keeps files)
```

Example:

```
/mb:skill add project/otoqi-rls
/mb:skill add community/alice-testing git:https://github.com/alice/skill-testing
/mb:skill remove community/alice-testing
```

## Process

Parse the first arg from $ARGUMENTS.

### list

```bash
PYTHONPATH="${MB_DIR:-.claude/mb}" python3 -m scripts.v2_2.skills
```

### add <tier>/<key> [source]

Split arg1 on `/` → tier + key. Default source = `local`.
For git URLs: clone into `skills/<tier>/<key>/` first, then call register.

```bash
PYTHONPATH="${MB_DIR:-.claude/mb}" python3 -c "
from scripts.v2_2 import skills
skills.register(tier='<tier>', key='<key>', source='<source>')
print('Registered:', '<tier>/<key>')
"
```

### remove <tier>/<key>

```bash
PYTHONPATH="${MB_DIR:-.claude/mb}" python3 -c "
from scripts.v2_2 import skills
skills.unregister('<tier>/<key>')
print('Removed from registry (files preserved):', '<tier>/<key>')
"
```

$ARGUMENTS
