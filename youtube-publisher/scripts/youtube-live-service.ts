import * as fs from "fs";
import * as path from "path";
import { youtube_v3 } from "googleapis";
import { authenticate } from "./authenticate";

const MAX_THUMBNAIL_BYTES = 2 * 1024 * 1024;

export function validateThumbnail(filePath: string): string {
  const resolved = path.resolve(filePath);
  if (!fs.existsSync(resolved) || !fs.statSync(resolved).isFile()) throw new Error(`Thumbnail file not found: ${resolved}`);
  if (![".jpg", ".jpeg", ".png"].includes(path.extname(resolved).toLowerCase())) throw new Error("Thumbnail must be JPEG or PNG");
  if (fs.statSync(resolved).size > MAX_THUMBNAIL_BYTES) throw new Error("Thumbnail exceeds YouTube's 2 MB limit");
  return resolved;
}

export class YouTubeLiveService {
  private constructor(private readonly youtube: youtube_v3.Youtube) {}

  static async create(): Promise<YouTubeLiveService> {
    const { youtube } = await authenticate(false);
    return new YouTubeLiveService(youtube);
  }

  static fromClient(youtube: youtube_v3.Youtube): YouTubeLiveService {
    return new YouTubeLiveService(youtube);
  }

  async setThumbnail(videoId: string, filePath: string): Promise<void> {
    const thumbnail = validateThumbnail(filePath);
    await this.youtube.thumbnails.set({ videoId, media: { body: fs.createReadStream(thumbnail) } });
  }

  async listLiveBroadcasts(status: "all" | "active" | "completed" | "upcoming"): Promise<youtube_v3.Schema$LiveBroadcast[]> {
    const items: youtube_v3.Schema$LiveBroadcast[] = [];
    let pageToken: string | undefined;
    do {
      const response = await this.youtube.liveBroadcasts.list({ part: ["id", "snippet", "status", "contentDetails"], mine: true, maxResults: 50, pageToken });
      items.push(...(response.data.items ?? []));
      pageToken = response.data.nextPageToken ?? undefined;
    } while (pageToken);
    if (status === "all") return items;
    const accepted = status === "active" ? new Set(["testing", "live"]) : status === "completed" ? new Set(["complete"]) : new Set(["created", "ready"]);
    return items.filter((item) => accepted.has(item.status?.lifeCycleStatus ?? ""));
  }

  async getLiveBroadcast(id: string): Promise<youtube_v3.Schema$LiveBroadcast> {
    const response = await this.youtube.liveBroadcasts.list({ part: ["id", "snippet", "status", "contentDetails"], id: [id] });
    const item = response.data.items?.[0];
    if (!item) throw new Error(`Live broadcast not found or not accessible: ${id}`);
    return item;
  }

  async createLiveBroadcast(resource: youtube_v3.Schema$LiveBroadcast): Promise<youtube_v3.Schema$LiveBroadcast> {
    return (await this.youtube.liveBroadcasts.insert({ part: ["snippet", "status", "contentDetails"], requestBody: resource })).data;
  }

  async updateLiveBroadcast(parts: string[], resource: youtube_v3.Schema$LiveBroadcast): Promise<youtube_v3.Schema$LiveBroadcast> {
    return (await this.youtube.liveBroadcasts.update({ part: parts, requestBody: resource })).data;
  }

  async bindLiveBroadcast(id: string, streamId?: string): Promise<youtube_v3.Schema$LiveBroadcast> {
    return (await this.youtube.liveBroadcasts.bind({ id, part: ["id", "snippet", "status", "contentDetails"], streamId })).data;
  }

  async transitionLiveBroadcast(id: string, status: "testing" | "live" | "complete"): Promise<youtube_v3.Schema$LiveBroadcast> {
    const broadcast = await this.getLiveBroadcast(id);
    const streamId = broadcast.contentDetails?.boundStreamId;
    if ((status === "testing" || status === "live") && !streamId) throw new Error(`Broadcast ${id} is not bound to a stream`);
    if ((status === "testing" || status === "live") && streamId) {
      const stream = await this.getLiveStream(streamId);
      if (stream.status?.streamStatus !== "active") throw new Error(`Bound stream is not active (current status: ${stream.status?.streamStatus ?? "unknown"})`);
    }
    return (await this.youtube.liveBroadcasts.transition({ id, broadcastStatus: status, part: ["id", "snippet", "status", "contentDetails"] })).data;
  }

  async deleteLiveBroadcast(id: string): Promise<void> { await this.youtube.liveBroadcasts.delete({ id }); }

  async listLiveStreams(): Promise<youtube_v3.Schema$LiveStream[]> {
    const items: youtube_v3.Schema$LiveStream[] = [];
    let pageToken: string | undefined;
    do {
      const response = await this.youtube.liveStreams.list({ part: ["id", "snippet", "cdn", "status", "contentDetails"], mine: true, maxResults: 50, pageToken });
      items.push(...(response.data.items ?? []));
      pageToken = response.data.nextPageToken ?? undefined;
    } while (pageToken);
    return items;
  }

  async getLiveStream(id: string): Promise<youtube_v3.Schema$LiveStream> {
    const response = await this.youtube.liveStreams.list({ part: ["id", "snippet", "cdn", "status", "contentDetails"], id: [id] });
    const item = response.data.items?.[0];
    if (!item) throw new Error(`Live stream not found or not accessible: ${id}`);
    return item;
  }

  async createLiveStream(resource: youtube_v3.Schema$LiveStream): Promise<youtube_v3.Schema$LiveStream> {
    return (await this.youtube.liveStreams.insert({ part: ["snippet", "cdn", "contentDetails"], requestBody: resource })).data;
  }

  async updateLiveStream(resource: youtube_v3.Schema$LiveStream): Promise<youtube_v3.Schema$LiveStream> {
    return (await this.youtube.liveStreams.update({ part: ["snippet", "cdn"], requestBody: resource })).data;
  }

  async deleteLiveStream(id: string): Promise<void> { await this.youtube.liveStreams.delete({ id }); }
}
