#!/usr/bin/env bash
# cleanup-talk.sh — delete pptx-to-slidev's intermediate artifacts.
#
# Usage:
#   .claude/scripts/cleanup-talk.sh <talk-dir>
#
# Removes (only inside <talk-dir>, never outside):
#   _analysis.json
#   _analysis.md
#   _thumbnails/   (whole dir)
#   _shots/        (verify-talk.sh output)
#   dist/          (slidev build output)
#
# Prints what it removed. Safe to re-run.

set -euo pipefail

[[ $# -eq 1 ]] || { echo "usage: $0 <talk-dir>" >&2; exit 2; }
TALK_DIR="$1"
[[ -d "$TALK_DIR" ]] || { echo "cleanup-talk: no such dir: $TALK_DIR" >&2; exit 1; }
[[ -f "$TALK_DIR/slides.md" ]] || {
  echo "cleanup-talk: refusing — $TALK_DIR has no slides.md (is this a talk dir?)" >&2
  exit 1
}

TALK_DIR="$(cd "$TALK_DIR" && pwd)"
cd "$TALK_DIR"

removed=0
for path in _analysis.json _analysis.md _thumbnails _shots dist; do
  if [[ -e "$path" ]]; then
    rm -rf "$path"
    echo "removed: $TALK_DIR/$path"
    removed=$((removed + 1))
  fi
done

if [[ "$removed" -eq 0 ]]; then
  echo "cleanup-talk: nothing to remove in $TALK_DIR"
fi
