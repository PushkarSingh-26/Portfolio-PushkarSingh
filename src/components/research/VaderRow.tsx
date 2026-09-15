import { sentimentPaper } from "@/content/research";
import { researchVars } from "./tokens";
import styles from "./VaderRow.module.css";

const row = sentimentPaper.sampleRow;

/** Position on a −1…+1 axis, as a percentage from the left. */
const onAxis = (v: number) => ((v + 1) / 2) * 100;

const parts = [
  { id: "negative", label: "Negative", value: row.negative, className: styles.neg },
  { id: "neutral", label: "Neutral", value: row.neutral, className: styles.neu },
  { id: "positive", label: "Positive", value: row.positive, className: styles.pos },
] as const;

/**
 * One headline and the four VADER scores the paper printed for it (Figure 4):
 * compound on a diverging −1…+1 axis, and negative/neutral/positive as one 100% bar.
 */
export function VaderRow({ className = "" }: { className?: string }) {
  const at = onAxis(row.compound);
  const zero = onAxis(0);
  const barLeft = Math.min(at, zero);
  const barWidth = Math.abs(at - zero);

  return (
    <figure className={`${styles.row} ${className}`} style={researchVars}>
      <div>
        <p className={styles.headline}>“{row.headline}”</p>
        <p className="mono text-ink-2 mt-1">{row.date}</p>
      </div>

      <div>
        <p className="small text-ink-2">Compound</p>
        <div className={styles.axis} aria-hidden="true">
          <span className={`mono ${styles.value}`} style={{ right: `${100 - at}%` }}>
            {row.compound.toFixed(4)}
          </span>
          <span className={styles.axisLine} />
          <span className={styles.tick} style={{ left: "0%" }} />
          <span className={styles.tick} style={{ left: `${zero}%` }} />
          <span className={styles.tick} style={{ left: "100%" }} />
          <span
            className={`${styles.bar} ${row.compound < 0 ? styles.barNeg : ""}`}
            style={{ left: `${barLeft}%`, width: `${barWidth}%` }}
          />
          <span className={styles.marker} style={{ left: `${at}%` }} />
        </div>
        <div className={styles.axisLabels} aria-hidden="true">
          <span className="mono">−1</span>
          <span className="mono">0</span>
          <span className="mono">+1</span>
        </div>
        <p className="sr-only">Compound score {row.compound}, on a scale from −1 to +1.</p>
      </div>

      <div>
        <p className="small text-ink-2">Negative, neutral and positive</p>
        <div className={styles.stack} aria-hidden="true">
          {parts.map((p) => (
            <span key={p.id} className={`${styles.seg} ${p.className}`} style={{ flexGrow: p.value }} />
          ))}
        </div>
        <dl className={styles.legend}>
          {parts.map((p) => (
            <div key={p.id} className={styles.legendItem}>
              <span className={`${styles.swatch} ${p.className}`} aria-hidden="true" />
              <dt className="small text-ink-2">{p.label}</dt>
              <dd className="mono text-ink">{p.value.toFixed(3)}</dd>
            </div>
          ))}
        </dl>
      </div>

      <figcaption className="small text-ink-2">
        One row from the paper&rsquo;s results (Figure 4).
      </figcaption>
    </figure>
  );
}
