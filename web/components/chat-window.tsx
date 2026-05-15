"use client";

import { useRef, useEffect, useState } from "react";
import MessageBubble, { type Message } from "./message-bubble";
import TypingIndicator from "./typing-indicator";

const ALL_SUGGESTIONS = [
  "Recitiraj pesem Bori",
  "Recitiraj pesem o morju",
  "Recitiraj svojo najljubšo pesem",
  "Katere pesmi omenjajo Kras?",
  "Pesmi o samoti in naravi",
  "Ali imaš pesem o upanju?",
  "Katera pesem govori o osamljenosti?",
  "Pesmi z besedo 'smrt'",
  "Kdo si?",
  "Kaj te je navdihovalo?",
  "Povej mi o konstruktivizmu",
  "Kakšen je bil čas, v katerem si živel?",
];

function pickRandom<T>(arr: T[], n: number): T[] {
  return [...arr].sort(() => Math.random() - 0.5).slice(0, n);
}

interface ChatWindowProps {
  messages: Message[];
  isLoading: boolean;
  onSuggestionClick: (text: string) => void;
}

export default function ChatWindow({
  messages,
  isLoading,
  onSuggestionClick,
}: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const [suggestions, setSuggestions] = useState(ALL_SUGGESTIONS.slice(0, 4));

  useEffect(() => {
    setSuggestions(pickRandom(ALL_SUGGESTIONS, 4));
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const showWelcome = messages.length === 0 && !isLoading;

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="mx-auto max-w-3xl py-6">
        {showWelcome && (
          <div className="flex flex-col items-center px-4 pt-10 pb-6 animate-fade-up">
            {/* Portrait with constructivist double-frame */}
            <div className="relative mb-10 animate-fade-up">
              {/* Outer shadow frame */}
              <div className="absolute -inset-4 border border-[var(--color-subtle)]" />
              {/* Inner ink frame */}
              <div className="absolute -inset-2 border-2 border-[var(--color-ink)]" />
              {/* Offset accent frame */}
              <div className="absolute -inset-2 translate-x-2 translate-y-2 border-2 border-[var(--color-accent)]" />
              <img
                src="/srecko-avatar.jpg"
                alt="Srečko Kosovel — portret"
                className="relative h-32 w-32 object-cover grayscale contrast-[1.05]"
              />
            </div>

            {/* Title block */}
            <div className="mb-5 text-center animate-fade-up-delay">
              <h2 className="font-display text-2xl font-bold uppercase tracking-tight sm:text-3xl">
                Pogovor s Srečkom
              </h2>
              <div className="geo-line mx-auto mt-4 w-40" />
            </div>

            <p className="mx-auto max-w-xs text-center text-sm leading-relaxed text-[var(--color-muted)] animate-fade-up-delay">
              Sem Srečko Kosovel, avantgardni pesnik s Krasa.
              Vprašaj me o mojih pesmih, temah ali mi naroči
              recitacijo.
            </p>

            {/* Suggestion chips */}
            <div className="mt-8 flex flex-wrap justify-center gap-2 animate-fade-up-delay-2">
              {suggestions.map((q) => (
                <button
                  key={q}
                  onClick={() => onSuggestionClick(q)}
                  className="cursor-pointer border border-[var(--color-ink)] bg-[var(--color-paper-warm)] px-4 py-2 font-display text-[0.8125rem] font-medium tracking-tight transition-all duration-200 hover:border-[var(--color-accent)] hover:bg-[var(--color-ink)] hover:text-[var(--color-paper)] active:scale-[0.97] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-accent)]"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="space-y-4">
          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}
        </div>

        {isLoading && (
          <div className="mt-4">
            <TypingIndicator />
          </div>
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  );
}
