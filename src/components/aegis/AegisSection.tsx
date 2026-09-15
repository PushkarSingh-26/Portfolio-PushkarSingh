import Link from "next/link";
import { Section } from "@/components/ui/Section";
import { AEGIS_REPO, aegisIntro, aegisPrinciples } from "@/content/aegis";
import { InvestigationJourney } from "./InvestigationJourney";
import styles from "./Aegis.module.css";

/** Home-page section: what AegisAI holds to, then the journey that shows it. */
export function AegisSection() {
  return (
    <Section id="aegisai" label="AegisAI" pace="loose">
      <div className="wrap">
        <div className={styles.intro}>
          <header className={styles.introHead}>
            <h2 className="h-section">{aegisIntro.title}</h2>
            <p className="lead measure mt-6">{aegisIntro.description}</p>
            <p className="small body-2 measure mt-4">
              {aegisIntro.repoName}
            </p>
          </header>
          <div className={styles.principles}>
            <h3 className={styles.principlesTitle}>What it holds to</h3>
            <ul className={styles.principleList}>
              {aegisPrinciples.map((p) => (
                <li key={p.id} className={styles.principle}>
                  <p className={styles.principleText}>{p.text}</p>
                  <p className={`small ${styles.principleMeta}`}>
                    Shown by the {p.device} below.
                  </p>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="mt-14 md:mt-20">
          <InvestigationJourney />
        </div>

        <div className={`${styles.links} mt-12`}>
          <Link href="/work/aegisai" className="btn btn-primary">
            Read the case study
          </Link>
          <a href={AEGIS_REPO} className="btn btn-secondary" target="_blank" rel="noreferrer">
            View the repository
          </a>
        </div>
      </div>
    </Section>
  );
}
