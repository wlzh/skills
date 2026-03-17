# YouTube Tracker

A script-backed skill to track YouTube channels and get notified of new uploads.

## Version History
### v2.0.0 (2026-03-17) - RSS Mode
**Major update**: now uses YouTube RSS feeds by default - no API key needed!
- ✅ No API quota limits
- ✅ No API key required
- ✅ Unlimited channel tracking
- ✅ Official YouTube RSS feeds (fully compliant)
- ✅ ~5-30 min delay (acceptable for most use cases)

**Why this change?**
- YouTube API free quota: 10,000 units/day
- With 56 channels, each check consumed 5,600 units
- Only 1-2 checks per day before quota exhausted
- RSS feeds are free, unlimited, and official

**Migration from v1.x**
- Existing `state/config.json` and `state/seen.json` are fully compatible
- Just switch to `youtube-tracker-rss.js` commands
- No need to re-add channels

---

## Quick Start (RSS Mode)

```bash
# Add channels
node scripts/youtube-tracker-rss.js add "@veritasium"
node scripts/youtube-tracker-rss.js add "https://www.youtube.com/@tech-shrimp"

# List tracked channels
node scripts/youtube-tracker-rss.js list

# Check for new videos
node scripts/youtube-tracker-rss.js check

# Remove a channel
node scripts/youtube-tracker-rss.js remove "UCddiUEpeqJcYeBxX1IVBKvQ"
```
## API Mode (Legacy)
If you need higher quota or still use API mode:

```bash
# Set API key
node scripts/youtube-tracker.js set-key "YOUR_API_KEY"

# Add channels (requires API key for handle resolution)
node scripts/youtube-tracker.js add "@veritasium"
```
## Cron Usage
Run periodically and forward output to help notification system

```bash
# Check every 30 minutes
*/30 * * * * cd /path/to/youtube-tracker && node scripts/youtube-tracker-rss.js check | your-notification-command
```
If there are no new videos, the command outputs nothing (silent).

## State files
Located in `state/` directory

- `config.json` - tracked channels (no API key needed for RSS mode)
- `seen.json` - video IDs already seen (deduplication)
## API Quota Notes
YouTube Data API v3 has quota limits:
- Daily quota: 10,000 units (default)
- `search.list` costs 100 units per request
- Monitor usage in [Google Cloud Console](https://console.cloud.google.com/apis/api_youtube.googleapis.com/quotas)
## Troubleshooting
### "API key not set" (API mode only)
Run `set-key` command or set `Youtube_api_key` environment variable
### "YouTube API error: quota exceeded"
This:
- Wait for quota reset (midnight Pacific time)
- Request higher quota from Google
- Reduce check frequency or number of channels
### "Channel not found" (API mode only)
- Verify the channel exists
- Try using the full channel URL instead of handle