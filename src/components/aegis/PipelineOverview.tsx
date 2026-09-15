import { stages } from "@/content/aegis";
import styles from "./Aegis.module.css";

/** The nine stages as one labelled track, with the optional LLM and the human step marked. */
export function PipelineOverview() {
  return (
    <ol className={styles.pipeline} aria-label="AegisAI pipeline">
      {stages.map((s, i) => (
        <li key={s.id} className={styles.pStage}>
          <span className={styles.pDot} aria-hidden="true" />
          <span className={`small ${styles.pNo}`}>{i + 1}</span>
          <div className={styles.pBody}>
            <span className={styles.pName}>{s.name}</span>
            <p className={`small ${styles.pText}`}>
              {s.oneLine}
            </p>
            <span className={`mono ${styles.pComponent}`}>{s.component}</span>
            {s.id === "analyst" && (
              <p className={`${styles.pNote} ${styles.pLane}`}>
                <span className="tok tok-llm mono">AI_PROVIDER</span>
                <span>Optional LLM narration. It touches this stage only, and it&apos;s off by default.</span>
              </p>
            )}
            {s.id === "approval" && (
              <p className={`${styles.pNote} ${styles.pPerson}`}>A person decides here.</p>
            )}
          </div>
        </li>
      ))}
    </ol>
  );
}
