import { capabilities, areas } from "@/content/capabilities";
import { toolGroups } from "@/content/tools";
import { work, workById } from "@/content/work";
import { papers } from "@/content/research";
import { profile } from "@/content/profile";

export type ResultGroup = "Sections" | "Work" | "Capabilities" | "Toolkit" | "Actions";

export interface SearchEntry {
  id: string;
  group: ResultGroup;
  title: string;
  subtitle: string;
  keywords: string;
  href?: string;
  external?: boolean;
  action?: "copy-email" | { capmap: { capability?: string; area?: string } };
}

const sections: SearchEntry[] = [
  { id: "s-capabilities", group: "Sections", title: "Capabilities", subtitle: "What I work on, and where", keywords: "skills map attention", href: "/#capabilities" },
  { id: "s-sigma", group: "Sections", title: "Sigma rule LLM", subtitle: "QLoRA fine-tuning and a compiler-based eval harness", keywords: "llm fine-tuning evaluation", href: "/#sigma-llm" },
  { id: "s-aegis", group: "Sections", title: "AegisAI", subtitle: "Follow an alert through a grounded investigation", keywords: "soc threat intelligence approval", href: "/#aegisai" },
  { id: "s-experience", group: "Sections", title: "Experience", subtitle: "Closer to the model", keywords: "work roles timeline internship", href: "/#experience" },
  { id: "s-research", group: "Sections", title: "Research", subtitle: "Two papers", keywords: "papers publications", href: "/#research" },
  { id: "s-projects", group: "Sections", title: "More projects", subtitle: "Finance Pilot and Kisan Diary", keywords: "finance stocks rag chatbot gemini opensearch agriculture erp", href: "/#projects" },
  { id: "s-recognition", group: "Sections", title: "Recognition", subtitle: "Awards and leadership", keywords: "achievements awards datathon", href: "/#recognition" },
  { id: "s-contact", group: "Sections", title: "Contact", subtitle: profile.email, keywords: "email hire reach", href: "/#contact" },
  { id: "s-resume", group: "Sections", title: "Résumé", subtitle: "Readable version with a PDF download", keywords: "cv resume pdf", href: "/resume" },
];

const actions: SearchEntry[] = [
  { id: "a-pdf", group: "Actions", title: "Download résumé (PDF)", subtitle: "pushkar-singh-resume.pdf", keywords: "cv resume download", href: profile.resumePdf, external: true },
  { id: "a-copy", group: "Actions", title: "Copy email address", subtitle: profile.email, keywords: "email contact mail", action: "copy-email" },
  { id: "a-github", group: "Actions", title: "Open GitHub", subtitle: "github.com/PushkarSingh-26", keywords: "code repositories", href: profile.links.github, external: true },
  { id: "a-linkedin", group: "Actions", title: "Open LinkedIn", subtitle: "linkedin.com/in/pushkar-singh-b34b9b341", keywords: "profile", href: profile.links.linkedin, external: true },
  { id: "a-leetcode", group: "Actions", title: "Open LeetCode", subtitle: "leetcode.com/u/Pushkar-26", keywords: "problems", href: profile.links.leetcode, external: true },
  { id: "a-tensortonic", group: "Actions", title: "Open Tensortonic", subtitle: "tensortonic.com/profile/pushkarml", keywords: "ml practice", href: profile.links.tensortonic, external: true },
];

const workEntries: SearchEntry[] = work.map((w) => ({
  id: `w-${w.id}`,
  group: "Work",
  title: w.title,
  subtitle: `${w.context}, ${w.when}`,
  keywords: `${w.kind} ${w.context}`,
  href: w.href,
}));

const paperEntries: SearchEntry[] = papers.map((p) => ({
  id: `p-${p.slug}`,
  group: "Work",
  title: p.title,
  subtitle: `${p.label} with ${p.authors.slice(1).join(", ")}`,
  keywords: `paper research ${p.keywords.join(" ")}`,
  href: `/research/${p.slug}`,
}));

const usedIn = (links: { work: string }[]) =>
  links.length ? `Used in ${[...new Set(links.map((l) => workById[l.work]?.title))].join(", ")}` : "Listed in my résumé skills";

const capabilityEntries: SearchEntry[] = capabilities.map((c) => ({
  id: `c-${c.id}`,
  group: "Capabilities",
  title: c.label,
  subtitle: usedIn(c.links),
  keywords: `${areas.find((a) => a.id === c.area)?.label ?? ""}`,
  href: "/#capabilities",
  action: { capmap: { capability: c.id } },
}));

const toolEntries: SearchEntry[] = toolGroups.flatMap((g) =>
  g.tools.map((t) => ({
    id: `t-${g.id}-${t.label}`,
    group: "Toolkit" as const,
    title: t.label,
    subtitle: usedIn(t.links),
    keywords: g.label,
    href: t.links[0] ? workById[t.links[0].work]?.href : "/#capabilities",
  })),
);

export const searchIndex: SearchEntry[] = [
  ...sections,
  ...workEntries,
  ...paperEntries,
  ...capabilityEntries,
  ...toolEntries,
  ...actions,
];

export const defaultResults = [...sections, ...actions];

const fold = (s: string) => s.toLowerCase().normalize("NFKD").replace(/[̀-ͯ]/g, "");

/** Every query word must match somewhere; title matches and prefixes rank higher. */
export function search(query: string, limit = 12): SearchEntry[] {
  const words = fold(query).split(/\s+/).filter(Boolean);
  if (!words.length) return defaultResults;
  const scored: { e: SearchEntry; score: number }[] = [];
  for (const e of searchIndex) {
    const title = fold(e.title);
    const rest = fold(`${e.subtitle} ${e.keywords} ${e.group}`);
    let score = 0;
    let ok = true;
    for (const w of words) {
      if (title.startsWith(w)) score += 6;
      else if (new RegExp(`\\b${w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}`).test(title)) score += 4;
      else if (title.includes(w)) score += 3;
      else if (rest.includes(w)) score += 1;
      else {
        ok = false;
        break;
      }
    }
    if (ok) scored.push({ e, score });
  }
  return scored.sort((a, b) => b.score - a.score).slice(0, limit).map((s) => s.e);
}
