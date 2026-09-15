import { ev, type Evidence } from "./types";

/*
  AegisAI — every fact on the AegisAI section and case study lives here.
  Quotes are verbatim from the repository snapshot in content/sources/aegisai/
  (see VERIFIED_FACTS.md) or the résumé, and are checked by scripts/check-content.mjs.
  Keep ev() arguments as plain double-quoted literals.
*/

export const AEGIS_REPO = "https://github.com/PushkarSingh-26/cyber-threat-intelligence-platform";

/* ------------------------------------------------------------------ */
/* Identity                                                            */
/* ------------------------------------------------------------------ */

export const aegisIntro = {
  title: "AegisAI",
  /** One line for the home section. Backed by `descriptionEvidence`. */
  description:
    "A threat-intelligence platform with ML risk scoring, graph investigation and an AI analyst, where findings carry their evidence and response actions run only after a person approves them.",
  descriptionEvidence: [
    ev("resume", "AegisAI – Intelligent SOC & Threat Intelligence Platform"),
    ev("resume", "Implemented ML risk scoring, graph-based threat analysis, predictive intelligence, AI-driven investigations"),
    ev("aegis", "Nothing executes automatically: attempting to execute an unapproved recommendation returns HTTP 409.", "README.md"),
  ],
  /** The repo never uses the name AegisAI; say so once. */
  repoName: "The repository calls it the Cyber Threat Intelligence Platform.",
  repoNameEvidence: ev("aegis", "# Cyber Threat Intelligence Platform", "README.md"),
  purpose: ev("aegis", "A platform for collecting, enriching, analyzing, and serving cyber threat intelligence.", "README.md"),
};

export const aegisFacts = {
  built: { value: "June – Aug 2026", evidence: ev("resume", "June - Aug 2026") },
  status: {
    value: "“Phase 19 — human-in-the-loop response (approval-gated)”",
    evidence: ev("aegis", "Current status: Phase 19 — human-in-the-loop response (approval-gated).", "README.md"),
  },
  runs: {
    value: "Locally: databases in Docker Compose, API under uvicorn",
    evidence: [
      ev("aegis", "Docker Desktop with Docker Compose v2+", "README.md"),
      ev("aegis", "Neo4j runs as a Docker service", "README.md"),
    ],
  },
};

/** The five principles, and the device in the journey that carries each one. */
export const aegisPrinciples: { id: string; text: string; device: string; evidence: Evidence }[] = [
  {
    id: "preserved",
    text: "Every finding keeps the evidence behind it.",
    device: "evidence ledger",
    evidence: ev("aegis", "Every enrichment stores the evidence and a human-readable rationale.", "docs/wazuh_soc_architecture.md"),
  },
  {
    id: "no-llm",
    text: "The pipeline works without an LLM.",
    device: "LLM switch",
    evidence: ev("aegis", "Deterministic by default; no external LLM required (optional narration only).", "docs/agentic_soc.md"),
  },
  {
    id: "fenced",
    text: "The agent stays inside existing evidence and approved tools.",
    device: "tool fence",
    evidence: ev("aegis", "The agent acts only through a 12-tool read-only registry over existing services;", "README.md"),
  },
  {
    id: "decide",
    text: "Recommendations never run themselves; a person decides.",
    device: "approval gate",
    evidence: ev("aegis", "No action ever runs automatically.", "docs/response_approval.md"),
  },
  {
    id: "audit",
    text: "Every state change is written to an audit log.",
    device: "audit trail",
    evidence: ev("aegis", "every transition appends to response_audit (event, actor, timestamp, detail)", "docs/response_approval.md"),
  },
];

/* ------------------------------------------------------------------ */
/* Evidence ledger — numbered in this order, grouped by stage           */
/* ------------------------------------------------------------------ */

export type StageId =
  | "alert"
  | "evidence"
  | "correlation"
  | "risk"
  | "investigation"
  | "analyst"
  | "recommendation"
  | "approval"
  | "response";

export interface LedgerEntry {
  id: string;
  stage: StageId;
  /** Short entry text. `mono` when it is machine text (a field, a value, a formula). */
  label: string;
  mono?: boolean;
  evidence: Evidence;
}

const FIXTURE = "collectors/fixtures/sample_wazuh.json";

export const ledger: LedgerEntry[] = [
  // Alert — fields from the repository's test fixture
  { id: "level", stage: "alert", label: "rule.level: 12", mono: true, evidence: ev("aegis", "\"level\": 12", "collectors/fixtures/sample_wazuh.json") },
  {
    id: "description",
    stage: "alert",
    label: "Possible SQL injection against public-facing web application",
    evidence: ev("aegis", "\"description\": \"Possible SQL injection against public-facing web application\"", "collectors/fixtures/sample_wazuh.json"),
  },
  { id: "mitre", stage: "alert", label: "rule.mitre.id: [\"T1190\"]", mono: true, evidence: ev("aegis", "\"mitre\": {\"id\": [\"T1190\"]}", "collectors/fixtures/sample_wazuh.json") },
  { id: "agent", stage: "alert", label: "agent: 001 web-server-01", mono: true, evidence: ev("aegis", "\"agent\": {\"id\": \"001\", \"name\": \"web-server-01\"}", "collectors/fixtures/sample_wazuh.json") },
  { id: "location", stage: "alert", label: "location: /var/log/nginx/access.log", mono: true, evidence: ev("aegis", "\"location\": \"/var/log/nginx/access.log\"", "collectors/fixtures/sample_wazuh.json") },

  // Evidence
  { id: "raw", stage: "evidence", label: "raw_event: the alert's _source, kept as JSON", evidence: ev("aegis", "\"raw_event\": src,", "collectors/wazuh.py") },
  { id: "enrichment", stage: "evidence", label: "wazuh_alert_enrichment: one row per alert", evidence: ev("aegis", "wazuh_alert_enrichment row (one per alert, explainable evidence stored)", "docs/wazuh_soc_architecture.md") },
  { id: "src-attack", stage: "evidence", label: "Collected from MITRE ATT&CK (STIX bundle)", evidence: ev("aegis", "Download the official Enterprise ATT&CK STIX bundle", "README.md") },
  { id: "src-nvd", stage: "evidence", label: "Collected from NVD (CVE records)", evidence: ev("aegis", "Download CVE records from the NVD 2.0 API", "README.md") },
  { id: "src-epss", stage: "evidence", label: "Collected from FIRST EPSS", evidence: ev("aegis", "FIRST EPSS scores", "README.md") },
  { id: "src-kev", stage: "evidence", label: "Collected from the CISA KEV catalog", evidence: ev("aegis", "CISA KEV catalog", "README.md") },
  { id: "src-misp", stage: "evidence", label: "Collected from MISP (events, IOCs, actors)", evidence: ev("aegis", "Ingest MISP events, IOCs, and galaxy entities (actors/malware/campaigns)", "README.md") },

  // Correlation
  { id: "rule", stage: "correlation", label: "T1190 rule: Initial Access, weight 0.7", evidence: ev("aegis", "\"T1190\", \"Initial Access\", 0.7,", "backend/app/correlation/rules.py") },
  { id: "phrases", stage: "correlation", label: "Matched phrases stored verbatim as evidence", evidence: ev("aegis", "The matched phrases are stored verbatim as the evidence for the link", "backend/app/correlation/engine.py") },
  { id: "method", stage: "correlation", label: "METHOD = \"rule-based-keyword-v1\"", mono: true, evidence: ev("aegis", "METHOD = \"rule-based-keyword-v1\"", "backend/app/correlation/engine.py") },

  // Risk
  { id: "soc-weights", stage: "risk", label: "Alert SOC priority: six weighted signals", evidence: ev("aegis", "base = 100 * ( 0.25 * wazuh_severity     (rule_level / 15)", "docs/wazuh_soc_architecture.md") },
  { id: "cve-weights", stage: "risk", label: "CVE priority v2: five weighted signals", evidence: ev("aegis", "base   = 100 * ( 0.20*cvss + 0.15*correlation + 0.15*ml + 0.30*epss + 0.20*attack )", "backend/app/prioritization/engine.py") },
  { id: "kev", stage: "risk", label: "KEV override: min(100, max(base, 75) + 15)", mono: true, evidence: ev("aegis", "final = min(100, max(base,75)+15)", "docs/wazuh_soc_architecture.md") },
  { id: "weak-label", stage: "risk", label: "ML risk: trained on a heuristic weak-supervision label", evidence: ev("aegis", "Heuristic weak-supervision target in [0, 100].", "ml/feature_engineering.py") },

  // Investigation
  { id: "path", stage: "investigation", label: "Path: alert, technique, CVE, actor, malware or campaign", evidence: ev("aegis", "Investigation workflows (alert → technique → CVE → actor → malware/campaign", "README.md") },
  { id: "blast", stage: "investigation", label: "Blast radius: depth ≤ 4, undirected", evidence: ev("aegis", "bounded Neo4j traversal, depth ≤4, undirected", "docs/agentic_soc.md") },
  { id: "gds", stage: "investigation", label: "GDS: degree, PageRank, betweenness, Louvain, WCC, similarity", evidence: ev("aegis", "GDS: degree/pagerank/betweenness/louvain/wcc/similarity", "README.md") },

  // AI analyst
  { id: "provider", stage: "analyst", label: "AI_PROVIDER=none by default", mono: true, evidence: ev("aegis", "AI_PROVIDER=none", ".env.example") },
  { id: "tools", stage: "analyst", label: "12 tools, all read-only", evidence: ev("aegis", "Tools implemented (12, all read-only over existing services)", "docs/agentic_soc.md") },
  { id: "plan", stage: "analyst", label: "Alert plan: 8 fixed tool steps", evidence: ev("aegis", "\"wazuh_alert_retrieval\", {\"alert_id\": aid}, \"Retrieve the raw Wazuh alert and its enrichment\"", "backend/app/agents/planner.py") },
  { id: "cypher", stage: "analyst", label: "The LLM never writes or executes Cypher", evidence: ev("aegis", "The LLM never writes or executes Cypher.", "docs/ai_analyst.md") },

  // Recommendation
  { id: "rec-rule", stage: "recommendation", label: "Techniques found: “Validate / tune detections”", evidence: ev("aegis", "recs.append({\"action\": \"Validate / tune detections\",", "backend/app/agents/report_generator.py") },
  { id: "rec-type", stage: "recommendation", label: "“detection” maps to tune_detection", evidence: ev("aegis", "return \"tune_detection\"", "backend/app/response_engine.py") },

  // Human approval
  { id: "states", stage: "approval", label: "pending → approved | rejected; approved → executed; executed → verified | failed", mono: true, evidence: ev("aegis", "# pending -> approved | rejected ; approved -> executed ; executed -> verified | failed", "backend/app/models/response.py") },
  { id: "gate", stage: "approval", label: "Executing an unapproved recommendation returns 409", evidence: ev("aegis", "The approval gate is enforced in", "docs/response_approval.md") },

  // Response
  { id: "mock", stage: "response", label: "ShuffleProvider, mock by default", evidence: ev("aegis", "Mock by default so nothing external is required for dev/tests.", "docs/response_approval.md") },
  { id: "verify", stage: "response", label: "Verify: the provider accepted the action", evidence: ev("aegis", "Verify that the executed action was accepted by the SOAR provider.", "backend/app/response_engine.py") },
  { id: "audit", stage: "response", label: "Every transition appends to response_audit", evidence: ev("aegis", "every transition appends to response_audit (event, actor, timestamp, detail)", "docs/response_approval.md") },
];

/** 1-based ledger number for an entry id. */
export const ledgerNo: Record<string, number> = Object.fromEntries(ledger.map((e, i) => [e.id, i + 1]));

/* ------------------------------------------------------------------ */
/* Stages                                                               */
/* ------------------------------------------------------------------ */

export interface AegisStage {
  id: StageId;
  name: string;
  /** Panel heading. */
  title: string;
  /** Two or three short sentences. Backticks mark machine text. */
  body: string;
  quotes: Evidence[];
  /** One-line summary once the stage is collapsed in the case file. */
  summary: string;
  summaryRefs: string[];
  /** Pipeline overview (case study). */
  oneLine: string;
  component: string;
  overviewEvidence: Evidence;
}

export const stages: AegisStage[] = [
  {
    id: "alert",
    name: "Alert",
    title: "An alert in Wazuh's indexer format, kept as it arrived",
    body: "The platform pulls alerts from the Wazuh indexer and keeps each one with its raw event. This one is from the repository's test fixture: a level 12 SQL-injection alert on a web server, tagged ATT&CK `T1190`. Its Wazuh severity stays as it is.",
    quotes: [
      ev("aegis", "Production path pulls agents from the Wazuh Manager API (JWT auth) and alerts from the Wazuh Indexer (OpenSearch).", "collectors/wazuh.py"),
      ev("aegis", "Wazuh's native severity is never modified", "docs/wazuh_soc_architecture.md"),
    ],
    summary: "alert-0001 on web-server-01, level 12, T1190",
    summaryRefs: ["level", "mitre", "agent"],
    oneLine: "Alerts are pulled from the Wazuh indexer and stored with their raw event.",
    component: "collectors/wazuh.py",
    overviewEvidence: ev("aegis", "Pull agents (Manager API) and alerts (OpenSearch indexer), then enrich + score:", "README.md"),
  },
  {
    id: "evidence",
    name: "Evidence",
    title: "Evidence is added beside the alert, not over it",
    body: "The raw event is saved as JSON. Enrichment goes into a separate record that keeps the evidence behind each link and a plain-English rationale. It draws on sources the platform collects from: MITRE ATT&CK, NVD, FIRST EPSS, CISA KEV and MISP.",
    quotes: [
      ev("aegis", "Every enrichment stores the evidence and a human-readable rationale.", "docs/wazuh_soc_architecture.md"),
      ev("aegis", "All correlation/EPSS/KEV/actor links reuse the existing CTI tables — no data is re-derived.", "docs/wazuh_soc_architecture.md"),
    ],
    summary: "raw event kept; enrichment stored in its own record",
    summaryRefs: ["raw", "enrichment"],
    oneLine: "Each alert gets a separate enrichment record that stores its evidence.",
    component: "wazuh_enrichment/engine.py",
    overviewEvidence: ev("aegis", "Every enrichment stores the evidence and a human-readable rationale.", "docs/wazuh_soc_architecture.md"),
  },
  {
    id: "correlation",
    name: "Correlation",
    title: "Techniques meet CVEs through phrases you can read",
    body: "The alert's technique, `T1190`, is the join key. A versioned rule base links techniques to CVEs when a CVE description contains a known exploitation phrase, and saves the matched phrases as the link's evidence. When several rules hit one technique, their weights combine by noisy-OR.",
    quotes: [
      ev("aegis", "the matched phrases are stored as evidence so every link is explainable.", "README.md"),
      ev("aegis", "No LLMs or paid services are involved;", "README.md"),
    ],
    summary: "T1190 rule, weight 0.7; matched phrases kept as evidence",
    summaryRefs: ["rule", "phrases"],
    oneLine: "Rules link ATT&CK techniques to CVEs and keep the matched phrases.",
    component: "correlation/rules.py",
    overviewEvidence: ev("aegis", "A versioned rule base (`backend/app/correlation/rules.py`) maps high-signal exploitation phrases", "README.md"),
  },
  {
    id: "risk",
    name: "Risk",
    title: "Priority is a formula you can inspect",
    body: "The alert gets its own SOC priority from 0 to 100, separate from its Wazuh level; CVEs get a different blend in which EPSS weighs most. A CISA KEV listing overrides both. The ML risk score inside them learns a heuristic label, so its strong test metrics show it learned that label, not that it predicts exploitation.",
    quotes: [
      ev("aegis", "Because the label is a function of the same features, held-out regression metrics are high by construction", "README.md"),
      ev("aegis", "Treat the score as a transparent prioritization aid, not a validated probability.", "README.md"),
    ],
    summary: "two priority formulas; no score computed for the sample",
    summaryRefs: ["soc-weights", "cve-weights", "kev"],
    oneLine: "Two priority engines and an ML risk score rank what matters first.",
    component: "prioritization/engine.py",
    overviewEvidence: ev("aegis", "Each score stores its per-signal point breakdown and a plain-English explanation", "README.md"),
  },
  {
    id: "investigation",
    name: "Investigation",
    title: "The graph is walked, within bounds",
    body: "Neo4j holds a projection of PostgreSQL, which stays the system of record. From the alert, the investigation follows typed relationships to the technique, correlated CVEs, attributed actors, and their malware and campaigns. Blast radius walks the same graph, never more than four hops out.",
    quotes: [
      ev("aegis", "PostgreSQL stays the system of record and the graph is rebuildable at any time.", "README.md"),
      ev("aegis", "bounded Neo4j traversal, depth ≤4, undirected", "docs/agentic_soc.md"),
    ],
    summary: "alert → technique → CVE → actor, depth ≤ 4",
    summaryRefs: ["path", "blast"],
    oneLine: "A Neo4j projection is walked outward from the alert, within bounds.",
    component: "backend/app/graph",
    overviewEvidence: ev("aegis", "Each workflow is one API call returning a visualization-ready subgraph", "docs/graph_schema.md"),
  },
  {
    id: "analyst",
    name: "AI analyst",
    title: "An agent inside a fence, an LLM behind a switch",
    body: "For an alert, the planner lays out eight fixed steps, and each step calls one of twelve read-only tools; anything else is refused. The agent's report is built deterministically from those steps. The separate AI analyst answers from the same platform data: with `AI_PROVIDER=none`, the default, it returns an evidence-only answer; switch a provider on and a model narrates that evidence.",
    quotes: [
      ev("aegis", "The LLM never writes or executes Cypher.", "docs/ai_analyst.md"),
      ev("aegis", "with no LLM configured it returns deterministic, evidence-only answers", "docs/ai_analyst.md"),
    ],
    summary: "8 fenced tool steps",
    summaryRefs: ["tools", "plan"],
    oneLine: "A planner runs fenced read-only tools; a separate analyst can have an LLM narrate.",
    component: "backend/app/agents",
    overviewEvidence: ev("aegis", "Run an autonomous investigation that plans, gathers evidence via vetted tools,", "README.md"),
  },
  {
    id: "recommendation",
    name: "Recommendation",
    title: "A recommendation, with its citation attached",
    body: "Fixed rules turn the evidence into recommendations: patch if KEV, prioritize if EPSS is high, escalate if CRITICAL or HIGH, hunt actor TTPs, tune detections, investigate related alerts. Each names the tool whose evidence triggered it. Here the alert's technique triggers “Validate / tune detections”; the others need evidence the fixture doesn't hold.",
    quotes: [
      ev("aegis", "every tool call is logged and every recommendation cites its evidence.", "README.md"),
      ev("aegis", "No hallucinated remediation.", "docs/agentic_soc.md"),
    ],
    summary: "tune_detection, citing alert_investigation",
    summaryRefs: ["rec-rule", "rec-type"],
    oneLine: "Rules turn evidence into recommendations that cite their source tool.",
    component: "agents/report_generator.py",
    overviewEvidence: ev("aegis", "Every recommendation references supporting evidence", "backend/app/agents/report_generator.py"),
  },
  {
    id: "approval",
    name: "Human approval",
    title: "Nothing runs until a person says so",
    body: "Every recommendation starts pending, and only an approved one can execute. Press Execute now and the API refuses with a 409. Then approve or reject it yourself; the diagram follows the state machine in the code.",
    quotes: [
      ev("aegis", "Nothing executes automatically: attempting to execute an unapproved recommendation returns HTTP 409.", "README.md"),
      ev("aegis", "No action ever runs automatically.", "docs/response_approval.md"),
    ],
    summary: "status",
    summaryRefs: ["states", "gate"],
    oneLine: "An analyst approves or rejects. Nothing executes before that.",
    component: "response_engine.py",
    overviewEvidence: ev("aegis", "execution requires a prior recorded approval;", "docs/response_approval.md"),
  },
  {
    id: "response",
    name: "Response",
    title: "Handed to the SOAR provider, then checked",
    body: "An approved action goes out through the ShuffleProvider, which defaults to a credential-free mock; that's what runs here. Verify checks the provider's reply: it confirms the provider accepted the action, not that anything changed on a host. Each transition is written to `response_audit`.",
    quotes: [
      ev("aegis", "execution goes through the existing ShuffleProvider; Mock by default so nothing external is required for dev/tests.", "docs/response_approval.md"),
      ev("aegis", "Verify that the executed action was accepted by the SOAR provider.", "backend/app/response_engine.py"),
    ],
    summary: "status",
    summaryRefs: ["mock", "verify"],
    oneLine: "Approved actions go to the SOAR provider; verify checks it accepted.",
    component: "ticketing/providers.py",
    overviewEvidence: ev("aegis", "Approved actions execute through the existing `ShuffleProvider` (mock by default);", "README.md"),
  },
];

export const stageIndex: Record<StageId, number> = Object.fromEntries(stages.map((s, i) => [s.id, i])) as Record<StageId, number>;

/* ------------------------------------------------------------------ */
/* Stage 1 — the sample alert                                           */
/* ------------------------------------------------------------------ */

export const sampleAlert = {
  label: "Sample alert from the repository's test fixture — not production data.",
  file: FIXTURE,
  record: ev(
    "aegis",
    "{\"_id\": \"alert-0001\", \"_source\": {\"@timestamp\": \"2026-06-16T08:25:11\", \"agent\": {\"id\": \"001\", \"name\": \"web-server-01\"}, \"rule\": {\"id\": \"100210\", \"level\": 12, \"description\": \"Possible SQL injection against public-facing web application\", \"mitre\": {\"id\": [\"T1190\"]}}, \"decoder\": {\"name\": \"web-accesslog\"}, \"location\": \"/var/log/nginx/access.log\"}}",
    "collectors/fixtures/sample_wazuh.json",
  ),
  /** Fixture field, its value, and the `wazuh_alerts` column the parser writes it to. */
  fields: [
    { key: "_id", value: "alert-0001", column: "wazuh_alert_id" },
    { key: "@timestamp", value: "2026-06-16T08:25:11", column: "timestamp" },
    { key: "agent.id", value: "001", column: "agent_id", ref: "agent" },
    { key: "rule.id", value: "100210", column: "rule_id" },
    { key: "rule.level", value: "12", column: "rule_level", ref: "level" },
    { key: "rule.description", value: "Possible SQL injection against public-facing web application", column: "description", ref: "description" },
    { key: "rule.mitre.id", value: "[\"T1190\"]", column: "mitre_techniques", ref: "mitre" },
    { key: "decoder.name", value: "web-accesslog", column: "decoder" },
    { key: "location", value: "/var/log/nginx/access.log", column: "source", ref: "location" },
  ] as { key: string; value: string; column: string; ref?: string }[],
  parserEvidence: ev("aegis", "\"rule_level\": rule.get(\"level\"),", "collectors/wazuh.py"),
};

/* ------------------------------------------------------------------ */
/* Stage 2 — evidence                                                   */
/* ------------------------------------------------------------------ */

export const enrichmentKeys = {
  keys: ["techniques", "cves", "cve_count", "threat_actors", "malware", "campaigns", "signals", "priority_components", "rationale"],
  evidence: ev("aegis", "\"priority_components\": prio[\"components\"],", "backend/app/wazuh_enrichment/engine.py"),
};

export const collectedSources = ["src-attack", "src-nvd", "src-epss", "src-kev", "src-misp"];

/* ------------------------------------------------------------------ */
/* Stage 3 — correlation                                                */
/* ------------------------------------------------------------------ */

export const t1190Rule = {
  lines: [
    "CorrelationRule(",
    "    \"T1190\", \"Initial Access\", 0.7,",
    "    (\"sql injection\", \"sqli\", \"deserialization\", \"xml external entity\",",
    "     \"xxe\", \"server-side request forgery\", \"ssrf\", \"local file inclusion\",",
    "     \"remote file inclusion\", \"lfi\", \"rfi\"),",
    "    \"Exploitation of a public-facing application weakness\",",
    "),",
  ],
  evidence: ev(
    "aegis",
    "CorrelationRule( \"T1190\", \"Initial Access\", 0.7, (\"sql injection\", \"sqli\", \"deserialization\", \"xml external entity\", \"xxe\", \"server-side request forgery\", \"ssrf\", \"local file inclusion\", \"remote file inclusion\", \"lfi\", \"rfi\"), \"Exploitation of a public-facing application weakness\", ),",
    "backend/app/correlation/rules.py",
  ),
};

export const noisyOr = {
  formula: "score = 1 − Π(1 − wᵢ)",
  formulaEvidence: ev("aegis", "their weights combine via noisy-OR (`1 − Π(1 − wᵢ)`)", "README.md"),
  buckets: [
    { level: "HIGH", rule: "≥ 0.7" },
    { level: "MEDIUM", rule: "≥ 0.4" },
    { level: "LOW", rule: "below 0.4" },
  ],
  bucketsEvidence: ev("aegis", "3. The score is bucketed: HIGH ≥ 0.7, MEDIUM ≥ 0.4, otherwise LOW.", "backend/app/correlation/engine.py"),
  examples: [
    {
      call: "combine_weights([0.7, 0.5]) == 0.85",
      note: "1 − (1 − 0.7)(1 − 0.5) = 0.85",
      evidence: ev("aegis", "assert combine_weights([0.7, 0.5]) == 0.85", "tests/test_correlations.py"),
    },
    {
      call: "correlate_description(\"SQL injection allows remote code execution\")",
      note: "matches T1190 and T1203",
      evidence: ev("aegis", "matches = correlate_description(\"SQL injection allows remote code execution\")", "tests/test_correlations.py"),
    },
  ],
};

/* ------------------------------------------------------------------ */
/* Stage 4 — risk                                                       */
/* ------------------------------------------------------------------ */

export interface WeightPart {
  key: string;
  weight: number;
  input: string;
  /** Ledger ref when this input is known from the case file. */
  ref?: string;
}

export const socPriority = {
  name: "Alert SOC priority",
  note: "Scores this alert. Separate from Wazuh severity.",
  parts: [
    { key: "wazuh_severity", weight: 0.25, input: "rule_level / 15", ref: "level" },
    { key: "existing_risk", weight: 0.2, input: "max ML risk of related CVEs" },
    { key: "epss", weight: 0.2, input: "max EPSS of related CVEs" },
    { key: "cve_breadth", weight: 0.15, input: "related CVEs, up to 5" },
    { key: "technique_breadth", weight: 0.1, input: "techniques, up to 5" },
    { key: "actor_present", weight: 0.1, input: "an attributed actor" },
  ] as WeightPart[],
  evidence: ev(
    "aegis",
    "base = 100 * ( 0.25 * wazuh_severity     (rule_level / 15) + 0.20 * existing_risk       (max ML risk of related CVEs / 100) + 0.20 * epss                (max EPSS of related CVEs) + 0.15 * cve_breadth         (min(#related_cves, 5) / 5) + 0.10 * technique_breadth   (min(#techniques, 5) / 5) + 0.10 * actor_present )",
    "docs/wazuh_soc_architecture.md",
  ),
};

export const cvePriority = {
  name: "CVE priority (Priority Engine v2)",
  note: "Scores each CVE. EPSS carries the largest weight.",
  parts: [
    { key: "cvss", weight: 0.2, input: "CVSS" },
    { key: "correlation", weight: 0.15, input: "correlation confidence" },
    { key: "ml", weight: 0.15, input: "ML risk" },
    { key: "epss", weight: 0.3, input: "EPSS" },
    { key: "attack", weight: 0.2, input: "ATT&CK strength" },
  ] as WeightPart[],
  evidence: ev("aegis", "The five predictive signals are a weighted blend (CVSS 0.20, correlation confidence 0.15, ML risk", "README.md"),
};

export const kevOverride = {
  formula: "final = min(100, max(base, 75) + 15)",
  evidence: ev("aegis", "final  = base, unless KEV → final = min(100, max(base, 75) + 15)", "backend/app/prioritization/engine.py"),
};

export const riskLevels = {
  levels: [
    { level: "CRITICAL", rule: "≥ 75" },
    { level: "HIGH", rule: "≥ 50" },
    { level: "MEDIUM", rule: "≥ 25" },
    { level: "LOW", rule: "< 25" },
  ],
  evidence: ev("aegis", "Levels: CRITICAL ≥ 75, HIGH ≥ 50, MEDIUM ≥ 25, LOW < 25.", "docs/wazuh_soc_architecture.md"),
};

/** What each ML risk-model version adds, and its top feature. */
export const modelVersions: { v: string; adds: string; top: string; evidence: Evidence }[] = [
  { v: "V1", adds: "CVE, correlation and ATT&CK features", top: "cvss_score", evidence: ev("aegis", "| V1 | CVE + correlation + ATT&CK | `cvss_score` |", "docs/graph_analytics.md") },
  { v: "V2", adds: "EPSS and CISA KEV", top: "kev_age_days", evidence: ev("aegis", "| V2 | EPSS + CISA KEV | `kev_age_days` |", "docs/graph_analytics.md") },
  { v: "V3", adds: "MISP actor attribution", top: "misp_actor_linked", evidence: ev("aegis", "| V3 | MISP actor attribution | `misp_actor_linked` |", "docs/graph_analytics.md") },
  { v: "V4", adds: "Wazuh alert telemetry", top: "misp_actor_linked", evidence: ev("aegis", "| V4 | live Wazuh telemetry | `misp_actor_linked`", "docs/graph_analytics.md") },
  { v: "V5", adds: "Graph topology from GDS", top: "cve_degree", evidence: ev("aegis", "graph topology (GDS)", "docs/graph_analytics.md") },
  { v: "V6", adds: "Graph embeddings and link prediction", top: "cve_degree", evidence: ev("aegis", "V6 layers predictive-intelligence features on the graph-topology model;", "docs/phases_15_17.md") },
];

export const weakSupervision = {
  noTruth: ev("aegis", "The platform has no observed ground truth for \"risk\" (no exploitation outcomes, no analyst labels).", "README.md"),
  label: ev("aegis", "Supervised learning on real labels is therefore not possible today.", "README.md"),
  model: ev("aegis", "Prefers XGBoost; falls back to scikit-learn's RandomForest if XGBoost is not available.", "ml/risk_model.py"),
  byConstruction: ev("aegis", "Because the label is a function of the same features, held-out regression metrics are high by construction", "README.md"),
  meaning: ev("aegis", "they confirm the model faithfully learns the target, *not* that it predicts real-world exploitation", "README.md"),
  aid: ev("aegis", "Treat the score as a transparent prioritization aid, not a validated probability.", "README.md"),
  swappable: ev("aegis", "a serving pipeline whose labels can later be replaced by real signals", "README.md"),
  kevAnchor: ev("aegis", "KEV-listed CVEs are anchored ≥ 90", "README.md"),
};

/* ------------------------------------------------------------------ */
/* Stage 5 — investigation graph                                        */
/* ------------------------------------------------------------------ */

export interface GraphNode {
  type: string;
  /** Known value from the fixture, or null when the database would resolve it. */
  value: string | null;
  ref?: string;
  /** Relationship from the previous node in the chain. */
  rel?: string;
  hop?: number;
}

export const graphChain: GraphNode[] = [
  { type: "Alert", value: "alert-0001" },
  { type: "Technique", value: "T1190", ref: "mitre", rel: "USES_TECHNIQUE", hop: 1 },
  { type: "CVE", value: null, rel: "CORRELATED_TO", hop: 2 },
  { type: "ThreatActor", value: null, rel: "ATTRIBUTED_TO", hop: 3 },
];

export const graphBranches: GraphNode[] = [
  { type: "Malware", value: null, rel: "USES", hop: 4 },
  { type: "Campaign", value: null, rel: "RUNS", hop: 4 },
];

export const graphSide: GraphNode = { type: "Agent", value: "web-server-01", ref: "agent", rel: "OBSERVED_ON", hop: 1 };

export const graphEvidence = [
  ev("aegis", "Alert ─USES_TECHNIQUE▶ Technique ─CORRELATED_TO▶ CVE ─ATTRIBUTED_TO▶ ThreatActor", "docs/graph_analytics.md"),
  ev("aegis", "├─USES▶ Malware", "docs/graph_analytics.md"),
  ev("aegis", "└─RUNS▶ Campaign", "docs/graph_analytics.md"),
  ev("aegis", "Relationships: `OBSERVED_ON`, `USES_TECHNIQUE`, `CORRELATED_TO` (confidence),", "docs/graph_schema.md"),
];

export const gdsAlgorithms: { name: string; proc: string; evidence: Evidence }[] = [
  { name: "Degree centrality", proc: "gds.degree", evidence: ev("aegis", "| Degree centrality | `gds.degree` |", "docs/graph_analytics.md") },
  { name: "PageRank", proc: "gds.pageRank", evidence: ev("aegis", "| PageRank | `gds.pageRank` |", "docs/graph_analytics.md") },
  { name: "Betweenness", proc: "gds.betweenness", evidence: ev("aegis", "| Betweenness | `gds.betweenness` |", "docs/graph_analytics.md") },
  { name: "Louvain communities", proc: "gds.louvain", evidence: ev("aegis", "| Louvain communities | `gds.louvain` |", "docs/graph_analytics.md") },
  { name: "Weakly-connected components", proc: "gds.wcc", evidence: ev("aegis", "| Weakly-connected components | `gds.wcc` |", "docs/graph_analytics.md") },
  { name: "Node similarity", proc: "gds.nodeSimilarity", evidence: ev("aegis", "| Node similarity | `gds.nodeSimilarity` |", "docs/graph_analytics.md") },
];

/* ------------------------------------------------------------------ */
/* Stage 6 — AI analyst: tool fence, plan, provider switch               */
/* ------------------------------------------------------------------ */

export const agentTools = [
  "graph_investigation",
  "attack_path_investigation",
  "alert_investigation",
  "threat_actor_investigation",
  "campaign_investigation",
  "technique_investigation",
  "risk_score_retrieval",
  "graph_metrics_retrieval",
  "wazuh_alert_retrieval",
  "misp_intel_retrieval",
  "kev_retrieval",
  "epss_retrieval",
] as const;

export const agentToolsEvidence = ev(
  "aegis",
  "`graph_investigation`, `attack_path_investigation`, `alert_investigation`, `threat_actor_investigation`, `campaign_investigation`, `technique_investigation`, `risk_score_retrieval`, `graph_metrics_retrieval`, `wazuh_alert_retrieval`, `misp_intel_retrieval`, `kev_retrieval`, `epss_retrieval`.",
  "docs/agentic_soc.md",
);

export const fenceRefusal = {
  text: "Anything outside the registry: run_tool raises ValueError.",
  evidence: ev("aegis", "raise ValueError(f\"Unknown agent tool '{name}'\")", "backend/app/agents/tools.py"),
};

export interface PlanStep {
  tool: string;
  params: string;
  rationale: string;
  /** What the step returns for this case file. `refs` point at ledger entries. */
  output: string;
  refs?: string[];
  evidence: Evidence;
}

/** The planner's real alert plan (backend/app/agents/planner.py), in order. */
export const alertPlan: PlanStep[] = [
  {
    tool: "wazuh_alert_retrieval",
    params: "alert_id",
    rationale: "Retrieve the raw Wazuh alert and its enrichment",
    output: "rule_level 12, mitre_techniques [T1190]",
    refs: ["level", "mitre"],
    evidence: ev("aegis", "(\"wazuh_alert_retrieval\", {\"alert_id\": aid}, \"Retrieve the raw Wazuh alert and its enrichment\"),", "backend/app/agents/planner.py"),
  },
  {
    tool: "alert_investigation",
    params: "alert_id",
    rationale: "Correlate alert -> technique -> CVE -> actor",
    output: "techniques, CVEs and actors; sets $cve_id",
    evidence: ev("aegis", "(\"alert_investigation\", {\"alert_id\": aid}, \"Correlate alert -> technique -> CVE -> actor\"),", "backend/app/agents/planner.py"),
  },
  {
    tool: "attack_path_investigation",
    params: "alert_id",
    rationale: "Enumerate attack paths from the alert",
    output: "attack paths read from the graph",
    evidence: ev("aegis", "(\"attack_path_investigation\", {\"alert_id\": aid}, \"Enumerate attack paths from the alert\"),", "backend/app/agents/planner.py"),
  },
  {
    tool: "risk_score_retrieval",
    params: "$cve_id",
    rationale: "ML risk + priority for the top related CVE",
    output: "$cve_id from step 2; skipped if unresolved",
    evidence: ev("aegis", "(\"risk_score_retrieval\", {\"cve_id\": \"$cve_id\"}, \"ML risk + priority for the top related CVE\"),", "backend/app/agents/planner.py"),
  },
  {
    tool: "epss_retrieval",
    params: "$cve_id",
    rationale: "EPSS exploit probability of the CVE",
    output: "$cve_id from step 2; skipped if unresolved",
    evidence: ev("aegis", "(\"epss_retrieval\", {\"cve_id\": \"$cve_id\"}, \"EPSS exploit probability of the CVE\"),", "backend/app/agents/planner.py"),
  },
  {
    tool: "kev_retrieval",
    params: "$cve_id",
    rationale: "CISA KEV (active-exploitation) status",
    output: "$cve_id from step 2; skipped if unresolved",
    evidence: ev("aegis", "(\"kev_retrieval\", {\"cve_id\": \"$cve_id\"}, \"CISA KEV (active-exploitation) status\"),", "backend/app/agents/planner.py"),
  },
  {
    tool: "graph_metrics_retrieval",
    params: "CVE, $cve_id",
    rationale: "Graph centrality of the CVE",
    output: "$cve_id from step 2; skipped if unresolved",
    evidence: ev("aegis", "(\"graph_metrics_retrieval\", {\"entity_type\": \"CVE\", \"entity_id\": \"$cve_id\"}, \"Graph centrality of the CVE\"),", "backend/app/agents/planner.py"),
  },
  {
    tool: "misp_intel_retrieval",
    params: "$cve_id",
    rationale: "MISP threat-actor attribution",
    output: "$cve_id from step 2; skipped if unresolved",
    evidence: ev("aegis", "(\"misp_intel_retrieval\", {\"cve_id\": \"$cve_id\"}, \"MISP threat-actor attribution\"),", "backend/app/agents/planner.py"),
  },
];

export const planAfter = [
  { call: "blast_radius.compute()", output: "graph-driven impact surface, depth ≤ 4", refs: ["blast"] },
  { call: "report_generator.build_report()", output: "risk assessment and cited recommendations" },
];

export const planAfterEvidence = ev("aegis", "Pipeline: plan -> execute tools (collect evidence + log) -> blast radius -> report -> persist.", "backend/app/agents/agent.py");
export const planSkipEvidence = ev("aegis", "unresolved steps are skipped (logged), never fabricated.", "docs/agentic_soc.md");
export const planLogEvidence = ev("aegis", "every call is logged with status, summary, and duration.", "docs/agentic_soc.md");

export type Provider = "none" | "gemini" | "openai" | "ollama";
export const providers: Provider[] = ["none", "gemini", "openai", "ollama"];

export const providerFacts = {
  options: ev("aegis", "`AI_PROVIDER` ∈ `none | gemini | openai | ollama` selects the backend;", "docs/ai_analyst.md"),
  noneDefault: ev("aegis", "AI_PROVIDER=none (default) needs no LLM keys.", "README.md"),
  narrate: ev("aegis", "to have an LLM narrate the same evidence.", "README.md"),
  fallback: ev("aegis", "On any provider error the analyst falls back to the grounded summary.", "docs/ai_analyst.md"),
  prompt: ev("aegis", "never invent CVEs, actors, scores, or relationships.", "backend/app/ai/prompt_templates.py"),
  models: {
    gemini: { model: "gemini-1.5-flash", evidence: ev("aegis", "\"gemini\": \"gemini-1.5-flash\",", "backend/app/ai/providers.py") },
    openai: { model: "gpt-4o-mini", evidence: ev("aegis", "\"openai\": \"gpt-4o-mini\",", "backend/app/ai/providers.py") },
    ollama: { model: "llama3", evidence: ev("aegis", "\"ollama\": \"llama3\",", "backend/app/ai/providers.py") },
  } as Record<Exclude<Provider, "none">, { model: string; evidence: Evidence }>,
};

/**
 * The deterministic answer, in the generator's own format, filled only from the
 * case file. `‹…›` tokens stand for values the platform reads from its database.
 */
export const deterministicAnswer = {
  tokens: [
    "SOC", " priority", " ‹n›", " (‹level›):", " …;", " Wazuh", " level", " 12.", " Supporting", " entities:", " T1190,", " …",
  ],
  caption: "The deterministic generator's format, filled from this case file. ‹ › and … stand for values the platform reads from its database.",
  evidence: [
    ev("aegis", "rationale = f\"SOC priority {final:.0f} ({priority_level(final)}): \" + \"; \".join(reasons)", "backend/app/wazuh_enrichment/engine.py"),
    ev("aegis", "reasons.append(f\"Wazuh level {signals.get('rule_level', 0)}\")", "backend/app/wazuh_enrichment/engine.py"),
    ev("aegis", "parts.append(f\"Supporting entities: {names}.\")", "backend/app/ai/response_generator.py"),
    ev("aegis", "return _deterministic(evidence), \"deterministic\"", "backend/app/ai/response_generator.py"),
  ],
};

/** Narration shown when a provider is switched on. Restates ledger facts only. */
export const narration = {
  label: "Illustrative narration — the real wording depends on the model",
  parts: [
    { text: "Wazuh raised a level 12 alert", ref: "level" },
    { text: " on web-server-01", ref: "agent" },
    { text: ": a possible SQL injection against a public-facing web application", ref: "description" },
    { text: ", mapped to ATT&CK T1190", ref: "mitre" },
    { text: ". The ledger names no CVE or actor for this alert, so this briefing doesn't either." },
  ] as { text: string; ref?: string }[],
};

/* ------------------------------------------------------------------ */
/* Stages 7–9 — recommendation, approval gate, response                 */
/* ------------------------------------------------------------------ */

export const recommendation = {
  label: "Built from the real rule and this alert's technique. Severity and confidence come from the investigation report.",
  fields: [
    { key: "source_type", value: "\"investigation\"" },
    { key: "action_type", value: "\"tune_detection\"", ref: "rec-type" },
    { key: "title", value: "\"Validate / tune detections\"", ref: "rec-rule" },
    { key: "description", value: "\"Ensure coverage for ATT&CK technique(s): T1190.\"", ref: "mitre" },
    { key: "severity", value: "‹risk_assessment.level›", placeholder: true },
    { key: "rationale", value: "\"Derived from agent evidence: alert_investigation\"" },
    { key: "evidence", value: "{\"evidence_tool\": \"alert_investigation\", …}" },
    { key: "confidence", value: "‹investigation confidence›", placeholder: true },
  ] as { key: string; value: string; ref?: string; placeholder?: boolean }[],
  evidence: [
    ev("aegis", "\"detail\": f\"Ensure coverage for ATT&CK technique(s): {', '.join(techniques[:5])}.\",", "backend/app/agents/report_generator.py"),
    ev("aegis", "\"evidence\": \"alert_investigation\"})", "backend/app/agents/report_generator.py"),
    ev("aegis", "rationale=f\"Derived from agent evidence: {rec.get('evidence', 'n/a')}\",", "backend/app/response_engine.py"),
    ev("aegis", "evidence={\"evidence_tool\": rec.get(\"evidence\"), \"target\": inv.target,", "backend/app/response_engine.py"),
    ev("aegis", "confidence=inv.confidence or 0.0, status=PENDING, created_at=_now())", "backend/app/response_engine.py"),
  ],
  otherRules: "Patch, prioritize, escalate and threat-hunt recommendations need KEV, EPSS, risk and actor evidence; the fixture has none of it, so they don't appear.",
  otherRulesEvidence: ev("aegis", "(Patch immediately if KEV; prioritize if high EPSS; escalate if CRITICAL/HIGH; hunt actor TTPs; tune detections; investigate related alerts)", "docs/agentic_soc.md"),
};

export type RecStatus = "pending" | "approved" | "rejected" | "executed" | "verified" | "failed";
export type GateAction = "approve" | "reject" | "execute" | "verify";

export const simulationLabel = "Simulated in your browser; it follows the documented state machine.";

/** The engine's real refusal messages (backend/app/response_engine.py), mapped to HTTP 409. */
export const gateMessages: Record<GateAction, (status: RecStatus) => string> = {
  approve: (s) => `Cannot approve a '${s}' recommendation`,
  reject: (s) => `Cannot reject a '${s}' recommendation`,
  execute: (s) => `Refusing to execute: recommendation is '${s}', not 'approved'. Analyst approval is required before execution.`,
  verify: (s) => `Cannot verify a '${s}' recommendation (must be executed)`,
};

export const gateEvidence = {
  approve: ev("aegis", "raise PermissionError(f\"Cannot approve a '{r.status}' recommendation\")", "backend/app/response_engine.py"),
  reject: ev("aegis", "raise PermissionError(f\"Cannot reject a '{r.status}' recommendation\")", "backend/app/response_engine.py"),
  execute: ev("aegis", "f\"Refusing to execute: recommendation is '{r.status}', not 'approved'. \"", "backend/app/response_engine.py"),
  executeTail: ev("aegis", "\"Analyst approval is required before execution.\")", "backend/app/response_engine.py"),
  verify: ev("aegis", "raise PermissionError(f\"Cannot verify a '{r.status}' recommendation (must be executed)\")", "backend/app/response_engine.py"),
  to409: ev("aegis", "raise HTTPException(status_code=409, detail=str(exc))", "backend/app/routers/response.py"),
  endpoint: ev("aegis", "`/response/recommendations/{id}/approve|reject|execute|verify` — approval-gated response actions", "README.md"),
  refusedNotLogged: "A refused call changes no state, so nothing is appended to the audit log.",
};

/** What the credential-free mock returns, computed the way MockProvider does. */
export const mockExecution = {
  ticketId: "MOCK-4E288705",
  derivation: "sha1 of the ticket title plus \"response_action\", first 8 hex characters",
  evidence: [
    ev("aegis", "tid = \"MOCK-\" + hashlib.sha1(f\"{title}{extra.get('kind','')}\".encode()).hexdigest()[:8].upper()", "backend/app/ticketing/providers.py"),
    ev("aegis", "return {\"provider\": \"mock\", \"ticket_id\": tid, \"status\": \"created\",", "backend/app/ticketing/providers.py"),
    ev("aegis", "title = f\"[RESPONSE:{action.get('action_type', 'action')}] {action.get('title', '')}\"[:250]", "backend/app/ticketing/service.py"),
    ev("aegis", "kind=\"response_action\", action_type=action.get(\"action_type\"),", "backend/app/ticketing/service.py"),
  ],
  verifyRule: ev("aegis", "ok = bool(res.get(\"status\") in (\"created\", \"triggered\", \"accepted\") or res.get(\"ticket_id\"))", "backend/app/response_engine.py"),
};

export const auditFacts = {
  actorNote: "The platform records whatever actor the request names; here that's you.",
  actorEvidence: ev("aegis", "curl -X POST localhost:8000/response/recommendations/1/approve -d '{\"approver\":\"jane\"}'", "README.md"),
  generatedEvidence: ev("aegis", "_audit(db, row.id, \"generated\", \"system\",", "backend/app/response_engine.py"),
  columns: ev("aegis", "append-only (recommendation_id, event, actor, detail, ts).", "docs/response_approval.md"),
};

/* ------------------------------------------------------------------ */
/* Case study: grounding, stack, limits                                 */
/* ------------------------------------------------------------------ */

export const grounding = {
  evidence: {
    title: "Evidence is kept",
    body: "Every link the platform draws carries the evidence behind it: matched phrases for correlations, a stored record and rationale for each alert. Agent memory is candid about its limits: it keeps summaries, and the full findings stay in the report.",
    quotes: [
      ev("aegis", "The matched phrases are stored verbatim as the evidence for the link, so every correlation is auditable.", "backend/app/correlation/engine.py"),
      ev("aegis", "Heavy raw evidence is trimmed to summaries on save - the full structured findings live in the report.", "backend/app/agents/memory.py"),
    ],
  },
  llm: {
    title: "The LLM is optional",
    body: "Routing, evidence gathering and the default answer are all deterministic. A provider can be switched on to narrate, and its prompt forbids anything beyond the evidence. If it fails, the grounded summary comes back.",
    quotes: [
      ev("aegis", "AI_PROVIDER=none (default) needs no LLM keys.", "README.md"),
      ev("aegis", "never invent CVEs, actors, scores, or relationships.", "backend/app/ai/prompt_templates.py"),
      ev("aegis", "On any provider error the analyst falls back to the grounded summary.", "docs/ai_analyst.md"),
    ],
  },
  fence: {
    title: "The agent is fenced",
    body: "The agent's plan is fixed per investigation type, and it can only call twelve read-only tools. Graph access runs through parameterized services and vetted read-only templates that reject write tokens.",
    quotes: [
      ev("aegis", "The LLM never writes or executes Cypher.", "docs/ai_analyst.md"),
      ev("aegis", "So arbitrary or mutating graph queries are impossible by construction.", "docs/ai_analyst.md"),
      ev("aegis", "unresolved steps are skipped (logged), never fabricated.", "docs/agentic_soc.md"),
    ],
  },
};

/** Section copy for /work/aegisai. Facts in these leads are quoted nearby on the page. */
export const caseStudy = {
  metaDescription:
    "Follow one alert through AegisAI, a threat-intelligence platform by Pushkar Singh: cited evidence, an optional LLM, a fenced agent, and response actions that wait for a person's approval.",
  whatItDoes: {
    title: "What it does",
    lead: "It pulls security alerts, adds what the platform already knows about each one, ranks what matters and investigates with an agent that can only read. Every stage keeps its evidence. The last one waits for a person.",
  },
  follow: {
    title: "Follow an alert",
    lead: "One alert from the repository's test fixture, through all nine stages. Switch the LLM on and off, run the agent's plan, and try executing the recommendation before anyone has approved it.",
  },
  grounded: {
    title: "How it stays grounded",
    lead: "Three decisions carry most of the weight: keep the evidence, make the LLM optional, and fence the agent in.",
  },
  people: {
    title: "People decide",
  },
  risk: {
    title: "The risk model, honestly",
    lead: "There's no ground truth for risk in this data, so the model learns a transparent heuristic label instead. The README spells out what follows: the held-out metrics are high by construction. They show the model learned its target, not that it predicts exploitation. The pipeline is built so real labels can replace the heuristic one later.",
  },
  stack: {
    title: "Stack",
    lead: "Only what the repository itself names.",
  },
  limits: {
    title: "What it isn't",
    lead: "What the repository doesn't claim, said plainly.",
  },
};

export const peopleDecide = {
  body: "Recommendations become actions only through an explicit approval that is recorded first. Execution, verification and every transition in between land in an audit table with the actor and a timestamp.",
  quotes: [
    ev("aegis", "execution requires a prior recorded approval;", "docs/response_approval.md"),
    ev("aegis", "every transition (generated/approved/rejected/executed/verified) is logged with actor + timestamp in `response_audit`.", "docs/response_approval.md"),
  ],
};

export const stack: { group: string; items: { label: string; evidence: Evidence }[] }[] = [
  {
    group: "API and data",
    items: [
      { label: "Python", evidence: ev("aegis", "Python 3.11+ (3.14 tested)", "README.md") },
      { label: "FastAPI and Uvicorn", evidence: ev("aegis", "| API | FastAPI + Uvicorn |", "README.md") },
      { label: "PostgreSQL 16", evidence: ev("aegis", "| Database | PostgreSQL 16 (Docker) |", "README.md") },
      { label: "SQLAlchemy and Alembic", evidence: ev("aegis", "| ORM / Migrations | SQLAlchemy 2.x / Alembic", "README.md") },
      { label: "Pandas", evidence: ev("aegis", "| Data processing | Pandas |", "README.md") },
    ],
  },
  {
    group: "Graph",
    items: [
      { label: "Neo4j 5 community", evidence: ev("aegis", "image: neo4j:5-community", "docker-compose.yml") },
      { label: "Neo4j Graph Data Science", evidence: ev("aegis", "# Graph Data Science plugin (Phase 12). Auto-downloaded on first start.", "docker-compose.yml") },
    ],
  },
  {
    group: "Machine learning",
    items: [
      { label: "XGBoost", evidence: ev("aegis", "Prefers XGBoost; falls back to scikit-learn's RandomForest", "ml/risk_model.py") },
      { label: "scikit-learn", evidence: ev("aegis", "permutation importance (scikit-learn)", "ml/explainability.py") },
    ],
  },
  {
    group: "LLM providers (optional)",
    items: [
      { label: "Gemini, OpenAI or Ollama", evidence: ev("aegis", "provider-agnostic LLM abstraction (Gemini/OpenAI/Ollama)", "README.md") },
      { label: "Plain REST calls with requests", evidence: ev("aegis", "each is called over its REST API with `requests` (no heavy SDKs).", "docs/ai_analyst.md") },
    ],
  },
  {
    group: "Security integrations",
    items: [
      { label: "Wazuh", evidence: ev("aegis", "Pull agents (Manager API) and alerts (OpenSearch indexer)", "README.md") },
      { label: "MISP via PyMISP", evidence: ev("aegis", "the production connector uses PyMISP against a live MISP instance", "README.md") },
      { label: "Shuffle SOAR", evidence: ev("aegis", "Shuffle SOAR via webhook (preferred) or workflow execute API.", "backend/app/ticketing/providers.py") },
      { label: "Jira and TheHive", evidence: ev("aegis", "ticketing/SOAR abstraction (Mock/Jira/TheHive/Shuffle-webhook)", "README.md") },
    ],
  },
  {
    group: "Running it",
    items: [
      { label: "Docker Compose", evidence: ev("aegis", "Docker Desktop with Docker Compose v2+", "README.md") },
      { label: "APScheduler", evidence: ev("aegis", "APScheduler orchestration", "README.md") },
      { label: "Streamlit", evidence: ev("aegis", "A 69-page Streamlit dashboard", "README.md") },
      { label: "Plotly", evidence: ev("aegis", "Charts are rendered with Plotly", "README.md") },
    ],
  },
];

export const limits: { text: string; evidence: Evidence }[] = [
  {
    text: "Execution goes to a mock SOAR provider by default. Running Shuffle playbooks for approved actions is listed as future work.",
    evidence: ev("aegis", "live Shuffle playbooks for approved actions", "README.md"),
  },
  {
    text: "Verify confirms that the provider accepted an action. It doesn't check that the fix took effect on any host.",
    evidence: ev("aegis", "Verify that the executed action was accepted by the SOAR provider.", "backend/app/response_engine.py"),
  },
  {
    text: "Approvals record the approver's name from the request; they aren't tied to user accounts.",
    evidence: ev("aegis", "-d '{\"approver\":\"jane\"}'", "README.md"),
  },
  {
    text: "The audit table is append-only by design; it isn't cryptographically signed.",
    evidence: ev("aegis", "append-only (recommendation_id, event, actor, detail, ts).", "docs/response_approval.md"),
  },
  {
    text: "The MISP counts come from a sample fixture, used because no MISP instance was available.",
    evidence: ev("aegis", "With no instance available, an offline", "README.md"),
  },
  {
    text: "The risk score is a prioritization aid, not a validated probability of exploitation.",
    evidence: ev("aegis", "Treat the score as a transparent prioritization aid, not a validated probability.", "README.md"),
  },
  {
    text: "Correlation is keyword rules, not a learned model, built to be swapped out later.",
    evidence: ev("aegis", "the design is built to be swapped for an ML/graph model later without a schema change.", "README.md"),
  },
  {
    text: "It runs on a developer machine: PostgreSQL and Neo4j in Docker Compose, the API under uvicorn.",
    evidence: ev("aegis", "uvicorn backend.app.main:app --reload", "README.md"),
  },
];
