#!/bin/bash
# 兼容入口：站点已迁移 Cloudflare Pages（GitHub 账号封禁后无 Actions 可触发），
# 现在的"重建"= 本地全量构建 + wrangler 部署 + 频道通知。
set -euo pipefail
exec bash "$(dirname "$0")/deploy_cloudflare_pages.sh" "$@"
