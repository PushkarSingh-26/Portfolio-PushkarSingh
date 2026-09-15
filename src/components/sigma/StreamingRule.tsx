"use client";

import { useEffect, useRef, useState } from "react";
import { usePrefersReducedMotion } from "@/lib/hooks";
import s from "./sigma.module.css";

const MS_PER_TOKEN = 12;

/**
 * Stream: the example rule appears token by token, split at real o200k_base
 * boundaries, behind a caret. Starts the first time `start` is true and runs
 * once. Reduced motion shows the full text immediately. A hidden sizer holds
 * the final height so nothing shifts while it streams.
 */
export function StreamingRule({
  tokens,
  start,
  fill = false,
}: {
  tokens: readonly string[];
  start: boolean;
  /** Fill the parent's height and scroll inside (desktop stage panel). */
  fill?: boolean;
}) {
  const reduced = usePrefersReducedMotion();
  const [started, setStarted] = useState(false);
  const [count, setCount] = useState(0);
  const boxRef = useRef<HTMLDivElement | null>(null);
  const caretRef = useRef<HTMLSpanElement | null>(null);
  const total = tokens.length;
  const full = tokens.join("");

  useEffect(() => {
    if (start && !started) setStarted(true);
  }, [start, started]);

  useEffect(() => {
    if (!started || reduced) return;
    let raf = 0;
    let t0 = -1;
    const tick = (t: number) => {
      if (t0 < 0) t0 = t;
      const n = Math.min(total, Math.floor((t - t0) / MS_PER_TOKEN) + 1);
      setCount((c) => Math.max(c, n));
      if (n < total) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [started, reduced, total]);

  const shown = reduced ? total : started ? count : 0;
  const streaming = !reduced && started && shown < total;

  // Keep the caret in view inside the rule box (never scrolls the page).
  useEffect(() => {
    if (!streaming) return;
    const box = boxRef.current;
    const caret = caretRef.current;
    if (!box || !caret || box.scrollHeight <= box.clientHeight) return;
    const bottom = caret.offsetTop + caret.offsetHeight + 24;
    if (bottom > box.scrollTop + box.clientHeight) box.scrollTop = bottom - box.clientHeight;
  }, [shown, streaming]);

  return (
    <div className={`${s.rule} ${fill ? s.ruleFill : ""}`}>
      <p className={s.label}>Hand-written example rule — not model output. Split into real o200k_base tokens.</p>
      <div ref={boxRef} className={s.ruleBox}>
        <span className="sr-only">{full}</span>
        <div className={s.ruleText} aria-hidden="true">
          <pre className={`mono ${s.ruleSizer}`}>{full}</pre>
          <pre className={`mono ${s.ruleLive}`}>
            {tokens.slice(0, shown).map((tok, i) => (
              <span key={i} className={s.t}>
                {tok}
              </span>
            ))}
            {streaming && <span ref={caretRef} className={s.caret} />}
          </pre>
        </div>
      </div>
    </div>
  );
}
