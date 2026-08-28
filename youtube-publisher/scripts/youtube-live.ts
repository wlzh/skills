import * as fs from "node:fs";
import * as path from "node:path";
import { youtube_v3 } from "googleapis";
import { BroadcastPatch, LatencyPreference, LiveCommand, parseLiveCommand } from "./youtube-live-cli";
import { YouTubeLiveService, validateThumbnail } from "./youtube-live-service";

type LiveBroadcastSnippetWithCategory = youtube_v3.Schema$LiveBroadcastSnippet & { categoryId?: string | null };
type LiveBroadcastContentDetailsWithAvailability = youtube_v3.Schema$LiveBroadcastContentDetails & {
  availabilityConfig?: unknown;
};

function printJson(value: unknown): void { console.log(JSON.stringify(value, null, 2)); }

function requireFile(filePath: string, label: string): string {
  const resolved = path.resolve(filePath);
  if (!fs.existsSync(resolved) || !fs.statSync(resolved).isFile()) throw new Error(`${label} file not found: ${resolved}`);
  return resolved;
}

function readDescription(inline: string | undefined, filePath: string | undefined, limit: number): string {
  const description = filePath ? fs.readFileSync(requireFile(filePath, "Description"), "utf8") : (inline ?? "");
  if (description.length > limit) throw new Error(`Description exceeds ${limit} characters`);
  return description;
}

function validateBroadcastText(title: string, description: string): void {
  if (title.length < 1 || title.length > 100) throw new Error("Live broadcast title must contain 1-100 characters");
  if (description.length > 5000) throw new Error("Live broadcast description exceeds 5000 characters");
}

function validateStreamText(title: string, description: string): void {
  if (title.length < 1 || title.length > 128) throw new Error("Live stream title must contain 1-128 characters");
  if (description.length > 10000) throw new Error("Live stream description exceeds 10000 characters");
}

export function redactStreamKey(stream: youtube_v3.Schema$LiveStream): youtube_v3.Schema$LiveStream {
  const clone = JSON.parse(JSON.stringify(stream)) as youtube_v3.Schema$LiveStream;
  if (clone.cdn?.ingestionInfo?.streamName) clone.cdn.ingestionInfo.streamName = "[redacted]";
  return clone;
}

function summarizeBroadcast(item: youtube_v3.Schema$LiveBroadcast): object {
  return {
    id: item.id,
    title: item.snippet?.title,
    scheduledStartTime: item.snippet?.scheduledStartTime,
    lifeCycleStatus: item.status?.lifeCycleStatus,
    privacyStatus: item.status?.privacyStatus,
    boundStreamId: item.contentDetails?.boundStreamId,
    url: item.id ? `https://youtu.be/${item.id}` : undefined,
  };
}

function summarizeStream(item: youtube_v3.Schema$LiveStream): object {
  return {
    id: item.id,
    title: item.snippet?.title,
    streamStatus: item.status?.streamStatus,
    healthStatus: item.status?.healthStatus?.status,
    ingestionType: item.cdn?.ingestionType,
    resolution: item.cdn?.resolution,
    frameRate: item.cdn?.frameRate,
    reusable: item.contentDetails?.isReusable,
  };
}

export function findStreamBindingConflicts(
  broadcasts: youtube_v3.Schema$LiveBroadcast[], streamId: string, excludeBroadcastId?: string,
): youtube_v3.Schema$LiveBroadcast[] {
  const relevantStates = new Set(["created", "ready", "testing", "live"]);
  return broadcasts.filter((broadcast) => broadcast.id !== excludeBroadcastId
    && broadcast.contentDetails?.boundStreamId === streamId
    && relevantStates.has(broadcast.status?.lifeCycleStatus ?? ""));
}

async function assertStreamBindingAvailable(
  service: YouTubeLiveService, streamId: string, excludeBroadcastId: string | undefined, allowSharedStream: boolean,
): Promise<void> {
  if (allowSharedStream) return;
  const conflicts = findStreamBindingConflicts(await service.listLiveBroadcasts("all"), streamId, excludeBroadcastId);
  if (conflicts.length === 0) return;
  const details = conflicts.map((item) => `${item.id} (${item.snippet?.title ?? "untitled"})`).join(", ");
  throw new Error(`Stream ${streamId} is already assigned to active/upcoming broadcast(s): ${details}. `
    + "Use a dedicated stream, or pass --allow-shared-stream for a deliberate single-encoder workflow.");
}

type InheritableBroadcastSettings = {
  latencyPreference?: LatencyPreference;
  enableAutoStart?: boolean;
  enableAutoStop?: boolean;
  enableDvr?: boolean;
  enableEmbed?: boolean;
  recordFromStart?: boolean;
  enableMonitorStream?: boolean;
  broadcastStreamDelayMs?: number;
};
const SAFE_BROADCAST_DEFAULTS: Required<InheritableBroadcastSettings> = { latencyPreference: "normal", enableAutoStart: false, enableAutoStop: false, enableDvr: true, enableEmbed: true, recordFromStart: true, enableMonitorStream: true, broadcastStreamDelayMs: 0 };

export function inheritNonstandardBroadcastSettings(previous: youtube_v3.Schema$LiveBroadcast | undefined, explicitOptions: string[]): { settings: InheritableBroadcastSettings; applied: string[] } {
  if (!previous) return { settings: {}, applied: [] };
  const candidates: Array<[keyof InheritableBroadcastSettings, string, unknown]> = [
    ["latencyPreference", "--latency", previous.contentDetails?.latencyPreference], ["enableAutoStart", "--auto-start", previous.contentDetails?.enableAutoStart],
    ["enableAutoStop", "--auto-stop", previous.contentDetails?.enableAutoStop], ["enableDvr", "--dvr", previous.contentDetails?.enableDvr],
    ["enableEmbed", "--embeddable", previous.contentDetails?.enableEmbed], ["recordFromStart", "--record-from-start", previous.contentDetails?.recordFromStart],
    ["enableMonitorStream", "--monitor-stream", previous.contentDetails?.monitorStream?.enableMonitorStream], ["broadcastStreamDelayMs", "--delay-ms", previous.contentDetails?.monitorStream?.broadcastStreamDelayMs],
  ];
  const settings: InheritableBroadcastSettings = {}; const applied: string[] = [];
  for (const [property, option, value] of candidates) {
    if (value === undefined || explicitOptions.includes(option) || value === SAFE_BROADCAST_DEFAULTS[property]) continue;
    (settings as Record<string, unknown>)[property] = value; applied.push(option);
  }
  return { settings, applied };
}

function mostRecentCompletedBroadcast(items: youtube_v3.Schema$LiveBroadcast[]): youtube_v3.Schema$LiveBroadcast | undefined {
  const stamp = (item: youtube_v3.Schema$LiveBroadcast) => Date.parse(item.snippet?.actualEndTime ?? item.snippet?.scheduledStartTime ?? item.snippet?.publishedAt ?? "") || 0;
  return [...items].sort((left, right) => stamp(right) - stamp(left))[0];
}

function broadcastCreateResource(command: Extract<LiveCommand, { kind: "live-broadcast-create" }>, description: string, inherited: InheritableBroadcastSettings = {}): youtube_v3.Schema$LiveBroadcast {
  validateBroadcastText(command.title, description);
  return {
    snippet: {
      title: command.title,
      description,
      scheduledStartTime: command.scheduledStartTime,
      scheduledEndTime: command.scheduledEndTime,
      categoryId: command.categoryId,
    } as LiveBroadcastSnippetWithCategory,
    status: {
      privacyStatus: command.privacyStatus,
      selfDeclaredMadeForKids: command.selfDeclaredMadeForKids,
    },
    contentDetails: {
      latencyPreference: inherited.latencyPreference ?? command.latencyPreference,
      enableAutoStart: inherited.enableAutoStart ?? command.enableAutoStart,
      enableAutoStop: inherited.enableAutoStop ?? command.enableAutoStop,
      enableDvr: inherited.enableDvr ?? command.enableDvr,
      enableEmbed: inherited.enableEmbed ?? command.enableEmbed,
      recordFromStart: inherited.recordFromStart ?? command.recordFromStart,
      monitorStream: {
        enableMonitorStream: inherited.enableMonitorStream ?? command.enableMonitorStream,
        broadcastStreamDelayMs: inherited.broadcastStreamDelayMs ?? command.broadcastStreamDelayMs,
      },
    },
  };
}

export function mergeLiveBroadcastUpdate(current: youtube_v3.Schema$LiveBroadcast, patch: BroadcastPatch): { parts: string[]; resource: youtube_v3.Schema$LiveBroadcast } {
  if (!current.id) throw new Error("Current live broadcast has no ID");
  const resource: youtube_v3.Schema$LiveBroadcast = { id: current.id };
  const parts: string[] = [];
  const snippetKeys: Array<keyof BroadcastPatch> = ["title", "description", "categoryId", "scheduledStartTime", "scheduledEndTime"];
  if (snippetKeys.some((key) => Object.prototype.hasOwnProperty.call(patch, key))) {
    const currentSnippet = current.snippet as LiveBroadcastSnippetWithCategory | null | undefined;
    const snippet = {
      title: patch.title ?? current.snippet?.title,
      description: Object.prototype.hasOwnProperty.call(patch, "description") ? patch.description : current.snippet?.description,
      categoryId: patch.categoryId ?? currentSnippet?.categoryId,
      scheduledStartTime: patch.scheduledStartTime ?? current.snippet?.scheduledStartTime,
      scheduledEndTime: patch.scheduledEndTime ?? current.snippet?.scheduledEndTime,
    };
    if (!snippet.title || !snippet.scheduledStartTime) throw new Error("Existing broadcast is missing required title or scheduled start time");
    validateBroadcastText(snippet.title, snippet.description ?? "");
    if (snippet.scheduledEndTime && new Date(snippet.scheduledEndTime).getTime() <= new Date(snippet.scheduledStartTime).getTime()) {
      throw new Error("Scheduled end time must be later than scheduled start time");
    }
    resource.snippet = snippet as LiveBroadcastSnippetWithCategory;
    parts.push("snippet");
  }
  if (Object.prototype.hasOwnProperty.call(patch, "privacyStatus")) {
    resource.status = { privacyStatus: patch.privacyStatus ?? current.status?.privacyStatus };
    parts.push("status");
  }
  const contentKeys: Array<keyof BroadcastPatch> = [
    "enableAutoStart", "enableAutoStop", "enableDvr", "enableEmbed", "recordFromStart", "enableMonitorStream", "broadcastStreamDelayMs",
  ];
  if (contentKeys.some((key) => Object.prototype.hasOwnProperty.call(patch, key))) {
    const currentDetails = current.contentDetails as LiveBroadcastContentDetailsWithAvailability | null | undefined;
    const captionDetails = currentDetails?.closedCaptionsType
      ? { closedCaptionsType: currentDetails.closedCaptionsType }
      : { enableClosedCaptions: currentDetails?.enableClosedCaptions };
    const contentDetails: LiveBroadcastContentDetailsWithAvailability = {
      enableAutoStart: patch.enableAutoStart ?? current.contentDetails?.enableAutoStart,
      enableAutoStop: patch.enableAutoStop ?? current.contentDetails?.enableAutoStop,
      enableDvr: patch.enableDvr ?? current.contentDetails?.enableDvr,
      enableEmbed: patch.enableEmbed ?? current.contentDetails?.enableEmbed,
      recordFromStart: patch.recordFromStart ?? current.contentDetails?.recordFromStart,
      availabilityConfig: currentDetails?.availabilityConfig,
      ...captionDetails,
      monitorStream: {
        enableMonitorStream: patch.enableMonitorStream ?? current.contentDetails?.monitorStream?.enableMonitorStream ?? true,
        broadcastStreamDelayMs: patch.broadcastStreamDelayMs ?? current.contentDetails?.monitorStream?.broadcastStreamDelayMs ?? 0,
      },
    };
    resource.contentDetails = contentDetails;
    parts.push("contentDetails");
  }
  if (parts.length === 0) throw new Error("Live broadcast update requires at least one editable field");
  return { parts, resource };
}

async function createService(): Promise<YouTubeLiveService> { return YouTubeLiveService.create(); }
export type LiveServiceFactory = () => Promise<YouTubeLiveService>;

export async function runBroadcastCommand(
  command: Extract<LiveCommand, { kind: `live-broadcast${string}` }>,
  serviceFactory: LiveServiceFactory = createService,
): Promise<void> {
  if (command.kind === "live-broadcasts-list") {
    const broadcasts = await (await serviceFactory()).listLiveBroadcasts(command.status);
    if (command.json) printJson(broadcasts);
    else console.table(broadcasts.map(summarizeBroadcast));
    return;
  }
  if (command.kind === "live-broadcast-show") {
    printJson(await (await serviceFactory()).getLiveBroadcast(command.broadcastId));
    return;
  }
  if (command.kind === "live-broadcast-create") {
    const description = readDescription(command.description, command.descriptionFile, 5000);
    const thumbnail = command.thumbnail ? validateThumbnail(command.thumbnail) : undefined;
    const service = command.inheritPrevious || !command.dryRun ? await serviceFactory() : undefined;
    const previous = command.inheritPrevious && service ? mostRecentCompletedBroadcast(await service.listLiveBroadcasts("completed")) : undefined;
    const inheritance = inheritNonstandardBroadcastSettings(previous, command.explicitOptions);
    const resource = broadcastCreateResource(command, description, inheritance.settings);
    if (command.dryRun) {
      printJson({ dryRun: true, operation: command.kind, resource, streamId: command.streamId, thumbnail, inheritedFromBroadcastId: previous?.id, inheritedOptions: inheritance.applied });
      return;
    }
    if (!service) throw new Error("YouTube service was not initialized");
    if (command.streamId) await assertStreamBindingAvailable(service, command.streamId, undefined, command.allowSharedStream);
    const created = await service.createLiveBroadcast(resource);
    if (!created.id) throw new Error("YouTube created a broadcast without returning an ID");
    console.log(`BROADCAST_CREATED: ${created.id}`);
    try {
      if (command.streamId) await service.bindLiveBroadcast(created.id, command.streamId);
      if (thumbnail) await service.setThumbnail(created.id, thumbnail);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      throw new Error(`Broadcast ${created.id} was created, but post-create setup failed: ${message}`);
    }
    printJson({ broadcast: summarizeBroadcast(await service.getLiveBroadcast(created.id)), thumbnailSet: Boolean(thumbnail) });
    return;
  }
  if (command.kind === "live-broadcast-update") {
    const patch = { ...command.patch };
    if (command.descriptionFile) patch.description = readDescription(undefined, command.descriptionFile, 5000);
    const service = await serviceFactory();
    const update = mergeLiveBroadcastUpdate(await service.getLiveBroadcast(command.broadcastId), patch);
    if (command.dryRun) {
      printJson({ dryRun: true, operation: command.kind, ...update });
      return;
    }
    printJson(await service.updateLiveBroadcast(update.parts, update.resource));
    return;
  }
  if (command.kind === "live-broadcast-bind") {
    const service = await serviceFactory();
    if (!command.unbind && command.streamId) {
      await assertStreamBindingAvailable(service, command.streamId, command.broadcastId, command.allowSharedStream);
    }
    if (command.dryRun) {
      printJson({ dryRun: true, operation: command.kind, broadcastId: command.broadcastId, streamId: command.unbind ? null : command.streamId });
      return;
    }
    printJson(await service.bindLiveBroadcast(command.broadcastId, command.unbind ? undefined : command.streamId));
    return;
  }
  if (command.kind === "live-broadcast-transition") {
    if ((command.status === "live" || command.status === "complete") && !command.confirmed && !command.dryRun) {
      throw new Error(`Transition to ${command.status} requires --yes`);
    }
    if (command.dryRun) {
      printJson({ dryRun: true, operation: command.kind, broadcastId: command.broadcastId, status: command.status });
      return;
    }
    printJson(await (await serviceFactory()).transitionLiveBroadcast(command.broadcastId, command.status));
    return;
  }
  if (!command.confirmed && !command.dryRun) throw new Error("Live broadcast deletion requires --yes");
  if (command.dryRun) {
    printJson({ dryRun: true, operation: command.kind, broadcastId: command.broadcastId });
    return;
  }
  await (await serviceFactory()).deleteLiveBroadcast(command.broadcastId);
  console.log(`Live broadcast deleted: ${command.broadcastId}`);
}

async function runStreamCommand(command: Extract<LiveCommand, { kind: `live-stream${string}` }>): Promise<void> {
  if (command.kind === "live-streams-list") {
    const streams = await (await createService()).listLiveStreams();
    if (command.json) printJson(streams.map(redactStreamKey));
    else console.table(streams.map(summarizeStream));
    return;
  }
  if (command.kind === "live-stream-show") {
    printJson(redactStreamKey(await (await createService()).getLiveStream(command.streamId)));
    return;
  }
  if (command.kind === "live-stream-key") {
    if (!command.confirmed) throw new Error("Printing a live stream key requires --yes");
    const stream = await (await createService()).getLiveStream(command.streamId);
    printJson({
      streamId: stream.id,
      streamName: stream.cdn?.ingestionInfo?.streamName,
      ingestionAddress: stream.cdn?.ingestionInfo?.ingestionAddress,
      rtmpsIngestionAddress: stream.cdn?.ingestionInfo?.rtmpsIngestionAddress,
      backupIngestionAddress: stream.cdn?.ingestionInfo?.backupIngestionAddress,
      rtmpsBackupIngestionAddress: stream.cdn?.ingestionInfo?.rtmpsBackupIngestionAddress,
    });
    return;
  }
  if (command.kind === "live-stream-create") {
    const description = readDescription(command.description, command.descriptionFile, 10000);
    validateStreamText(command.title, description);
    if (command.revealKey && !command.confirmed && !command.dryRun) throw new Error("--reveal-key requires --yes");
    const resource: youtube_v3.Schema$LiveStream = {
      snippet: { title: command.title, description },
      cdn: { ingestionType: command.ingestionType, resolution: command.resolution, frameRate: command.frameRate },
      contentDetails: { isReusable: command.reusable },
    };
    if (command.dryRun) {
      printJson({ dryRun: true, operation: command.kind, resource, revealKey: command.revealKey });
      return;
    }
    const created = await (await createService()).createLiveStream(resource);
    printJson(command.revealKey ? created : redactStreamKey(created));
    return;
  }
  if (command.kind === "live-stream-update") {
    const service = await createService();
    const current = await service.getLiveStream(command.streamId);
    const description = command.descriptionFile
      ? readDescription(undefined, command.descriptionFile, 10000)
      : (command.description ?? current.snippet?.description ?? "");
    const title = command.title ?? current.snippet?.title ?? "";
    validateStreamText(title, description);
    const resource: youtube_v3.Schema$LiveStream = {
      id: command.streamId,
      snippet: { title, description },
      cdn: {
        ingestionType: current.cdn?.ingestionType,
        resolution: current.cdn?.resolution,
        frameRate: current.cdn?.frameRate,
      },
    };
    if (command.dryRun) {
      printJson({ dryRun: true, operation: command.kind, resource });
      return;
    }
    printJson(redactStreamKey(await service.updateLiveStream(resource)));
    return;
  }
  if (!command.confirmed && !command.dryRun) throw new Error("Live stream deletion requires --yes");
  if (command.dryRun) {
    printJson({ dryRun: true, operation: command.kind, streamId: command.streamId });
    return;
  }
  await (await createService()).deleteLiveStream(command.streamId);
  console.log(`Live stream deleted: ${command.streamId}`);
}

export async function runLiveCommand(args: string[]): Promise<void> {
  const command = parseLiveCommand(args);
  if (command.kind.startsWith("live-broadcast")) {
    await runBroadcastCommand(command as Extract<LiveCommand, { kind: `live-broadcast${string}` }>);
    return;
  }
  await runStreamCommand(command as Extract<LiveCommand, { kind: `live-stream${string}` }>);
}

if (require.main === module) {
  runLiveCommand(process.argv.slice(2)).catch((error) => {
    console.error(`Error: ${error instanceof Error ? error.message : String(error)}`);
    process.exitCode = 1;
  });
}
