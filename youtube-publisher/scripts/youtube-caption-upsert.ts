import * as fs from "fs";
import { youtube_v3 } from "googleapis";

export interface CaptionClient {
  captions: {
    list(params: object): Promise<{ data: { items?: youtube_v3.Schema$Caption[] | null } }>;
    insert(params: object): Promise<{ data: youtube_v3.Schema$Caption }>;
    update(params: object): Promise<{ data: youtube_v3.Schema$Caption }>;
  };
}

export async function upsertCaptionTrack(
  youtube: CaptionClient,
  options: { videoId: string; captionFile: string; language: string; name: string; mediaBody?: unknown },
): Promise<{ action: "inserted" | "updated"; captionId?: string | null }> {
  if (!fs.existsSync(options.captionFile) || !fs.statSync(options.captionFile).isFile()) {
    throw new Error(`Caption file not found: ${options.captionFile}`);
  }

  const existing = await youtube.captions.list({ part: ["snippet"], videoId: options.videoId });
  const matches = (existing.data.items ?? []).filter((caption) =>
    caption.id
    && caption.snippet?.language === options.language
    && (caption.snippet?.name ?? "") === options.name);
  if (matches.length > 1) {
    throw new Error(`Multiple matching caption tracks found for ${options.language}/${options.name}; refusing destructive cleanup`);
  }

  const snippet = {
    videoId: options.videoId,
    language: options.language,
    name: options.name,
    isDraft: false,
  };
  const media = { body: options.mediaBody ?? fs.createReadStream(options.captionFile) };
  if (matches.length === 1) {
    const captionId = matches[0].id!;
    const result = await youtube.captions.update({
      part: ["snippet"],
      requestBody: { id: captionId, snippet },
      media,
    });
    return { action: "updated", captionId: result.data.id ?? captionId };
  }

  const result = await youtube.captions.insert({
    part: ["snippet"],
    requestBody: { snippet },
    media,
  });
  return { action: "inserted", captionId: result.data.id };
}
