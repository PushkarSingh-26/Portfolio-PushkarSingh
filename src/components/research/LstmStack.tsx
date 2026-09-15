import { sentimentPaper } from "@/content/research";
import { Cite } from "@/components/ui/Evidence";
import styles from "./LstmStack.module.css";

/**
 * The network exactly as the published notebook builds it: input at the top,
 * one value out at the bottom. Static on purpose — this is a spec to read.
 */
export function LstmStack({ className = "" }: { className?: string }) {
  const m = sentimentPaper.model;
  return (
    <div className={`grid gap-10 lg:grid-cols-12 ${className}`}>
      <figure className="lg:col-span-7">
        <p className={styles.io}>
          <span className="small text-ink-2">In</span>
          <span>{m.input.text}</span>
          <Cite evidence={m.input.evidence} compact />
        </p>
        <ol className={styles.stack} aria-label="Layers, top to bottom">
          {m.layers.map((l, i) => (
            <li key={i} className={styles.layer} data-kind={l.kind}>
              <span className="mono text-ink">{l.spec}</span>
              {l.note && <span className="small text-ink-2">{l.note}</span>}
            </li>
          ))}
        </ol>
        <p className={styles.io}>
          <span className="small text-ink-2">Out</span>
          <span>{m.target.text}</span>
          <Cite evidence={m.target.evidence} compact />
        </p>
        <figcaption className="mt-3">
          <Cite evidence={m.layersEvidence} />
        </figcaption>
      </figure>

      <div className="lg:col-span-4 lg:col-start-9">
        <h3 className="font-semibold">Training</h3>
        <dl className="mt-3 border-t border-rule">
          {m.training.map((t) => (
            <div key={t.label} className="flex items-baseline justify-between gap-4 border-b border-rule py-2.5">
              <dt className="small text-ink-2">{t.label}</dt>
              <dd className="font-semibold">{t.value}</dd>
            </div>
          ))}
        </dl>
        <p className="mt-3 small">{m.scaling.text}</p>
        <p className="mt-3">
          <Cite evidence={m.trainingEvidence} />
        </p>
      </div>
    </div>
  );
}
