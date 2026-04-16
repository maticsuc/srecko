export default function TypingIndicator() {
  return (
    <div className="animate-message-in flex items-end gap-3 px-4">
      <img
        src="/srecko/srecko-avatar.jpg"
        alt="Srečko Kosovel"
        className="h-8 w-8 shrink-0 self-start rounded-full border-2 border-[var(--color-ink)] object-cover grayscale mt-0.5"
      />
      <div className="border-l-[3px] border-[var(--color-accent)] bg-[var(--color-paper-warm)] px-4 py-3 shadow-[2px_2px_0_var(--color-subtle)]">
        <div className="flex items-center gap-1.5">
          <span className="animate-dot-1 h-1.5 w-1.5 rounded-full bg-[var(--color-ink)]" />
          <span className="animate-dot-2 h-1.5 w-1.5 rounded-full bg-[var(--color-ink)]" />
          <span className="animate-dot-3 h-1.5 w-1.5 rounded-full bg-[var(--color-ink)]" />
        </div>
      </div>
    </div>
  );
}
