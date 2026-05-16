type SiteHeaderProps = {
  activeMode: "chat" | "game";
};

const modes = [
  {
    id: "chat",
    href: "/",
    label: "Chat",
    description: "Pogovor",
    ariaLabel: "Odpri pogovor",
  },
  {
    id: "game",
    href: "/game",
    label: "Igra",
    description: "Dopolni verze",
    ariaLabel: "Odpri igro",
  },
] as const;

export default function SiteHeader({ activeMode }: SiteHeaderProps) {
  return (
    <>
      <header className="border-b border-[var(--color-ink)] px-4 py-2">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-4">
          <a
            href="/"
            className="font-display text-[0.6875rem] font-bold tracking-[0.18em] text-[var(--color-ink)] uppercase transition-colors duration-150 hover:text-[var(--color-accent)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-accent)]"
            aria-label="Pojdi domov"
          >
            Srečko Kosovel
          </a>

          <nav
            aria-label="Način"
            className="flex items-center gap-2 font-display text-[0.6875rem] tracking-[0.12em] uppercase"
          >
            {modes.map((mode) => {
              const isActive = mode.id === activeMode;

              return (
                <a
                  key={mode.id}
                  href={mode.href}
                  aria-label={mode.ariaLabel}
                  aria-current={isActive ? "page" : undefined}
                  className={[
                    "group inline-flex min-h-9 items-center gap-2 border-2 px-3 py-1 font-bold shadow-[3px_3px_0_var(--color-ink)] transition-all duration-150 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[var(--color-accent)] active:translate-x-0.5 active:translate-y-0.5 active:shadow-[1px_1px_0_var(--color-ink)]",
                    isActive
                      ? "border-[var(--color-ink)] bg-[var(--color-ink)] text-[var(--color-paper)]"
                      : "border-[var(--color-ink)] bg-[var(--color-accent)] text-[var(--color-paper)] hover:-translate-y-0.5 hover:shadow-[4px_4px_0_var(--color-ink)]",
                  ].join(" ")}
                >
                  <span
                    className={[
                      "h-3 w-3 border border-[var(--color-paper)] transition-colors duration-150",
                      isActive
                        ? "bg-[var(--color-accent)]"
                        : "bg-[var(--color-ink)] group-hover:bg-[var(--color-paper)]",
                    ].join(" ")}
                  />
                  <span>{mode.label}</span>
                  <span className="hidden border-l border-[rgba(245,242,237,0.55)] pl-2 text-[0.56rem] font-semibold tracking-[0.14em] text-[rgba(245,242,237,0.82)] sm:inline">
                    {mode.description}
                  </span>
                </a>
              );
            })}
          </nav>
        </div>
      </header>
      <div className="h-[2px] bg-[var(--color-accent)]" />
    </>
  );
}
