import type { Area } from "@/content/types";
import type { ReactNode } from "react";

export const areaTok: Record<Area | "neutral", string> = {
  ml: "tok-ml",
  llm: "tok-llm",
  genai: "tok-genai",
  applied: "tok-applied",
  neutral: "tok-neutral",
};

export const areaLine: Record<Area, string> = {
  ml: "var(--color-line-ml)",
  llm: "var(--color-line-llm)",
  genai: "var(--color-line-genai)",
  applied: "var(--color-line-applied)",
};

export const areaTint: Record<Area, string> = {
  ml: "var(--color-tint-ml)",
  llm: "var(--color-tint-llm)",
  genai: "var(--color-tint-genai)",
  applied: "var(--color-tint-applied)",
};

/** A tinted token span. The tint says which capability area it belongs to. */
export function Token({
  area = "neutral",
  children,
  className = "",
}: {
  area?: Area | "neutral";
  children: ReactNode;
  className?: string;
}) {
  return <span className={`tok ${areaTok[area]} ${className}`}>{children}</span>;
}

/** Renders text split at real tokenizer boundaries, with hairlines between sub-tokens. */
export function SplitToken({ parts, area, className = "" }: { parts: string[]; area: Area | "neutral"; className?: string }) {
  return (
    <span className={`tok ${areaTok[area]} ${className}`}>
      <span className="sr-only">{parts.join("")}</span>
      <span aria-hidden="true">
        {parts.map((p, i) => (
          <span key={i} className={i > 0 ? "tok-part" : undefined} style={{ whiteSpace: "pre" }}>
            {p.replace(/^ /, "")}
          </span>
        ))}
      </span>
    </span>
  );
}
