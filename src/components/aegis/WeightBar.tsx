import type { WeightPart } from "@/content/aegis";
import { Ref } from "./shared";
import styles from "./Artifacts.module.css";

/**
 * A weighted formula drawn to scale: each segment's width is its weight.
 * Not a score — the inputs aren't known here, only the recipe.
 */
export function WeightBar({
  name,
  note,
  parts,
  refs = true,
}: {
  name: string;
  note: string;
  parts: WeightPart[];
  refs?: boolean;
}) {
  const summary = parts.map((p) => `${p.key} ${p.weight.toFixed(2)}`).join(", ");
  return (
    <figure className={styles.weights} style={{ margin: 0 }}>
      <figcaption className={styles.labelRow}>
        <span className={styles.label}>{name}</span>
        <span className={styles.caption}>{note}</span>
      </figcaption>
      <div className={styles.bar} role="img" aria-label={`${name}, weights: ${summary}`}>
        {parts.map((p) => (
          <span
            key={p.key}
            className={`${styles.seg} ${refs && p.ref ? styles.segKnown : ""}`}
            style={{ flexGrow: p.weight, flexBasis: 0 }}
            aria-hidden="true"
          >
            {p.weight.toFixed(2)}
          </span>
        ))}
      </div>
      <ul className={styles.legend}>
        {parts.map((p) => (
          <li key={p.key} className={styles.legendItem}>
            <span className={styles.legendW}>{p.weight.toFixed(2)}</span>
            <span>
              <span className={styles.legendKey}>{p.key}</span> <span className={styles.legendInput}>{p.input}</span>
              {refs && p.ref && <Ref id={p.ref} />}
            </span>
          </li>
        ))}
      </ul>
    </figure>
  );
}
