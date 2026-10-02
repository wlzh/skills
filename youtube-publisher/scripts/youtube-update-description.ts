/**
 * youtube-update-description.ts — Update a YouTube video description with
 * post-write verification and robust token refresh.
 *
 * Changelog:
 *  v1.8  2026-10-01  YouTube chapter-display contract gate (refuse upload on
 *                    invalid chapters: first!=0:00 / <3 chapters / any gap<10s)
 *  v1.7  2026-09-28  Strip duanku baseline header before upload
 *  v1.7.1 2026-09-28 Unknown flags are fatal, not silent no-ops
 *  v1.6  2026-08-16  Update after retry with fresh token
 *  v1.5  2026-08-02  Better error diagnostics for transient proxy failures
 *    - Catch empty/blank error messages (proxy drops with "Error: \n")
 *    - Log full error stack and HTTP status when available
 *    - Expand isNetwork to include proxy EOF and empty-message patterns
 *  v1.4  2026-06-27  Network error retry for API calls
 *    - Wrap videos.list and videos.update in retry-with-backoff (3 attempts,
 *      5s delay) to handle transient "Premature close" / ECONNRESET errors.
 *    - Separate from the verify-mismatch retry loop which already existed.
 *  v1.3  2026-06-11  Fix verify mismatch caused by trailing newline
 *    - YouTube API strips trailing newlines on storage, causing the exact
 *      string comparison to always fail (off by 1 char).
 *    - Fix: trimEnd() both sides before comparing.
 *  v1.2  2026-06-09  Refactor: use shared authenticate.ts module
 *    - Remove inline authenticate() function; import from ./authenticate.
 *    - Remove dotenv/TOKEN_PATH/google auth imports (handled by shared module).
 *  v1.1  2026-06-09  Post-write verification + token refresh fix
 *    - After videos.update, immediately GET to verify description matches.
 *    - If mismatch, retry up to 3 times with 5s delay.
 *    - Token refresh: always refresh when expiry_date is missing OR expired
 *      (previously skipped refresh when expiry_date was absent).
 *    - After refresh, ensure expiry_date is present in saved token file
 *      (compute from expires_in if Google omits it).
 */

import * as fs from "fs";
import { authenticate } from "./authenticate";

const MAX_VERIFY_RETRIES = 3;
const VERIFY_RETRY_DELAY_MS = 5000;
const MAX_NETWORK_RETRIES = 3;
const NETWORK_RETRY_DELAY_MS = 5000;

/**
 * Retry wrapper for transient network errors (Premature close, ECONNRESET, etc.).
 * Distinct from the verify-mismatch retry loop.
 */
async function withNetworkRetry<T>(
  fn: () => Promise<T>,
  label: string
): Promise<T> {
  let lastErr: unknown;
  for (let attempt = 1; attempt <= MAX_NETWORK_RETRIES; attempt++) {
    try {
      return await fn();
    } catch (err: any) {
      lastErr = err;
      const isNetwork =
        err.message?.includes("Premature close") ||
        err.message?.includes("ECONNRESET") ||
        err.message?.includes("ETIMEDOUT") ||
        err.message?.includes("EPIPE") ||
        err.message?.includes("socket hang up") ||
        // v1.5: proxy drops often produce empty or whitespace-only messages
        !err.message?.trim() ||
        err.code === "ECONNRESET" ||
        err.code === "ETIMEDOUT" ||
        err.code === "EPIPE";
      if (isNetwork && attempt < MAX_NETWORK_RETRIES) {
        console.error(
          `${label} network error (attempt ${attempt}/${MAX_NETWORK_RETRIES}): ${err.message}`
        );
        await new Promise((r) => setTimeout(r, NETWORK_RETRY_DELAY_MS));
      } else {
        throw err;
      }
    }
  }
  throw lastErr;
}

async function updateDescription(
  youtube: any,
  videoId: string,
  newDescription: string
): Promise<void> {
  // Get current snippet to preserve required fields
  const videoResponse: any = await withNetworkRetry(
    () => youtube.videos.list({ id: [videoId], part: ["snippet"] }),
    "videos.list (get snippet)"
  );

  const video = videoResponse.data.items?.[0];
  if (!video) {
    throw new Error(`Video not found: ${videoId}`);
  }

  const cur = video.snippet!;

  // Strip angle brackets — YouTube rejects them in descriptions
  const cleanDescription = newDescription.replace(/<[^>]*>/g, "").replace(/[<>]/g, "");

  // Build the snippet update payload
  const snippetPayload = {
    title: cur.title,
    description: cleanDescription,
    categoryId: cur.categoryId,
    tags: cur.tags,
    defaultLanguage: cur.defaultLanguage,
    defaultAudioLanguage: cur.defaultAudioLanguage,
  };

  // Update + verify loop
  for (let attempt = 1; attempt <= MAX_VERIFY_RETRIES; attempt++) {
    await withNetworkRetry(
      () => youtube.videos.update({
        part: ["snippet"],
        requestBody: {
          id: videoId,
          snippet: snippetPayload,
        },
      }),
      "videos.update"
    );

    // Verify: GET the video again and compare description
    const verifyResponse: any = await withNetworkRetry(
      () => youtube.videos.list({ id: [videoId], part: ["snippet"] }),
      "videos.list (verify)"
    );

    const actualDesc = verifyResponse.data.items?.[0]?.snippet?.description || "";

    // YouTube API strips trailing newlines on storage — trim both before comparing
    if (actualDesc.trimEnd() === cleanDescription.trimEnd()) {
      console.log(`Description updated and verified for video ${videoId}`);
      return;
    }

    // Mismatch — log details and decide whether to retry
    console.error(
      `Verify mismatch (attempt ${attempt}/${MAX_VERIFY_RETRIES}): ` +
      `expected ${cleanDescription.trimEnd().length} chars, got ${actualDesc.trimEnd().length} chars`
    );

    if (attempt < MAX_VERIFY_RETRIES) {
      console.error(`Retrying in ${VERIFY_RETRY_DELAY_MS / 1000}s...`);
      await new Promise((resolve) => setTimeout(resolve, VERIFY_RETRY_DELAY_MS));
    }
  }

  // All retries exhausted
  console.error(
    `Error: Description verification failed after ${MAX_VERIFY_RETRIES} attempts for video ${videoId}`
  );
  process.exit(1);
}

function parseArgs(): { videoId: string; description: string; descriptionFile: string } {
  const args = process.argv.slice(2);
  let videoId = "";
  let description = "";
  let descriptionFile = "";

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    const next = args[i + 1];
    switch (arg) {
      case "--video-id":
        videoId = next!;
        i++;
        break;
      case "--description":
        description = next!;
        i++;
        break;
      case "--description-file":
        descriptionFile = next!;
        i++;
        break;
      case "--help":
      case "-h":
        console.log(`
Usage:
  npx ts-node youtube-update-description.ts --video-id <ID> --description "new desc"
  npx ts-node youtube-update-description.ts --video-id <ID> --description-file <path>
`);
        process.exit(0);
      default:
        // v1.7.1 (2026-09-28): unknown flags are fatal, not silent no-ops.
        // A --dry-run passed on 9/28 was silently ignored and a truncated test
        // file went live. Fail fast instead.
        if (arg.startsWith("--")) {
          console.error(`Error: unknown option "${arg}" — this script has no such flag, refusing to run (v1.7.1 guard)`);
          process.exit(2);
        }
        break;
    }
  }

  if (!videoId) {
    console.error("Error: --video-id is required");
    process.exit(1);
  }

  if (descriptionFile && fs.existsSync(descriptionFile)) {
    description = fs.readFileSync(descriptionFile, "utf-8");
  }

  if (!description) {
    console.error("Error: --description or --description-file is required");
    process.exit(1);
  }

  // v1.7 (2026-09-28): Strip duanku baseline header before upload.
  // run_pipeline v2.46+ writes {slug}-youtube-description-final.txt with a 6-line
  // "# YouTube description baseline" comment header for manual-diff use only.
  // On 9/15 (tello) / 9/27 (capital_one) / 9/28 (maya), agent-driven description
  // edits loaded that baseline file and re-uploaded it verbatim, leaking the
  // header into live YouTube descriptions. Guard here so no caller path can
  // ever push the header on-wire again.
  const BASELINE_MARKER = "# YouTube description baseline";
  if (description.startsWith(BASELINE_MARKER)) {
    const lines = description.split("\n");
    // Header = leading comment lines + the "─────" separator line + blank line(s)
    let i = 0;
    while (i < lines.length) {
      const l = lines[i].trim();
      if (l === "" || l.startsWith("#") || l.startsWith("──")) i++;
      else break;
    }
    description = lines.slice(i).join("\n").replace(/^\n+/, "");
    console.log("NOTE: stripped baseline header before upload (v1.7 guard)");
  }

  return { videoId, description, descriptionFile };
}

// v1.8 (2026-10-01): YouTube chapter-display contract gate.
// YouTube requires: first chapter 0:00, at least 3 chapters, every chapter
// >=10 seconds. ANY violation makes YouTube silently drop the WHOLE chapter
// list — the description still looks fine but the progress bar shows no
// chapters (2026-10-01 charles_schwab FWtCu4EKcPo: "0:00"/"0:01" sat 1 second
// apart, killing all 18 chapters). Refuse the upload instead of publishing a
// description whose chapters cannot render; fix with
// duanku-youtube-publish/scripts/split_description_chapters.py (self-healing)
// then re-run --validate.
const YOUTUBE_MIN_CHAPTER_SECONDS = 10;
const YOUTUBE_MIN_CHAPTERS = 3;

function chapterContractProblems(description: string): string[] {
  const entries: Array<{ sec: number; line: string }> = [];
  for (const raw of description.split("\n")) {
    const line = raw.trim();
    const m = line.match(/^(\d{1,3}):(\d{2})\s/);
    if (m) entries.push({ sec: parseInt(m[1], 10) * 60 + parseInt(m[2], 10), line });
  }
  if (entries.length === 0) return [];  // 无章节块：下方单独 WARN，不拦上传
  const problems: string[] = [];
  if (entries[0].sec !== 0) problems.push(`首章不是 0:00（实际 ${entries[0].line}）`);
  if (entries.length < YOUTUBE_MIN_CHAPTERS) problems.push(`章节数 ${entries.length} < ${YOUTUBE_MIN_CHAPTERS}`);
  for (let i = 0; i < entries.length - 1; i++) {
    const gap = entries[i + 1].sec - entries[i].sec;
    if (gap < YOUTUBE_MIN_CHAPTER_SECONDS) {
      problems.push(`间隔 ${gap}s < ${YOUTUBE_MIN_CHAPTER_SECONDS}s: «${entries[i].line}» → «${entries[i + 1].line}»`);
    }
  }
  return problems;
}

async function main() {
  const { videoId, description } = parseArgs();
  const chapterProblems = chapterContractProblems(description);
  if (chapterProblems.length > 0) {
    console.error("❌ 章节不符合 YouTube 显示契约（首章 0:00 / 每章 ≥10s / ≥3 章），拒绝上传：");
    for (const p of chapterProblems) console.error(`   - ${p}`);
    console.error("YouTube 会静默忽略整份章节列表 → 播放轴不显示章节（描述里看不出异常）。");
    console.error("修复：python3 duanku-youtube-publish/scripts/split_description_chapters.py --timeline <t> --scene-plan <sp> --description <当前描述> --output <out>（内置自愈）；复检：同脚本 --validate。");
    process.exit(3);
  }
  if (!/^\s*\d{1,3}:\d{2}\s/m.test(description)) {
    console.warn("WARN: 描述中没有章节块——播放轴不会有章节标记（v1.8 门禁仅告警，不拦截）");
  }
  const { youtube } = await authenticate();
  await updateDescription(youtube, videoId, description);
}

main().catch((err) => {
  // v1.5: Log full error details for debugging transient proxy failures
  const msg = err?.message?.trim() || "(empty error message — likely proxy drop)";
  const stack = err?.stack || "";
  const code = err?.code || "";
  console.error(`Error: ${msg}`);
  if (code) console.error(`Error code: ${code}`);
  if (stack && stack !== msg) console.error(`Stack: ${stack}`);
  process.exit(1);
});
