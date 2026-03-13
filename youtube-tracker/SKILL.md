---
name: youtube-tracker
description: "Track YouTube channels for new uploads using a YouTube Data API key. Use when: add/remove/list tracked YouTube channels, set/validate YouTube API key, check for new videos, or run scheduled YouTube channel monitoring that outputs new video items (channel name, title, short description, and video URL)."
---

# youtube-tracker

A small, script-backed Skill to maintain a list of tracked YouTube channels and periodically check for **new uploads**.

## What it does

- Set / validate **YouTube Data API v3 key**
- Add / remove / list tracked channels (input can be URL / @handle / channelId)
- On `check`, prints only **new videos since last run** with:
  - channel name
  - title
  - short description
  - video URL

## Data files

All state is stored inside this Skill folder:

- `state/config.json` (apiKey, tracked channels)
- `state/seen.json` (dedupe: already announced video ids)

## Commands

Run from this skill directory:

```bash
# set api key
node scripts/youtube-tracker.js set-key "YOUR_YT_API_KEY"

# validate api key
node scripts/youtube-tracker.js validate-key

# add a channel (url / @handle / channelId)
node scripts/youtube-tracker.js add "https://www.youtube.com/@veritasium"
node scripts/youtube-tracker.js add "@veritasium"
node scripts/youtube-tracker.js add "UCddiUEpeqJcYeBxX1IVBKvQ"

# list channels
node scripts/youtube-tracker.js list

# remove channel (by normalized id)
node scripts/youtube-tracker.js remove "UCddiUEpeqJcYeBxX1IVBKvQ"

# check new videos (stdout: only new items)
node scripts/youtube-tracker.js check
```

## Cron usage notes

- If `check` outputs nothing, treat it as **no updates**.
- If it outputs lines, send them to the target chat/topic.
