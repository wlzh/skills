# wlzh-youtube-tracker

A script-backed skill to track YouTube channels and get notified of new uploads.

## Version History

### v3.0.0 (2026-06-06) - Parallel Fetching + Notify Mode
**Major optimization**: Eliminates cron failures by removing LLM dependency.

- ✅ Parallel HTTP fetching (15 concurrent curl processes)
- ✅ ~10x faster: 55 channels in ~4-5s (was ~45s)
- ✅ New `notify` command for Telegram-ready output
- ✅ Cron uses `systemEvent` instead of `agentTurn` — no API rate limits, no timeouts
- ✅ Expected success rate: ~99% (was ~64%)

**Root cause of v2.x failures:**
- 36% failure rate (22% timeout + 12% rate limit + 2% network)
- `agentTurn` cron required LLM call for every check (~24k tokens each)
- Total time: script 45s + LLM latency = frequent 180s timeout

**v3.0 fix:**
- `systemEvent` cron → direct exec → 4-5s total, no LLM needed
- Rate limit errors eliminated entirely

### v2.1.0 (2026-06-05) - Proxy Support
- Added automatic proxy support for YouTube RSS feeds
- Auto-detects from `HTTPS_PROXY` / `HTTP_PROXY` env vars, falls back to `http://127.0.0.1:10808`
- Replaced `fetch()` calls with `curl` for consistent proxy routing

### v2.0.1 (2026-03-17) - Bugfix
- Increased seen video ID limit from 500 to 2000

### v2.0.0 (2026-03-17) - RSS Mode
- YouTube RSS feeds by default - no API key needed
- No API quota limits, unlimited channel tracking

---

## Quick Start (RSS Mode)

```bash
# Add channels
node scripts/youtube-tracker-rss.js add "@veritasium"
node scripts/youtube-tracker-rss.js add "https://www.youtube.com/@tech-shrimp"

# List tracked channels
node scripts/youtube-tracker-rss.js list

# Check for new videos (original format)
node scripts/youtube-tracker-rss.js check

# Check for new videos (Telegram-ready format, for cron)
node scripts/youtube-tracker-rss.js notify

# Remove a channel
node scripts/youtube-tracker-rss.js remove "UCddiUEpeqJcYeBxX1IVBKvQ"
```

## Cron Usage

### v3.0+ (recommended): systemEvent

```bash
# Cron fires systemEvent → main session runs script → sends if new videos
# No LLM overhead, ~4-5s per check, no rate limits
```

### Legacy: agentTurn

Higher overhead, subject to API rate limits. Not recommended for frequent checks.

## State files

Located in `state/` directory

- `config.json` - tracked channels (no API key needed for RSS mode)
- `seen.json` - video IDs already seen (deduplication, keeps up to 2000)

## Troubleshooting

### "Fetch failed" errors
- Check proxy settings (`HTTPS_PROXY` env var or default `http://127.0.0.1:10808`)
- Ensure curl is installed and proxy is running

### Duplicate notifications
- `state/seen.json` tracks up to 2000 video IDs
- If tracking many active channels, this limit may need increasing

### "Channel not found"
- Verify the channel exists
- Try using the full channel URL instead of handle
- For handles, the script fetches the channel page to resolve the ID
