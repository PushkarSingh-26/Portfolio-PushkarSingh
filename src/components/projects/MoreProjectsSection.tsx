import { kisanDiary } from "@/content/experience";
import { Section } from "@/components/ui/Section";
import { FinancePilot } from "./FinancePilot";

/**
 * Projects beyond the two flagships. Finance Pilot leads because it is the AI
 * work; Kisan Diary follows as applied product engineering.
 */
export function MoreProjectsSection() {
  return (
    <Section id="projects" label="More projects">
      <div className="wrap">
        <h2 className="h-section">More projects</h2>

        <div className="mt-12">
          <FinancePilot />
        </div>

        <div id="kisan-diary" className="mt-20 grid gap-10 border-t border-rule pt-14 lg:grid-cols-12 lg:items-center">
          <div className="lg:col-span-5">
            <p className="small text-ink-2">Freelance, in development</p>
            <h3 className="h-sub mt-2 text-[clamp(1.75rem,3.4vw,2.5rem)]!">Kisan Diary</h3>
            <p className="mt-4 measure">{kisanDiary.summary.quote}</p>
          </div>
          <figure className="lg:col-span-6 lg:col-start-7">
            <div className="rounded-lg border-[1.5px] border-ink p-4 sm:p-6">
              <ul className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                {kisanDiary.modules.map((m) => (
                  <li
                    key={m}
                    className={`tok ${m.startsWith("AI") ? "tok-genai" : "tok-neutral"} min-h-11 items-center! px-3! font-semibold`}
                  >
                    {m}
                  </li>
                ))}
              </ul>
              <p className="mt-4 small text-ink-2">One platform, designed for future government deployment.</p>
            </div>
            <figcaption className="sr-only">The six modules Kisan Diary brings together</figcaption>
          </figure>
        </div>
      </div>
    </Section>
  );
}
