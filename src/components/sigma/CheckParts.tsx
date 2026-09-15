import { benchmarkRows, sigmaChecks, sigmaProject } from "@/content/sigma";
import { Token } from "@/components/ui/Token";
import { commandFor, fieldCheckMethod, type CheckId, type Variant } from "./data";
import s from "./sigma.module.css";

export type CheckState = "idle" | "checking" | "pass" | "fail";
export type CheckMeta = (typeof sigmaChecks)[number];

/* ---------- Icons (always paired with a text label) ---------- */

export function PassIcon() {
  return (
    <svg viewBox="0 0 16 16" aria-hidden="true" focusable="false">
      <path d="M3 8.5 6.5 12 13 4.5" />
    </svg>
  );
}

export function FailIcon() {
  return (
    <svg viewBox="0 0 16 16" aria-hidden="true" focusable="false">
      <path d="M4 4 12 12M12 4 4 12" />
    </svg>
  );
}

export function PendingIcon() {
  return (
    <svg viewBox="0 0 16 16" aria-hidden="true" focusable="false">
      <circle cx="8" cy="8" r="6" />
      <path d="M8 4.8V8l2.2 1.4" />
    </svg>
  );
}

/** Verification state as icon + text + color. Never color alone. */
export function StatusMark({ state }: { state: CheckState | "pending" }) {
  const text =
    state === "pass"
      ? "Pass"
      : state === "fail"
        ? "Fail"
        : state === "pending"
          ? "Pending"
          : state === "checking"
            ? "Checking…"
            : "Not run";
  return (
    <span className={s.status} data-state={state}>
      {state === "pass" && <PassIcon />}
      {state === "fail" && <FailIcon />}
      {state === "pending" && <PendingIcon />}
      {text}
    </span>
  );
}

function Chevron() {
  return (
    <svg className={s.chev} viewBox="0 0 18 18" aria-hidden="true" focusable="false">
      <path d="M4.5 7 9 11.5 13.5 7" />
    </svg>
  );
}

function FieldList({ items, flag }: { items: string[]; flag?: boolean }) {
  if (items.length === 0) return <span className="small text-ink-2">None</span>;
  return (
    <>
      {items.map((f) => (
        <Token key={f} className={`mono ${s.fieldTok} ${flag ? s.fieldTokFlag : ""}`}>
          {f}
        </Token>
      ))}
    </>
  );
}

/** The exact output behind one check, for one rule variant. */
export function CheckOutput({ id, variant }: { id: CheckId; variant: Variant }) {
  if (id === "fields") {
    const f = variant.checks.fields;
    return (
      <div>
        <dl className={s.fieldGrid}>
          <dt>Used</dt>
          <dd>
            <FieldList items={f.used} />
          </dd>
          <dt>Expected</dt>
          <dd>
            <FieldList items={f.expected} />
          </dd>
          <dt>Missing</dt>
          <dd>
            <FieldList items={f.missing} flag />
          </dd>
          <dt>Unexpected</dt>
          <dd>
            <FieldList items={f.unexpected} flag />
          </dd>
        </dl>
        <p className="small body-2 measure mt-4">{fieldCheckMethod}</p>
      </div>
    );
  }
  const c = variant.checks[id];
  const cmd = commandFor(id);
  return (
    <div>
      <div className={s.outHead}>
        {cmd && <code className={`mono ${s.machine}`}>{cmd}</code>}
        <span className="small text-ink-2">Exit code {c.exitCode}</span>
      </div>
      <pre className={`mono scroll-x ${s.out}`} tabIndex={0} role="group" aria-label={`${id === "schema" ? "sigma check" : "sigma convert"} output`}>
        {c.output}
      </pre>
    </div>
  );
}

/**
 * One check as an expandable row. The <details> element stays mounted across
 * state changes so an open row stays open while a new run resolves.
 */
export function CheckRow({ check, state, variant }: { check: CheckMeta; state: CheckState; variant: Variant }) {
  const resolved = state === "pass" || state === "fail";
  return (
    <li className={s.checkItem}>
      <details>
        <summary className={s.checkSummary}>
          <span>
            <span className={s.checkName}>{check.name}</span>
            <span className={s.checkQuestion}>{check.question}</span>
          </span>
          <StatusMark state={state} />
          <Chevron />
          <span className="sr-only">Show output</span>
        </summary>
        <div className={s.checkBody}>
          {resolved ? (
            <CheckOutput id={check.id} variant={variant} />
          ) : (
            <p className="small text-ink-2">{state === "checking" ? "Checking…" : "Run the checks to see this output."}</p>
          )}
        </div>
      </details>
    </li>
  );
}

/** Rows = models, columns = checks. Every cell is honestly pending. */
export function BenchmarkTable({ className = "" }: { className?: string }) {
  return (
    <figure className={className}>
      <div className="scroll-x" tabIndex={0} role="group" aria-label="Benchmark table, scrollable">
        <table className={s.bench}>
          <caption className="sr-only">Benchmark results by model and check. All results are pending.</caption>
          <thead>
            <tr>
              <th scope="col">Model</th>
              {sigmaChecks.map((c) => (
                <th key={c.id} scope="col">
                  {c.name}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {benchmarkRows.map((row) => (
              <tr key={row}>
                <th scope="row">{row}</th>
                {sigmaChecks.map((c) => (
                  <td key={c.id}>
                    <span className={s.pendingSlot}>
                      <PendingIcon />
                      Pending
                    </span>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <figcaption className={s.caption}>
        Runs are tracked in MLflow. Results will appear here when benchmarking is complete.
      </figcaption>
    </figure>
  );
}

/** "In progress" as a text label with a hold-colored dot, followed by the status sentence. */
export function StatusLine({ className = "" }: { className?: string }) {
  const label = "In progress";
  const status = sigmaProject.status;
  const rest = status.startsWith(label) ? status.slice(label.length) : ` ${status}`;
  return (
    <p className={`small flex gap-2 ${className}`}>
      <svg className={`${s.statusDot} text-hold`} viewBox="0 0 8 8" aria-hidden="true" focusable="false">
        <circle cx="4" cy="4" r="4" fill="currentColor" />
      </svg>
      <span>
        <span className="font-semibold text-hold">{label}</span>
        <span className="text-ink-2">{rest}</span>
      </span>
    </p>
  );
}
