# youtube-tracker

Track YouTube channels for **new uploads**.

- Maintains a local channel list
- Periodically checks the latest uploads
- **Outputs nothing when there is no update** (perfect for cron)

## Output format

When new videos are detected, each item prints:

- 频道：<频道名字>
- 标题：<视频标题>
- 简介：<简介摘要>
- 链接：<视频URL>

Items are separated by a blank line.

## Requirements

- Node.js 18+ (recommended: Node 20+)
- A **YouTube Data API v3** key

## How to get a YouTube API key

1. Open Google Cloud Console: https://console.cloud.google.com/
2. Create/select a project
3. Enable API: **YouTube Data API v3**
4. Go to **APIs & Services → Credentials**
5. Create **API key**

> Tip: Restrict the key (HTTP referrer/IP) if you can.

## State & config files

All state lives under this skill’s `state/` directory:

- `state/config.json` (local, not committed)

```json
{
  "apiKey": "YOUR_KEY",
  "channels": [
    {
      "channelId": "UCxxxxxxxxxxxxxxxxxxxxxx",
      "title": "Channel Name",
      "handle": "@handle",
      "addedAt": "2026-03-13T00:00:00.000Z"
    }
  ]
}
```

- `state/seen.json` (local, not committed)

```json
{
  "seenVideoIds": ["VIDEO_ID_1", "VIDEO_ID_2"],
  "updatedAt": "2026-03-13T00:00:00.000Z"
}
```

Repo only ships examples:
- `state/config.json.example`
- `state/seen.json.example`

## Commands

Run in this directory:

```bash
# 1) set API key (3 ways)
node scripts/youtube-tracker.js set-key "YOUR_KEY"
# or
YOUTUBE_API_KEY="YOUR_KEY" node scripts/youtube-tracker.js set-key
# or
echo "YOUR_KEY" | node scripts/youtube-tracker.js set-key

# 2) validate key
node scripts/youtube-tracker.js validate-key

# 3) add channels
node scripts/youtube-tracker.js add "@veritasium"
node scripts/youtube-tracker.js add "https://www.youtube.com/@veritasium"
node scripts/youtube-tracker.js add "https://www.youtube.com/channel/UCddiUEpeqJcYeBxX1IVBKvQ"
node scripts/youtube-tracker.js add "UCddiUEpeqJcYeBxX1IVBKvQ"

# 4) list / remove
node scripts/youtube-tracker.js list
node scripts/youtube-tracker.js remove "@veritasium"
node scripts/youtube-tracker.js remove "UCddiUEpeqJcYeBxX1IVBKvQ"

# 5) check new videos (prints only NEW)
node scripts/youtube-tracker.js check
```

## Baseline behavior (anti-spam)

When a channel is newly added, the first `check` run will **not announce old videos**.
Only videos published **after** `addedAt` will be treated as new.

## OpenClaw / cron usage

- Schedule: run `node scripts/youtube-tracker.js check`
- If stdout is empty → do nothing
- If stdout has content → send it to your target chat/topic

