# wlzh-youtube-tracker（YouTube 频道新视频追踪）

定时追踪一组 YouTube 频道是否有**新视频上传**。

## 版本历史

### v3.0.0 (2026-06-06) - 并行抓取 + 通知模式
**重大优化**：消除 cron 失败问题，不再依赖 LLM。

- ✅ 并行 HTTP 抓取（15 个并发 curl 进程）
- ✅ ~10 倍加速：55 个频道 ~4-5 秒（原来 ~45 秒）
- ✅ 新增 `notify` 命令，输出 Telegram 格式消息
- ✅ Cron 使用 `systemEvent` 替代 `agentTurn`，无 API 限速、无超时
- ✅ 预期成功率：~99%（原来 ~64%）

### v2.1.0 (2026-06-05) - 代理支持
- 自动代理检测，中国大陆必须

### v2.0.0 (2026-03-17) - RSS 模式
- 使用 YouTube RSS feeds，无需 API Key，无配额限制

---

## ✅ 输出格式

### `check` 命令（原始格式）
```
频道：最佳拍档
标题：Anthropic呼吁按下AI暂停键？
链接：https://www.youtube.com/watch?v=xxx
```

### `notify` 命令（Telegram 格式）
```
📺 最佳拍档
🎬 Anthropic呼吁按下AI暂停键？
🔗 https://www.youtube.com/watch?v=xxx
```

---

## ✅ 依赖

- Node.js 18+（建议 Node 20+）
- `curl` 命令行工具（用于 HTTP 请求）
- **代理**（中国大陆必须，自动检测 `HTTPS_PROXY`/`HTTP_PROXY`，默认 `http://127.0.0.1:10808`）

---

## 📁 配置与状态文件

本 skill 的本地状态都在 `state/` 目录下（**不提交到 git**）：

- `state/config.json` — 追踪的频道列表
- `state/seen.json` — 已播报的视频 ID（去重，保留最近 2000 条）

---

## 🧰 命令用法

```bash
cd wlzh-youtube-tracker

# 添加频道
node scripts/youtube-tracker-rss.js add "@veritasium"
node scripts/youtube-tracker-rss.js add "https://www.youtube.com/@veritasium"

# 列出 / 删除频道
node scripts/youtube-tracker-rss.js list
node scripts/youtube-tracker-rss.js remove "@veritasium"

# 检查新视频（原始格式）
node scripts/youtube-tracker-rss.js check

# 检查新视频（Telegram 格式，用于 cron）
node scripts/youtube-tracker-rss.js notify
```

---

## ⏱️ OpenClaw / Cron 接法（推荐 v3.0+）

### systemEvent 模式（推荐）
```
Cron payload:
  执行 `cd .../wlzh-youtube-tracker && node scripts/youtube-tracker-rss.js notify`
  stdout 有内容 → 逐条发到 Telegram topic 1016
  stdout 为空 → HEARTBEAT_OK
```

优势：
- 不消耗 LLM tokens
- 4-5 秒完成
- 不会被 API 限速
- 成功率 ~99%

### agentTurn 模式（旧版）
每次消耗 ~24k tokens，容易超时和限速，不推荐。
