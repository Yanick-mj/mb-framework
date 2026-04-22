"""Tests for migrate_memory.py — v2.1 flat memory/ → v2.2 layers."""
from pathlib import Path

import pytest

from scripts.v2_2 import migrate_memory


def test_migrate_runs_jsonl_to_agents_layer(tmp_project):
    # v2.1 layout: memory/runs.jsonl at flat top
    (tmp_project / "memory" / "runs.jsonl").write_text(
        '{"agent":"fe-dev","ts":"2026-04-19T14:00:00"}\n'
    )
    report = migrate_memory.run(dry_run=False)
    # After migration: memory/agents/_common/runs.jsonl (shared log)
    new_log = tmp_project / "memory" / "agents" / "_common" / "runs.jsonl"
    assert new_log.exists()
    assert "fe-dev" in new_log.read_text()
    assert report.migrated_files == 1


def test_migrate_cost_log_to_project_layer(tmp_project):
    (tmp_project / "memory" / "cost-log.md").write_text("# Costs\n- item")
    migrate_memory.run(dry_run=False)
    assert (tmp_project / "memory" / "project" / "cost-log.md").exists()


def test_migrate_dry_run_does_not_move_files(tmp_project):
    (tmp_project / "memory" / "runs.jsonl").write_text("{}\n")
    report = migrate_memory.run(dry_run=True)
    assert report.migrated_files == 1
    # Original still exists
    assert (tmp_project / "memory" / "runs.jsonl").exists()
    # New target does NOT exist yet
    assert not (tmp_project / "memory" / "agents" / "_common" / "runs.jsonl").exists()


def test_migrate_is_idempotent(tmp_project):
    (tmp_project / "memory" / "runs.jsonl").write_text("{}\n")
    migrate_memory.run(dry_run=False)
    # Running a second time should no-op (source already moved)
    report2 = migrate_memory.run(dry_run=False)
    assert report2.migrated_files == 0


def test_migrate_preserves_unknown_files(tmp_project):
    """Files not in the migration map are left alone."""
    (tmp_project / "memory" / "weird-custom.md").write_text("keep me")
    migrate_memory.run(dry_run=False)
    assert (tmp_project / "memory" / "weird-custom.md").exists()
