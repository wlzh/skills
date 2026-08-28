export type LivePrivacy = "public" | "unlisted" | "private";
export type BroadcastFilter = "all" | "active" | "completed" | "upcoming";
export type TransitionStatus = "testing" | "live" | "complete";
export type LatencyPreference = "normal" | "low" | "ultraLow";
export type IngestionType = "dash" | "hls" | "rtmp";
export type StreamResolution = "240p" | "360p" | "480p" | "720p" | "1080p" | "1440p" | "2160p" | "variable";
export type StreamFrameRate = "30fps" | "60fps" | "variable";

export interface BroadcastPatch {
  title?: string;
  description?: string;
  categoryId?: string;
  scheduledStartTime?: string;
  scheduledEndTime?: string;
  privacyStatus?: LivePrivacy;
  enableAutoStart?: boolean;
  enableAutoStop?: boolean;
  enableDvr?: boolean;
  enableEmbed?: boolean;
  recordFromStart?: boolean;
  enableMonitorStream?: boolean;
  broadcastStreamDelayMs?: number;
}
export type LiveCommand =
  | { kind: "live-broadcasts-list"; status: BroadcastFilter; json: boolean }
  | { kind: "live-broadcast-show"; broadcastId: string; json: boolean }
  | {
      kind: "live-broadcast-create";
      title: string;
      description: string;
      descriptionFile?: string;
      scheduledStartTime: string;
      scheduledEndTime?: string;
      privacyStatus: LivePrivacy;
      categoryId?: string;
      selfDeclaredMadeForKids: boolean;
      latencyPreference: LatencyPreference;
      enableAutoStart: boolean;
      enableAutoStop: boolean;
      enableDvr: boolean;
      enableEmbed: boolean;
      recordFromStart: boolean;
      enableMonitorStream: boolean;
      broadcastStreamDelayMs: number;
      streamId?: string;
      allowSharedStream: boolean;
      inheritPrevious: boolean;
      explicitOptions: string[];
      thumbnail?: string;
      dryRun: boolean;
    }
  | { kind: "live-broadcast-update"; broadcastId: string; patch: BroadcastPatch; descriptionFile?: string; dryRun: boolean }
  | { kind: "live-broadcast-bind"; broadcastId: string; streamId?: string; unbind: boolean; allowSharedStream: boolean; dryRun: boolean }
  | { kind: "live-broadcast-transition"; broadcastId: string; status: TransitionStatus; confirmed: boolean; dryRun: boolean }
  | { kind: "live-broadcast-delete"; broadcastId: string; confirmed: boolean; dryRun: boolean }
  | { kind: "live-streams-list"; json: boolean }
  | { kind: "live-stream-show"; streamId: string; json: boolean }
  | { kind: "live-stream-key"; streamId: string; confirmed: boolean }
  | {
      kind: "live-stream-create";
      title: string;
      description: string;
      descriptionFile?: string;
      ingestionType: IngestionType;
      resolution: StreamResolution;
      frameRate: StreamFrameRate;
      reusable: boolean;
      revealKey: boolean;
      confirmed: boolean;
      dryRun: boolean;
    }
  | { kind: "live-stream-update"; streamId: string; title?: string; description?: string; descriptionFile?: string; dryRun: boolean }
  | { kind: "live-stream-delete"; streamId: string; confirmed: boolean; dryRun: boolean };

const BOOLEAN_FLAGS = new Set(["--dry-run", "--json", "--yes", "--unbind", "--reveal-key", "--allow-shared-stream", "--inherit-previous"]);

class Flags {
  private readonly values = new Map<string, string | true>();

  constructor(args: string[]) {
    for (let index = 0; index < args.length; index += 1) {
      const name = args[index];
      if (!name.startsWith("--")) throw new Error(`Unexpected argument: ${name}`);
      if (this.values.has(name)) throw new Error(`Duplicate option: ${name}`);
      if (BOOLEAN_FLAGS.has(name)) {
        this.values.set(name, true);
        continue;
      }
      if (index + 1 >= args.length) throw new Error(`Missing value for ${name}`);
      this.values.set(name, args[++index]);
    }
  }

  has(name: string): boolean { return this.values.has(name); }

  optional(name: string): string | undefined {
    const value = this.values.get(name);
    if (value === true) throw new Error(`${name} requires a value`);
    return value;
  }

  required(name: string): string {
    const value = this.optional(name);
    if (!value) throw new Error(`${name} is required`);
    return value;
  }

  assertOnly(allowed: string[]): void {
    const accepted = new Set(allowed);
    for (const name of this.values.keys()) {
      if (!accepted.has(name)) throw new Error(`Unknown option for this command: ${name}`);
    }
  }
}

function choice<T extends string>(value: string | undefined, name: string, allowed: readonly T[], fallback?: T): T {
  if (value === undefined && fallback !== undefined) return fallback;
  if (value !== undefined && (allowed as readonly string[]).includes(value)) return value as T;
  throw new Error(`${name} must be one of: ${allowed.join(", ")}`);
}

function bool(value: string | undefined, name: string, fallback?: boolean): boolean {
  if (value === undefined && fallback !== undefined) return fallback;
  if (value === "true") return true;
  if (value === "false") return false;
  throw new Error(`${name} must be true or false`);
}

function integer(value: string | undefined, name: string, fallback?: number): number {
  if (value === undefined && fallback !== undefined) return fallback;
  const parsed = Number(value);
  if (!Number.isSafeInteger(parsed) || parsed < 0) throw new Error(`${name} must be a non-negative integer`);
  return parsed;
}

function isoDate(value: string, name: string): string {
  if (!/(?:Z|[+-]\d{2}:\d{2})$/i.test(value)) {
    throw new Error(`${name} must include an explicit timezone (Z or ±HH:MM)`);
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) throw new Error(`${name} must be an ISO 8601 date-time`);
  return parsed.toISOString();
}

function validateBroadcastTimes(start: string, end?: string): void {
  if (new Date(start).getTime() <= Date.now()) throw new Error("--scheduled-start must be in the future");
  if (end && new Date(end).getTime() <= new Date(start).getTime()) {
    throw new Error("--scheduled-end must be later than --scheduled-start");
  }
}

export function parseLiveCommand(args: string[]): LiveCommand {
  const kind = args[0] as LiveCommand["kind"];
  const flags = new Flags(args.slice(1));
  switch (kind) {
    case "live-broadcasts-list":
      flags.assertOnly(["--status", "--json"]);
      return { kind, status: choice(flags.optional("--status"), "--status", ["all", "active", "completed", "upcoming"], "upcoming"), json: flags.has("--json") };
    case "live-broadcast-show":
      flags.assertOnly(["--broadcast-id", "--json"]);
      return { kind, broadcastId: flags.required("--broadcast-id"), json: flags.has("--json") };
    case "live-broadcast-create": {
      flags.assertOnly([
        "--title", "--description", "--description-file", "--scheduled-start", "--scheduled-end",
        "--privacy", "--category", "--made-for-kids", "--latency", "--auto-start", "--auto-stop",
        "--dvr", "--embeddable", "--record-from-start", "--monitor-stream", "--delay-ms", "--stream-id",
        "--thumbnail", "--allow-shared-stream", "--inherit-previous", "--dry-run",
      ]);
      if (flags.has("--description") && flags.has("--description-file")) throw new Error("Use either --description or --description-file, not both");
      const scheduledStartTime = isoDate(flags.required("--scheduled-start"), "--scheduled-start");
      const scheduledEnd = flags.optional("--scheduled-end");
      const scheduledEndTime = scheduledEnd ? isoDate(scheduledEnd, "--scheduled-end") : undefined;
      validateBroadcastTimes(scheduledStartTime, scheduledEndTime);
      return {
        kind,
        title: flags.required("--title"),
        description: flags.optional("--description") ?? "",
        descriptionFile: flags.optional("--description-file"),
        scheduledStartTime,
        scheduledEndTime,
        privacyStatus: choice(flags.optional("--privacy"), "--privacy", ["public", "unlisted", "private"], "private"),
        categoryId: flags.optional("--category"),
        selfDeclaredMadeForKids: bool(flags.optional("--made-for-kids"), "--made-for-kids", false),
        latencyPreference: choice(flags.optional("--latency"), "--latency", ["normal", "low", "ultraLow"], "normal"),
        enableAutoStart: bool(flags.optional("--auto-start"), "--auto-start", false),
        enableAutoStop: bool(flags.optional("--auto-stop"), "--auto-stop", false),
        enableDvr: bool(flags.optional("--dvr"), "--dvr", true),
        enableEmbed: bool(flags.optional("--embeddable"), "--embeddable", true),
        recordFromStart: bool(flags.optional("--record-from-start"), "--record-from-start", true),
        enableMonitorStream: bool(flags.optional("--monitor-stream"), "--monitor-stream", true),
        broadcastStreamDelayMs: integer(flags.optional("--delay-ms"), "--delay-ms", 0),
        streamId: flags.optional("--stream-id"),
        allowSharedStream: flags.has("--allow-shared-stream"),
        inheritPrevious: flags.has("--inherit-previous"),
        explicitOptions: ["--latency", "--auto-start", "--auto-stop", "--dvr", "--embeddable", "--record-from-start", "--monitor-stream", "--delay-ms"].filter((name) => flags.has(name)),
        thumbnail: flags.optional("--thumbnail"),
        dryRun: flags.has("--dry-run"),
      };
    }
    case "live-broadcast-update": {
      flags.assertOnly([
        "--broadcast-id", "--title", "--description", "--description-file", "--category", "--scheduled-start",
        "--scheduled-end", "--privacy", "--auto-start", "--auto-stop", "--dvr", "--embeddable",
        "--record-from-start", "--monitor-stream", "--delay-ms", "--dry-run",
      ]);
      if (flags.has("--description") && flags.has("--description-file")) throw new Error("Use either --description or --description-file, not both");
      const patch: BroadcastPatch = {};
      if (flags.optional("--title") !== undefined) patch.title = flags.optional("--title");
      if (flags.optional("--description") !== undefined) patch.description = flags.optional("--description");
      if (flags.optional("--category") !== undefined) patch.categoryId = flags.optional("--category");
      if (flags.optional("--scheduled-start") !== undefined) patch.scheduledStartTime = isoDate(flags.required("--scheduled-start"), "--scheduled-start");
      if (flags.optional("--scheduled-end") !== undefined) patch.scheduledEndTime = isoDate(flags.required("--scheduled-end"), "--scheduled-end");
      if (flags.optional("--privacy") !== undefined) patch.privacyStatus = choice<LivePrivacy>(flags.optional("--privacy"), "--privacy", ["public", "unlisted", "private"]);
      const booleanFields: Array<[keyof BroadcastPatch, string]> = [
        ["enableAutoStart", "--auto-start"], ["enableAutoStop", "--auto-stop"], ["enableDvr", "--dvr"],
        ["enableEmbed", "--embeddable"], ["recordFromStart", "--record-from-start"], ["enableMonitorStream", "--monitor-stream"],
      ];
      for (const [property, option] of booleanFields) {
        const value = flags.optional(option);
        if (value !== undefined) (patch as Record<string, unknown>)[property] = bool(value, option);
      }
      if (flags.optional("--delay-ms") !== undefined) patch.broadcastStreamDelayMs = integer(flags.optional("--delay-ms"), "--delay-ms");
      const descriptionFile = flags.optional("--description-file");
      if (Object.keys(patch).length === 0 && !descriptionFile) throw new Error("Live broadcast update requires at least one editable field");
      return { kind, broadcastId: flags.required("--broadcast-id"), patch, descriptionFile, dryRun: flags.has("--dry-run") };
    }
    case "live-broadcast-bind":
      flags.assertOnly(["--broadcast-id", "--stream-id", "--unbind", "--allow-shared-stream", "--dry-run"]);
      if (flags.has("--unbind") === (flags.optional("--stream-id") !== undefined)) throw new Error("Specify exactly one of --stream-id or --unbind");
      return { kind, broadcastId: flags.required("--broadcast-id"), streamId: flags.optional("--stream-id"), unbind: flags.has("--unbind"), allowSharedStream: flags.has("--allow-shared-stream"), dryRun: flags.has("--dry-run") };
    case "live-broadcast-transition":
      flags.assertOnly(["--broadcast-id", "--status", "--yes", "--dry-run"]);
      return { kind, broadcastId: flags.required("--broadcast-id"), status: choice(flags.optional("--status"), "--status", ["testing", "live", "complete"]), confirmed: flags.has("--yes"), dryRun: flags.has("--dry-run") };
    case "live-broadcast-delete":
      flags.assertOnly(["--broadcast-id", "--yes", "--dry-run"]);
      return { kind, broadcastId: flags.required("--broadcast-id"), confirmed: flags.has("--yes"), dryRun: flags.has("--dry-run") };
    case "live-streams-list":
      flags.assertOnly(["--json"]);
      return { kind, json: flags.has("--json") };
    case "live-stream-show":
      flags.assertOnly(["--stream-id", "--json"]);
      return { kind, streamId: flags.required("--stream-id"), json: flags.has("--json") };
    case "live-stream-key":
      flags.assertOnly(["--stream-id", "--yes"]);
      return { kind, streamId: flags.required("--stream-id"), confirmed: flags.has("--yes") };
    case "live-stream-create": {
      flags.assertOnly(["--title", "--description", "--description-file", "--ingestion-type", "--resolution", "--frame-rate", "--reusable", "--reveal-key", "--yes", "--dry-run"]);
      if (flags.has("--description") && flags.has("--description-file")) throw new Error("Use either --description or --description-file, not both");
      const resolution = choice(flags.optional("--resolution"), "--resolution", ["240p", "360p", "480p", "720p", "1080p", "1440p", "2160p", "variable"], "variable");
      const frameRate = choice(flags.optional("--frame-rate"), "--frame-rate", ["30fps", "60fps", "variable"], "variable");
      if ((resolution === "variable") !== (frameRate === "variable")) throw new Error("Variable resolution and frame rate must be used together");
      return {
        kind,
        title: flags.required("--title"),
        description: flags.optional("--description") ?? "",
        descriptionFile: flags.optional("--description-file"),
        ingestionType: choice(flags.optional("--ingestion-type"), "--ingestion-type", ["dash", "hls", "rtmp"], "rtmp"),
        resolution,
        frameRate,
        reusable: bool(flags.optional("--reusable"), "--reusable", true),
        revealKey: flags.has("--reveal-key"),
        confirmed: flags.has("--yes"),
        dryRun: flags.has("--dry-run"),
      };
    }
    case "live-stream-update":
      flags.assertOnly(["--stream-id", "--title", "--description", "--description-file", "--dry-run"]);
      if (flags.has("--description") && flags.has("--description-file")) throw new Error("Use either --description or --description-file, not both");
      if (!flags.has("--title") && !flags.has("--description") && !flags.has("--description-file")) throw new Error("Live stream update requires --title or --description");
      return { kind, streamId: flags.required("--stream-id"), title: flags.optional("--title"), description: flags.optional("--description"), descriptionFile: flags.optional("--description-file"), dryRun: flags.has("--dry-run") };
    case "live-stream-delete":
      flags.assertOnly(["--stream-id", "--yes", "--dry-run"]);
      return { kind, streamId: flags.required("--stream-id"), confirmed: flags.has("--yes"), dryRun: flags.has("--dry-run") };
    default:
      throw new Error(`Unknown live command: ${kind}`);
  }
}
