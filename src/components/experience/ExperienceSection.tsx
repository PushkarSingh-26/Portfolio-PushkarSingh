"use client";

import Link from "next/link";
import { useId, useState } from "react";
import { capabilities } from "@/content/capabilities";
import { timeline, NOW, type TimelineEntry } from "@/content/experience";
import type { Area } from "@/content/types";
import { Section } from "@/components/ui/Section";
import { areaTint } from "@/components/ui/Token";
import { usePrefersReducedMotion } from "@/lib/hooks";
import styles from "./Experience.module.css";

/** Which area each step leans on — the tint shift from sky to pollen is the arc. */
const stepArea: Record<string, Area> = {
  globtier: "ml",
  rento: "genai",
  codec: "genai",
  aegisai: "applied",
  "sigma-llm": "llm",
};

const capById = Object.fromEntries(capabilities.map((c) => [c.id, c]));
const steps = timeline.filter((t) => t.lane !== "education");

export function ExperienceSection() {
  const [open, setOpen] = useState<string | null>("codec");
  const [hover, setHover] = useState<string | null>(null);
  const baseId = useId();

  return (
    <Section id="experience" label="Experience">
      <div className="wrap">
        <div className="grid gap-6 lg:grid-cols-12">
          <h2 className="h-section lg:col-span-6">Closer to the model</h2>
          <p className="lead measure lg:col-span-6 lg:pt-3">
            Each step has moved me closer to the language model itself: classic machine learning in 2023, AI inside a
            product in 2025, LLM systems at work in 2026 — and now tuning and evaluating the model.
          </p>
        </div>

        <TimelineStrip highlight={hover ?? open} />

        <ol className={styles.steps}>
          {steps.map((entry) => {
            const isOpen = open === entry.id;
            const panelId = `${baseId}-${entry.id}`;
            const area = stepArea[entry.id];
            return (
              <li
                key={entry.id}
                id={`experience-${entry.id}`}
                className={styles.step}
                data-open={isOpen || undefined}
                onPointerEnter={() => setHover(entry.id)}
                onPointerLeave={() => setHover(null)}
              >
                <span className={styles.node} style={{ background: areaTint[area] }} aria-hidden="true" />
                <button
                  type="button"
                  className={styles.head}
                  aria-expanded={isOpen}
                  aria-controls={panelId}
                  onClick={() => setOpen(isOpen ? null : entry.id)}
                  onFocus={() => setHover(entry.id)}
                  onBlur={() => setHover(null)}
                >
                  <span className={styles.year}>{Math.floor(entry.start)}</span>
                  <span className={styles.stepLine}>{entry.step}</span>
                  <span className={styles.who}>
                    <span className="font-semibold text-ink">{entry.lane === "project" ? entry.title : entry.org}</span>
                    <span className="text-ink-2">
                      {entry.lane === "project" ? `Project, ${entry.period}` : `${entry.title}, ${entry.period}`}
                    </span>
                  </span>
                  <span className={styles.chevron} aria-hidden="true" />
                </button>
                <div id={panelId} className={styles.panel} hidden={!isOpen}>
                  <StepDetail entry={entry} />
                </div>
              </li>
            );
          })}
        </ol>
      </div>
    </Section>
  );
}

function StepDetail({ entry }: { entry: TimelineEntry }) {
  return (
    <div className={styles.detail}>
      <div className={styles.detailMain}>
        {entry.roles && (
          <ol className={styles.roles} aria-label="Roles at Codec Networks">
            {entry.roles.map((r) => (
              <li key={r.title}>
                <span className="font-semibold">{r.title}</span>
                <span className="text-ink-2 small">{r.period}</span>
              </li>
            ))}
          </ol>
        )}
        <ul className={styles.points}>
          {entry.points.map((p) => (
            <li key={p.quote}>
              <p>{p.quote}</p>
            </li>
          ))}
        </ul>
        {entry.id === "codec" && <RagFlow />}
        {entry.href && (
          <p className="mt-6">
            <Link className="link font-semibold" href={entry.href}>
              Open the {entry.title} case study
            </Link>
          </p>
        )}
      </div>
      <div className={styles.detailSide}>
        {entry.capabilities.length > 0 && (
          <div>
            <h3 className="small text-ink-2 mb-2">Capabilities</h3>
            <ul className="flex flex-wrap gap-2">
              {entry.capabilities.map((id) => {
                const c = capById[id];
                if (!c) return null;
                return (
                  <li key={id}>
                    <button
                      type="button"
                      className={`tok tok-${c.area} small ${styles.capBtn}`}
                      onClick={() => {
                        document.getElementById("capabilities")?.scrollIntoView({ behavior: "smooth" });
                        window.setTimeout(
                          () => window.dispatchEvent(new CustomEvent("capmap:select", { detail: { capability: id } })),
                          50,
                        );
                      }}
                    >
                      {c.label}
                    </button>
                  </li>
                );
              })}
            </ul>
          </div>
        )}
        {entry.tools.length > 0 && (
          <div className="mt-5">
            <h3 className="small text-ink-2 mb-2">Tools</h3>
            <ul className="flex flex-wrap gap-2">
              {entry.tools.map((t) => (
                <li key={t} className="tok tok-neutral small">
                  {t}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

/** Codec's retrieval pipeline, as the résumé describes it. The pulse shows data moving. */
function RagFlow() {
  const reduced = usePrefersReducedMotion();
  const nodes = ["350+ policy documents", "pgvector", "Semantic search", "RAG application"];
  return (
    <figure className={styles.rag}>
      <ol className={styles.ragNodes} data-animate={!reduced || undefined}>
        {nodes.map((n, i) => (
          <li key={n} style={{ ["--i" as string]: i }}>
            {n}
          </li>
        ))}
      </ol>
      <figcaption className="small text-ink-2 mt-3">Part of an AI-powered Managed SOC platform.</figcaption>
    </figure>
  );
}

/** Real proportions: one lane each for education, work and projects. */
function TimelineStrip({ highlight }: { highlight: string | null }) {
  const START = 2021.4;
  const span = NOW - START;
  const x = (t: number) => ((t - START) / span) * 100;
  const lanes: { id: TimelineEntry["lane"]; label: string }[] = [
    { id: "education", label: "Education" },
    { id: "work", label: "Work" },
    { id: "project", label: "Projects" },
  ];
  const years = [2022, 2023, 2024, 2025, 2026];

  return (
    <figure className={styles.strip} aria-hidden="true">
      <div className={styles.stripGrid}>
        {lanes.map((lane) => (
          <div key={lane.id} className={styles.lane}>
            <span className={styles.laneLabel}>{lane.label}</span>
            <div className={styles.laneTrack}>
              {timeline
                .filter((t) => t.lane === lane.id)
                .map((t) => {
                  const left = x(t.start);
                  const width = Math.max(0.9, x(t.end ?? NOW) - left);
                  const area = stepArea[t.id];
                  return (
                    <span
                      key={t.id}
                      className={styles.bar}
                      data-active={highlight === t.id || undefined}
                      data-ongoing={t.end === null || undefined}
                      style={{
                        left: `${left}%`,
                        width: `${width}%`,
                        background: area ? areaTint[area] : "var(--color-paper-3)",
                      }}
                      title={`${t.lane === "education" ? t.title : t.lane === "project" ? t.title : t.org}, ${t.period}`}
                    >
                      {t.lane === "education" && <span className={styles.barLabel}>{t.id.toUpperCase()}</span>}
                    </span>
                  );
                })}
            </div>
          </div>
        ))}
        <div className={styles.lane} aria-hidden="true">
          <span />
          <div className={styles.axis}>
            {years.map((y) => (
              <span key={y} style={{ left: `${x(y)}%` }}>
                {y}
              </span>
            ))}
          </div>
        </div>
      </div>
    </figure>
  );
}
