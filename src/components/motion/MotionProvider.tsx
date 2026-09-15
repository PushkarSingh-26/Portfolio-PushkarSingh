"use client";

import { LazyMotion, MotionConfig } from "motion/react";
import type { ReactNode } from "react";

const loadFeatures = () => import("./features").then((m) => m.default);

/**
 * Loads Motion's DOM animation features once, asynchronously, after first paint. Components must use `m.*`
 * (not `motion.*`) so the full bundle never ships. `reducedMotion="user"` makes
 * every Motion transform respect prefers-reduced-motion automatically.
 */
export function MotionProvider({ children }: { children: ReactNode }) {
  return (
    <LazyMotion features={loadFeatures} strict>
      <MotionConfig reducedMotion="user" transition={{ duration: 0.24, ease: [0.2, 0, 0, 1] }}>
        {children}
      </MotionConfig>
    </LazyMotion>
  );
}
