"""Tests for _paths.py output_root() and v2.4 legacy fallback.

Phase 1b of v2.4 independence cut: pin the contract that lets
projects with _bmad-output/ keep working while new projects use
_mb-output/. The fallback is removed at v2.5.
"""
from scripts.v2_2 import _paths


def test_constants_define_the_cut():
    assert _paths.OUTPUT_DIRNAME == "_mb-output"
    assert _paths.LEGACY_OUTPUT_DIRNAME == "_bmad-output"


def test_output_root_defaults_to_new_when_neither_exists(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert _paths.output_root() == tmp_path / "_mb-output"


def test_output_root_picks_new_when_only_new_exists(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "_mb-output").mkdir()
    assert _paths.output_root() == tmp_path / "_mb-output"


def test_output_root_falls_back_to_legacy(tmp_path, monkeypatch):
    """Pre-v2.4 project: only _bmad-output/ exists. Read-compat must hold."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "_bmad-output").mkdir()
    assert _paths.output_root() == tmp_path / "_bmad-output"


def test_output_root_prefers_new_when_both_exist(tmp_path, monkeypatch):
    """Mid-migration: both can coexist briefly. New always wins."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "_mb-output").mkdir()
    (tmp_path / "_bmad-output").mkdir()
    assert _paths.output_root() == tmp_path / "_mb-output"


def test_stories_root_flows_through_output_root_default(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    expected = tmp_path / "_mb-output" / "implementation-artifacts" / "stories"
    assert _paths.stories_root() == expected


def test_stories_root_flows_through_output_root_legacy(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "_bmad-output").mkdir()
    expected = tmp_path / "_bmad-output" / "implementation-artifacts" / "stories"
    assert _paths.stories_root() == expected


def test_deliverables_root_default(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert _paths.deliverables_root() == tmp_path / "_mb-output" / "deliverables"


def test_deliverables_root_legacy(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "_bmad-output").mkdir()
    assert _paths.deliverables_root() == tmp_path / "_bmad-output" / "deliverables"


def test_sprint_status_file_default(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    expected = tmp_path / "_mb-output" / "implementation-artifacts" / "sprint-status.yaml"
    assert _paths.sprint_status_file() == expected


def test_sprint_status_file_legacy(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "_bmad-output").mkdir()
    expected = tmp_path / "_bmad-output" / "implementation-artifacts" / "sprint-status.yaml"
    assert _paths.sprint_status_file() == expected
