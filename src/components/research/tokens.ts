import type { CSSProperties } from "react";

/**
 * Theme tokens the research CSS modules read, re-exposed as local custom properties.
 * Tailwind v4 only emits theme variables it finds referenced in scanned source files,
 * and it does not scan CSS modules — so the references live here, in TypeScript.
 */
export const researchVars = {
  "--r-paper": "var(--color-paper)",
  "--r-paper-2": "var(--color-paper-2)",
  "--r-paper-3": "var(--color-paper-3)",
  "--r-ink": "var(--color-ink)",
  "--r-ink-2": "var(--color-ink-2)",
  "--r-ink-3": "var(--color-ink-3)",
  "--r-rule": "var(--color-rule)",
  "--r-caret": "var(--color-caret)",
  "--r-caret-soft": "var(--color-caret-soft)",
  /* The agents paper sits in the Generative AI area, the sentiment paper in Machine learning. */
  "--r-tint-genai": "var(--color-tint-genai)",
  "--r-line-genai": "var(--color-line-genai)",
  "--r-tint-ml": "var(--color-tint-ml)",
  "--r-line-ml": "var(--color-line-ml)",
  "--r-mono": "var(--font-mono)",
  "--r-ease": "var(--ease-decode)",
} as CSSProperties;

/** Roving-tabindex arrow handling. Returns the next index, or null if the key isn't ours. */
export function rovingIndex(key: string, i: number, n: number, axis: "x" | "y" | "both"): number | null {
  const fwd = axis === "x" ? ["ArrowRight"] : axis === "y" ? ["ArrowDown"] : ["ArrowRight", "ArrowDown"];
  const back = axis === "x" ? ["ArrowLeft"] : axis === "y" ? ["ArrowUp"] : ["ArrowLeft", "ArrowUp"];
  if (fwd.includes(key)) return (i + 1) % n;
  if (back.includes(key)) return (i - 1 + n) % n;
  if (key === "Home") return 0;
  if (key === "End") return n - 1;
  return null;
}

/** "A", "A and B", "A, B and C". */
export function listNames(names: readonly string[]): string {
  if (names.length <= 1) return names.join("");
  return `${names.slice(0, -1).join(", ")} and ${names[names.length - 1]}`;
}
