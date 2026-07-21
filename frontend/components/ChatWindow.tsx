"use client";

import { type FormEvent, useState } from "react";
import { streamChat } from "@/lib/sseClient";
import type { ChatMessage, ChatSource, Language } from "@/lib/types";
import { LanguageToggle } from "./LanguageToggle";
import { MessageBubble } from "./MessageBubble";

const COPY: Record<Language, { placeholder: string; send: string; error: string }> = {
  en: {
    placeholder: "Ask a question about AkademiaTA...",
    send: "Send",
    error: "Something went wrong. Please try again.",
  },
  pl: {
    placeholder: "Zadaj pytanie o AkademiaTA...",
    send: "Wyslij",
    error: "Cos poszlo nie tak. Sprobuj ponownie.",
  },
};

function newId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

export function ChatWindow() {
  const [language, setLanguage] = useState<Language>("pl");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const question = input.trim();
    if (!question || isStreaming) return;

    const assistantId = newId();
    setMessages((prev) => [
      ...prev,
      { id: newId(), role: "user", text: question },
      { id: assistantId, role: "assistant", text: "", streaming: true },
    ]);
    setInput("");
    setIsStreaming(true);

    const updateAssistant = (updater: (message: ChatMessage) => ChatMessage) => {
      setMessages((prev) =>
        prev.map((message) => (message.id === assistantId ? updater(message) : message))
      );
    };

    try {
      await streamChat({ question }, (sseEvent) => {
        if (sseEvent.event === "sources") {
          updateAssistant((message) => ({ ...message, sources: sseEvent.data as ChatSource[] }));
        } else if (sseEvent.event === "token") {
          updateAssistant((message) => ({ ...message, text: message.text + sseEvent.data }));
        } else if (sseEvent.event === "done") {
          updateAssistant((message) => ({
            ...message,
            confidence: sseEvent.data.confidence,
            answered: sseEvent.data.answered,
            streaming: false,
          }));
        }
      });
    } catch {
      updateAssistant((message) => ({
        ...message,
        text: COPY[language].error,
        streaming: false,
      }));
    } finally {
      setIsStreaming(false);
    }
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex justify-end p-2">
        <LanguageToggle language={language} onChange={setLanguage} />
      </div>
      <div className="flex-1 space-y-3 overflow-y-auto p-4">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
      </div>
      <form onSubmit={handleSubmit} className="flex gap-2 border-t p-4">
        <input
          className="flex-1 rounded border border-gray-300 px-3 py-2"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder={COPY[language].placeholder}
          disabled={isStreaming}
        />
        <button
          type="submit"
          className="rounded bg-blue-600 px-4 py-2 text-white disabled:opacity-50"
          disabled={isStreaming || !input.trim()}
        >
          {COPY[language].send}
        </button>
      </form>
    </div>
  );
}
