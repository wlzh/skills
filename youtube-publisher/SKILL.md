---
name: youtube-publisher
description: "Upload and publish videos to YouTube with title, description, tags, thumbnail and subtitles. Use for: youtube upload, publish video, share on youtube."
setup_complete: true
setup: "./SETUP.md"
---

# YouTube Publisher

> **First time?** If `setup_complete: false` above, run `./SETUP.md` first, then set `setup_complete: true`.

Upload videos to YouTube with full metadata control.

## Quick Start

```bash
cd ~/.claude/skills/youtube-publisher/scripts

# First time: authenticate
npx ts-node youtube-upload.ts --auth

# Upload video
npx ts-node youtube-upload.ts \
  --video /path/to/video.mp4 \
  --title "My Awesome Video" \
  --description "Check out this amazing content!" \
  --tags "tech,ai,tutorial" \
  --privacy unlisted

# Upload as YouTube Short (vertical video)
npx ts-node youtube-upload.ts \
  --video /path/to/short.mp4 \
  --title "Quick Tip #Shorts" \
  --description "A quick tip for you!" \
  --privacy public \
  --short
```

## Options

| Option | Short | Description |
|--------|-------|-------------|
| `--video` | `-v` | Video file path (required) |
| `--title` | `-t` | Video title (required) |
| `--description` | `-d` | Video description |
| `--tags` | | Comma-separated tags |
| `--privacy` | `-p` | Privacy: public, unlisted, private (default: unlisted) |
| `--category` | `-c` | Category ID (default: 22 = People & Blogs) |
| `--thumbnail` | | Custom thumbnail image (local path or URL) |
| `--subtitles` | | Subtitle file path (SRT/VTT) |
| `--subtitle-lang` | | Subtitle language code (default: zh) |
| `--subtitle-name` | | Subtitle display name (default: 中文) |
| `--playlist` | | Add to playlist ID |
| `--short` | | Mark as YouTube Short |
| `--auth` | | Run OAuth2 authentication flow |
| `--dry-run` | | Preview without uploading |

## Category IDs

| ID | Category |
|----|----------|
| 1 | Film & Animation |
| 2 | Autos & Vehicles |
| 10 | Music |
| 15 | Pets & Animals |
| 17 | Sports |
| 19 | Travel & Events |
| 20 | Gaming |
| 22 | People & Blogs |
| 23 | Comedy |
| 24 | Entertainment |
| 25 | News & Politics |
| 26 | Howto & Style |
| 27 | Education |
| 28 | Science & Technology |

## Authentication

First-time setup requires OAuth2 authentication:

1. Run `npx ts-node youtube-upload.ts --auth`
2. Browser opens Google login
3. Grant permissions to upload videos
4. Token is saved to `.youtube-token.json`

Token refreshes automatically. Re-run `--auth` if expired.

## Environment

Create `scripts/.env`:

```env
YOUTUBE_CLIENT_ID=your_client_id
YOUTUBE_CLIENT_SECRET=your_client_secret
```

Get credentials from Google Cloud Console:
1. Create project at console.cloud.google.com
2. Enable YouTube Data API v3
3. Create OAuth2 credentials (Desktop app)
4. Download and extract client_id & client_secret

## Examples

### Upload Tutorial Video

```bash
npx ts-node youtube-upload.ts \
  -v tutorial.mp4 \
  -t "How to Use Claude Code - Complete Guide" \
  -d "Learn everything about Claude Code in this comprehensive tutorial.

Timestamps:
00:00 Introduction
02:30 Getting Started
05:00 Advanced Features

#ClaudeCode #AI #Tutorial" \
  --tags "claude code,ai,tutorial,anthropic,coding" \
  --category 28 \
  --privacy public
```

### Upload YouTube Short

```bash
npx ts-node youtube-upload.ts \
  -v short_video.mp4 \
  -t "Mind-blowing AI trick! #Shorts" \
  -d "This will change how you work! #AI #Tech" \
  --privacy public \
  --short
```

### Upload to Playlist

```bash
npx ts-node youtube-upload.ts \
  -v episode5.mp4 \
  -t "Podcast Episode 5" \
  --playlist PLxxxxxxxxxxxxxx \
  --privacy unlisted
```

### Upload with Thumbnail and Subtitles

```bash
npx ts-node youtube-upload.ts \
  -v tutorial.mp4 \
  -t "Tutorial with Subtitles" \
  -d "Learn step by step with subtitles" \
  --thumbnail /path/to/cover.jpg \
  --subtitles /path/to/subtitles.srt \
  --subtitle-lang zh \
  --subtitle-name "中文" \
  --privacy public
```

### Upload with Local Thumbnail

```bash
npx ts-node youtube-upload.ts \
  -v video.mp4 \
  -t "My Video Title" \
  --thumbnail "/Users/m/Downloads/shell/work/cover.jpg" \
  --privacy public
```

## Output

On success, returns:
- Video ID
- Video URL (https://youtu.be/VIDEO_ID)
- Status

## Limitations

- Max file size: 256GB (YouTube limit)
- Supported formats: MP4, MOV, AVI, WMV, FLV, 3GP, MPEG
- Supported subtitle formats: SRT, VTT
- Daily upload quota: 10,000 units (typically ~6 videos/day)
- Title max: 100 characters
- Description max: 5,000 characters
- Tags max: 500 characters total
