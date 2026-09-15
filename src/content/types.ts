/** The four capability areas. Their tints encode the same meaning everywhere on the site. */
export type Area = "ml" | "llm" | "genai" | "applied";

export type SourceId = "resume" | "aegis" | "paper-agents" | "paper-sentiment" | "sigma-demo" | "stated" | "finance" | "sentiment-code";

/**
 * A verbatim quote from one of the source documents. `scripts/check-content.mjs`
 * fails the build if the quote can't be found in the matching source file.
 */
export interface Evidence {
  source: SourceId;
  quote: string;
  /** For multi-file sources (AegisAI repo docs): the path inside the repo. */
  file?: string;
}

/**
 * Evidence helper. Keep the arguments as plain double-quoted string literals —
 * the content checker reads them statically.
 */
export function ev(source: SourceId, quote: string, file?: string): Evidence {
  return { source, quote, file };
}

export type WorkKind = "project" | "role" | "paper" | "product";

export interface WorkItem {
  id: string;
  title: string;
  kind: WorkKind;
  /** Short context line: org, role, or venue-free status. */
  context: string;
  when: string;
  href?: string;
  area: Area;
}

export interface Capability {
  id: string;
  label: string;
  area: Area;
  links: { work: string; evidence: Evidence }[];
}

export interface Tool {
  label: string;
  links: { work: string; evidence: Evidence }[];
}

export interface ToolGroup {
  id: string;
  label: string;
  /** Where the grouping comes from. Résumé groups keep the résumé's own names. */
  tools: Tool[];
}
