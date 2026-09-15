"use client";

import { m } from "motion/react";
import { useEffect, useState } from "react";
import {
  agentTools,
  agentToolsEvidence,
  alertPlan,
  deterministicAnswer,
  fenceRefusal,
  narration,
  planAfter,
  planAfterEvidence,
  planSkipEvidence,
  providerFacts,
  type Provider,
} from "@/content/aegis";
import { ProviderSwitch } from "./ProviderSwitch";
import { Ref, Refs, useJourney } from "./shared";
import styles from "./Artifacts.module.css";

const TOTAL = alertPlan.length + planAfter.length;

/**
 * 6 — AI analyst. The agent's fixed plan walks through a fence of twelve read-only
 * tools; the answer is deterministic unless a provider is switched on, and even then
 * the model only narrates the same evidence.
 */
export function AnalystArtifact({
  provider,
  onProvider,
  planRun,
  onRunNext,
  onRunAll,
  switchName,
}: {
  provider: Provider;
  onProvider: (p: Provider) => void;
  planRun: number;
  onRunNext: () => void;
  onRunAll: () => void;
  switchName: string;
}) {
  const ctx = useJourney();
  const toolRuns = alertPlan.slice(0, Math.min(planRun, alertPlan.length)).map((s) => s.tool);
  const activeTool = planRun >= 1 && planRun <= alertPlan.length ? alertPlan[planRun - 1].tool : null;
  const done = planRun >= TOTAL;

  return (
    <div className={styles.stack}>
      {/* The fence: the only things the agent can call. */}
      <section className={styles.fence} aria-label="Tool registry">
        <div className={styles.fenceHead}>
          <span className={styles.label}>
            Tool registry, 12 read-only tools
            <Ref id="tools" />
          </span>
        </div>
        <ul className={styles.tools}>
          {agentTools.map((t) => {
            const calls = toolRuns.filter((x) => x === t).length;
            return (
              <li
                key={t}
                className={`${styles.tool} ${calls ? styles.toolCalled : ""} ${activeTool === t ? styles.toolActive : ""}`}
              >
                {t}
                {calls > 0 && (
                  <span className={styles.toolCount}>
                    <span className="sr-only">called </span>×{calls}
                  </span>
                )}
              </li>
            );
          })}
        </ul>
        <p className={styles.refusal}>
          {fenceRefusal.text}
        </p>
      </section>

      {/* The plan: fixed per investigation type, run one step at a time. */}
      <section aria-label="Alert investigation plan">
        <div className={styles.labelRow}>
          <span className={styles.label}>
            The planner&apos;s alert plan
            <Ref id="plan" />
          </span>
          <span className={styles.caption} aria-live="polite">
            {planRun === 0 ? "Not run yet" : done ? "Plan complete, every call logged" : `${planRun} of ${TOTAL} run`}
          </span>
        </div>
        <ol className={`${styles.plan} mt-2`}>
          {alertPlan.map((s, i) => {
            const ran = planRun > i;
            return (
              <li key={s.tool} className={`${styles.step} ${ran ? styles.stepRun : ""}`}>
                <span className={styles.stepNo}>{i + 1}</span>
                <div>
                  <div className={styles.stepCall}>
                    {s.tool}
                    <span className={styles.stepParams}>({s.params})</span>
                  </div>
                  <div className={styles.stepWhy}>{s.rationale}</div>
                  {ran && (
                    <m.div
                      className={styles.stepOut}
                      initial={ctx?.animate ? { opacity: 0 } : false}
                      animate={{ opacity: 1 }}
                      transition={{ duration: 0.18 }}
                    >
                      <span className={styles.logged}>logged</span>
                      {s.output}
                      <Refs ids={s.refs} />
                    </m.div>
                  )}
                </div>
              </li>
            );
          })}
          {planAfter.map((s, j) => {
            const ran = planRun > alertPlan.length + j;
            return (
              <li key={s.call} className={`${styles.step} ${ran ? styles.stepRun : ""}`}>
                <span className={styles.stepNo} aria-hidden="true">
                  ·
                </span>
                <div>
                  <div className={styles.stepCall}>{s.call}</div>
                  {ran && (
                    <div className={styles.stepOut}>
                      {s.output}
                      <Refs ids={s.refs} />
                    </div>
                  )}
                </div>
              </li>
            );
          })}
        </ol>
        <div className={`${styles.buttons} mt-3`}>
          <button type="button" className="btn btn-secondary" onClick={onRunNext} aria-disabled={done || undefined}>
            {done ? "Plan complete" : planRun === 0 ? "Run step 1" : `Run the next step`}
          </button>
          {!done && (
            <button type="button" className="btn btn-quiet" onClick={onRunAll}>
              Run every step
            </button>
          )}
        </div>
        <p className={`${styles.caption} mt-2`}>
          Steps that need <code className="mono">$cve_id</code> take it from step 2&apos;s output.
        </p>
      </section>

      {/* The answer: deterministic by default, narrated only if a provider is on. */}
      <p className={`${styles.caption} mt-4`}>
        The agent&apos;s report comes from these steps alone. The AI analyst below is a separate part of the
        platform that answers from the same data.
      </p>
      <section aria-label="Analyst answer" className={styles.record}>
        <div className={styles.recordHead}>
          <span className={styles.recordName}>AIResponse</span>
          <ProviderSwitch value={provider} onChange={onProvider} name={switchName} />
        </div>
        <dl className={styles.kv}>
          <dt>generator</dt>
          <dd>
            {provider === "none" ? (
              <>
                &quot;deterministic&quot;
                <Ref id="provider" />
              </>
            ) : (
              <span className="tok tok-llm">&quot;{provider}&quot;</span>
            )}
          </dd>
          {provider !== "none" && (
            <>
              <dt>AI_MODEL</dt>
              <dd>
                {providerFacts.models[provider].model} <span className={styles.placeholder}>default</span>
              </dd>
            </>
          )}
          <dt>supporting_entities</dt>
          <dd>
            [&#123;&quot;type&quot;: &quot;Technique&quot;, &quot;id&quot;: &quot;T1190&quot;&#125;, …]
            <Ref id="mitre" />
          </dd>
        </dl>

        {provider !== "none" && (
          <m.div
            key={provider}
            className={`${styles.narration} mt-3`}
            initial={ctx?.animate ? { opacity: 0 } : false}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.22 }}
          >
            <p className={styles.caption}>
              <span className={styles.captionStrong}>{narration.label}</span>
            </p>
            <p className={styles.narrationText}>
              {narration.parts.map((p, i) => (
                <span key={i}>
                  {p.text}
                  {p.ref && <Ref id={p.ref} />}
                </span>
              ))}
            </p>
            <p className={`${styles.caption} mt-2`}>
              The prompt tells the model to “{providerFacts.prompt.quote}”
            </p>
          </m.div>
        )}

        <div className="mt-3">
          <p className={styles.caption}>
            {provider === "none" ? (
              <>
                <code className="mono">answer</code>
              </>
            ) : (
              <>
                Grounded summary, returned instead if the provider fails.
              </>
            )}
          </p>
          <StreamText tokens={deterministicAnswer.tokens} play={!!ctx?.animate && provider === "none"} />
          <p className={`${styles.caption} mt-2`}>{deterministicAnswer.caption}</p>
        </div>
      </section>
    </div>
  );
}

/** Token-by-token reveal behind a caret, for short machine text only. */
function StreamText({ tokens, play }: { tokens: string[]; play: boolean }) {
  const [shown, setShown] = useState(play ? 0 : tokens.length);
  useEffect(() => {
    if (!play) {
      setShown(tokens.length);
      return;
    }
    setShown(0);
    let i = 0;
    const id = window.setInterval(() => {
      i += 1;
      setShown(i);
      if (i >= tokens.length) window.clearInterval(id);
    }, 48);
    return () => window.clearInterval(id);
  }, [play, tokens.length]);
  const done = shown >= tokens.length;
  return (
    <p className={`${styles.stream} mt-1`}>
      <span className="sr-only">{tokens.join("")}</span>
      <span aria-hidden="true">
        {tokens.slice(0, shown).map((t, i) => (
          <Tok key={i} t={t} />
        ))}
        {!done && <span className={styles.caret} />}
      </span>
    </p>
  );
}

function Tok({ t }: { t: string }) {
  const parts = t.split(/(‹[^›]*›|…)/g);
  return (
    <>
      {parts.map((p, i) =>
        p === "…" || (p.startsWith("‹") && p.endsWith("›")) ? (
          <span key={i} className={styles.placeholder}>
            {p}
          </span>
        ) : (
          <span key={i} style={{ whiteSpace: "pre-wrap" }}>
            {p}
          </span>
        ),
      )}
    </>
  );
}
