import * as fs from "fs";
import { authenticate } from "./authenticate";

async function main() {
  const { youtube } = await authenticate();

  // Delete dummy video
  try {
    await youtube.videos.delete({ id: "TsUEsCo2jgo" });
    console.log("Deleted dummy video TsUEsCo2jgo");
  } catch (e: any) {
    console.log("Delete failed:", e.message);
  }

  // Upload thumbnail
  try {
    await youtube.thumbnails.set({
      videoId: "GsI9cX8-pzs",
      media: { body: fs.createReadStream("/tmp/thumbnail-compressed.jpg") },
    });
    console.log("Thumbnail uploaded to GsI9cX8-pzs");
  } catch (e: any) {
    console.log("Thumbnail failed:", e.message);
  }
}

main();
