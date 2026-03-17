---
name: youtube-tracker
description: "Track YouTube channels for new uploads. Supports both RSS mode (no API key needed, unlimited quota) and API mode. Use when: add/remove/list tracked YouTube channels, check for new videos, or run scheduled YouTube channel monitoring."
version: "2.0.0"
---

# youtube-tracker

A script-backed Skill to maintain a list of tracked YouTube channels and periodically check for **new uploads**.

## v2.0.0 - RSS Mode (2026-03-17)

**Breaking change**: Now uses YouTube RSS feeds by default - **no API key needed, no quota limits!**

### Why RSS?
- YouTube API free quota: 10,000 units/day
- API mode with 56 channels × 100 units/check = 5,600 units
- That means only 1-2 checks per day before quota exhausted
- RSS feeds are official, free, unlimited, and only 5-30 min delayed

### Changes
- New script: `youtube-tracker-rss.js` (RSS mode, no API key required)
- Legacy script: `youtube-tracker.js` (API mode, requires key)
- `check` command now defaults to RSS mode
- Removed API key requirement for basic operations

## What it does

- Add / remove / list tracked channels (input can be URL / @handle / channelId)
- On `add`, it will **baseline** (mark the channel's current latest videos as seen)
- On `check`, prints only **new videos since last run** with:
  - channel name
  - title
  - video URL

## Data files

All state is stored inside this Skill folder:

- `state/config.json` (tracked channels, no API key needed for RSS mode)
- `state/seen.json` (dedupe: already announced video ids)

## Commands

Run from this skill directory:

```bash
# RSS mode (recommended, no API key needed)
node scripts/youtube-tracker-rss.js add "https://www.youtube.com/@veritasium"
node scripts/youtube-tracker-rss.js add "@veritasium"
node scripts/youtube-tracker-rss.js add "UCddiUEpeqJcYeBxX1IVBKvQ"
node scripts/youtube-tracker-rss.js list
node scripts/youtube-tracker-rss.js remove "UCddiUEpeqJcYeBxX1IVBKvQ"
node scripts/youtube-tracker-rss.js check

# API mode (legacy, requires API key)
node scripts/youtube-tracker.js set-key "YOUR_YT_API_KEY"
node scripts/youtube-tracker.js validate-key
node scripts/youtube-tracker.js add "@veritasium"
node scripts/youtube-tracker.js check
```

## Cron usage notes

- Use `youtube-tracker-rss.js check` for scheduled monitoring
- If `check` outputs nothing, treat it as **no updates**
- If it outputs lines, send them to the target chat/topic
- No API quota concerns with RSS mode - check as often as needed

## Migration from v1.x

If upgrading from v1.x (API mode):
1. Your existing `state/config.json` and `state/seen.json` are compatible
2. Simply switch to `youtube-tracker-rss.js` commands
3. No need to re-add channels
