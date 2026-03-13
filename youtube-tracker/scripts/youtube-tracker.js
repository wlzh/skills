#!/usr/bin/env node
/**
 * youtube-tracker skill script
 *
 * Commands:
 *   set-key <apiKey>
 *   validate-key
 *   add <channelInput>
 *   remove <channelId>
 *   list
 *   check
 *
 * State files (relative to this script):
 *   ../state/config.json  { apiKey: string, channels: Array<{channelId, title, handle?, addedAt}> }
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
  if (typeof cfg.apiKey !== 'string') cfg.apiKey = '';
  return cfg;
}

function saveConfig(cfg) {
  ensureStateDir();
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
    // https://www.youtube.com/channel/UC...
    const m1 = p.match(/^\/channel\/(UC[\w-]{20,})/);
    if (m1) return { kind: 'channelId', value: m1[1] };
    // https://www.youtube.com/@handle
    const m2 = p.match(/^\/@([^\/]+)/);
    if (m2) return { kind: 'handle', value: m2[1] };
  } catch {}

  return { kind: 'unknown', value: s };
}

async function ytGetJson(url) {
  const res = await fetch(url, {
    method: 'GET',
    headers: { 'accept': 'application/json' },
  });
  const text = await res.text();
  let json;
  try {
    json = JSON.parse(text);
  } catch {
    // non-json response
    throw new Error(`YouTube API non-JSON response (status ${res.status}): ${text.slice(0, 200)}`);
  }
  if (!res.ok) {
    const msg = json?.error?.message || `HTTP ${res.status}`;
    throw new Error(`YouTube API error: ${msg}`);
  }
  return json;
}

async function resolveChannel(input, apiKey) {
  const parsed = normalizeChannelInput(input);

  if (parsed.kind === 'channelId') {
    const url = `https://www.googleapis.com/youtube/v3/channels?part=snippet&id=${encodeURIComponent(parsed.value)}&key=${encodeURIComponent(apiKey)}`;
    const j = await ytGetJson(url);
    const item = j.items?.[0];
    if (!item) throw new Error(`Channel not found for id: ${parsed.value}`);
    return {
      channelId: item.id,
      title: item.snippet?.title || item.id,
      handle: item.snippet?.customUrl || null,
    };
  }

  if (parsed.kind === 'handle') {
    // Use search to resolve handle -> channelId
    // Note: search query with @handle is generally reliable.
    const q = `@${parsed.value}`;
    const url = `https://www.googleapis.com/youtube/v3/search?part=snippet&type=channel&maxResults=5&q=${encodeURIComponent(q)}&key=${encodeURIComponent(apiKey)}`;
    const j = await ytGetJson(url);
    const item = j.items?.find(it => it.id?.channelId);
    if (!item) throw new Error(`Channel not found for handle: @${parsed.value}`);
    return {
      channelId: item.id.channelId,
      title: item.snippet?.channelTitle || item.snippet?.title || item.id.channelId,
      handle: `@${parsed.value}`,
    };
  }

  throw new Error(`Unsupported channel input: ${input}`);
}

async function validateKey(apiKey) {
  const url = `https://www.googleapis.com/youtube/v3/i18nLanguages?part=snippet&hl=en_US&key=${encodeURIComponent(apiKey)}`;
  await ytGetJson(url);
  return true;
}

async function fetchLatestVideos(channelId, apiKey, maxResults = 5) {
  // Search for most recent videos on a channel.
  const url = `https://www.googleapis.com/youtube/v3/search?part=snippet&channelId=${encodeURIComponent(channelId)}&order=date&type=video&maxResults=${maxResults}&key=${encodeURIComponent(apiKey)}`;
  const j = await ytGetJson(url);
  const items = j.items || [];
  return items
    .filter(it => it.id?.videoId)
    .map(it => ({
      videoId: it.id.videoId,
      title: it.snippet?.title || '',
      description: it.snippet?.description || '',
      publishedAt: it.snippet?.publishedAt || '',
      channelTitle: it.snippet?.channelTitle || '',
    }));
}

function summarize(desc) {
  const s = String(desc || '').replace(/\s+/g, ' ').trim();
  if (!s) return '';
  return s.length > 120 ? s.slice(0, 120) + '…' : s;
}

function videoUrl(videoId) {
  return `https://www.youtube.com/watch?v=${videoId}`;
}

async function main() {
  const { cmd, rest } = parseArgs();
  if (!cmd) {
    die('Usage: node scripts/youtube-tracker.js <set-key|validate-key|add|remove|list|check> ...');
  }

  const cfg = getConfig();

  if (cmd === 'set-key') {
    const key = rest[0];
    if (!key) die('Missing apiKey');
    cfg.apiKey = key.trim();
    saveConfig(cfg);
    console.log('OK: apiKey saved');
    return;
  }

  if (cmd === 'validate-key') {
    if (!cfg.apiKey) die('API key not set. Run: set-key <apiKey>');
    await validateKey(cfg.apiKey);
    console.log('OK: apiKey valid');
    return;
  }

  if (cmd === 'add') {
    if (!cfg.apiKey) die('API key not set. Run: set-key <apiKey>');
    const input = rest.join(' ').trim();
    if (!input) die('Missing channel input');

    const ch = await resolveChannel(input, cfg.apiKey);
    const exists = cfg.channels.some(c => c.channelId === ch.channelId);
    if (!exists) {
      cfg.channels.push({
        channelId: ch.channelId,
        title: ch.title,
        handle: ch.handle,
        addedAt: nowIso(),
      });
      saveConfig(cfg);

      // Baseline: mark current latest videos as seen to avoid "old videos" being announced as new.
      try {
        const baseline = await fetchLatestVideos(ch.channelId, cfg.apiKey, 5);
        if (baseline.length) {
          const seen = getSeen();
          const merged = (seen.seenVideoIds || []).concat(baseline.map(v => v.videoId));
          const unique = Array.from(new Set(merged));
          const trimmed = unique.slice(Math.max(0, unique.length - 500));
          saveSeen({ seenVideoIds: trimmed, updatedAt: nowIso() });
        }
      } catch {
        // ignore baseline errors; add still succeeds
      }
    }
    console.log(`OK: added ${ch.title} (${ch.channelId})`);
    return;
  }

  if (cmd === 'remove') {
    const channelId = rest[0];
    if (!channelId) die('Missing channelId');
    const before = cfg.channels.length;
    cfg.channels = cfg.channels.filter(c => c.channelId !== channelId);
    saveConfig(cfg);
    console.log(`OK: removed ${before - cfg.channels.length}`);
    return;
  }

  if (cmd === 'list') {
    if (!cfg.channels.length) {
      console.log('No channels tracked');
      return;
    }
    for (const c of cfg.channels) {
      console.log(`${c.channelId}\t${c.title}${c.handle ? `\t${c.handle}` : ''}`);
    }
    return;
  }

  if (cmd === 'check') {
    if (!cfg.apiKey) die('API key not set. Run: set-key <apiKey>');
    if (!cfg.channels.length) return; // silent

    const seen = getSeen();
    const seenSet = new Set(seen.seenVideoIds);

    const newLines = [];
    const newlySeen = [];

    for (const c of cfg.channels) {
      const vids = await fetchLatestVideos(c.channelId, cfg.apiKey, 5);
      for (const v of vids) {
        if (seenSet.has(v.videoId)) continue;
        // Mark as new
        seenSet.add(v.videoId);
        newlySeen.push(v.videoId);

        const chName = c.title || v.channelTitle || c.channelId;
        const line = [
          `频道：${chName}`,
          `标题：${v.title}`,
          `简介：${summarize(v.description)}`,
          `链接：${videoUrl(v.videoId)}`,
        ].join('\n');
        newLines.push(line);
      }
    }

    if (newlySeen.length) {
      // keep seen list bounded
      const merged = (seen.seenVideoIds || []).concat(newlySeen);
      const unique = Array.from(new Set(merged));
      // Keep last 500
      const trimmed = unique.slice(Math.max(0, unique.length - 500));
      saveSeen({ seenVideoIds: trimmed, updatedAt: nowIso() });
    }

    if (!newLines.length) return; // silent

    // separate items by blank line
    process.stdout.write(newLines.join('\n\n') + '\n');
    return;
  }

  die(`Unknown command: ${cmd}`);
}

main().catch(err => {
  console.error(err?.message || String(err));
  process.exit(2);
});
