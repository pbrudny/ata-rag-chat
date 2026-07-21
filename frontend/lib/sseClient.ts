import type { ChatSSEEvent } from "./types";

export interface StreamChatOptions {
  question: string;
  topK?: number;
  signal?: AbortSignal;
}

/**
 * Streams /api/chat via fetch + ReadableStream rather than the native
 * EventSource API, because EventSource only supports GET and this endpoint
 * is a POST.
 */
export async function streamChat(
  options: StreamChatOptions,
  onEvent: (event: ChatSSEEvent) => void
): Promise<void> {
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question: options.question, top_k: options.topK ?? 5 }),
    signal: options.signal,
  });

  if (!response.ok || !response.body) {
    throw new Error(`Chat request failed with status ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let boundary = buffer.indexOf("\n\n");
    while (boundary !== -1) {
      dispatchFrame(buffer.slice(0, boundary), onEvent);
      buffer = buffer.slice(boundary + 2);
      boundary = buffer.indexOf("\n\n");
    }
  }

  if (buffer.trim()) {
    dispatchFrame(buffer, onEvent);
  }
}

function dispatchFrame(frame: string, onEvent: (event: ChatSSEEvent) => void): void {
  const parsed = parseFrame(frame);
  if (parsed) onEvent(parsed);
}

function parseFrame(frame: string): ChatSSEEvent | null {
  let eventName = "";
  let dataLine = "";
  for (const line of frame.split("\n")) {
    if (line.startsWith("event:")) {
      eventName = line.slice("event:".length).trim();
    } else if (line.startsWith("data:")) {
      dataLine += line.slice("data:".length).trim();
    }
  }
  if (!eventName || !dataLine) return null;

  return { event: eventName, data: JSON.parse(dataLine) } as ChatSSEEvent;
}
