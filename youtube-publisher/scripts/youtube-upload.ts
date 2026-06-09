import { google, youtube_v3 } from "googleapis";
import * as fs from "fs";
import * as path from "path";
import { authenticate } from "./authenticate";

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

function sanitizeYouTubeMetadata(text: string = ""): string {
  return text
    .replace(/>/g, "》")
    .replace(/</g, "《")
    .replace(/\r\n/g, "\n")
    .trim();
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

// Upload video
async function uploadVideo(
  auth: any,
  options: UploadOptions
): Promise<{ videoId: string; url: string }> {
  const youtube = google.youtube({ version: "v3", auth });
  const sanitizedTitle = sanitizeYouTubeMetadata(options.title);
  const sanitizedDescription = sanitizeYouTubeMetadata(options.description || "");

  // Prepare video metadata
  const videoMetadata: youtube_v3.Schema$Video = {
    snippet: {
      title: sanitizedTitle,
      description: sanitizedDescription,
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
    videoMetadata.snippet!.title = sanitizedTitle.includes("#Shorts")
      ? sanitizedTitle
      : `${sanitizedTitle} #Shorts`;
  }

  console.log("\n=== Uploading to YouTube ===");
  console.log(`Title: ${videoMetadata.snippet!.title}`);
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

  // Upload video with resumable upload for better reliability
  const maxRetries = 3;
  let response;
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      response = await youtube.videos.insert(
        {
          part: ["snippet", "status"],
          requestBody: videoMetadata,
          media: {
            mimeType: "video/mp4",
            body: fs.createReadStream(options.video),
          },
        },
        {
          onUploadProgress: (evt: { bytesRead: number }) => {
            const progress = (evt.bytesRead / stats.size) * 100;
            if (progress % 10 < 1 || progress >= 99.9) {
              console.log(`Upload progress: ${progress.toFixed(1)}%`);
            }
          },
        }
      );
      break;
    } catch (err: any) {
      const isRetryable =
        err.message?.includes("EPIPE") ||
        err.message?.includes("ETIMEDOUT") ||
        err.message?.includes("ECONNRESET") ||
        err.message?.includes("socket hang up");
      if (isRetryable && attempt < maxRetries) {
        console.log(
          `\nUpload failed (attempt ${attempt}/${maxRetries}): ${err.message}`
        );
        console.log(`Retrying in ${attempt * 5} seconds...`);
        await new Promise((r) => setTimeout(r, attempt * 5000));
      } else {
        throw err;
      }
    }
  }

  if (!response) {
    throw new Error("Upload failed after all retries");
  }
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
    await authenticate(true);
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

  // Authenticate (interactive mode allowed for upload)
  const { oauth2Client: auth } = await authenticate(true);

  // Upload
  const result = await uploadVideo(auth, options);

  console.log(`\n${result.url}`);
}

main().catch((err) => {
  console.error("Error:", err.message);
  process.exit(1);
});
