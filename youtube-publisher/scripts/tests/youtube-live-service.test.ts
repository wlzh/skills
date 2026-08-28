import assert from "node:assert/strict";
import test from "node:test";
import { youtube_v3 } from "googleapis";
import { YouTubeLiveService } from "../youtube-live-service";

function serviceWith(overrides: Record<string, unknown> = {}): { service: YouTubeLiveService; calls: string[] } {
  const calls: string[] = [];
  const youtube = {
    liveBroadcasts: {
      list: async () => ({ data: { items: [{ id: "broadcast-1", contentDetails: { boundStreamId: "stream-1" } }] } }),
      insert: async () => { calls.push("broadcast.insert"); return { data: { id: "broadcast-new" } }; },
      update: async () => { calls.push("broadcast.update"); return { data: { id: "broadcast-1" } }; },
      bind: async () => { calls.push("broadcast.bind"); return { data: { id: "broadcast-1" } }; },
      transition: async () => { calls.push("broadcast.transition"); return { data: { id: "broadcast-1" } }; },
      delete: async () => { calls.push("broadcast.delete"); },
      ...((overrides.liveBroadcasts as object | undefined) ?? {}),
    },
    liveStreams: {
      list: async () => ({ data: { items: [{ id: "stream-1", status: { streamStatus: "active" } }] } }),
      insert: async () => ({ data: { id: "stream-new" } }),
      update: async () => ({ data: { id: "stream-1" } }),
      delete: async () => undefined,
      ...((overrides.liveStreams as object | undefined) ?? {}),
    },
    thumbnails: { set: async () => ({ data: {} }) },
  } as unknown as youtube_v3.Youtube;
  return { service: YouTubeLiveService.fromClient(youtube), calls };
}

test("service create, bind, transition and delete paths call the API", async () => {
  const { service, calls } = serviceWith();
  await service.createLiveBroadcast({ snippet: { title: "Test" } });
  await service.bindLiveBroadcast("broadcast-1", "stream-1");
  await service.transitionLiveBroadcast("broadcast-1", "live");
  await service.deleteLiveBroadcast("broadcast-1");
  assert.deepEqual(calls, ["broadcast.insert", "broadcast.bind", "broadcast.transition", "broadcast.delete"]);
});

test("transition stops before mutation when bound stream is inactive", async () => {
  const { service, calls } = serviceWith({
    liveStreams: {
      list: async () => ({ data: { items: [{ id: "stream-1", status: { streamStatus: "inactive" } }] } }),
    },
  });
  await assert.rejects(() => service.transitionLiveBroadcast("broadcast-1", "live"), /not active/i);
  assert.equal(calls.includes("broadcast.transition"), false);
});

test("transition stops before mutation when broadcast has no bound stream", async () => {
  const { service, calls } = serviceWith({
    liveBroadcasts: {
      list: async () => ({ data: { items: [{ id: "broadcast-1", contentDetails: {} }] } }),
      transition: async () => { calls.push("broadcast.transition"); return { data: {} }; },
    },
  });
  await assert.rejects(() => service.transitionLiveBroadcast("broadcast-1", "testing"), /not bound/i);
  assert.equal(calls.includes("broadcast.transition"), false);
});
