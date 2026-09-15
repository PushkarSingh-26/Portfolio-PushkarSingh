"use client";

import { m } from "motion/react";
import {
  auditFacts,
  gateEvidence,
  mockExecution,
  recommendation,
  simulationLabel,
  type GateAction,
} from "@/content/aegis";
import { Cite } from "@/components/ui/Evidence";
import { REC_ID, recTitle, type AuditRow, type Reply, type SimState } from "./responseSim";
import { Ref, useJourney } from "./shared";
import { StateMachine } from "./StateMachine";
import styles from "./Artifacts.module.css";
import jstyles from "./Journey.module.css";

function StatusChip({ status }: { status: string }) {
  return (
    <span className={`${styles.status} ${styles[`status_${status}`] ?? ""}`}>
      <span className="sr-only">status </span>
      {status}
    </span>
  );
}

/* 7 — Recommendation: the record the response engine would create, with its citation. */
export function RecommendationArtifact({ sim }: { sim: SimState }) {
  return (
    <div className={styles.stack}>
      <article className={styles.card} aria-label="Response recommendation">
        <div className={styles.cardHead}>
          <span className={styles.cardTitle}>{recTitle}</span>
          <StatusChip status={sim.status} />
        </div>
        <dl className={styles.kv}>
          {recommendation.fields.map((f) => (
            <FieldRow key={f.key} k={f.key} v={f.value} refId={f.ref} placeholder={f.placeholder} />
          ))}
          <dt>status</dt>
          <dd>&quot;{sim.status}&quot;</dd>
        </dl>
      </article>
      <p className={styles.caption}>
        {recommendation.label} <Cite evidence={recommendation.evidence[0]} />
      </p>
      <p className={styles.caption}>
        {recommendation.otherRules} <Cite evidence={recommendation.otherRulesEvidence} />
      </p>
    </div>
  );
}

function FieldRow({ k, v, refId, placeholder }: { k: string; v: string; refId?: string; placeholder?: boolean }) {
  return (
    <>
      <dt>{k}</dt>
      <dd>
        {placeholder ? <span className={styles.placeholder}>{v}</span> : v}
        {refId && <Ref id={refId} />}
      </dd>
    </>
  );
}

/* The HTTP reply to the last call. A refusal gets a short, firm nudge. */
function ReplyBlock({ reply }: { reply: Reply | null }) {
  const ctx = useJourney();
  return (
    <div aria-live="polite">
      {reply && (
        <m.div
          key={reply.seq}
          className={styles.reply}
          initial={{ x: 0 }}
          animate={reply.code === 409 && ctx?.animate ? { x: [0, -2, 2, -2, 0] } : { x: 0 }}
          transition={{ duration: 0.24, ease: "easeOut" }}
        >
          <div className={styles.replyReq}>
            POST /response/recommendations/{REC_ID}/{reply.action}
          </div>
          <div>
            <span className={reply.code === 409 ? styles.code409 : styles.code200}>
              {reply.code} {reply.code === 409 ? "Conflict" : "OK"}
            </span>
          </div>
          <div>{reply.body}</div>
          {reply.code === 409 && (
            <p className={styles.replyNote}>
              Refused. {gateEvidence.refusedNotLogged} <Cite evidence={gateEvidence.to409} />
            </p>
          )}
        </m.div>
      )}
    </div>
  );
}

function ActionButtons({
  actions,
  onAct,
}: {
  actions: { action: GateAction; label: string; primary?: boolean }[];
  onAct: (a: GateAction) => void;
}) {
  return (
    <div className={styles.buttons}>
      {actions.map((a) => (
        <button
          key={a.action}
          type="button"
          className={`btn ${a.primary ? "btn-primary" : "btn-secondary"}`}
          onClick={() => onAct(a.action)}
        >
          {a.label}
        </button>
      ))}
    </div>
  );
}

/* 8 — Human approval: the gate. Execute is always pressable; the engine decides. */
export function GateArtifact({
  sim,
  onAct,
  onReset,
  onContinue,
}: {
  sim: SimState;
  onAct: (a: GateAction) => void;
  onReset: () => void;
  onContinue: () => void;
}) {
  const ctx = useJourney();
  const executeFirst = sim.status === "pending";
  return (
    <div className={styles.stack}>
      <p className={styles.caption}>
        <span className={styles.captionStrong}>{simulationLabel}</span>{" "}
        <Cite evidence={gateEvidence.endpoint} />
      </p>
      <StateMachine status={sim.status} animate={!!ctx?.animate} />
      <ActionButtons
        onAct={onAct}
        actions={[
          { action: "approve", label: "Approve", primary: true },
          { action: "reject", label: "Reject" },
          { action: "execute", label: "Execute" },
        ]}
      />
      {executeFirst && !sim.reply && (
        <p className={styles.hint}>Try Execute first: it isn&apos;t approved yet.</p>
      )}
      <ReplyBlock reply={sim.reply} />
      {sim.status === "approved" && (
        <p className={styles.hint}>
          Approved by you.{" "}
          <button type="button" className={`link ${styles.textButton}`} onClick={onContinue}>
            Continue to the response
          </button>
        </p>
      )}
      {sim.status === "rejected" && (
        <p className={styles.hint}>
          Rejected. A rejected recommendation can&apos;t move again; nothing will run.{" "}
          <button type="button" className={`link ${styles.textButton}`} onClick={onReset}>
            Start the simulation over
          </button>
        </p>
      )}
      <p className={styles.caption}>
        The same guard sits in the engine: <code className="mono">approve</code> and{" "}
        <code className="mono">reject</code> need <code className="mono">pending</code>,{" "}
        <code className="mono">execute</code> needs <code className="mono">approved</code>.{" "}
        <Cite evidence={gateEvidence.execute} />
      </p>
    </div>
  );
}

/* 9 — Response: hand-off to the provider (the mock), then verification. */
export function ResponseArtifact({
  sim,
  onAct,
  onReset,
  onBack,
}: {
  sim: SimState;
  onAct: (a: GateAction) => void;
  onReset: () => void;
  onBack: () => void;
}) {
  const ctx = useJourney();
  return (
    <div className={styles.stack}>
      <p className={styles.caption}>
        <span className={styles.captionStrong}>{simulationLabel}</span> The provider here is the credential-free
        mock, the platform&apos;s default
        <Ref id="mock" />.
      </p>
      <StateMachine status={sim.status} animate={!!ctx?.animate} />
      <ActionButtons
        onAct={onAct}
        actions={[
          { action: "execute", label: "Execute", primary: true },
          { action: "verify", label: "Verify" },
        ]}
      />
      {(sim.status === "pending" || sim.status === "rejected") && !sim.reply && (
        <p className={styles.hint}>
          {sim.status === "pending" ? "Still pending, so Execute will be refused. " : "This one was rejected. "}
          <button type="button" className={`link ${styles.textButton}`} onClick={onBack}>
            Back to human approval
          </button>
        </p>
      )}
      <ReplyBlock reply={sim.reply} />

      {sim.execution && (
        <div className={styles.record}>
          <div className={styles.recordHead}>
            <span className={styles.recordName}>execution_result</span>
            <Cite evidence={mockExecution.evidence[1]} />
          </div>
          <dl className={styles.kv}>
            <dt>provider</dt>
            <dd>&quot;{sim.execution.provider}&quot;</dd>
            <dt>ticket_id</dt>
            <dd>&quot;{sim.execution.ticket_id}&quot;</dd>
            <dt>status</dt>
            <dd>&quot;{sim.execution.status}&quot;</dd>
            <dt>simulated</dt>
            <dd>true</dd>
          </dl>
          <p className={`${styles.caption} mt-2`}>
            <code className="mono">ticket_id</code> is computed the way MockProvider does it: {mockExecution.derivation}.{" "}
            <Cite evidence={mockExecution.evidence[0]} />
          </p>
        </div>
      )}

      {sim.verification && (
        <div className={styles.record}>
          <div className={styles.recordHead}>
            <span className={styles.recordName}>verification</span>
            <Ref id="verify" />
          </div>
          <dl className={styles.kv}>
            <dt>verified</dt>
            <dd>{String(sim.verification.verified)}</dd>
            <dt>provider</dt>
            <dd>&quot;{sim.verification.provider}&quot;</dd>
            <dt>reference</dt>
            <dd>&quot;{sim.verification.reference}&quot;</dd>
          </dl>
          <p className={`${styles.caption} mt-2`}>
            This only confirms the provider accepted the action: a status of created, triggered or accepted, or a
            ticket id. It says nothing about whether anything changed on a host.{" "}
            <Cite evidence={mockExecution.verifyRule} />
          </p>
        </div>
      )}

      {(sim.status === "verified" || sim.status === "rejected") && (
        <p className={styles.hint}>
          <button type="button" className={`link ${styles.textButton}`} onClick={onReset}>
            Start the simulation over
          </button>
        </p>
      )}
    </div>
  );
}

/* The response_audit log. Rows are only ever appended while the simulation runs. */
export function AuditLog({ rows, headingId }: { rows: AuditRow[]; headingId: string }) {
  const ctx = useJourney();
  const last = rows.length ? rows[rows.length - 1].seq : -1;
  return (
    <section className={jstyles.audit} aria-labelledby={headingId}>
      <h3 id={headingId} className="small font-semibold">
        <span className="mono">response_audit</span>
        <Ref id="audit" />
      </h3>
      <p className={`small ${jstyles.auditNote}`}>
        Simulated rows with the platform&apos;s fields. {auditFacts.actorNote} <Cite evidence={auditFacts.actorEvidence} />
      </p>
      <div className="scroll-x" aria-live="polite">
        <table className={jstyles.auditTable}>
          <thead>
            <tr>
              <th scope="col">Time</th>
              <th scope="col">Recommendation</th>
              <th scope="col">Event</th>
              <th scope="col">Change</th>
              <th scope="col">Actor</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.seq} className={ctx?.animate && r.seq === last ? jstyles.auditRowNew : undefined}>
                <td>{r.time}</td>
                <td>{r.rec}</td>
                <td>{r.event}</td>
                <td>
                  {r.from ?? "(new)"} → {r.to}
                </td>
                <td>{r.actor}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
