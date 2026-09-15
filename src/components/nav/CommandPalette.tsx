"use client";

import { useRouter, usePathname } from "next/navigation";
import { useEffect, useId, useMemo, useRef, useState } from "react";
import { profile } from "@/content/profile";
import { search, type SearchEntry } from "./searchIndex";
import styles from "./CommandPalette.module.css";

/**
 * Search everything on the site. A native <dialog> gives focus trapping,
 * Esc-to-close and an inert background; the input is an ARIA combobox.
 */
export function CommandPalette({ open, onClose }: { open: boolean; onClose: () => void }) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLUListElement>(null);
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const [status, setStatus] = useState("");
  const router = useRouter();
  const pathname = usePathname();
  const listId = useId();
  const results = useMemo(() => search(query), [query]);

  useEffect(() => {
    const d = dialogRef.current;
    if (!d) return;
    if (open && !d.open) {
      d.showModal();
      setQuery("");
      setActive(0);
      setStatus("");
      requestAnimationFrame(() => inputRef.current?.focus());
    } else if (!open && d.open) {
      d.close();
    }
  }, [open]);

  useEffect(() => setActive(0), [query]);

  useEffect(() => {
    listRef.current?.querySelector(`[data-index="${active}"]`)?.scrollIntoView({ block: "nearest" });
  }, [active]);

  const run = async (e: SearchEntry) => {
    if (e.action === "copy-email") {
      try {
        await navigator.clipboard.writeText(profile.email);
        setStatus("Email copied");
      } catch {
        setStatus(`Couldn't copy. The address is ${profile.email}`);
      }
      return;
    }
    onClose();
    if (e.external && e.href) {
      window.open(e.href, "_blank", "noopener,noreferrer");
      return;
    }
    if (!e.href) return;
    const [path, hash] = e.href.split("#");
    const samePage = (path || "/") === pathname;
    if (samePage && hash) {
      const el = document.getElementById(hash);
      el?.scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
      history.replaceState(null, "", `#${hash}`);
      el?.focus({ preventScroll: true });
    } else {
      router.push(e.href);
    }
    if (e.action && typeof e.action === "object") {
      const detail = e.action.capmap;
      // Let navigation settle, then ask the capability map to select.
      window.setTimeout(() => window.dispatchEvent(new CustomEvent("capmap:select", { detail })), samePage ? 60 : 600);
    }
  };

  const onKeyDown = (ev: React.KeyboardEvent) => {
    if (ev.key === "ArrowDown") {
      ev.preventDefault();
      setActive((a) => Math.min(results.length - 1, a + 1));
    } else if (ev.key === "ArrowUp") {
      ev.preventDefault();
      setActive((a) => Math.max(0, a - 1));
    } else if (ev.key === "Home") {
      setActive(0);
    } else if (ev.key === "End") {
      setActive(results.length - 1);
    } else if (ev.key === "Enter") {
      ev.preventDefault();
      const r = results[active];
      if (r) run(r);
    }
  };

  // Group results while keeping one flat index for keyboard movement.
  let flat = -1;
  const groups = results.reduce<Record<string, { e: SearchEntry; i: number }[]>>((acc, e) => {
    flat++;
    (acc[e.group] ??= []).push({ e, i: flat });
    return acc;
  }, {});

  return (
    <dialog
      ref={dialogRef}
      className={styles.dialog}
      aria-label="Search the site"
      onClose={onClose}
      onClick={(e) => {
        if (e.target === dialogRef.current) onClose();
      }}
    >
      <div className={styles.panel}>
        <div className={styles.inputRow}>
          <svg width="18" height="18" viewBox="0 0 16 16" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.6">
            <circle cx="7" cy="7" r="4.75" />
            <path d="M10.5 10.5L14 14" strokeLinecap="round" />
          </svg>
          <input
            ref={inputRef}
            className={styles.input}
            type="text"
            role="combobox"
            aria-expanded="true"
            aria-controls={listId}
            aria-autocomplete="list"
            aria-activedescendant={results[active] ? `${listId}-${active}` : undefined}
            placeholder="Search projects, skills, papers…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={onKeyDown}
            autoComplete="off"
            spellCheck={false}
          />
          <button type="button" className={`btn btn-quiet ${styles.close}`} onClick={onClose}>
            Close
          </button>
        </div>

        <ul ref={listRef} id={listId} role="listbox" aria-label="Results" className={styles.results}>
          {results.length === 0 && (
            <li role="presentation" className={styles.empty}>
              No matches for “{query}”. Try a skill like QLoRA, or a project like AegisAI.
            </li>
          )}
          {Object.entries(groups).map(([group, items]) => (
            <li key={group} role="presentation">
              <p className={styles.groupLabel} aria-hidden="true">
                {group}
              </p>
              <ul role="group" aria-label={group}>
                {items.map(({ e, i }) => (
                  <li
                    key={e.id}
                    id={`${listId}-${i}`}
                    data-index={i}
                    role="option"
                    aria-selected={i === active}
                    className={styles.option}
                    onMouseMove={() => setActive(i)}
                    onClick={() => run(e)}
                  >
                    <span className={styles.optionTitle}>{e.title}</span>
                    <span className={styles.optionSub}>{e.subtitle}</span>
                  </li>
                ))}
              </ul>
            </li>
          ))}
        </ul>

        <div className={styles.footer}>
          <span aria-live="polite" className={styles.status}>
            {status}
          </span>
          <span className="hidden sm:inline">
            <kbd className="mono">↑</kbd> <kbd className="mono">↓</kbd> to move, <kbd className="mono">Enter</kbd> to open,{" "}
            <kbd className="mono">Esc</kbd> to close
          </span>
        </div>
      </div>
    </dialog>
  );
}
