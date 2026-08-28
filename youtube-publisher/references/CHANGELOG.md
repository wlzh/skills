# Changelog — youtube-publisher

Current version: `1.7.0`

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
