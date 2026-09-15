import type { ReactNode } from "react";

/**
 * A narrative section. `id` is the anchor the context bar and search jump to.
 * Spacing varies by `pace` so the page doesn't beat out one rhythm.
 */
export function Section({
  id,
  label,
  children,
  pace = "standard",
  className = "",
}: {
  id: string;
  /** Accessible name; also what the context bar shows. */
  label: string;
  children: ReactNode;
  pace?: "tight" | "standard" | "loose";
  className?: string;
}) {
  const pad = pace === "tight" ? "py-16 md:py-20" : pace === "loose" ? "py-24 md:py-40" : "py-20 md:py-28";
  return (
    <section id={id} aria-label={label} data-section={id} className={`${pad} ${className}`}>
      {children}
    </section>
  );
}
