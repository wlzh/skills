# YouTube Publisher - Setup Guide

> Repository: [https://github.com/wlzh/skills](https://github.com/wlzh/skills)

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

## 2.1 Add Test User (Required for New Projects)

New Google Cloud projects require adding test users to access the API:

1. In the OAuth client page, click **Audience** on the left sidebar
2. Find the **Test users** section
3. Click **Add users**
4. Enter your Google email address (e.g., xxx@gmail.com)
5. Click Save

This fixes the "403 Access Denied" error for new projects.

## 2.2 Add API Permissions (For Subtitle Upload)

To enable subtitle uploads, add the required scope:

1. In the OAuth client page, click **Data access** on the left sidebar
2. Click **Add or remove scopes**
3. Search and add: `https://www.googleapis.com/auth/youtube.force-ssl`
4. Click Save

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
| 403 Access Denied | Add your email as Test User in Audience settings |
| Redirect URI mismatch | For Desktop app, no redirect URI needed |
| API not enabled | Enable YouTube Data API v3 |
| Caption upload fails | Add `youtube.force-ssl` scope in Data access settings, re-run --auth |
| Quota exceeded | Check quota in Cloud Console |
| Access denied | Re-authorize: `npx ts-node youtube-upload.ts --auth` |
