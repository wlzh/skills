#!/bin/bash
set -euo pipefail

find_site_repo() {
  if [ -n "${MSWNLZ_SITE_REPO:-}" ] && [ -d "$MSWNLZ_SITE_REPO/.git" ]; then
    printf '%s\n' "$MSWNLZ_SITE_REPO"
    return 0
  fi

  local candidates=(
    "/Users/m/document/QNSZ/project/mswnlz-github/mswnlz.github.io"
    "/Users/m/document/QNSZ/project/mswnlz/mswnlz.github.io"
  )

  for repo in "${candidates[@]}"; do
    if [ -d "$repo/.git" ]; then
      printf '%s\n' "$repo"
      return 0
    fi
  done

  return 1
}

REPO_DIR="$(find_site_repo)" || {
  echo "Cannot find mswnlz.github.io repo. Set MSWNLZ_SITE_REPO." >&2
  exit 1
}

cd "$REPO_DIR"

git checkout main
git pull --rebase

# Validate the redesigned site pipeline before triggering Pages.
npm run build
npm run validate

# Keep generated build artifacts out of the source commit. GitHub Actions builds the production artifact.
git restore docs/.vitepress/dist 2>/dev/null || true
git restore docs/public/resource-catalog.json docs/.vitepress/generated/resourceCatalog.ts 2>/dev/null || true
tmp_dist="/tmp/quark-mswnlz-publisher-dist-$$"
mkdir -p "$tmp_dist"
git ls-files -o --exclude-standard docs/.vitepress/dist | while read -r file; do
  [ -f "$file" ] || continue
  mv "$file" "$tmp_dist/"
done

git commit --allow-empty -m "chore: trigger site rebuild"
git push origin main

echo "Triggered rebuild via push after catalog/build validation."
