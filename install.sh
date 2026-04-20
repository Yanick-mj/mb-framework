#!/bin/bash
# mb-framework installer
# Run from project root after: git submodule add git@github.com:Yanick-mj/mb-framework.git .claude/mb

set -e

MB_DIR=".claude/mb"

if [ ! -d "$MB_DIR" ]; then
  echo "Error: $MB_DIR not found. Run: git submodule add git@github.com:Yanick-mj/mb-framework.git .claude/mb"
  exit 1
fi

NO_STAGE=false
for arg in "$@"; do
  case "$arg" in
    --no-stage) NO_STAGE=true ;;
  esac
done

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

# 2b. (v2) Symlink early-stage agents → .claude/skills/mb-early-{name}/
if [ -d "$MB_DIR/agents-early" ]; then
  for agent_dir in "$MB_DIR"/agents-early/*/; do
    [ -d "$agent_dir" ] || continue
    agent_name=$(basename "$agent_dir")
    ln -sfn "../../$MB_DIR/agents-early/$agent_name" ".claude/skills/mb-early-$agent_name"
  done
  echo "  Early-stage agents linked"
fi

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

# 5. (v2) Stage initialization
if [ "$NO_STAGE" = false ] && [ ! -f "mb-stage.yaml" ]; then
  echo ""
  echo "── Stage Setup (v2) ──────────────────────────────────────"
  echo "What stage is this project in?"
  echo "  1) discovery — validating an idea, no users yet"
  echo "  2) mvp       — building janky wedge, looking for first paying users"
  echo "  3) pmf       — first customers, looking for product-market fit"
  echo "  4) scale     — production-grade, recurring revenue (default)"
  echo ""
  read -r -p "Choose [1-4] (default: 4): " stage_choice
  case "$stage_choice" in
    1) chosen_stage="discovery" ;;
    2) chosen_stage="mvp" ;;
    3) chosen_stage="pmf" ;;
    *) chosen_stage="scale" ;;
  esac
  today=$(date +%Y-%m-%d)
  cp "$MB_DIR/mb-stage.yaml.template" mb-stage.yaml
  # Patch stage and date
  if [ "$(uname)" = "Darwin" ]; then
    sed -i '' "s/^stage: discovery/stage: $chosen_stage/" mb-stage.yaml
    sed -i '' "s/^since: YYYY-MM-DD/since: $today/" mb-stage.yaml
  else
    sed -i "s/^stage: discovery/stage: $chosen_stage/" mb-stage.yaml
    sed -i "s/^since: YYYY-MM-DD/since: $today/" mb-stage.yaml
  fi
  echo "  mb-stage.yaml created (stage: $chosen_stage)"
fi

# 5b. (v2.1) Auto-register project in user registry
if [ -f "mb-stage.yaml" ]; then
  # pwd -P resolves symlinks, giving a stable absolute path for the registry
  project_path="$(pwd -P)"
  project_name=$(basename "$project_path")
  project_stage=$(grep '^stage:' mb-stage.yaml | awk '{print $2}')
  MB_REG_NAME="$project_name" MB_REG_PATH="$project_path" MB_REG_STAGE="$project_stage" \
  PYTHONPATH="$MB_DIR/scripts" python3 -c "
import os
from v2_1 import projects
name = os.environ['MB_REG_NAME']
path = os.environ['MB_REG_PATH']
stage = os.environ['MB_REG_STAGE']
projects.add(name=name, path=path, stage=stage)
print(f'  Registered in ~/.mb/projects.yaml ({name}, stage:{stage})')
" 2>/dev/null || echo "  (skipped registration — python3 or pyyaml missing)"
fi

# 5c. (v2.1) Offer to install shell helper
if [ "$NO_STAGE" = false ] && [ -n "${ZDOTDIR:-$HOME}" ]; then
  rc_file="${ZDOTDIR:-$HOME}/.zshrc"
  [ ! -f "$rc_file" ] && rc_file="$HOME/.bashrc"
  mb_framework_abs="$(cd "$MB_DIR" && pwd)"
  helper_marker="# mb-framework shell helper"
  if ! grep -qF "$helper_marker" "$rc_file" 2>/dev/null; then
    echo ""
    read -rp "Install 'mb' shell helper in $rc_file? [y/N] " answer
    if [[ "$answer" =~ ^[Yy]$ ]]; then
      echo "" >> "$rc_file"
      echo "$helper_marker" >> "$rc_file"
      echo "export MB_FRAMEWORK_PATH=\"$mb_framework_abs\"" >> "$rc_file"
      echo "source \"\$MB_FRAMEWORK_PATH/scripts/v2_1/mb_shell_helper.sh\"" >> "$rc_file"
      echo "  Added 'mb' helper to $rc_file — run 'source $rc_file' to activate"
    fi
  fi
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
echo "  /mb:stage                  — (v2) View/manage project stage"
echo "  /mb:validate \"idea\"        — (v2) Discovery: validate an idea"
echo "  /mb:ship \"wedge\"           — (v2) MVP: ship a wedge product"
