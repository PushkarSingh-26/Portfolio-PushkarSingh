"use client";

import { m } from "motion/react";
import { useEffect, useRef, type KeyboardEvent } from "react";
import { providerFacts, stageIndex, stages, type Provider } from "@/content/aegis";
import { Cite } from "@/components/ui/Evidence";
import { ProviderSwitch } from "./ProviderSwitch";
import styles from "./Journey.module.css";

const LAST = stages.length - 1;
const ANALYST = stageIndex.analyst;

/**
 * Nine numbered stops (a real sequence). Current is caret, visited ink, upcoming
 * dim. Above it, the optional LLM lane: it starts at the AI_PROVIDER setting and
 * touches only the AI analyst stop. Roving tabindex; ←/→/Home/End move and select.
 */
export function JourneyRail({
  current,
  from,
  reached,
  tick,
  reduced,
  provider,
  onProvider,
  onSelect,
  switchName,
}: {
  current: number;
  from: number;
  reached: number;
  tick: number;
  reduced: boolean;
  provider: Provider;
  onProvider: (p: Provider) => void;
  onSelect: (i: number) => void;
  switchName: string;
}) {
  const buttons = useRef<(HTMLButtonElement | null)[]>([]);
  const scroller = useRef<HTMLDivElement>(null);
  const llmOn = provider !== "none";

  // Keep the current stop in view when the rail is a scrolling strip.
  useEffect(() => {
    const sc = scroller.current;
    const b = buttons.current[current];
    if (!sc || !b || sc.scrollWidth <= sc.clientWidth + 1) return;
    const left = b.offsetLeft - sc.clientWidth / 2 + b.offsetWidth / 2;
    sc.scrollTo({ left: Math.max(0, left), behavior: reduced ? "auto" : "smooth" });
  }, [current, reduced]);

  const onKey = (e: KeyboardEvent<HTMLButtonElement>, i: number) => {
    let next = -1;
    if (e.key === "ArrowRight") next = Math.min(i + 1, LAST);
    else if (e.key === "ArrowLeft") next = Math.max(i - 1, 0);
    else if (e.key === "Home") next = 0;
    else if (e.key === "End") next = LAST;
    if (next < 0) return;
    e.preventDefault();
    onSelect(next);
    buttons.current[next]?.focus();
  };

  return (
    <div className={`${styles.railBlock} ${llmOn ? styles.laneOn : ""}`} data-rail="">
      <div className={styles.lane}>
        <ProviderSwitch value={provider} onChange={onProvider} name={switchName} />
        <span className={styles.laneLine} aria-hidden="true" />
      </div>
      <span className={styles.laneRiser} aria-hidden="true" />

      <div className={styles.railScroll} ref={scroller}>
        <div role="group" aria-label="Investigation stages">
          <ol className={styles.rail}>
            <li className={styles.track} aria-hidden="true">
              <span className={styles.trackDone} style={{ transform: `scaleX(${reached / LAST})` }} />
            </li>
            {!reduced && tick > 0 && from !== current && (
              <li className={styles.pulseLane} aria-hidden="true">
                <span className={styles.pulseTrack}>
                  <m.span
                    key={tick}
                    className={styles.pulseWrap}
                    initial={{ x: `${(from / LAST) * 100}%`, opacity: 0 }}
                    animate={{ x: `${(current / LAST) * 100}%`, opacity: [0, 1, 1, 0] }}
                    transition={{
                      x: { duration: 0.5, ease: [0.2, 0, 0, 1] },
                      opacity: { duration: 0.62, times: [0, 0.12, 0.78, 1] },
                    }}
                  >
                    <span className={styles.pulse} />
                  </m.span>
                </span>
              </li>
            )}
            {stages.map((s, i) => {
              const isCurrent = i === current;
              const visited = i <= reached;
              const cls = [
                styles.stop,
                isCurrent ? styles.stopCurrent : visited ? styles.stopVisited : "",
                i === ANALYST && llmOn ? styles.stopLlm : "",
              ].join(" ");
              return (
                <li key={s.id} className="flex min-w-0">
                  <button
                    ref={(el) => {
                      buttons.current[i] = el;
                    }}
                    type="button"
                    className={cls}
                    tabIndex={isCurrent ? 0 : -1}
                    aria-current={isCurrent ? "step" : undefined}
                    aria-label={`Stage ${i + 1}, ${s.name}${visited ? "" : ", not reached yet"}`}
                    onClick={() => onSelect(i)}
                    onKeyDown={(e) => onKey(e, i)}
                  >
                    <span className={styles.dot} aria-hidden="true" />
                    <span className={styles.stopLabel}>
                      <span className={styles.stopNo}>{i + 1}</span>
                      <span className={styles.stopName}> {s.name}</span>
                    </span>
                  </button>
                </li>
              );
            })}
          </ol>
        </div>
      </div>

      <p className={`small ${styles.railCaption}`}>
        {llmOn ? (
          <>
            Only the AI analyst stage changes: a model narrates the evidence the analyst already gathered. Every other stage is identical.{" "}
            <Cite evidence={providerFacts.narrate} />
          </>
        ) : (
          <>
            <code className="mono">none</code> is the platform default. Every stage below works without an LLM.{" "}
            <Cite evidence={providerFacts.noneDefault} />
          </>
        )}
      </p>
    </div>
  );
}
