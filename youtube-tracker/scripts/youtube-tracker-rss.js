#!/usr/bin/env node
/**
 * youtube-tracker-rss skill script
 *
 * Uses YouTube RSS feeds instead of API - no quota limits!
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

const STATE_DIR = path.resolve(__dirname, '..', 'state');
const CONFIG_PATH = path.join(STATE_DIR, 'config.json');
const SEEN_PATH = path.join(STATE_DIR, 'seen.json');

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
  const cfg = readJson(CONFIG_PATH, { apiKey: '', channels: [] });
  if (!cfg.channels) cfg.channels = [];
  return cfg;
}

function saveConfig(cfg) {
  ensureStateDir();
  // Remove apiKey if present (no longer needed for RSS)
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

function parseArgs() {
  const [, , cmd, ...rest] = process.argv;
  return { cmd, rest };
}

function normalizeChannelInput(input) {
  const s = String(input || '').trim();
  if (!s) return { kind: 'unknown', value: '' };

  // channelId
  if (/^UC[\w-]{20,}$/.test(s)) return { kind: 'channelId', value: s };

  // @handle
  if (s.startsWith('@')) return { kind: 'handle', value: s.replace(/^@+/, '') };

  // url patterns
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

/**
 * Parse YouTube RSS feed (XML)
 * Returns array of video entries
 */
function parseRSS(xml) {
  const entries = [];
  
  // Simple XML parsing without external dependencies
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

/**
 * Fetch RSS feed for a channel
 */
async function fetchChannelRSS(channelId) {
  const url = `https://www.youtube.com/feeds/videos.xml?channel_id=${encodeURIComponent(channelId)}`;
  
  const res = await fetch(url, {
    method: 'GET',
    headers: {
      'User-Agent': 'Mozilla/5.0 (compatible; YouTube-RSS-Tracker/1.0)',
      'Accept': 'application/xml, application/rss+xml, text/xml, */*'
    }
  });
  
  if (!res.ok) {
    throw new Error(`HTTP ${res.status} fetching RSS for ${channelId}`);
  }
  
  const xml = await res.text();
  return parseRSS(xml);
}

/**
 * Resolve handle to channelId using YouTube oEmbed (works without API)
 * Falls back to scraping if needed
 */
async function resolveHandleToChannelId(handle) {
  const handleClean = handle.replace(/^@/, '');
  
  // Try oEmbed API (doesn't require auth, but may not work for all handles)
  try {
    const oembedUrl = `https://www.youtube.com/oembed?url=https://www.youtube.com/@${handleClean}&format=json`;
    const res = await fetch(oembedUrl);
    if (res.ok) {
      const data = await res.json();
      // oEmbed doesn't return channelId directly, so we need another approach
    }
  } catch {}
  
  // Try fetching the channel page and extracting channelId
  try {
    const channelUrl = `https://www.youtube.com/@${handleClean}`;
    const res = await fetch(channelUrl, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
      }
    });
    
    if (res.ok) {
      const html = await res.text();
      
      // Look for channelId in various places
      const patterns = [
        /"channelId":"(UC[\w-]{22})"/,
        /"externalId":"(UC[\w-]{22})"/,
        /channel_id=(UC[\w-]{22})/,
        /<meta itemprop="channelId" content="(UC[\w-]{22})">/
      ];
      
      for (const pattern of patterns) {
        const match = html.match(pattern);
        if (match) {
          return match[1];
        }
      }
    }
  } catch {}
  
  throw new Error(`无法解析频道 @${handleClean}，请直接提供 channelId（以 UC 开头的字符串）`);
}

/**
 * Get channel title from RSS feed
 */
async function getChannelInfo(channelId) {
  try {
    const url = `https://www.youtube.com/feeds/videos.xml?channel_id=${encodeURIComponent(channelId)}`;
    const res = await fetch(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (compatible; YouTube-RSS-Tracker/1.0)'
      }
    });
    
    if (!res.ok) return null;
    
    const xml = await res.text();
    
    // Extract channel title from feed
    const titleMatch = xml.match(/<title>([^<]*)<\/title>/i);
    const authorMatch = xml.match(/<author>[\s\S]*?<name>([^<]*)<\/name>/i);
    
    return {
      title: authorMatch ? authorMatch[1] : (titleMatch ? titleMatch[1] : channelId),
      channelId: channelId
    };
  } catch {
    return null;
  }
}

function summarize(desc) {
  const s = String(desc || '').replace(/\s+/g, ' ').trim();
  if (!s) return '';
  return s.length > 120 ? s.slice(0, 120) + '…' : s;
}

function videoUrl(videoId) {
  return `https://www.youtube.com/watch?v=${videoId}`;
}

async function readStdin() {
  return new Promise(resolve => {
    let data = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', chunk => (data += chunk));
    process.stdin.on('end', () => resolve(data));
    process.stdin.resume();
  });
}

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
      const info = await getChannelInfo(channelId);
      if (info) title = info.title;
    } else if (parsed.kind === 'handle') {
      console.error(`正在解析 @${parsed.value}...`);
      try {
        channelId = await resolveHandleToChannelId(parsed.value);
        const info = await getChannelInfo(channelId);
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
      // Try to find by handle first
      const found = cfg.channels.find(c => 
        c.handle && c.handle.toLowerCase() === `@${parsed.value}`.toLowerCase()
      );
      if (found) {
        channelId = found.channelId;
      } else {
        // Try to resolve handle to channelId
        try {
          channelId = await resolveHandleToChannelId(parsed.value);
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
    if (!cfg.channels.length) return; // silent

    const seen = getSeen();
    const seenSet = new Set(seen.seenVideoIds);

    const newLines = [];
    const newlySeen = [];
    const errors = [];

    console.error(`检查 ${cfg.channels.length} 个频道...`);

    for (const c of cfg.channels) {
      try {
        const vids = await fetchChannelRSS(c.channelId);
        
        for (const v of vids) {
          if (seenSet.has(v.videoId)) continue;

          // Baseline filter: do not announce videos published before/at the time the channel was added.
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
      } catch (err) {
        errors.push(`${c.title}: ${err.message}`);
      }
    }

    if (newlySeen.length) {
      const merged = (seen.seenVideoIds || []).concat(newlySeen);
      const unique = Array.from(new Set(merged));
      const trimmed = unique.slice(Math.max(0, unique.length - 500));
      saveSeen({ seenVideoIds: trimmed, updatedAt: nowIso() });
    }

    if (errors.length) {
      console.error(`\n警告: ${errors.length} 个频道获取失败:`);
      errors.forEach(e => console.error(`  - ${e}`));
    }

    if (!newLines.length) {
      console.error('无新视频');
      return; // silent exit
    }
    
    console.error(`发现 ${newLines.length} 个新视频!\n`);
    process.stdout.write(newLines.join('\n\n') + '\n');
    return;
  }

  die(`Unknown command: ${cmd}\nRun: node scripts/youtube-tracker-rss.js (without args for help)`);
}

main().catch(err => {
  console.error(err?.message || String(err));
  process.exit(2);
});
