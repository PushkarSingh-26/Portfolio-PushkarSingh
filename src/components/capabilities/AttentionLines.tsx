"use client";

import { AnimatePresence, m } from "motion/react";

export interface Line {
  key: string;
  d: string;
  color: string;
}

const EASE = [0.2, 0, 0, 1] as const;

/**
 * The "attend" primitive: one bezier per relationship, drawn with pathLength.
 * Only the active selection's lines exist. Decorative — the evidence panel carries
 * the same information for assistive tech, so the SVG is aria-hidden.
 */
export function AttentionLines({
  width,
  height,
  lines,
  draw,
  reduced,
}: {
  width: number;
  height: number;
  lines: Line[];
  /** False for the first, not-user-caused render: lines appear already drawn. */
  draw: boolean;
  reduced: boolean;
}) {
  const animateIn = draw && !reduced;
  return (
    <svg
      className="pointer-events-none absolute left-0 top-0 z-0 overflow-visible"
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      aria-hidden="true"
      focusable="false"
    >
      <AnimatePresence initial={false}>
        {lines.map((l, i) => (
          <m.path
            key={l.key}
            d={l.d}
            fill="none"
            stroke={l.color}
            strokeWidth={1.5}
            strokeLinecap="butt"
            initial={animateIn ? { pathLength: 0, opacity: 1 } : false}
            animate={{
              pathLength: 1,
              opacity: 1,
              transition: {
                pathLength: { duration: animateIn ? 0.36 : 0, delay: animateIn ? i * 0.04 : 0, ease: EASE },
                opacity: { duration: 0 },
              },
            }}
            exit={{ opacity: 0, transition: { duration: reduced ? 0 : 0.12, ease: EASE } }}
          />
        ))}
      </AnimatePresence>
    </svg>
  );
}
