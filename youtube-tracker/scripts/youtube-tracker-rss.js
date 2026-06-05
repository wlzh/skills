#!/usr/bin/env node
/**
 * youtube-tracker-rss skill script
 * v2.1.0 - Proxy support for YouTube RSS feeds
 *
 * Uses YouTube RSS feeds instead of API - no quota limits!
 * Auto-detects proxy from env vars or falls back to common local proxies.
 *
 * Commands:
 *   add <channelId|@handle|url>
 *   remove <channelId|@handle|url>
 *   list
 *   check
 *
 * State files (relative to this script):
 *   ../state/config.json  { channels: Array<{channelId, title, handle?, addedAt}> }
 *   ../state/seen.json    { seenVideoIds: string[], updatedAt }
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// ── Proxy ──────────────────────────────────────────────────────────
// Priority: HTTPS_PROXY > HTTPS_PROXY > http_proxy > http://127.0.0.1:10808 (fallback)
const PROXY = process.env.HTTPS_PROXY || process.env.https_proxy ||
              process.env.HTTP_PROXY || process.env.http_proxy ||
              'http://127.0.0.1:10808';

const STATE_DIR = path.resolve(__dirname, '..', 'state');
const CONFIG_PATH = path.join(STATE_DIR, 'config.json');
const SEEN_PATH = path.join(STATE_DIR, 'seen.json');

// ── HTTP with proxy ────────────────────────────────────────────────
/**
 * Fetch URL using curl with proxy. Always uses proxy for YouTube domains.
 * Returns the response body text.
 */
function httpGet(url, timeoutMs = 15000) {
  const cmd = `curl -sS -m ${Math.ceil(timeoutMs / 1000)} -x "${PROXY}" -L "${url}"`;
  try {
    return execSync(cmd, { encoding: 'utf-8', maxBuffer: 10 * 1024 * 1024, timeout: timeoutMs + 5000 });
  } catch (err) {
    throw new Error(`Fetch failed: ${url} - ${err.message}`);
  }
}

// ── State I/O ──────────────────────────────────────────────────────
function ensureStateDir() {
  fs.mkdirSync(STATE_DIR, { recursive: true });
}

function readJson(file, fallback) {
  try {
    return JSON.parse(fs.readFileSync(file, 'utf8'));
  } catch (e) {
    return fallback;
  }
}

function writeJson(file, obj) {
  fs.writeFileSync(file, JSON.stringify(obj, null, 2) + '\n', 'utf8');
}

function die(msg) {
  console.error(msg);
  process.exit(1);
}

function nowIso() {
  return new Date().toISOString();
}

function getConfig() {
  ensureStateDir();
  const cfg = readJson(CONFIG_PATH, { channels: [] });
  if (!cfg.channels) cfg.channels = [];
  return cfg;
}

function saveConfig(cfg) {
  ensureStateDir();
  delete cfg.apiKey;
  writeJson(CONFIG_PATH, cfg);
}

function getSeen() {
  ensureStateDir();
  const seen = readJson(SEEN_PATH, { seenVideoIds: [], updatedAt: null });
  if (!Array.isArray(seen.seenVideoIds)) seen.seenVideoIds = [];
  return seen;
}

function saveSeen(seen) {
  ensureStateDir();
  seen.updatedAt = nowIso();
  writeJson(SEEN_PATH, seen);
}

// ── Input parsing ──────────────────────────────────────────────────
function parseArgs() {
  const [, , cmd, ...rest] = process.argv;
  return { cmd, rest };
}

function normalizeChannelInput(input) {
  const s = String(input || '').trim();
  if (!s) return { kind: 'unknown', value: '' };

  if (/^UC[\w-]{20,}$/.test(s)) return { kind: 'channelId', value: s };
  if (s.startsWith('@')) return { kind: 'handle', value: s.replace(/^@+/, '') };

  try {
    const u = new URL(s);
    const p = u.pathname;
    const m1 = p.match(/^\/channel\/(UC[\w-]{20,})/);
    if (m1) return { kind: 'channelId', value: m1[1] };
    const m2 = p.match(/^\/@([^\/]+)/);
    if (m2) return { kind: 'handle', value: m2[1] };
    const m3 = p.match(/^\/c\/([^\/]+)/);
    if (m3) return { kind: 'handle', value: m3[1] };
    const m4 = p.match(/^\/user\/([^\/]+)/);
    if (m4) return { kind: 'handle', value: m4[1] };
  } catch {}

  return { kind: 'unknown', value: s };
}

// ── RSS parsing ────────────────────────────────────────────────────
function parseRSS(xml) {
  const entries = [];
  const entryMatches = xml.match(/<entry[\s\S]*?<\/entry>/gi) || [];

  for (const entryXml of entryMatches) {
    const videoIdMatch = entryXml.match(/<yt:videoId>([^<]+)<\/yt:videoId>/i);
    const titleMatch = entryXml.match(/<title>([^<]*)<\/title>/i);
    const publishedMatch = entryXml.match(/<published>([^<]+)<\/published>/i);
    const authorMatch = entryXml.match(/<author>[\s\S]*?<name>([^<]*)<\/name>[\s\S]*?<\/author>/i);
    const linkMatch = entryXml.match(/<link[^>]*href="([^"]+)"[^>]*rel="alternate"[^>]*>/i) ||
                      entryXml.match(/<link[^>]*rel="alternate"[^>]*href="([^"]+)"[^>]*>/i);

    if (videoIdMatch) {
      entries.push({
        videoId: videoIdMatch[1],
        title: titleMatch ? titleMatch[1] : '',
        publishedAt: publishedMatch ? publishedMatch[1] : '',
        channelTitle: authorMatch ? authorMatch[1] : '',
        link: linkMatch ? linkMatch[1] : `https://www.youtube.com/watch?v=${videoIdMatch[1]}`
      });
    }
  }

  return entries;
}

// ── YouTube API (all via proxy) ────────────────────────────────────
function fetchChannelRSS(channelId) {
  const url = `https://www.youtube.com/feeds/videos.xml?channel_id=${encodeURIComponent(channelId)}`;
  const xml = httpGet(url);
  return parseRSS(xml);
}

function resolveHandleToChannelId(handle) {
  const handleClean = handle.replace(/^@/, '');

  // Try fetching the channel page and extracting channelId
  try {
    const channelUrl = `https://www.youtube.com/@${handleClean}`;
    const html = httpGet(channelUrl);

    const patterns = [
      /"channelId":"(UC[\w-]{22})"/,
      /"externalId":"(UC[\w-]{22})"/,
      /channel_id=(UC[\w-]{22})/,
      /<meta itemprop="channelId" content="(UC[\w-]{22})">/
    ];

    for (const pattern of patterns) {
      const match = html.match(pattern);
      if (match) return match[1];
    }
  } catch {}

  throw new Error(`无法解析频道 @${handleClean}，请直接提供 channelId（以 UC 开头的字符串）`);
}

function getChannelInfo(channelId) {
  try {
    const url = `https://www.youtube.com/feeds/videos.xml?channel_id=${encodeURIComponent(channelId)}`;
    const xml = httpGet(url);

    const titleMatch = xml.match(/<title>([^<]*)<\/title>/i);
    const authorMatch = xml.match(/<author>[\s\S]*?<name>([^<]*)<\/name>[\s\S]*?<\/author>/i);

    return {
      title: authorMatch ? authorMatch[1] : (titleMatch ? titleMatch[1] : channelId),
      channelId: channelId
    };
  } catch {
    return null;
  }
}

function videoUrl(videoId) {
  return `https://www.youtube.com/watch?v=${videoId}`;
}

// ── Main ───────────────────────────────────────────────────────────
async function main() {
  const { cmd, rest } = parseArgs();
  if (!cmd) {
    die('Usage: node scripts/youtube-tracker-rss.js <add|remove|list|check> ...\n\nCommands:\n  add <channelId|@handle|url>  添加频道\n  remove <channelId|@handle|url>  移除频道\n  list  列出所有频道\n  check  检查新视频');
  }

  const cfg = getConfig();

  if (cmd === 'add') {
    const input = rest.join(' ').trim();
    if (!input) die('Missing channel input');

    const parsed = normalizeChannelInput(input);
    let channelId = null;
    let title = input;

    if (parsed.kind === 'channelId') {
      channelId = parsed.value;
      const info = getChannelInfo(channelId);
      if (info) title = info.title;
    } else if (parsed.kind === 'handle') {
      console.error(`正在解析 @${parsed.value}...`);
      try {
        channelId = resolveHandleToChannelId(parsed.value);
        const info = getChannelInfo(channelId);
        if (info) title = info.title;
      } catch (err) {
        die(err.message);
      }
    } else {
      die(`Unsupported input format: ${input}`);
    }

    const exists = cfg.channels.some(c => c.channelId === channelId);
    if (!exists) {
      cfg.channels.push({
        channelId: channelId,
        title: title,
        handle: parsed.kind === 'handle' ? `@${parsed.value}` : null,
        addedAt: nowIso(),
      });
      saveConfig(cfg);
    }
    console.log(`OK: added ${title} (${channelId})`);
    return;
  }

  if (cmd === 'remove') {
    const input = rest.join(' ').trim();
    if (!input) die('Missing channel input');

    const parsed = normalizeChannelInput(input);
    let channelId = input;

    if (parsed.kind === 'channelId') {
      channelId = parsed.value;
    } else if (parsed.kind === 'handle') {
      const found = cfg.channels.find(c =>
        c.handle && c.handle.toLowerCase() === `@${parsed.value}`.toLowerCase()
      );
      if (found) {
        channelId = found.channelId;
      } else {
        try {
          channelId = resolveHandleToChannelId(parsed.value);
        } catch (err) {
          die(err.message);
        }
      }
    }

    const before = cfg.channels.length;
    cfg.channels = cfg.channels.filter(c => c.channelId !== channelId);
    saveConfig(cfg);
    console.log(`OK: removed ${before - cfg.channels.length} channel(s)`);
    return;
  }

  if (cmd === 'list') {
    if (!cfg.channels.length) {
      console.log('No channels tracked');
      return;
    }
    console.log(`共 ${cfg.channels.length} 个频道:\n`);
    for (const c of cfg.channels) {
      console.log(`${c.title}${c.handle ? ` (${c.handle})` : ''}`);
      console.log(`  ${c.channelId}`);
    }
    return;
  }

  if (cmd === 'check') {
    if (!cfg.channels.length) return;

    const seen = getSeen();
    const seenSet = new Set(seen.seenVideoIds);

    const newLines = [];
    const newlySeen = [];
    const errors = [];

    console.error(`检查 ${cfg.channels.length} 个频道... (proxy: ${PROXY})`);

    // Process channels in batches of 10 for speed
    const BATCH_SIZE = 10;
    for (let i = 0; i < cfg.channels.length; i += BATCH_SIZE) {
      const batch = cfg.channels.slice(i, i + BATCH_SIZE);
      const results = batch.map(c => {
        try {
          const vids = fetchChannelRSS(c.channelId);

          for (const v of vids) {
            if (seenSet.has(v.videoId)) continue;

            if (c.addedAt && v.publishedAt) {
              const added = Date.parse(c.addedAt);
              const pub = Date.parse(v.publishedAt);
              if (!Number.isNaN(added) && !Number.isNaN(pub) && pub <= added) {
                seenSet.add(v.videoId);
                newlySeen.push(v.videoId);
                continue;
              }
            }

            seenSet.add(v.videoId);
            newlySeen.push(v.videoId);

            const chName = c.title || v.channelTitle || c.channelId;
            const line = [
              `频道：${chName}`,
              `标题：${v.title}`,
              `链接：${v.link || videoUrl(v.videoId)}`,
            ].join('\n');
            newLines.push(line);
          }
          return null;
        } catch (err) {
          return `${c.title}: ${err.message}`;
        }
      });

      for (const e of results) {
        if (e) errors.push(e);
      }
    }

    if (newlySeen.length) {
      const merged = (seen.seenVideoIds || []).concat(newlySeen);
      const unique = Array.from(new Set(merged));
      const trimmed = unique.slice(Math.max(0, unique.length - 2000));
      saveSeen({ seenVideoIds: trimmed, updatedAt: nowIso() });
    }

    if (errors.length) {
      console.error(`\n警告: ${errors.length} 个频道获取失败:`);
      errors.forEach(e => console.error(`  - ${e}`));
    }

    if (!newLines.length) {
      console.error('无新视频');
      return;
    }

    console.error(`发现 ${newLines.length} 个新视频!\n`);
    process.stdout.write(newLines.join('\n\n') + '\n');
    return;
  }

  die(`Unknown command: ${cmd}`);
}

main().catch(err => {
  console.error(err?.message || String(err));
  process.exit(2);
});
