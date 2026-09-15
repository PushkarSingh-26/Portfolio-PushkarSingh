"use client";

import { m } from "motion/react";
import { useId, useRef, useState, type KeyboardEvent, type RefObject } from "react";
import { agentsPaper } from "@/content/research";
import type { Evidence } from "@/content/types";
import { EvidenceQuote } from "@/components/ui/Evidence";
import { useCanHover, usePrefersReducedMotion } from "@/lib/hooks";
import { StablePanel } from "./StablePanel";
import { researchVars, rovingIndex } from "./tokens";
import styles from "./AgentLayerMatrix.module.css";

/*
  Four domain agents (columns) passing through the paper's five layers (rows, top to
  bottom). Each agent is a vertical path; the orchestration row is one shared line
  (the n8n backbone); the sales path carries a human review checkpoint.

  Compact (home): cells are nodes, a readout panel quotes the selection.
  Expanded (detail page): cells carry the verbatim text.
  Narrow containers: an agent tablist and a stepper list of the five layers.
*/

const { layers, agents, sharedBackbone, humanInLoop } = agentsPaper;

type Agent = (typeof agents)[number];
type Layer = (typeof layers)[number];
type LayerId = keyof Agent["cells"];

const cellOf = (a: Agent, layerId: string): Evidence => a.cells[layerId as LayerId];

const BACKBONE_LAYER = "orchestrate";
const HUMAN_AGENT = "sales";
const DEFAULT_AGENT = "hr";

type Sel = { kind: "agent"; id: string } | { kind: "layer"; id: string } | { kind: "backbone" } | { kind: "human" };

const DEFAULT_SEL: Sel = { kind: "agent", id: DEFAULT_AGENT };
const keyOf = (s: Sel) => (s.kind === "agent" || s.kind === "layer" ? `${s.kind}:${s.id}` : s.kind);

/* ---------- Readouts (compact panel) ---------- */

function AgentReadout({ agent }: { agent: Agent }) {
  return (
    <div>
      <p className={styles.readTitle}>{agent.name}</p>
      <dl className={styles.readList}>
        {layers.map((l) => (
          <div key={l.id} className={styles.readItem}>
            <dt className="small text-ink-2">{l.name}</dt>
            <dd className="small text-ink">
              “{cellOf(agent, l.id).quote}”
              {agent.id === HUMAN_AGENT && l.id === BACKBONE_LAYER && (
                <span className={`tok tok-neutral ${styles.inlineTag}`}>human review</span>
              )}
            </dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

function LayerReadout({ layer }: { layer: Layer }) {
  return (
    <div>
      <p className={styles.readTitle}>{layer.name}</p>
      <EvidenceQuote evidence={layer.evidence} size="small" className={styles.readQuote} />
      <dl className={styles.readList}>
        {agents.map((a) => (
          <div key={a.id} className={styles.readItem}>
            <dt className="small text-ink-2">{a.name}</dt>
            <dd className="small text-ink">“{cellOf(a, layer.id).quote}”</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

function QuoteReadout({ title, evidence }: { title: string; evidence: Evidence }) {
  return (
    <div>
      <p className={styles.readTitle}>{title}</p>
      <EvidenceQuote evidence={evidence} size="small" className={styles.readQuote} />
    </div>
  );
}

const READOUTS = [
  ...agents.map((a) => ({ key: `agent:${a.id}`, node: <AgentReadout agent={a} /> })),
  ...layers.map((l) => ({ key: `layer:${l.id}`, node: <LayerReadout layer={l} /> })),
  { key: "backbone", node: <QuoteReadout title="Shared n8n backbone" evidence={sharedBackbone} /> },
  { key: "human", node: <QuoteReadout title="Human review" evidence={humanInLoop} /> },
];

/* ---------- Component ---------- */

export function AgentLayerMatrix({
  mode = "compact",
  backboneHref,
  humanReviewHref,
}: {
  mode?: "compact" | "expanded";
  /** Expanded mode: where the shared-backbone quote lives on the page. */
  backboneHref?: string;
  /** Expanded mode: where the human-in-the-loop quote lives on the page. */
  humanReviewHref?: string;
}) {
  const uid = useId();
  const panelId = `${uid}-readout`;
  const compact = mode === "compact";
  const canHover = useCanHover();
  const reduced = usePrefersReducedMotion();

  const [pinned, setPinned] = useState<Sel>(DEFAULT_SEL);
  const [preview, setPreview] = useState<Sel | null>(null);
  /** The last agent explicitly chosen: the column group's tab stop and the narrow tab. */
  const [agentId, setAgentId] = useState(DEFAULT_AGENT);

  const shown = canHover && preview ? preview : pinned;
  const shownAgent = shown.kind === "agent" ? shown.id : null;
  const shownLayer = shown.kind === "layer" ? shown.id : null;

  // Flow: whenever a different agent comes into view, one pulse runs down its path.
  const [pulse, setPulse] = useState(0);
  const [pulsedFor, setPulsedFor] = useState<string | null>(shownAgent);
  if (pulsedFor !== shownAgent) {
    setPulsedFor(shownAgent);
    if (shownAgent) setPulse((n) => n + 1);
  }
  const [stepPulse, setStepPulse] = useState(0);
  const [stepFor, setStepFor] = useState(agentId);
  if (stepFor !== agentId) {
    setStepFor(agentId);
    setStepPulse((n) => n + 1);
  }

  const agentRefs = useRef<(HTMLButtonElement | null)[]>([]);
  const layerRefs = useRef<(HTMLButtonElement | null)[]>([]);
  const tabRefs = useRef<(HTMLButtonElement | null)[]>([]);

  const pin = (s: Sel) => {
    setPinned(s);
    setPreview(null);
    if (s.kind === "agent") setAgentId(s.id);
  };
  const peek = (s: Sel | null) => {
    if (canHover) setPreview(s);
  };

  const agentStop = Math.max(0, agents.findIndex((a) => a.id === agentId));
  const layerStop = pinned.kind === "layer" ? Math.max(0, layers.findIndex((l) => l.id === pinned.id)) : 0;

  const moveAgent = (
    e: KeyboardEvent<HTMLButtonElement>,
    i: number,
    refs: RefObject<(HTMLButtonElement | null)[]>,
    axis: "x" | "both",
  ) => {
    const next = rovingIndex(e.key, i, agents.length, axis);
    if (next === null) return;
    e.preventDefault();
    pin({ kind: "agent", id: agents[next].id });
    refs.current[next]?.focus();
  };

  const moveLayer = (e: KeyboardEvent<HTMLButtonElement>, i: number) => {
    const next = rovingIndex(e.key, i, layers.length, "y");
    if (next === null) return;
    e.preventDefault();
    pin({ kind: "layer", id: layers[next].id });
    layerRefs.current[next]?.focus();
  };

  const onRootKey = (e: KeyboardEvent<HTMLDivElement>) => {
    if (e.key !== "Escape") return;
    if (keyOf(pinned) === keyOf(DEFAULT_SEL) && !preview) return;
    pin(DEFAULT_SEL);
  };

  const table = !compact;
  const showPulse = !reduced && pulse > 0;
  const tabAgent = agents.find((a) => a.id === agentId) ?? agents[0];

  return (
    <div
      className={`${styles.root} ${compact ? styles.compact : styles.expanded}`}
      style={researchVars}
      onKeyDown={onRootKey}
    >
      {/* ---------- Wide: the matrix ---------- */}
      <div className={styles.wide}>
        <p className={`small text-ink-2 ${styles.hint}`}>
          {compact
            ? "Choose an agent to follow its path through the five layers, or a layer to compare all four."
            : "Choose an agent to follow its path down through the layers."}
        </p>

        <div
          className={styles.grid}
          role={table ? "table" : "group"}
          aria-label={table ? "Four domain agents across five layers" : "Agents by layer"}
          onPointerLeave={() => peek(null)}
        >
          <div className={`${styles.row} ${styles.headRow}`} role={table ? "row" : undefined} style={{ gridRow: 1 }}>
            <div className={styles.corner} role={table ? "columnheader" : undefined}>
              {table && <span className="small text-ink-2">Layer</span>}
            </div>
            {agents.map((a, i) => (
              <div key={a.id} className={styles.colHead} role={table ? "columnheader" : undefined}>
                <button
                  ref={(el) => {
                    agentRefs.current[i] = el;
                  }}
                  type="button"
                  className={styles.headBtn}
                  aria-pressed={shownAgent === a.id}
                  aria-controls={compact ? panelId : undefined}
                  tabIndex={i === agentStop ? 0 : -1}
                  onClick={() => pin({ kind: "agent", id: a.id })}
                  onPointerEnter={() => peek({ kind: "agent", id: a.id })}
                  onKeyDown={(e) => moveAgent(e, i, agentRefs, "x")}
                >
                  {a.name}
                </button>
              </div>
            ))}
          </div>

          {agents.map((a, i) => (
            <span
              key={a.id}
              aria-hidden="true"
              className={styles.track}
              data-col={i}
              data-on={shownAgent === a.id ? "" : undefined}
            >
              {showPulse && shownAgent === a.id && (
                <m.span
                  key={pulse}
                  className={styles.pulse}
                  initial={{ y: "0%", opacity: 0 }}
                  animate={{ y: "100%", opacity: [0, 1, 1, 0] }}
                  transition={{
                    y: { duration: 0.6, ease: [0.2, 0, 0, 1] },
                    opacity: { duration: 0.6, times: [0, 0.1, 0.8, 1], ease: "linear" },
                  }}
                />
              )}
            </span>
          ))}

          {layers.map((l, r) => (
            <div
              key={l.id}
              className={styles.row}
              role={table ? "row" : undefined}
              style={{ gridRow: r + 2 }}
              data-layer={l.id}
            >
              <div className={styles.rowHead} role={table ? "rowheader" : undefined}>
                {compact ? (
                  <button
                    ref={(el) => {
                      layerRefs.current[r] = el;
                    }}
                    type="button"
                    className={styles.rowBtn}
                    aria-pressed={shownLayer === l.id}
                    aria-controls={panelId}
                    tabIndex={r === layerStop ? 0 : -1}
                    onClick={() => pin({ kind: "layer", id: l.id })}
                    onPointerEnter={() => peek({ kind: "layer", id: l.id })}
                    onKeyDown={(e) => moveLayer(e, r)}
                  >
                    {l.name}
                  </button>
                ) : (
                  <>
                    <p className={styles.layerName}>{l.name}</p>
                    <p className={`small text-ink-2 ${styles.layerQuote}`}>“{l.evidence.quote}”</p>
                    {l.id === BACKBONE_LAYER && (
                      <p className={`small ${styles.backboneNote}`}>
                        <span className={styles.swatch} aria-hidden="true" />
                        {backboneHref ? (
                          <a className="link" href={backboneHref}>
                            Shared n8n backbone
                          </a>
                        ) : (
                          "Shared n8n backbone"
                        )}
                      </p>
                    )}
                  </>
                )}
              </div>

              {agents.map((a) => {
                const on = shownAgent === a.id || shownLayer === l.id;
                const human = a.id === HUMAN_AGENT && l.id === BACKBONE_LAYER;
                return compact ? (
                  <div
                    key={a.id}
                    className={styles.cell}
                    data-on={on ? "" : undefined}
                    aria-hidden="true"
                    onClick={() => pin({ kind: "agent", id: a.id })}
                    onPointerEnter={() => peek({ kind: "agent", id: a.id })}
                  >
                    <span className={styles.sq} />
                  </div>
                ) : (
                  <div key={a.id} role="cell" className={styles.cell} data-on={on ? "" : undefined}>
                    {cellOf(a, l.id).quote}
                    {human && (
                      <span className={styles.humanTag}>
                        {humanReviewHref ? (
                          <a className="tok tok-neutral" href={humanReviewHref}>
                            human review
                          </a>
                        ) : (
                          <span className="tok tok-neutral">human review</span>
                        )}
                      </span>
                    )}
                  </div>
                );
              })}

              {l.id === BACKBONE_LAYER && <span aria-hidden="true" className={styles.backbone} />}

              {compact && l.id === BACKBONE_LAYER && (
                <>
                  <button
                    type="button"
                    className={styles.backboneBtn}
                    aria-pressed={shown.kind === "backbone"}
                    aria-controls={panelId}
                    onClick={() => pin({ kind: "backbone" })}
                    onPointerEnter={() => peek({ kind: "backbone" })}
                  >
                    <span className={styles.swatch} aria-hidden="true" />
                    Shared n8n backbone
                  </button>
                  <button
                    type="button"
                    className={styles.humanBtn}
                    aria-pressed={shown.kind === "human"}
                    aria-controls={panelId}
                    onClick={() => pin({ kind: "human" })}
                    onPointerEnter={() => peek({ kind: "human" })}
                  >
                    <span>human review</span>
                  </button>
                </>
              )}
            </div>
          ))}
        </div>

        {compact ? (
          <StablePanel id={panelId} className={styles.panel} variants={READOUTS} active={keyOf(shown)} />
        ) : (
          <p className={styles.tableCite}>
            <span className="small text-ink-2">Every cell is quoted from the paper. </span>
          </p>
        )}
      </div>

      {/* ---------- Narrow: agent tabs and a stepper through the layers ---------- */}
      <div className={styles.narrow}>
        <p className={`small text-ink-2 ${styles.hint}`}>
          Choose an agent to follow its path through the five layers. Open a layer to see what it does.
        </p>
        <div role="tablist" aria-label="Agents" className={styles.tabs}>
          {agents.map((a, i) => (
            <button
              key={a.id}
              ref={(el) => {
                tabRefs.current[i] = el;
              }}
              id={`${uid}-tab-${a.id}`}
              type="button"
              role="tab"
              className={styles.tab}
              aria-selected={a.id === agentId}
              aria-controls={`${uid}-tabpanel`}
              tabIndex={a.id === agentId ? 0 : -1}
              onClick={() => pin({ kind: "agent", id: a.id })}
              onKeyDown={(e) => moveAgent(e, i, tabRefs, "both")}
            >
              {a.name}
            </button>
          ))}
        </div>

        <div
          role="tabpanel"
          id={`${uid}-tabpanel`}
          aria-labelledby={`${uid}-tab-${tabAgent.id}`}
          className={styles.tabpanel}
        >
          <ol className={styles.path} aria-label={`${tabAgent.name}, layer by layer`}>
            {layers.map((l, r) => (
              <li key={l.id} className={styles.pstep}>
                <span className={styles.pnode} aria-hidden="true">
                  {!reduced && stepPulse > 0 && (
                    <span key={stepPulse} className={styles.flash} style={{ animationDelay: `${r * 110}ms` }} />
                  )}
                </span>
                <div className={styles.pbody}>
                  <details className={styles.disclosure}>
                    <summary className={styles.summary}>{l.name}</summary>
                    <EvidenceQuote evidence={l.evidence} size="small" className={styles.disclosureQuote} />
                  </details>
                  <p className="small text-ink">“{cellOf(tabAgent, l.id).quote}”</p>
                  {l.id === BACKBONE_LAYER && (
                    <div className={styles.extras}>
                      <details className={styles.disclosure}>
                        <summary className={styles.summary}>
                          <span className={styles.swatch} aria-hidden="true" />
                          Shared n8n backbone
                        </summary>
                        <EvidenceQuote evidence={sharedBackbone} size="small" className={styles.disclosureQuote} />
                      </details>
                      {tabAgent.id === HUMAN_AGENT && (
                        <details className={styles.disclosure}>
                          <summary className={styles.summary}>
                            <span className="tok tok-neutral">human review</span>
                          </summary>
                          <EvidenceQuote evidence={humanInLoop} size="small" className={styles.disclosureQuote} />
                        </details>
                      )}
                    </div>
                  )}
                </div>
              </li>
            ))}
          </ol>
        </div>
      </div>
    </div>
  );
}
