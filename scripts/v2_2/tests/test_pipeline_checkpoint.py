"""Tests for pipeline_checkpoint.py."""
import pytest
import yaml

from scripts.v2_2 import pipeline_checkpoint as pc
from scripts.v2_2.memory import session_path


SAMPLE_AGENTS = [
    ("architect", "plan"),
    ("lead-dev", "breakdown"),
    ("be-dev", "implement"),
    ("fe-dev", "implement"),
    ("tea", "test"),
    ("verifier", "verify"),
]


@pytest.fixture
def active_pipeline(tmp_project):
    """Init a pipeline and return the state."""
    return pc.init(
        task_original="Add Stripe checkout",
        classified_as="full-stack-feature",
        story_id="STU-058",
        stage="scale",
        agents=SAMPLE_AGENTS,
        chunk_size=4,
    )


class TestInit:
    def test_creates_state_file(self, tmp_project):
        state = pc.init(
            task_original="Fix login",
            classified_as="backend-feature",
            story_id="STU-001",
            stage="pmf",
            agents=[("architect", "plan"), ("be-dev", "implement")],
        )
        assert session_path(pc.STATE_FILENAME).exists()
        assert state["version"] == 1
        assert state["status"] == "active"
        assert state["total_count"] == 2
        assert state["completed_count"] == 0
        assert state["current_step"] == 0
        assert len(state["pipeline"]) == 2
        assert state["pipeline"][0]["agent"] == "architect"
        assert state["pipeline"][0]["status"] == "pending"

    def test_pipeline_already_active_error(self, active_pipeline):
        with pytest.raises(pc.PipelineAlreadyActiveError) as exc_info:
            pc.init(
                task_original="Another task",
                classified_as="trivial-fix",
                story_id="",
                stage="scale",
                agents=[("quick-flow", "fix")],
            )
        assert active_pipeline["pipeline_id"] in str(exc_info.value)

    def test_allows_init_after_completed(self, tmp_project):
        state = pc.init(
            task_original="First",
            classified_as="trivial-fix",
            story_id="",
            stage="scale",
            agents=[("quick-flow", "fix")],
        )
        # Manually mark completed
        state["status"] = "completed"
        pc._write_state(state)

        # Should succeed
        new_state = pc.init(
            task_original="Second",
            classified_as="trivial-fix",
            story_id="",
            stage="scale",
            agents=[("quick-flow", "fix")],
        )
        assert new_state["task"]["original"] == "Second"

    def test_allows_init_after_failed(self, tmp_project):
        state = pc.init(
            task_original="First",
            classified_as="trivial-fix",
            story_id="",
            stage="scale",
            agents=[("quick-flow", "fix")],
        )
        state["status"] = "failed"
        pc._write_state(state)

        new_state = pc.init(
            task_original="Second",
            classified_as="trivial-fix",
            story_id="",
            stage="scale",
            agents=[("quick-flow", "fix")],
        )
        assert new_state["task"]["original"] == "Second"

    def test_default_chunk_size(self, tmp_project):
        state = pc.init(
            task_original="X",
            classified_as="trivial-fix",
            story_id="",
            stage="scale",
            agents=[("quick-flow", "fix")],
        )
        assert state["chunk_size"] == 4

    def test_custom_chunk_size(self, tmp_project):
        state = pc.init(
            task_original="X",
            classified_as="trivial-fix",
            story_id="",
            stage="scale",
            agents=[("quick-flow", "fix")],
            chunk_size=2,
        )
        assert state["chunk_size"] == 2

    def test_task_fields(self, active_pipeline):
        assert active_pipeline["task"]["original"] == "Add Stripe checkout"
        assert active_pipeline["task"]["classified_as"] == "full-stack-feature"
        assert active_pipeline["task"]["story_id"] == "STU-058"
        assert active_pipeline["stage"] == "scale"


class TestMarkInProgress:
    def test_marks_current_step(self, active_pipeline):
        state = pc.mark_in_progress()
        assert state["pipeline"][0]["status"] == "in_progress"

    def test_no_state_raises(self, tmp_project):
        with pytest.raises(FileNotFoundError):
            pc.mark_in_progress()


class TestCompleteStep:
    def test_completes_and_advances(self, active_pipeline):
        pc.mark_in_progress()
        state = pc.complete_step(run_id="abc123")
        assert state["pipeline"][0]["status"] == "done"
        assert state["pipeline"][0]["run_id"] == "abc123"
        assert state["completed_count"] == 1
        assert state["current_step"] == 1

    def test_multiple_completions(self, active_pipeline):
        for i in range(3):
            pc.mark_in_progress()
            pc.complete_step(run_id=f"run-{i}")

        state = pc.get_state()
        assert state["completed_count"] == 3
        assert state["current_step"] == 3
        for j in range(3):
            assert state["pipeline"][j]["status"] == "done"
        assert state["pipeline"][3]["status"] == "pending"

    def test_no_state_raises(self, tmp_project):
        with pytest.raises(FileNotFoundError):
            pc.complete_step()


class TestFailStep:
    def test_fails_and_pauses(self, active_pipeline):
        pc.mark_in_progress()
        state = pc.fail_step(error="TypeError in handler")
        assert state["pipeline"][0]["status"] == "failed"
        assert state["paused"] is not None
        assert state["paused"]["reason"] == "agent_failure"
        assert "TypeError" in state["paused"]["message"]

    def test_default_error_message(self, active_pipeline):
        pc.mark_in_progress()
        state = pc.fail_step()
        assert "architect" in state["paused"]["message"]


class TestPause:
    def test_pause_sets_fields(self, active_pipeline):
        pc.mark_in_progress()
        pc.complete_step()
        state = pc.pause(reason="chunk_budget", message="Pausing at 1/6")
        assert state["paused"]["reason"] == "chunk_budget"
        assert state["paused"]["at_step"] == 1
        assert "Pausing" in state["paused"]["message"]

    def test_default_message(self, active_pipeline):
        state = pc.pause()
        assert "context preservation" in state["paused"]["message"]


class TestUnpause:
    def test_clears_paused(self, active_pipeline):
        pc.pause()
        state = pc.unpause()
        assert state["paused"] is None


class TestShouldPause:
    def test_no_state_returns_false(self, tmp_project):
        assert pc.should_pause() is False

    def test_no_completions_returns_false(self, active_pipeline):
        assert pc.should_pause() is False

    def test_pause_at_chunk_boundary(self, active_pipeline):
        # chunk_size=4, complete 4 agents (0..3) — should pause before 5th
        for i in range(4):
            pc.mark_in_progress()
            pc.complete_step(run_id=f"run-{i}")
        assert pc.should_pause() is True

    def test_no_pause_before_chunk(self, active_pipeline):
        # Complete only 3 of chunk_size=4 — should NOT pause
        for i in range(3):
            pc.mark_in_progress()
            pc.complete_step(run_id=f"run-{i}")
        assert pc.should_pause() is False

    def test_no_pause_when_all_done(self, tmp_project):
        # 4 agents, chunk_size=4 → completed=4, remaining=0 → no pause
        pc.init(
            task_original="X",
            classified_as="trivial-fix",
            story_id="",
            stage="scale",
            agents=[("a", "r"), ("b", "r"), ("c", "r"), ("d", "r")],
            chunk_size=4,
        )
        for i in range(4):
            pc.mark_in_progress()
            pc.complete_step()
        assert pc.should_pause() is False

    def test_multi_chunk_pipeline(self, tmp_project):
        # 10 agents, chunk_size=2
        agents = [(f"agent-{i}", "role") for i in range(10)]
        pc.init(
            task_original="Big task",
            classified_as="full-stack-feature",
            story_id="",
            stage="scale",
            agents=agents,
            chunk_size=2,
        )
        # Complete 2 → should pause
        for i in range(2):
            pc.mark_in_progress()
            pc.complete_step()
        assert pc.should_pause() is True

        # Unpause, complete 2 more (total 4) → should pause again
        pc.unpause()
        for i in range(2):
            pc.mark_in_progress()
            pc.complete_step()
        assert pc.should_pause() is True

    def test_trivial_pipeline_no_pause(self, tmp_project):
        # 2 agents, chunk_size=4 → never pauses
        pc.init(
            task_original="Fix typo",
            classified_as="trivial-fix",
            story_id="",
            stage="scale",
            agents=[("quick-flow", "fix"), ("verifier", "verify")],
            chunk_size=4,
        )
        pc.mark_in_progress()
        pc.complete_step()
        assert pc.should_pause() is False
        pc.mark_in_progress()
        pc.complete_step()
        assert pc.should_pause() is False


class TestArchive:
    def test_archives_and_cleans(self, active_pipeline):
        # Create preamble file to test cleanup
        preamble = session_path(pc.PREAMBLE_FILENAME)
        preamble.parent.mkdir(parents=True, exist_ok=True)
        preamble.write_text("preamble content")

        dest = pc.archive()
        assert dest is not None
        assert dest.exists()
        assert "pipeline-state-" in dest.name
        assert active_pipeline["pipeline_id"] in dest.name
        # Original is gone
        assert not session_path(pc.STATE_FILENAME).exists()
        # Preamble cleaned up
        assert not preamble.exists()

    def test_archive_marks_completed(self, active_pipeline):
        dest = pc.archive()
        archived = yaml.safe_load(dest.read_text())
        assert archived["status"] == "completed"
        assert "completed_at" in archived

    def test_archive_no_state(self, tmp_project):
        assert pc.archive() is None


class TestAbandon:
    def test_abandon_marks_failed(self, active_pipeline):
        dest = pc.abandon()
        assert dest is not None
        archived = yaml.safe_load(dest.read_text())
        assert archived["status"] == "failed"
        assert "abandoned_at" in archived
        assert not session_path(pc.STATE_FILENAME).exists()

    def test_abandon_no_state(self, tmp_project):
        assert pc.abandon() is None

    def test_abandon_cleans_preamble(self, active_pipeline):
        preamble = session_path(pc.PREAMBLE_FILENAME)
        preamble.parent.mkdir(parents=True, exist_ok=True)
        preamble.write_text("content")
        pc.abandon()
        assert not preamble.exists()


class TestRenderStatus:
    def test_no_pipeline(self, tmp_project):
        assert pc.render_status() == "No active pipeline."

    def test_active_pipeline(self, active_pipeline):
        output = pc.render_status()
        assert "Add Stripe checkout" in output
        assert "full-stack-feature" in output
        assert "0/6" in output
        assert "architect" in output

    def test_paused_pipeline(self, active_pipeline):
        pc.mark_in_progress()
        pc.complete_step()
        pc.pause(reason="chunk_budget")
        output = pc.render_status()
        assert "PAUSED" in output
        assert "chunk_budget" in output


class TestGetState:
    def test_returns_none_when_no_state(self, tmp_project):
        assert pc.get_state() is None

    def test_returns_state(self, active_pipeline):
        state = pc.get_state()
        assert state["pipeline_id"] == active_pipeline["pipeline_id"]


class TestResetCurrentStep:
    def test_resets_to_pending(self, active_pipeline):
        pc.mark_in_progress()
        state = pc.reset_current_step()
        assert state["pipeline"][0]["status"] == "pending"
        assert state["pipeline"][0]["run_id"] is None
        assert state["paused"] is None

    def test_clears_pause_on_reset(self, active_pipeline):
        pc.mark_in_progress()
        pc.fail_step(error="boom")  # sets paused + status=failed
        state = pc.reset_current_step()
        assert state["paused"] is None
        assert state["pipeline"][0]["status"] == "pending"

    def test_no_state_raises(self, tmp_project):
        with pytest.raises(FileNotFoundError):
            pc.reset_current_step()

    def test_out_of_bounds_raises(self, tmp_project):
        pc.init("X", "trivial-fix", "", "scale", agents=[("a", "r")])
        pc.mark_in_progress()
        pc.complete_step()
        with pytest.raises(IndexError, match="out of range"):
            pc.reset_current_step()


class TestSkipStep:
    def test_skips_and_advances(self, active_pipeline):
        state = pc.skip_step()
        assert state["pipeline"][0]["status"] == "skipped"
        assert state["current_step"] == 1
        assert state["completed_count"] == 0  # skipped != completed

    def test_skip_clears_pause(self, active_pipeline):
        pc.pause()
        state = pc.skip_step()
        assert state["paused"] is None

    def test_no_state_raises(self, tmp_project):
        with pytest.raises(FileNotFoundError):
            pc.skip_step()

    def test_skip_then_continue(self, active_pipeline):
        pc.skip_step()  # skip architect
        pc.mark_in_progress()  # start lead-dev
        state = pc.complete_step()
        assert state["pipeline"][0]["status"] == "skipped"
        assert state["pipeline"][1]["status"] == "done"
        assert state["completed_count"] == 1
        assert state["current_step"] == 2


class TestUpdateResumeContext:
    def test_appends_artifacts(self, active_pipeline):
        pc.update_resume_context(key_artifacts=["file1.ts", "file2.ts"])
        state = pc.get_state()
        assert state["resume_context"]["key_artifacts"] == ["file1.ts", "file2.ts"]

    def test_appends_decisions(self, active_pipeline):
        pc.update_resume_context(decisions=["Use RPC over REST"])
        pc.update_resume_context(decisions=["Skip caching"])
        state = pc.get_state()
        assert state["resume_context"]["decisions_so_far"] == [
            "Use RPC over REST", "Skip caching"
        ]

    def test_appends_unknowns(self, active_pipeline):
        pc.update_resume_context(open_unknowns=["RLS policy unclear"])
        state = pc.get_state()
        assert state["resume_context"]["open_unknowns"] == ["RLS policy unclear"]

    def test_no_state_raises(self, tmp_project):
        with pytest.raises(FileNotFoundError):
            pc.update_resume_context(key_artifacts=["x"])

    def test_mixed_update(self, active_pipeline):
        pc.update_resume_context(
            key_artifacts=["a.ts"],
            decisions=["d1"],
            open_unknowns=["u1"],
        )
        state = pc.get_state()
        assert state["resume_context"]["key_artifacts"] == ["a.ts"]
        assert state["resume_context"]["decisions_so_far"] == ["d1"]
        assert state["resume_context"]["open_unknowns"] == ["u1"]


class TestInitValidation:
    def test_empty_agents_raises(self, tmp_project):
        with pytest.raises(ValueError, match="must not be empty"):
            pc.init("X", "trivial-fix", "", "scale", agents=[])

    def test_zero_chunk_size_raises(self, tmp_project):
        with pytest.raises(ValueError, match="chunk_size must be >= 1"):
            pc.init("X", "trivial-fix", "", "scale",
                    agents=[("a", "r")], chunk_size=0)

    def test_negative_chunk_size_raises(self, tmp_project):
        with pytest.raises(ValueError, match="chunk_size must be >= 1"):
            pc.init("X", "trivial-fix", "", "scale",
                    agents=[("a", "r")], chunk_size=-1)


class TestBoundsCheck:
    def test_mark_in_progress_past_end_raises(self, tmp_project):
        pc.init("X", "trivial-fix", "", "scale", agents=[("a", "r")])
        pc.mark_in_progress()
        pc.complete_step()
        # current_step is now 1, pipeline has 1 agent
        with pytest.raises(IndexError, match="out of range"):
            pc.mark_in_progress()

    def test_complete_step_past_end_raises(self, tmp_project):
        pc.init("X", "trivial-fix", "", "scale", agents=[("a", "r")])
        pc.mark_in_progress()
        pc.complete_step()
        with pytest.raises(IndexError, match="out of range"):
            pc.complete_step()


class TestCorruptedState:
    def test_corrupted_yaml_returns_none(self, tmp_project):
        pc.init("X", "trivial-fix", "", "scale", agents=[("a", "r")])
        pc._state_path().write_text("{{{invalid yaml", encoding="utf-8")
        assert pc.get_state() is None

    def test_empty_file_returns_none(self, tmp_project):
        path = pc._state_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")
        assert pc.get_state() is None

    def test_non_dict_yaml_returns_none(self, tmp_project):
        path = pc._state_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("- just a list\n- not a dict\n", encoding="utf-8")
        assert pc.get_state() is None


class TestRenderStatusResumeIndicator:
    def test_shows_next_step_when_paused(self, active_pipeline):
        pc.mark_in_progress()
        pc.complete_step()
        pc.pause(reason="chunk_budget")
        output = pc.render_status()
        # The > marker should appear at step 2 even when paused
        assert "> [  ] 2." in output


class TestCrashRecovery:
    """Verify that an in_progress step is detectable after a crash."""

    def test_detect_in_progress_step(self, active_pipeline):
        pc.mark_in_progress()
        # Simulate crash — read state directly
        state = pc.get_state()
        in_progress_steps = [
            (i, s) for i, s in enumerate(state["pipeline"])
            if s["status"] == "in_progress"
        ]
        assert len(in_progress_steps) == 1
        assert in_progress_steps[0][0] == 0
        assert in_progress_steps[0][1]["agent"] == "architect"
