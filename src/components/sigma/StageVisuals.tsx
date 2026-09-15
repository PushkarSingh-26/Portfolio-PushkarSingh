"use client";

import { useEffect, useId, useState } from "react";
import { m } from "motion/react";
import { sigmaChecks, type SigmaStageId } from "@/content/sigma";
import { usePrefersReducedMotion } from "@/lib/hooks";
import { BenchmarkTable, CheckRow } from "./CheckParts";
import { StreamingRule } from "./StreamingRule";
import { compiledQuery, reference, referenceTokens, ruleFileName, threatDescription, tooling } from "./data";
import s from "./sigma.module.css";

const EASE = [0.2, 0, 0, 1] as const;

/** True from the first time `on` is true. Stage visuals play once, then hold their final state. */
function useLatch(on: boolean) {
  const [latched, setLatched] = useState(false);
  useEffect(() => {
    if (on && !latched) setLatched(true);
  }, [on, latched]);
  return latched || on;
}

/** Reveals `count` items one after another once `trigger` is true. */
function useStagger(trigger: boolean, count: number, stepMs: number, reduced: boolean) {
  const [n, setN] = useState(0);
  useEffect(() => {
    if (!trigger || reduced) return;
    const timers = Array.from({ length: count }, (_, i) =>
      window.setTimeout(() => setN((v) => Math.max(v, i + 1)), (i + 1) * stepMs),
    );
    return () => timers.forEach((t) => window.clearTimeout(t));
  }, [trigger, count, stepMs, reduced]);
  return reduced ? count : n;
}

function ArrowDown({ run, reduced, delay = 0 }: { run: boolean; reduced: boolean; delay?: number }) {
  const t = { duration: reduced ? 0 : 0.42, ease: EASE, delay: reduced ? 0 : delay };
  return (
    <svg className={s.arrowV} viewBox="0 0 24 30" aria-hidden="true" focusable="false">
      <m.path d="M12 1 V27" initial={false} animate={{ pathLength: run ? 1 : 0 }} transition={t} />
      <m.path
        d="M7 22 L12 27 L17 22"
        initial={false}
        animate={{ opacity: run ? 1 : 0 }}
        transition={{ ...t, delay: reduced ? 0 : delay + 0.3 }}
      />
    </svg>
  );
}

/* ---------- 1. Data: category-level held-out split ---------- */

const COUNTS = [8, 5, 7, 4, 6, 5];
const HELD = [1, 4];
const TRAIN = COUNTS.map((_, i) => i).filter((i) => !HELD.includes(i));
const COL_W = 36;
const ROW = 15;
const BLOCK_H = 11;
const BASE_Y = 140;

function startX(i: number) {
  return 10 + i * 56;
}
function finalX(i: number) {
  const h = HELD.indexOf(i);
  if (h >= 0) return 262 + h * 48;
  return 10 + TRAIN.indexOf(i) * 48;
}

function DataVisual({ active, reduced }: { active: boolean; reduced: boolean }) {
  const run = useLatch(active) || reduced;
  const hatch = `hatch-${useId().replace(/[^a-zA-Z0-9_-]/g, "")}`;
  const trainEnd = finalX(TRAIN[TRAIN.length - 1]) + COL_W;
  const heldStart = finalX(HELD[0]);
  const heldEnd = finalX(HELD[HELD.length - 1]) + COL_W;
  const fade = { duration: reduced ? 0 : 0.36, ease: EASE, delay: reduced ? 0 : 0.42 };
  return (
    <figure>
      <svg
        className={s.dataSvg}
        viewBox="0 0 360 196"
        role="img"
        aria-label="Illustration: a rule corpus drawn as six category columns of small blocks. Two whole columns are hatched and pulled aside as held out."
      >
        <defs>
          <pattern id={hatch} width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
            <line x1="0" y1="0" x2="0" y2="5" className={s.hatch} />
          </pattern>
        </defs>
        {COUNTS.map((count, i) => {
          const held = HELD.includes(i);
          return (
            <m.g
              key={i}
              initial={false}
              animate={{ x: run ? finalX(i) : startX(i), y: run && held ? -6 : 0 }}
              transition={{ duration: reduced ? 0 : 0.56, ease: EASE, delay: reduced ? 0 : held ? 0.06 : 0 }}
            >
              {Array.from({ length: count }, (_, b) => (
                <rect
                  key={b}
                  x={0}
                  y={BASE_Y - (b + 1) * ROW + (ROW - BLOCK_H)}
                  width={COL_W}
                  height={BLOCK_H}
                  className={held ? s.blockHeld : s.block}
                  fill={held ? `url(#${hatch})` : undefined}
                />
              ))}
            </m.g>
          );
        })}
        <m.g initial={false} animate={{ opacity: run ? 1 : 0 }} transition={fade}>
          <path className={s.bracket} d={`M10 150 V156 H${trainEnd} V150`} />
          <text className={s.svgLabel} x={(10 + trainEnd) / 2} y={176} textAnchor="middle">
            Training
          </text>
          <path className={`${s.bracket} ${s.bracketDim}`} d={`M${heldStart} 150 V156 H${heldEnd} V150`} />
          <text className={`${s.svgLabel} ${s.svgLabelDim}`} x={(heldStart + heldEnd) / 2} y={176} textAnchor="middle">
            Held out
          </text>
        </m.g>
      </svg>
      <figcaption className={s.caption}>Illustration: whole categories are held out of training.</figcaption>
    </figure>
  );
}

/* ---------- 2. QLoRA: frozen quantized base + trained low-rank adapters ---------- */

const LAYERS = [0, 1, 2, 3, 4, 5];

function QloraVisual({ active, reduced }: { active: boolean; reduced: boolean }) {
  const run = useLatch(active) || reduced;
  return (
    <figure>
      <div className={s.qRow}>
        <div className={s.qBase}>
          <div className={s.qHead}>
            <span className="font-semibold">Base model weights</span>
            <span className="text-ink-2">Frozen, 4-bit</span>
          </div>
          <ul className={s.qList} aria-hidden="true">
            {LAYERS.map((l) => (
              <li key={l} className={s.qLayer} />
            ))}
          </ul>
        </div>
        <div className={s.qAdCol}>
          <div className={s.qHead}>
            <span className="font-semibold">Low-rank adapters</span>
            <span className="text-ink-2">Trained</span>
          </div>
          <ul className={s.qList} aria-hidden="true">
            {LAYERS.map((l) => (
              <li key={l} className={s.qAdRow}>
                <span className={s.qConnector} />
                <m.span
                  className={s.qAdapter}
                  initial={false}
                  animate={{ opacity: run ? 1 : 0, scaleX: run ? 1 : 0.3 }}
                  transition={{ duration: reduced ? 0 : 0.36, ease: EASE, delay: reduced ? 0 : 0.12 + l * 0.06 }}
                />
              </li>
            ))}
          </ul>
        </div>
      </div>
      <figcaption className={s.caption}>
        Illustration: the base weights stay frozen in quantized form; only the small adapters are trained.
      </figcaption>
    </figure>
  );
}

/* ---------- 3. Model: threat description in, rule out ---------- */

function ModelVisual({ active, reduced }: { active: boolean; reduced: boolean }) {
  const run = useLatch(active) || reduced;
  return (
    <div className={s.flowCol}>
      <figure className={s.box}>
        <figcaption className={s.label}>Threat description (example input)</figcaption>
        <p className="mt-1.5">{threatDescription}</p>
      </figure>
      <ArrowDown run={run} reduced={reduced} />
      <div className={`${s.box} flex flex-wrap items-center gap-x-2 gap-y-1`}>
        <span className="font-semibold">Open-weight LLM</span>
        <span aria-hidden="true" className="text-ink-2">
          +
        </span>
        <span className="sr-only">plus</span>
        <span className="tok tok-llm small font-semibold">adapters</span>
      </div>
      <ArrowDown run={run} reduced={reduced} delay={0.3} />
      <div className={`${s.box} ${s.boxDim}`}>
        <span className="font-semibold">A Sigma rule, in YAML</span>
        <span className={`${s.label} block`}>Written token by token in the next stage</span>
      </div>
    </div>
  );
}

/* ---------- 5. Compiler: the rule goes through sigma-cli ---------- */

function CompilerVisual({ active, reduced }: { active: boolean; reduced: boolean }) {
  const run = useLatch(active) || reduced;
  return (
    <div className={s.flowCol}>
      <div className={s.box}>
        <span className={`${s.label} block`}>Hand-written example rule</span>
        <code className={`mono ${s.machine}`}>{ruleFileName}</code>
      </div>
      <ArrowDown run={run} reduced={reduced} />
      <div className={`${s.box} ${s.boxInk}`}>
        <code className="mono font-semibold">sigma-cli</code>
        <span className={`${s.label} block mt-1`}>Command</span>
        <pre className={`mono ${s.machine} ${s.machineBlock}`}>{tooling.convertCommand}</pre>
      </div>
      <ArrowDown run={run} reduced={reduced} delay={0.3} />
      <div className={s.box}>
        <span className={`${s.label} block`}>Splunk query (real output)</span>
        <pre className={`mono ${s.machine} ${s.machineBlock}`}>{compiledQuery(reference)}</pre>
      </div>
    </div>
  );
}

/* ---------- 6. Validation: three checks on the valid example ---------- */

function ValidationVisual({ active, reduced }: { active: boolean; reduced: boolean }) {
  const run = useLatch(active);
  const shown = useStagger(run, sigmaChecks.length, 220, reduced);
  return (
    <div>
      <p className={`${s.label} mb-3`}>The three checks, run on the hand-written example rule. Open a row for the real output.</p>
      <ul className={s.checkList}>
        {sigmaChecks.map((c, i) => (
          <CheckRow key={c.id} check={c} variant={reference} state={i < shown ? (reference.checks[c.id].pass ? "pass" : "fail") : "checking"} />
        ))}
      </ul>
    </div>
  );
}

/* ---------- Switch ---------- */

export function StageVisual({ id, active, fill = false }: { id: SigmaStageId; active: boolean; fill?: boolean }) {
  const reduced = usePrefersReducedMotion();
  switch (id) {
    case "data":
      return <DataVisual active={active} reduced={reduced} />;
    case "qlora":
      return <QloraVisual active={active} reduced={reduced} />;
    case "model":
      return <ModelVisual active={active} reduced={reduced} />;
    case "rule":
      return <StreamingRule tokens={referenceTokens} start={active} fill={fill} />;
    case "compiler":
      return <CompilerVisual active={active} reduced={reduced} />;
    case "validation":
      return <ValidationVisual active={active} reduced={reduced} />;
    case "benchmark":
      return <BenchmarkTable />;
  }
}
