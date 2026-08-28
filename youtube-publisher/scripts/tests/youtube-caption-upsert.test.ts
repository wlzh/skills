import assert from "node:assert/strict";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import test, { TestContext } from "node:test";
import { CaptionClient, upsertCaptionTrack } from "../youtube-caption-upsert";

function captionFile(t: TestContext): string {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), "youtube-caption-test-"));
  t.after(() => fs.rmSync(directory, { recursive: true, force: true }));
  const file = path.join(directory, "caption.vtt");
  fs.writeFileSync(file, "WEBVTT\n\n00:00.000 --> 00:01.000\nTest\n");
  return file;
}

test("existing exact caption track is updated without deletion", async (t) => {
  let inserted = false;
  let updated = false;
  const client: CaptionClient = { captions: {
    list: async () => ({ data: { items: [{ id: "caption-1", snippet: { language: "zh", name: "中文" } }] } }),
    insert: async () => { inserted = true; return { data: {} }; },
    update: async () => { updated = true; return { data: { id: "caption-1" } }; },
  } };
  const result = await upsertCaptionTrack(client, {
    videoId: "video-1", captionFile: captionFile(t), language: "zh", name: "中文", mediaBody: "fixture",
  });
  assert.equal(result.action, "updated");
  assert.equal(updated, true);
  assert.equal(inserted, false);
});

test("missing caption track is inserted", async (t) => {
  let inserted = false;
  const client: CaptionClient = { captions: {
    list: async () => ({ data: { items: [] } }),
    insert: async () => { inserted = true; return { data: { id: "caption-new" } }; },
    update: async () => { throw new Error("unexpected update"); },
  } };
  const result = await upsertCaptionTrack(client, {
    videoId: "video-1", captionFile: captionFile(t), language: "zh", name: "中文", mediaBody: "fixture",
  });
  assert.equal(result.action, "inserted");
  assert.equal(inserted, true);
});

test("multiple exact caption tracks fail closed", async (t) => {
  const client: CaptionClient = { captions: {
    list: async () => ({ data: { items: [
      { id: "caption-1", snippet: { language: "zh", name: "中文" } },
      { id: "caption-2", snippet: { language: "zh", name: "中文" } },
    ] } }),
    insert: async () => { throw new Error("unexpected insert"); },
    update: async () => { throw new Error("unexpected update"); },
  } };
  await assert.rejects(
    () => upsertCaptionTrack(client, {
      videoId: "video-1", captionFile: captionFile(t), language: "zh", name: "中文", mediaBody: "fixture",
    }),
    /multiple matching caption tracks/i,
  );
});
