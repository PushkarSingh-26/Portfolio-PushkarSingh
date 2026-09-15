import type { Metadata } from "next";
import Link from "next/link";
import { profile } from "@/content/profile";
import { timeline, education, kisanDiary } from "@/content/experience";
import { achievements, leadership } from "@/content/recognition";
import { papers } from "@/content/research";
import { ev } from "@/content/types";
import { PrintButton } from "./PrintButton";

export const metadata: Metadata = {
  title: "Résumé — Pushkar Singh",
  description: "Pushkar Singh's résumé: AI/ML engineer working on LLM fine-tuning, evaluation, retrieval and agents.",
};

// The résumé's skills section, verbatim.
const skills = [
  { group: "Programming languages", line: ev("resume", "Programming Languages: Python, Java") },
  { group: "Generative AI and LLM tools", line: ev("resume", "Generative AI & LLM Tools: Transformers (Hugging Face), LangChain, LangGraph, N8N, MCP") },
  { group: "Data science and analytics", line: ev("resume", "Data Science & Analytics: Machine Learning, Pandas, NumPy, Scikit-Learn, TensorFlow, Matplotlib, yfinance, Seaborn, Tableau, Power BI") },
  { group: "Databases", line: ev("resume", "Databases: SQL, MongoDB, Pinecone") },
  { group: "Cloud and DevOps", line: ev("resume", "Cloud & DevOps: AWS (EC2, Lambda, ECS, EKS, RDS, S3, DDB, Aurora, EBS), Azure, Git Bash, GitHub, Terraform(HCL), Jenkins, Ansible") },
  { group: "Tools and frameworks", line: ev("resume", "Tools & Frameworks: Streamlit, Gradio, Google Colab, Jupyter Notebook, MLflow (MLOps), API Integration (FAST API, REST, OpenAI, Gemini, SerpAPI)") },
  { group: "Cyber security", line: ev("resume", "Cyber Security : Digital Accessibility testing (DAT), Configuration Audit") },
  { group: "Foreign language", line: ev("resume", "Foreign Language: German (Conversational)") },
];

const valueOf = (line: string) => line.slice(line.indexOf(":") + 1).trim();

/** Links on screen; plain text in print, so the PDF carries no site-relative links. */
function ScreenLink({ href, children }: { href?: string; children: React.ReactNode }) {
  if (!href) return <>{children}</>;
  return (
    <>
      <Link className="link print:hidden" href={href}>
        {children}
      </Link>
      <span className="hidden print:inline">{children}</span>
    </>
  );
}

function Block({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="grid gap-4 border-t border-rule py-8 md:grid-cols-12 print:grid-cols-12 print:gap-2 print:py-2.5">
      <h2 className="font-semibold text-[1.125rem] md:col-span-3 print:col-span-2 print:text-[10pt]">{title}</h2>
      <div className="md:col-span-9 grid gap-6 print:col-span-10 print:gap-1.5">{children}</div>
    </section>
  );
}

function Item({ title, meta, children }: { title: React.ReactNode; meta?: string; children?: React.ReactNode }) {
  return (
    <article className="print:break-inside-avoid">
      <div className="flex flex-wrap items-baseline justify-between gap-x-6">
        <h3 className="font-semibold print:text-[9.5pt]">{title}</h3>
        <p className="small text-ink-2 tabular-nums print:text-[8.5pt]">{meta}</p>
      </div>
      {children && <div className="mt-1.5 body-2 measure print:mt-0.5 print:max-w-none print:text-[9pt] print:leading-snug">{children}</div>}
    </article>
  );
}

export default function ResumePage() {
  const work = timeline.filter((t) => t.lane === "work").reverse();
  const projects = timeline.filter((t) => t.lane === "project").reverse();
  return (
    <div className="wrap pt-10 pb-20 md:pt-16 print:p-0 print:text-[9pt]">
      <header className="flex flex-wrap items-end justify-between gap-6 pb-8 print:pb-3">
        <div>
          <h1 className="h-section print:text-[22pt]">{profile.name}</h1>
          <p className="lead mt-2 print:mt-0 print:text-[11pt]">{profile.role}</p>
          <p className="small text-ink-2 mt-3">
            <a className="link" href={`mailto:${profile.email}`}>
              {profile.email}
            </a>
            <span className="print:hidden">
              {" "}
              <span aria-hidden="true">/</span>{" "}
              <a className="link" href={profile.links.linkedin} target="_blank" rel="noreferrer">
                LinkedIn
              </a>{" "}
              <span aria-hidden="true">/</span>{" "}
              <a className="link" href={profile.links.github} target="_blank" rel="noreferrer">
                GitHub
              </a>
            </span>
          </p>
        </div>
        <div className="flex flex-wrap gap-3 no-print">
          <a className="btn btn-primary" href={profile.resumePdf} download>
            Download PDF
          </a>
          <PrintButton />
        </div>
      </header>

      <Block title="Experience">
        {work.map((w) => (
          <Item
            key={w.id}
            title={
              <>
                {w.org}
                <span className="font-normal text-ink-2">, {w.roles ? w.roles.map((r) => r.title).join(", then ") : w.title}</span>
              </>
            }
            meta={w.period}
          >
            {w.points.map((p) => (
              <p key={p.quote}>{p.quote}</p>
            ))}
          </Item>
        ))}
        <Item title="Kisan Diary (freelance)" meta="In development">
          <p>{kisanDiary.summary.quote}</p>
        </Item>
      </Block>

      <Block title="Projects">
        {projects.map((p) => (
          <Item
            key={p.id}
            title={<ScreenLink href={p.href}>{p.resumeTitle ?? p.title}</ScreenLink>}
            meta={p.period}
          >
            {p.points.map((pt) => (
              <p key={pt.quote}>{pt.quote}</p>
            ))}
          </Item>
        ))}
      </Block>

      <Block title="Research">
        {papers.map((p) => (
          <Item
            key={p.slug}
            title={<ScreenLink href={`/research/${p.slug}`}>{p.title}</ScreenLink>}
            meta={p.label}
          >
            <p>With {p.authors.slice(1).join(", ")}</p>
          </Item>
        ))}
      </Block>

      <Block title="Education">
        {education.map((e) => (
          <Item key={e.degree} title={`${e.degree}, ${e.school}`} meta={`${e.period}, ${e.grade}`} />
        ))}
      </Block>

      <Block title="Achievements">
        <ul className="grid gap-2 print:gap-0.5">
          {achievements.map((a) => (
            <li key={a.event} className="flex flex-wrap justify-between gap-x-6 print:text-[9pt]">
              <span>
                {a.event}
                {a.organizer && <span className="text-ink-2">, {a.organizer}</span>}, {a.year}
              </span>
              <span className="font-semibold">{a.result}</span>
            </li>
          ))}
        </ul>
      </Block>

      {/* This page mirrors the résumé document, so it lists only résumé-sourced roles. */}
      <Block title="Positions of responsibility">
        {leadership
          .filter((l) => l.evidence.source === "resume")
          .map((l) => (
            <Item key={l.title} title={`${l.title}, ${l.org}`} meta={l.period}>
              <p>{l.evidence.quote}</p>
            </Item>
          ))}
      </Block>

      <Block title="Skills">
        <dl className="grid gap-3 print:gap-0.5">
          {skills.map((s) => (
            <div key={s.group} className="grid gap-1 sm:grid-cols-[14rem_1fr] sm:gap-4 print:grid-cols-[9rem_1fr] print:gap-2">
              <dt className="small text-ink-2 print:text-[8.5pt]">{s.group}</dt>
              <dd className="print:text-[9pt]">{valueOf(s.line.quote)}</dd>
            </div>
          ))}
        </dl>
      </Block>
    </div>
  );
}
