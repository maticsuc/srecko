"use client";

import { useState, useRef, useCallback } from "react";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export default function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const submit = useCallback(() => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }, [value, disabled, onSend]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setValue(e.target.value);
    const el = e.target;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 150) + "px";
  };

  return (
    <div className="border-t border-[rgba(17,16,14,0.28)] bg-[var(--color-paper)]/88 px-4 py-4 backdrop-blur-[1px]">
      <div className="mx-auto flex max-w-3xl items-end gap-3">
        <div className="paper-panel flex flex-1 items-end transition-all duration-200 focus-within:shadow-[0_0_0_2px_var(--color-ink)]">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            disabled={disabled}
            placeholder="Vprašaj Srečka..."
            rows={1}
            className="flex-1 resize-none bg-transparent px-4 py-3 text-[0.9375rem] leading-relaxed outline-none placeholder:text-[var(--color-subtle)] disabled:opacity-40"
          />
        </div>
        <button
          onClick={submit}
          disabled={disabled || !value.trim()}
          aria-label="Pošlji sporočilo"
          className="cursor-pointer shrink-0 flex h-[46px] w-[46px] items-center justify-center border border-[var(--color-ink)] bg-[var(--color-ink)] text-[var(--color-paper)] transition-all duration-150 hover:bg-transparent hover:text-[var(--color-ink)] active:scale-95 disabled:cursor-not-allowed disabled:opacity-25 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-ink)]"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 20 20"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="square"
            strokeLinejoin="miter"
            className="h-5 w-5"
            aria-hidden="true"
          >
            <path d="M10 16V4M4 10l6-6 6 6" />
          </svg>
        </button>
      </div>
    </div>
  );
}
