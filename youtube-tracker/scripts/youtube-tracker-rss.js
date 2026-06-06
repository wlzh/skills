#!/usr/bin/env node
/**
 * youtube-tracker-rss skill script
 * v3.0.0 - Parallel fetching + notify mode (no LLM needed for cron)
 *
 * Uses YouTube RSS feeds instead of API - no quota limits!
 * Auto-detects proxy from env vars or falls back to common local proxies.
 *
 * Commands:
 *   add <channelId|@handle|url>   添加频道
 *   remove <channelId|@handle|url> 移除频道
 *   list                          列出所有频道
 *   check                         检查新视频（原样输出）
 *   notify                        检查新视频并输出 Telegram 格式消息
 *
 * State files (relative to this script):
 *   ../state/config.json  { channels: Array<{channelId, title, handle?, addedAt}> }
 *   ../state/seen.json    { seenVideoIds: string[], updatedAt }
 *
 * v3.0.0 changes:
 *   - Parallel HTTP fetching (all channels concurrent via async curl)
 *   - New `notify` command: outputs Telegram-ready message, exit code signals result
 *     exit 0 + stdout: new videos found, stdout is the message
 *     exit 0 + no stdout: no new videos
 *     exit 1: error
 *   - ~10x faster: 55 channels now check in ~5-8s (was ~45s with serial curl)
 */

const fs = require('fs');
const path = require('path');
const { execSync, exec: execAsync } = require('child_process');
const { promisify } = require('util');

const execPromise = promisify(execAsync);

// ── Proxy ──────────────────────────────────────────────────────────
const PROXY = process.env.HTTPS_PROXY || process.env.https_proxy ||
              process.env.HTTP_PROXY || process.env.http_proxy ||
              'http://127.0.0.1:10808';

const STATE_DIR = path.resolve(__dirname, '..', 'state');
const CONFIG_PATH = path.join(STATE_DIR, 'config.json');
const SEEN_PATH = path.join(STATE_DIR, 'seen.json');

// ── HTTP with proxy (async parallel) ───────────────────────────────
/**
 * Fetch URL using curl with proxy (async, for parallel execution).
 */
async function httpGetAsync(url, timeoutMs = 15000) {
  const cmd = `curl -sS -m ${Math.ceil(timeoutMs / 1000)} -x "${PROXY}" -L "${url}"`;
  const { stdout } = await execPromise(cmd, {
    encoding: 'utf-8',
    maxBuffer: 10 * 1024 * 1024,
    timeout: timeoutMs + 5000,
  });
  return stdout;
}

/**
 * Fetch URL using curl with proxy (sync, for one-off calls like add/remove).
 */
function httpGetSync(url, timeoutMs = 15000) {
  const cmd = `curl -sS -m ${Math.ceil(timeoutMs / 1000)} -x "${PROXY}" -L "${url}"`;
  try {
    return execSync(cmd, { encoding: 'utf-8', maxBuffer: 10 * 1024 * 1024, timeout: timeoutMs + 5000 });
  } catch (err) {
    throw new Error(`Fetch failed: ${url} - ${err.message}`);
  }
}

// ── Parallel channel fetcher ───────────────────────────────────────
/**
 * Fetch multiple channels' RSS feeds in parallel.
 * Returns array of { channel, videos, error } objects.
 */
async function fetchAllChannelsParallel(channels) {
  const concurrency = 15; // curl handles connections well, 15 concurrent is safe
  const results = [];

  for (let i = 0; i < channels.length; i += concurrency) {
    const batch = channels.slice(i, i + concurrency);
    const batchResults = await Promise.allSettled(
      batch.map(async (c) => {
        try {
          const url = `https://www.youtube.com/feeds/videos.xml?channel_id=${encodeURIComponent(c.channelId)}`;
          const xml = await httpGetAsync(url);
          const videos = parseRSS(xml);
          return { channel: c, videos, error: null };
        } catch (err) {
          return { channel: c, videos: [], error: `${c.title}: ${err.message}` };
        }
      })
    );

    for (const r of batchResults) {
      if (r.status === 'fulfilled') {
        results.push(r.value);
      } else {
        // Should not happen since we catch inside, but just in case
        results.push({ channel: null, videos: [], error: r.reason?.message || String(r.reason) });
      }
    }
  }

  return results;
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

// ── YouTube helpers (sync, for add/remove) ─────────────────────────
function fetchChannelRSSSync(channelId) {
  const url = `https://www.youtube.com/feeds/videos.xml?channel_id=${encodeURIComponent(channelId)}`;
  const xml = httpGetSync(url);
  return parseRSS(xml);
}

function resolveHandleToChannelId(handle) {
  const handleClean = handle.replace(/^@/, '');

  try {
    const channelUrl = `https://www.youtube.com/@${handleClean}`;
    const html = httpGetSync(channelUrl);

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
    const xml = httpGetSync(url);

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

// ── Shared check logic ─────────────────────────────────────────────
/**
 * Core check logic used by both `check` and `notify` commands.
 * Returns { newVideos: Array<{channel, video}>, errors: string[] }
 */
async function doCheck(cfg) {
  if (!cfg.channels.length) return { newVideos: [], errors: [] };

  const seen = getSeen();
  const seenSet = new Set(seen.seenVideoIds);
  const newVideos = [];
  const newlySeen = [];
  const errors = [];

  console.error(`检查 ${cfg.channels.length} 个频道... (proxy: ${PROXY}, parallel: 15)`);

  const fetchResults = await fetchAllChannelsParallel(cfg.channels);

  for (const { channel, videos, error } of fetchResults) {
    if (error) {
      errors.push(error);
      continue;
    }
    if (!channel) continue;

    for (const v of videos) {
      if (seenSet.has(v.videoId)) continue;

      // Baseline: skip videos published before channel was added
      if (channel.addedAt && v.publishedAt) {
        const added = Date.parse(channel.addedAt);
        const pub = Date.parse(v.publishedAt);
        if (!Number.isNaN(added) && !Number.isNaN(pub) && pub <= added) {
          seenSet.add(v.videoId);
          newlySeen.push(v.videoId);
          continue;
        }
      }

      seenSet.add(v.videoId);
      newlySeen.push(v.videoId);

      newVideos.push({
        channel: channel,
        video: v,
      });
    }
  }

  // Persist seen IDs
  if (newlySeen.length) {
    const merged = (seen.seenVideoIds || []).concat(newlySeen);
    const unique = Array.from(new Set(merged));
    const trimmed = unique.slice(Math.max(0, unique.length - 2000));
    saveSeen({ seenVideoIds: trimmed, updatedAt: nowIso() });
  }

  return { newVideos, errors };
}

// ── Main ───────────────────────────────────────────────────────────
async function main() {
  const { cmd, rest } = parseArgs();
  if (!cmd) {
    die('Usage: node scripts/youtube-tracker-rss.js <add|remove|list|check|notify> ...\n\nCommands:\n  add <channelId|@handle|url>  添加频道\n  remove <id|@handle|url>     移除频道\n  list                        列出所有频道\n  check                       检查新视频\n  notify                      检查新视频（Telegram 消息格式）');
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

  // ── check command: original output format (backwards compatible) ──
  if (cmd === 'check') {
    const { newVideos, errors } = await doCheck(cfg);

    if (errors.length) {
      console.error(`\n警告: ${errors.length} 个频道获取失败:`);
      errors.forEach(e => console.error(`  - ${e}`));
    }

    if (!newVideos.length) {
      console.error('无新视频');
      return;
    }

    console.error(`发现 ${newVideos.length} 个新视频!\n`);

    const lines = newVideos.map(({ channel, video }) => {
      const chName = channel.title || video.channelTitle || channel.channelId;
      return [
        `频道：${chName}`,
        `标题：${video.title}`,
        `链接：${video.link || videoUrl(video.videoId)}`,
      ].join('\n');
    });

    process.stdout.write(lines.join('\n\n') + '\n');
    return;
  }

  // ── notify command: Telegram-ready output for cron ────────────────
  if (cmd === 'notify') {
    const { newVideos, errors } = await doCheck(cfg);

    if (errors.length) {
      console.error(`警告: ${errors.length} 个频道获取失败: ${errors.join('; ')}`);
      // Don't exit with error - still report any new videos found
    }

    if (!newVideos.length) {
      // No new videos - exit silently (stdout empty)
      console.error('无新视频');
      return;
    }

    // Format: one message per video, suitable for Telegram
    // Each video gets its own block so they can be sent individually
    const messages = newVideos.map(({ channel, video }) => {
      const chName = channel.title || video.channelTitle || channel.channelId;
      const lines = [];
      lines.push(`📺 ${chName}`);
      lines.push(`🎬 ${video.title}`);
      lines.push(`🔗 ${video.link || videoUrl(video.videoId)}`);
      return lines.join('\n');
    });

    // Output all as a single block, separated by blank lines
    // The cron systemEvent handler can split on \n\n if needed
    const output = messages.join('\n\n');
    process.stdout.write(output + '\n');

    console.error(`发现 ${newVideos.length} 个新视频，已输出到 stdout`);
    return;
  }

  die(`Unknown command: ${cmd}`);
}

main().catch(err => {
  console.error(err?.message || String(err));
  process.exit(2);
});
