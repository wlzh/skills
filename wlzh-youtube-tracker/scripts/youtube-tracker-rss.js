#!/usr/bin/env node
/**
 * wlzh-youtube-tracker skill script
 * v3.1.0 - Self-contained notify: sends Telegram directly, marks seen only on success
 *
 * Uses YouTube RSS feeds instead of API - no quota limits!
 * Auto-detects proxy from env vars or falls back to common local proxies.
 *
 * Commands:
 *   add <channelId|@handle|url>   添加频道
 *   remove <channelId|@handle|url> 移除频道
 *   list                          列出所有频道
 *   check                         检查新视频（原样输出，立即标记 seen）
 *   notify                        检查新视频 → 直接发 Telegram → 发送成功才标记 seen
 *
 * State files (relative to this script):
 *   ../state/config.json  { channels: Array<{channelId, title, handle?, addedAt}> }
 *   ../state/seen.json    { seenVideoIds: string[], updatedAt }
 *
 * v3.1.0 changes:
 *   - notify 命令直接调 Telegram Bot API 发送消息
 *   - 发送成功才标记 seen，失败的视频下次自动重试
 *   - Cron 只需 exec 脚本，不需要 LLM 中转
 *   - 从 openclaw.json 自动读取 bot token
 *
 * v3.0.0 changes:
 *   - Parallel HTTP fetching (all channels concurrent via async curl)
 *   - ~10x faster: 55 channels now check in ~5-8s (was ~45s with serial curl)
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
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

// ── Telegram config (read from openclaw.json) ──────────────────────
const OPENCLAW_CONFIG_PATH = path.join(os.homedir(), '.openclaw', 'openclaw.json');
const TG_CHAT_ID = '-1003831627871';
const TG_TOPIC_ID = '1016';

function loadBotToken() {
  try {
    const cfg = JSON.parse(fs.readFileSync(OPENCLAW_CONFIG_PATH, 'utf8'));
    const token = cfg?.channels?.telegram?.accounts?.default?.botToken;
    if (!token) throw new Error('botToken not found in openclaw.json');
    return token;
  } catch (err) {
    console.error(`无法读取 Telegram Bot Token: ${err.message}`);
    console.error(`请确认 ${OPENCLAW_CONFIG_PATH} 中 channels.telegram.accounts.default.botToken 存在`);
    return null;
  }
}

/**
 * Send a message to Telegram via Bot API.
 * Returns true on success, false on failure.
 */
async function sendTelegram(botToken, text) {
  const url = `https://api.telegram.org/bot${botToken}/sendMessage`;
  const body = JSON.stringify({
    chat_id: TG_CHAT_ID,
    message_thread_id: TG_TOPIC_ID,
    text: text,
    parse_mode: 'HTML',
    disable_web_page_preview: false,
  });

  const cmd = `curl -sS -m 15 -x "${PROXY}" -X POST -H "Content-Type: application/json" -d '${body.replace(/'/g, "'\\''")}' "${url}"`;

  try {
    const { stdout } = await execPromise(cmd, { encoding: 'utf-8', timeout: 20000 });
    const resp = JSON.parse(stdout);
    if (resp.ok) {
      return true;
    } else {
      console.error(`Telegram API error: ${resp.description || JSON.stringify(resp)}`);
      return false;
    }
  } catch (err) {
    console.error(`Telegram send failed: ${err.message}`);
    return false;
  }
}

// ── HTTP with proxy (async parallel) ───────────────────────────────
async function httpGetAsync(url, timeoutMs = 15000) {
  const cmd = `curl -sS -m ${Math.ceil(timeoutMs / 1000)} -x "${PROXY}" -L "${url}"`;
  const { stdout } = await execPromise(cmd, {
    encoding: 'utf-8',
    maxBuffer: 10 * 1024 * 1024,
    timeout: timeoutMs + 5000,
  });
  return stdout;
}

function httpGetSync(url, timeoutMs = 15000) {
  const cmd = `curl -sS -m ${Math.ceil(timeoutMs / 1000)} -x "${PROXY}" -L "${url}"`;
  try {
    return execSync(cmd, { encoding: 'utf-8', maxBuffer: 10 * 1024 * 1024, timeout: timeoutMs + 5000 });
  } catch (err) {
    throw new Error(`Fetch failed: ${url} - ${err.message}`);
  }
}

// ── Parallel channel fetcher ───────────────────────────────────────
async function fetchAllChannelsParallel(channels) {
  const concurrency = 15;
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

/**
 * Add video IDs to seen list and persist.
 * Deduplicates and trims to max 2000 entries.
 */
function markAsSeen(videoIds) {
  if (!videoIds.length) return;
  const seen = getSeen();
  const merged = (seen.seenVideoIds || []).concat(videoIds);
  const unique = Array.from(new Set(merged));
  const trimmed = unique.slice(Math.max(0, unique.length - 2000));
  saveSeen({ seenVideoIds: trimmed, updatedAt: nowIso() });
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

// ── Core check logic ───────────────────────────────────────────────
/**
 * Detect new (unseen) videos across all channels.
 * Does NOT write to seen.json — caller decides when to mark as seen.
 *
 * Returns { newVideos: Array<{channel, video}>, skippedOld: string[], errors: string[] }
 */
async function detectNewVideos(cfg) {
  if (!cfg.channels.length) return { newVideos: [], skippedOld: [], errors: [] };

  const seen = getSeen();
  const seenSet = new Set(seen.seenVideoIds);
  const newVideos = [];
  const skippedOld = [];
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

      // Skip videos published before channel was added
      if (channel.addedAt && v.publishedAt) {
        const added = Date.parse(channel.addedAt);
        const pub = Date.parse(v.publishedAt);
        if (!Number.isNaN(added) && !Number.isNaN(pub) && pub <= added) {
          skippedOld.push(v.videoId);
          continue;
        }
      }

      newVideos.push({ channel, video: v });
    }
  }

  return { newVideos, skippedOld, errors };
}

/**
 * Legacy check: detect + immediately mark all as seen (for `check` command).
 * Used when we just want to see what's new without Telegram sending.
 */
async function doCheckAndMark(cfg) {
  const { newVideos, skippedOld, errors } = await detectNewVideos(cfg);

  // Mark everything as seen immediately (legacy behavior)
  const allNewIds = newVideos.map(v => v.video.videoId).concat(skippedOld);
  if (allNewIds.length) markAsSeen(allNewIds);

  return { newVideos, errors };
}

// ── Format helpers ─────────────────────────────────────────────────
function formatVideoNotify({ channel, video }) {
  const chName = channel.title || video.channelTitle || channel.channelId;
  return `📺 ${chName}\n🎬 ${video.title}\n🔗 ${video.link || videoUrl(video.videoId)}`;
}

function formatVideoCheck({ channel, video }) {
  const chName = channel.title || video.channelTitle || channel.channelId;
  return `频道：${chName}\n标题：${video.title}\n链接：${video.link || videoUrl(video.videoId)}`;
}

// ── Main ───────────────────────────────────────────────────────────
async function main() {
  const { cmd, rest } = parseArgs();
  if (!cmd) {
    die(`Usage: node scripts/youtube-tracker-rss.js <add|remove|list|check|notify> ...

Commands:
  add <channelId|@handle|url>  添加频道
  remove <id|@handle|url>     移除频道
  list                        列出所有频道
  check                       检查新视频（输出到 stdout，立即标记 seen）
  notify                      检查新视频 → 发 Telegram → 成功才标记 seen`);
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

  // ── check command: detect + output + mark seen immediately ───────
  if (cmd === 'check') {
    const { newVideos, errors } = await doCheckAndMark(cfg);

    if (errors.length) {
      console.error(`\n警告: ${errors.length} 个频道获取失败:`);
      errors.forEach(e => console.error(`  - ${e}`));
    }

    if (!newVideos.length) {
      console.error('无新视频');
      return;
    }

    console.error(`发现 ${newVideos.length} 个新视频!\n`);

    const lines = newVideos.map(formatVideoCheck);
    process.stdout.write(lines.join('\n\n') + '\n');
    return;
  }

  // ── notify command: detect → send Telegram → mark seen on success ─
  if (cmd === 'notify') {
    const { newVideos, skippedOld, errors } = await detectNewVideos(cfg);

    if (errors.length) {
      console.error(`警告: ${errors.length} 个频道获取失败: ${errors.join('; ')}`);
    }

    // Mark old videos (pre-add date) as seen immediately — they're not meant to be notified
    if (skippedOld.length) {
      markAsSeen(skippedOld);
    }

    if (!newVideos.length) {
      console.error('无新视频');
      // Exit 0, no stdout — cron handler knows this means nothing to send
      return;
    }

    console.error(`发现 ${newVideos.length} 个新视频，开始发送 Telegram...`);

    // Load bot token
    const botToken = loadBotToken();
    if (!botToken) {
      // Cannot send — output to stdout as fallback so LLM can still relay
      console.error('Bot token 不可用，回退到 stdout 输出模式');
      const messages = newVideos.map(formatVideoNotify);
      process.stdout.write(messages.join('\n\n') + '\n');
      // Still mark as seen to avoid re-detecting forever (better to lose once than spam)
      markAsSeen(newVideos.map(v => v.video.videoId));
      return;
    }

    // Send each video as a separate Telegram message
    let sentOk = 0;
    let sentFail = 0;
    const sentIds = [];

    for (const nv of newVideos) {
      const text = formatVideoNotify(nv);
      const ok = await sendTelegram(botToken, text);

      if (ok) {
        sentOk++;
        sentIds.push(nv.video.videoId);
        console.error(`✅ 已发送: ${nv.video.title}`);
      } else {
        sentFail++;
        console.error(`❌ 发送失败: ${nv.video.title} (${nv.video.videoId}) — 下次重试`);
      }
    }

    // Only mark successfully sent videos as seen
    if (sentIds.length) {
      markAsSeen(sentIds);
    }

    // Summary
    console.error(`\n发送完成: ✅ ${sentOk} 成功, ❌ ${sentFail} 失败`);
    if (sentFail > 0) {
      console.error(`失败的视频未被标记为 seen，下次 cron 会自动重试`);
      // Exit with code 1 to signal partial failure (cron can track this)
      process.exit(1);
    }

    return;
  }

  die(`Unknown command: ${cmd}`);
}

main().catch(err => {
  console.error(err?.message || String(err));
  process.exit(2);
});
