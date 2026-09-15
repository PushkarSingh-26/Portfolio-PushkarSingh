"use client";

import { useRef, type KeyboardEvent } from "react";
import type { Mode } from "./model";
import styles from "./capabilities.module.css";

const OPTIONS: { id: Mode; label: string }[] = [
  { id: "capabilities", label: "Capabilities" },
  { id: "toolkit", label: "Toolkit" },
];

/** Two-option segmented control with radio semantics: arrows move and select. */
export function ModeSwitch({ mode, onChange }: { mode: Mode; onChange: (m: Mode) => void }) {
  const refs = useRef(new Map<Mode, HTMLButtonElement>());

  const onKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
    const i = OPTIONS.findIndex((o) => o.id === mode);
    let n = -1;
    if (e.key === "ArrowRight" || e.key === "ArrowDown") n = (i + 1) % OPTIONS.length;
    else if (e.key === "ArrowLeft" || e.key === "ArrowUp") n = (i - 1 + OPTIONS.length) % OPTIONS.length;
    else if (e.key === "Home") n = 0;
    else if (e.key === "End") n = OPTIONS.length - 1;
    if (n < 0) return;
    e.preventDefault();
    const next = OPTIONS[n].id;
    onChange(next);
    refs.current.get(next)?.focus();
  };

  return (
    <div role="radiogroup" aria-label="Map by" className={styles.seg} onKeyDown={onKeyDown}>
      {OPTIONS.map((o) => {
        const checked = o.id === mode;
        return (
          <button
            key={o.id}
            ref={(el) => {
              if (el) refs.current.set(o.id, el);
              else refs.current.delete(o.id);
            }}
            type="button"
            role="radio"
            aria-checked={checked}
            tabIndex={checked ? 0 : -1}
            className={styles.segBtn}
            onClick={() => {
              if (!checked) onChange(o.id);
            }}
          >
            {o.label}
          </button>
        );
      })}
    </div>
  );
}
