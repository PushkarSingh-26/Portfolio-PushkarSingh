import { achievements, beyondWork, leadership } from "@/content/recognition";
import { achievementPhotos } from "@/content/photos";
import { PhotoEvidence } from "./PhotoEvidence";
import { education } from "@/content/experience";
import { Section } from "@/components/ui/Section";

/** A precise results list — the type does the work, no badges. */
export function RecognitionSection() {
  return (
    <Section id="recognition" label="Recognition">
      <div className="wrap">
        <h2 className="h-section">Recognition and leadership</h2>

        <div className="mt-12 grid gap-14 lg:grid-cols-12">
          <div className="lg:col-span-7">
            <h3 className="h-sub">Competitions</h3>
            <ul className="mt-5 border-t border-rule">
              {achievements.map((a) => (
                <li
                  key={a.event}
                  className="grid grid-cols-[3.25rem_1fr] gap-x-4 gap-y-1 border-b border-rule py-4 sm:grid-cols-[3.25rem_1fr_auto] sm:items-baseline"
                >
                  <span className="small text-ink-2 tabular-nums">{a.year}</span>
                  <span>
                    <span className="font-semibold">{a.event}</span>
                    {a.organizer && <span className="text-ink-2">, {a.organizer}</span>}
                    {achievementPhotos[a.event] && (
                      <span className="mt-2 flex">
                        <PhotoEvidence
                          photo={achievementPhotos[a.event]}
                          caption={`${a.event}${a.organizer ? `, ${a.organizer}` : ""}, ${a.year}. ${a.result}.`}
                        />
                      </span>
                    )}
                  </span>
                  <span className="col-start-2 sm:col-start-3 sm:text-right font-semibold text-ink">{a.result}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="lg:col-span-4 lg:col-start-9">
            <h3 className="h-sub">Leadership</h3>
            <ul className="mt-5 border-t border-rule">
              {leadership.map((l) => (
                <li key={l.title} className="border-b border-rule py-4">
                  <p className="font-semibold">{l.title}</p>
                  <p className="small text-ink-2">{l.period ? `${l.org}, ${l.period}` : l.org}</p>
                  {l.summary && <p className="mt-2 small">{l.summary}</p>}
                </li>
              ))}
            </ul>

            <h3 className="h-sub mt-12">Outside the work</h3>
            <ul className="mt-5 border-t border-rule">
              <li className="border-b border-rule py-4">
                <p className="font-semibold">{beyondWork.karate.title}</p>
                <dl className="mt-2">
                  {beyondWork.karate.medals.map((m) => (
                    <div key={m.label} className="flex items-baseline justify-between gap-4 py-0.5">
                      <dt className="small text-ink-2">{m.label}</dt>
                      <dd className="font-semibold tabular-nums">{m.count}</dd>
                    </div>
                  ))}
                </dl>
              </li>
              <li className="border-b border-rule py-4">
                <p className="font-semibold">{beyondWork.esports.title}</p>
                <p className="small text-ink-2">{beyondWork.esports.result}</p>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </Section>
  );
}

export function EducationSection() {
  return (
    <Section id="education" label="Education" pace="tight">
      <div className="wrap grid gap-8 lg:grid-cols-12">
        <h2 className="h-sub lg:col-span-4 text-[clamp(1.75rem,3.4vw,2.5rem)]!">Education</h2>
        <ul className="lg:col-span-8 border-t border-rule">
          {education.map((e) => (
            <li
              key={e.degree}
              className="grid gap-1 border-b border-rule py-4 sm:grid-cols-[1fr_auto] sm:gap-x-8 sm:items-baseline"
            >
              <span>
                <span className="font-semibold">{e.degree}</span>
                <span className="block text-ink-2 small">{e.school}</span>
              </span>
              <span className="small text-ink-2 tabular-nums sm:text-right">
                {e.period}
                <span className="block font-semibold text-ink">{e.grade}</span>
              </span>
            </li>
          ))}
        </ul>
      </div>
    </Section>
  );
}
