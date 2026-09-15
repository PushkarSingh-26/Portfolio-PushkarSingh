"use client";

import { m } from "motion/react";
import { useLayoutEffect, useRef } from "react";
import { EvidenceQuote } from "@/components/ui/Evidence";
import { areaTok } from "@/components/ui/Token";
import { WorkLink, emptyToolMessage } from "./EvidencePanel";
import { ForeignLanguages, ToolLegend } from "./ToolLegend";
import { groupsByMode, readoutFor, type LeftGroup, type Mode } from "./model";
import styles from "./capabilities.module.css";

/**
 * Touch and narrow screens: no lines. Capabilities are tappable tokens grouped by
 * area, and the readout opens directly under the group you tapped in, so the answer
 * lands next to your thumb instead of a screen away.
 */
export function MobileMap({
  mode,
  selected,
  onSelect,
  engaged,
  reduced,
  idBase,
}: {
  mode: Mode;
  /** Key of the selected left item. */
  selected: string;
  onSelect: (key: string) => void;
  engaged: boolean;
  reduced: boolean;
  idBase: string;
}) {
  // Moving the readout between groups changes the height above the tapped chip.
  // Keep the chip where the finger left it (not every browser anchors scroll).
  const anchor = useRef<{ el: HTMLElement; top: number } | null>(null);
  useLayoutEffect(() => {
    const a = anchor.current;
    anchor.current = null;
    if (!a || !a.el.isConnected) return;
    const delta = a.el.getBoundingClientRect().top - a.top;
    if (Math.abs(delta) > 1) window.scrollBy({ top: delta, behavior: "instant" });
  }, [selected, mode]);

  const groups = groupsByMode[mode];

  return (
    <div className={`${styles.mobileOnly} max-w-2xl`}>
      {mode === "toolkit" && <ToolLegend className="small mb-6 max-w-[44ch] text-ink-2" />}

      {groups.map((g) => (
        <MobileGroup
          key={g.id}
          group={g}
          mode={mode}
          selected={selected}
          panelId={`${idBase}-m-${mode}-${g.id}`}
          animateIn={engaged && !reduced}
          onTap={(key, el) => {
            anchor.current = { el, top: el.getBoundingClientRect().top };
            onSelect(key);
          }}
        />
      ))}

      {mode === "toolkit" && <ForeignLanguages className="small mt-8 text-ink-2" />}
    </div>
  );
}

function MobileGroup({
  group,
  mode,
  selected,
  panelId,
  animateIn,
  onTap,
}: {
  group: LeftGroup;
  mode: Mode;
  selected: string;
  panelId: string;
  animateIn: boolean;
  onTap: (key: string, el: HTMLElement) => void;
}) {
  const headId = `${panelId}-h`;
  const current = group.items.find((i) => i.key === selected);
  const readout = current ? readoutFor(mode, { side: "L", key: current.key }) : null;
  const isTool = mode === "toolkit";

  return (
    <div className={styles.mGroup}>
      <h3 id={headId} className={`${styles.groupHead} ${styles.toolHead}`}>
        {group.area && <span aria-hidden="true" className={`${areaTok[group.area]} ${styles.swatch}`} />}
        {group.label}
      </h3>
      <ul aria-labelledby={headId} className={styles.mChips}>
        {group.items.map((it) => {
          const linked = it.links.length > 0;
          return (
            <li key={it.key}>
              <button
                type="button"
                className={`${areaTok[it.area ?? "neutral"]} ${styles.mChip}`}
                data-tool={isTool ? "" : undefined}
                data-muted={isTool && !linked ? "" : undefined}
                aria-pressed={it.key === selected}
                aria-controls={panelId}
                onClick={(e) => onTap(it.key, e.currentTarget)}
              >
                {it.label}
                {isTool && linked && (
                  <>
                    <span aria-hidden="true" className={styles.dot} />
                    <span className="sr-only">, linked to work</span>
                  </>
                )}
              </button>
            </li>
          );
        })}
      </ul>

      {/* Always mounted so screen readers announce the readout when it lands here. */}
      <div id={panelId} aria-live="polite">
        {readout && readout.kind === "forward" && (
          <m.div
            key={readout.key}
            className={styles.mPanel}
            initial={animateIn ? { opacity: 0 } : false}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.22, ease: [0.2, 0, 0, 1] }}
          >
            <h4 className="text-[15px] font-semibold leading-snug">Where “{readout.item.label}” shows up</h4>
            {readout.rows.length === 0 ? (
              <p className="small mt-2 text-ink-2">{emptyToolMessage(readout.item.label)}</p>
            ) : (
              <ul className="mt-4">
                {readout.rows.map((r) => (
                  <li key={r.work.id} className={styles.mItem}>
                    {/* Padding lifts the touch target to 44px without moving the text. */}
                    <WorkLink work={r.work} className="inline-block py-2.5 -my-2.5" />
                    <p className="small mt-0.5 text-ink-2">{r.work.when}</p>
                    <EvidenceQuote evidence={r.evidence} size="small" className="mt-3" />
                  </li>
                ))}
              </ul>
            )}
          </m.div>
        )}
      </div>
    </div>
  );
}
