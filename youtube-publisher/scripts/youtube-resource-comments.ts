/** Read-only inspection and single-attempt comment insertion. Never pins or uploads. */
import * as fs from "fs";
import { authenticate } from "./authenticate";

export async function resourceCommentRequest(youtube: any, input: any) {
  if (!/^[A-Za-z0-9_-]{11}$/.test(input.videoId)) throw new Error("Invalid video ID");
  const own = await youtube.channels.list({ part: ["id"], mine: true });
  const ids = new Set((own.data.items || []).map((c: any) => c.id));
  const response = await youtube.videos.list({ part: ["snippet", "status"], id: [input.videoId] });
  const video = response.data.items?.[0];
  if (!video || !ids.has(video.snippet?.channelId)) throw new Error("Target is not owned by authenticated channel");
  const channelId = video.snippet!.channelId!;
  if (input.op === "inspect") {
    const comments: any[] = [];
    if (video.status?.privacyStatus !== "private") {
      let pageToken: string | undefined;
      let pages = 0;
      do {
        const page: any = await youtube.commentThreads.list({
          part: ["snippet"], videoId: input.videoId, maxResults: 100,
          textFormat: "plainText", order: "time", pageToken,
        });
        for (const thread of page.data.items || []) {
          const c = thread.snippet?.topLevelComment;
          if (c?.snippet?.authorChannelId?.value === channelId) {
            comments.push({ id: c.id, text: c.snippet.textOriginal, authorChannelId: channelId });
          }
        }
        pageToken = page.data.nextPageToken;
        if (++pages >= 100 && pageToken) throw new Error("Comment scan incomplete; refusing insertion");
      } while (pageToken);
    }
    return { videoId: input.videoId, channelId, title: video.snippet?.title,
      privacy: video.status?.privacyStatus, description: video.snippet?.description,
      comments, complete: true };
  }
  if (input.op !== "insert" || input.channelId !== channelId || typeof input.text !== "string" || !input.text.trim() || input.text.length > 9000) {
    throw new Error("Invalid insert request");
  }
  if (video.status?.privacyStatus === "private") throw new Error("Private video cannot receive comments");
  // A failed POST can have succeeded remotely. Disable transport-level retries.
  const result = await youtube.commentThreads.insert({ part: ["snippet"], requestBody: {
    snippet: { channelId, videoId: input.videoId,
      topLevelComment: { snippet: { textOriginal: input.text } } },
  } }, { retry: false });
  const c = result.data.snippet?.topLevelComment;
  return { id: c?.id, text: c?.snippet?.textOriginal, channelId };
}
if (require.main === module) {
  const input = JSON.parse(fs.readFileSync(0, "utf8"));
  authenticate(false).then(({ youtube }) => resourceCommentRequest(youtube, input))
    .then(result => console.log("RESOURCE_COMMENT_JSON=" + JSON.stringify(result))).catch(error => {
      console.error("Resource comment request failed:", error.message);
      process.exitCode = 1;
    });
}
