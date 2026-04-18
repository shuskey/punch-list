#!/usr/bin/env bash
# install-skills.sh
# Creates symlinks so Claude Code can discover skills from this repo.
#
# Chain: ~/.claude/skills/<name> -> ~/.agents/skills/<name> -> <repo>/skills/<name>
# Edit skills in <repo>/skills/ — changes are live immediately.
#
# Usage: ./punch-list/install-skills.sh [--force]

SKILLS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/skills" && pwd)"
AGENTS_DIR="$HOME/.agents/skills"
CLAUDE_DIR="$HOME/.claude/skills"
FORCE=false

for arg in "$@"; do
  [[ "$arg" == "--force" ]] && FORCE=true
done

mkdir -p "$AGENTS_DIR"
mkdir -p "$CLAUDE_DIR"

echo "Installing skills from: $SKILLS_DIR"
echo ""

installed=0
skipped=0
replaced=0

link_one() {
  local target="$1"
  local dest="$2"
  local label="$3"
  local name="$4"

  if [[ -L "$target" ]]; then
    existing="$(readlink "$target")"
    if [[ "$existing" == "$dest" || "$existing" == "${dest%/}" ]]; then
      echo "  ✓ [$label] $name"
      skipped=$((skipped + 1))
    elif [[ "$FORCE" == "true" ]]; then
      rm "$target" && ln -s "$dest" "$target"
      echo "  ↺ [$label] $name  (replaced)"
      replaced=$((replaced + 1))
    else
      echo "  ! [$label] $name  (points elsewhere — use --force)"
      skipped=$((skipped + 1))
    fi
  elif [[ -e "$target" ]]; then
    if [[ "$FORCE" == "true" ]]; then
      rm -rf "$target" && ln -s "$dest" "$target"
      echo "  ↺ [$label] $name  (replaced existing)"
      replaced=$((replaced + 1))
    else
      echo "  ! [$label] $name  (path exists — use --force)"
      skipped=$((skipped + 1))
    fi
  else
    ln -s "$dest" "$target"
    echo "  + [$label] $name"
    installed=$((installed + 1))
  fi
}

for skill_path in "$SKILLS_DIR"/*/; do
  skill_name="$(basename "$skill_path")"
  link_one "$AGENTS_DIR/$skill_name" "$skill_path"                         "agents" "$skill_name"
  link_one "$CLAUDE_DIR/$skill_name" "../../.agents/skills/$skill_name"    "claude" "$skill_name"
done

echo ""
echo "Installing punchlist.py to ~/.punch-list/"
mkdir -p "$HOME/.punch-list"
cp "$(dirname "${BASH_SOURCE[0]}")/punchlist.py" "$HOME/.punch-list/punchlist.py"
echo "  + punchlist.py"

echo ""
echo "Installing Python dependency: typer"
pip install typer --quiet && echo "  + typer" || echo "  ! pip install typer failed — install manually"

echo ""
echo "Done. Installed: $installed  Replaced: $replaced  Skipped: $skipped"
echo ""
echo "Edit skills in: $SKILLS_DIR"
