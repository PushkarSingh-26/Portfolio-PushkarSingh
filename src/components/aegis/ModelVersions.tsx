import { modelVersions } from "@/content/aegis";
import styles from "./Artifacts.module.css";

/** V1 → V6: what each risk-model version adds, and the feature it leans on most. */
export function ModelVersions({ showTop = true }: { showTop?: boolean }) {
  return (
    <ol className={styles.versions} aria-label="Risk model versions">
      {modelVersions.map((v) => (
        <li key={v.v} className={styles.version}>
          <span className={styles.versionV}>{v.v}</span>
          <span className="block mt-1">{v.adds}</span>
          {showTop && (
            <span className={styles.versionTop}>
              <span className="sr-only">Top feature: </span>
              {v.top}
            </span>
          )}
        </li>
      ))}
    </ol>
  );
}
