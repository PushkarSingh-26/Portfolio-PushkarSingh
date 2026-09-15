import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import type { ReactNode } from "react";
import { agentsPaper, papers, sentimentPaper } from "@/content/research";
import { Cite, EvidenceQuote } from "@/components/ui/Evidence";
import { PageHeader } from "@/components/ui/PageHeader";
import { Section } from "@/components/ui/Section";
import { Token } from "@/components/ui/Token";
import { AgentLayerMatrix } from "@/components/research/AgentLayerMatrix";
import { DataSplit } from "@/components/research/DataSplit";
import { SentimentPipeline } from "@/components/research/SentimentPipeline";
import { VaderRow } from "@/components/research/VaderRow";
import { LstmStack } from "@/components/research/LstmStack";
import { listNames } from "@/components/research/tokens";

type Params = { slug: string };
type Paper = (typeof papers)[number];

export const dynamicParams = false;

export function generateStaticParams(): Params[] {
  return papers.map((p) => ({ slug: p.slug }));
}

const findPaper = (slug: string) => papers.find((p) => p.slug === slug);

export async function generateMetadata({ params }: { params: Promise<Params> }): Promise<Metadata> {
  const { slug } = await params;
  const paper = findPaper(slug);
  if (!paper) return {};
  return {
    title: { absolute: `${paper.title} — Pushkar Singh` },
    description: paper.question.quote,
  };
}

export default async function ResearchPage({ params }: { params: Promise<Params> }) {
  const { slug } = await params;
  const paper = findPaper(slug);
  if (!paper) notFound();

  return (
    <article>
      <PageHeader
        title={paper.title}
        back={{ href: "/#research", label: "Back to research" }}
        lead={<p>“{paper.question.quote}”</p>}
        facts={[
          { label: "Type", value: paper.label },
          { label: "Authors", value: listNames(paper.authors) },
          { label: "Affiliation", value: paper.affiliation },
          {
            label: "Keywords",
            value: (
              <span className="flex flex-wrap gap-1.5 font-normal small">
                {paper.keywords.map((k) => (
                  <Token key={k}>{k}</Token>
                ))}
              </span>
            ),
          },
        ]}
        actions={
          <>
            <a className="btn btn-primary" href={paper.pdf} target="_blank" rel="noreferrer">
              Read the paper (PDF)<span className="sr-only">, opens in a new tab</span>
            </a>
            {paper.code && (
              <a className="btn btn-secondary" href={paper.code} target="_blank" rel="noreferrer">
                Code on GitHub<span className="sr-only">, opens in a new tab</span>
              </a>
            )}
          </>
        }
      />

      {paper.slug === agentsPaper.slug ? <AgentsBody /> : <SentimentBody />}

      <Closing paper={paper} />
    </article>
  );
}

/* ---------- Layout helper ---------- */

/** One titled part of the page. `full` lets a diagram take the whole measure. */
function Part({
  id,
  title,
  children,
  pace = "tight",
  full = false,
}: {
  id: string;
  title: string;
  children: ReactNode;
  pace?: "tight" | "standard" | "loose";
  full?: boolean;
}) {
  return (
    <Section id={id} label={title} pace={pace}>
      <div className="wrap">
        <div className="grid grid-cols-1 gap-y-6 border-t border-rule pt-6 md:pt-8 lg:grid-cols-12 lg:gap-x-10">
          <h2 className={`h-sub ${full ? "lg:col-span-12" : "lg:col-span-3"}`}>{title}</h2>
          <div className={`min-w-0 ${full ? "lg:col-span-12" : "lg:col-span-8 lg:col-start-5"}`}>{children}</div>
        </div>
      </div>
    </Section>
  );
}

/* ---------- AI agents paper ---------- */

function AgentsBody() {
  const p = agentsPaper;
  return (
    <>
      <Part id="problem" title="The problem">
        <EvidenceQuote evidence={p.question} className="measure" />
      </Part>

      <Part id="approach" title="The approach">
        <EvidenceQuote evidence={p.approach} className="measure" />
        <div className="mt-10 grid gap-8 md:grid-cols-2 md:gap-10">
          <div id="shared-backbone" className="scroll-mt-24">
            <h3 className="font-semibold mb-3">Shared n8n backbone</h3>
            <EvidenceQuote evidence={p.sharedBackbone} size="small" />
          </div>
          <div id="human-review" className="scroll-mt-24">
            <h3 className="font-semibold mb-3">Human review</h3>
            <EvidenceQuote evidence={p.humanInLoop} size="small" />
          </div>
        </div>
      </Part>

      <Part id="architecture" title="Architecture" pace="standard" full>
        <AgentLayerMatrix mode="expanded" backboneHref="#shared-backbone" humanReviewHref="#human-review" />
      </Part>

      <Part id="results" title="Reported results">
        <div className="scroll-x" tabIndex={0} role="group" aria-label="Reported results table, scrollable">
          <table className="w-full min-w-[34rem] border-collapse text-left">
            <caption className="small text-ink-2 pb-3 text-left">As reported in the paper (Table 4).</caption>
            <thead>
              <tr className="border-b border-ink">
                <th scope="col" className="small font-semibold py-2 pr-4">
                  Domain
                </th>
                <th scope="col" className="small font-semibold py-2 pr-4">
                  Manual
                </th>
                <th scope="col" className="small font-semibold py-2 pr-4">
                  Automated
                </th>
                <th scope="col" className="small font-semibold py-2">
                  Reduction
                </th>
              </tr>
            </thead>
            <tbody className="tabular-nums">
              {p.reportedTimes.map((r) => (
                <tr key={r.domain} className="border-b border-rule align-top">
                  <th scope="row" className="small font-semibold py-3 pr-4">
                    {r.domain}
                  </th>
                  <td className="small py-3 pr-4">{r.manual}</td>
                  <td className="small py-3 pr-4">{r.automated}</td>
                  <td className="small py-3">{r.reduction}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-3">
          <Cite evidence={p.reportedTimes[0].evidence} />
        </p>
      </Part>
    </>
  );
}

/* ---------- Sentiment paper ---------- */

function SentimentBody() {
  const p = sentimentPaper;
  const [scale, range, meaning] = p.vaderScale.quote.split(" | ");
  return (
    <>
      <Part id="question" title="The question">
        <EvidenceQuote evidence={p.question} className="measure" />
      </Part>

      <Part id="approach" title="The approach">
        <EvidenceQuote evidence={p.approach} className="measure" />
      </Part>

      <Part id="method" title="Method" pace="standard">
        <SentimentPipeline mode="expanded" />
      </Part>

      <Part id="model" title="Model" pace="standard">
        <p className="body-2 measure">
          The paper describes stacked LSTM layers with dropout and a dense output. The published notebook fills in the
          sizes.
        </p>
        <LstmStack className="mt-8" />
      </Part>

      <Part id="data" title="Data" pace="standard">
        <h3 className="font-semibold">Training and test rows</h3>
        <DataSplit className="mt-4" />
        <p className="small text-ink-2 mt-4 measure">
          These are the paper&apos;s figures. The notebook in the repository is a separate run, with{" "}
          <span className="mono text-ink">3,913</span> training and <span className="mono text-ink">977</span> test rows.{" "}
          <Cite evidence={p.codeRunSplit} />
        </p>

        <h3 className="font-semibold mt-14">Sentiment scores</h3>
        <VaderRow className="mt-4" />

        <figure className="mt-10 max-w-[40rem] border-t border-rule pt-5">
          <figcaption className="small">
            <span className="font-semibold">{scale}</span> <span className="mono text-ink-2">{range}</span>
          </figcaption>
          <div className="quote-mark mt-2">
            <blockquote className="small text-ink">“{meaning}”</blockquote>
            <p className="mt-1">
              <Cite evidence={p.vaderScale} />
            </p>
          </div>
        </figure>
      </Part>
    </>
  );
}

/* ---------- Closing ---------- */

function Closing({ paper }: { paper: Paper }) {
  return (
    <div className="wrap pb-24 md:pb-32">
      <p className="body-2 border-t border-rule pt-6 measure">
        Read it in full in the{" "}
        <a className="link" href={paper.pdf} target="_blank" rel="noreferrer">
          paper (PDF)<span className="sr-only">, opens in a new tab</span>
        </a>
        {paper.code && (
          <>
            , browse the{" "}
            <a className="link" href={paper.code} target="_blank" rel="noreferrer">
              code on GitHub<span className="sr-only">, opens in a new tab</span>
            </a>
          </>
        )}
        , or go{" "}
        <Link className="link" href="/#research">
          back to research on the overview
        </Link>
        .
      </p>
    </div>
  );
}
