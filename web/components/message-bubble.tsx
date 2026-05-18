import ReactMarkdown from "react-markdown";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

export default function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";
  const isError = !isUser && message.content.startsWith("Napaka:");

  return (
    <div
      className={`animate-message-in flex items-end gap-3 px-4 ${
        isUser ? "flex-row-reverse" : ""
      }`}
    >
      {/* Avatar — only for assistant */}
      {!isUser && (
        <img
          src="/srecko-avatar.jpg"
          alt="Srečko Kosovel"
          className="mt-0.5 h-8 w-8 shrink-0 self-start border border-[var(--color-ink)] object-cover grayscale contrast-125"
        />
      )}

      <div
        className={`max-w-[80%] px-4 py-3 ${
          isUser
            ? "border border-[var(--color-ink)] bg-[var(--color-ink)] text-[var(--color-paper)]"
            : isError
            ? "border-l-[3px] border-[var(--color-ink)] bg-[rgba(229,220,203,0.68)] opacity-80"
            : "paper-panel border-l-[3px] border-[var(--color-ink)]"
        }`}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap text-[0.9375rem] leading-relaxed">
            {message.content}
          </p>
        ) : isError ? (
          <p className="text-sm leading-relaxed text-[var(--color-ink)] italic">
            {message.content}
          </p>
        ) : (
          <div className="prose prose-stone prose-sm max-w-none leading-relaxed prose-p:my-1.5 prose-hr:my-4 prose-strong:font-semibold prose-strong:text-[var(--color-ink)] prose-em:text-[var(--color-ink)] prose-headings:font-display prose-headings:text-[var(--color-ink)]">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}
