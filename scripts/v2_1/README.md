# mb-framework v2.1 helper scripts

Pure-stdlib Python + bash helpers that back the `/mb:*` v2.1 commands.

## Running tests

```bash
cd scripts/v2_1
python3 -m venv .venv && source .venv/bin/activate
pip install -r tests/requirements.txt
pytest tests/ -v
```

## Scripts index

| File | Feature | Backs command |
|---|---|---|
| `projects.py` | A — multi-project overview | `/mb:projects` |
| `deliverables.py` | B — typed deliverables | writing convention |
| `tree.py` | C — parent/child story tree | `/mb:tree` |
| `runs.py` | D — run log | writing convention |
| `backlog.py` | E — backlog/roadmap | `/mb:backlog`, `/mb:roadmap` |
| `_emoji.py` | UX — emoji/ASCII tag resolver | all render funcs |

## Contributing — shell portability rules

When editing `install.sh` or any bash helpers:

**`sed -i` is NOT portable between BSD (macOS) and GNU (Linux).**

- macOS: `sed -i '' 's/a/b/' file` (needs empty string backup arg)
- GNU:   `sed -i    's/a/b/' file` (rejects that arg)

Always use the uname check pattern (already in install.sh §5):

```bash
if [ "$(uname)" = "Darwin" ]; then
    sed -i '' "s/OLD/NEW/" file
else
    sed -i    "s/OLD/NEW/" file
fi
```

**Better alternative — inline Python** (portable, no sed-dialect headache):

```bash
python3 -c "
import pathlib
p = pathlib.Path('file')
p.write_text(p.read_text().replace('OLD', 'NEW'))
"
```

New code should prefer the Python alternative unless doing heavy regex.

## Emoji fallback — `MB_NO_EMOJI=1`

All render functions lead with a domain emoji (📁 projects, 📋 backlog,
📦 deliverables, 🏃 runs, 🌲 tree). On legacy terminals or when piping
through `grep`/CI logs, set `MB_NO_EMOJI=1` for ASCII tags:

```bash
MB_NO_EMOJI=1 python3 projects.py
# → [PROJECTS] 3 mb project(s)
```

Accepted truthy values: `1`, `true`, `yes`. All others → emoji on.

## Dependency policy

- Stdlib only — EXCEPT PyYAML.
- PyYAML missing → scripts fail early with a pedagogic "pip install pyyaml"
  message (not a cryptic traceback).
- Never add a second runtime dep without a very strong case (v3 commercial).
