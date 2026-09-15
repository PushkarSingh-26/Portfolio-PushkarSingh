"use client";

import { createContext, useContext, type ReactNode } from "react";
import { ledger, ledgerNo } from "@/content/aegis";
import styles from "./Journey.module.css";

/** Journey-wide state the artifacts read: which ledger entry is lit, motion, ids. */
export interface JourneyCtxValue {
  /** Ledger number currently lit (pinned, else previewed). */
  active: number | null;
  preview: (n: number | null) => void;
  pin: (n: number) => void;
  canHover: boolean;
  /** True only after the visitor has acted and motion is allowed. */
  animate: boolean;
  reduced: boolean;
  prefix: string;
}

export const JourneyCtx = createContext<JourneyCtxValue | null>(null);

export function useJourney() {
  return useContext(JourneyCtx);
}

/**
 * A citation marker pointing at an evidence-ledger entry. Hover or focus lights
 * the entry; click pins it (Esc clears). On touch, the tap jumps to the entry.
 */
export function Ref({ id }: { id: string }) {
  const ctx = useContext(JourneyCtx);
  const n = ledgerNo[id];
  if (!n) return null;
  const entry = ledger[n - 1];
  if (!ctx) return <sup className={styles.refStatic}>[{n}]</sup>;
  const lit = ctx.active === n;
  return (
    <a
      href={`#${ctx.prefix}-ev-${n}`}
      className={styles.ref}
      data-lit={lit || undefined}
      aria-label={`Evidence ${n}: ${entry.label}`}
      onMouseEnter={() => ctx.canHover && ctx.preview(n)}
      onMouseLeave={() => ctx.canHover && ctx.preview(null)}
      onFocus={() => ctx.preview(n)}
      onBlur={() => ctx.preview(null)}
      onClick={(e) => {
        if (ctx.canHover) e.preventDefault();
        ctx.pin(n);
      }}
    >
      [{n}]
    </a>
  );
}

export function Refs({ ids }: { ids?: string[] }) {
  if (!ids?.length) return null;
  return (
    <>
      {ids.map((id) => (
        <Ref key={id} id={id} />
      ))}
    </>
  );
}

/** Renders `backtick` spans as machine text. */
export function InlineText({ text }: { text: string }): ReactNode {
  const parts = text.split(/(`[^`]+`)/g);
  return parts.map((p, i) =>
    p.startsWith("`") && p.endsWith("`") ? (
      <code key={i} className="mono">
        {p.slice(1, -1)}
      </code>
    ) : (
      <span key={i}>{p}</span>
    ),
  );
}
