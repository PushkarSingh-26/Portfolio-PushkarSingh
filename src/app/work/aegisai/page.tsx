import type { Metadata } from "next";
import { EvidenceQuote } from "@/components/ui/Evidence";
import { PageHeader } from "@/components/ui/PageHeader";
import { Section } from "@/components/ui/Section";
import { InvestigationJourney } from "@/components/aegis/InvestigationJourney";
import { ModelVersions } from "@/components/aegis/ModelVersions";
import { PipelineOverview } from "@/components/aegis/PipelineOverview";
import { StateMachine } from "@/components/aegis/StateMachine";
import { WeightBar } from "@/components/aegis/WeightBar";
import styles from "@/components/aegis/Aegis.module.css";
import {
  AEGIS_REPO,
  aegisFacts,
  aegisIntro,
  agentTools,
  auditFacts,
  caseStudy,
  cvePriority,
  grounding,
  kevOverride,
  limits,
  peopleDecide,
  providerFacts,
  socPriority,
  stack,
  weakSupervision,
} from "@/content/aegis";

export const metadata: Metadata = {
  title: "AegisAI — Pushkar Singh",
  description: caseStudy.metaDescription,
  alternates: { canonical: "/work/aegisai" },
  openGraph: { title: "AegisAI — Pushkar Singh", description: caseStudy.metaDescription },
};

function SectionHead({ title, lead }: { title: string; lead?: string }) {
  return (
    <div className={styles.sectionHead}>
      <h2 className="h-section">{title}</h2>
      {lead && <p className={`lead ${styles.sectionLead}`}>{lead}</p>}
    </div>
  );
}

export default function AegisCaseStudy() {
  return (
    <>
      <PageHeader
        title="AegisAI"
        lead={
          <>
            <p>{aegisIntro.purpose.quote}</p>
            <p className="small body-2 mt-3">
              {aegisIntro.repoName}
            </p>
          </>
        }
        facts={[
          { label: "Built", value: aegisFacts.built.value },
          { label: "Status", value: aegisFacts.status.value },
          { label: "Runs", value: aegisFacts.runs.value },
          {
            label: "Repository",
            value: (
              <a className="link mono break-all" href={AEGIS_REPO} target="_blank" rel="noreferrer">
                cyber-threat-intelligence-platform
              </a>
            ),
          },
        ]}
      />

      <Section id="what-it-does" label="What it does" pace="tight">
        <div className="wrap">
          <SectionHead title={caseStudy.whatItDoes.title} lead={caseStudy.whatItDoes.lead} />
          <PipelineOverview />
        </div>
      </Section>

      <Section id="follow-an-alert" label="Follow an alert">
        <div className="wrap">
          <SectionHead title={caseStudy.follow.title} lead={caseStudy.follow.lead} />
          <div className="mt-12">
            <InvestigationJourney />
          </div>
        </div>
      </Section>

      <Section id="grounded" label="How it stays grounded" pace="loose">
        <div className="wrap">
          <SectionHead title={caseStudy.grounded.title} lead={caseStudy.grounded.lead} />
          <div className={styles.threeCol}>
            <div className={styles.block}>
              <h3 className="h-sub">{grounding.evidence.title}</h3>
              <p className={`body-2 ${styles.blockBody}`}>{grounding.evidence.body}</p>
              <div className={styles.quoteStack}>
                {grounding.evidence.quotes.map((q) => (
                  <EvidenceQuote key={q.quote} evidence={q} size="small" />
                ))}
              </div>
            </div>

            <div className={styles.block}>
              <h3 className="h-sub">{grounding.llm.title}</h3>
              <p className={`body-2 ${styles.blockBody}`}>{grounding.llm.body}</p>
              <ul className={styles.providerList} aria-label="AI_PROVIDER options and default models">
                <li className={styles.providerRow}>
                  <span className="mono">none</span>
                  <span className="body-2">
                    The default: deterministic answers, no keys.
                  </span>
                </li>
                {(Object.keys(providerFacts.models) as (keyof typeof providerFacts.models)[]).map((p) => (
                  <li key={p} className={styles.providerRow}>
                    <span className="mono">{p}</span>
                    <span className="body-2">
                      Narrates the evidence. Default model <code className="mono">{providerFacts.models[p].model}</code>.
                    </span>
                  </li>
                ))}
              </ul>
              <div className={styles.quoteStack}>
                {grounding.llm.quotes.map((q) => (
                  <EvidenceQuote key={q.quote} evidence={q} size="small" />
                ))}
              </div>
            </div>

            <div className={styles.block}>
              <h3 className="h-sub">{grounding.fence.title}</h3>
              <p className={`body-2 ${styles.blockBody}`}>{grounding.fence.body}</p>
              <ul className={styles.toolTokens} aria-label="The twelve read-only agent tools">
                {agentTools.map((t) => (
                  <li key={t} className={styles.toolToken}>
                    {t}
                  </li>
                ))}
              </ul>
              <div className={styles.quoteStack}>
                {grounding.fence.quotes.map((q) => (
                  <EvidenceQuote key={q.quote} evidence={q} size="small" />
                ))}
              </div>
            </div>
          </div>
        </div>
      </Section>

      <Section id="people-decide" label="People decide">
        <div className="wrap">
          <SectionHead title={caseStudy.people.title} lead={peopleDecide.body} />
          <div className={styles.twoCol}>
            <div className={styles.colMain}>
              <div className={styles.quoteStack}>
                {peopleDecide.quotes.map((q) => (
                  <EvidenceQuote key={q.quote} evidence={q} size="small" />
                ))}
              </div>
              <p className={`body-2 ${styles.auditFields}`}>
                Each audit row records <code className="mono">recommendation_id</code>, <code className="mono">event</code>,{" "}
                <code className="mono">actor</code>, <code className="mono">detail</code> and a timestamp.
              </p>
            </div>
            <div className={`${styles.colSide} ${styles.container}`}>
              <p className="small body-2 mb-3">The recommendation state machine, as the code defines it.</p>
              <StateMachine />
              <p className="small body-2 mt-4">
                <a className="link" href="#follow-an-alert">
                  Try the gate in the journey
                </a>
              </p>
            </div>
          </div>
        </div>
      </Section>

      <Section id="risk-model" label="The risk model, honestly" pace="loose">
        <div className="wrap">
          <SectionHead title={caseStudy.risk.title} lead={caseStudy.risk.lead} />
          <div className={styles.twoCol}>
            <div className={styles.colMain}>
              <div className={styles.quoteStack}>
                <EvidenceQuote evidence={weakSupervision.noTruth} size="small" />
                <EvidenceQuote evidence={weakSupervision.byConstruction} size="small" />
                <EvidenceQuote evidence={weakSupervision.aid} size="small" />
                <EvidenceQuote evidence={weakSupervision.swappable} size="small" />
              </div>
            </div>
            <div className={`${styles.colSide} ${styles.container}`}>
              <h3 className="h-sub">Six versions, each adding a signal</h3>
              <p className="body-2 mt-3">
                The top feature moves from raw severity toward exploitation evidence and then graph structure. The
                model itself is XGBoost, with RandomForest as a fallback.
              </p>
              <div className="mt-5">
                <ModelVersions />
              </div>
              <h3 className="h-sub mt-12">The score is a formula you can read</h3>
              <div className="mt-5 grid gap-8">
                <WeightBar name={socPriority.name} note={socPriority.note} parts={socPriority.parts} refs={false} />
                <WeightBar name={cvePriority.name} note={cvePriority.note} parts={cvePriority.parts} refs={false} />
              </div>
              <p className="small body-2 mt-5">
                A CISA KEV listing overrides both: <code className="mono">{kevOverride.formula}</code>.
              </p>
            </div>
          </div>
        </div>
      </Section>

      <Section id="stack" label="Stack" pace="tight">
        <div className="wrap">
          <SectionHead title={caseStudy.stack.title} lead={caseStudy.stack.lead} />
          <div className={styles.stackGrid}>
            {stack.map((g) => (
              <div key={g.group} className={styles.stackGroup}>
                <h3>{g.group}</h3>
                <ul className={styles.stackList}>
                  {g.items.map((it) => (
                    <li key={it.label} className={styles.stackItem}>
                      {it.label}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </Section>

      <Section id="limits" label="What it isn't">
        <div className="wrap">
          <SectionHead title={caseStudy.limits.title} lead={caseStudy.limits.lead} />
          <ul className={styles.limits}>
            {limits.map((l) => (
              <li key={l.text} className={styles.limit}>
                <p className={styles.limitText}>{l.text}</p>
              </li>
            ))}
          </ul>
        </div>
      </Section>
    </>
  );
}
