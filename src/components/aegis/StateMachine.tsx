"use client";

import { m } from "motion/react";
import type { RecStatus } from "@/content/aegis";
import styles from "./StateMachine.module.css";

type Edge = { id: string; from: RecStatus; to: RecStatus; label: string; d: string; arrow: string; lx: number; ly: number };

const BOX = { w: 104, h: 34 };
const NODES: Record<RecStatus, { x: number; y: number }> = {
  pending: { x: 8, y: 20 },
  approved: { x: 184, y: 20 },
  executed: { x: 360, y: 20 },
  verified: { x: 528, y: 20 },
  rejected: { x: 184, y: 100 },
  failed: { x: 528, y: 100 },
};

const head = (x: number, y: number) => `${x},${y} ${x - 7},${y - 4} ${x - 7},${y + 4}`;

const EDGES: Edge[] = [
  { id: "approve", from: "pending", to: "approved", label: "approve", d: "M112 37 H184", arrow: head(184, 37), lx: 148, ly: 29 },
  { id: "execute", from: "approved", to: "executed", label: "execute", d: "M288 37 H360", arrow: head(360, 37), lx: 324, ly: 29 },
  { id: "verify", from: "executed", to: "verified", label: "verify", d: "M464 37 H528", arrow: head(528, 37), lx: 496, ly: 29 },
  { id: "reject", from: "pending", to: "rejected", label: "reject", d: "M60 54 V117 H184", arrow: head(184, 117), lx: 124, ly: 109 },
  { id: "fail", from: "executed", to: "failed", label: "not accepted", d: "M412 54 V117 H528", arrow: head(528, 117), lx: 472, ly: 109 },
];

/** States reached on the way to `status`, and the edges taken. */
function pathTo(status: RecStatus): { states: Set<RecStatus>; edges: Set<string> } {
  switch (status) {
    case "pending":
      return { states: new Set(["pending"]), edges: new Set() };
    case "approved":
      return { states: new Set(["pending", "approved"]), edges: new Set(["approve"]) };
    case "rejected":
      return { states: new Set(["pending", "rejected"]), edges: new Set(["reject"]) };
    case "executed":
      return { states: new Set(["pending", "approved", "executed"]), edges: new Set(["approve", "execute"]) };
    case "verified":
      return { states: new Set(["pending", "approved", "executed", "verified"]), edges: new Set(["approve", "execute", "verify"]) };
    case "failed":
      return { states: new Set(["pending", "approved", "executed", "failed"]), edges: new Set(["approve", "execute", "fail"]) };
  }
}

const LAST_EDGE: Partial<Record<RecStatus, string>> = {
  approved: "approve",
  rejected: "reject",
  executed: "execute",
  verified: "verify",
  failed: "fail",
};

/**
 * The recommendation state machine from backend/app/models/response.py.
 * With `status`, the current state lights up and the edge just taken draws in.
 * Without it, the whole machine is shown plainly.
 */
export function StateMachine({ status, animate = false }: { status?: RecStatus; animate?: boolean }) {
  const path = status ? pathTo(status) : null;
  const last = status ? LAST_EDGE[status] : undefined;
  const stateClass = (s: RecStatus) =>
    !path ? styles.plain : status === s ? styles.current : path.states.has(s) ? styles.visited : styles.idle;
  const edgeClass = (id: string) => (!path ? styles.edgePlain : path.edges.has(id) ? styles.edgeTaken : styles.edgeIdle);

  return (
    <div className={styles.root}>
      <p className="sr-only">
        Recommendation state machine: pending to approved or rejected; approved to executed; executed to verified
        or failed.{status ? ` Current state: ${status}.` : ""}
      </p>
      <svg className={styles.wide} viewBox="0 0 640 150" aria-hidden="true">
        {EDGES.map((e) => (
          <g key={e.id} className={edgeClass(e.id)}>
            <m.path
              key={`${e.id}-${e.id === last ? status : "x"}`}
              d={e.d}
              fill="none"
              initial={animate && e.id === last ? { pathLength: 0 } : false}
              animate={{ pathLength: 1 }}
              transition={{ duration: 0.36, ease: [0.2, 0, 0, 1] }}
            />
            <polygon points={e.arrow} />
            <text x={e.lx} y={e.ly} textAnchor="middle" className={styles.edgeText}>
              {e.label}
            </text>
          </g>
        ))}
        {(Object.keys(NODES) as RecStatus[]).map((s) => {
          const n = NODES[s];
          return (
            <g key={s} className={stateClass(s)}>
              <rect x={n.x} y={n.y} width={BOX.w} height={BOX.h} rx={4} />
              <text x={n.x + BOX.w / 2} y={n.y + BOX.h / 2 + 4.5} textAnchor="middle" className={styles.stateText}>
                {s}
              </text>
            </g>
          );
        })}
      </svg>

      {/* Narrow columns: the same machine as an indented tree. */}
      <ul className={styles.narrow} aria-hidden="true">
        <li>
          <State s="pending" cls={stateClass("pending")} />
          <ul>
            <li>
              <Rel label="approve" cls={edgeClass("approve")} />
              <State s="approved" cls={stateClass("approved")} />
              <ul>
                <li>
                  <Rel label="execute" cls={edgeClass("execute")} />
                  <State s="executed" cls={stateClass("executed")} />
                  <ul>
                    <li>
                      <Rel label="verify" cls={edgeClass("verify")} />
                      <State s="verified" cls={stateClass("verified")} />
                    </li>
                    <li>
                      <Rel label="not accepted" cls={edgeClass("fail")} />
                      <State s="failed" cls={stateClass("failed")} />
                    </li>
                  </ul>
                </li>
              </ul>
            </li>
            <li>
              <Rel label="reject" cls={edgeClass("reject")} />
              <State s="rejected" cls={stateClass("rejected")} />
            </li>
          </ul>
        </li>
      </ul>
    </div>
  );
}

function State({ s, cls }: { s: RecStatus; cls: string }) {
  return <span className={`${styles.chip} ${cls}`}>{s}</span>;
}

function Rel({ label, cls }: { label: string; cls: string }) {
  return <span className={`${styles.rel} ${cls}`}>{label}</span>;
}
