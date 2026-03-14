#!/bin/bash
set -euo pipefail

REPO_DIR="/Users/m./Documents/QNSZ/project/mswnlz/mswnlz.github.io"

cd "$REPO_DIR"

git checkout main
# best-effort pull
(git pull --rebase) || true

git commit --allow-empty -m "chore: trigger site rebuild"
git push origin main

echo "Triggered rebuild via push."
