"use client";

import { useState, useCallback } from "react";

function genId(): string {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return genId();
  }
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
}
import ChatWindow from "@/components/chat-window";
import ChatInput from "@/components/chat-input";
import { type Message } from "@/components/message-bubble";
import { sendMessage } from "@/lib/api";

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
      {/* Header */}
      <header className="bg-[var(--color-paper-warm)] border-b border-[var(--color-subtle)] px-4 py-4">
        <div className="mx-auto flex max-w-3xl items-center gap-4">
          <div className="shrink-0">
            <img
              src="/srecko/srecko-avatar.jpg"
              alt="Srecko Kosovel"
              className="h-11 w-11 rounded-full object-cover ring-2 ring-[var(--color-accent)] ring-offset-2 ring-offset-[var(--color-paper-warm)]"
            />
          </div>
          <div className="min-w-0 flex-1">
            <h1 className="font-display text-base font-bold tracking-wide text-[var(--color-ink)] uppercase leading-none">
              Srečko Kosovel
            </h1>
            <p className="mt-1 text-[0.7rem] tracking-wide text-[var(--color-muted)]">
              Pesnik &middot; Kras &middot; 1904–1926
            </p>
          </div>
          <span className="hidden text-[0.65rem] font-medium tracking-[0.18em] text-[var(--color-muted)] uppercase sm:block">
            Avantgarda
          </span>
        </div>
      </header>
      <div className="h-[3px] bg-[var(--color-accent)]" />

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
