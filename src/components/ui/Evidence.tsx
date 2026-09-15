import { sources } from "@/content/profile";
import type { Evidence as EvidenceT } from "@/content/types";

/** Multi-file sources: citations link to the exact file in the repository. */
const REPOS: Partial<Record<EvidenceT["source"], { blob: string; name: string; aliases?: Record<string, string> }>> = {
  aegis: { blob: "https://github.com/PushkarSingh-26/cyber-threat-intelligence-platform/blob/main/", name: "AegisAI" },
  finance: { blob: "https://github.com/PushkarSingh-26/YFinance-Stockbot/blob/main/", name: "Finance Pilot" },
  // The notebook's code and outputs are extracted to text for checking; citations link to the notebook itself.
  "sentiment-code": {
    blob: "https://github.com/PushkarSingh-26/stock-market-pred-using-LSTM-NLP/blob/main/",
    name: "Paper code",
    aliases: { "notebook-code.py": "ntcc_project.ipynb", "notebook-text.txt": "ntcc_project.ipynb" },
  },
};

/** The file as it exists in the repository (extracted text files map back to their notebook). */
function repoFile(e: EvidenceT): string | undefined {
  const repo = REPOS[e.source];
  if (!repo || !e.file) return undefined;
  return repo.aliases?.[e.file] ?? e.file;
}

export function sourceHref(e: EvidenceT): string | undefined {
  const repo = REPOS[e.source];
  const file = repoFile(e);
  if (repo && file) return repo.blob + file;
  return sources[e.source].href;
}

export function sourceLabel(e: EvidenceT): string {
  const repo = REPOS[e.source];
  const file = repoFile(e);
  if (repo && file) return `${repo.name} ${file}`;
  return sources[e.source].label;
}

/**
 * Small "Source: …" citation line. Links out when the source is public.
 * `compact` shows only the file name — for places where the surrounding section
 * already names the source — and keeps the full label for screen readers and on hover.
 */
export function Cite({ evidence, className = "", compact = false }: { evidence: EvidenceT; className?: string; compact?: boolean }) {
  const href = sourceHref(evidence);
  const label = sourceLabel(evidence);
  if (compact && evidence.file) {
    const name = (repoFile(evidence) ?? evidence.file).split("/").pop();
    return (
      <span className={`cite ${className}`}>
        {href ? (
          // The accessible name contains the visible file name, so voice control still matches it.
          <a className="link" href={href} target="_blank" rel="noreferrer" title={`Source: ${label}`} aria-label={`Source: ${label}`}>
            {name}
          </a>
        ) : (
          <span title={`Source: ${label}`}>
            <span className="sr-only">Source: {label}</span>
            <span aria-hidden="true">{name}</span>
          </span>
        )}
      </span>
    );
  }
  return (
    <span className={`cite ${className}`}>
      Source:{" "}
      {href ? (
        <a className="link" href={href} target={href.startsWith("http") ? "_blank" : undefined} rel="noreferrer">
          {label}
        </a>
      ) : (
        label
      )}
    </span>
  );
}

/** A verbatim quote with its citation. Quotes are checked against sources at build time. */
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
      <figcaption className="mt-1">
        <Cite evidence={evidence} />
      </figcaption>
    </figure>
  );
}
