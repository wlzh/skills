# X Twitter Scraper Skill

> Source: https://github.com/Xquik-dev/x-twitter-scraper
> Version: 2.4.16

API-backed X (Twitter) data workflows for agents through Xquik.

## Features

- Search tweets and inspect tweet engagement data.
- Fetch profiles, timelines, media tweets, followers, following, lists, and communities.
- Run approved bulk extraction workflows for larger X datasets.
- Configure Xquik MCP and SDK usage.
- Prepare webhook and monitor workflows with explicit user approval.
- Draft X publishing actions while keeping execution approval-gated.

## When To Use

Use this skill when a task needs structured X data from Xquik's hosted API, MCP server, webhooks, SDKs, or extraction jobs.

Use `x-fetcher` instead when the task only needs to save a single public tweet or X Article as local Markdown.

## Requirements

- Xquik API key in `XQUIK_API_KEY`
- Internet access to `xquik.com` and `docs.xquik.com`
- User approval for private reads, writes, monitors, webhooks, and metered bulk jobs

## Official Install

For the complete reference bundle:

```bash
npx skills@1.5.3 add Xquik-dev/x-twitter-scraper
```

## Links

- Docs: https://docs.xquik.com
- API overview: https://docs.xquik.com/api-reference/overview
- MCP overview: https://docs.xquik.com/mcp/overview
- Skill page: https://skills.sh/xquik-dev/x-twitter-scraper/x-twitter-scraper
