#!/usr/bin/env bash
set -euo pipefail

# This runner is designed for cron usage.
# - It runs the check.
# - If output is empty -> exit 0 with no stdout.
# - If output is non-empty -> print it to stdout.

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR"

OUT="$(node scripts/youtube-tracker.js check 2>/dev/null || true)"

# Only print when there is real content
if [ -n "${OUT//[[:space:]]/}" ]; then
  echo "$OUT"
fi
