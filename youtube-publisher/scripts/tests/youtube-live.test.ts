import assert from "node:assert/strict";
import test from "node:test";
import { parseLiveCommand } from "../youtube-live-cli";
import { findStreamBindingConflicts, inheritNonstandardBroadcastSettings, mergeLiveBroadcastUpdate, redactStreamKey, runBroadcastCommand } from "../youtube-live";
import { YouTubeLiveService } from "../youtube-live-service";

test("broadcast creation defaults to private and emits safe production defaults", () => {
  const future = new Date(Date.now() + 86_400_000).toISOString();
  const command = parseLiveCommand([
    "live-broadcast-create",
    "--title", "Test broadcast",
    "--scheduled-start", future,
    "--dry-run",
  ]);

  assert.equal(command.kind, "live-broadcast-create");
  if (command.kind !== "live-broadcast-create") return;
  assert.equal(command.privacyStatus, "private");
  assert.equal(command.enableDvr, true);
  assert.equal(command.recordFromStart, true);
  assert.equal(command.dryRun, true);
});

test("broadcast creation rejects an end before start", () => {
  const start = new Date(Date.now() + 86_400_000).toISOString();
  const end = new Date(Date.now() + 3_600_000).toISOString();
  assert.throws(
    () => parseLiveCommand([
      "live-broadcast-create",
      "--title", "Bad timing",
      "--scheduled-start", start,
      "--scheduled-end", end,
    ]),
    /later than/i,
  );
});

test("broadcast dates require an explicit timezone", () => {
  assert.throws(
    () => parseLiveCommand([
      "live-broadcast-create",
      "--title", "Ambiguous time",
      "--scheduled-start", "2030-01-01T10:00:00",
    ]),
    /explicit timezone/i,
  );
});

test("broadcast binding requires exactly one bind action", () => {
  assert.throws(
    () => parseLiveCommand(["live-broadcast-bind", "--broadcast-id", "abc"]),
    /exactly one/i,
  );
  assert.throws(
    () => parseLiveCommand(["live-broadcast-bind", "--broadcast-id", "abc", "--stream-id", "def", "--unbind"]),
    /exactly one/i,
  );
});

test("variable stream resolution and frame rate must be paired", () => {
  assert.throws(
    () => parseLiveCommand([
      "live-stream-create", "--title", "Stream", "--resolution", "variable", "--frame-rate", "30fps",
    ]),
    /used together/i,
  );
});

test("broadcast update preserves untouched fields in each overwritten part", () => {
  const current = {
    id: "broadcast-1",
    snippet: {
      title: "Old title",
      description: "Keep description",
      categoryId: "28",
      scheduledStartTime: "2030-01-01T10:00:00Z",
      scheduledEndTime: "2030-01-01T11:00:00Z",
    },
    status: { privacyStatus: "private" },
    contentDetails: {
      enableAutoStart: false,
      enableAutoStop: false,
      enableDvr: true,
      enableEmbed: true,
      recordFromStart: true,
      enableClosedCaptions: true,
      closedCaptionsType: "closedCaptionsHttpPost",
      availabilityConfig: { globalConfig: { excludedRegionCodes: ["AQ"] } },
      boundStreamId: "read-only-stream",
      boundStreamLastUpdateTimeMs: "2030-01-01T09:00:00Z",
      projection: "360",
      monitorStream: { enableMonitorStream: true, broadcastStreamDelayMs: 0, embedHtml: "read-only" },
    },
  };

  const update = mergeLiveBroadcastUpdate(current, { title: "New title", enableAutoStop: true });
  const updatedDetails = update.resource.contentDetails as typeof current.contentDetails;

  assert.deepEqual(update.parts, ["snippet", "contentDetails"]);
  assert.equal(update.resource.snippet?.description, "Keep description");
  assert.equal(update.resource.snippet?.scheduledStartTime, "2030-01-01T10:00:00Z");
  assert.equal(updatedDetails?.enableDvr, true);
  assert.equal(updatedDetails?.enableAutoStop, true);
  assert.equal(updatedDetails?.enableClosedCaptions, undefined);
  assert.equal(updatedDetails?.closedCaptionsType, "closedCaptionsHttpPost");
  assert.deepEqual(updatedDetails?.availabilityConfig?.globalConfig?.excludedRegionCodes, ["AQ"]);
  assert.equal(updatedDetails?.boundStreamId, undefined);
  assert.equal(updatedDetails?.projection, undefined);
  assert.equal(updatedDetails?.monitorStream?.embedHtml, undefined);
  assert.equal(update.resource.status, undefined);
});

test("broadcast update rejects unsupported latency mutation", () => {
  assert.throws(
    () => parseLiveCommand(["live-broadcast-update", "--broadcast-id", "abc", "--latency", "low"]),
    /unknown option/i,
  );
});

test("destructive commands parse confirmation separately from dry-run", () => {
  const preview = parseLiveCommand(["live-broadcast-delete", "--broadcast-id", "abc", "--dry-run"]);
  const confirmed = parseLiveCommand(["live-broadcast-delete", "--broadcast-id", "abc", "--yes"]);
  assert.equal(preview.kind, "live-broadcast-delete");
  assert.equal(preview.confirmed, false);
  assert.equal(preview.dryRun, true);
  assert.equal(confirmed.kind, "live-broadcast-delete");
  assert.equal(confirmed.confirmed, true);
});

test("ordinary stream output redacts the ingestion key without mutating the source", () => {
  const source = { id: "stream-1", cdn: { ingestionInfo: { streamName: "secret-key" } } };
  const redacted = redactStreamKey(source);
  assert.equal(redacted.cdn?.ingestionInfo?.streamName, "[redacted]");
  assert.equal(source.cdn.ingestionInfo.streamName, "secret-key");
});

test("stream binding conflicts include only other active or upcoming broadcasts", () => {
  const broadcasts = [
    { id: "current", status: { lifeCycleStatus: "ready" }, contentDetails: { boundStreamId: "stream-1" } },
    { id: "other", snippet: { title: "Other show" }, status: { lifeCycleStatus: "ready" }, contentDetails: { boundStreamId: "stream-1" } },
    { id: "done", status: { lifeCycleStatus: "complete" }, contentDetails: { boundStreamId: "stream-1" } },
    { id: "different", status: { lifeCycleStatus: "ready" }, contentDetails: { boundStreamId: "stream-2" } },
  ];
  assert.deepEqual(findStreamBindingConflicts(broadcasts, "stream-1", "current").map((item) => item.id), ["other"]);
});

test("previous broadcast inheritance applies only nonstandard non-explicit settings", () => {
  const previous = { contentDetails: { latencyPreference: "low", enableAutoStart: true, enableAutoStop: false, enableDvr: true, enableEmbed: true, recordFromStart: true, monitorStream: { enableMonitorStream: false, broadcastStreamDelayMs: 0 } } };
  const result = inheritNonstandardBroadcastSettings(previous, ["--auto-start"]);
  assert.deepEqual(result.settings, { latencyPreference: "low", enableMonitorStream: false });
  assert.deepEqual(result.applied, ["--latency", "--monitor-stream"]);
});

test("broadcast creation emits its ID before post-create setup failure", async () => {
  const future = new Date(Date.now() + 86_400_000).toISOString();
  const command = parseLiveCommand([
    "live-broadcast-create", "--title", "Recovery test", "--scheduled-start", future,
    "--stream-id", "stream-1",
  ]);
  if (command.kind !== "live-broadcast-create") throw new Error("unexpected command");
  const service = {
    listLiveBroadcasts: async () => [],
    createLiveBroadcast: async () => ({ id: "broadcast-123" }),
    bindLiveBroadcast: async () => { throw new Error("bind failed"); },
  } as unknown as YouTubeLiveService;
  const messages: string[] = [];
  const originalLog = console.log;
  console.log = (...args: unknown[]) => { messages.push(args.join(" ")); };
  try {
    await assert.rejects(
      () => runBroadcastCommand(command, async () => service),
      /Broadcast broadcast-123 was created.*bind failed/,
    );
  } finally {
    console.log = originalLog;
  }
  assert.ok(messages.includes("BROADCAST_CREATED: broadcast-123"));
});
