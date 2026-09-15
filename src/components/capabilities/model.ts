import { areas, capabilities } from "@/content/capabilities";
import { toolGroups } from "@/content/tools";
import type { Area, Evidence, WorkItem, WorkKind } from "@/content/types";
import { work, workById } from "@/content/work";

/**
 * View model for the attention map. Capabilities and tools are both "left" items:
 * things that point at work. Nothing here adds facts — it only reshapes src/content.
 */

export type Mode = "capabilities" | "toolkit";

/**
 * The hero and search palette open the map on a capability with
 * `window.dispatchEvent(new CustomEvent(CAPMAP_SELECT, { detail }))`.
 * `capability` is a capability id (a label also works); `area` picks its first capability.
 * Lives here (no "use client") so server and client modules can both import it.
 */
export const CAPMAP_SELECT = "capmap:select";

export interface CapMapSelectDetail {
  area?: Area;
  capability?: string;
}

export interface Link {
  work: string;
  evidence: Evidence;
}

export interface LeftItem {
  /** Unique across modes: "cap:<id>" or "tool:<group>/<label>". */
  key: string;
  label: string;
  /** Tools have no area; they render neutral. */
  area: Area | null;
  links: Link[];
}

export interface LeftGroup {
  id: string;
  label: string;
  area: Area | null;
  items: LeftItem[];
}

/** What the map is showing: a left item's links, or a work item's backers. */
export type Focus = { side: "L"; key: string } | { side: "R"; id: string };

export interface Pin {
  left: string;
  work: string | null;
}

export const workOrder = new Map(work.map((w, i) => [w.id, i]));

const validLinks = (links: Link[]) => links.filter((l) => workById[l.work]);

const capGroups: LeftGroup[] = areas.map((a) => ({
  id: a.id,
  label: a.label,
  area: a.id,
  items: capabilities
    .filter((c) => c.area === a.id)
    .map((c) => ({ key: `cap:${c.id}`, label: c.label, area: c.area, links: validLinks(c.links) })),
}));

const toolLeftGroups: LeftGroup[] = toolGroups.map((g) => ({
  id: g.id,
  label: g.label,
  area: null,
  items: g.tools.map((t) => ({ key: `tool:${g.id}/${t.label}`, label: t.label, area: null, links: validLinks(t.links) })),
}));

export const groupsByMode: Record<Mode, LeftGroup[]> = {
  capabilities: capGroups,
  toolkit: toolLeftGroups,
};

export const flatByMode: Record<Mode, LeftItem[]> = {
  capabilities: capGroups.flatMap((g) => g.items),
  toolkit: toolLeftGroups.flatMap((g) => g.items),
};

export const itemByKey = new Map<string, LeftItem>(
  [...flatByMode.capabilities, ...flatByMode.toolkit].map((i) => [i.key, i]),
);

export const capKey = (id: string) => `cap:${id}`;

function firstKey(mode: Mode, pick: (i: LeftItem) => boolean) {
  const flat = flatByMode[mode];
  return (flat.find(pick) ?? flat.find((i) => i.links.length > 0) ?? flat[0]).key;
}

/** Default pins, so the map never loads empty. */
export const DEFAULT_LEFT: Record<Mode, string> = {
  capabilities: firstKey("capabilities", (i) => i.key === capKey("qlora")),
  toolkit: firstKey("toolkit", (i) => i.label === "QLoRA" && i.links.length > 0),
};

export const kindLabel: Record<WorkKind, string> = {
  project: "Project",
  role: "Role",
  paper: "Paper",
  product: "Product",
};

export type Readout =
  | {
      kind: "forward";
      key: string;
      item: LeftItem;
      rows: { work: WorkItem; evidence: Evidence }[];
    }
  | {
      kind: "reverse";
      key: string;
      work: WorkItem;
      /** Every left item that links to this work, in list order (one line each). */
      items: LeftItem[];
      /** The same links grouped by the sentence that backs them. */
      rows: { items: LeftItem[]; evidence: Evidence }[];
    };

const norm = (s: string) => s.replace(/\s+/g, " ").trim();
const sameDoc = (a: Evidence, b: Evidence) => a.source === b.source && (a.file ?? "") === (b.file ?? "");

/**
 * Several links often quote overlapping parts of one résumé sentence. Group each
 * link under the longest quote (same document) that contains its own quote, so the
 * panel shows each backing sentence once — still verbatim, just not repeated.
 */
function groupByEvidence(pairs: { item: LeftItem; evidence: Evidence }[]) {
  const unique: Evidence[] = [];
  for (const p of pairs) {
    if (!unique.some((u) => sameDoc(u, p.evidence) && norm(u.quote) === norm(p.evidence.quote))) unique.push(p.evidence);
  }
  const hosts = unique.filter(
    (e) =>
      !unique.some(
        (o) => o !== e && sameDoc(o, e) && norm(o.quote).length > norm(e.quote).length && norm(o.quote).includes(norm(e.quote)),
      ),
  );
  const groups = new Map<Evidence, LeftItem[]>();
  for (const p of pairs) {
    const host = hosts.find((h) => sameDoc(h, p.evidence) && norm(h.quote).includes(norm(p.evidence.quote))) ?? p.evidence;
    const list = groups.get(host) ?? [];
    if (!list.includes(p.item)) list.push(p.item);
    groups.set(host, list);
  }
  return [...groups].map(([evidence, items]) => ({ evidence, items }));
}

export function readoutFor(mode: Mode, f: Focus): Readout | null {
  if (f.side === "L") {
    const item = itemByKey.get(f.key);
    if (!item) return null;
    const rows = item.links
      .map((l) => ({ work: workById[l.work], evidence: l.evidence }))
      .sort((a, b) => (workOrder.get(a.work.id) ?? 0) - (workOrder.get(b.work.id) ?? 0));
    return { kind: "forward", key: `L:${item.key}`, item, rows };
  }
  const w = workById[f.id];
  if (!w) return null;
  const pairs = flatByMode[mode].flatMap((item) =>
    item.links.filter((l) => l.work === w.id).map((l) => ({ item, evidence: l.evidence })),
  );
  const items = pairs.map((p) => p.item).filter((it, i, all) => all.indexOf(it) === i);
  return { kind: "reverse", key: `R:${mode}:${w.id}`, work: w, items, rows: groupByEvidence(pairs) };
}

/** Stable string form of a focus, for memo keys and comparisons. */
export const focusId = (f: Focus) => (f.side === "L" ? `L|${f.key}` : `R|${f.id}`);

export const parseFocusId = (s: string): Focus =>
  s.startsWith("L|") ? { side: "L", key: s.slice(2) } : { side: "R", id: s.slice(2) };

export const sameFocus = (a: Focus, b: Focus) => focusId(a) === focusId(b);

/** Tint behind a lit item: its area, or the caret's soft tint for tools. */
export const TOOL_TINT = "var(--color-caret-soft)";
/** Stroke for tool relationships (tools carry no area). */
export const TOOL_LINE = "var(--color-ink)";
