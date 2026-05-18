export default function TypingIndicator() {
  return (
    <div className="animate-message-in flex items-end gap-3 px-4">
      <img
        src="/srecko-avatar.jpg"
        alt="Srečko Kosovel"
        className="mt-0.5 h-8 w-8 shrink-0 self-start border border-[var(--color-ink)] object-cover grayscale contrast-125"
      />
      <div className="paper-panel border-l-[3px] border-[var(--color-ink)] px-4 py-3">
        <div className="flex items-center gap-1.5">
          <span className="animate-dot-1 h-1.5 w-1.5 rounded-full bg-[var(--color-ink)]" />
          <span className="animate-dot-2 h-1.5 w-1.5 rounded-full bg-[var(--color-ink)]" />
          <span className="animate-dot-3 h-1.5 w-1.5 rounded-full bg-[var(--color-ink)]" />
        </div>
      </div>
    </div>
  );
}
