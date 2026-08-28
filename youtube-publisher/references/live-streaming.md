# YouTube Live operations

- [Broadcasts](#broadcasts)
- [Encoder streams](#encoder-streams)
- [Verification](#verification)

Use these commands for the core broadcast-and-stream lifecycle. Always preview mutations
with `--dry-run`, show the exact resource IDs and requested state to the user, and run the
real command only after authorization.

## Broadcasts

```bash
# List or inspect
npx ts-node youtube-live.ts live-broadcasts-list --status upcoming --json
npx ts-node youtube-live.ts live-broadcast-show --broadcast-id BROADCAST_ID --json

# Schedule; private is the safe default
npx ts-node youtube-live.ts live-broadcast-create \
  --title "Event title" \
  --description-file description.txt \
  --scheduled-start 2030-01-01T10:00:00Z \
  --scheduled-end 2030-01-01T11:00:00Z \
  --privacy private \
  --category 28 \
  --latency normal \
  --monitor-stream false \
  --auto-start true \
  --auto-stop true \
  --stream-id STREAM_ID \
  --thumbnail cover.jpg \
  --dry-run

# Merge editable fields without erasing untouched fields in an overwritten API part
npx ts-node youtube-live.ts live-broadcast-update \
  --broadcast-id BROADCAST_ID --title "Updated title" --dry-run

# Bind or unbind
npx ts-node youtube-live.ts live-broadcast-bind \
  --broadcast-id BROADCAST_ID --stream-id STREAM_ID --dry-run
npx ts-node youtube-live.ts live-broadcast-bind \
  --broadcast-id BROADCAST_ID --unbind --dry-run

# State transitions
npx ts-node youtube-live.ts live-broadcast-transition \
  --broadcast-id BROADCAST_ID --status testing --dry-run
npx ts-node youtube-live.ts live-broadcast-transition \
  --broadcast-id BROADCAST_ID --status live --dry-run
npx ts-node youtube-live.ts live-broadcast-transition \
  --broadcast-id BROADCAST_ID --status live --yes

# Cleanup
npx ts-node youtube-live.ts live-broadcast-delete \
  --broadcast-id BROADCAST_ID --dry-run
npx ts-node youtube-live.ts live-broadcast-delete \
  --broadcast-id BROADCAST_ID --yes
```

Editable broadcast settings include title, description, category, scheduled start/end,
privacy, auto-start/stop, DVR, embedding, recording, monitor stream, and delay. Creation
also supports made-for-kids and latency preference. Updating a broadcast preserves every
untouched mutable field in each submitted API part because `liveBroadcasts.update`
otherwise clears omitted fields. The update request is built from an explicit writable
allowlist rather than spreading a GET response; read-only binding/embed fields and
unsupported latency updates are never submitted. Closed captions use exactly one of the
legacy boolean or replacement type fields, never both.

The CLI refuses to transition to `testing` or `live` unless the broadcast is bound and the
stream reports `active`. Transitions to `live` or `complete` require `--yes`. Do not use a
transition merely to test the API without an active encoder.

By default, creation and binding reject an encoder stream already attached to another
`created`, `ready`, `testing`, or `live` broadcast. Although YouTube officially permits a
reusable stream to serve multiple broadcasts, dedicated named streams avoid Live Control
Room assignment conflicts and accidental `autoStart` routing. For a deliberate
single-encoder recurring workflow, opt in with `--allow-shared-stream`.

Before creation, the CLI reads the most recent completed broadcast and compares latency,
auto-start/stop, DVR, embedding, recording, monitor-stream, and delay settings with safe
defaults. Only nonstandard values are inherited, and explicit options win. The skill uses
`--inherit-previous` by default; the raw CLI stays offline unless that flag is supplied.

## Encoder streams

```bash
# List or inspect; stream keys are always redacted
npx ts-node youtube-live.ts live-streams-list --json
npx ts-node youtube-live.ts live-stream-show --stream-id STREAM_ID --json

# Create an RTMP/RTMPS-compatible reusable variable-resolution stream
npx ts-node youtube-live.ts live-stream-create \
  --title "Reusable encoder stream" \
  --ingestion-type rtmp \
  --resolution variable \
  --frame-rate variable \
  --reusable true \
  --dry-run

# Only title and description are mutable after stream creation
npx ts-node youtube-live.ts live-stream-update \
  --stream-id STREAM_ID --title "New internal title" --dry-run

# Reveal credentials only when the user explicitly asks
npx ts-node youtube-live.ts live-stream-key --stream-id STREAM_ID --yes

# Cleanup
npx ts-node youtube-live.ts live-stream-delete --stream-id STREAM_ID --dry-run
npx ts-node youtube-live.ts live-stream-delete --stream-id STREAM_ID --yes
```

Supported ingestion types are `rtmp` (including RTMPS addresses), `hls`, and `dash`.
Supported frame rates are `30fps`, `60fps`, and `variable`; supported resolutions are
`240p` through `2160p` plus `variable`. Variable resolution and frame rate must be paired.
YouTube does not allow changing CDN settings or reusability after stream creation.

`liveStreams.list --mine` does not return non-reusable streams, so retain the ID returned
by creation and use `live-stream-show --stream-id ID` for verification or cleanup.

## Verification

After a mutation, read the resource back with the corresponding `show` command. For a
scheduled event, verify at least its title, privacy, scheduled start, lifecycle status,
bound stream ID, and thumbnail state. YouTube Studio can be used as an independent UI
check when the user authorizes browser control.

### Automatic chat translation

YouTube does not expose automatic chat translation through the Live Streaming API or as
a channel-level default. It is a creator/moderator device preference. During every
browser verification, inspect the live-chat settings and turn **Automatic chat
translation** off when the control is present. YouTube may hide the control in an empty
scheduled chat; if so, report that it cannot be preconfigured and repeat the check after
the first message in a language different from the Studio display language. Never claim
the preference is disabled without observing the off state in the chat UI.

Official references:

- https://developers.google.com/youtube/v3/live/docs
- https://developers.google.com/youtube/v3/live/guides/implementation/broadcasts-and-streams
- https://developers.google.com/youtube/v3/live/life-of-a-broadcast
- https://developers.google.com/youtube/v3/determine_quota_cost
