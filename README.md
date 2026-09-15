# Pushkar Singh — portfolio

An interactive portfolio for an AI/ML engineer, built around one idea: show how a
language model reads, then show systems that are **grounded, verifiable, evaluated
and human-controlled**. Design notes live in [`docs/DESIGN.md`](docs/DESIGN.md).

## Run it

```bash
npm install
npm run dev          # http://localhost:3200 — live reload while editing
npm run build        # runs the content check first, then builds
npm start            # http://localhost:3200 — the production build
```

Both commands use port 3200, so run one at a time: stop one with Ctrl+C before
starting the other. After `npm run build`, restart `npm start` — a running
server keeps serving the build it started with.

Requires Node 20+.

## How the content stays honest

Every factual sentence on the site is a verbatim quote from a source document,
wrapped in `ev(source, "quote", file?)` inside `src/content/`. Before every build,
`scripts/check-content.mjs` confirms each quote exists in its source and fails the
build if any doesn't.

| Source id | File(s) |
|---|---|
| `resume` | `content/sources/resume.txt` (text of the résumé PDF, phone number removed) |
| `paper-agents` | `content/sources/papers/ai-agents.txt` + figure transcriptions |
| `paper-sentiment` | `content/sources/papers/sentiment-lstm.txt` + figure transcriptions |
| `aegis` | raw files from the AegisAI repository in `content/sources/aegisai/` (see `VERIFIED_FACTS.md` there) |
| `sigma-demo` | `src/content/generated/sigma-demo.json` |

Comparison ignores whitespace, hyphens and quote styles (PDF extraction adds stray
spaces); the words must match exactly.

### Generated data

- `src/content/generated/tokens.json` — real `o200k_base` tokens, IDs and the BPE merge
  order for the hero. Regenerate with `npm run tokenize` (uses `js-tiktoken`, dev-only;
  the output is cross-checked against the reference encoder).
- `src/content/generated/sigma-demo.json` — real `sigma-cli` output for the hand-written
  example rule and its three broken variants. Produced by running sigma-cli 3.1.0 with
  pySigma 1.5.0 and the Splunk backend 2.1.0; the rule files are in
  `src/content/generated/sigma-rules/`.

## Updating content

1. Update the source (e.g. replace `content/sources/resume.txt` with the new résumé text).
2. Edit the matching file in `src/content/` using `ev()` for anything factual.
3. `npm run check:content` — fix anything it flags.
4. Replace `public/pushkar-singh-resume.pdf` if the PDF changed.

## Deploy (Vercel)

Import the repository in Vercel; the defaults work (framework: Next.js, build:
`npm run build`). Optionally set `NEXT_PUBLIC_SITE_URL` to the production URL so
social cards use absolute links; otherwise Vercel's production URL is used.

## Stack

Next.js 16 (App Router, static pages), React 19, TypeScript, Tailwind CSS 4,
Motion (LazyMotion, `m.*` components). Fonts: Mona Sans and Martian Mono via
`next/font`. No 3D, canvas or animation libraries beyond Motion.
