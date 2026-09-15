// Content harness: every ev("source", "quote", "file?") call in src/content must be
// a verbatim quote from the matching source document. Runs before every build.
//
// Comparison ignores whitespace, hyphens/dashes and quote styles, because PDF text
// extraction inserts stray spaces ("th e LSTM") and drops soft hyphens. Words
// themselves must match exactly.
import { readFileSync, readdirSync, statSync, existsSync } from "node:fs";
import { join, dirname, relative } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const src = join(root, "content/sources");

const normalize = (s) =>
  s
    .normalize("NFKC")
    .replace(/[‘’ʼ′]/g, "'")
    .replace(/[“”″]/g, '"')
    .replace(/[\s\-‐‑‒–—−]+/g, "")
    .replace(/\\/g, "");

function readTree(dir) {
  if (!existsSync(dir)) return "";
  let out = "";
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) out += readTree(p);
    else if (/\.(md|txt|py|json|ya?ml|sql)$/i.test(name)) out += "\n" + readFileSync(p, "utf8");
  }
  return out;
}

const sourceText = {
  resume: readFileSync(join(src, "resume.txt"), "utf8"),
  "paper-agents":
    readFileSync(join(src, "papers/ai-agents.txt"), "utf8") +
    "\n" +
    readFileSync(join(src, "papers/figure-transcriptions.txt"), "utf8"),
  "paper-sentiment":
    readFileSync(join(src, "papers/sentiment-lstm.txt"), "utf8") +
    "\n" +
    readFileSync(join(src, "papers/figure-transcriptions.txt"), "utf8"),
  "sigma-demo": readFileSync(join(root, "src/content/generated/sigma-demo.json"), "utf8"),
  stated: readFileSync(join(src, "user-provided.md"), "utf8"),
};
const aegisDir = join(src, "aegisai");
const repoDirs = { aegis: aegisDir, finance: join(src, "finance-pilot"), "sentiment-code": join(src, "sentiment-repo") };
const normalized = Object.fromEntries(Object.entries(sourceText).map(([k, v]) => [k, normalize(v)]));

function sourceFor(source, file) {
  const dir = repoDirs[source];
  if (!dir) return normalized[source];
  if (file) {
    const p = join(dir, file);
    if (!existsSync(p)) return null;
    return normalize(readFileSync(p, "utf8"));
  }
  return normalize(readTree(dir));
}

function walk(dir) {
  const files = [];
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) files.push(...walk(p));
    else if (/\.tsx?$/.test(name)) files.push(p);
  }
  return files;
}

// ev("source", "quote") or ev("source", "quote", "file"), allowing newlines between args.
const EV = /\bev\(\s*"([a-z-]+)"\s*,\s*"((?:[^"\\]|\\.)*)"\s*(?:,\s*"((?:[^"\\]|\\.)*)"\s*)?,?\s*\)/g;

let count = 0;
const failures = [];
for (const file of walk(join(root, "src"))) {
  const text = readFileSync(file, "utf8");
  for (const m of text.matchAll(EV)) {
    count++;
    const [, source, rawQuote, fileArg] = m;
    const quote = JSON.parse(`"${rawQuote}"`);
    const hay = sourceFor(source, fileArg);
    const where = `${relative(root, file)}:${text.slice(0, m.index).split("\n").length}`;
    if (hay == null) failures.push(`${where}  unknown source/file: ${source} ${fileArg ?? ""}`);
    else if (!hay.includes(normalize(quote))) failures.push(`${where}  [${source}${fileArg ? `:${fileArg}` : ""}] "${quote}"`);
  }
}

if (failures.length) {
  console.error(`\nContent check failed: ${failures.length} of ${count} quotes are not in their sources.\n`);
  for (const f of failures) console.error("  ✗ " + f);
  console.error("");
  process.exit(1);
}
console.log(`Content check passed: ${count} quotes verified against source documents.`);
