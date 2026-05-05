"""TDD tests for roadmap ↔ sprint links — STU-P2S3.4."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.dashboard.tests.conftest import (
    write_sprint, write_story, write_roadmap,
)


class TestRoadmapSprintAggregation:
    def test_phase_shows_sprint_count(self, tmp_project):
        from scripts.dashboard.parsers import get_roadmap_data
        write_roadmap(tmp_project, phases=[
            {"num": "2", "name": "Dashboard", "timeframe": "weeks 1-3",
             "goal": "Build dashboard"},
        ])
        write_sprint(tmp_project, "sprint-1", "S1", "G1", phase="Phase 2")
        write_sprint(tmp_project, "sprint-2", "S2", "G2", phase="Phase 2")
        data = get_roadmap_data(tmp_project)
        phase = data["phases"][0]
        assert phase["sprint_count"] == 2

    def test_phase_shows_avg_completion(self, tmp_project):
        from scripts.dashboard.parsers import get_roadmap_data
        write_roadmap(tmp_project, phases=[
            {"num": "2", "name": "Dashboard", "timeframe": "weeks 1-3",
             "goal": "Build it"},
        ])
        write_story(tmp_project, "S1", "done", "Done")
        write_story(tmp_project, "S2", "todo", "Todo")
        write_sprint(tmp_project, "sprint-1", "S1", "G1",
                     phase="Phase 2", stories=["S1"])  # 100%
        write_sprint(tmp_project, "sprint-2", "S2", "G2",
                     phase="Phase 2", stories=["S2"])  # 0%
        data = get_roadmap_data(tmp_project)
        phase = data["phases"][0]
        assert phase["sprint_pct"] == 50

    def test_phase_no_sprints(self, tmp_project):
        from scripts.dashboard.parsers import get_roadmap_data
        write_roadmap(tmp_project, phases=[
            {"num": "3", "name": "Agent", "timeframe": "TBD", "goal": "AI"},
        ])
        data = get_roadmap_data(tmp_project)
        phase = data["phases"][0]
        assert phase["sprint_count"] == 0
        assert phase["sprint_pct"] == 0


class TestSprintsFilterByPhase:
    def test_filter_returns_only_matching_phase(self, client, tmp_project):
        write_sprint(tmp_project, "sprint-1", "S1", "G1", phase="Phase 2")
        write_sprint(tmp_project, "sprint-2", "S2", "G2", phase="Phase 3")
        resp = client.get("/projects/demo/sprints?phase=Phase+2")
        assert resp.status_code == 200
        assert "S1" in resp.text
        assert "S2" not in resp.text

    def test_no_filter_shows_all(self, client, tmp_project):
        write_sprint(tmp_project, "sprint-1", "S1", "G1", phase="Phase 2")
        write_sprint(tmp_project, "sprint-2", "S2", "G2", phase="Phase 3")
        resp = client.get("/projects/demo/sprints")
        assert "S1" in resp.text
        assert "S2" in resp.text


class TestSprintCardShowsPhase:
    def test_phase_tag_visible(self, client, tmp_project):
        write_sprint(tmp_project, "sprint-1", "Sprint", "Goal", phase="Phase 2")
        resp = client.get("/projects/demo/sprints")
        assert "Phase 2" in resp.text
