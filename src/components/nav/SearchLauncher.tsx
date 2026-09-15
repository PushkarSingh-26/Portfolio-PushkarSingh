"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";

// The palette and its search index load only when first opened.
const CommandPalette = dynamic(() => import("./CommandPalette").then((m) => m.CommandPalette), { ssr: false });

export function SearchLauncher() {
  const [open, setOpen] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [mac, setMac] = useState(false);

  useEffect(() => {
    setMac(/Mac|iPhone|iPad/.test(navigator.platform || navigator.userAgent));
    const onKey = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement | null;
      const typing = target && (target.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(target.tagName));
      if ((e.key === "k" || e.key === "K") && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setLoaded(true);
        setOpen((o) => !o);
      } else if (e.key === "/" && !typing && !e.metaKey && !e.ctrlKey && !e.altKey) {
        e.preventDefault();
        setLoaded(true);
        setOpen(true);
      }
    };
    const onOpen = () => {
      setLoaded(true);
      setOpen(true);
    };
    window.addEventListener("keydown", onKey);
    window.addEventListener("palette:open", onOpen);
    return () => {
      window.removeEventListener("keydown", onKey);
      window.removeEventListener("palette:open", onOpen);
    };
  }, []);

  return (
    <>
      <button
        type="button"
        className="btn btn-quiet"
        aria-haspopup="dialog"
        aria-keyshortcuts={mac ? "Meta+K /" : "Control+K /"}
        onClick={() => {
          setLoaded(true);
          setOpen(true);
        }}
        onPointerEnter={() => setLoaded(true)}
        onFocus={() => setLoaded(true)}
      >
        <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.6">
          <circle cx="7" cy="7" r="4.75" />
          <path d="M10.5 10.5L14 14" strokeLinecap="round" />
        </svg>
        <span>Search</span>
        <kbd className="mono text-ink-2 hidden lg:inline border border-rule rounded px-1.5 py-0.5 text-[11px] leading-none">
          {mac ? "⌘K" : "Ctrl K"}
        </kbd>
      </button>
      {loaded && <CommandPalette open={open} onClose={() => setOpen(false)} />}
    </>
  );
}
