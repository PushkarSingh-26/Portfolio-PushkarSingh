"use client";

import { useCallback, useEffect, useRef, useState, type KeyboardEvent, type RefObject } from "react";
import { m } from "motion/react";
import { sigmaStages } from "@/content/sigma";
import { useInViewOnce, usePrefersReducedMotion } from "@/lib/hooks";
import { StageVisual } from "./StageVisuals";
import s from "./sigma.module.css";

const N = sigmaStages.length;
const EASE = [0.2, 0, 0, 1] as const;
/** Horizontal center of node i, as a percentage of the strip width. */
const center = (i: number) => ((i + 0.5) / N) * 100;

const MODEL = sigmaStages.findIndex((st) => st.id === "model");
const BENCHMARK = sigmaStages.findIndex((st) => st.id === "benchmark");

/** Structure of the loop: which stages train, which generate, which evaluate. */
const GROUPS = [
  { label: "Training", from: 0, to: 1 },
  { label: "Generation", from: 2, to: 3 },
  { label: "Evaluation", from: 4, to: 6 },
];

type Flow = { active: number; from: number; n: number };

function markerState(i: number, active: number) {
  return i < active ? "done" : i === active ? "active" : "todo";
}

/* ---------- Node strip (desktop) ---------- */

function NodeStrip({
  flow,
  reduced,
  onSelect,
  nodeRefs,
}: {
  flow: Flow;
  reduced: boolean;
  onSelect: (i: number) => void;
  nodeRefs: RefObject<(HTMLButtonElement | null)[]>;
}) {
  const { active, from, n } = flow;
  const loopOn = active === BENCHMARK;
  const x1 = center(BENCHMARK) * 7;
  const x2 = center(MODEL) * 7;
  const arc = `M${x1} 46 C ${x1} 2, ${x2} 2, ${x2} 46`;
  return (
    <div className={s.strip}>
      {/* The loop: every model in the benchmark takes the same generate-and-check path. */}
      <div className={s.arcWrap}>
        <span className={s.arcLabel} data-active={loopOn}>
          Base and frontier models take the same path
        </span>
        <svg className={s.arcSvg} viewBox="0 0 700 48" preserveAspectRatio="none" aria-hidden="true" focusable="false">
          <path className={s.arcBase} d={arc} />
          <m.path
            className={s.arcLive}
            d={arc}
            initial={false}
            animate={{ pathLength: loopOn ? 1 : 0, opacity: loopOn ? 1 : 0 }}
            transition={{ duration: reduced ? 0 : 0.6, ease: EASE }}
          />
        </svg>
        <svg
          className={s.arcHead}
          style={{ left: `${center(MODEL)}%` }}
          data-active={loopOn}
          viewBox="0 0 12 8"
          aria-hidden="true"
          focusable="false"
        >
          <path d="M1.5 1.5 6 6.5 10.5 1.5" />
        </svg>
      </div>

      <div className={s.track}>
        {sigmaStages.slice(0, -1).map((st, i) => (
          <span
            key={st.id}
            aria-hidden="true"
            className={s.edge}
            data-done={i < active}
            style={{ left: `${center(i)}%`, width: `${100 / N}%` }}
          />
        ))}
        {/* Flow: a pulse travels from the previous stage to the new one. */}
        {!reduced && n > 0 && from !== active && (
          <m.div
            key={n}
            aria-hidden="true"
            className={s.pulseTrack}
            initial={{ x: `${center(from)}%`, opacity: 0 }}
            animate={{ x: `${center(active)}%`, opacity: [0, 1, 1, 0] }}
            transition={{ duration: 0.42, ease: EASE, opacity: { duration: 0.42, times: [0, 0.12, 0.8, 1] } }}
          >
            <span className={s.pulse} />
          </m.div>
        )}
        <ol className={s.nodes} data-node-strip="" aria-label="Pipeline stages">
          {sigmaStages.map((st, i) => (
            <li key={st.id}>
              <button
                ref={(el) => {
                  nodeRefs.current[i] = el;
                }}
                type="button"
                className={s.node}
                data-index={i}
                data-state={markerState(i, active)}
                tabIndex={i === active ? 0 : -1}
                aria-current={i === active ? "step" : undefined}
                onClick={() => onSelect(i)}
              >
                <span className={s.marker} data-state={markerState(i, active)}>
                  {i + 1}
                </span>
                <span>{st.name}</span>
              </button>
            </li>
          ))}
        </ol>
      </div>

      <div className={s.groups} aria-hidden="true">
        {GROUPS.map((g) => (
          <div
            key={g.label}
            className={s.group}
            data-active={active >= g.from && active <= g.to}
            style={{ left: `${center(g.from)}%`, width: `${center(g.to) - center(g.from)}%` }}
          >
            <span className={s.groupLabel}>{g.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function ChevronIcon({ dir }: { dir: "left" | "right" }) {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true" focusable="false">
      <path
        d={dir === "left" ? "M10 3.5 5.5 8 10 12.5" : "M6 3.5 10.5 8 6 12.5"}
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

/* ---------- Mobile stage block ---------- */

function MobileStage({ index, idPrefix }: { index: number; idPrefix: string }) {
  const st = sigmaStages[index];
  const [ref, inView] = useInViewOnce<HTMLLIElement>("0px 0px -30% 0px");
  return (
    <li ref={ref} id={`${idPrefix}-m-${st.id}`} className={s.mStage}>
      <p className={s.stepMeta}>
        <span className={`${s.marker} ${s.markerSm}`} data-state="active" aria-hidden="true">
          {index + 1}
        </span>
        <span>
          <span className="sr-only">Stage {index + 1}: </span>
          {st.name}
        </span>
      </p>
      <h3 className="h-sub mt-4">{st.title}</h3>
      <p className="body-2 measure mt-3">{st.body}</p>
      <div className={s.mPanel}>
        <StageVisual id={st.id} active={inView} />
      </div>
    </li>
  );
}

/* ---------- Pipeline ---------- */

/**
 * The seven stages from public rules to benchmark. Desktop: a sticky diagram
 * whose emphasis follows the step text crossing the middle of the viewport.
 * Mobile: a stepper, one block per stage with its own visual inline.
 */
export function SigmaPipeline({ idPrefix = "sigma", className = "" }: { idPrefix?: string; className?: string }) {
  const reduced = usePrefersReducedMotion();
  const [flow, setFlow] = useState<Flow>({ active: 0, from: 0, n: 0 });
  const stepRefs = useRef<(HTMLLIElement | null)[]>([]);
  const nodeRefs = useRef<(HTMLButtonElement | null)[]>([]);
  /** While a click-initiated scroll is in flight, ignore the steps it passes. */
  const pending = useRef<{ index: number; until: number } | null>(null);

  const activate = useCallback((i: number) => {
    setFlow((f) => (f.active === i ? f : { active: i, from: f.active, n: f.n + 1 }));
  }, []);

  useEffect(() => {
    const els = stepRefs.current.filter((el): el is HTMLLIElement => el != null);
    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          if (!e.isIntersecting) continue;
          const i = Number((e.target as HTMLElement).dataset.index);
          const p = pending.current;
          if (p) {
            if (i === p.index || performance.now() > p.until) pending.current = null;
            else continue;
          }
          activate(i);
        }
      },
      { rootMargin: "-45% 0px -45% 0px" },
    );
    els.forEach((el) => io.observe(el));
    return () => io.disconnect();
  }, [activate]);

  const goTo = useCallback(
    (i: number, focusNode = false) => {
      const t = Math.max(0, Math.min(N - 1, i));
      pending.current = { index: t, until: performance.now() + 1400 };
      activate(t);
      stepRefs.current[t]?.scrollIntoView({ block: "center", behavior: reduced ? "auto" : "smooth" });
      if (focusNode) nodeRefs.current[t]?.focus({ preventScroll: true });
    },
    [activate, reduced],
  );

  const onKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
    const target = e.target as HTMLElement;
    // Leave arrow keys alone inside scrollable machine output.
    if (target.closest("pre")) return;
    const inStrip = target.closest("[data-node-strip]") != null;
    const base = inStrip ? Number(target.dataset.index ?? flow.active) : flow.active;
    let next: number | null = null;
    if (e.key === "ArrowRight") next = base + 1;
    else if (e.key === "ArrowLeft") next = base - 1;
    else if (inStrip && e.key === "Home") next = 0;
    else if (inStrip && e.key === "End") next = N - 1;
    if (next == null) return;
    e.preventDefault();
    if (next < 0 || next >= N) return;
    goTo(next, inStrip);
  };

  const { active } = flow;
  const prev = active > 0 ? sigmaStages[active - 1] : null;
  const next = active < N - 1 ? sigmaStages[active + 1] : null;

  return (
    <div className={className}>
      {/* ---------- Desktop ---------- */}
      <div className="hidden lg:grid lg:grid-cols-12 lg:gap-x-8">
        <div className="lg:col-span-7">
          <div
            className={s.sticky}
            role="group"
            aria-label="Pipeline diagram. Left and right arrow keys move between stages."
            aria-keyshortcuts="ArrowLeft ArrowRight"
            onKeyDown={onKeyDown}
          >
            <NodeStrip flow={flow} reduced={reduced} onSelect={(i) => goTo(i)} nodeRefs={nodeRefs} />

            <div className={s.panel}>
              {sigmaStages.map((st, i) => (
                <div
                  key={st.id}
                  className={s.panelItem}
                  data-active={i === active}
                  inert={i !== active}
                  role="group"
                  aria-label={`${st.name} stage`}
                >
                  <p className={s.panelHead}>
                    <span className="font-semibold">{st.name}</span>
                    <span className="text-ink-2">{st.title}</span>
                  </p>
                  <StageVisual id={st.id} active={i === active} fill />
                </div>
              ))}
            </div>

            <div className={s.controls}>
              <button
                type="button"
                className="btn btn-quiet"
                aria-disabled={prev == null}
                aria-label={prev ? `Previous stage: ${prev.name}` : "Previous stage"}
                onClick={() => prev && goTo(active - 1)}
              >
                <ChevronIcon dir="left" />
                Previous
              </button>
              <p className="small text-ink-2" aria-live="polite">
                Stage {active + 1} of {N}: <span className="font-semibold text-ink">{sigmaStages[active].name}</span>
              </p>
              <button
                type="button"
                className="btn btn-quiet"
                aria-disabled={next == null}
                aria-label={next ? `Next stage: ${next.name}` : "Next stage"}
                onClick={() => next && goTo(active + 1)}
              >
                Next
                <ChevronIcon dir="right" />
              </button>
            </div>
          </div>
        </div>

        <ol className={`${s.steps} lg:col-start-9 lg:col-span-4`}>
          {sigmaStages.map((st, i) => (
            <li
              key={st.id}
              ref={(el) => {
                stepRefs.current[i] = el;
              }}
              id={`${idPrefix}-step-${st.id}`}
              data-index={i}
              data-active={i === active}
              className={s.step}
            >
              <p className={s.stepMeta}>
                <span className={`${s.marker} ${s.markerSm}`} data-state={markerState(i, active)} aria-hidden="true">
                  {i + 1}
                </span>
                <span>
                  <span className="sr-only">Stage {i + 1}: </span>
                  {st.name}
                </span>
              </p>
              <h3 className="h-sub mt-4">{st.title}</h3>
              <p className="body-2 mt-3">{st.body}</p>
            </li>
          ))}
        </ol>
      </div>

      {/* ---------- Mobile ---------- */}
      <div className="lg:hidden">
        <nav aria-label="Pipeline stages" className="scroll-x -mx-1 px-1">
          <ol className={s.overview}>
            {sigmaStages.map((st, i) => (
              <li key={st.id} className={s.overviewItem}>
                <a href={`#${idPrefix}-m-${st.id}`} className={s.overviewLink}>
                  <span className={s.marker} aria-hidden="true">
                    {i + 1}
                  </span>
                  <span>{st.name}</span>
                </a>
              </li>
            ))}
          </ol>
        </nav>
        <ol className={`${s.mStages} mt-6`}>
          {sigmaStages.map((st, i) => (
            <MobileStage key={st.id} index={i} idPrefix={idPrefix} />
          ))}
        </ol>
      </div>
    </div>
  );
}
