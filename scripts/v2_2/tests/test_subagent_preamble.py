"""Tests for subagent_preamble.py."""
import pytest

from scripts.v2_2 import subagent_preamble as sp
from scripts.v2_2.memory import session_path


@pytest.fixture
def mb_with_skills(tmp_project_with_mb_installed):
    """tmp_project with the 3 core skill SKILL.md files populated."""
    project = tmp_project_with_mb_installed
    mb = project / ".claude" / "mb"

    for skill_name in sp.CORE_SKILLS:
        skill_dir = mb / "skills" / "core" / skill_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: core/{skill_name}\n---\n\n## {skill_name} rules\n\nDo the thing.\n"
        )

    return project


@pytest.fixture
def mb_missing_skill(tmp_project_with_mb_installed):
    """tmp_project with only 2 of 3 core skills — handoff-contract missing."""
    project = tmp_project_with_mb_installed
    mb = project / ".claude" / "mb"

    for skill_name in ["evidence-rules", "run-summary"]:
        skill_dir = mb / "skills" / "core" / skill_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(f"# {skill_name}\n")

    return project


class TestCompose:
    def test_returns_string_with_all_skills(self, mb_with_skills):
        result = sp.compose()
        assert isinstance(result, str)
        for skill_name in sp.CORE_SKILLS:
            assert f"core/{skill_name}" in result
            assert f"{skill_name} rules" in result

    def test_contains_preamble_header(self, mb_with_skills):
        result = sp.compose()
        assert "subagent-preamble" in result
        assert "MANDATORY" in result

    def test_skills_separated_by_divider(self, mb_with_skills):
        result = sp.compose()
        assert result.count("---") >= len(sp.CORE_SKILLS)

    def test_missing_skill_raises(self, mb_missing_skill):
        with pytest.raises(FileNotFoundError, match="handoff-contract"):
            sp.compose()


class TestComposeAndWrite:
    def test_writes_file(self, mb_with_skills):
        path = sp.compose_and_write()
        assert path.exists()
        assert path == session_path(sp.PREAMBLE_FILENAME)

        content = path.read_text()
        for skill_name in sp.CORE_SKILLS:
            assert skill_name in content

    def test_creates_parent_dirs(self, mb_with_skills):
        # session dir may not exist yet
        session_dir = session_path(sp.PREAMBLE_FILENAME).parent
        if session_dir.exists():
            import shutil
            shutil.rmtree(session_dir)

        path = sp.compose_and_write()
        assert path.exists()

    def test_overwrites_existing(self, mb_with_skills):
        path1 = sp.compose_and_write()
        content1 = path1.read_text()

        # Modify a skill
        mb = mb_with_skills / ".claude" / "mb"
        (mb / "skills" / "core" / "evidence-rules" / "SKILL.md").write_text(
            "---\nname: core/evidence-rules\n---\n\n## UPDATED rules\n\nNew content.\n"
        )

        path2 = sp.compose_and_write()
        content2 = path2.read_text()

        assert path1 == path2
        assert "UPDATED" in content2
        assert "UPDATED" not in content1
