# Changelog — youtube-publisher

Current version: `1.5.0`

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
