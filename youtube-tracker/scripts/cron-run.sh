#!/usr/bin/env bash
set -euo pipefail

# youtube-tracker cron runner (v3.0+)
# - Runs `notify` command (parallel, Telegram-ready output)
# - If stdout is empty -> exit 0 with no output (no new videos)
# - If stdout has content -> print it (new videos found)

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR"

node scripts/youtube-tracker-rss.js notify 2>/dev/null || true
