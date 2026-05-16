"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import SiteHeader from "@/components/site-header";
import { fetchGameRound, type GameBlankPart, type GameRound } from "@/lib/api";

type PlacementMap = Record<string, string>;

function getBlankIds(round: GameRound): string[] {
  return round.lines
    .flat()
    .filter((part): part is GameBlankPart => part.type === "blank")
    .map((part) => part.blankId);
}

function cx(...classes: Array<string | false | null | undefined>): string {
  return classes.filter(Boolean).join(" ");
}

export default function GamePage() {
  const [round, setRound] = useState<GameRound | null>(null);
  const [placements, setPlacements] = useState<PlacementMap>({});
  const [mistakes, setMistakes] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [draggedWordId, setDraggedWordId] = useState<string | null>(null);
  const [hoverBlankId, setHoverBlankId] = useState<string | null>(null);
  const [wrongBlankId, setWrongBlankId] = useState<string | null>(null);
  const [wrongWordId, setWrongWordId] = useState<string | null>(null);
  const [freshBlankId, setFreshBlankId] = useState<string | null>(null);

  const blankIds = useMemo(() => (round ? getBlankIds(round) : []), [round]);
  const completed = round !== null && blankIds.every((id) => placements[id]);

  const loadRound = useCallback(async () => {
    setLoading(true);
    setError(null);
    setRound(null);
    setPlacements({});
    setMistakes(0);
    setDraggedWordId(null);
    setHoverBlankId(null);
    setWrongBlankId(null);
    setWrongWordId(null);
    setFreshBlankId(null);

    try {
      const data = await fetchGameRound();
      setRound(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Igre ni bilo mogoče naložiti.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadRound();
  }, [loadRound]);

  const attemptPlacement = useCallback(
    (targetBlankId: string, wordBlankId: string) => {
      if (!round || placements[targetBlankId] || placements[wordBlankId]) {
        return;
      }

      if (targetBlankId === wordBlankId) {
        setPlacements((prev) => ({ ...prev, [targetBlankId]: wordBlankId }));
        setFreshBlankId(targetBlankId);
        window.setTimeout(() => setFreshBlankId(null), 520);
        return;
      }

      setMistakes((prev) => prev + 1);
      setWrongBlankId(targetBlankId);
      setWrongWordId(wordBlankId);
      window.setTimeout(() => {
        setWrongBlankId(null);
        setWrongWordId(null);
      }, 620);
    },
    [placements, round],
  );

  const handleWordClick = useCallback(
    (wordBlankId: string) => {
      const firstEmptyBlank = blankIds.find((id) => !placements[id]);
      if (firstEmptyBlank) {
        attemptPlacement(firstEmptyBlank, wordBlankId);
      }
    },
    [attemptPlacement, blankIds, placements],
  );

  const wordByBlankId = useMemo(() => {
    const map = new Map<string, string>();
    round?.words.forEach((word) => map.set(word.blankId, word.word));
    return map;
  }, [round]);

  const remainingWords = useMemo(
    () => round?.words.filter((word) => !placements[word.blankId]) ?? [],
    [placements, round],
  );

  return (
    <main className="min-h-dvh bg-[var(--color-paper)] text-[var(--color-ink)]">
      <SiteHeader activeMode="game" />

      <section className="mx-auto flex min-h-[calc(100dvh-43px)] max-w-5xl flex-col px-4 py-6 sm:px-6 lg:px-8">
        <div className="mb-5 flex flex-wrap items-end justify-between gap-4 border-b border-[var(--color-ink)] pb-4">
          <div>
            <p className="font-display text-[0.6875rem] font-bold tracking-[0.16em] text-[var(--color-accent)] uppercase">
              Manjkajoče besede
            </p>
            <h1 className="mt-2 max-w-3xl font-display text-3xl font-bold tracking-normal sm:text-5xl">
              {round?.title ?? "Nalaganje pesmi"}
            </h1>
            {round && (
              <p className="mt-2 text-sm text-[var(--color-muted)]">
                {round.category}
                {round.url && (
                  <>
                    {" "}
                    /{" "}
                    <a
                      href={round.url}
                      target="_blank"
                      rel="noreferrer"
                      className="underline decoration-[var(--color-subtle)] underline-offset-4 hover:text-[var(--color-accent)]"
                    >
                      vir
                    </a>
                  </>
                )}
              </p>
            )}
          </div>
          <div className="flex items-center gap-3">
            <div className="border border-[var(--color-ink)] bg-[var(--color-paper-warm)] px-3 py-2 font-display text-sm">
              Napake: <span className="font-bold">{mistakes}</span>
            </div>
            <button
              type="button"
              onClick={loadRound}
              className="cursor-pointer border-2 border-[var(--color-ink)] bg-[var(--color-ink)] px-4 py-2 font-display text-sm font-bold text-[var(--color-paper)] transition-all duration-200 hover:border-[var(--color-accent)] hover:bg-[var(--color-accent)] active:scale-[0.97] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-accent)]"
            >
              Nova pesem
            </button>
          </div>
        </div>

        {loading && (
          <div className="grid flex-1 place-items-center py-16 font-display text-sm tracking-[0.16em] text-[var(--color-muted)] uppercase">
            Nalagam krog
          </div>
        )}

        {!loading && error && (
          <div className="my-10 border-2 border-[var(--color-accent)] bg-[var(--color-paper-warm)] p-5">
            <p className="font-display font-bold">Napaka pri nalaganju igre</p>
            <p className="mt-2 text-sm text-[var(--color-muted)]">{error}</p>
          </div>
        )}

        {!loading && round && (
          <>
            <div className="game-poem-sheet flex-1 py-5">
              <div className="max-w-4xl font-display text-[1.35rem] leading-[2.35] sm:text-[1.65rem] sm:leading-[2.45]">
                {round.lines.map((line, lineIndex) => (
                  <div key={`${round.id}-${lineIndex}`} className="min-h-[2.35em]">
                    {line.length === 0 ? (
                      <span>&nbsp;</span>
                    ) : (
                      line.map((part, partIndex) => {
                        if (part.type === "text") {
                          return <span key={`${lineIndex}-${partIndex}`}>{part.text}</span>;
                        }

                        const placedWordId = placements[part.blankId];
                        const placedWord = placedWordId ? wordByBlankId.get(placedWordId) : null;

                        return (
                          <span
                            key={part.blankId}
                            aria-label={placedWord ? `Vstavljena beseda ${placedWord}` : "Prazno mesto"}
                            onDragOver={(event) => {
                              if (!placedWord) {
                                event.preventDefault();
                                setHoverBlankId(part.blankId);
                              }
                            }}
                            onDragLeave={() => setHoverBlankId(null)}
                            onDrop={(event) => {
                              event.preventDefault();
                              const wordId = event.dataTransfer.getData("text/plain") || draggedWordId;
                              setHoverBlankId(null);
                              setDraggedWordId(null);
                              if (wordId) {
                                attemptPlacement(part.blankId, wordId);
                              }
                            }}
                            className={cx(
                              "mx-1 inline-flex min-h-[2.15rem] min-w-24 items-center justify-center border-b-2 px-3 align-baseline transition-all duration-200 sm:min-w-32",
                              placedWord
                                ? "border-[var(--color-ink)] bg-transparent font-bold"
                                : "border-[var(--color-accent)] bg-[var(--color-paper-warm)]/80",
                              hoverBlankId === part.blankId && !placedWord
                                ? "scale-105 border-[var(--color-ink)] bg-[var(--color-accent)] text-[var(--color-paper)] shadow-[0_8px_0_var(--color-ink)]"
                                : null,
                              wrongBlankId === part.blankId ? "animate-game-wrong" : null,
                              freshBlankId === part.blankId ? "animate-game-success" : null,
                            )}
                          >
                            {placedWord ?? ""}
                          </span>
                        );
                      })
                    )}
                  </div>
                ))}
              </div>
            </div>

            <div className="sticky bottom-0 -mx-4 border-t-2 border-[var(--color-ink)] bg-[var(--color-paper)]/95 px-4 py-4 backdrop-blur sm:-mx-6 sm:px-6 lg:-mx-8 lg:px-8">
              {completed ? (
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <p className="font-display text-lg font-bold">
                    Pesem je sestavljena.
                  </p>
                  <button
                    type="button"
                    onClick={loadRound}
                    className="cursor-pointer border-2 border-[var(--color-accent)] bg-[var(--color-accent)] px-4 py-2 font-display text-sm font-bold text-[var(--color-paper)] transition-transform duration-200 active:scale-[0.97] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-accent)]"
                  >
                    Naslednja pesem
                  </button>
                </div>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {remainingWords.map((word) => (
                    <button
                      key={word.blankId}
                      type="button"
                      draggable
                      onClick={() => handleWordClick(word.blankId)}
                      onDragStart={(event) => {
                        setDraggedWordId(word.blankId);
                        event.dataTransfer.setData("text/plain", word.blankId);
                        event.dataTransfer.effectAllowed = "move";
                      }}
                      onDragEnd={() => {
                        setDraggedWordId(null);
                        setHoverBlankId(null);
                      }}
                      className={cx(
                        "cursor-grab border-2 border-[var(--color-ink)] bg-[var(--color-paper-warm)] px-4 py-2 font-display text-base font-bold transition-all duration-200 hover:-translate-y-0.5 hover:bg-[var(--color-ink)] hover:text-[var(--color-paper)] active:cursor-grabbing active:scale-[0.97] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-accent)]",
                        draggedWordId === word.blankId ? "opacity-50" : null,
                        wrongWordId === word.blankId ? "animate-game-wrong" : null,
                      )}
                    >
                      {word.word}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </section>
    </main>
  );
}
