import { google } from "googleapis";
import * as fs from "fs";
import * as path from "path";
import open from "open";
import dotenv from "dotenv";

// Load environment variables (same .env as youtube-upload.ts)
dotenv.config({ path: path.join(__dirname, ".env") });

const TOKEN_PATH = path.join(__dirname, ".youtube-token.json");

async function authenticate(): Promise<any> {
  const clientId = process.env.YOUTUBE_CLIENT_ID;
  const clientSecret = process.env.YOUTUBE_CLIENT_SECRET;

  if (!clientId || !clientSecret) {
    console.error("Error: Missing YOUTUBE_CLIENT_ID or YOUTUBE_CLIENT_SECRET in .env");
    process.exit(1);
  }

  const oauth2Client = new google.auth.OAuth2(
    clientId,
    clientSecret,
    process.env.YOUTUBE_REDIRECT_URI || "http://localhost:3333/oauth2callback"
  );

  if (!fs.existsSync(TOKEN_PATH)) {
    console.error("Error: No token found. Run youtube-upload.ts --auth first.");
    process.exit(1);
  }

  const tokenData = JSON.parse(fs.readFileSync(TOKEN_PATH, "utf-8"));
  oauth2Client.setCredentials(tokenData);

  // Try to refresh if expired
  if (tokenData.expiry_date && tokenData.expiry_date <= Date.now()) {
    if (tokenData.refresh_token) {
      try {
        const { credentials } = await oauth2Client.refreshAccessToken();
        oauth2Client.setCredentials(credentials);
        fs.writeFileSync(TOKEN_PATH, JSON.stringify(credentials, null, 2));
        console.log("Token refreshed successfully");
      } catch {
        console.error("Token refresh failed. Run youtube-upload.ts --auth first.");
        process.exit(1);
      }
    }
  }

  return oauth2Client;
}

async function updateDescription(
  auth: any,
  videoId: string,
  newDescription: string
): Promise<void> {
  const youtube = google.youtube({ version: "v3", auth });

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

  // Send only the snippet fields the API requires on update.
  // Avoid any status or contentDetails fields that cause "invalid" errors.
  await youtube.videos.update({
    part: ["snippet"],
    requestBody: {
      id: videoId,
      snippet: {
        title: cur.title,
        description: cleanDescription,
        categoryId: cur.categoryId,
        tags: cur.tags,
        defaultLanguage: cur.defaultLanguage,
        defaultAudioLanguage: cur.defaultAudioLanguage,
      },
    },
  });

  console.log(`Description updated for video ${videoId}`);
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
  const auth = await authenticate();
  await updateDescription(auth, videoId, description);
}

main().catch((err) => {
  console.error("Error:", err.message);
  process.exit(1);
});
