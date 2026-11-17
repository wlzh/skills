import { test } from "node:test";
import * as assert from "node:assert/strict";
import { resourceCommentRequest } from "../youtube-resource-comments";

const videoId = "s8huUBAJwQ4";
function fixture() {
  const calls: any[] = [];
  const api = {
    channels: { list: async () => ({ data: { items: [{ id: "owner" }] } }) },
    videos: { list: async () => ({ data: { items: [{ snippet: { channelId: "owner" }, status: { privacyStatus: "public" } }] } }) },
    commentThreads: {
      list: async (_: any): Promise<any> => ({ data: { items: [] } }),
      insert: async (...args: any[]) => { calls.push(args); return { data: { snippet: { topLevelComment: { id: "comment" } } } }; },
    },
  };
  return { api, calls };
}

test("comment insertion disables transport retries and never uploads a video", async () => {
  const { api, calls } = fixture();
  const result = await resourceCommentRequest(api, { op: "insert", videoId, channelId: "owner", text: "https://a.example?ref=X%2FY" });
  assert.equal(result.id, "comment");
  assert.equal(calls.length, 1);
  assert.deepEqual(calls[0][1], { retry: false });
  assert.equal(calls[0][0].requestBody.snippet.topLevelComment.snippet.textOriginal, "https://a.example?ref=X%2FY");
});

test("foreign videos are rejected before comment mutation", async () => {
  const { api, calls } = fixture();
  api.channels.list = async () => ({ data: { items: [{ id: "other" }] } });
  await assert.rejects(resourceCommentRequest(api, { op: "insert", videoId, channelId: "owner", text: "x" }), /not owned/);
  assert.equal(calls.length, 0);
});

test("inspection scans pagination and only returns owner comments", async () => {
  const { api } = fixture();
  let pages = 0;
  const c = (id: string, owner: string) => ({ snippet: { topLevelComment: { id, snippet: { textOriginal: id, authorChannelId: { value: owner } } } } });
  api.commentThreads.list = async params => {
    pages++;
    if (!params.pageToken) return { data: { items: [c("foreign", "other")], nextPageToken: "page2" } };
    return { data: { items: [c("mine", "owner")] } };
  };
  const result = await resourceCommentRequest(api, { op: "inspect", videoId });
  assert.equal(pages, 2);
  assert.equal(result.complete, true);
  assert.deepEqual(result.comments?.map((c: any) => c.id), ["mine"]);
});

test("incomplete scans fail closed", async () => {
  const { api, calls } = fixture();
  api.commentThreads.list = async () => ({ data: { nextPageToken: "again" } });
  await assert.rejects(resourceCommentRequest(api, { op: "inspect", videoId }), /incomplete/);
  assert.equal(calls.length, 0);
});

test("private video inspections never query comments or allow insertion", async () => {
  const { api, calls } = fixture();
  api.videos.list = async () => ({ data: { items: [{ snippet: { channelId: "owner" }, status: { privacyStatus: "private" } }] } });
  api.commentThreads.list = async () => { throw new Error("must not query"); };
  const result = await resourceCommentRequest(api, { op: "inspect", videoId });
  assert.equal(result.privacy, "private");
  await assert.rejects(resourceCommentRequest(api, { op: "insert", videoId, channelId: "owner", text: "x" }), /Private video/);
  assert.equal(calls.length, 0);
});
