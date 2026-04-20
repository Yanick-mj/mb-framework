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
