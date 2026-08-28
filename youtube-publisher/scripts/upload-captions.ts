import { authenticate } from "./authenticate";
import { upsertCaptionTrack } from "./youtube-caption-upsert";

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

  const result = await upsertCaptionTrack(youtube as unknown as Parameters<typeof upsertCaptionTrack>[0], {
    videoId: options.videoId,
    captionFile: options.captionFile,
    language: options.language,
    name: options.name,
  });
  console.log(`Caption ${result.action}: ${result.captionId ?? "unknown"}`);
  console.log("Done!");
}

main().catch(console.error);
