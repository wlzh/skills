---
name: wlzh-youtube-tracker
description: "Track YouTube channels for new uploads. Supports both RSS mode (no API key needed, unlimited quota) and API mode. Use when: add/remove/list tracked YouTube channels, check for new videos, or run scheduled YouTube channel monitoring."
version: "3.1.0"
---

# wlzh-youtube-tracker

A script-backed Skill to maintain a list of tracked YouTube channels and periodically check for **new uploads**.

## v3.1.0 - Self-contained Telegram Sending (2026-06-06)

**Critical reliability fix** — script now sends Telegram directly, no LLM relay needed.

### Changes
- **`notify` sends Telegram directly**: Script calls Telegram Bot API itself, no LLM relay
- **Atomic seen marking**: Only marks video as seen AFTER successful Telegram send
- **Auto-retry on failure**: Failed sends stay "unseen", next cron cycle retries automatically
- **Reads bot token from `~/.openclaw/openclaw.json`**: No extra config needed
- **Fallback mode**: If bot token unavailable, falls back to stdout output for LLM relay

### Bug fix
- v3.0.0 had a critical bug: `notify` marked videos as seen immediately upon detection,
  but Telegram sending was done by LLM. If LLM failed (rate limit/timeout), videos were
  lost forever — marked as seen but never sent. v3.1.0 fixes this completely.

---

## v3.0.0 - Parallel Fetching + Notify Mode (2026-06-06)

**Major performance optimization** — parallel fetching, ~10x faster.

### Changes
- **Parallel HTTP fetching**: All channels now fetch concurrently (15 parallel curl processes)
- **~10x faster**: 55 channels check in ~4-5 seconds (was ~45 seconds with serial curl)
- **New `notify` command**: Outputs Telegram-ready formatted messages (📺🎬🔗 format)

---
  - Eliminates timeout failures (the #2 failure cause)
  - No more ~24k tokens consumed per check
  - Success rate expected: ~99% (was ~64%)

### Why this matters
- Previous cron used `isolated agentTurn`: LLM → exec script → LLM interpret → send
- Each run consumed 24-95k tokens and took 45-180s, frequently hitting API rate limits
- New approach: systemEvent → exec script (4s) → send if needed → done

## v2.1.0 - Proxy Support (2026-06-05)

**Fix**: Added automatic proxy support for YouTube RSS feeds.
- YouTube is inaccessible from China without proxy; all HTTP requests now route through proxy
- Auto-detects proxy from `HTTPS_PROXY` / `HTTP_PROXY` env vars, falls back to `http://127.0.0.1:10808`
- Replaced `fetch()` API calls with `curl` via `execSync` for consistent proxy routing

## v2.0.0 - RSS Mode (2026-03-17)

**Breaking change**: Now uses YouTube RSS feeds by default - **no API key needed, no quota limits!**

## What it does

- Add / remove / list tracked channels (input can be URL / @handle / channelId)
- On `add`, it will **baseline** (mark the channel's current latest videos as seen)
- On `check`, prints only **new videos since last run** with channel name, title, video URL
- On `notify`, prints Telegram-formatted output (📺🎬🔗) for direct cron use

## Data files

All state is stored inside this Skill folder:

- `state/config.json` (tracked channels, no API key needed for RSS mode)
- `state/seen.json` (dedupe: already announced video ids, keeps up to 2000)

## Commands

Run from this skill directory:

```bash
# RSS mode (recommended, no API key needed)
node scripts/youtube-tracker-rss.js add "https://www.youtube.com/@veritasium"
node scripts/youtube-tracker-rss.js add "@veritasium"
node scripts/youtube-tracker-rss.js add "UCddiUEpeqJcYeBxX1IVBKvQ"
node scripts/youtube-tracker-rss.js list
node scripts/youtube-tracker-rss.js remove "UCddiUEpeqJcYeBxX1IVBKvQ"
node scripts/youtube-tracker-rss.js check    # original output format
node scripts/youtube-tracker-rss.js notify   # Auto-sends to Telegram, marks seen on success

# API mode (legacy, requires API key)
node scripts/youtube-tracker.js set-key "YOUR_YT_API_KEY"
node scripts/youtube-tracker.js validate-key
node scripts/youtube-tracker.js add "@veritasium"
node scripts/youtube-tracker.js check
```

## Cron usage

### Recommended (v3.0+): systemEvent mode

Uses `notify` command + `systemEvent` cron target — no LLM needed per check.

```
Cron payload (isolated agentTurn):
  Execute `cd /Users/m./Documents/QNSZ/project/skills/wlzh-youtube-tracker && node scripts/youtube-tracker-rss.js notify`
  Script auto-sends new videos to Telegram topic 1016 via Bot API.
  Only marks seen on successful send — failed videos retry next cycle.
  stdout 有内容 → 逐条发到 Telegram
  stdout 为空 → HEARTBEAT_OK
```

### Legacy: agentTurn mode

Previous approach using isolated LLM session. Higher overhead, subject to API rate limits.

```
Legacy (agentTurn with LLM relay — not recommended):
  Run `cd .../wlzh-youtube-tracker && node scripts/youtube-tracker-rss.js check`
  Interpret stdout, send if "发现" found
```

## Output formats

### `check` command (original)
```
频道：最佳拍档
标题：Anthropic呼吁按下AI暂停键？
链接：https://www.youtube.com/watch?v=xxx
```

### `notify` command (Telegram-ready)
```
📺 最佳拍档
🎬 Anthropic呼吁按下AI暂停键？
🔗 https://www.youtube.com/watch?v=xxx
```

## Migration from v1.x / v2.x

- Existing `state/config.json` and `state/seen.json` are fully compatible
- `check` command output unchanged (backwards compatible)
- New `notify` command is optional, designed for cron use
