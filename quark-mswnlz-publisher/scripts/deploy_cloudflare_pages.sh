#!/bin/bash
set -euo pipefail

# Cloudflare Pages 部署脚本（取代 GitHub Actions deploy.yml）
# 流程：本地全量构建 VitePress → 校验 → Gitee 私有快照 → Cloudflare Pages → Telegram 通知。
# 依赖：content-source/ 软链到本地 11 个内容仓库 + duanku-guides；wrangler 已登录。

CF_PROJECT_NAME="${CF_PAGES_PROJECT:-doc869hr}"

# 自动加载 secrets.env（与 mswnlz_publish.py 的 SECRETS_ENV 约定一致；已 gitignore）
SECRETS_ENV="/Users/m/document/QNSZ/project/QuarkPanTool/config/secrets.env"
if [ -f "$SECRETS_ENV" ]; then
  set -a; . "$SECRETS_ENV"; set +a
fi
SKIP_NOTIFY="${SKIP_NOTIFY:-0}"
SITE_REPO="${MSWNLZ_SITE_REPO:-}"

find_site_repo() {
  if [ -n "$SITE_REPO" ] && [ -d "$SITE_REPO/.git" ]; then
    printf '%s\n' "$SITE_REPO"
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

# 幂等建立 content-source/ 软链（GitHub 已不可用，内容一律取本地仓库）
ensure_content_source() {
  local base="/Users/m/document/QNSZ/project/mswnlz-github"
  local repos=(AIknowledge auto book chinese-traditional cross-border curriculum edu-knowlege healthy movies self-media tools)
  mkdir -p content-source
  for repo in "${repos[@]}"; do
    # -e 跟随符号链接；坏链（相对路径写错等）直接删了重建为绝对路径
    [ -e "content-source/$repo" ] || { rm -f "content-source/$repo"; ln -s "$base/$repo" "content-source/$repo"; }
  done
  [ -e "content-source/duanku-guides" ] || { rm -f "content-source/duanku-guides"; ln -s "/Users/m/document/QNSZ/project/Hexo-BLog/duanku-guides" "content-source/duanku-guides"; }
}

# wrangler 走代理（本机小火箭 7798）；已设代理则尊重现状
ensure_proxy() {
  if [ -z "${https_proxy:-}${HTTPS_PROXY:-}" ] && nc -z 127.0.0.1 7798 2>/dev/null; then
    export https_proxy=http://127.0.0.1:7798 http_proxy=http://127.0.0.1:7798
    echo "[proxy] 使用 127.0.0.1:7798"
  fi
}

# 频道通知：token 只从环境变量读；未设置时从既有 notify_telegram.py 的默认值兜底（不新增硬编码副本）
send_channel_notify() {
  [ "$SKIP_NOTIFY" = "1" ] && { echo "[notify] SKIP_NOTIFY=1 跳过"; return 0; }
  local bot_token="${TELEGRAM_BOT_TOKEN:-}"
  if [ -z "$bot_token" ]; then
    bot_token=$(python3 - <<'PY' 2>/dev/null || true
import sys
sys.path.insert(0, "/Users/m/document/QNSZ/project/skills_wlzh_pri/duanku-youtube-publish/scripts")
try:
    from notify_telegram import DEFAULT_BOT_TOKEN
    print(DEFAULT_BOT_TOKEN)
except Exception:
    pass
PY
)
  fi
  local channel="${TELEGRAM_CHANNEL_ID:-@dabaziyuan}"
  if [ -z "$bot_token" ]; then
    echo "[notify] 未找到 TELEGRAM_BOT_TOKEN，跳过频道通知"
    return 0
  fi
  local current_month url text
  current_month=$(date +'%Y%m')
  url="https://doc.869hr.uk"
  text=$'🌐 资源站已更新上线\n\n🔗 总站：'"${url}"$'\n📦 资料频道：https://t.me/dabaziyuan'
  curl -s -X POST "https://api.telegram.org/bot${bot_token}/sendMessage" \
    --data-urlencode "chat_id=${channel}" \
    --data-urlencode "text=${text}" >/dev/null \
    && echo "[notify] 频道通知已发送 (${channel})" \
    || echo "[notify] WARN: 频道通知发送失败（不影响部署）"
}

REPO_DIR="$(find_site_repo)" || {
  echo "Cannot find site repo. Set MSWNLZ_SITE_REPO." >&2
  exit 1
}
cd "$REPO_DIR"

ensure_content_source

if [ -n "$(git status --porcelain --untracked-files=all)" ]; then
  echo "资源站源码仓库存在发布前变更；请先独立审查提交，避免自动备份混入人工改动。" >&2
  git status --short >&2
  exit 1
fi

export SOURCE_BASE_DIR=./content-source TARGET_DOCS_DIR=./docs CONTENT_SOURCE_DIR=./content-source
export DUANKU_GUIDES_DIR=./content-source/duanku-guides ENABLE_ADSENSE=false

echo "=== [1/7] 同步内容 copy_content.sh"
bash ./copy_content.sh

echo "=== [2/7] 同步目录页签 sync-tabs.sh"
bash ./scripts/sync-tabs.sh --auto

# fetch-commits 依赖 GitHub API（仓库已随账号封禁不可用），沿用仓库内现有 commits.json
echo "=== [3/7] 构建教程枢纽 build:guides"
npm run build:guides

echo "=== [4/7] 构建 VitePress"
npm run build

echo "=== [5/7] 校验产物"
npm run validate

echo "=== [6/7] 备份已校验源码到 Gitee 私有仓库"
bash ./scripts/push-gitee-backup.sh

ensure_proxy
echo "=== [7/7] 部署 Cloudflare Pages（项目：${CF_PROJECT_NAME}）"
wrangler pages deploy docs/.vitepress/dist \
  --project-name="${CF_PROJECT_NAME}" \
  --branch=main \
  --commit-dirty=true

echo "=== 部署完成：https://${CF_PROJECT_NAME}.pages.dev （自定义域名 doc.869hr.uk）"
send_channel_notify
