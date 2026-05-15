"use client";

import { useState, useCallback } from "react";
import ChatWindow from "@/components/chat-window";
import ChatInput from "@/components/chat-input";
import { type Message } from "@/components/message-bubble";
import { sendMessage } from "@/lib/api";

function genId(): string {
  if (typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSend = useCallback(async (text: string) => {
    const userMsg: Message = {
      id: genId(),
      role: "user",
      content: text,
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const data = await sendMessage(text);
      const assistantMsg: Message = {
        id: genId(),
        role: "assistant",
        content: data.answer,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      const errorMsg: Message = {
        id: genId(),
        role: "assistant",
        content: `Napaka: ${err instanceof Error ? err.message : "Nekaj je slo narobe."}`,
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  return (
    <div className="flex h-dvh flex-col">
      {/* Masthead */}
      <header className="border-b border-[var(--color-ink)] px-4 py-2">
        <div className="mx-auto flex max-w-3xl items-center justify-between">
          <h1 className="font-display text-[0.6875rem] font-bold tracking-[0.18em] text-[var(--color-ink)] uppercase">
            <button
              onClick={() => { window.location.href = "/"; }}
              className="cursor-pointer hover:text-[var(--color-accent)] transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-accent)]"
              aria-label="Pojdi domov"
            >
              Srečko Kosovel
            </button>
          </h1>
          <span className="font-display text-[0.6875rem] tracking-[0.12em] text-[var(--color-muted)] uppercase">
            1904–1926
          </span>
        </div>
      </header>
      <div className="h-[2px] bg-[var(--color-accent)]" />

      {/* Chat */}
      <ChatWindow
        messages={messages}
        isLoading={isLoading}
        onSuggestionClick={handleSend}
      />

      {/* Input */}
      <ChatInput onSend={handleSend} disabled={isLoading} />
    </div>
  );
}
