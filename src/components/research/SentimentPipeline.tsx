"use client";

import { useId, useRef, useState, type KeyboardEvent } from "react";
import { sentimentPaper } from "@/content/research";
import { useCanHover, usePrefersReducedMotion } from "@/lib/hooks";
import { StablePanel } from "./StablePanel";
import { VaderRow } from "./VaderRow";
import { researchVars, rovingIndex } from "./tokens";
import styles from "./SentimentPipeline.module.css";

/*
  The paper's methodology (Figure 2) as the sequence it is. Compact: a strip of
  steps with one readout; the data has "flowed" up to the chosen step (ink edges),
  and a pulse runs along the edge into it. Expanded: every step written out.
*/

const { steps } = sentimentPaper;
type Step = (typeof steps)[number];

const DEFAULT_STEP = "vader";

function StepReadout({ step, index }: { step: Step; index: number }) {
  return (
    <div>
      <div className={styles.readHead}>
        <span className={styles.node} data-tone="active" aria-hidden="true">
          {index + 1}
        </span>
        <p className={styles.readName}>
          <span className="sr-only">Step {index + 1}: </span>
          {step.name}
        </p>
      </div>
      <div className={styles.readBody}>
        <p className="small text-ink-2">{step.detail}</p>
        {step.id === "vader" && <VaderRow className={styles.vader} />}
      </div>
    </div>
  );
}

const READOUTS = steps.map((s, i) => ({ key: s.id, node: <StepReadout step={s} index={i} /> }));

export function SentimentPipeline({ mode = "compact" }: { mode?: "compact" | "expanded" }) {
  return mode === "expanded" ? <PipelineList /> : <PipelineStrip />;
}

/* ---------- Compact: interactive strip ---------- */

function PipelineStrip() {
  const uid = useId();
  const panelId = `${uid}-readout`;
  const canHover = useCanHover();
  const reduced = usePrefersReducedMotion();

  const [pinned, setPinned] = useState(DEFAULT_STEP);
  const [preview, setPreview] = useState<string | null>(null);
  const shown = canHover && preview ? preview : pinned;
  const shownIndex = steps.findIndex((s) => s.id === shown);
  const pinnedIndex = Math.max(0, steps.findIndex((s) => s.id === pinned));

  // Flow: each time a different step becomes current, a pulse runs along the edge into it.
  const [pulse, setPulse] = useState(0);
  const [pulsedFor, setPulsedFor] = useState(shown);
  if (pulsedFor !== shown) {
    setPulsedFor(shown);
    setPulse((n) => n + 1);
  }

  const refs = useRef<(HTMLButtonElement | null)[]>([]);

  const pin = (id: string) => {
    setPinned(id);
    setPreview(null);
  };

  const onKey = (e: KeyboardEvent<HTMLButtonElement>, i: number) => {
    const next = rovingIndex(e.key, i, steps.length, "both");
    if (next === null) return;
    e.preventDefault();
    pin(steps[next].id);
    refs.current[next]?.focus();
  };

  const onRootKey = (e: KeyboardEvent<HTMLDivElement>) => {
    if (e.key === "Escape" && (pinned !== DEFAULT_STEP || preview)) pin(DEFAULT_STEP);
  };

  return (
    <div className={styles.root} style={researchVars} onKeyDown={onRootKey}>
      <p className={`small text-ink-2 ${styles.hint}`}>Choose a step to see what it does.</p>
      <ol className={styles.strip} aria-label="Method, in order" onPointerLeave={() => setPreview(null)}>
        {steps.map((s, i) => {
          const state = i < shownIndex ? "done" : i === shownIndex ? "active" : "todo";
          const into = i === shownIndex - 1;
          return (
            <li key={s.id} className={styles.step} data-state={state}>
              <button
                ref={(el) => {
                  refs.current[i] = el;
                }}
                type="button"
                className={styles.stepBtn}
                aria-pressed={shown === s.id}
                aria-controls={panelId}
                tabIndex={i === pinnedIndex ? 0 : -1}
                onClick={() => pin(s.id)}
                onPointerEnter={() => {
                  if (canHover) setPreview(s.id);
                }}
                onKeyDown={(e) => onKey(e, i)}
              >
                <span className={styles.node} data-tone={state} aria-hidden="true">
                  {i + 1}
                </span>
                <span className={styles.name}>{s.name}</span>
              </button>
              {i < steps.length - 1 && (
                <span className={styles.edge} aria-hidden="true">
                  {into && !reduced && pulse > 0 && <span key={pulse} className={styles.flow} />}
                </span>
              )}
            </li>
          );
        })}
      </ol>
      <StablePanel id={panelId} className={styles.panel} variants={READOUTS} active={shown} />
    </div>
  );
}

/* ---------- Expanded: every step written out ---------- */

function PipelineList() {
  return (
    <ol className={styles.list} style={researchVars} aria-label="Method, in order">
      {steps.map((s, i) => (
        <li key={s.id} className={styles.listStep}>
          <span className={styles.node} data-tone="done" aria-hidden="true">
            {i + 1}
          </span>
          <div className={styles.listBody}>
            <p className={styles.listName}>{s.name}</p>
            <p className="body-2 mt-1">{s.detail}</p>
          </div>
        </li>
      ))}
    </ol>
  );
}
