"use client";

import { useCallback, useEffect, useId, useMemo, useRef, useState } from "react";
import { capabilities } from "@/content/capabilities";
import { work } from "@/content/work";
import { useCanHover, useMediaQuery, usePrefersReducedMotion } from "@/lib/hooks";
import { DesktopMap } from "./DesktopMap";
import { MobileMap } from "./MobileMap";
import { ModeSwitch } from "./ModeSwitch";
import {
  CAPMAP_SELECT,
  DEFAULT_LEFT,
  capKey,
  type CapMapSelectDetail,
  focusId,
  parseFocusId,
  readoutFor,
  sameFocus,
  type Focus,
  type Mode,
  type Pin,
} from "./model";
import styles from "./capabilities.module.css";

/**
 * State for the attention map. Desktop and touch layouts both render (CSS picks one),
 * so they share pins: what you chose survives a rotate or a window resize.
 */
export function CapabilityMap() {
  const uid = useId().replace(/[^a-zA-Z0-9_-]/g, "");
  const idBase = `capmap-${uid}`;
  const panelId = `${idBase}-panel`;

  const canHover = useCanHover();
  const wide = useMediaQuery("(min-width: 1024px)", true);
  const isDesktop = canHover && wide;
  const reduced = usePrefersReducedMotion();

  const [mode, setModeState] = useState<Mode>("capabilities");
  const [pins, setPins] = useState<Record<Mode, Pin>>({
    capabilities: { left: DEFAULT_LEFT.capabilities, work: null },
    toolkit: { left: DEFAULT_LEFT.toolkit, work: null },
  });
  const [preview, setPreview] = useState<Focus | null>(null);
  const [rovingL, setRovingL] = useState<Record<Mode, string>>(DEFAULT_LEFT);
  const [rovingR, setRovingR] = useState<string>(work[0]?.id ?? "");
  const [engaged, setEngaged] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  const pin = pins[mode];
  const pinnedFocus: Focus = pin.work ? { side: "R", id: pin.work } : { side: "L", key: pin.left };
  const active = preview ?? pinnedFocus;
  const previewing = preview !== null && !sameFocus(preview, pinnedFocus);
  const activeId = focusId(active);
  const readout = useMemo(() => readoutFor(mode, parseFocusId(activeId)), [mode, activeId]);

  const setMode = useCallback((m: Mode) => {
    setEngaged(true);
    setPreview(null);
    setModeState(m);
  }, []);

  const onPreview = useCallback((f: Focus | null) => {
    if (f) setEngaged(true);
    setPreview((prev) => (prev && f && sameFocus(prev, f) ? prev : f));
  }, []);

  const onPin = useCallback(
    (f: Focus) => {
      setEngaged(true);
      setPins((p) => ({
        ...p,
        [mode]: f.side === "L" ? { left: f.key, work: null } : { left: p[mode].left, work: f.id },
      }));
      setPreview(null);
    },
    [mode],
  );

  const onRoveL = useCallback((key: string) => setRovingL((r) => (r[mode] === key ? r : { ...r, [mode]: key })), [mode]);

  // Mobile: tap = select (always a left item).
  const onSelectMobile = useCallback(
    (key: string) => {
      setEngaged(true);
      setPins((p) => ({ ...p, [mode]: { left: key, work: null } }));
      setRovingL((r) => ({ ...r, [mode]: key }));
    },
    [mode],
  );

  // Esc: drop a preview first (back to the pin). A second Esc, with focus in the map,
  // drops a pinned work item back to the pinned capability.
  const hasPreview = preview !== null;
  const pinWork = pin.work;
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== "Escape") return;
      const map = rootRef.current?.querySelector("[data-capmap-root]");
      const inside = !!map && map.contains(document.activeElement);
      if (previewing) setPreview(null);
      else if (pinWork && inside) {
        setPins((p) => ({ ...p, [mode]: { ...p[mode], work: null } }));
        setPreview(null);
      } else if (hasPreview) setPreview(null);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [previewing, pinWork, hasPreview, mode]);

  // capmap:select from the hero / search palette.
  useEffect(() => {
    const onSelect = (e: Event) => {
      const d = ((e as CustomEvent<CapMapSelectDetail>).detail ?? {}) as CapMapSelectDetail;
      const wanted = d.capability?.toLowerCase();
      const cap =
        (wanted && capabilities.find((c) => c.id.toLowerCase() === wanted || c.label.toLowerCase() === wanted)) ||
        (d.area && capabilities.find((c) => c.area === d.area)) ||
        null;
      setEngaged(true);
      setPreview(null);
      setModeState("capabilities");
      if (cap) {
        const key = capKey(cap.id);
        setPins((p) => ({ ...p, capabilities: { left: key, work: null } }));
        setRovingL((r) => ({ ...r, capabilities: key }));
      }
      // If the section is off screen, bring it in. Harmless if the caller already scrolls here.
      const el = rootRef.current?.closest("section") ?? rootRef.current;
      if (el) {
        const r = el.getBoundingClientRect();
        if (r.top > window.innerHeight * 0.6 || r.bottom < window.innerHeight * 0.2) {
          const smooth = !window.matchMedia("(prefers-reduced-motion: reduce)").matches;
          el.scrollIntoView({ behavior: smooth ? "smooth" : "auto", block: "start" });
        }
      }
    };
    window.addEventListener(CAPMAP_SELECT, onSelect);
    return () => window.removeEventListener(CAPMAP_SELECT, onSelect);
  }, []);

  return (
    <div ref={rootRef} className="mt-10 md:mt-14">
      <div className="mb-5 grid grid-cols-12 items-center gap-x-6">
        <div className="col-span-12 lg:col-span-4">
          <ModeSwitch mode={mode} onChange={setMode} />
        </div>
        <p className={`${styles.desktopOnly} small col-span-5 col-start-8 pl-4 text-ink-2`}>Work</p>
      </div>

      <DesktopMap
        mode={mode}
        pin={pin}
        readout={readout}
        previewing={previewing}
        engaged={engaged}
        reduced={reduced}
        enabled={isDesktop}
        tabL={rovingL[mode]}
        tabR={rovingR}
        panelId={panelId}
        onPreview={onPreview}
        onPin={onPin}
        onRoveL={onRoveL}
        onRoveR={setRovingR}
      />

      <MobileMap
        mode={mode}
        selected={pin.left}
        onSelect={onSelectMobile}
        engaged={engaged}
        reduced={reduced}
        idBase={idBase}
      />
    </div>
  );
}
