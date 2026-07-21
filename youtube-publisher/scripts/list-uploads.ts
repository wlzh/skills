import { authenticate } from "./authenticate";
import { google } from "googleapis";

(async () => {
  try {
    const auth = await authenticate() as any;
    const youtube = google.youtube({ version: "v3", auth: auth.oauth2Client });

    const channels = await youtube.channels.list({
      part: ["contentDetails"],
      mine: true,
    });

    if (!channels.data.items || channels.data.items.length === 0) {
      console.error("No channel found");
      process.exit(1);
    }

    const uploadsPlaylist =
      channels.data.items[0]?.contentDetails?.relatedPlaylists?.uploads;
    if (!uploadsPlaylist) {
      throw new Error("The authenticated channel has no uploads playlist");
    }
    console.log("Uploads playlist:", uploadsPlaylist);

    const videos = await youtube.playlistItems.list({
      part: ["snippet", "status"],
      playlistId: uploadsPlaylist,
      maxResults: 20,
    });

    console.log("\nRecent uploads:");
    for (const item of videos.data.items || []) {
      const vid = item.snippet?.resourceId?.videoId;
      const title = item.snippet?.title;
      if (!vid || !title) {
        continue;
      }
      const privacy = item.status?.privacyStatus || "unknown";
      const date = item.snippet?.publishedAt || "unknown";
      console.log(vid + " | " + privacy + " | " + date + " | " + title);
    }
  } catch (err) {
    console.error("Error:", (err as any).message || String(err));
    process.exit(1);
  }
})();
