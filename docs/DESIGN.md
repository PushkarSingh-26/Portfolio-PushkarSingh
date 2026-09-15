# Next Token — design system

Portfolio of **Pushkar Singh, AI/ML engineer**. The site is an interactive demonstration:
a visitor watches a language model "read" him, then explores systems that are
**grounded, verifiable, evaluated and human-controlled**.

## Non-negotiables

1. AI/ML is the primary identity. LLMs, generative AI, ML, fine-tuning, RAG and agents lead the visual narrative.
2. Cybersecurity is an *application domain*. Never style anything like a SOC dashboard: no dark consoles, red sirens, shields, locks, glowing nodes, matrix/terminal aesthetics.
3. No generic AI-portfolio aesthetics: no purple gradients, glassmorphism, blobs, particles, glowing cards, skill bars, bento grids, logo walls, fake stats.
4. **Every fact comes from `src/content/*`.** Never invent numbers, results, names, dates, usage or outcomes. New factual sentences must be backed by `ev(source, "verbatim quote", file?)` so `npm run check:content` can verify them. Illustrations and demo data must be labelled as such, visibly, next to the thing.
5. Animation and interaction must mean something. Each motion answers "why does this move?" (hierarchy, relationship, state, progression). Nothing moves on its own except the hero.

## Tokens (Tailwind v4 theme in `src/app/globals.css`)

| Token | Hex | Use |
|---|---|---|
| `paper` | #F3F5F7 | page ground |
| `paper-2` / `paper-3` | #E8ECF1 / #DDE3EA | sunken panels, code blocks, tracks |
| `ink` | #14233A | text, strokes, primary buttons |
| `ink-2` | #4A5668 | secondary text (≥ 6.9:1) |
| `ink-3` | #7A8596 | **non-text only** (dim lines, disabled glyphs) |
| `rule` | #D5DAE1 | hairlines — only where they encode structure |
| `caret` | #2449FF | focus, links, active/current state, progress |
| `tint-ml / tint-llm / tint-genai / tint-applied` | #CFE3FF / #FFE7A3 / #C9EFD9 / #F6D2E0 | **area encoding only**, behind ink text |
| `line-ml / line-llm / line-genai / line-applied` | #2F6FD6 / #A87A00 / #1D8A5C / #B8406A | strokes for the same areas |
| `pass / fail / hold` | #1F7A4D / #B3261E / #8A5A00 | verification states (with icon/text, never color alone) |

Utilities: `bg-paper`, `text-ink-2`, `border-rule`, `bg-tint-llm`, `stroke-[var(--color-line-ml)]`, `font-mono`, etc.
Area → tint mapping lives in `src/components/ui/Token.tsx` (`areaTok`, `areaLine`, `areaTint`).

Areas, always in this order: **LLMs** (pollen) · **Generative AI** (mint) · **Machine learning** (sky) · **Applied AI** (rose).

## Type

- **Mona Sans** (variable `wght` 200–900, `wdth` 75–125 via `font-stretch`). Headings and body.
- **Martian Mono** — *only* for machine text: token IDs, YAML, CLI output, file names, code, HTTP codes. Never for labels or decoration. Class `.mono`.
- Classes: `.display-name` (hero), `.h-section` (section titles, wide + tight), `.h-sub`, `.lead`, `.body-2`, `.small`.
- Sentence case everywhere. **No** all-caps labels, **no** eyebrow labels above headings, **no** `A · B · C` middle-dot strings, **no** `→` appended to links/buttons, **no** single accented word in a headline. Numbered markers only when content is truly a sequence (pipeline stages, steps).
- Body line length ≤ 64ch (`.measure`).

## Shape and surface

- Token spans: radius 4px (`.tok` + area class). Buttons: 6px (`.btn .btn-primary|secondary|quiet`). Panels: 8px max. Small circular markers (dots, pulses) are fine; no other radii.
- No drop shadows except overlays (dialog/popover). No gradients. No blur/glass.
- Diagrams: SVG, 1.5px `ink` strokes, `ink-3` for inactive, area `line-*` colors for active relationships.

## Motion system

Four primitives, each tied to an LLM concept:

| Primitive | Meaning | Implementation |
|---|---|---|
| **Merge** | parts become a whole | gaps close, width axis tightens (hero only) |
| **Stream** | generation | tokens appear one by one behind a caret — short machine text only, never paragraphs |
| **Attend** | relationship | SVG lines draw (`pathLength` 0→1) between related items on hover/focus/select |
| **Flow** | data moving | a small pulse travels along a pipeline edge when a stage becomes active |

- Durations: 120ms press/hover · 220ms open/close · 360–600ms diagram transitions. Easing `cubic-bezier(0.2,0,0,1)` (`--ease-decode`).
- Animate only `transform`, `opacity`, `stroke-dashoffset`/`pathLength`, `clip-path`. No layout thrash.
- **Motion library:** `import { m, AnimatePresence } from "motion/react"` — use `m.div` etc. (LazyMotion strict is set in `MotionProvider`; `motion.div` will throw).
- **Reduced motion:** `usePrefersReducedMotion()` from `src/lib/hooks.ts` → render final states, no streaming, lines appear without drawing. The site must be fully understandable with motion off.
- **Never:** fade-up-on-scroll for text blocks, parallax backgrounds, hover lifts on every block, looping ambient animation, custom cursors.

## Interaction rules

- Desktop: hover/focus = preview, click = pin, Esc = drop the preview and return to the pin. Touch: tap = select.
- Switch desktop/mobile layouts with CSS media queries (render both), not JS — `useCanHover()` is `true` during SSR, so JS switching flashes the wrong layout on phones. Use the hooks only to decide whether to measure/animate.
- Full keyboard parity: every interactive thing reachable by Tab, arrows within composite widgets (roving tabindex), Enter/Space to activate, visible focus (global `:focus-visible` ring).
- Targets ≥ 44px tall on touch. Use real `<button>`/`<a>`. `aria-pressed`, `aria-expanded`, `aria-controls`, `aria-live="polite"` for panels that change with selection.
- Mobile is designed, not shrunk: graphs become progressive lists, pinned diagrams become steppers.

## Layout

- Container: `.wrap` (max 1280px, `--gutter` side padding). Left-aligned. Asymmetric 12-col grids; diagrams may break to full width.
- Sections use `<Section id label pace>` (`src/components/ui/Section.tsx`). Vary pacing; not everything is full-screen.
- Min supported width 360px. Nothing scrolls horizontally except code blocks/tables inside `.scroll-x`.

## Code conventions

- Next.js 16 App Router, React 19, TypeScript strict, Tailwind v4. Server components by default; `"use client"` only for interactive leaves.
- Component-specific CSS goes in a co-located `*.module.css`. Don't edit `globals.css` — report needed tokens instead.
- No new dependencies.
- Evidence UI: `EvidenceQuote` / `Cite` from `src/components/ui/Evidence.tsx`.
