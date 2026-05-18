"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import SiteHeader from "@/components/site-header";
import { fetchOpus, type OpusCategory, type OpusWork } from "@/lib/api";

function cx(...classes: Array<string | false | null | undefined>): string {
  return classes.filter(Boolean).join(" ");
}

function normalizeSearch(value: string): string {
  return value.trim().toLocaleLowerCase("sl-SI");
}

function workMatches(work: OpusWork, query: string): boolean {
  if (!query) {
    return true;
  }

  return (
    work.title.toLocaleLowerCase("sl-SI").includes(query) ||
    work.content.toLocaleLowerCase("sl-SI").includes(query)
  );
}

export default function OpusPage() {
  const [categories, setCategories] = useState<OpusCategory[]>([]);
  const [selectedCategorySlug, setSelectedCategorySlug] = useState<string | null>(null);
  const [selectedWorkId, setSelectedWorkId] = useState<number | null>(null);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadOpus() {
      setLoading(true);
      setError(null);

      try {
        const data = await fetchOpus();
        if (!cancelled) {
          setCategories(data.categories);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Opusa ni bilo mogoče naložiti.");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadOpus();

    return () => {
      cancelled = true;
    };
  }, []);

  const query = useMemo(() => normalizeSearch(search), [search]);

  const filteredCategories = useMemo(() => {
    return categories
      .map((category) => ({
        ...category,
        works: category.works.filter((work) => workMatches(work, query)),
      }))
      .filter((category) => category.works.length > 0);
  }, [categories, query]);

  const selectedCategory = useMemo(() => {
    if (!selectedCategorySlug) {
      return null;
    }

    return categories.find((category) => category.slug === selectedCategorySlug) ?? null;
  }, [categories, selectedCategorySlug]);

  const selectedFilteredCategory = useMemo(() => {
    if (!selectedCategorySlug) {
      return null;
    }

    return filteredCategories.find((category) => category.slug === selectedCategorySlug) ?? null;
  }, [filteredCategories, selectedCategorySlug]);

  const selectedWork = useMemo(() => {
    if (!selectedCategory || selectedWorkId === null) {
      return null;
    }

    return selectedCategory.works.find((work) => work.id === selectedWorkId) ?? null;
  }, [selectedCategory, selectedWorkId]);

  const visibleWorkCount = useMemo(() => {
    return filteredCategories.reduce((total, category) => total + category.works.length, 0);
  }, [filteredCategories]);

  useEffect(() => {
    if (!selectedCategorySlug || categories.length === 0) {
      return;
    }

    if (!categories.some((category) => category.slug === selectedCategorySlug)) {
      setSelectedCategorySlug(null);
      setSelectedWorkId(null);
    }
  }, [categories, selectedCategorySlug]);

  useEffect(() => {
    if (!selectedCategorySlug) {
      return;
    }

    if (!selectedFilteredCategory) {
      setSelectedWorkId(null);
      return;
    }

    if (
      selectedWorkId !== null &&
      !selectedFilteredCategory.works.some((work) => work.id === selectedWorkId)
    ) {
      setSelectedWorkId(null);
    }
  }, [selectedCategorySlug, selectedFilteredCategory, selectedWorkId]);

  const selectCategory = useCallback((slug: string) => {
    setSelectedCategorySlug(slug);
    setSelectedWorkId(null);
  }, []);

  const clearSelection = useCallback(() => {
    setSelectedCategorySlug(null);
    setSelectedWorkId(null);
  }, []);

  return (
    <main className="min-h-dvh bg-[var(--color-paper)] text-[var(--color-ink)]">
      <SiteHeader activeMode="opus" />

      <section className="mx-auto min-h-[calc(100dvh-43px)] max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
        <div className="mb-5 grid gap-4 border-b-2 border-[var(--color-ink)] pb-5 lg:grid-cols-[1fr_21rem] lg:items-end">
          <div>
            <p className="font-display text-[0.6875rem] font-bold tracking-[0.16em] text-[#b0221b] uppercase">
              Celotni korpus
            </p>
            <h1 className="mt-2 font-display text-3xl font-bold tracking-normal sm:text-5xl">
              Kosovelov opus
            </h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-[var(--color-muted)]">
              {loading
                ? "Nalagam arhiv del."
                : `${visibleWorkCount} del v ${filteredCategories.length} zbirkah`}
            </p>
          </div>

          <label className="block">
            <span className="mb-2 block font-display text-[0.6875rem] font-bold tracking-[0.14em] uppercase">
              Iskanje
            </span>
            <input
              type="search"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Naslov ali vsebina"
              className="h-11 w-full border-2 border-[var(--color-ink)] bg-[var(--color-paper-warm)] px-3 font-display text-sm outline-none transition-colors placeholder:text-[var(--color-muted)] focus:bg-[var(--color-paper)] focus:ring-2 focus:ring-[#b0221b]"
            />
          </label>
        </div>

        {loading && (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3" aria-hidden="true">
            {Array.from({ length: 6 }).map((_, index) => (
              <div
                key={index}
                className="h-32 animate-pulse border-2 border-[rgba(17,16,14,0.26)] bg-[rgba(229,220,203,0.65)]"
              />
            ))}
          </div>
        )}

        {!loading && error && (
          <div className="border-2 border-[#b0221b] bg-[var(--color-paper-warm)] p-5">
            <p className="font-display font-bold">Napaka pri nalaganju opusa</p>
            <p className="mt-2 text-sm text-[var(--color-muted)]">{error}</p>
          </div>
        )}

        {!loading && !error && filteredCategories.length === 0 && (
          <div className="border-2 border-[var(--color-ink)] bg-[var(--color-paper-warm)] p-5">
            <p className="font-display font-bold">Ni zadetkov</p>
            <p className="mt-2 text-sm text-[var(--color-muted)]">
              Poskusite z drugim naslovom ali izrazom iz besedila.
            </p>
          </div>
        )}

        {!loading && !error && filteredCategories.length > 0 && !selectedCategorySlug && (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {filteredCategories.map((category, index) => (
              <button
                key={category.slug}
                type="button"
                onClick={() => selectCategory(category.slug)}
                className="group min-h-36 cursor-pointer border-2 border-[var(--color-ink)] bg-[var(--color-paper)] p-4 text-left transition-all duration-150 hover:-translate-y-0.5 hover:bg-[var(--color-paper-warm)] hover:shadow-[6px_6px_0_var(--color-ink)] focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#b0221b] active:translate-y-0"
              >
                <div className="flex items-start justify-between gap-3">
                  <span className="border border-[var(--color-ink)] bg-[#b0221b] px-2 py-1 font-display text-[0.625rem] font-bold text-[var(--color-paper)]">
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  <span className="font-display text-[0.75rem] font-bold tracking-[0.12em] uppercase text-[var(--color-muted)]">
                    {category.works.length} del
                  </span>
                </div>
                <h2 className="mt-8 font-display text-xl font-bold leading-tight">
                  {category.name}
                </h2>
                {query && category.works.length !== category.workCount && (
                  <p className="mt-2 text-xs text-[var(--color-muted)]">
                    {category.works.length} od {category.workCount} zadetkov
                  </p>
                )}
                <div className="mt-4 h-2 w-24 bg-[var(--color-ink)] transition-all duration-150 group-hover:w-32 group-hover:bg-[#b0221b]" />
              </button>
            ))}
          </div>
        )}

        {!loading && !error && selectedCategorySlug && selectedCategory && (
          <div className="grid gap-5 lg:grid-cols-[20rem_1fr]">
            <aside className="lg:sticky lg:top-5 lg:self-start">
              <div className="mb-3 flex items-center justify-between gap-3 border-b border-[var(--color-ink)] pb-3">
                <button
                  type="button"
                  onClick={clearSelection}
                  className="cursor-pointer border border-[var(--color-ink)] bg-[var(--color-paper-warm)] px-3 py-2 font-display text-[0.75rem] font-bold uppercase tracking-[0.1em] transition-colors hover:bg-[var(--color-ink)] hover:text-[var(--color-paper)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#b0221b]"
                >
                  Zbirke
                </button>
                <span className="font-display text-[0.6875rem] font-bold tracking-[0.14em] uppercase text-[var(--color-muted)]">
                  {selectedFilteredCategory?.works.length ?? 0}/{selectedCategory.workCount}
                </span>
              </div>

              <h2 className="mb-3 font-display text-2xl font-bold leading-tight">
                {selectedCategory.name}
              </h2>

              <div className="max-h-[62dvh] overflow-y-auto border-y-2 border-[var(--color-ink)]">
                {(selectedFilteredCategory?.works ?? []).map((work) => (
                  <button
                    key={work.id}
                    type="button"
                    onClick={() => setSelectedWorkId(work.id)}
                    className={cx(
                      "grid w-full cursor-pointer grid-cols-[3.25rem_1fr] border-b border-[rgba(17,16,14,0.22)] text-left font-display text-sm transition-colors last:border-b-0 focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-[#b0221b]",
                      selectedWorkId === work.id
                        ? "bg-[var(--color-ink)] text-[var(--color-paper)]"
                        : "bg-transparent hover:bg-[var(--color-paper-warm)]",
                    )}
                  >
                    <span className="border-r border-current px-2 py-3 text-[0.6875rem] opacity-70">
                      {work.id}
                    </span>
                    <span className="px-3 py-3 leading-5">{work.title}</span>
                  </button>
                ))}
              </div>
            </aside>

            <article className="min-h-[28rem] border-l-2 border-[var(--color-ink)] pl-5">
              {!selectedWork && (
                <div className="flex min-h-[24rem] items-center border-y-2 border-[var(--color-ink)]">
                  <p className="max-w-md font-display text-2xl font-bold leading-tight text-[var(--color-muted)]">
                    Izberite naslov za branje celotnega besedila.
                  </p>
                </div>
              )}

              {selectedWork && (
                <>
                  <header className="border-b-2 border-[var(--color-ink)] pb-4">
                    <div className="flex flex-wrap items-center gap-2 font-display text-[0.6875rem] font-bold tracking-[0.14em] uppercase">
                      <span className="bg-[#b0221b] px-2 py-1 text-[var(--color-paper)]">
                        {selectedWork.category}
                      </span>
                      <span>{selectedWork.wordCount ?? 0} besed</span>
                      {selectedWork.url && (
                        <a
                          href={selectedWork.url}
                          target="_blank"
                          rel="noreferrer"
                          className="underline decoration-[var(--color-subtle)] underline-offset-4 hover:text-[#b0221b]"
                        >
                          Wikisource
                        </a>
                      )}
                    </div>
                    <h2 className="mt-4 font-display text-3xl font-bold leading-tight sm:text-5xl">
                      {selectedWork.title}
                    </h2>
                  </header>

                  <div className="opus-reader whitespace-pre-wrap py-6 font-display text-[1.05rem] leading-8 sm:text-[1.18rem] sm:leading-9">
                    {selectedWork.content}
                  </div>
                </>
              )}
            </article>
          </div>
        )}
      </section>
    </main>
  );
}
