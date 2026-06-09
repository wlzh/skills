import * as fs from "fs";
import { authenticate } from "./authenticate";

interface Options {
  videoId: string;
  captionFile: string;
  language: string;
  name: string;
}

function parseArgs(): Options {
  const args = process.argv.slice(2);
  const options: Options = { videoId: "", captionFile: "", language: "zh", name: "中文" };
  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case "--video-id": options.videoId = args[++i]; break;
      case "--caption-file": options.captionFile = args[++i]; break;
      case "--language": options.language = args[++i]; break;
      case "--name": options.name = args[++i]; break;
    }
  }
  return options;
}

async function main() {
  const options = parseArgs();
  if (!options.videoId || !options.captionFile) {
    console.error("Usage: npx ts-node upload-captions.ts --video-id <id> --caption-file <vtt> [--language zh] [--name 中文]");
    process.exit(1);
  }

  const { youtube } = await authenticate();

  // Delete existing captions first
  const existingCaptions = await youtube.captions.list({
    part: ["snippet"],
    videoId: options.videoId,
  });
  for (const caption of existingCaptions.data.items || []) {
    if (caption.id) {
      try {
        await youtube.captions.delete({ id: caption.id });
        console.log("Deleted existing caption: " + caption.id);
      } catch (e: any) {
        console.error("Failed to delete caption " + caption.id + ": " + e.message);
      }
    }
  }

  // Check file exists  
  if (!fs.existsSync(options.captionFile)) {
    console.error("Caption file not found: " + options.captionFile);
    process.exit(1);
  }

  // Upload new caption
  const result = await youtube.captions.insert(
    {
      part: ["snippet"],
      requestBody: {
        snippet: {
          videoId: options.videoId,
          language: options.language,
          name: options.name,
        },
      },
      media: {
        body: fs.createReadStream(options.captionFile),
        mimeType: "text/vtt",
      },
    },
    { headers: { "Content-Type": "application/octet-stream" } }
  );

  console.log("Caption uploaded: " + result.data.id);
  console.log("Done!");
}

main().catch(console.error);
