"use client";

import { m } from "motion/react";
import {
  useCallback,
  useEffect,
  useId,
  useMemo,
  useReducer,
  useRef,
  useState,
  type KeyboardEvent,
} from "react";
import {
  alertPlan,
  ledger,
  planAfter,
  sampleAlert,
  stageIndex,
  stages,
  type GateAction,
  type Provider,
  type StageId,
} from "@/content/aegis";
import { EvidenceQuote } from "@/components/ui/Evidence";
import { useCanHover, usePrefersReducedMotion } from "@/lib/hooks";
import { AlertArtifact, CorrelationArtifact, EvidenceArtifact, GraphArtifact, RiskArtifact } from "./Artifacts";
import { AnalystArtifact } from "./AnalystArtifact";
import { JourneyRail } from "./JourneyRail";
import { AuditLog, GateArtifact, RecommendationArtifact, ResponseArtifact } from "./ResponseArtifacts";
import { initialSim, simReducer } from "./responseSim";
import { InlineText, JourneyCtx, Refs, useJourney, type JourneyCtxValue } from "./shared";
import styles from "./Journey.module.css";

const LAST = stages.length - 1;
const REC = stageIndex.recommendation;
const PLAN_TOTAL = alertPlan.length + planAfter.length;

const clockTime = (d: Date) => d.toLocaleTimeString("en-GB", { hour12: false });

/**
 * Follow one alert through AegisAI, stage by stage. Nothing advances on its own.
 * The case file keeps every artifact (earlier ones collapse to a line with their
 * citations); the evidence ledger only grows; the approval gate and audit log are
 * a browser simulation of the documented state machine.
 */
export function InvestigationJourney() {
  const reduced = usePrefersReducedMotion();
  const canHover = useCanHover();
  const prefix = "aegis" + useId().replace(/[^a-zA-Z0-9]/g, "");

  const [nav, setNav] = useState({ current: 0, from: 0, reached: 0, tick: 0 });
  const [fresh, setFresh] = useState<ReadonlySet<StageId>>(() => new Set());
  const [provider, setProvider] = useState<Provider>("none");
  const [planRun, setPlanRun] = useState(0);
  const [preview, setPreview] = useState<number | null>(null);
  const [pinned, setPinned] = useState<number | null>(null);
  const [sim, dispatch] = useReducer(simReducer, initialSim);
  const [acted, setActed] = useState(false);

  const scrollPending = useRef(false);
  const itemRefs = useRef<Partial<Record<StageId, HTMLLIElement | null>>>({});
  const runTimer = useRef<number | null>(null);

  const animate = !reduced && (nav.tick > 0 || acted);

  const goTo = (target: number) => {
    const i = Math.min(Math.max(target, 0), LAST);
    if (i === nav.current) return;
    const reached = Math.max(nav.reached, i);
    if (reached > nav.reached) setFresh(new Set(stages.slice(nav.reached + 1, reached + 1).map((s) => s.id)));
    setNav({ current: i, from: nav.current, reached, tick: nav.tick + 1 });
    if (reached >= REC) dispatch({ type: "generate", time: clockTime(new Date()) });
    scrollPending.current = true;
  };

  // Bring the newly opened stage into view if it's off screen.
  useEffect(() => {
    if (!scrollPending.current) return;
    scrollPending.current = false;
    const el = itemRefs.current[stages[nav.current].id];
    if (!el) return;
    const top = el.getBoundingClientRect().top;
    if (top < 64 || top > window.innerHeight * 0.72) {
      el.scrollIntoView({ block: "start", behavior: reduced ? "auto" : "smooth" });
    }
  }, [nav.current, reduced]);

  const stopRun = useCallback(() => {
    if (runTimer.current != null) window.clearInterval(runTimer.current);
    runTimer.current = null;
  }, []);
  useEffect(() => stopRun, [stopRun]);
  useEffect(() => {
    if (planRun >= PLAN_TOTAL) stopRun();
  }, [planRun, stopRun]);

  const runNext = () => {
    stopRun();
    setActed(true);
    setPlanRun((r) => Math.min(r + 1, PLAN_TOTAL));
  };
  const runAll = () => {
    stopRun();
    setActed(true);
    if (reduced) {
      setPlanRun(PLAN_TOTAL);
      return;
    }
    setPlanRun((r) => Math.min(r + 1, PLAN_TOTAL));
    runTimer.current = window.setInterval(() => setPlanRun((r) => Math.min(r + 1, PLAN_TOTAL)), 170);
  };

  const onAct = (action: GateAction) => {
    const d = new Date();
    setActed(true);
    dispatch({ type: "act", action, time: clockTime(d), iso: d.toISOString().slice(0, 19) });
  };
  const onReset = () => {
    setActed(true);
    dispatch({ type: "reset", time: clockTime(new Date()) });
  };

  const onKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
    if (e.defaultPrevented || e.altKey || e.ctrlKey || e.metaKey || e.shiftKey) return;
    const t = e.target as HTMLElement;
    if (e.key === "Escape") {
      setPinned(null);
      return;
    }
    if (t.closest("[data-rail]") || t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.isContentEditable) return;
    if (e.key === "ArrowRight") {
      e.preventDefault();
      goTo(nav.current + 1);
    } else if (e.key === "ArrowLeft") {
      e.preventDefault();
      goTo(nav.current - 1);
    }
  };

  const ctx = useMemo<JourneyCtxValue>(
    () => ({
      active: pinned ?? preview,
      preview: setPreview,
      pin: (n) => setPinned((p) => (canHover ? (p === n ? null : n) : n)),
      canHover,
      animate,
      reduced,
      prefix,
    }),
    [pinned, preview, canHover, animate, reduced, prefix],
  );

  const summaryFor = (id: StageId, fallback: string) => {
    if (id === "analyst") return `8 fenced tool steps; generator ${provider === "none" ? "deterministic" : provider}`;
    if (id === "approval") return `status: ${sim.status}`;
    if (id === "response")
      return sim.execution
        ? `mock ticket ${sim.execution.ticket_id}${sim.verification ? ", verified" : ""}`
        : `status: ${sim.status}`;
    return fallback;
  };

  const artifactFor = (id: StageId) => {
    switch (id) {
      case "alert":
        return <AlertArtifact />;
      case "evidence":
        return <EvidenceArtifact />;
      case "correlation":
        return <CorrelationArtifact />;
      case "risk":
        return <RiskArtifact />;
      case "investigation":
        return <GraphArtifact />;
      case "analyst":
        return (
          <AnalystArtifact
            provider={provider}
            onProvider={setProvider}
            planRun={planRun}
            onRunNext={runNext}
            onRunAll={runAll}
            switchName={`${prefix}-provider-analyst`}
          />
        );
      case "recommendation":
        return <RecommendationArtifact sim={sim} />;
      case "approval":
        return <GateArtifact sim={sim} onAct={onAct} onReset={onReset} onContinue={() => goTo(stageIndex.response)} />;
      case "response":
        return <ResponseArtifact sim={sim} onAct={onAct} onReset={onReset} onBack={() => goTo(stageIndex.approval)} />;
    }
  };

  const { current, reached } = nav;

  return (
    <JourneyCtx.Provider value={ctx}>
      <div
        className={styles.journey}
        role="region"
        aria-label="Follow an alert through AegisAI"
        tabIndex={-1}
        onKeyDown={onKeyDown}
      >
        <JourneyRail
          current={current}
          from={nav.from}
          reached={reached}
          tick={nav.tick}
          reduced={reduced}
          provider={provider}
          onProvider={setProvider}
          onSelect={goTo}
          switchName={`${prefix}-provider`}
        />

        <div className={styles.body}>
          <div className={styles.caseFile}>
            <div className={styles.caseHead}>
              <h3 className={styles.caseTitle}>
                Case file <span className="mono text-ink-2">alert-0001</span>
              </h3>
              <p className={`small ${styles.caseLabel}`}>{sampleAlert.label}</p>
            </div>

            <ol className={styles.items}>
              {stages.slice(0, reached + 1).map((s, i) => {
                const isCurrent = i === current;
                return (
                  <li
                    key={s.id}
                    ref={(el) => {
                      itemRefs.current[s.id] = el;
                    }}
                    className={styles.item}
                  >
                    {isCurrent ? (
                      <div className={styles.itemCurrentHead}>
                        <span className={styles.itemNo}>{i + 1}</span>
                        <span className={styles.itemName}>{s.name}</span>
                      </div>
                    ) : (
                      <div className={styles.itemHead}>
                        <button
                          type="button"
                          className={styles.itemButton}
                          onClick={() => goTo(i)}
                          aria-expanded={false}
                          aria-label={`Open stage ${i + 1}, ${s.name}: ${summaryFor(s.id, s.summary)}`}
                        >
                          <span className={styles.itemNo}>{i + 1}</span>
                          <span className={styles.itemName}>{s.name}</span>
                          <span className={`small ${styles.itemSummary}`}>{summaryFor(s.id, s.summary)}</span>
                        </button>
                        <span className={styles.itemRefs}>
                          <Refs ids={s.summaryRefs} />
                        </span>
                      </div>
                    )}
                    {isCurrent && (
                      <div className={styles.itemBody}>
                        <div className={`${styles.mobileOnly} ${styles.mobilePanel}`} aria-live="polite">
                          <StagePanel index={i} showCount={false} />
                        </div>
                        <m.div
                          key={s.id}
                          className={styles.artifact}
                          initial={animate ? { opacity: 0, y: 6 } : false}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ duration: 0.22, ease: [0.2, 0, 0, 1] }}
                        >
                          {artifactFor(s.id)}
                        </m.div>
                      </div>
                    )}
                  </li>
                );
              })}
            </ol>

            {reached >= REC && sim.generated && <AuditLog rows={sim.audit} headingId={`${prefix}-audit`} />}
            <Ledger reached={reached} fresh={fresh} />
          </div>

          <aside className={styles.aside} aria-label="Stage explanation">
            <div aria-live="polite">
              <StagePanel index={current} showCount />
            </div>
            <Controls current={current} goTo={goTo} />
            <p className={`small ${styles.kbdHint}`}>
              <kbd className={styles.kbd}>←</kbd> <kbd className={styles.kbd}>→</kbd> move between stages when the
              journey has focus.
            </p>
          </aside>
        </div>

        {/* A direct child of the journey, so it can stick to the bottom while the journey is on screen. */}
        <Controls current={current} goTo={goTo} compact />
      </div>
    </JourneyCtx.Provider>
  );
}

function StagePanel({ index, showCount }: { index: number; showCount: boolean }) {
  const s = stages[index];
  return (
    <div>
      {showCount && (
        <p className={`small ${styles.panelCount}`}>
          Stage {index + 1} of {stages.length}: {s.name}
        </p>
      )}
      <h3 className={`h-sub ${styles.panelTitle}`}>{s.title}</h3>
      <p className={`body-2 ${styles.panelBody}`}>
        <InlineText text={s.body} />
      </p>
      <div className={styles.quotes}>
        {s.quotes.map((q) => (
          <EvidenceQuote key={q.quote} evidence={q} size="small" />
        ))}
      </div>
    </div>
  );
}

function Controls({ current, goTo, compact = false }: { current: number; goTo: (i: number) => void; compact?: boolean }) {
  const next = stages[current + 1];
  const atStart = current === 0;
  return (
    <div className={compact ? `${styles.mobileBar} ${styles.mobileOnly}` : styles.controls}>
      <button
        type="button"
        className="btn btn-secondary"
        aria-disabled={atStart || undefined}
        onClick={() => !atStart && goTo(current - 1)}
      >
        Previous
      </button>
      <button
        type="button"
        className={`btn ${next ? "btn-primary" : "btn-secondary"}`}
        onClick={() => goTo(next ? current + 1 : 0)}
      >
        {next ? `Next: ${next.name}` : "Back to the alert"}
      </button>
    </div>
  );
}

/** Footnotes for the case file. Entries appear as stages are reached and are never removed. */
function Ledger({ reached, fresh }: { reached: number; fresh: ReadonlySet<StageId> }) {
  const ctx = useJourney()!;
  const visible = ledger.map((e, i) => ({ e, n: i + 1 })).filter(({ e }) => stageIndex[e.stage] <= reached);
  return (
    <section className={styles.ledger} aria-labelledby={`${ctx.prefix}-ledger`}>
      <div className={styles.ledgerHead}>
        <h3 id={`${ctx.prefix}-ledger`} className={`small ${styles.ledgerTitle}`}>
          Evidence ledger
        </h3>
        <p className={`small ${styles.ledgerNote}`} aria-live="polite">
          {visible.length} {visible.length === 1 ? "entry" : "entries"}. Added as the case grows, never removed.
        </p>
      </div>
      <ol className={styles.ledgerList}>
        {visible.map(({ e, n }) => {
          return (
            <li
              key={e.id}
              id={`${ctx.prefix}-ev-${n}`}
              className={`${styles.ledgerItem} ${fresh.has(e.stage) && ctx.animate ? styles.ledgerFresh : ""}`}
              data-lit={ctx.active === n || undefined}
              onMouseEnter={() => ctx.canHover && ctx.preview(n)}
              onMouseLeave={() => ctx.canHover && ctx.preview(null)}
            >
              <span className={styles.ledgerNo}>[{n}]</span>
              <span>
                <span className={`${styles.ledgerLabel} ${e.mono ? "mono" : ""}`}>{e.label}</span>
              </span>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
