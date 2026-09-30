import * as fs from "fs";
import * as path from "path";
import { authenticate } from "./authenticate";

function readOutputPath(): string {
  const index = process.argv.indexOf("--output");
  if (index === -1 || !process.argv[index + 1]) {
    throw new Error("Usage: npx ts-node export-playlists.ts --output <path>");
  }
  return path.resolve(process.argv[index + 1]);
}

async function main(): Promise<void> {
  const outputPath = readOutputPath();
  const { youtube } = await authenticate(false);
  const channelResponse = await youtube.channels.list({
    part: ["snippet", "contentDetails"],
    mine: true,
  });
  const channel = channelResponse.data.items?.[0];
  if (!channel?.id) throw new Error("Authenticated YouTube channel was not found");

  const playlists: any[] = [];
  let playlistPageToken: string | undefined;
  do {
    const response = await youtube.playlists.list({
      part: ["snippet", "contentDetails", "status"],
      mine: true,
      maxResults: 50,
      pageToken: playlistPageToken,
    });
    for (const playlist of response.data.items || []) {
      if (!playlist.id || playlist.status?.privacyStatus !== "public") continue;
      const videos: any[] = [];
      let itemPageToken: string | undefined;
      do {
        const items = await youtube.playlistItems.list({
          part: ["snippet", "contentDetails", "status"],
          playlistId: playlist.id,
          maxResults: 50,
          pageToken: itemPageToken,
        });
        for (const item of items.data.items || []) {
          const videoId = item.contentDetails?.videoId || item.snippet?.resourceId?.videoId;
          const title = item.snippet?.title || "";
          if (!videoId || item.status?.privacyStatus !== "public" || title === "Deleted video" || title === "Private video") continue;
          videos.push({
            videoId,
            title,
            position: item.snippet?.position ?? videos.length,
            privacyStatus: item.status?.privacyStatus || "unknown",
            publishedAt: item.contentDetails?.videoPublishedAt || null,
            thumbnailUrl:
              item.snippet?.thumbnails?.maxres?.url ||
              item.snippet?.thumbnails?.high?.url ||
              item.snippet?.thumbnails?.medium?.url ||
              item.snippet?.thumbnails?.default?.url ||
              `https://img.youtube.com/vi/${videoId}/hqdefault.jpg`,
          });
        }
        itemPageToken = items.data.nextPageToken || undefined;
      } while (itemPageToken);

      playlists.push({
        playlistId: playlist.id,
        title: playlist.snippet?.title || playlist.id,
        description: playlist.snippet?.description || "",
        url: `https://www.youtube.com/playlist?list=${playlist.id}`,
        thumbnailUrl:
          playlist.snippet?.thumbnails?.maxres?.url ||
          playlist.snippet?.thumbnails?.high?.url ||
          playlist.snippet?.thumbnails?.medium?.url ||
          playlist.snippet?.thumbnails?.default?.url ||
          videos[0]?.thumbnailUrl || null,
        itemCount: videos.length,
        videos: videos.sort((a, b) => a.position - b.position),
      });
    }
    playlistPageToken = response.data.nextPageToken || undefined;
  } while (playlistPageToken);

  const payload = {
    schemaVersion: 1,
    channel: {
      channelId: channel.id,
      title: channel.snippet?.title || "短裤AI分享",
      handle: channel.snippet?.customUrl || "@gxjdian",
      url: "https://youtube.com/@gxjdian",
    },
    playlists,
  };
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, `${JSON.stringify(payload, null, 2)}\n`);
  console.log(`Exported ${playlists.length} public playlists to ${outputPath}`);
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exit(1);
});
