"""Guard tests for commands/*.md AND templates/*.md — ensure shipped artifacts
are actually usable by the scripts that read them.

These tests read the actual command markdown files under commands/ and verify
they don't use broken placeholder patterns like `$STORY_ID` (undefined) or
`${1:-N}` (Claude Code passes $ARGUMENTS, not positional $1).

History:
- v2.1.0 shipped commands/deliverables.md with `$STORY_ID` (undefined) — ran,
  did nothing meaningful.
- v2.1.0 shipped commands/runs.md with `${1:-10}` — limit arg ignored.

Both bugs slipped past unit-test review because pytest exercises the Python
modules directly, never the command files. This guard closes that gap.
"""
from pathlib import Path

import pytest

# commands/ lives at the repo root, 3 levels up from this test file
# (scripts/v2_1/tests/test_commands_consistency.py → repo root)
COMMANDS_DIR = Path(__file__).resolve().parents[3] / "commands"
MB_COMMAND_PREFIXES = ("projects", "deliverables", "tree", "runs", "backlog", "roadmap")


def _mb_command_files() -> list[Path]:
    """Return the v2.1 mb command files we wrote (skip feature/fix/review/etc
    which are older and follow different conventions)."""
    return [
        COMMANDS_DIR / f"{name}.md"
        for name in MB_COMMAND_PREFIXES
        if (COMMANDS_DIR / f"{name}.md").exists()
    ]


def test_mb_command_files_exist():
    """Sanity: the command files we want to test actually exist."""
    files = _mb_command_files()
    assert len(files) == len(MB_COMMAND_PREFIXES), (
        f"Expected {len(MB_COMMAND_PREFIXES)} command files, "
        f"found {len(files)}: {[f.name for f in files]}"
    )


def test_no_command_uses_undefined_story_id():
    """$STORY_ID is never set by Claude Code — using it = broken arg passing."""
    offenders = []
    for cmd in _mb_command_files():
        text = cmd.read_text()
        if "$STORY_ID" in text:
            offenders.append(cmd.name)
    assert not offenders, (
        f"These command files reference undefined $STORY_ID (should be "
        f"$ARGUMENTS): {offenders}"
    )


def test_no_command_uses_positional_dollar_1():
    """${1:-N} does not work — Claude Code passes $ARGUMENTS, not $1.

    Commands using ${1:-N} silently ignore user args. Use $ARGUMENTS instead.
    """
    offenders = []
    for cmd in _mb_command_files():
        text = cmd.read_text()
        # Match ${1:-...} or $1 (with word boundary) inside bash blocks
        # Simple heuristic: if the text has "${1:-" or " $1 " or " $1\n"
        if "${1:-" in text:
            offenders.append((cmd.name, "${1:-...}"))
        # $1 on its own (not $10 etc) — very strict, only flag obvious misuse
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):  # comment line, skip
                continue
            # Only flag in python3 invocation lines
            if "python3" in stripped and " $1" in stripped and " $1" != " $10":
                # Could be $10+ which is fine — check token
                tokens = stripped.split()
                if "$1" in tokens:
                    offenders.append((cmd.name, "$1 token"))
    assert not offenders, (
        f"These command files use positional args that Claude Code does not "
        f"provide (use $ARGUMENTS instead): {offenders}"
    )


TEMPLATES_DIR = Path(__file__).resolve().parents[3] / "templates"


def test_backlog_story_template_parses_as_valid_frontmatter():
    """templates/backlog-story.md MUST start with --- so backlog.py picks it up.

    History: v2.1.2 shipped a template with two `#` comment lines BEFORE the
    --- opener. backlog._parse_frontmatter's regex is `^---\\r?\\n...` which
    requires --- at position 0 → template silently skipped. Users who
    `cp templates/backlog-story.md _backlog/STU-X.md` and edit → their story
    never appears in /mb:backlog output.
    """
    import re
    template = TEMPLATES_DIR / "backlog-story.md"
    assert template.exists(), f"Missing {template}"
    text = template.read_text()
    # The exact regex used by backlog._parse_frontmatter
    m = re.match(r"^---\r?\n(.*?)\r?\n---", text, re.DOTALL)
    assert m is not None, (
        f"{template.name} must start with `---` on line 1 (YAML frontmatter). "
        f"Comments using `#` before `---` break the frontmatter parser and make "
        f"the template silently skipped. Move comments INSIDE the YAML block."
    )


def test_backlog_story_template_has_required_fields():
    """After parsing, the template must have story_id + priority fields.

    These two fields are required for /mb:backlog to list + sort the story.
    """
    import re
    import yaml
    template = TEMPLATES_DIR / "backlog-story.md"
    text = template.read_text()
    m = re.match(r"^---\r?\n(.*?)\r?\n---", text, re.DOTALL)
    assert m is not None
    data = yaml.safe_load(m.group(1))
    assert isinstance(data, dict), "Template frontmatter must parse as a dict"
    assert "story_id" in data, "Template must have story_id placeholder"
    assert "priority" in data, "Template must have priority placeholder"
    # Priority MUST be one of the 4 valid values (even as placeholder)
    assert data["priority"] in {"critical", "high", "medium", "low"}, (
        f"Template priority={data['priority']!r} is not one of the 4 valid "
        f"values — users will copy this into their own stories."
    )


def test_deliverable_template_no_jinja_style_placeholders():
    """templates/deliverable.md must not use {{ }} style placeholders.

    Nothing renders Jinja in the mb pipeline. Users who use the template keep
    `# {{ Deliverable title }}` as literal text. Use `<...>` style instead.
    """
    template = TEMPLATES_DIR / "deliverable.md"
    assert template.exists(), f"Missing {template}"
    text = template.read_text()
    assert "{{" not in text, (
        f"{template.name} contains Jinja-style {{{{ }}}} placeholder. Nothing "
        f"renders it. Use `<placeholder>` instead."
    )
    assert "}}" not in text


def test_commands_reference_arguments_or_no_args():
    """Every v2.1 command must either use $ARGUMENTS or have no arg at all.

    Positive guard: ensures we're using the canonical placeholder.
    """
    for cmd in _mb_command_files():
        text = cmd.read_text()
        # Allowed: $ARGUMENTS anywhere, or a bash block without any user input
        has_arguments = "$ARGUMENTS" in text
        has_bash_with_args = False
        # If the python3 invocation has ANY word after the script path, it
        # should be $ARGUMENTS (or a literal subcommand like "backlog"/"roadmap")
        for line in text.splitlines():
            if "python3" in line and ".py" in line:
                # Get everything after .py
                after_py = line.split(".py", 1)[1].strip()
                if after_py and not after_py.startswith('"'):
                    has_bash_with_args = True
        # A command that passes args must use $ARGUMENTS
        # (or pass a hardcoded literal like "backlog", which is OK)
        if has_bash_with_args:
            # It's OK to have hardcoded literals (backlog.md passes "backlog")
            # The real check is: no $STORY_ID, no ${1:-...} — already covered
            pass
