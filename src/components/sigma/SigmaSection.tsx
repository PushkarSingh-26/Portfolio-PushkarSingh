import Link from "next/link";
import { sigmaProject } from "@/content/sigma";
import { Section } from "@/components/ui/Section";
import { StatusLine } from "./CheckParts";
import { HarnessDemo } from "./HarnessDemo";
import { SigmaPipeline } from "./SigmaPipeline";

/** Home page section: the Sigma rule LLM, told through its evaluation loop. */
export function SigmaSection() {
  return (
    <Section id="sigma-llm" label="Sigma rule LLM" pace="loose">
      <div className="wrap">
        <header className="grid gap-x-8 lg:grid-cols-12">
          <h2 className="h-section max-w-[20ch] lg:col-span-10">{sigmaProject.title}</h2>
          <div className="mt-8 lg:col-span-7">
            <StatusLine />
            <p className="lead measure mt-5">{sigmaProject.question}</p>
            <Link href="/work/sigma-llm" className="link mt-4 inline-flex min-h-11 items-center font-semibold">
              Read the case study
            </Link>
          </div>
        </header>

        <SigmaPipeline idPrefix="sigma" className="mt-14 md:mt-20" />

        <HarnessDemo headingLevel="h3" className="mt-20 md:mt-32" />
      </div>
    </Section>
  );
}
