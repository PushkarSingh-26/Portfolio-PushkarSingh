import { foreignLanguages } from "@/content/tools";
import styles from "./capabilities.module.css";

/** Explains the dot on linked tools. Shared by both layouts. */
export function ToolLegend({ className = "" }: { className?: string }) {
  return (
    <p className={className}>
      Tools marked with a <span aria-hidden="true" className={`${styles.dot} ${styles.legendDot}`} />
      <span className="sr-only">dot</span> link to work on this site. The rest are skills listed on my résumé.
    </p>
  );
}

/** The résumé's spoken languages, quietly, at the end of the toolkit. */
export function ForeignLanguages({ className = "" }: { className?: string }) {
  if (foreignLanguages.length === 0) return null;
  return (
    <p className={className}>
      {foreignLanguages.length > 1 ? "Foreign languages" : "Foreign language"}: {foreignLanguages.join(", ")}
    </p>
  );
}
