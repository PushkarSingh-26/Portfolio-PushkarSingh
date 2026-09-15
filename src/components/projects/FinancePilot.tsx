"use client";

import { useRef, useState } from "react";
import { financePilot, routes, chartCountEvidence, type Route } from "@/content/finance-pilot";
import styles from "./FinancePilot.module.css";

/**
 * Finance Pilot: the product on the left, and on the right the three routes a
 * question can take through the backend. Choosing a route replays its path;
 * that motion is the only animation here and it only runs on a click.
 */
export function FinancePilot() {
  const [active, setActive] = useState<Route["id"]>("single");
  const tabs = useRef<(HTMLButtonElement | null)[]>([]);
  const route = routes.find((r) => r.id === active)!;
  const chartTotal = routes.reduce((n, r) => n + (r.output.charts?.length ?? 0), 0);

  const onKey = (e: React.KeyboardEvent, i: number) => {
    const last = routes.length - 1;
    const next = e.key === "ArrowRight" ? (i === last ? 0 : i + 1) : e.key === "ArrowLeft" ? (i === 0 ? last : i - 1) : e.key === "Home" ? 0 : e.key === "End" ? last : null;
    if (next === null) return;
    e.preventDefault();
    setActive(routes[next].id);
    tabs.current[next]?.focus();
  };

  return (
    <div id="finance-pilot" className="grid gap-12 lg:grid-cols-12">
      <div className="lg:col-span-5">
        <p className="small text-ink-2">
          Project,{" "}
          <a className="link" href={financePilot.repo} target="_blank" rel="noreferrer">
            {financePilot.repoName} on GitHub
          </a>
        </p>
        <h3 className="h-sub mt-2 text-[clamp(1.75rem,3.4vw,2.5rem)]!">{financePilot.title}</h3>
        <p className="mt-4 measure">{financePilot.summary}</p>

        <h4 className="mt-8 small text-ink-2">Built with</h4>
        <ul className="mt-2 flex flex-wrap gap-2" aria-label="Technologies">
          {financePilot.stack.map((s) => (
            <li key={s.label} className={`tok ${s.area ? `tok-${s.area}` : "tok-neutral"} small font-semibold`}>
              {s.label}
            </li>
          ))}
        </ul>

        <h4 className="mt-8 small text-ink-2">Also in the app</h4>
        <ul className="mt-2 border-t border-rule">
          {financePilot.extras.map((x) => (
            <li key={x.text} className="flex flex-wrap items-baseline justify-between gap-x-4 border-b border-rule py-2.5">
              <span className="small">{x.text}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="lg:col-span-7 lg:col-start-6">
        <h4 className="font-semibold">Three ways a question gets answered</h4>
        <p className="small text-ink-2 mt-1">Pick a kind of question to follow its path through the backend.</p>

        <div role="tablist" aria-label="Kinds of question" className={`${styles.tabs} mt-4`}>
          {routes.map((r, i) => (
            <button
              key={r.id}
              ref={(el) => {
                tabs.current[i] = el;
              }}
              role="tab"
              type="button"
              id={`fp-tab-${r.id}`}
              aria-selected={r.id === active}
              aria-controls="fp-panel"
              tabIndex={r.id === active ? 0 : -1}
              className={styles.tab}
              onClick={() => setActive(r.id)}
              onKeyDown={(e) => onKey(e, i)}
            >
              {r.tab}
            </button>
          ))}
        </div>

        {/* Keyed by route so the path replays when the choice changes. */}
        <div
          key={route.id}
          role="tabpanel"
          id="fp-panel"
          aria-labelledby={`fp-tab-${route.id}`}
          className={styles.panel}
          aria-live="polite"
        >
          <p className="small text-ink-2">
            Example question
          </p>
          <p className={styles.question}>{route.example}</p>

          <ol className={styles.steps}>
            {route.steps.map((s, i) => (
              <li
                key={s.text}
                className={styles.step}
                data-area={s.area}
                style={{ "--i": i } as React.CSSProperties}
              >
                <span className={styles.dot} aria-hidden="true" />
                <span className={styles.stepText}>{s.text}</span>
              </li>
            ))}
          </ol>

          <div className={styles.output} style={{ "--i": route.steps.length } as React.CSSProperties}>
            <p className="small text-ink-2">Result</p>
            <p className="font-semibold">{route.output.label}</p>
            {route.output.charts ? (
              <ul className="mt-2 flex flex-wrap gap-2" aria-label="Chart types on this path">
                {route.output.charts.map((c) => (
                  <li key={c} className="tok tok-neutral small">
                    {c}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="small text-ink-2 mt-1">{route.output.note}</p>
            )}
          </div>
        </div>

        <p className="mt-4 small text-ink-2">
          {chartTotal} chart types in all, each drawn by its own Plotly function.
        </p>
      </div>
    </div>
  );
}
