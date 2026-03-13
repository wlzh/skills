#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR"

# check returns stdout only when there are new videos
node scripts/youtube-tracker.js check
