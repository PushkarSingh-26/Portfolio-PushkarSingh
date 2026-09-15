// Build-time tokenizer: replays real o200k_base BPE merges so the hero animation
// shows what the tokenizer actually does. Output is committed as static JSON;
// nothing from the tokenizer ships to the browser.
import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { Tiktoken } from "js-tiktoken/lite";
import o200k from "js-tiktoken/ranks/o200k_base";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const outFile = join(root, "src/content/generated/tokens.json");

// Same parsing js-tiktoken uses: "<prefix> <offset> <b64> <b64> ..."
const ranks = new Map();
for (const line of o200k.bpe_ranks.split("\n")) {
  if (!line) continue;
  const [, offsetStr, ...tokens] = line.split(" ");
  const offset = Number.parseInt(offsetStr, 10);
  tokens.forEach((b64, i) => ranks.set(Buffer.from(b64, "base64").toString("latin1"), offset + i));
}

const enc = new Tiktoken(o200k);
const pattern = new RegExp(o200k.pat_str, "gu");

/** Byte-level BPE with a merge log. Assumes ASCII input (1 char = 1 byte). */
function bpeWithSteps(piece) {
  let parts = [...Buffer.from(piece, "utf8").toString("latin1")];
  const steps = [];
  while (parts.length > 1) {
    let best = -1;
    let bestRank = Infinity;
    for (let i = 0; i < parts.length - 1; i++) {
      const r = ranks.get(parts[i] + parts[i + 1]);
      if (r !== undefined && r < bestRank) {
        bestRank = r;
        best = i;
      }
    }
    if (best === -1) break;
    // Character offset of the boundary that closes (between parts[best] and parts[best+1]).
    const boundary = parts.slice(0, best + 1).join("").length;
    steps.push({ boundary, rank: bestRank });
    parts = [...parts.slice(0, best), parts[best] + parts[best + 1], ...parts.slice(best + 2)];
  }
  return { parts, steps };
}

function tokenize(text) {
  for (const ch of text) {
    if (ch.charCodeAt(0) > 127) throw new Error(`Non-ASCII input not supported: ${text}`);
  }
  const pieces = text.match(pattern) ?? [];
  const tokens = [];
  const merges = [];
  let offset = 0;
  pieces.forEach((piece, pieceIndex) => {
    const { parts, steps } = bpeWithSteps(piece);
    for (const s of steps) merges.push({ piece: pieceIndex, boundary: offset + s.boundary, rank: s.rank });
    for (const p of parts) tokens.push({ text: p, id: ranks.get(p) });
    offset += piece.length;
  });

  // Cross-check against the reference encoder.
  const reference = enc.encode(text);
  const ours = tokens.map((t) => t.id);
  if (JSON.stringify(reference) !== JSON.stringify(ours)) {
    throw new Error(`Mismatch for "${text}": ${ours} vs ${reference}`);
  }
  return { text, pieces, tokens, merges };
}

const phrases = {
  name: "Pushkar Singh",
  llms: "LLMs",
  genai: "Generative AI",
  ml: "Machine learning",
  systems: "Intelligent systems",
};

const out = {
  encoding: "o200k_base",
  generatedWith: "js-tiktoken ranks, merges replayed and cross-checked against js-tiktoken encode()",
  phrases: Object.fromEntries(Object.entries(phrases).map(([k, v]) => [k, tokenize(v)])),
  special: { endoftext: { text: "<|endoftext|>", id: o200k.special_tokens["<|endoftext|>"] } },
};

// Tokenize the example Sigma rule for the streaming display, if the demo data exists.
const sigmaFile = join(root, "src/content/generated/sigma-demo.json");
if (existsSync(sigmaFile)) {
  const demo = JSON.parse(readFileSync(sigmaFile, "utf8"));
  out.sigmaRuleTokens = Object.fromEntries(
    demo.variants.map((v) => [v.id, enc.encode(v.yaml).map((id) => enc.decode([id]))]),
  );
}

mkdirSync(dirname(outFile), { recursive: true });
writeFileSync(outFile, JSON.stringify(out, null, 2) + "\n");
console.log(`Wrote ${outFile}`);
for (const [k, v] of Object.entries(out.phrases)) {
  console.log(k.padEnd(8), v.tokens.map((t) => `[${t.text}|${t.id}]`).join(" "), `merges=${v.merges.length}`);
}
