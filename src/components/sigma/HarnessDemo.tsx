"use client";

import { useCallback, useEffect, useId, useMemo, useRef, useState, type KeyboardEvent } from "react";
import { sigmaChecks } from "@/content/sigma";
import { usePrefersReducedMotion } from "@/lib/hooks";
import { CheckRow, FailIcon, PassIcon, type CheckState } from "./CheckParts";
import { reference, ruleFileName, tooling, toolingLine, variants, type Variant } from "./data";
import s from "./sigma.module.css";

const STEP_MS = 220;

/** The summary is derived from the pass flags, never from variant ids. */
function verdict(v: Variant): { pass: boolean; text: string } {
  const c = v.checks;
  if (!c.schema.pass) return { pass: false, text: "Rejected at the first check." };
  if (!c.compile.pass) return { pass: false, text: "Valid Sigma, but it can't become a query." };
  if (!c.fields.pass)
    return { pass: false, text: "It compiles. It still watches the wrong field — only the field check catches it." };
  return { pass: true, text: "Passes all three checks." };
}

const referenceLines = reference.yaml.replace(/\n$/, "").split("\n");

type Run = { ran: boolean; resolved: number };

export function HarnessDemo({
  headingLevel = "h3",
  className = "",
}: {
  headingLevel?: "h2" | "h3";
  className?: string;
}) {
  const Heading = headingLevel;
  const headingId = useId();
  const reduced = usePrefersReducedMotion();
  const [index, setIndex] = useState(0);
  const [run, setRun] = useState<Run>({ ran: false, resolved: 0 });
  const timers = useRef<number[]>([]);
  const radios = useRef<(HTMLButtonElement | null)[]>([]);
  const codeRef = useRef<HTMLDivElement | null>(null);

  const variant = variants[index];
  const lines = useMemo(() => variant.yaml.replace(/\n$/, "").split("\n"), [variant]);
  const changed = useMemo(() => lines.map((l, i) => l !== referenceLines[i]), [lines]);

  const clearTimers = () => {
    timers.current.forEach((t) => window.clearTimeout(t));
    timers.current = [];
  };

  const runChecks = useCallback(() => {
    clearTimers();
    if (reduced) {
      setRun({ ran: true, resolved: sigmaChecks.length });
      return;
    }
    setRun({ ran: true, resolved: 0 });
    for (let k = 1; k <= sigmaChecks.length; k++) {
      timers.current.push(window.setTimeout(() => setRun({ ran: true, resolved: k }), k * STEP_MS));
    }
  }, [reduced]);

  useEffect(() => clearTimers, []);

  // Bring the first changed line into view inside the code box (never scrolls the page).
  useEffect(() => {
    const box = codeRef.current;
    if (!box || box.scrollHeight <= box.clientHeight) return;
    const first = box.querySelector<HTMLElement>("[data-changed='true']");
    box.scrollTop = first ? Math.max(0, first.offsetTop - box.clientHeight / 2) : 0;
  }, [index]);

  const select = (i: number) => {
    if (i === index) return;
    setIndex(i);
    runChecks();
  };

  const onRadioKey = (e: KeyboardEvent<HTMLDivElement>) => {
    const last = variants.length - 1;
    let next: number | null = null;
    if (e.key === "ArrowRight" || e.key === "ArrowDown") next = index === last ? 0 : index + 1;
    else if (e.key === "ArrowLeft" || e.key === "ArrowUp") next = index === 0 ? last : index - 1;
    else if (e.key === "Home") next = 0;
    else if (e.key === "End") next = last;
    if (next == null) return;
    e.preventDefault();
    select(next);
    radios.current[next]?.focus();
  };

  const stateFor = (k: number, pass: boolean): CheckState =>
    !run.ran ? "idle" : k < run.resolved ? (pass ? "pass" : "fail") : "checking";

  const done = run.ran && run.resolved >= sigmaChecks.length;
  const v = verdict(variant);

  return (
    <div className={className}>
      <div className="measure">
        <Heading id={headingId} className="h-sub">
          Try the harness
        </Heading>
        <p className="body-2 mt-3">
          Pick a rule and run it through three checks. Schema and compile results are real sigma-cli output, generated
          while building this page; the field check is a simple comparison written for this demo.
        </p>
      </div>

      <div role="radiogroup" aria-label="Example rule" className={`${s.segmented} mt-8`} onKeyDown={onRadioKey}>
        {variants.map((vr, i) => (
          <button
            key={vr.id}
            ref={(el) => {
              radios.current[i] = el;
            }}
            type="button"
            role="radio"
            aria-checked={i === index}
            tabIndex={i === index ? 0 : -1}
            className={s.segment}
            onClick={() => select(i)}
          >
            {vr.label}
          </button>
        ))}
      </div>

      <div className="mt-8 grid grid-cols-1 gap-x-10 gap-y-10 lg:grid-cols-12">
        {/* Rule */}
        <div className="min-w-0 lg:col-span-7">
          <div className={`${s.changeNote} measure`}>
            <p className="small font-semibold">What changed</p>
            <p className="body-2 small mt-1">
              {variant.change ?? "Nothing. This is the reference rule; each other version changes one line of it."}
            </p>
          </div>
          <div className={`${s.codePanel} mt-5`}>
            <div className={s.codeHead}>
              <code className="mono">{ruleFileName}</code>
              <span className="small text-ink-2">Hand-written example rule</span>
            </div>
            <div
              ref={codeRef}
              className={`scroll-x ${s.codeScroll}`}
              tabIndex={0}
              role="group"
              aria-label={`Rule YAML: ${variant.label}`}
            >
              <pre className={`mono ${s.code}`}>
                <code>
                  {lines.map((ln, i) => (
                    <span key={i} className={s.line} data-changed={changed[i]}>
                      <span className={s.ln} aria-hidden="true">
                        {i + 1}
                      </span>
                      <span className={s.lc}>
                        {ln || " "}
                        {changed[i] && <span className="sr-only"> (changed line)</span>}
                      </span>
                    </span>
                  ))}
                </code>
              </pre>
            </div>
          </div>
        </div>

        {/* Checks */}
        <div className="min-w-0 lg:col-span-5">
          <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
            <button type="button" className="btn btn-primary" onClick={runChecks}>
              Run checks
            </button>
            <p className="small text-ink-2">Picking a rule runs them too.</p>
          </div>

          <div className="mt-6" aria-live="polite">
            <ul className={s.checkList} aria-label={`Checks for: ${variant.label}`}>
              {sigmaChecks.map((c, k) => (
                <CheckRow key={c.id} check={c} variant={variant} state={stateFor(k, variant.checks[c.id].pass)} />
              ))}
            </ul>
            {done ? (
              <p className={`${s.verdict} ${v.pass ? "text-pass" : "text-fail"}`}>
                {v.pass ? <PassIcon /> : <FailIcon />}
                <span className="text-ink">{v.text}</span>
              </p>
            ) : (
              <p className={`${s.verdict} ${s.verdictIdle}`}>
                {run.ran ? "Checking…" : "Not run yet. Press Run checks, or pick a rule."}
              </p>
            )}
          </div>
        </div>
      </div>

      <div className={s.foot}>
        <p className="small text-ink-2">Tooling: {toolingLine}.</p>
        <p className="small text-ink-2">
          Schema check: <code className="mono">{tooling.checkCommand}</code>
        </p>
        <p className="small text-ink-2">
          Compilation: <code className="mono">{tooling.convertCommand}</code>
        </p>
      </div>
    </div>
  );
}
