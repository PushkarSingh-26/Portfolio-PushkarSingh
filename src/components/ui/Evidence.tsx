import type { Evidence as EvidenceT } from "@/content/types";

/**
 * A verbatim quote shown as a quoted passage. The quote is still checked
 * against its source document at build time; the source itself is not shown.
 */
export function EvidenceQuote({
  evidence,
  className = "",
  size = "base",
}: {
  evidence: EvidenceT;
  className?: string;
  size?: "base" | "small";
}) {
  return (
    <figure className={`quote-mark ${className}`}>
      <blockquote className={size === "small" ? "small text-ink" : "text-ink"}>“{evidence.quote}”</blockquote>
    </figure>
  );
}
