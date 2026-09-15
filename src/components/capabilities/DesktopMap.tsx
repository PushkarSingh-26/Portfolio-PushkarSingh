"use client";

import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
  type CSSProperties,
  type FocusEvent,
  type KeyboardEvent,
  type PointerEvent,
} from "react";
import { areaLine, areaTint, areaTok } from "@/components/ui/Token";
import { work } from "@/content/work";
import { AttentionLines, type Line } from "./AttentionLines";
import { EvidencePanel } from "./EvidencePanel";
import { ForeignLanguages, ToolLegend } from "./ToolLegend";
import {
  TOOL_LINE,
  TOOL_TINT,
  flatByMode,
  groupsByMode,
  kindLabel,
  type Focus,
  type LeftItem,
  type Mode,
  type Pin,
  type Readout,
} from "./model";
import styles from "./capabilities.module.css";

interface Pt {
  x: number;
  y: number;
}

interface Geom {
  w: number;
  h: number;
  /** Right edge of the left column: lines leave the column here. */
  edge: number;
  L: Record<string, Pt>;
  R: Record<string, Pt>;
}

const r1 = (n: number) => Math.round(n * 2) / 2;

/**
 * Cubic bezier from a left item (right edge, vertical centre) to a work row (left
 * edge, vertical centre). Chips inside the column first run straight to the column
 * edge, under their neighbours, so the curve only happens in the gutter.
 * Reverse paths start at the work row, so they draw from the work outwards.
 */
function curve(a: Pt, edge: number, b: Pt, reverse: boolean) {
  const c = Math.max(24, (b.x - edge) * 0.5);
  if (!reverse) return `M${a.x} ${a.y}H${edge}C${edge + c} ${a.y} ${b.x - c} ${b.y} ${b.x} ${b.y}`;
  return `M${b.x} ${b.y}C${b.x - c} ${b.y} ${edge + c} ${a.y} ${edge} ${a.y}H${a.x}`;
}

const tintOf = (item: LeftItem) => (item.area ? areaTint[item.area] : TOOL_TINT);
const lineOf = (item: LeftItem) => (item.area ? areaLine[item.area] : TOOL_LINE);

export interface DesktopMapProps {
  mode: Mode;
  pin: Pin;
  readout: Readout | null;
  previewing: boolean;
  /** Has the visitor done anything yet? Until then lines appear without drawing. */
  engaged: boolean;
  reduced: boolean;
  /** Only measure when this layout is the one on screen. */
  enabled: boolean;
  tabL: string;
  tabR: string;
  panelId: string;
  onPreview: (f: Focus | null) => void;
  onPin: (f: Focus) => void;
  onRoveL: (key: string) => void;
  onRoveR: (id: string) => void;
}

export function DesktopMap({
  mode,
  pin,
  readout,
  previewing,
  engaged,
  reduced,
  enabled,
  tabL,
  tabR,
  panelId,
  onPreview,
  onPin,
  onRoveL,
  onRoveR,
}: DesktopMapProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const leftColRef = useRef<HTMLDivElement>(null);
  const workColRef = useRef<HTMLUListElement>(null);
  const leftEls = useRef(new Map<string, HTMLButtonElement>());
  const workEls = useRef(new Map<string, HTMLButtonElement>());
  const [geom, setGeom] = useState<Geom | null>(null);

  // ---------- Geometry ----------

  const measure = useCallback(() => {
    const root = mapRef.current;
    const col = leftColRef.current;
    if (!root || !col) return;
    const rb = root.getBoundingClientRect();
    if (rb.width === 0 || rb.height === 0) return; // hidden layout
    const L: Record<string, Pt> = {};
    const R: Record<string, Pt> = {};
    // A line leaves from the end of its item's visual row. For full-width capability
    // rows that's the row itself; for wrapped tool chips it's the last chip on the same
    // line, so the stroke never threads through the gaps between chips.
    const lefts = [...root.querySelectorAll<HTMLElement>("[data-l]")].map((el) => ({
      el,
      list: el.closest("ul"),
      r: el.getBoundingClientRect(),
    }));
    for (const a of lefts) {
      const cy = a.r.top + a.r.height / 2;
      let end = a.r.right;
      for (const b of lefts) {
        if (b.list === a.list && Math.abs(b.r.top + b.r.height / 2 - cy) < a.r.height / 2) end = Math.max(end, b.r.right);
      }
      L[a.el.dataset.l as string] = { x: r1(end - rb.left), y: r1(cy - rb.top) };
    }
    root.querySelectorAll<HTMLElement>("[data-r]").forEach((el) => {
      const r = el.getBoundingClientRect();
      R[el.dataset.r as string] = { x: r1(r.left - rb.left), y: r1(r.top + r.height / 2 - rb.top) };
    });
    const next: Geom = { w: r1(rb.width), h: r1(rb.height), edge: r1(col.getBoundingClientRect().right - rb.left), L, R };
    setGeom((prev) => (prev && JSON.stringify(prev) === JSON.stringify(next) ? prev : next));
  }, []);

  // Before paint whenever the column contents change.
  useLayoutEffect(() => {
    if (enabled) measure();
  }, [enabled, mode, measure]);

  useEffect(() => {
    if (!enabled) return;
    const root = mapRef.current;
    if (!root) return;
    let raf = 0;
    let alive = true;
    const schedule = () => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(measure);
    };
    const ro = new ResizeObserver(measure);
    ro.observe(root);
    if (leftColRef.current) ro.observe(leftColRef.current);
    if (workColRef.current) ro.observe(workColRef.current);
    window.addEventListener("resize", schedule);
    document.fonts?.ready.then(() => {
      if (alive) measure();
    });
    return () => {
      alive = false;
      cancelAnimationFrame(raf);
      ro.disconnect();
      window.removeEventListener("resize", schedule);
    };
  }, [enabled, mode, measure]);

  // ---------- What's lit ----------

  const litLeft = useMemo(() => {
    if (!readout) return new Set<string>();
    return new Set(readout.kind === "forward" ? [readout.item.key] : readout.items.map((i) => i.key));
  }, [readout]);

  const workTint = useMemo(() => {
    const t = new Map<string, string>();
    if (!readout) return t;
    if (readout.kind === "forward") {
      for (const r of readout.rows) t.set(r.work.id, tintOf(readout.item));
    } else {
      t.set(readout.work.id, mode === "toolkit" ? TOOL_TINT : areaTint[readout.work.area]);
    }
    return t;
  }, [readout, mode]);

  const lines = useMemo<Line[]>(() => {
    if (!geom || !readout) return [];
    const out: Line[] = [];
    if (readout.kind === "forward") {
      const a = geom.L[readout.item.key];
      if (!a) return out;
      for (const r of readout.rows) {
        const b = geom.R[r.work.id];
        if (b) out.push({ key: `${readout.key}>${r.work.id}`, d: curve(a, geom.edge, b, false), color: lineOf(readout.item) });
      }
    } else {
      const b = geom.R[readout.work.id];
      if (!b) return out;
      for (const it of readout.items) {
        const a = geom.L[it.key];
        if (a) out.push({ key: `${readout.key}<${it.key}`, d: curve(a, geom.edge, b, true), color: lineOf(it) });
      }
    }
    return out;
  }, [geom, readout]);

  // ---------- Keyboard: roving focus ----------

  const flat = flatByMode[mode];

  const onLeftKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
    const i = flat.findIndex((it) => it.key === tabL);
    const back = e.key === "ArrowUp" || (mode === "toolkit" && e.key === "ArrowLeft");
    const fwd = e.key === "ArrowDown" || (mode === "toolkit" && e.key === "ArrowRight");
    let n = -1;
    if (back) n = Math.max(0, i - 1);
    else if (fwd) n = Math.min(flat.length - 1, i + 1);
    else if (e.key === "Home") n = 0;
    else if (e.key === "End") n = flat.length - 1;
    if (n < 0) return;
    e.preventDefault();
    leftEls.current.get(flat[n].key)?.focus();
  };

  const onWorkKeyDown = (e: KeyboardEvent<HTMLUListElement>) => {
    const i = work.findIndex((w) => w.id === tabR);
    let n = -1;
    if (e.key === "ArrowUp") n = Math.max(0, i - 1);
    else if (e.key === "ArrowDown") n = Math.min(work.length - 1, i + 1);
    else if (e.key === "Home") n = 0;
    else if (e.key === "End") n = work.length - 1;
    if (n < 0) return;
    e.preventDefault();
    workEls.current.get(work[n].id)?.focus();
  };

  // Leaving the map (by mouse or focus) returns to the pinned view.
  const onBlur = (e: FocusEvent<HTMLDivElement>) => {
    if (!mapRef.current?.contains(e.relatedTarget as Node | null)) onPreview(null);
  };
  const onPointerLeave = (e: PointerEvent<HTMLDivElement>) => {
    if (e.pointerType === "mouse") onPreview(null);
  };

  const leftProps = (it: LeftItem) => {
    const f: Focus = { side: "L", key: it.key };
    return {
      type: "button" as const,
      "data-l": it.key,
      "data-lit": litLeft.has(it.key) ? "" : undefined,
      "aria-pressed": !pin.work && pin.left === it.key,
      "aria-controls": panelId,
      tabIndex: it.key === tabL ? 0 : -1,
      style: { "--tint": tintOf(it) } as CSSProperties,
      ref: (el: HTMLButtonElement | null) => {
        if (el) leftEls.current.set(it.key, el);
        else leftEls.current.delete(it.key);
      },
      onFocus: () => {
        onRoveL(it.key);
        onPreview(f);
      },
      onPointerEnter: (e: PointerEvent) => {
        if (e.pointerType === "mouse") onPreview(f);
      },
      onClick: () => onPin(f),
    };
  };

  return (
    <div className={styles.desktopOnly}>
      <div
        ref={mapRef}
        className="relative grid grid-cols-12 gap-x-6"
        onBlur={onBlur}
        onPointerLeave={onPointerLeave}
        data-capmap-root=""
      >
        {geom && <AttentionLines width={geom.w} height={geom.h} lines={lines} draw={engaged} reduced={reduced} />}

        <div ref={leftColRef} className="relative z-[1] col-span-4" onKeyDown={onLeftKeyDown}>
          {mode === "capabilities"
            ? groupsByMode.capabilities.map((g) => (
                <div key={g.id} className={styles.group}>
                  <h3 id={`${panelId}-g-${g.id}`} className={styles.groupHead}>
                    {g.area && <span aria-hidden="true" className={`${areaTok[g.area]} ${styles.swatch}`} />}
                    {g.label}
                  </h3>
                  <ul aria-labelledby={`${panelId}-g-${g.id}`}>
                    {g.items.map((it) => (
                      <li key={it.key}>
                        <button className={styles.row} {...leftProps(it)}>
                          {it.label}
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              ))
            : (
              <>
                <ToolLegend className="small mb-4 max-w-[40ch] text-ink-2" />
                {groupsByMode.toolkit.map((g) => (
                  <div key={g.id} className={styles.group}>
                    <h3 id={`${panelId}-t-${g.id}`} className={`${styles.groupHead} ${styles.toolHead}`}>
                      {g.label}
                    </h3>
                    <ul aria-labelledby={`${panelId}-t-${g.id}`} className={styles.chipList}>
                      {g.items.map((it) => {
                        const linked = it.links.length > 0;
                        return (
                          <li key={it.key}>
                            <button
                              className={`tok-neutral ${styles.chip}`}
                              data-linked={linked ? "" : undefined}
                              {...leftProps(it)}
                            >
                              {it.label}
                              {linked && (
                                <>
                                  <span aria-hidden="true" className={styles.dot} />
                                  <span className="sr-only">, linked to work</span>
                                </>
                              )}
                            </button>
                          </li>
                        );
                      })}
                    </ul>
                  </div>
                ))}
                <ForeignLanguages className="small mt-6 text-ink-2" />
              </>
            )}
        </div>

        <ul
          ref={workColRef}
          aria-label="Work"
          className="relative z-[1] col-span-5 col-start-8 flex flex-col justify-between gap-2"
          onKeyDown={onWorkKeyDown}
        >
          {work.map((w) => {
            const f: Focus = { side: "R", id: w.id };
            const tint = workTint.get(w.id);
            return (
              <li key={w.id}>
                <button
                  type="button"
                  ref={(el) => {
                    if (el) workEls.current.set(w.id, el);
                    else workEls.current.delete(w.id);
                  }}
                  data-r={w.id}
                  data-lit={tint ? "" : undefined}
                  aria-pressed={pin.work === w.id}
                  aria-controls={panelId}
                  tabIndex={w.id === tabR ? 0 : -1}
                  className={styles.work}
                  style={tint ? ({ "--tint": tint } as CSSProperties) : undefined}
                  onFocus={() => {
                    onRoveR(w.id);
                    onPreview(f);
                  }}
                  onPointerEnter={(e) => {
                    if (e.pointerType === "mouse") onPreview(f);
                  }}
                  onClick={() => onPin(f)}
                >
                  <span className={styles.workTitle}>{w.title}</span>
                  <span className={styles.workMeta}>{w.context}</span>
                  <span className={styles.workKind}>{kindLabel[w.kind]}</span>
                  <span className={styles.workWhen}>{w.when}</span>
                </button>
              </li>
            );
          })}
        </ul>
      </div>

      <EvidencePanel id={panelId} mode={mode} readout={readout} previewing={previewing} />
    </div>
  );
}
