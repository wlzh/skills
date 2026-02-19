import { google, youtube_v3 } from "googleapis";
import * as fs from "fs";
import * as path from "path";
import * as http from "http";
import open from "open";
import dotenv from "dotenv";

// Load environment variables
dotenv.config({ path: path.join(__dirname, ".env") });

const SCOPES = [
  "https://www.googleapis.com/auth/youtube.upload",
  "https://www.googleapis.com/auth/youtube",
  "https://www.googleapis.com/auth/youtube.force-ssl",
];

const TOKEN_PATH = path.join(__dirname, ".youtube-token.json");

interface UploadOptions {
  video: string;
  title: string;
  description?: string;
  tags?: string[];
  privacy?: "public" | "unlisted" | "private";
  category?: string;
  thumbnail?: string;
  playlist?: string;
  isShort?: boolean;
  dryRun?: boolean;
  subtitles?: string;
  subtitleLang?: string;
  subtitleName?: string;
}

interface TokenData {
  access_token: string;
  refresh_token: string;
  scope: string;
  token_type: string;
  expiry_date: number;
}

// Parse command line arguments
function parseArgs(): { auth: boolean; options: UploadOptions } {
  const args = process.argv.slice(2);
  let auth = false;
  const options: UploadOptions = {
    video: "",
    title: "",
    description: "",
    tags: [],
    privacy: "unlisted",
    category: "22", // People & Blogs
    isShort: false,
    dryRun: false,
    subtitleLang: "zh",
    subtitleName: "中文",
  };

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    const next = args[i + 1];

    switch (arg) {
      case "--auth":
        auth = true;
        break;
      case "--video":
      case "-v":
        options.video = next;
        i++;
        break;
      case "--title":
      case "-t":
        options.title = next;
        i++;
        break;
      case "--description":
      case "-d":
        options.description = next;
        i++;
        break;
      case "--tags":
        options.tags = next.split(",").map((t) => t.trim());
        i++;
        break;
      case "--privacy":
      case "-p":
        options.privacy = next as "public" | "unlisted" | "private";
        i++;
        break;
      case "--category":
      case "-c":
        options.category = next;
        i++;
        break;
      case "--thumbnail":
        options.thumbnail = next;
        i++;
        break;
      case "--playlist":
        options.playlist = next;
        i++;
        break;
      case "--short":
        options.isShort = true;
        break;
      case "--dry-run":
        options.dryRun = true;
        break;
      case "--subtitles":
        options.subtitles = next;
        i++;
        break;
      case "--subtitle-lang":
        options.subtitleLang = next;
        i++;
        break;
      case "--subtitle-name":
        options.subtitleName = next;
        i++;
        break;
      case "--help":
      case "-h":
        printHelp();
        process.exit(0);
    }
  }

  return { auth, options };
}

function printHelp() {
  console.log(`
YouTube Uploader

Usage:
  npx ts-node youtube-upload.ts [options]

Options:
  --auth                  Run OAuth2 authentication
  --video, -v <path>      Video file path (required)
  --title, -t <title>     Video title (required)
  --description, -d <desc> Video description
  --tags <tags>           Comma-separated tags
  --privacy, -p <level>   public, unlisted, or private (default: unlisted)
  --category, -c <id>     Category ID (default: 22)
  --thumbnail <path>      Custom thumbnail image (local path or URL)
  --subtitles <path>      Subtitle file path (SRT/VTT)
  --subtitle-lang <code>  Subtitle language code (default: zh)
  --subtitle-name <name>  Subtitle display name (default: 中文)
  --playlist <id>         Add to playlist
  --short                 Mark as YouTube Short
  --dry-run               Preview without uploading
  --help, -h              Show this help

Examples:
  npx ts-node youtube-upload.ts --auth
  npx ts-node youtube-upload.ts -v video.mp4 -t "My Video" -p public
  npx ts-node youtube-upload.ts -v video.mp4 -t "My Video" --subtitles subs.srt --subtitle-lang zh
`);
}

// OAuth2 authentication
async function authenticate(): Promise<any> {
  const clientId = process.env.YOUTUBE_CLIENT_ID;
  const clientSecret = process.env.YOUTUBE_CLIENT_SECRET;

  if (!clientId || !clientSecret) {
    console.error("Error: Missing YOUTUBE_CLIENT_ID or YOUTUBE_CLIENT_SECRET in .env");
    console.error("Get credentials from Google Cloud Console:");
    console.error("1. Go to console.cloud.google.com");
    console.error("2. Create a project and enable YouTube Data API v3");
    console.error("3. Create OAuth2 credentials (Desktop app)");
    process.exit(1);
  }

  const oauth2Client = new google.auth.OAuth2(
    clientId,
    clientSecret,
    process.env.YOUTUBE_REDIRECT_URI || "http://localhost:3333/oauth2callback"
  );

  // Check for existing token
  if (fs.existsSync(TOKEN_PATH)) {
    const tokenData: TokenData = JSON.parse(fs.readFileSync(TOKEN_PATH, "utf-8"));
    oauth2Client.setCredentials(tokenData);

    // Check if token is expired
    if (tokenData.expiry_date && tokenData.expiry_date > Date.now()) {
      return oauth2Client;
    }

    // Try to refresh token
    if (tokenData.refresh_token) {
      try {
        const { credentials } = await oauth2Client.refreshAccessToken();
        oauth2Client.setCredentials(credentials);
        fs.writeFileSync(TOKEN_PATH, JSON.stringify(credentials, null, 2));
        console.log("Token refreshed successfully");
        return oauth2Client;
      } catch (err) {
        console.log("Token refresh failed, re-authenticating...");
      }
    }
  }

  // Need new authentication
  return new Promise((resolve, reject) => {
    const authUrl = oauth2Client.generateAuthUrl({
      access_type: "offline",
      scope: SCOPES,
      prompt: "consent",
    });

    console.log("\n=== YouTube Authentication ===");
    console.log("Opening browser for authentication...\n");

    // Create local server to receive callback
    const server = http.createServer(async (req, res) => {
      try {
        const urlObj = new URL(req.url || "", "http://localhost:3333");
        if (urlObj.pathname === "/oauth2callback") {
          console.log("Received callback, exchanging code for tokens...");
          const code = urlObj.searchParams.get("code");

          if (code) {
            try {
              const { tokens } = await oauth2Client.getToken(code);
              console.log("Token obtained successfully");
              oauth2Client.setCredentials(tokens);

            // Save token
            fs.writeFileSync(TOKEN_PATH, JSON.stringify(tokens, null, 2));

            res.writeHead(200, { "Content-Type": "text/html" });
            res.end(`
              <html>
                <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                  <h1>Authentication Successful!</h1>
                  <p>You can close this window and return to the terminal.</p>
                </body>
              </html>
            `);

            server.close();
            console.log("Authentication successful! Token saved.");
            resolve(oauth2Client);
          } else {
            res.writeHead(400);
            res.end("No code received");
            reject(new Error("No code received"));
          }
        }
      } catch (err: any) {
        console.error("Authentication error:", err.message);
        console.error("Error details:", err);
        res.writeHead(500);
        res.end(`Authentication failed: ${err.message}`);
        reject(err);
      }
    });

    server.listen(3333, () => {
      open(authUrl);
    });

    // Timeout after 2 minutes
    setTimeout(() => {
      server.close();
      reject(new Error("Authentication timeout"));
    }, 120000);
  });
}

// Upload video
async function uploadVideo(
  auth: any,
  options: UploadOptions
): Promise<{ videoId: string; url: string }> {
  const youtube = google.youtube({ version: "v3", auth });

  // Prepare video metadata
  const videoMetadata: youtube_v3.Schema$Video = {
    snippet: {
      title: options.title,
      description: options.description || "",
      tags: options.tags,
      categoryId: options.category,
    },
    status: {
      privacyStatus: options.privacy,
      selfDeclaredMadeForKids: false,
    },
  };

  // Add Shorts indicator if specified
  if (options.isShort) {
    videoMetadata.snippet!.title = options.title.includes("#Shorts")
      ? options.title
      : `${options.title} #Shorts`;
  }

  console.log("\n=== Uploading to YouTube ===");
  console.log(`Title: ${options.title}`);
  console.log(`Privacy: ${options.privacy}`);
  console.log(`Category: ${options.category}`);
  if (options.tags?.length) {
    console.log(`Tags: ${options.tags.join(", ")}`);
  }
  if (options.isShort) {
    console.log("Type: YouTube Short");
  }

  // Get file size
  const stats = fs.statSync(options.video);
  const fileSizeMB = (stats.size / (1024 * 1024)).toFixed(2);
  console.log(`File: ${path.basename(options.video)} (${fileSizeMB} MB)`);

  if (options.dryRun) {
    console.log("\n[DRY RUN] Would upload video with above settings");
    return { videoId: "DRY_RUN", url: "https://youtu.be/DRY_RUN" };
  }

  console.log("\nUploading... (this may take a while for large files)");

  // Upload video
  const response = await youtube.videos.insert({
    part: ["snippet", "status"],
    requestBody: videoMetadata,
    media: {
      body: fs.createReadStream(options.video),
    },
  });

  const videoId = response.data.id!;
  const videoUrl = `https://youtu.be/${videoId}`;

  console.log("\n=== Upload Complete! ===");
  console.log(`Video ID: ${videoId}`);
  console.log(`URL: ${videoUrl}`);

  // Upload thumbnail if provided
  if (options.thumbnail && fs.existsSync(options.thumbnail)) {
    console.log("\nUploading thumbnail...");
    try {
      await youtube.thumbnails.set({
        videoId: videoId,
        media: {
          body: fs.createReadStream(options.thumbnail),
        },
      });
      console.log("Thumbnail uploaded!");
    } catch (err: any) {
      console.error("Thumbnail upload failed:", err.message);
    }
  }

  // Upload subtitles if provided
  if (options.subtitles && fs.existsSync(options.subtitles)) {
    console.log("\nUploading subtitles...");
    try {
      // First, need to get the track ID from the snippet
      await youtube.captions.insert({
        part: ["snippet"],
        requestBody: {
          snippet: {
            videoId: videoId,
            language: options.subtitleLang || "zh",
            name: options.subtitleName || "中文",
            isDraft: false,
          },
        },
        media: {
          body: fs.createReadStream(options.subtitles),
        },
      });
      console.log("Subtitles uploaded!");
    } catch (err: any) {
      console.error("Subtitles upload failed:", err.message);
    }
  } else if (options.subtitles) {
    console.error(`Subtitle file not found: ${options.subtitles}`);
  }

  // Add to playlist if specified
  if (options.playlist) {
    console.log(`\nAdding to playlist ${options.playlist}...`);
    try {
      await youtube.playlistItems.insert({
        part: ["snippet"],
        requestBody: {
          snippet: {
            playlistId: options.playlist,
            resourceId: {
              kind: "youtube#video",
              videoId: videoId,
            },
          },
        },
      });
      console.log("Added to playlist!");
    } catch (err: any) {
      console.error("Failed to add to playlist:", err.message);
    }
  }

  return { videoId, url: videoUrl };
}

// Main function
async function main() {
  const { auth: runAuth, options } = parseArgs();

  // Just authenticate
  if (runAuth && !options.video) {
    await authenticate();
    console.log("\nAuthentication complete! You can now upload videos.");
    return;
  }

  // Validate required options
  if (!options.video) {
    console.error("Error: --video is required");
    printHelp();
    process.exit(1);
  }

  if (!options.title) {
    console.error("Error: --title is required");
    printHelp();
    process.exit(1);
  }

  if (!fs.existsSync(options.video)) {
    console.error(`Error: Video file not found: ${options.video}`);
    process.exit(1);
  }

  // Authenticate
  const auth = await authenticate();

  // Upload
  const result = await uploadVideo(auth, options);

  console.log(`\n${result.url}`);
}

main().catch((err) => {
  console.error("Error:", err.message);
  process.exit(1);
});
