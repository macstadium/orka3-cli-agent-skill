#!/usr/bin/env bash
set -euo pipefail

# Build a .skill archive from the orka3-cli/ directory.
#
# Usage:
#   ./scripts/build-skill.sh [VERSION]
#
# VERSION defaults to the latest git tag (stripped of the leading "v").
# The archive is written to dist/orka3-cli-v<VERSION>.skill (a zip file).

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKILL_DIR="$REPO_ROOT/orka3-cli"
DIST_DIR="$REPO_ROOT/dist"

# Resolve version
if [[ ${1:-} ]]; then
  VERSION="$1"
else
  TAG="$(git -C "$REPO_ROOT" describe --tags --abbrev=0 2>/dev/null || true)"
  if [[ -z "$TAG" ]]; then
    echo "Error: no version argument and no git tag found." >&2
    exit 1
  fi
  VERSION="${TAG#v}"
fi

# Validate skill directory
if [[ ! -f "$SKILL_DIR/SKILL.md" ]]; then
  echo "Error: orka3-cli/SKILL.md not found." >&2
  exit 1
fi

ARCHIVE="$DIST_DIR/orka3-cli-v${VERSION}.skill"

mkdir -p "$DIST_DIR"
rm -f "$ARCHIVE"

# Build zip with SKILL.md and references/ at zip root (no wrapper directory)
(cd "$SKILL_DIR" && zip -r "$ARCHIVE" SKILL.md references/)

echo "Built $ARCHIVE"
echo "Install: unzip $ARCHIVE -d ~/.claude/skills/orka3-cli"
