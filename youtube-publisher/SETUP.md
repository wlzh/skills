# YouTube Publisher - Setup Guide

## Prerequisites

- Node.js installed
- Google Cloud account
- YouTube channel

## 1. Create Google Cloud Project

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create new project or select existing
3. Enable YouTube Data API v3:
   - APIs & Services → Library
   - Search "YouTube Data API v3"
   - Click Enable

4. (Optional) Enable YouTube Caption API for subtitle uploads:
   - APIs & Services → Library
   - Search "YouTube Caption API" or "YouTube Data API v3"
   - Click Enable

## 2. Create OAuth Credentials

1. APIs & Services → Credentials
2. Create Credentials → OAuth client ID
3. **Application type: Desktop app** (NOT Web application)
4. No redirect URI needed for Desktop app
5. Download JSON or copy Client ID and Secret

## 3. Configure Environment

```bash
cd ~/.claude/skills/youtube-publisher/scripts
cp .env.example .env
```

Edit `.env`:
```
YOUTUBE_CLIENT_ID=your_client_id
YOUTUBE_CLIENT_SECRET=your_client_secret
```

## 4. Install Dependencies

```bash
cd ~/.claude/skills/youtube-publisher/scripts
npm install
```

## 5. First-Time Authorization

Run the upload script once - it will:
1. Open browser for Google sign-in
2. Ask for YouTube permissions
3. Save refresh token for future use

```bash
npx ts-node youtube-upload.ts --auth
```

## 6. Mark Setup Complete

Edit `SKILL.md` and change:
```yaml
setup_complete: true
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Redirect URI mismatch | For Desktop app, no redirect URI needed |
| API not enabled | Enable YouTube Data API v3 |
| Caption upload fails | Enable YouTube Data API v3 with full permissions, re-run --auth |
| Quota exceeded | Check quota in Cloud Console |
| Access denied | Re-authorize: `npx ts-node youtube-upload.ts --auth` |
