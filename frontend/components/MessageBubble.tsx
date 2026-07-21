import type { ChatMessage } from "@/lib/types";
import { ConfidenceBadge } from "./ConfidenceBadge";
import { SourceCitations } from "./SourceCitations";

interface MessageBubbleProps {
  message: ChatMessage;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] rounded-lg px-4 py-2 ${
          isUser ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-900"
        }`}
      >
        <p className="whitespace-pre-wrap">{message.text}</p>
        {!isUser && message.sources && <SourceCitations sources={message.sources} />}
        {!isUser && typeof message.confidence === "number" && (
          <ConfidenceBadge confidence={message.confidence} answered={message.answered ?? true} />
        )}
      </div>
    </div>
  );
}
