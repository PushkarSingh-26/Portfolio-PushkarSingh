import { sentimentPaper } from "@/content/research";
import { Cite } from "@/components/ui/Evidence";
import { researchVars } from "./tokens";
import styles from "./DataSplit.module.css";

const { split, splitTest } = sentimentPaper;

/** Reads "X: (rows, columns)" from the paper's own shape printout, so the numbers can't drift from the quote. */
function shapeOf(quote: string): [number, number] {
  const m = /X:\s*\((\d+),\s*(\d+)\)/.exec(quote);
  if (!m) throw new Error(`No X shape in quote: ${quote}`);
  return [Number(m[1]), Number(m[2])];
}

const [TRAIN_ROWS, FEATURES] = shapeOf(split.quote);
const [TEST_ROWS] = shapeOf(splitTest.quote);

const fmt = (n: number) => n.toLocaleString("en-US");

/** The date-ordered train/test split as one proportional bar, with the source lines. */
export function DataSplit({ className = "" }: { className?: string }) {
  return (
    <figure className={`${styles.figure} ${className}`} style={researchVars}>
      <div className={styles.bar} aria-hidden="true">
        <span className={styles.train} style={{ flexGrow: TRAIN_ROWS }} />
        <span className={styles.test} style={{ flexGrow: TEST_ROWS }} />
      </div>
      <dl className={styles.labels}>
        <div className={styles.label}>
          <dt className="small text-ink-2">
            <span className={`${styles.swatch} ${styles.train}`} aria-hidden="true" />
            Training set
          </dt>
          <dd className="mono text-ink">{fmt(TRAIN_ROWS)} rows</dd>
        </div>
        <div className={`${styles.label} ${styles.labelEnd}`}>
          <dt className="small text-ink-2">
            <span className={`${styles.swatch} ${styles.test}`} aria-hidden="true" />
            Test set
          </dt>
          <dd className="mono text-ink">{fmt(TEST_ROWS)} rows</dd>
        </div>
      </dl>
      <p className="small text-ink-2 mt-3">
        A date-ordered split. Both sets have <span className="mono text-ink">{FEATURES}</span> features.
      </p>
      <pre className={`mono scroll-x ${styles.source}`} tabIndex={0} aria-label="Source lines from the paper">
        {split.quote}
        {"\n"}
        {splitTest.quote}
      </pre>
      <figcaption>
        <Cite evidence={split} />
      </figcaption>
    </figure>
  );
}
