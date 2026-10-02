# Changelog — youtube-publisher

Current version: `1.8.3`

## v1.8.3 (2026-10-01)

`youtube-update-description.ts` **v1.8：YouTube 章节显示契约门禁**（上传口）。

- **背景**：YouTube 章节显示有 3 条硬规则——首章 `0:00`、至少 3 章、**每章 ≥10 秒**。任一不满足 → YouTube **静默忽略整份章节列表**：描述原文照旧（肉眼查不出），播放轴却没有任何章节标记。2026-10-01 charles_schwab（FWtCu4EKcPo）实测：`0:00 开场…` 与 `0:01 背景…` 只差 1 秒 → 18 章全废；同期 capital_one（最短间隔 31s）正常显示。
- **门禁**：`main()` 在上传前调用 `chapterContractProblems()`；有违规 → 打印违规清单 + 修复指引并 **exit 3，拒绝上传**。描述里完全没有章节块时只打 `WARN` 不拦（避免误伤历史无章节的描述）。
- **修复入口**：`duanku-youtube-publish/scripts/split_description_chapters.py`（v2.83.0 起内置自愈：首章归位 0:00、间隔 <10s 并入上一章）；复检 `--validate`。
- **配套门禁**：blog-pipeline v2.61.2（发布前 2/8 硬门禁）、publish v2.83.0 `verify_publish.py` 新增 `description_chapter_contract` 检查（发布后）。

## v1.8.2 (2026-09-30)

- Removed automatic per-video playlist assignment from the uploader and publishing contract at the user's request.
- Retained authenticated public playlist export for read-only blog, GitHub knowledge-base and resource-site series pages.

## v1.8.1 (2026-09-30)

- Public playlist export now excludes unlisted, private and unknown-visibility items so staged videos cannot leak through series indexes.

## v1.8.0 (2026-09-30)

- `youtube-upload.ts` accepts repeated or comma-separated `--playlist` values and adds an upload to each unique playlist.
- Added `export-playlists.ts` and `npm run export:playlists` to export all public owned playlists with ordered video metadata for downstream blog and GitHub synchronization.

## v1.7.0 (2026-08-28)

- Added full Live broadcast and encoder-stream lifecycle commands.
- Added dry-run previews, explicit confirmations, stream-key redaction, and transition preflights.
- Added shared-stream conflict detection; deliberate reuse now requires `--allow-shared-stream`.
- Added previous-broadcast setting inspection and safe nonstandard-setting inheritance.
- Added OAuth `state` validation, loopback-only callback binding, and `0600` token permissions.
- Live updates now round-trip only API-writable fields, omit response-only fields, and never submit both closed-caption representations. Unsupported latency updates are rejected at CLI parsing.
- Removed automatic deletion of metadata-only upload shells. Interrupted inserts stop fail-closed with stable P0D/ambiguous markers and distinct exit codes instead of issuing another internal insert.
- Caption retries update an exact existing language/name track or insert a new one; they no longer delete caption tracks before replacement succeeds.
- Added upload-recovery, caption-upsert, Live service and post-create recovery regression tests plus a path-scoped GitHub Actions workflow.
- Updated `googleapis` to a patched dependency line.

## v1.6.4 (2026-08-26)

- Fix `upload-captions.ts` captions.insert failing with HTTP 400 `invalidMetadata`.
- Root cause: the script passed `mimeType: "text/vtt"` in `media` and a
  `Content-Type: application/octet-stream` header override on the request.
  googleapis builds the `multipart/related` body and computes its own boundary;
  overriding the header corrupts metadata parsing, so the API saw garbage
  snippet values. Also added `isDraft: false` to match the working call site
  in `youtube-upload.ts`.
- Verified live: caption upload succeeds immediately after removing both.

## v1.6.3 (2026-08-02)

- **youtube-update-description.ts v1.5**: Better error diagnostics for transient proxy failures. `isNetwork` now catches empty/blank error messages (proxy drops with "Error: \n"), logs full error stack and HTTP status when available, and matches proxy EOF / `ECONNRESET` / `ETIMEDOUT` / `EPIPE` by error code in addition to message string.

## v1.6.2 (2026-07-28)

- **Thumbnail 2 MB limit check**: All three thumbnail upload paths (main upload, `--subtitles-only` recovery, `upload-thumbnail.ts`) now validate file size before sending. Files exceeding YouTube's 2 MB limit are rejected with a clear error message instead of failing silently with "The provided image content is invalid."

## v1.6.1 (2026-07-28)

- **P0D guard**: When retry-recovering a server-side upload after "Premature close", verify the video has real content (`contentDetails.duration !== "P0D"`) before accepting it. P0D metadata-only shells are auto-deleted and the upload is retried properly instead of being treated as a successful recovery.

## v1.6.0 (2026-07-28)

- Add `upload-thumbnail.ts` for safe thumbnail-only recovery with required CLI parameters, bounded retry, video verification, and structured output.
- Remove the tracked hardcoded repair script that could permanently delete a fixed video ID.
- Cover the thumbnail recovery command in the production TypeScript gate and document it in English and Chinese.

## v1.5.0 (2026-07-21)

- Use `searchResult.id.videoId` when recovering a server-side upload after a retryable transport error.
- Add the reusable, strict-typed `list-uploads.ts` helper for duplicate-upload inspection.
- Add `npm run typecheck:production` for the upload and recovery scripts.
- Move version history out of frontmatter so the Skill metadata is valid YAML.

## v1.4.0 (2026-06-27)

- Return `rc=2` and structured subtitle/thumbnail markers for partial post-upload failures.
- Add `--subtitles-only` with `--video-id` and a pipeline-readable Upload Summary.

## v1.3.0

- Add proxy support and retry recovery for premature connection closure.

## v1.2.0 (2026-06-11)

- Normalize trailing newlines when verifying updated descriptions.

## v1.1.1 (2026-06-11)

- Correct the CommonJS import for `open` v8.x.

## v1.1.0 (2026-06-09)

- Share OAuth2 authentication and token refresh across publisher scripts.

## v1.0.1 (2026-05-23)

- Add strict execution and metadata-validation rules.
