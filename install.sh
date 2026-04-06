#!/bin/bash
# mb-framework installer
# Run from project root after: git submodule add git@github.com:Yanick-mj/mb-framework.git .claude/mb

set -e

MB_DIR=".claude/mb"

if [ ! -d "$MB_DIR" ]; then
  echo "Error: $MB_DIR not found. Run: git submodule add git@github.com:Yanick-mj/mb-framework.git .claude/mb"
  exit 1
fi

echo "Installing mb-framework..."

# 1. Symlink commands → .claude/commands/mb/
mkdir -p .claude/commands
ln -sfn "../mb/commands" .claude/commands/mb
echo "  Commands linked"

# 2. Symlink agents → .claude/skills/mb-{name}/
mkdir -p .claude/skills
for agent_dir in "$MB_DIR"/agents/*/; do
  agent_name=$(basename "$agent_dir")
  ln -sfn "../../$MB_DIR/agents/$agent_name" ".claude/skills/mb-$agent_name"
done
echo "  Agents linked as skills"

# 3. Symlink skills → .claude/skills/mb-skill-{name}/
for skill_dir in "$MB_DIR"/skills/*/; do
  [ -d "$skill_dir" ] || continue
  skill_name=$(basename "$skill_dir")
  [ "$skill_name" = "_README.md" ] && continue
  ln -sfn "../../$MB_DIR/skills/$skill_name" ".claude/skills/mb-skill-$skill_name"
done
echo "  Skills linked"

# 4. Install git hook
mkdir -p .githooks
if [ -f "$MB_DIR/templates/code/pre-commit.sh" ]; then
  cp "$MB_DIR/templates/code/pre-commit.sh" .githooks/pre-commit
  chmod +x .githooks/pre-commit
  git config core.hooksPath .githooks
  echo "  Git hook installed"
fi

echo ""
echo "mb-framework installed successfully!"
echo ""
echo "Available commands:"
echo "  /mb:feature \"description\"  — Implement a feature"
echo "  /mb:sprint                 — Execute next story"
echo "  /mb:fix \"bug\"              — Fix a bug"
echo "  /mb:review                 — Code review"
echo "  /mb:init                   — Scan project (run this first!)"
