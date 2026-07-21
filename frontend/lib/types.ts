export interface ChatSource {
  title: string | null;
  url: string;
  section: string | null;
}

export interface ChatDoneData {
  confidence: number;
  answered: boolean;
}

export type ChatSSEEvent =
  | { event: "sources"; data: ChatSource[] }
  | { event: "token"; data: string }
  | { event: "done"; data: ChatDoneData };

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
  sources?: ChatSource[];
  confidence?: number;
  answered?: boolean;
  streaming?: boolean;
}

export type Language = "en" | "pl";
