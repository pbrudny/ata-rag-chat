import { describe, expect, it, vi } from "vitest";
import { streamChat } from "../lib/sseClient";
import type { ChatSSEEvent } from "../lib/types";

function mockFetchResponse(chunks: string[]): Response {
  const encoder = new TextEncoder();
  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      for (const chunk of chunks) {
        controller.enqueue(encoder.encode(chunk));
      }
      controller.close();
    },
  });
  return { ok: true, status: 200, body: stream } as unknown as Response;
}

describe("streamChat", () => {
  it("parses sources, token, and done events in order", async () => {
    const frames =
      'event: sources\ndata: [{"title":"Rekrutacja","url":"https://akademiata.pl/r","section":null}]\n\n' +
      'event: token\ndata: "Hello"\n\n' +
      'event: token\ndata: " world"\n\n' +
      'event: done\ndata: {"confidence":0.8,"answered":true}\n\n';

    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(mockFetchResponse([frames])));

    const events: ChatSSEEvent[] = [];
    await streamChat({ question: "Kiedy jest rekrutacja?" }, (event) => events.push(event));

    expect(events.map((e) => e.event)).toEqual(["sources", "token", "token", "done"]);
    expect(events[0].data).toEqual([
      { title: "Rekrutacja", url: "https://akademiata.pl/r", section: null },
    ]);
    expect(events[1].data).toBe("Hello");
    expect(events[2].data).toBe(" world");
    expect(events[3].data).toEqual({ confidence: 0.8, answered: true });
  });

  it("handles a frame split across multiple stream chunks", async () => {
    const part1 = 'event: token\ndata: "Hel';
    const part2 = 'lo"\n\n';
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(mockFetchResponse([part1, part2])));

    const events: ChatSSEEvent[] = [];
    await streamChat({ question: "test" }, (event) => events.push(event));

    expect(events).toEqual([{ event: "token", data: "Hello" }]);
  });

  it("flushes a trailing frame with no terminating blank line", async () => {
    const frame = 'event: token\ndata: "Hi"';
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(mockFetchResponse([frame])));

    const events: ChatSSEEvent[] = [];
    await streamChat({ question: "test" }, (event) => events.push(event));

    expect(events).toEqual([{ event: "token", data: "Hi" }]);
  });

  it("throws when the response is not ok", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 500, body: null } as unknown as Response)
    );

    await expect(streamChat({ question: "test" }, () => {})).rejects.toThrow(
      "Chat request failed with status 500"
    );
  });

  it("sends the question and top_k in the POST body", async () => {
    const fetchMock = vi.fn().mockResolvedValue(mockFetchResponse([""]));
    vi.stubGlobal("fetch", fetchMock);

    await streamChat({ question: "Ile kosztuje czesne?", topK: 3 }, () => {});

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/chat",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ question: "Ile kosztuje czesne?", top_k: 3 }),
      })
    );
  });
});
