"use client";

import { m } from "motion/react";
import {
  collectedSources,
  cvePriority,
  enrichmentKeys,
  gdsAlgorithms,
  graphBranches,
  graphChain,
  graphSide,
  kevOverride,
  ledger,
  ledgerNo,
  noisyOr,
  riskLevels,
  sampleAlert,
  socPriority,
  t1190Rule,
  type GraphNode,
} from "@/content/aegis";
import { ModelVersions } from "./ModelVersions";
import { Ref, Refs, useJourney } from "./shared";
import { WeightBar } from "./WeightBar";
import styles from "./Artifacts.module.css";

/* 1 — Alert: the fixture record, field by field, with the column it lands in. */
export function AlertArtifact() {
  return (
    <div className={styles.stack}>
      <p className={styles.caption}>
        Each field of the fixture record, and the column the parser writes it to.
      </p>
      <div className={styles.record}>
        <div className={styles.recordHead}>
          <span className={styles.recordName}>wazuh-alerts-* hit</span>
          <span className={styles.recordName}>stored as wazuh_alerts</span>
        </div>
        <dl className={`${styles.kv} ${styles.kvWide}`}>
          {sampleAlert.fields.map((f) => (
            <FieldRow key={f.key} k={f.key} v={f.value} col={f.column} refId={f.ref} />
          ))}
        </dl>
      </div>
      <p className={styles.caption}>
        The parser keeps the hit's <code className="mono">_source</code> as <code className="mono">raw_event</code> and copies these fields into
        columns.
      </p>
    </div>
  );
}

function FieldRow({ k, v, col, refId }: { k: string; v: string; col: string; refId?: string }) {
  return (
    <>
      <dt>{k}</dt>
      <dd>
        {v}
        {refId && <Ref id={refId} />}
      </dd>
      <dd className={styles.kvCol} aria-label={`column ${col}`}>
        {col}
      </dd>
    </>
  );
}

/* 2 — Evidence: raw event kept, enrichment beside it, sources it draws on. */
export function EvidenceArtifact() {
  return (
    <div className={styles.stack}>
      <div className={styles.split}>
        <div className={styles.record}>
          <div className={styles.recordHead}>
            <span className={styles.recordName}>wazuh_alerts.raw_event</span>
            <Ref id="raw" />
          </div>
          <p className={styles.caption}>
            The indexer document for <code className="mono">alert-0001</code>, unchanged, as JSON. Wazuh&apos;s{" "}
            <code className="mono">rule_level</code> stays 12
            <Ref id="level" />.
          </p>
        </div>
        <div className={styles.record}>
          <div className={styles.recordHead}>
            <span className={styles.recordName}>wazuh_alert_enrichment.evidence</span>
            <Ref id="enrichment" />
          </div>
          <dl className={styles.kv}>
            {enrichmentKeys.keys.map((k) => (
              <FieldPlaceholder key={k} k={k} />
            ))}
          </dl>
        </div>
      </div>
      <p className={styles.caption}>
        Values in the enrichment come from the platform&apos;s database, so this page leaves them blank.
      </p>
      <div>
        <p className={styles.label}>Sources the platform collects from</p>
        <ul className={`${styles.list} mt-2`}>
          {collectedSources.map((id) => {
            const e = ledger[ledgerNo[id] - 1];
            return (
              <li key={id} className={styles.listRow}>
                <span>{e.label.replace(/^Collected from /, "")}</span>
                <Ref id={id} />
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}

function FieldPlaceholder({ k }: { k: string }) {
  return (
    <>
      <dt>{k}</dt>
      <dd>
        <span className={styles.placeholder}>‹from the database›</span>
      </dd>
    </>
  );
}

/* 3 — Correlation: the real T1190 rule, the scoring method, the unit-test examples. */
export function CorrelationArtifact() {
  return (
    <div className={styles.stack}>
      <div>
        <div className={styles.labelRow}>
          <span className={styles.label}>
            The rule for the alert&apos;s technique
            <Refs ids={["rule"]} />
          </span>
        </div>
        <div className="scroll-x mt-2">
          <pre className={styles.code}>
            {t1190Rule.lines.map((line, i) => (
              <span key={i}>
                {i === 1 ? (
                  <>
                    {"    "}
                    <mark className={styles.hl}>&quot;T1190&quot;</mark>
                    {line.replace(/^\s+"T1190"/, "")}
                  </>
                ) : (
                  line
                )}
                {"\n"}
              </span>
            ))}
          </pre>
        </div>
        <p className={`${styles.caption} mt-2`}>
          <mark className={styles.hl}>T1190</mark> is the same technique the alert carries
          <Ref id="mitre" />. CVEs whose descriptions contain one of these phrases link to it, and the matched phrases
          are kept as that link&apos;s evidence
          <Ref id="phrases" />.
        </p>
      </div>

      <div className={styles.formula}>
        <span className={styles.formulaText}>{noisyOr.formula}</span>
        <ul className={styles.buckets} aria-label="Confidence buckets">
          {noisyOr.buckets.map((b) => (
            <li key={b.level} className={styles.bucket}>
              <span>{b.level}</span>
              <span>{b.rule}</span>
            </li>
          ))}
        </ul>
      </div>
      <p className={styles.caption}>
        Method <code className="mono">rule-based-keyword-v1</code>
        <Ref id="method" />.
      </p>

      <div>
        <p className={styles.label}>Worked examples from the unit tests</p>
        <div className="mt-1">
          {noisyOr.examples.map((ex) => (
            <div key={ex.call} className={styles.example}>
              <span className={styles.exampleCall}>{ex.call}</span>
              <span className={styles.caption}>
                {ex.note}.
              </span>
            </div>
          ))}
        </div>
      </div>
      <p className={styles.caption}>
        Which CVEs carry T1190 depends on the CVE catalog in the database, so none is named here.
      </p>
    </div>
  );
}

/* 4 — Risk: two separate formulas drawn to scale, the override, the model's versions. */
export function RiskArtifact() {
  return (
    <div className={styles.stack}>
      <WeightBar name={socPriority.name} note={socPriority.note} parts={socPriority.parts} />
      <p className={styles.caption}>
        Only the Wazuh level is known from the alert
        <Ref id="level" />; every other input comes from related CVEs in the database, so no score is computed
        here
        <Ref id="soc-weights" />.
      </p>
      <WeightBar name={cvePriority.name} note={cvePriority.note} parts={cvePriority.parts} />
      <p className={styles.caption}>
        Two engines, kept separate: their weights are never mixed
        <Ref id="cve-weights" />.
      </p>
      <div className={styles.override}>
        <span className={styles.label}>CISA KEV override</span>
        <code className="mono">{kevOverride.formula}</code>
        <Ref id="kev" />
      </div>
      <ul className={styles.buckets} aria-label="Priority levels">
        {riskLevels.levels.map((l) => (
          <li key={l.level} className={styles.bucket}>
            <span>{l.level}</span>
            <span>{l.rule}</span>
          </li>
        ))}
      </ul>
      <div>
        <div className={styles.labelRow}>
          <span className={styles.label}>
            ML risk model, V1 to V6
            <Ref id="weak-label" />
          </span>
          <span className={styles.caption}>What each version adds, and its top feature</span>
        </div>
        <div className="mt-2">
          <ModelVersions />
        </div>
      </div>
    </div>
  );
}

/* 5 — Investigation: typed nodes connect, from the alert outward. */
export function GraphArtifact() {
  const ctx = useJourney();
  const animate = !!ctx?.animate;
  const STEP = 0.042;
  const node = (i: number) =>
    animate
      ? { initial: { opacity: 0 }, animate: { opacity: 1 }, transition: { duration: 0.2, delay: i * STEP, ease: [0.2, 0, 0, 1] as const } }
      : { initial: false as const };
  const line = (i: number, axis: "x" | "y") =>
    animate
      ? {
          initial: axis === "y" ? { scaleY: 0 } : { scaleX: 0 },
          animate: axis === "y" ? { scaleY: 1 } : { scaleX: 1 },
          transition: { duration: 0.2, delay: i * STEP, ease: [0.2, 0, 0, 1] as const },
        }
      : { initial: false as const };

  // Assembly order: alert, agent, then down the chain, then the two branches.
  let seq = 0;
  const [alert, ...rest] = graphChain;
  return (
    <div className={styles.stack}>
      <ol className={styles.chain} aria-label="Alert investigation path">
        <m.li className={styles.nodeRow} {...node(seq++)}>
          <NodeBox n={alert} />
          <span className={styles.sideRel}>
            <m.span className={styles.sideLine} {...line(seq, "x")} />
            <span className={styles.relName}>{graphSide.rel}</span>
          </span>
          <m.span {...node(seq++)}>
            <NodeBox n={graphSide} />
          </m.span>
        </m.li>
        {rest.map((n) => {
          const e = seq++;
          const v = seq++;
          return (
            <li key={n.type}>
              <div className={styles.edge}>
                <m.span className={styles.edgeLine} {...line(e, "y")} />
                <m.span className={styles.edgeLabel} {...node(e)}>
                  <span className={styles.relName}>{n.rel}</span>
                  <span className={styles.hop}>hop {n.hop}</span>
                </m.span>
              </div>
              <m.div className={styles.nodeRow} {...node(v)}>
                <NodeBox n={n} />
              </m.div>
            </li>
          );
        })}
        <li>
          <ul className={styles.branches}>
            {graphBranches.map((b, i) => {
              const s = seq++;
              return (
                <m.li key={b.type} className={styles.branch} {...node(s)}>
                  <m.span className={styles.branchElbow} {...line(s, "y")} />
                  {i < graphBranches.length - 1 && <span className={styles.branchContinue} />}
                  <span className={styles.relName}>{b.rel}</span>
                  <NodeBox n={b} />
                  <span className={styles.hop}>hop {b.hop}</span>
                </m.li>
              );
            })}
          </ul>
        </li>
      </ol>
      <p className={styles.caption}>
        Node types and relationships follow the graph schema
        <Ref id="path" />. Solid nodes come from the alert; dashed ones are resolved from the database, so they
        aren&apos;t named here. Blast radius runs the same traversal from the alert, up to four hops in any
        direction
        <Ref id="blast" />.
      </p>
      <div>
        <p className={styles.label}>
          Graph analytics on the same projection
          <Ref id="gds" />
        </p>
        <ul className={`${styles.chips} mt-2`}>
          {gdsAlgorithms.map((g) => (
            <li key={g.proc} className={styles.chip}>
              <span>{g.name}</span>
              <span className={styles.chipSub}>{g.proc}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

function NodeBox({ n }: { n: GraphNode }) {
  return (
    <span className={`${styles.node} ${n.value ? "" : styles.nodeUnknown}`}>
      <span className={styles.nodeType}>:{n.type}</span>
      {n.value ? (
        <span className={styles.nodeValue}>
          {n.value}
          {n.ref && <Ref id={n.ref} />}
        </span>
      ) : (
        <span className={styles.nodeMissing}>not in the fixture</span>
      )}
    </span>
  );
}
