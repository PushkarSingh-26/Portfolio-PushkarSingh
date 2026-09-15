"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { profile } from "@/content/profile";
import { SearchLauncher } from "./SearchLauncher";
import styles from "./ContextBar.module.css";

interface SectionInfo {
  id: string;
  label: string;
  weight: number;
}

/**
 * The page as a context window: one segment per section, sized by its length.
 * Segments fill as you read; the current one shows its progress in caret blue.
 * Sections are discovered from the DOM (`[data-section]`), so every page works.
 */
export function ContextBar() {
  const pathname = usePathname();
  const [sections, setSections] = useState<SectionInfo[]>([]);
  const [active, setActive] = useState(-1);
  const [progress, setProgress] = useState(0);
  const [pageProgress, setPageProgress] = useState(0);
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const menuButton = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  const discover = useCallback(() => {
    const els = Array.from(document.querySelectorAll<HTMLElement>("main [data-section]"));
    setSections(
      els.map((el) => ({
        id: el.id,
        label: el.getAttribute("aria-label") ?? el.id,
        weight: Math.max(1, el.offsetHeight),
      })),
    );
  }, []);

  useEffect(() => {
    setMenuOpen(false);
    const raf = requestAnimationFrame(discover);
    const ro = new ResizeObserver(() => discover());
    ro.observe(document.body);
    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
    };
  }, [pathname, discover]);

  useEffect(() => {
    let frame = 0;
    const update = () => {
      frame = 0;
      const vh = window.innerHeight;
      const probe = vh * 0.4;
      const doc = document.documentElement;
      setScrolled(window.scrollY > 8);
      const max = doc.scrollHeight - vh;
      setPageProgress(max > 0 ? Math.min(1, Math.max(0, window.scrollY / max)) : 0);
      let idx = -1;
      let p = 0;
      sections.forEach((s, i) => {
        const el = document.getElementById(s.id);
        if (!el) return;
        const r = el.getBoundingClientRect();
        if (r.top <= probe) {
          idx = i;
          p = Math.min(1, Math.max(0, (probe - r.top) / Math.max(1, r.height)));
        }
      });
      // At the very bottom, the last section is complete.
      if (max > 0 && window.scrollY >= max - 2 && sections.length) {
        idx = sections.length - 1;
        p = 1;
      }
      setActive(idx);
      setProgress(p);
    };
    const onScroll = () => {
      if (!frame) frame = requestAnimationFrame(update);
    };
    update();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
      if (frame) cancelAnimationFrame(frame);
    };
  }, [sections]);

  // Mobile menu: Esc closes and returns focus; clicks outside close.
  useEffect(() => {
    if (!menuOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setMenuOpen(false);
        menuButton.current?.focus();
      }
    };
    const onClick = (e: MouseEvent) => {
      if (!menuRef.current?.contains(e.target as Node) && !menuButton.current?.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    };
    document.addEventListener("keydown", onKey);
    document.addEventListener("mousedown", onClick);
    menuRef.current?.querySelector<HTMLElement>("a")?.focus();
    return () => {
      document.removeEventListener("keydown", onKey);
      document.removeEventListener("mousedown", onClick);
    };
  }, [menuOpen]);

  const hrefFor = (id: string) => (pathname === "/" ? `#${id}` : `${pathname}#${id}`);

  return (
    <header className={`${styles.bar} no-print`} data-scrolled={scrolled || undefined}>
      <div className={styles.inner}>
        <Link href="/" className={styles.wordmark} aria-label={`${profile.name}, home`}>
          {profile.name}
        </Link>

        <nav aria-label="Sections on this page" className={styles.segments}>
          {sections.length > 1 && (
            <ol>
              {sections.map((s, i) => {
                const fill = i < active ? 1 : i === active ? progress : 0;
                return (
                  <li key={s.id} style={{ flexGrow: Math.sqrt(s.weight) }}>
                    <a
                      href={hrefFor(s.id)}
                      aria-current={i === active ? "location" : undefined}
                      className={styles.segment}
                    >
                      <span className={styles.label}>{s.label}</span>
                      <span className={styles.track} aria-hidden="true">
                        <span
                          className={styles.fill}
                          data-state={i < active ? "done" : i === active ? "active" : "todo"}
                          style={{ transform: `scaleX(${fill})` }}
                        />
                      </span>
                    </a>
                  </li>
                );
              })}
            </ol>
          )}
        </nav>

        <div className={styles.actions}>
          <SearchLauncher />
          <Link href="/resume" className={`btn btn-quiet ${styles.resume}`}>
            Résumé
          </Link>
          <button
            ref={menuButton}
            type="button"
            className={`btn btn-quiet ${styles.menuButton}`}
            aria-expanded={menuOpen}
            aria-controls="site-menu"
            onClick={() => setMenuOpen((o) => !o)}
          >
            {menuOpen ? "Close" : "Menu"}
          </button>
        </div>
      </div>

      <span className={styles.pageProgress} aria-hidden="true" style={{ transform: `scaleX(${pageProgress})` }} />

      {menuOpen && (
        <div id="site-menu" ref={menuRef} className={styles.menu}>
          <nav aria-label="Site">
            {sections.length > 0 && (
              <ol className={styles.menuList}>
                {sections.map((s, i) => (
                  <li key={s.id}>
                    <a href={hrefFor(s.id)} aria-current={i === active ? "location" : undefined} onClick={() => setMenuOpen(false)}>
                      <span className="mono text-ink-2">{String(i + 1).padStart(2, "0")}</span>
                      {s.label}
                    </a>
                  </li>
                ))}
              </ol>
            )}
            <ul className={styles.menuLinks}>
              {pathname !== "/" && (
                <li>
                  <Link href="/">Overview</Link>
                </li>
              )}
              <li>
                <Link href="/resume">Résumé</Link>
              </li>
              <li>
                <Link href="/#contact">Contact</Link>
              </li>
            </ul>
          </nav>
        </div>
      )}
    </header>
  );
}
