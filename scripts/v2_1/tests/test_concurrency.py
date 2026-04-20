"""Concurrency smoke tests for v2.1 write paths.

These tests verify mb's writes don't lose data when two agents race. The
guarantees we test:

1. runs.py.append() — POSIX append writes < PIPE_BUF (4 KiB) are atomic
2. deliverables.write() — O_EXCL retry loop never overwrites
3. projects.add() — last-write-wins, but no partial yaml corruption

Note: projects.add() is NOT race-safe against simultaneous writes to the
SAME registry file. Two agents calling add() at the same instant can lose
one entry (the loser's write happens after loser's read). Deliberate
trade-off for v2.1 (solo-only tool). v2.2 can add file locking if needed.
"""
import json
import threading
from pathlib import Path

import pytest

from scripts.v2_1 import runs, deliverables, projects


def test_runs_append_atomic_under_concurrent_writes(tmp_project):
    """100 threads each appending one entry — all 100 entries present.

    POSIX guarantees that writes to append-only files < PIPE_BUF bytes are
    atomic. Each runs.py entry is ~300 bytes → well under 4 KiB.
    """
    N = 100

    def worker(i: int):
        runs.append(
            agent=f"a{i}", story="S", action="x",
            tokens_in=1, tokens_out=1, summary=f"run {i}",
        )

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(N)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    log = tmp_project / "memory" / "runs.jsonl"
    lines = log.read_text().strip().splitlines()
    assert len(lines) == N, f"Expected {N} entries, got {len(lines)}"
    # All lines must parse as valid JSON (no interleaving)
    run_ids = set()
    for l in lines:
        entry = json.loads(l)
        run_ids.add(entry["run_id"])
    assert len(run_ids) == N, "Duplicate or corrupted run_ids"


def test_deliverables_write_exclusive_under_concurrent_writes(tmp_project):
    """20 threads all try to write PLAN rev 1 — exactly 20 distinct rev files.

    None overwrites another thanks to O_EXCL retry loop.
    """
    N = 20
    results = []
    lock = threading.Lock()

    def worker(i: int):
        p = deliverables.write(
            story_id="STU-42", type="PLAN",
            body=f"plan from thread {i}", author="a",
        )
        with lock:
            results.append(p.name)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(N)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(results) == N
    # Each filename must be unique — no two threads overwrote the same rev
    assert len(set(results)) == N, (
        f"Expected {N} distinct rev files, got {len(set(results))} "
        f"({results})"
    )


def test_projects_add_concurrent_last_write_wins(tmp_home):
    """2 threads adding the SAME name — last write wins, no yaml corruption.

    Documented behavior: projects.yaml is not lock-protected. Race is
    acceptable in solo use case (same user rarely calls add() twice at once).
    We assert the file is still valid YAML after the race, not that both
    writes succeeded.
    """
    import yaml

    def worker(stage: str):
        projects.add(name="demo", path="/x", stage=stage)

    threads = [
        threading.Thread(target=worker, args=(s,))
        for s in ["mvp", "pmf", "scale", "discovery"]
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # File must still parse as valid YAML (no partial write corruption)
    registry = tmp_home / ".mb" / "projects.yaml"
    data = yaml.safe_load(registry.read_text())
    assert isinstance(data, dict)
    assert isinstance(data.get("projects"), list)
    # Demo project exists (either one of the 4 stages — don't care which)
    names = [p["name"] for p in data["projects"]]
    assert "demo" in names
    # No duplicates (name is idempotent key)
    assert names.count("demo") == 1
