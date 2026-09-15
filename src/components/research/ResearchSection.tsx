import Link from "next/link";
import type { ReactNode } from "react";
import { agentsPaper, sentimentPaper } from "@/content/research";
import { profile } from "@/content/profile";
import { EvidenceQuote } from "@/components/ui/Evidence";
import { Section } from "@/components/ui/Section";
import { AgentLayerMatrix } from "./AgentLayerMatrix";
import { SentimentPipeline } from "./SentimentPipeline";
import { listNames } from "./tokens";

type PaperLike = typeof agentsPaper | typeof sentimentPaper;

/** Home-page research: the two papers, newest first, each with a small working diagram. */
export function ResearchSection() {
  return (
    <Section id="research" label="Research">
      <div className="wrap">
        <h2 className="h-section">Research</h2>
        <p className="lead measure mt-6">
          Two papers, two ends of the same arc: in my BCA, a lexicon and an LSTM reading financial news; in my MCA,
          LLM agents that retrieve and reason, with a person reviewing high-value leads.
        </p>

        <div className="mt-14 md:mt-20">
          <PaperBlock paper={agentsPaper} visual={<AgentLayerMatrix mode="compact" />} />
          <PaperBlock paper={sentimentPaper} visual={<SentimentPipeline mode="compact" />} />
        </div>
      </div>
    </Section>
  );
}

function PaperBlock({ paper, visual }: { paper: PaperLike; visual: ReactNode }) {
  const headingId = `paper-${paper.slug}`;
  const coAuthors = paper.authors.filter((a) => a !== profile.name);
  return (
    <article
      aria-labelledby={headingId}
      className="grid grid-cols-1 gap-y-10 border-t border-rule pt-8 pb-16 md:pt-10 md:pb-24 last:pb-0 lg:grid-cols-12 lg:gap-x-12"
    >
      <div className="lg:col-span-5">
        <h3 id={headingId} className="h-sub max-w-[28ch]">
          {paper.title}
        </h3>
        <p className="small mt-3">
          {paper.label}, with {listNames(coAuthors)}
        </p>
        <p className="small text-ink-2">{paper.affiliation}</p>

        <dl className="mt-8 grid gap-y-6 measure">
          <div>
            <dt className="small text-ink-2 mb-2">The question</dt>
            <dd>
              <EvidenceQuote evidence={paper.question} size="small" />
            </dd>
          </div>
          <div>
            <dt className="small text-ink-2 mb-2">The approach</dt>
            <dd>
              <EvidenceQuote evidence={paper.approach} size="small" />
            </dd>
          </div>
        </dl>

        <p className="mt-6 flex flex-wrap gap-x-7">
          <a className="link inline-flex min-h-11 items-center" href={paper.pdf} target="_blank" rel="noreferrer">
            Read the paper (PDF)<span className="sr-only">, opens in a new tab</span>
          </a>
          {paper.code && (
            <a className="link inline-flex min-h-11 items-center" href={paper.code} target="_blank" rel="noreferrer">
              Code on GitHub<span className="sr-only">, opens in a new tab</span>
            </a>
          )}
          <Link className="link inline-flex min-h-11 items-center" href={`/research/${paper.slug}`}>
            Details<span className="sr-only"> on {paper.title}</span>
          </Link>
        </p>
      </div>

      <div className="min-w-0 lg:col-span-7">{visual}</div>
    </article>
  );
}
