import ReactMarkdown from "react-markdown";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

export default function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";

  return (
    <div
      className={`animate-message-in flex items-end gap-3 px-4 ${
        isUser ? "flex-row-reverse" : ""
      }`}
    >
      {/* Avatar — only for assistant */}
      {!isUser && (
        <img
          src="/srecko/srecko-avatar.jpg"
          alt="Srečko Kosovel"
          className="h-8 w-8 shrink-0 self-start rounded-full border-2 border-[var(--color-ink)] object-cover grayscale mt-0.5"
        />
      )}

      {/* Bubble */}
      <div
        className={`max-w-[80%] px-4 py-3 ${
          isUser
            ? "rounded-2xl rounded-br-sm bg-[var(--color-ink)] text-[var(--color-paper)] shadow-sm"
            : "border-l-[3px] border-[var(--color-accent)] bg-[var(--color-paper-warm)] shadow-[2px_2px_0_var(--color-subtle)]"
        }`}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap text-[0.9375rem] leading-relaxed">
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
