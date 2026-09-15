"use client";

import Link from "next/link";
import { useState } from "react";
import { EvidenceQuote } from "@/components/ui/Evidence";
import { Token } from "@/components/ui/Token";
import type { WorkItem } from "@/content/types";
import { kindLabel, type Mode, type Readout } from "./model";

const VISIBLE = 3;

/** Work title as a link when it has somewhere to go. */
export function WorkLink({ work, className = "" }: { work: WorkItem; className?: string }) {
  if (!work.href) return <span className={`font-semibold ${className}`}>{work.title}</span>;
  return (
    <Link href={work.href} className={`link font-semibold ${className}`}>
      {work.title}
    </Link>
  );
}

export function emptyToolMessage(label: string) {
  return `${label} is in my résumé skills. It isn't tied to a specific project on this site.`;
}

/**
 * The readout under the map: every relationship the lines show, as text, with the
 * sentence that backs it. Aligned to the map's 12-column grid — heading under the
 * capability column, work under the gutter, quotes under the work column.
 */
export function EvidencePanel({
  id,
  mode,
  readout,
  previewing,
}: {
  id: string;
  mode: Mode;
  readout: Readout | null;
  previewing: boolean;
}) {
  return (
    <div id={id} aria-live="polite" className="mt-14 grid min-h-[17rem] grid-cols-12 gap-x-6 border-t border-rule pt-8">
      {readout && <PanelBody key={readout.key} mode={mode} readout={readout} previewing={previewing} />}
    </div>
  );
}

function PanelBody({ mode, readout, previewing }: { mode: Mode; readout: Readout; previewing: boolean }) {
  const [expanded, setExpanded] = useState(false);
  const total = readout.rows.length;
  const hidden = expanded ? 0 : Math.max(0, total - VISIBLE);
  const shown = hidden > 0 ? readout.rows.slice(0, VISIBLE) : readout.rows;

  const heading =
    readout.kind === "forward" ? `Where “${readout.item.label}” shows up` : `What shows up in “${readout.work.title}”`;

  return (
    <>
      <div className="col-span-4">
        <h3 className="h-sub pr-6">{heading}</h3>
        {previewing && (
          <p className="small mt-3 text-ink-2" aria-hidden="true">
            Previewing. Click or press Enter to pin it.
          </p>
        )}
      </div>

      {total === 0 ? (
        <p className="body-2 col-span-5 col-start-8 max-w-[48ch]">
          {readout.kind === "forward"
            ? emptyToolMessage(readout.item.label)
            : `None of the listed ${mode === "toolkit" ? "tools" : "capabilities"} is linked to ${readout.work.title} on this site.`}
        </p>
      ) : (
        <ul className="col-span-8 col-start-5 grid grid-cols-subgrid gap-y-7">
          {readout.kind === "forward"
            ? (shown as Extract<Readout, { kind: "forward" }>["rows"]).map((r) => (
                <li key={r.work.id} className="col-span-8 grid grid-cols-subgrid">
                  <div className="col-span-3">
                    <WorkLink work={r.work} />
                    <p className="small mt-1 text-ink-2">
                      {kindLabel[r.work.kind]}, {r.work.when}
                    </p>
                  </div>
                  <EvidenceQuote evidence={r.evidence} className="col-span-5 max-w-[56ch]" />
                </li>
              ))
            : (shown as Extract<Readout, { kind: "reverse" }>["rows"]).map((r) => (
                <li key={r.evidence.quote} className="col-span-8 grid grid-cols-subgrid">
                  <ul className="col-span-3 flex flex-wrap content-start gap-1.5" aria-label="Backed by this sentence">
                    {r.items.map((it) => (
                      <li key={it.key} className="small">
                        <Token area={it.area ?? "neutral"}>{it.label}</Token>
                      </li>
                    ))}
                  </ul>
                  <EvidenceQuote evidence={r.evidence} className="col-span-5 max-w-[56ch]" />
                </li>
              ))}
          {hidden > 0 && (
            <li className="col-span-5 col-start-4">
              <button type="button" className="btn btn-quiet -ml-[0.7em]" onClick={() => setExpanded(true)}>
                Show {hidden} more
              </button>
            </li>
          )}
        </ul>
      )}
    </>
  );
}
