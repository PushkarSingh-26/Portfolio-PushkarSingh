"use client";

import Image from "next/image";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import tokens from "@/content/generated/tokens.json";
import { portraitPhoto } from "@/content/photos";
import { profile } from "@/content/profile";
import type { Area } from "@/content/types";
import { usePrefersReducedMotion } from "@/lib/hooks";
import styles from "./Hero.module.css";

type Phrase = (typeof tokens.phrases)["name"];

interface MergeStep {
  boundary: number;
  left: string;
  right: string;
  rank: number;
}

/** Replays the recorded merges to know which strings each step joins. */
function mergeSteps(p: Phrase): MergeStep[] {
  const pieces = p.pieces.map((piece, i) => {
    const offset = p.pieces.slice(0, i).join("").length;
    return { offset, parts: [...piece] };
  });
  const byPiece = p.pieces.map((_, i) => p.merges.filter((m) => m.piece === i));
  const order: (typeof p.merges)[number][] = [];
  const longest = Math.max(...byPiece.map((b) => b.length));
  for (let k = 0; k < longest; k++) for (const b of byPiece) if (b[k]) order.push(b[k]);

  return order.map((m) => {
    const piece = pieces[m.piece];
    let pos = piece.offset;
    let idx = 0;
    for (; idx < piece.parts.length; idx++) {
      pos += piece.parts[idx].length;
      if (pos === m.boundary) break;
    }
    const left = piece.parts[idx];
    const right = piece.parts[idx + 1];
    piece.parts.splice(idx, 2, left + right);
    return { boundary: m.boundary, left, right, rank: m.rank };
  });
}

const focus: { key: keyof typeof tokens.phrases; area: Area }[] = [
  { key: "llms", area: "llm" },
  { key: "genai", area: "genai" },
  { key: "ml", area: "ml" },
  { key: "systems", area: "applied" },
];

const show = (s: string) => s.replace(/ /g, " ");

export function Hero() {
  const name = tokens.phrases.name;
  const steps = useMemo(() => mergeSteps(name), [name]);
  const reduced = usePrefersReducedMotion();

  // Token boundaries (char offsets where one final token ends and the next begins).
  const tokenEnds = useMemo(() => {
    const ends = new Set<number>();
    let o = 0;
    for (const t of name.tokens) ends.add((o += t.text.length));
    return ends;
  }, [name]);

  const [playing, setPlaying] = useState(false);
  const [closed, setClosed] = useState<Set<number>>(() => new Set());
  const [flash, setFlash] = useState<number | null>(null);
  const [status, setStatus] = useState<MergeStep | null>(null);
  const [shown, setShown] = useState(99); // how many reveal groups are visible
  const timers = useRef<number[]>([]);

  const clearTimers = () => {
    timers.current.forEach((t) => window.clearTimeout(t));
    timers.current = [];
  };

  const finish = useCallback(() => {
    clearTimers();
    setClosed(new Set(steps.map((s) => s.boundary)));
    setFlash(null);
    setStatus(null);
    setShown(99);
    setPlaying(false);
    document.documentElement.removeAttribute("data-hero");
    try {
      sessionStorage.setItem("hero-played", "1");
    } catch {}
  }, [steps]);

  const play = useCallback(() => {
    clearTimers();
    document.documentElement.dataset.hero = "play";
    setPlaying(true);
    setClosed(new Set());
    setShown(0);
    setStatus(null);
    const at = (ms: number, fn: () => void) => timers.current.push(window.setTimeout(fn, ms));
    const START = 260;
    const STEP = 120;
    steps.forEach((s, i) => {
      at(START + i * STEP, () => {
        setFlash(s.boundary);
        setStatus(s);
        setClosed((c) => new Set(c).add(s.boundary));
      });
    });
    const merged = START + steps.length * STEP + 120;
    at(merged, () => {
      setFlash(null);
      setShown(1); // brackets + IDs
    });
    at(merged + 160, () => setShown(2)); // role
    focus.forEach((_, i) => at(merged + 300 + i * 110, () => setShown(3 + i))); // chips stream
    at(merged + 300 + focus.length * 110 + 80, () => setShown(7)); // statement, actions
    at(merged + 300 + focus.length * 110 + 450, finish);
  }, [steps, finish]);

  useEffect(() => {
    if (document.documentElement.dataset.hero === "play") play();
    return clearTimers;
  }, [play]);

  // Any input skips the intro.
  useEffect(() => {
    if (!playing) return;
    const skip = () => finish();
    const opts = { once: true, passive: true } as const;
    window.addEventListener("keydown", skip, opts);
    window.addEventListener("pointerdown", skip, opts);
    window.addEventListener("wheel", skip, opts);
    window.addEventListener("touchstart", skip, opts);
    return () => {
      window.removeEventListener("keydown", skip);
      window.removeEventListener("pointerdown", skip);
      window.removeEventListener("wheel", skip);
      window.removeEventListener("touchstart", skip);
    };
  }, [playing, finish]);

  // Lines break before tokens that start with a space.
  const lines: { text: string; id: number; start: number }[][] = [];
  let offset = 0;
  for (const t of name.tokens) {
    if (!lines.length || t.text.startsWith(" ")) lines.push([]);
    lines[lines.length - 1].push({ ...t, start: offset });
    offset += t.text.length;
  }

  const selectArea = (area: Area) => {
    document.getElementById("capabilities")?.scrollIntoView({ behavior: reduced ? "auto" : "smooth" });
    window.setTimeout(() => window.dispatchEvent(new CustomEvent("capmap:select", { detail: { area } })), 50);
  };

  const reveal = (n: number) => ({ "data-shown": shown >= n ? "" : undefined });

  return (
    <div className={`wrap ${styles.hero}`} data-playing={playing || undefined}>
        <h1 className={styles.name}>
          <span className="sr-only">{profile.name}</span>
          <span aria-hidden="true" className={styles.lines}>
            {lines.map((line, li) => (
              <span key={li} className={styles.line}>
                {line.map((t) => (
                  <span key={t.start} className={styles.tok}>
                    <span className={styles.chars}>
                      {[...t.text].map((ch, j) => {
                        const b = t.start + j + 1; // boundary after this char
                        const intra = j < t.text.length - 1 && !tokenEnds.has(b);
                        return (
                          <span
                            key={j}
                            className={ch === " " ? `${styles.char} ${styles.space}` : styles.char}
                            data-intra={intra || undefined}
                            data-closed={intra && closed.has(b) ? "" : undefined}
                            data-flash={flash === b || flash === t.start + j ? "" : undefined}
                          >
                            {ch === " " ? " " : ch}
                          </span>
                        );
                      })}
                    </span>
                    <span className={`${styles.bracket} ${styles.reveal}`} {...reveal(1)} />
                    <span className={`mono ${styles.id} ${styles.reveal}`} {...reveal(1)}>
                      {t.id}
                    </span>
                  </span>
                ))}
              </span>
            ))}
          </span>
        </h1>

        {/* The live merge log and the caption share one cell, so swapping them never moves the page. */}
        <div className={styles.captionRow}>
          <p className={`mono ${styles.status}`} aria-hidden="true" data-visible={status ? "" : undefined}>
            {status && (
              <>
                merge “{show(status.left)}” + “{show(status.right)}” → “{show(status.left + status.right)}”
                <span className={styles.rank}>rank {status.rank.toLocaleString("en-US")}</span>
              </>
            )}
          </p>
          <p className={`small text-ink-2 ${styles.caption} ${styles.reveal}`} {...reveal(1)} data-hidden={status ? "" : undefined}>
              My name as the o200k_base tokenizer (used by GPT-4o) splits it: {name.tokens.length} tokens, real IDs.
              {!reduced && (
                <>
                  {" "}
                  <button type="button" className={`link ${styles.replay}`} onClick={play}>
                    Replay the merges
                  </button>
                </>
              )}
          </p>
        </div>

        <div className={styles.identity}>
          <div className={`${styles.byline} ${styles.reveal}`} {...reveal(2)}>
            <Image
              src={portraitPhoto.src}
              alt={portraitPhoto.alt}
              width={144}
              height={144}
              placeholder="blur"
              className={styles.portrait}
            />
            <p className={styles.role}>{profile.role}</p>
          </div>
          <ul className={styles.focus} aria-label="Focus areas">
            {focus.map((f, i) => {
              const phrase = tokens.phrases[f.key];
              const text = phrase.text;
              return (
                <li key={f.key} className={styles.reveal} {...reveal(3 + i)}>
                  <button
                    type="button"
                    className={`tok tok-${f.area} ${styles.chip}`}
                    onClick={() => selectArea(f.area)}
                    aria-label={`${text}: see where this shows up in my work`}
                  >
                    {phrase.tokens.map((t, k) => (
                      <span key={k} className={styles.chipPart}>
                        {t.text.trimStart()}
                      </span>
                    ))}
                  </button>
                </li>
              );
            })}
            <li className={styles.caret} aria-hidden="true" data-on={playing && shown >= 3 && shown < 7 ? "" : undefined} />
          </ul>
        </div>

        <div className={`${styles.statement} ${styles.reveal}`} {...reveal(7)}>
          <p className="lead">{profile.statement}</p>
          <p className="body-2 mt-4">{profile.principle}</p>
          <div className="mt-8 flex flex-wrap gap-3">
            <a href="#capabilities" className="btn btn-primary">
              Explore the work
            </a>
            <a href={profile.resumePdf} className="btn btn-secondary" download>
              Download résumé (PDF)
            </a>
          </div>
        </div>
    </div>
  );
}
