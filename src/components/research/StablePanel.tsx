import type { ReactNode } from "react";
import styles from "./StablePanel.module.css";

/**
 * A readout panel whose height never changes with selection: every variant is laid
 * into the same grid cell, invisibly, so the tallest one sets the height. Only the
 * active variant is live (and announced politely); the sizers are hidden from
 * assistive tech and inert.
 */
export function StablePanel({
  id,
  variants,
  active,
  className = "",
}: {
  id: string;
  variants: readonly { key: string; node: ReactNode }[];
  active: string;
  className?: string;
}) {
  const current = variants.find((v) => v.key === active) ?? variants[0];
  return (
    <div className={`${styles.stack} ${className}`}>
      {variants.map((v) => (
        <div key={v.key} className={styles.sizer} aria-hidden="true" inert>
          {v.node}
        </div>
      ))}
      <div id={id} className={styles.live} aria-live="polite">
        {current?.node}
      </div>
    </div>
  );
}
