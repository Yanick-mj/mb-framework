"""Tests for runs.py — append-only structured run log."""
import json
from pathlib import Path

import pytest

from scripts.v2_1 import runs


def test_append_creates_log_and_writes_jsonl(tmp_project):
    runs.append(
        agent="fe-dev",
        story="STU-46",
        action="implement_oauth",
        tokens_in=1200,
        tokens_out=800,
        summary="Added OAuth callback handler",
    )
    log = tmp_project / "memory" / "runs.jsonl"
    assert log.exists()
    lines = log.read_text().strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["agent"] == "fe-dev"
    assert entry["story"] == "STU-46"
    assert "run_id" in entry
    assert "ts" in entry


def test_append_generates_unique_run_ids(tmp_project):
    runs.append(agent="a", story="S", action="x", tokens_in=1, tokens_out=1, summary="s")
    runs.append(agent="b", story="S", action="y", tokens_in=1, tokens_out=1, summary="s")
    lines = (tmp_project / "memory" / "runs.jsonl").read_text().strip().splitlines()
    ids = [json.loads(l)["run_id"] for l in lines]
    assert len(set(ids)) == 2


def test_load_recent_returns_sorted_by_ts_desc(tmp_project):
    for i in range(3):
        runs.append(
            agent=f"agent-{i}", story="STU-1", action=f"a{i}",
            tokens_in=100, tokens_out=100, summary=f"did {i}",
        )
    entries = runs.load_recent(limit=2)
    assert len(entries) == 2
    # Most recent first
    assert entries[0]["agent"] == "agent-2"
    assert entries[1]["agent"] == "agent-1"


def test_render_recent_human_readable(tmp_project):
    runs.append(
        agent="fe-dev", story="STU-46", action="impl",
        tokens_in=1200, tokens_out=800, summary="Added OAuth handler",
    )
    out = runs.render_recent(limit=5)
    assert "fe-dev" in out
    assert "STU-46" in out
    assert "OAuth" in out


def test_render_recent_empty_returns_placeholder(tmp_project):
    out = runs.render_recent()
    assert "No runs" in out


def test_load_recent_skips_corrupted_lines(tmp_project):
    """Corrupted JSONL lines are skipped, valid ones still load."""
    runs.append(agent="a", story="S", action="x", tokens_in=1, tokens_out=1, summary="good")
    log = tmp_project / "memory" / "runs.jsonl"
    # Inject a corrupted line
    with log.open("a") as f:
        f.write("this is not json\n")
    runs.append(agent="b", story="S", action="y", tokens_in=1, tokens_out=1, summary="also good")
    entries = runs.load_recent(limit=10)
    assert len(entries) == 2
    assert entries[0]["agent"] == "b"
    assert entries[1]["agent"] == "a"


def test_rapid_fire_appends_preserve_order(tmp_project):
    """10 consecutive appends keep insertion order on load_recent.

    Second-precision ts previously collided on fast loops. Microsecond
    precision restores a reliable ts tiebreaker; file-order reversal is
    the ultimate fallback.
    """
    for i in range(10):
        runs.append(
            agent=f"a{i}", story="S", action="x",
            tokens_in=1, tokens_out=1, summary=f"did {i}",
        )
    entries = runs.load_recent(limit=10)
    assert entries[0]["agent"] == "a9"
    assert entries[-1]["agent"] == "a0"


def test_ts_has_microsecond_precision(tmp_project):
    """Each run's ts includes microseconds (not just seconds)."""
    runs.append(
        agent="x", story="S", action="a",
        tokens_in=1, tokens_out=1, summary="s",
    )
    entry = runs.load_recent(limit=1)[0]
    assert "." in entry["ts"], f"expected microseconds in ts, got {entry['ts']}"
