import { youtube_v3 } from "googleapis";

export class PersistentP0DError extends Error {
  readonly exitCode = 42;

  constructor(readonly videoId: string) {
    super(`PERSISTENT_P0D_VIDEO_ID: ${videoId}`);
  }
}

export class AmbiguousUploadError extends Error {
  readonly exitCode = 43;

  constructor(readonly videoId: string | undefined, reason: string) {
    super(`AMBIGUOUS_UPLOAD_VIDEO_ID: ${videoId ?? "unknown"}; ${reason}`);
  }
}

export interface UploadRecoveryClient {
  search: {
    list(params: object): Promise<{ data: { items?: youtube_v3.Schema$SearchResult[] | null } }>;
  };
  videos: {
    list(params: object): Promise<{ data: { items?: youtube_v3.Schema$Video[] | null } }>;
  };
}

type Sleep = (milliseconds: number) => Promise<void>;

function validDuration(duration: string | null | undefined): boolean {
  return Boolean(duration && duration !== "P0D" && duration !== "PT0S");
}

function recentTimestamp(value: string | null | undefined, now: number): boolean {
  if (!value) return false;
  const timestamp = Date.parse(value);
  if (!Number.isFinite(timestamp)) return false;
  const age = now - timestamp;
  return age >= -5 * 60_000 && age <= 6 * 60 * 60_000;
}

export async function recoverAmbiguousUpload(
  youtube: UploadRecoveryClient,
  title: string,
  options: { rechecks?: number; sleep?: Sleep; now?: number } = {},
): Promise<youtube_v3.Schema$Video> {
  const rechecks = options.rechecks ?? 2;
  const sleep = options.sleep ?? ((milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds)));
  const now = options.now ?? Date.now();

  try {
    const search = await youtube.search.list({
      part: ["snippet"],
      forMine: true,
      maxResults: 5,
      order: "date",
      type: ["video"],
      q: title,
    });
    const candidates = (search.data.items ?? []).filter((item) =>
      item.id?.videoId
      && item.snippet?.title === title
      && recentTimestamp(item.snippet?.publishedAt, now));

    if (candidates.length !== 1) {
      const ids = candidates.map((item) => item.id?.videoId).filter(Boolean).join(",");
      throw new AmbiguousUploadError(ids || undefined, `expected one recent exact-title candidate, found ${candidates.length}`);
    }

    const videoId = candidates[0].id?.videoId;
    if (!videoId) throw new AmbiguousUploadError(undefined, "candidate did not contain a video ID");

    const fetchVideo = async (): Promise<youtube_v3.Schema$Video> => {
      const response = await youtube.videos.list({
        part: ["snippet", "status", "contentDetails"],
        id: [videoId],
      });
      const video = response.data.items?.[0];
      if (!video) throw new AmbiguousUploadError(videoId, "video metadata lookup returned no item");
      if (!video.contentDetails?.duration) {
        throw new AmbiguousUploadError(videoId, "video duration is unavailable");
      }
      return video;
    };

    let video = await fetchVideo();
    if (validDuration(video.contentDetails?.duration)) return video;
    if (video.contentDetails?.duration !== "P0D") {
      throw new AmbiguousUploadError(videoId, `video duration is not publishable: ${video.contentDetails?.duration}`);
    }

    for (let attempt = 1; attempt <= rechecks; attempt += 1) {
      await sleep(attempt * 2000);
      video = await fetchVideo();
      if (validDuration(video.contentDetails?.duration)) return video;
      if (video.contentDetails?.duration !== "P0D") {
        throw new AmbiguousUploadError(videoId, `video duration is not publishable: ${video.contentDetails?.duration}`);
      }
    }
    throw new PersistentP0DError(videoId);
  } catch (error) {
    if (error instanceof PersistentP0DError || error instanceof AmbiguousUploadError) throw error;
    const message = error instanceof Error ? error.message : String(error);
    throw new AmbiguousUploadError(undefined, `server-side recovery check failed: ${message}`);
  }
}
