import { Section } from "@/components/ui/Section";
import { CapabilityMap } from "./CapabilityMap";

/**
 * "Where did he actually use this?" — an attention view from capabilities (or tools)
 * to the work they show up in, each link backed by a verbatim sentence.
 */
export function CapabilitiesSection() {
  return (
    <Section id="capabilities" label="Capabilities">
      <div className="wrap">
        <h2 className="h-section">What I work on, and where</h2>
        <p className="lead mt-5 max-w-[60ch]">
          Pick a capability to see the work it shows up in, and the sentence from my résumé, papers or project docs
          that backs it.
        </p>
        <CapabilityMap />
      </div>
    </Section>
  );
}
