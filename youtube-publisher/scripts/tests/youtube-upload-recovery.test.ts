import assert from "node:assert/strict";
import test from "node:test";
import {
  AmbiguousUploadError,
  PersistentP0DError,
  UploadRecoveryClient,
  recoverAmbiguousUpload,
} from "../youtube-upload-recovery";

const now = Date.parse("2030-01-01T12:00:00Z");
const candidate = {
  id: { videoId: "AbCdEfGhI12" },
  snippet: { title: "Exact title", publishedAt: "2030-01-01T11:59:00Z" },
};

function clientWithDurations(durations: Array<string | undefined>): UploadRecoveryClient {
  let index = 0;
  return {
    search: { list: async () => ({ data: { items: [candidate] } }) },
    videos: {
      list: async () => {
        const duration = durations[Math.min(index, durations.length - 1)];
        index += 1;
        return { data: { items: duration === undefined ? [] : [{ id: "AbCdEfGhI12", contentDetails: { duration } }] } };
      },
    },
  };
}

test("ambiguous upload recovers one recent exact-title video with valid duration", async () => {
  const video = await recoverAmbiguousUpload(clientWithDurations(["PT2M"]), "Exact title", { now });
  assert.equal(video.id, "AbCdEfGhI12");
});

test("P0D is rechecked and accepted only after duration becomes valid", async () => {
  const video = await recoverAmbiguousUpload(clientWithDurations(["P0D", "PT2M"]), "Exact title", {
    now,
    sleep: async () => undefined,
  });
  assert.equal(video.contentDetails?.duration, "PT2M");
});

test("persistent P0D stops with stable video ID and exit code", async () => {
  await assert.rejects(
    () => recoverAmbiguousUpload(clientWithDurations(["P0D"]), "Exact title", { now, sleep: async () => undefined }),
    (error: unknown) => error instanceof PersistentP0DError
      && error.videoId === "AbCdEfGhI12"
      && error.exitCode === 42,
  );
});

test("empty metadata recheck is ambiguous and never permits another insert", async () => {
  await assert.rejects(
    () => recoverAmbiguousUpload(clientWithDurations(["P0D", undefined]), "Exact title", { now, sleep: async () => undefined }),
    (error: unknown) => error instanceof AmbiguousUploadError
      && error.videoId === "AbCdEfGhI12"
      && error.exitCode === 43,
  );
});

test("missing search candidate is ambiguous", async () => {
  const client: UploadRecoveryClient = {
    search: { list: async () => ({ data: { items: [] } }) },
    videos: { list: async () => ({ data: { items: [] } }) },
  };
  await assert.rejects(
    () => recoverAmbiguousUpload(client, "Exact title", { now }),
    (error: unknown) => error instanceof AmbiguousUploadError && error.exitCode === 43,
  );
});

test("recovery API failure is ambiguous", async () => {
  const client: UploadRecoveryClient = {
    search: { list: async () => { throw new Error("proxy unavailable"); } },
    videos: { list: async () => ({ data: { items: [] } }) },
  };
  await assert.rejects(
    () => recoverAmbiguousUpload(client, "Exact title", { now }),
    (error: unknown) => error instanceof AmbiguousUploadError
      && error.message.includes("proxy unavailable")
      && error.exitCode === 43,
  );
});
