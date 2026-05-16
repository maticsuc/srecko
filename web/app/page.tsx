"use client";

import { useState, useCallback } from "react";
import ChatWindow from "@/components/chat-window";
import ChatInput from "@/components/chat-input";
import SiteHeader from "@/components/site-header";
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
      <SiteHeader activeMode="chat" />

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
