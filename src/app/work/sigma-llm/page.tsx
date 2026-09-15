import type { Metadata } from "next";
import { sigmaProject } from "@/content/sigma";
import { PageHeader } from "@/components/ui/PageHeader";
import { Section } from "@/components/ui/Section";
import { Cite, EvidenceQuote } from "@/components/ui/Evidence";
import { Token } from "@/components/ui/Token";
import { BenchmarkTable, StatusLine } from "@/components/sigma/CheckParts";
import { HarnessDemo } from "@/components/sigma/HarnessDemo";
import { SigmaPipeline } from "@/components/sigma/SigmaPipeline";
import s from "@/components/sigma/sigma.module.css";

export const metadata: Metadata = {
  title: "Sigma rule LLM — Pushkar Singh",
  description:
    "Fine-tuning an open-weight LLM with QLoRA to write Sigma detection rules, and the compiler-based harness (sigma-cli) that checks every rule it writes. In progress; no results yet.",
};

/** Each tool, and what it does in this project. Strictly from the résumé line. */
const stack = [
  {
    label: "QLoRA",
    text: "Fine-tunes the model by training small low-rank adapters on top of frozen, quantized base weights.",
  },
  { label: "Open-weight LLM", text: "The model being tuned to write Sigma rules from threat descriptions." },
  {
    label: "SigmaHQ corpus",
    text: "The public rules it trains on, split by category so whole categories stay out of training.",
  },
  {
    label: "sigma-cli",
    text: "The compiler at the center of the eval harness: it checks each rule and converts it into a backend query.",
  },
  { label: "MLflow", text: "Tracks the benchmark runs comparing the tuned model with base and frontier models." },
];

export default function SigmaLlmPage() {
  return (
    <>
      <PageHeader
        title={sigmaProject.title}
        lead={sigmaProject.question}
        facts={[
          { label: "Status", value: "In progress" },
          { label: "Started", value: "Aug 2026" },
          { label: "Method", value: "QLoRA fine-tuning" },
          { label: "Evaluation", value: "Compiler-based harness (sigma-cli)" },
        ]}
      />

      <Section id="question" label="The question" pace="tight">
        <div className="wrap grid grid-cols-1 gap-x-8 gap-y-6 lg:grid-cols-12">
          <h2 className={`${s.h2} lg:col-span-4`}>The question</h2>
          <div className="measure lg:col-span-7 lg:col-start-6">
            <p>
              The model is being tuned to turn a plain-language threat description into a Sigma rule. The test is
              whether that rule holds up: well-formed, compilable, and looking at the right fields.
            </p>
            <p className="mt-4">
              The data is split by category, not by rule. Whole categories of the public SigmaHQ corpus are held out of
              training, so the test asks for rules in categories the model never saw. Memorizing the corpus
              doesn&rsquo;t help; only generalizing does.
            </p>
            <EvidenceQuote evidence={sigmaProject.summary} size="small" className="mt-8" />
          </div>
        </div>
      </Section>

      <Section id="how-it-works" label="How it works" pace="standard">
        <div className="wrap">
          <div className="measure">
            <h2 className={s.h2}>How it works</h2>
            <p className="body-2 mt-4">
              From public rules to a benchmark, in order. Scroll through the stages, or jump to one from the diagram.
            </p>
          </div>
          <SigmaPipeline idPrefix="cs" className="mt-12 md:mt-16" />
        </div>
      </Section>

      <Section id="harness" label="Try the harness" pace="standard">
        <div className="wrap">
          <HarnessDemo headingLevel="h2" />
        </div>
      </Section>

      <Section id="stack" label="Stack" pace="tight">
        <div className="wrap grid grid-cols-1 gap-x-8 gap-y-6 lg:grid-cols-12">
          <h2 className={`${s.h2} lg:col-span-4`}>Stack</h2>
          <div className="lg:col-span-8 lg:col-start-5">
            <dl className={s.stack}>
              {stack.map((item) => (
                <div key={item.label} className={s.stackRow}>
                  <dt>
                    <Token className="font-semibold">{item.label}</Token>
                  </dt>
                  <dd className="body-2 measure">{item.text}</dd>
                </div>
              ))}
            </dl>
            <Cite evidence={sigmaProject.summary} className="mt-4 block" />
          </div>
        </div>
      </Section>

      <Section id="status" label="Status" pace="standard">
        <div className="wrap grid grid-cols-1 gap-x-8 gap-y-6 lg:grid-cols-12">
          <h2 className={`${s.h2} lg:col-span-4`}>Status</h2>
          <div className="min-w-0 lg:col-span-8 lg:col-start-5">
            <StatusLine />
            <p className="measure mt-5">
              No benchmark results are published yet, so this page shows how the evaluation works rather than how any
              model scored.
            </p>
            <p className="measure mt-4">
              What will be reported: the three checks — schema validity, backend compilation and field correctness —
              for the fine-tuned model, its base model and frontier models, all through the same harness.
            </p>
            <BenchmarkTable className="mt-10" />
          </div>
        </div>
      </Section>
    </>
  );
}
