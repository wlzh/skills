/**
 * youtube-update-description.ts — Update a YouTube video description with
 * post-write verification and robust token refresh.
 *
 * Changelog:
 *  v1.3  2026-06-11  Fix verify mismatch caused by trailing newline
 *    - YouTube API strips trailing newlines on storage, causing the exact
 *      string comparison to always fail (off by 1 char).
 *    - Fix: trimEnd() both sides before comparing.
 *  v1.2  2026-06-09  Refactor: use shared authenticate.ts module
 *    - Remove inline authenticate() function; import from ./authenticate.
 *    - Remove dotenv/TOKEN_PATH/google auth imports (handled by shared module).
 *  v1.1  2026-06-09  Post-write verification + token refresh fix
 *    - After videos.update, immediately GET to verify description matches.
 *    - If mismatch, retry up to 3 times with 5s delay.
 *    - Token refresh: always refresh when expiry_date is missing OR expired
 *      (previously skipped refresh when expiry_date was absent).
 *    - After refresh, ensure expiry_date is present in saved token file
 *      (compute from expires_in if Google omits it).
 */

import * as fs from "fs";
import { authenticate } from "./authenticate";

const MAX_VERIFY_RETRIES = 3;
const VERIFY_RETRY_DELAY_MS = 5000;

async function updateDescription(
  youtube: any,
  videoId: string,
  newDescription: string
): Promise<void> {
  // Get current snippet to preserve required fields
  const videoResponse = await youtube.videos.list({
    id: [videoId],
    part: ["snippet"],
  });

  const video = videoResponse.data.items?.[0];
  if (!video) {
    throw new Error(`Video not found: ${videoId}`);
  }

  const cur = video.snippet!;

  // Strip angle brackets — YouTube rejects them in descriptions
  const cleanDescription = newDescription.replace(/<[^>]*>/g, "").replace(/[<>]/g, "");

  // Build the snippet update payload
  const snippetPayload = {
    title: cur.title,
    description: cleanDescription,
    categoryId: cur.categoryId,
    tags: cur.tags,
    defaultLanguage: cur.defaultLanguage,
    defaultAudioLanguage: cur.defaultAudioLanguage,
  };

  // Update + verify loop
  for (let attempt = 1; attempt <= MAX_VERIFY_RETRIES; attempt++) {
    await youtube.videos.update({
      part: ["snippet"],
      requestBody: {
        id: videoId,
        snippet: snippetPayload,
      },
    });

    // Verify: GET the video again and compare description
    const verifyResponse = await youtube.videos.list({
      id: [videoId],
      part: ["snippet"],
    });

    const actualDesc = verifyResponse.data.items?.[0]?.snippet?.description || "";

    // YouTube API strips trailing newlines on storage — trim both before comparing
    if (actualDesc.trimEnd() === cleanDescription.trimEnd()) {
      console.log(`Description updated and verified for video ${videoId}`);
      return;
    }

    // Mismatch — log details and decide whether to retry
    console.error(
      `Verify mismatch (attempt ${attempt}/${MAX_VERIFY_RETRIES}): ` +
      `expected ${cleanDescription.trimEnd().length} chars, got ${actualDesc.trimEnd().length} chars`
    );

    if (attempt < MAX_VERIFY_RETRIES) {
      console.error(`Retrying in ${VERIFY_RETRY_DELAY_MS / 1000}s...`);
      await new Promise((resolve) => setTimeout(resolve, VERIFY_RETRY_DELAY_MS));
    }
  }

  // All retries exhausted
  console.error(
    `Error: Description verification failed after ${MAX_VERIFY_RETRIES} attempts for video ${videoId}`
  );
  process.exit(1);
}

function parseArgs(): { videoId: string; description: string; descriptionFile: string } {
  const args = process.argv.slice(2);
  let videoId = "";
  let description = "";
  let descriptionFile = "";

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    const next = args[i + 1];
    switch (arg) {
      case "--video-id":
        videoId = next!;
        i++;
        break;
      case "--description":
        description = next!;
        i++;
        break;
      case "--description-file":
        descriptionFile = next!;
        i++;
        break;
      case "--help":
      case "-h":
        console.log(`
Usage:
  npx ts-node youtube-update-description.ts --video-id <ID> --description "new desc"
  npx ts-node youtube-update-description.ts --video-id <ID> --description-file <path>
`);
        process.exit(0);
    }
  }

  if (!videoId) {
    console.error("Error: --video-id is required");
    process.exit(1);
  }

  if (descriptionFile && fs.existsSync(descriptionFile)) {
    description = fs.readFileSync(descriptionFile, "utf-8");
  }

  if (!description) {
    console.error("Error: --description or --description-file is required");
    process.exit(1);
  }

  return { videoId, description, descriptionFile };
}

async function main() {
  const { videoId, description } = parseArgs();
  const { youtube } = await authenticate();
  await updateDescription(youtube, videoId, description);
}

main().catch((err) => {
  console.error("Error:", err.message);
  process.exit(1);
});
