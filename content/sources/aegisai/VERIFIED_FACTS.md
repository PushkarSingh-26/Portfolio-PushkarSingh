# AegisAI project — Verified Fact Sheet (exact quotes)

## Provenance

- **Repository:** https://github.com/PushkarSingh-26/cyber-threat-intelligence-platform (public, default branch `main`)
- **Commit quoted:** `main` HEAD `ab54d2b343ef3d508f562258ec8bf035cb23f3f3` ("Polish dashboard UI and navigation", 2026-08-10). Git tags present: `phase14-complete`, `phase17-complete`, `phase18-complete`, `phase19-complete`.
- **Retrieved:** 2026-09-11 with `curl` from `raw.githubusercontent.com` and the GitHub REST API (no summarizing tools). All 81 downloaded files were then checked byte-for-byte against the repo tarball from `codeload.github.com`: 0 differences.
- **How quotes were made:** a script copied exact line ranges out of the downloaded files. Nothing inside a quote block was retyped or paraphrased. Markdown markup such as `**`, backticks and box-drawing characters is kept as it appears in the source. `Lx-Ly` are 1-based line numbers in the file shown.
- **Rule for the website:** state only what a quote below supports. The "NOT FOUND IN DOCS" lines list claims to avoid.

---

## 0. Name and identity — READ FIRST

**The string "AegisAI" (or "Aegis") does not appear anywhere in the repository.** I searched every file in the tarball, case-insensitive. The project names itself as follows:

- **README title** — `README.md` L1-L3

~~~~text
# Cyber Threat Intelligence Platform

A platform for collecting, enriching, analyzing, and serving cyber threat intelligence.
~~~~

- **FastAPI app title (code)** — `backend/app/main.py` L77

~~~~text
    title="Cyber Threat Intelligence Platform",
~~~~

- **Dashboard page title (code)** — `dashboard/app.py` L38-L40

~~~~text
st.set_page_config(
    page_title="CTI Platform",
    page_icon="🛡️",
~~~~


Website implication: "AegisAI" is a portfolio or brand name that the source does not back up. Link to the repo as "Cyber Threat Intelligence Platform", or say plainly that AegisAI is the project's portfolio name.

---

## 1. ALERT — what an alert is and where it comes from

### Supported facts

- **Wazuh ingestion: agents from Manager API, alerts from OpenSearch indexer** — `README.md` L350-L361

~~~~text
### Ingesting Wazuh SOC data (Phase 10)

Pull agents (Manager API) and alerts (OpenSearch indexer), then enrich + score:

```powershell
# Live (requires WAZUH_API_URL/USERNAME/PASSWORD + INDEXER_URL/USERNAME/PASSWORD in .env):
python -m collectors.wazuh                 # full sync (agents + alerts)
python -m collectors.wazuh --since 2026-06-01   # incremental alerts

# Offline / no Wazuh credentials:
python -m collectors.wazuh --sample collectors/fixtures/sample_wazuh.json
```
~~~~

- **Enrichment + separate SOC priority** — `README.md` L363-L366

~~~~text
Each alert is enriched (technique → CVEs → EPSS/KEV → actor → malware/campaign)
with stored evidence, then assigned a **SOC priority** (0–100) that is *separate*
from Wazuh severity. See [docs/wazuh_soc_architecture.md](docs/wazuh_soc_architecture.md)
for the architecture and enrichment-flow diagrams.
~~~~

- **Connector docstring (code)** — `collectors/wazuh.py` L1-L16

~~~~text
"""Wazuh SOC connector (Phase 10).

Production path pulls agents from the Wazuh Manager API (JWT auth) and alerts
from the Wazuh Indexer (OpenSearch). All credentials come from environment
variables; nothing is hardcoded.

    python -m collectors.wazuh                       # full sync (agents + alerts)
    python -m collectors.wazuh --since 2026-06-01    # incremental alerts since
    python -m collectors.wazuh --sample collectors/fixtures/sample_wazuh.json  # offline

Environment variables:
    WAZUH_API_URL, WAZUH_USERNAME, WAZUH_PASSWORD     (manager API :55000)
    INDEXER_URL, INDEXER_USERNAME, INDEXER_PASSWORD   (indexer :9200)
    WAZUH_VERIFY_SSL                                  (true/false)

After ingestion the alert enrichment + SOC priority engine is run.
~~~~

- **Alert index pattern (code)** — `collectors/wazuh.py` L39

~~~~text
ALERTS_INDEX = "wazuh-alerts-*"
~~~~

- **Indexer paging with search_after (code)** — `collectors/wazuh.py` L101-L102

~~~~text
def fetch_alerts(session, settings, since: str | None) -> list[dict]:
    """Page through alerts using search_after (handles >10k results)."""
~~~~

- **Fields parsed from each alert (code)** — `collectors/wazuh.py` L155-L175

~~~~text
def parse_alert(hit: dict) -> dict:
    src = hit.get("_source", hit)
    rule = src.get("rule", {}) or {}
    mitre = rule.get("mitre", {}) or {}
    technique_ids = mitre.get("id") or []
    if isinstance(technique_ids, str):
        technique_ids = [technique_ids]
    agent = src.get("agent", {}) or {}
    decoder = src.get("decoder", {}) or {}
    return {
        "wazuh_alert_id": hit.get("_id") or src.get("id") or "",
        "timestamp": _parse_ts(src.get("@timestamp") or src.get("timestamp")),
        "agent_id": str(agent.get("id")) if agent.get("id") is not None else None,
        "rule_id": str(rule.get("id")) if rule.get("id") is not None else None,
        "rule_level": rule.get("level"),
        "description": rule.get("description"),
        "source": src.get("location") or "wazuh",
        "decoder": decoder.get("name"),
        "mitre_techniques": technique_ids,
        "raw_event": src,
    }
~~~~

- **Architecture overview** — `docs/wazuh_soc_architecture.md` L3-L5

~~~~text
The CTI platform now ingests Wazuh telemetry and turns raw alerts into
threat-prioritized, CTI-enriched SOC events. Wazuh's native severity is never
modified; the platform adds a *separate* SOC priority and an enrichment record.
~~~~

- **Integration architecture diagram (ports)** — `docs/wazuh_soc_architecture.md` L9-L30

~~~~text
```
        WAZUH DEPLOYMENT (Docker)                     CTI PLATFORM
 ┌─────────────────────────────────┐      ┌──────────────────────────────────┐
 │ wazuh.manager-1   :55000 (API)  │      │ collectors/wazuh.py              │
 │   • agents, rules, JWT auth     │─────▶│   • JWT auth (env creds)         │
 │ wazuh.indexer-1   :9200 (OS)    │      │   • GET /agents (paginated)      │
 │   • wazuh-alerts-* documents    │─────▶│   • indexer _search (search_after)│
 │ wazuh.dashboard-1 :443          │      │   • retries + SSL toggle          │
 └─────────────────────────────────┘      └───────────────┬──────────────────┘
        credentials via ENV VARS only                      │ upsert
   WAZUH_API_URL / USERNAME / PASSWORD                      ▼
   INDEXER_URL / USERNAME / PASSWORD          ┌──────────────────────────────┐
   WAZUH_VERIFY_SSL                           │ wazuh_agents · wazuh_alerts   │
                                              └───────────────┬──────────────┘
                                                              ▼
                                          backend/app/wazuh_enrichment/engine.py
                                                              ▼
                                              ┌──────────────────────────────┐
                                              │ wazuh_alert_enrichment        │
                                              │  (CTI links + SOC priority)   │
                                              └──────────────────────────────┘
```
~~~~

- **Credentials + offline fixture** — `docs/wazuh_soc_architecture.md` L85-L91

~~~~text
## Credentials

All Wazuh/Indexer credentials are read from environment variables; nothing is
hardcoded. Live ingestion requires `WAZUH_API_URL`, `WAZUH_USERNAME`,
`WAZUH_PASSWORD`, `INDEXER_URL`, `INDEXER_USERNAME`, `INDEXER_PASSWORD`, and
`WAZUH_VERIFY_SSL`. For offline verification, `collectors/wazuh.py --sample`
loads a MISP/Wazuh-shaped JSON fixture through the identical parser/enrichment.
~~~~

- **Wazuh severity preserved (model docstring)** — `backend/app/models/wazuh.py` L1-L5

~~~~text
"""Wazuh SOC models (Phase 10): agents, alerts, and per-alert enrichment.

Wazuh's own severity (`rule_level`) is preserved verbatim on `wazuh_alerts`.
The CTI platform adds a *separate* `priority_score` in `wazuh_alert_enrichment`
so the SOC view never overwrites Wazuh's native severity.
~~~~

- **wazuh_alerts table columns (code)** — `backend/app/models/wazuh.py` L43-L57

~~~~text
class WazuhAlert(Base):
    __tablename__ = "wazuh_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    wazuh_alert_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    timestamp: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    agent_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    rule_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    rule_level: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    decoder: Mapped[str | None] = mapped_column(String(128), nullable=True)
    mitre_techniques: Mapped[list | None] = mapped_column(JSON, nullable=True)
    raw_event: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
~~~~


### Sample fixture structure (`collectors/fixtures/sample_wazuh.json`)

The top-level object has two keys, `"agents"` (3 entries, lines 3-5) and `"alerts"` (8 entries, lines 8-15). Each alert is an indexer-style hit: `_id`, then `_source` holding `@timestamp`, `agent{id,name}`, `rule{id,level,description,mitre{id[]}}`, `decoder{name}` and `location`.

- **Fixture skeleton** — `collectors/fixtures/sample_wazuh.json` L1-L2

~~~~text
{
  "agents": [
~~~~

- **Fixture skeleton (alerts key)** — `collectors/fixtures/sample_wazuh.json` L6-L7

~~~~text
  ],
  "alerts": [
~~~~

- **ONE CONCRETE SAMPLE ALERT, reproduced exactly (alert-0001)** — `collectors/fixtures/sample_wazuh.json` L8

~~~~text
    {"_id": "alert-0001", "_source": {"@timestamp": "2026-06-16T08:25:11", "agent": {"id": "001", "name": "web-server-01"}, "rule": {"id": "100210", "level": 12, "description": "Possible SQL injection against public-facing web application", "mitre": {"id": ["T1190"]}}, "decoder": {"name": "web-accesslog"}, "location": "/var/log/nginx/access.log"}},
~~~~

- **Second sample alert (alert-0002; web shell, two techniques)** — `collectors/fixtures/sample_wazuh.json` L9

~~~~text
    {"_id": "alert-0002", "_source": {"@timestamp": "2026-06-16T08:20:03", "agent": {"id": "001", "name": "web-server-01"}, "rule": {"id": "100305", "level": 13, "description": "Command and scripting interpreter execution via web shell", "mitre": {"id": ["T1059", "T1505.003"]}}, "decoder": {"name": "auditd"}, "location": "auditd"}},
~~~~

- **Sample agent 001 (the host in alert-0001)** — `collectors/fixtures/sample_wazuh.json` L3

~~~~text
    {"id": "001", "name": "web-server-01", "ip": "10.0.1.21", "os": {"name": "Ubuntu", "version": "22.04"}, "version": "Wazuh v4.9.0", "status": "active", "lastKeepAlive": "2026-06-16T08:30:00"},
~~~~


Derived from the fixture (counted, not stated in the docs): rule levels in the 8 alerts are 12, 13, 10, 14, 11, 8, 9, 3. Alert-0008 ("Windows logon success") has an empty `mitre.id` list.

### Superseded older doc (do not quote it as current)

- **Phase 8.4 doc says no Wazuh was deployed at that time (later superseded by Phase 10)** — `docs/wazuh_integration.md` L1-L5

~~~~text
# Phase 8.4 — Wazuh Readiness Layer: Architecture & Future Integration

**Status: FOUNDATION ONLY.** No live Wazuh instance is deployed or contacted in
this phase. This document describes the future ingestion, enrichment, and SOC
workflows, and how the foundation already built (the `/soc/*` API and the
~~~~


**NOT FOUND IN DOCS (ALERT):** the name "AegisAI"; any alert volume, EPS or throughput figure; real-time streaming (Kafka or websockets). Ingestion is a pull or scheduled sync. Nothing says a live production Wazuh estate was ingested. The docs give a live connector plus an offline fixture, and the repo's `docker-compose.yml` defines only PostgreSQL and Neo4j, with no Wazuh services. Also absent: EDR, SIEMs other than Wazuh, Sigma rules, and auto-generated detection rules.

---

## 2. EVIDENCE — how evidence is stored and preserved

### Supported facts

- **Correlation evidence = matched phrases** — `README.md` L227-L230

~~~~text
their weights combine via noisy-OR (`1 − Π(1 − wᵢ)`). The result is bucketed
HIGH ≥ 0.7 / MEDIUM ≥ 0.4 / LOW, and the matched phrases are stored as evidence
so every link is explainable. No LLMs or paid services are involved; the design
is built to be swapped for an ML/graph model later without a schema change.
~~~~

- **Correlation engine: phrases stored verbatim as evidence (code docstring)** — `backend/app/correlation/engine.py` L11-L12

~~~~text
4. The matched phrases are stored verbatim as the evidence for the link, so
   every correlation is auditable.
~~~~

- **MISP enrichment edges store evidence** — `README.md` L335-L340

~~~~text
Ingestion writes entities + event-membership edges, then runs the enrichment
engine ([backend/app/enrichment/engine.py](backend/app/enrichment/engine.py)),
which derives confidence-scored, **explainable** relationships: actor→technique
and malware→technique (event co-occurrence), actor→CVE (transitive
actor→technique→correlation→CVE), actor→malware, and IOC→actor/malware. Every
edge stores the evidence behind it.
~~~~

- **Per-alert enrichment stores evidence + rationale** — `docs/wazuh_soc_architecture.md` L45-L55

~~~~text
     ▼                                          │
 evidence{techniques, cves[], epss, kev,        ├── uses_malware ──▶ malware
          risk, actors, malware, campaigns}     └── attributed ───▶ campaign
     ▼
 SOC Priority Engine  →  priority_score (0-100) + level (CRITICAL/HIGH/MEDIUM/LOW)
     ▼
 wazuh_alert_enrichment row (one per alert, explainable evidence stored)
```

All correlation/EPSS/KEV/actor links reuse the existing CTI tables — no data is
re-derived. Every enrichment stores the evidence and a human-readable rationale.
~~~~

- **Raw Wazuh event stored as JSON (code)** — `collectors/wazuh.py` L174

~~~~text
        "raw_event": src,
~~~~

- **raw_event column (code)** — `backend/app/models/wazuh.py` L56

~~~~text
    raw_event: Mapped[dict | None] = mapped_column(JSON, nullable=True)
~~~~

- **Enrichment evidence JSON (model docstring)** — `backend/app/models/wazuh.py` L67-L73

~~~~text
class WazuhAlertEnrichment(Base):
    """CTI enrichment + SOC priority for one alert.

    The single-value FK columns (technique_id, cve_id, threat_actor_id, ...)
    record the top-signal entity for quick filtering; the full multi-entity
    graph and how each link was derived live in the `evidence` JSON.
    """
~~~~

- **Enrichment evidence payload keys (code)** — `backend/app/wazuh_enrichment/engine.py` L194-L204

~~~~text
    evidence = {
        "techniques": techniques,
        "cves": cve_rows[:MAX_CVE_EVIDENCE],
        "cve_count": len(cve_rows),
        "threat_actors": sorted(actors),
        "malware": sorted(malware),
        "campaigns": sorted(campaigns),
        "signals": signals,
        "priority_components": prio["components"],
        "rationale": prio["rationale"],
    }
~~~~

- **Agent investigations persisted with evidence** — `docs/agentic_soc.md` L3-L6

~~~~text
Turns the AI Threat Analyst into an autonomous agent that **investigates,
correlates, prioritizes, explains, and recommends** by chaining existing
platform services as vetted tools. Every investigation is evidence-driven and
fully auditable (plan + tool-call log + evidence + report persisted).
~~~~

- **Agent memory trims raw evidence to summaries (code) — nuance** — `backend/app/agents/memory.py` L1-L5

~~~~text
"""Investigation memory (Phase 14.11).

Persists each investigation (plan, tool-call log, trimmed evidence, full report)
and supports history, lineage (continue), and comparison. Heavy raw evidence is
trimmed to summaries on save - the full structured findings live in the report.
~~~~

- **AI answers: nothing outside gathered evidence asserted** — `docs/ai_analyst.md` L76-L82

~~~~text
## Evidence generation & explainability (13.7)

Every answer includes: `answer`, `risk_justification`, `supporting_entities`,
`graph_relationships`, `findings` (structured), `confidence` (0–1, scaled by
entity resolution + evidence volume), `data_sources`, and `generator`
(`deterministic` or the provider name). Nothing outside the gathered evidence is
ever asserted.
~~~~

- **PostgreSQL is the system of record; graph is a rebuildable projection** — `docs/graph_schema.md` L3-L5

~~~~text
A live Neo4j property graph projected from PostgreSQL (the system of record).
The graph is rebuildable at any time via the sync engine; PostgreSQL remains
authoritative.
~~~~

- **Response recommendation evidence field (code)** — `backend/app/response_engine.py` L83-L89

~~~~text
        row = ResponseRecommendation(
            source_type="investigation", source_id=str(inv.id), action_type=action_type,
            title=title, description=rec.get("detail", ""), severity=level,
            rationale=f"Derived from agent evidence: {rec.get('evidence', 'n/a')}",
            evidence={"evidence_tool": rec.get("evidence"), "target": inv.target,
                      "investigation_id": inv.id},
            confidence=inv.confidence or 0.0, status=PENDING, created_at=_now())
~~~~


**NOT FOUND IN DOCS (EVIDENCE):** the phrases **"evidence-first"** and **"evidence tags"**. Both are absent from every file in the repo, so do not use them as quotes, and do not describe "evidence tags" as a feature. Also absent: chain-of-custody, hashing or signing of evidence, immutable, WORM or tamper-proof storage, forensic artifact collection (memory or disk images), and PCAP. Note that agent memory keeps trimmed summaries of raw tool evidence, not the full raw output (quote above).

---

## 3. CORRELATION — rule-based ATT&CK <-> CVE linking

### Supported facts

- **Method, noisy-OR, thresholds, evidence, no LLMs** — `README.md` L213-L230

~~~~text
### Generating ATT&CK ↔ CVE correlations

After ATT&CK techniques and CVEs are ingested, run the correlation engine to
link them. It is deterministic and idempotent (re-runs upsert):

```powershell
python -m collectors.correlate
```

**How it works.** A versioned rule base (`backend/app/correlation/rules.py`)
maps high-signal exploitation phrases (e.g. "sql injection", "privilege
escalation", "ransomware") to specific ATT&CK techniques and tactics, each with
a base weight. For every CVE description the engine finds matching phrases
(whole-word, plural-aware), and when several rules point at the same technique
their weights combine via noisy-OR (`1 − Π(1 − wᵢ)`). The result is bucketed
HIGH ≥ 0.7 / MEDIUM ≥ 0.4 / LOW, and the matched phrases are stored as evidence
so every link is explainable. No LLMs or paid services are involved; the design
is built to be swapped for an ML/graph model later without a schema change.
~~~~

- **Rule base docstring (code)** — `backend/app/correlation/rules.py` L1-L16

~~~~text
"""Rule base for ATT&CK <-> CVE correlation.

Each rule maps a set of high-signal exploitation-vector phrases to a single
ATT&CK technique, its tactic, and a base weight (how strongly the phrase
implies the technique). The rules are intentionally conservative - we favor
precision over recall, so a correlation is only emitted when a recognized
exploitation vector appears in the CVE description.

Weights are the per-rule probability that the match is meaningful. When more
than one rule fires for the same technique on the same CVE, the engine combines
their weights with a noisy-OR (see engine.combine_weights), so independent
signals reinforce each other without ever exceeding 1.0.

This rule base is versioned in code (not the database) so it is reviewable in
git and can be replaced by an ML/graph model in a later phase without touching
the schema.
~~~~

- **Example rule with weight (code)** — `backend/app/correlation/rules.py` L35-L40

~~~~text
    CorrelationRule(
        "T1190", "Initial Access", 0.7,
        ("sql injection", "sqli", "deserialization", "xml external entity",
         "xxe", "server-side request forgery", "ssrf", "local file inclusion",
         "remote file inclusion", "lfi", "rfi"),
        "Exploitation of a public-facing application weakness",
~~~~

- **Scoring methodology docstring (code)** — `backend/app/correlation/engine.py` L3-L15

~~~~text
Scoring methodology (deterministic + explainable)
-------------------------------------------------
1. For each CVE description, every rule whose phrases appear (as whole words)
   contributes its weight to the technique it maps to.
2. When several rules point at the same technique, their weights combine with a
   noisy-OR: ``score = 1 - Π(1 - wᵢ)``. Independent signals reinforce each
   other and the result stays in [0, 1].
3. The score is bucketed: HIGH ≥ 0.7, MEDIUM ≥ 0.4, otherwise LOW.
4. The matched phrases are stored verbatim as the evidence for the link, so
   every correlation is auditable.

Everything here is pure and deterministic - the same inputs always yield the
same correlations, which is what makes the engine testable and explainable.
~~~~

- **Method id + exact thresholds (code)** — `backend/app/correlation/engine.py` L26-L29

~~~~text
METHOD = "rule-based-keyword-v1"

HIGH_THRESHOLD = 0.7
MEDIUM_THRESHOLD = 0.4
~~~~

- **noisy-OR implementation (code)** — `backend/app/correlation/engine.py` L52-L65

~~~~text
def combine_weights(weights: Iterable[float]) -> float:
    """Noisy-OR combination of independent rule weights."""
    product = 1.0
    for w in weights:
        product *= (1.0 - w)
    return round(1.0 - product, 3)


def confidence_level(score: float) -> str:
    if score >= HIGH_THRESHOLD:
        return "HIGH"
    if score >= MEDIUM_THRESHOLD:
        return "MEDIUM"
    return "LOW"
~~~~

- **WORKED EXAMPLE (unit test, synthetic weights)** — `tests/test_correlations.py` L102-L111

~~~~text
def test_combine_weights_noisy_or():
    assert combine_weights([0.7]) == 0.7
    # 1 - (1-0.7)(1-0.5) = 1 - 0.15 = 0.85
    assert combine_weights([0.7, 0.5]) == 0.85


def test_confidence_level_buckets():
    assert confidence_level(0.85) == "HIGH"
    assert confidence_level(0.5) == "MEDIUM"
    assert confidence_level(0.3) == "LOW"
~~~~

- **Worked matching example (unit test)** — `tests/test_correlations.py` L114-L124

~~~~text
def test_correlate_description_matches_sqli():
    matches = correlate_description("SQL injection allows remote code execution")
    techniques = {m["technique_id"] for m in matches}
    assert "T1190" in techniques  # sql injection
    assert "T1203" in techniques  # remote code execution


def test_correlate_description_word_boundary():
    # "dos" must not match inside "Windows".
    matches = correlate_description("An issue affecting Windows endpoints.")
    assert all(m["technique_id"] != "T1499" for m in matches)
~~~~

- **Test CVE text mapping to 3 techniques (unit test)** — `tests/test_correlations.py` L179-L185

~~~~text
def test_correlations_for_cve():
    resp = client.get("/correlations/cve/CVE-2024-1000")
    assert resp.status_code == 200
    body = resp.json()
    techniques = {c["technique_id"] for c in body}
    # This CVE mentions SQLi, arbitrary commands, and privilege escalation.
    assert {"T1190", "T1059", "T1068"} <= techniques
~~~~

- **Roadmap line** — `README.md` L508

~~~~text
- **Phase 4 (done):** rule-based ATT&CK↔CVE correlation engine (confidence scoring, evidence), correlation endpoints + stats
~~~~


Derived from code (my count, not stated in the docs): `RULES` in `backend/app/correlation/rules.py` holds **19 rules**, and each maps to a **different** technique_id. With the rule base as shipped, a technique therefore only ever receives one weight, so the noisy-OR combination of 2+ weights happens only in the unit test. Rule weights range from 0.4 to 0.8, so with these rules the LOW bucket (< 0.4) is never produced. The website can show the formula and the unit-test example (0.7 and 0.5 give 0.85), labeled as the scoring method. It must not claim that real CVEs routinely combine multiple rules.

**NOT FOUND IN DOCS (CORRELATION):** ML, NLP, embedding or LLM-based correlation. It is keyword and regex rules, "built to be swapped for an ML/graph model later". Also absent: a stated total number of correlations, and precision or recall figures. The only scale figures are in the old Phase-7 design doc (`docs/neo4j_design.md` L126-127: "≈700 techniques + 2,600 CVEs + ≈1,500 edges") and `n_samples: 1291` correlated CVEs in the ML metrics files (see RISK).

---

## 4. RISK — ML risk model (V1-V6), weak supervision, priority engine

### 4a. Weak supervision and "high by construction"

- **Commands** — `README.md` L256-L265

~~~~text
### ML threat risk scoring (Phase 5)

After correlations exist, train the model and score CVEs:

```powershell
python -m ml.train        # build features, train XGBoost, persist model + metrics
python -m ml.inference    # score all correlated CVEs into the risk_scores table
python -m ml.evaluation   # held-out metrics + score/level distribution
python -m ml.explainability   # global feature importance + an example explanation
```
~~~~

- **Weak-supervision methodology** — `README.md` L267-L275

~~~~text
**Methodology — weak supervision (documented assumption).** The platform has no
observed ground truth for "risk" (no exploitation outcomes, no analyst labels).
Supervised learning on real labels is therefore not possible today. Instead we
derive a transparent **heuristic label** (a weighted blend of CVSS, correlation
confidence, ATT&CK breadth, technique centrality, and recency) and train a model
(XGBoost preferred, RandomForest fallback) to learn it. This produces a smooth,
explainable 0–100 score and — importantly — a serving pipeline whose labels can
later be replaced by real signals (**CISA KEV** known-exploited, **FIRST EPSS**
exploit probability) without changing the model or the API.
~~~~

- **Limitation — 'high by construction' + ML risk-level thresholds** — `README.md` L277-L281

~~~~text
**Limitation.** Because the label is a function of the same features, held-out
regression metrics are high by construction (they confirm the model faithfully
learns the target, *not* that it predicts real-world exploitation). Treat the
score as a transparent prioritization aid, not a validated probability. Risk
levels: CRITICAL ≥ 75, HIGH ≥ 50, MEDIUM ≥ 25, LOW < 25.
~~~~

- **Weak supervision rationale (code docstring)** — `ml/feature_engineering.py` L1-L15

~~~~text
"""Feature engineering for the threat risk-scoring model.

Builds one feature row per *correlated* CVE (a CVE with at least one ATT&CK
correlation) from data already in PostgreSQL, and provides the weak-supervision
label used to train the model (see compute_weak_labels).

Why weak supervision? The platform has no observed ground truth for "risk"
(no exploitation outcomes, no analyst-assigned scores). We therefore derive a
transparent heuristic label from domain knowledge and train a model to learn
it. This bootstraps a smooth, explainable score and — critically — produces a
serving pipeline whose labels can later be replaced by real signals (CISA KEV
"known exploited", FIRST EPSS exploit-probability) without changing the model
or the API. Assumptions and limitations are documented in the README and the
final report.
"""
~~~~

- **V1 heuristic label formula (code)** — `ml/feature_engineering.py` L223-L247

~~~~text
def compute_weak_labels(df: pd.DataFrame) -> pd.Series:
    """Heuristic weak-supervision target in [0, 100].

    Weighted blend of severity (CVSS), correlation strength, ATT&CK breadth,
    technique centrality, and recency, with small bumps for critical/high-
    confidence flags. CVSS dominates because it is the most established signal.
    """
    cvss_n = (df["cvss_score"] / 10.0).clip(0, 1)
    conf_n = df["max_confidence"].clip(0, 1)
    map_n = (df["num_mappings"].clip(upper=6) / 6.0)
    pop_n = df["technique_popularity"].clip(0, 1)

    age = df["published_age_days"].clip(lower=0)
    max_age = age.max() if age.max() and age.max() > 0 else 1
    recency_n = 1 - (age / max_age)

    label = 100 * (
        0.50 * cvss_n
        + 0.20 * conf_n
        + 0.15 * map_n
        + 0.10 * pop_n
        + 0.05 * recency_n
    )
    label = label + 3 * df["is_critical"] + 2 * df["is_high_confidence"]
    return label.clip(0, 100)
~~~~

- **Model factory: XGBoost preferred, RandomForest fallback (code)** — `ml/risk_model.py` L1-L6

~~~~text
"""Model factory, persistence, and risk-level mapping for the scoring engine.

Prefers XGBoost; falls back to scikit-learn's RandomForest if XGBoost is not
available. Both expose ``feature_importances_`` and a uniform fit/predict API,
so the rest of the pipeline is model-agnostic.
"""
~~~~

- **ML risk-level thresholds (code)** — `ml/risk_model.py` L19-L25

~~~~text
# Risk-level thresholds on the 0-100 score.
RISK_THRESHOLDS = (
    ("CRITICAL", 75.0),
    ("HIGH", 50.0),
    ("MEDIUM", 25.0),
    ("LOW", 0.0),
)
~~~~

- **Train/test split: 80/20 held-out (code)** — `ml/train.py` L81-L85

~~~~text
    y = label_fn(df)
    X = df[feature_columns]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE
    )
~~~~

- **Explainability: no SHAP (code docstring)** — `ml/explainability.py` L1-L12

~~~~text
"""Explainability for the risk model.

Two complementary views, both dependency-light (no SHAP required):

* Global  - model ``feature_importances_`` plus permutation importance
            (scikit-learn), which is model-agnostic and less biased toward
            high-cardinality features.
* Local   - per-CVE contribution estimate: a feature's standardized deviation
            from the corpus mean, weighted by its global importance. This gives
            an explainable "why is this CVE risky" breakdown without SHAP, and
            can be upgraded to SHAP later without changing callers.
"""
~~~~


### 4b. Versions V1 -> V6 and what each adds

- **V2 (EPSS + KEV) — KEV anchored >= 90** — `README.md` L283-L293

~~~~text
**Risk Scoring V2 (EPSS + KEV enriched).** `python -m ml.train` now trains a V2
model by default: it adds four intelligence features (EPSS score, EPSS
percentile, KEV present, KEV age) and enriches the weak-supervision label with
those real-world exploitation signals (KEV-listed CVEs are anchored ≥ 90).
Train V1 for comparison with `python -m ml.train --version v1`; both are
archived (`ml/models/risk_model_<version>.joblib`). Inference and explainability
are version-agnostic — they read the active model's own feature columns from its
metadata. The V1→V2 feature-importance shift is dramatic: V1 is CVSS/severity
dominated, while V2's top features become `kev_age_days`, `kev_present`, and
EPSS — i.e. the model leans on confirmed/likely exploitation instead of raw
severity.
~~~~

- **V2 label: KEV override (code)** — `ml/feature_engineering.py` L589-L619

~~~~text
def compute_weak_labels_v2(df: pd.DataFrame) -> pd.Series:
    """V2 weak-supervision target enriched with real-world exploitation signal.

    Modeling choice: V1's label was CVSS-dominated and used no exploitation
    evidence. V2 folds in EPSS (a calibrated exploit-probability) and CISA KEV
    (ground truth that a CVE *is* being exploited). KEV-listed CVEs are anchored
    to >= 90 because confirmed in-the-wild exploitation is the strongest signal
    of real risk. The model then learns this target from features that include
    EPSS/KEV, so their importance rises sharply versus V1.
    """
    cvss_n = (df["cvss_score"] / 10.0).clip(0, 1)
    epss_n = _opt(df, "epss_score").clip(0, 1)
    pct_n = _opt(df, "epss_percentile").clip(0, 1)
    conf_n = df["max_confidence"].clip(0, 1)
    map_n = (df["num_mappings"].clip(upper=6) / 6.0)
    pop_n = df["technique_popularity"].clip(0, 1)

    label = 100 * (
        0.30 * cvss_n
        + 0.30 * epss_n
        + 0.10 * pct_n
        + 0.10 * conf_n
        + 0.10 * map_n
        + 0.10 * pop_n
    )
    label = label + 3 * df["is_critical"] + 2 * df["is_high_confidence"]

    # KEV override: confirmed exploited in the wild -> anchor high.
    kev = _opt(df, "kev_present")
    label = label.where(kev == 0, other=label.clip(lower=90))
    return label.clip(0, 100)
~~~~

- **V3 (MISP actor attribution)** — `README.md` L342-L348

~~~~text
**Risk Scoring V3.** `python -m ml.train` now defaults to V3, adding MISP
actor-attribution features (`misp_actor_linked`, `misp_actor_count`,
`misp_max_actor_conf`) and a label bump for actor-attributed CVEs. Impact: the
top risk feature shifts from `cvss_score` (V1) → `kev_age_days` (V2) →
`misp_actor_linked` (V3) — the model increasingly leans on real-world
exploitation evidence over static severity. Train older versions with
`--version v1|v2|v3` for comparison.
~~~~

- **V4 (live Wazuh telemetry)** — `README.md` L368-L372

~~~~text
**Risk Scoring V4.** `python -m ml.train` defaults to V4, adding live Wazuh
telemetry features (`wazuh_observed`, `wazuh_alert_count`, `wazuh_max_level`):
CVEs whose techniques are firing as alerts in the monitored estate are
escalated. The Wazuh features rank among the top signals, confirming SOC
telemetry improves risk scoring.
~~~~

- **V5 (graph topology / GDS)** — `README.md` L400-L406

~~~~text
python -m ml.train --version v5             # ML Risk Scoring V5 (graph features); then: python -m ml.inference
```

GDS metrics are cached in `graph_metrics` and insights in `graph_insights`, so the
`/graph/*` analytics APIs and ML V5 read from PostgreSQL (no live Neo4j needed at
inference). V5 adds 11 graph features; `cve_degree` and `connected_entities` become
the top risk drivers. See [docs/graph_analytics.md](docs/graph_analytics.md).
~~~~

- **V5 feature + label diagram** — `docs/graph_analytics.md` L62-L76

~~~~text
## V5 feature-engineering diagram

```
 build_features_v5  =  V4 features (34)  +  GRAPH_COLUMNS (11)
   ┌─ from graph_metrics ──────────────┐   ┌─ from relationship tables ─────────┐
   │ cve_pagerank, cve_degree,         │   │ ta_pagerank/ta_degree (attributed   │
   │ technique_degree, community_risk, │   │   actors), related_campaigns,       │
   │ connected_entities                │   │   related_malware, related_alerts,  │
   └───────────────────────────────────┘   │   shortest_path_to_alert            │
                                            └─────────────────────────────────────┘
 label_v5 = label_v4 + 8·pagerank_n + 6·community_risk + 4·actor_pagerank_n   (clip 0-100)
```

Graph features are read from the persisted `graph_metrics` table, so training and
inference need **no live Neo4j connection** — the graph is computed once and reused.
~~~~

- **Model comparison V1->V5** — `docs/graph_analytics.md` L78-L90

~~~~text
## Model comparison (V1 → V5), top feature by version

| Version | New signal added | #1 feature |
|---|---|---|
| V1 | CVE + correlation + ATT&CK | `cvss_score` |
| V2 | EPSS + CISA KEV | `kev_age_days` |
| V3 | MISP actor attribution | `misp_actor_linked` |
| V4 | live Wazuh telemetry | `misp_actor_linked` (Wazuh #3/#5/#6) |
| V5 | **graph topology (GDS)** | **`cve_degree`** (graph degree), `connected_entities` #2 |

V5's risk now leans hardest on **graph topology** — `cve_degree` (0.39) and
`connected_entities` (0.29) are the top two features, with actor/KEV/Wazuh signals
following. This is the intended shift from static CVSS/EPSS to graph-aware risk.
~~~~

- **V6 (predictive: embeddings + link prediction) + model evolution table** — `docs/phases_15_17.md` L32-L44

~~~~text
   ML Risk Scoring V6 features: node_embedding_norm, predicted_link_count,
     predicted_actor_exposure, community_influence, graph_similarity
```
APIs: `GET /predictions`, `/predictions/actors|cves|campaigns|paths`.

### Model evolution (top risk feature by version)

| V1 | V2 | V3 | V4 | V5 | V6 |
|----|----|----|----|----|----|
| cvss_score | kev_age_days | misp_actor_linked | misp_actor_linked | cve_degree | cve_degree (graph_similarity + community_influence added) |

V6 layers predictive-intelligence features on the graph-topology model; risk is
driven by graph centrality + similarity + predicted exposure, not static CVSS.
~~~~

- **Feature column groups per version (code)** — `ml/feature_engineering.py` L24-L95

~~~~text
# The numeric features fed to the model, in a fixed order (reproducibility).
FEATURE_COLUMNS = [
    # CVE features
    "cvss_score",
    "severity_ordinal",
    "published_age_days",
    "description_length",
    # Correlation features
    "max_confidence",
    "avg_confidence",
    "num_mappings",
    "num_high_confidence",
    # ATT&CK features
    "distinct_tactics",
    "technique_popularity",
    # Derived features
    "is_critical",
    "is_high_confidence",
    "correlation_density",
]

# V2 adds real-world exploitation intelligence (EPSS + CISA KEV) on top of V1.
INTEL_COLUMNS = [
    "epss_score",       # FIRST EPSS exploit probability (0-1)
    "epss_percentile",  # EPSS percentile rank (0-1)
    "kev_present",      # 1 if listed in CISA KEV (confirmed exploited)
    "kev_age_days",     # days since KEV listing (0 if not listed)
]
FEATURE_COLUMNS_V2 = FEATURE_COLUMNS + INTEL_COLUMNS

# V3 adds MISP threat-intelligence context (actor attribution) per CVE.
MISP_COLUMNS = [
    "misp_actor_linked",    # 1 if a tracked threat actor exploits this CVE
    "misp_actor_count",     # number of distinct actors linked
    "misp_max_actor_conf",  # strongest actor->cve enrichment confidence
]
FEATURE_COLUMNS_V3 = FEATURE_COLUMNS_V2 + MISP_COLUMNS

# V4 adds live Wazuh SOC telemetry: is this CVE actively matching detections in
# the monitored environment? (CVE <- correlated technique <- Wazuh alert)
WAZUH_COLUMNS = [
    "wazuh_observed",     # 1 if any Wazuh alert technique correlates to this CVE
    "wazuh_alert_count",  # number of such alerts
    "wazuh_max_level",    # max Wazuh rule_level among them (0-15)
]
FEATURE_COLUMNS_V4 = FEATURE_COLUMNS_V3 + WAZUH_COLUMNS

# V5 adds Neo4j graph-topology intelligence (GDS centrality, community, reach).
GRAPH_COLUMNS = [
    "cve_pagerank",            # GDS PageRank of the CVE node
    "cve_degree",              # GDS degree centrality of the CVE
    "ta_pagerank",             # max PageRank of attributed threat actors
    "ta_degree",               # max degree of attributed threat actors
    "technique_degree",        # max degree of correlated techniques
    "community_risk",          # KEV/critical fraction of the CVE's community
    "connected_entities",      # graph neighbours of the CVE
    "related_alerts",          # Wazuh alerts reaching this CVE
    "related_campaigns",       # campaigns reachable via attributed actors
    "related_malware",         # malware families reachable via attributed actors
    "shortest_path_to_alert",  # graph distance to nearest active alert (0 = none)
]
FEATURE_COLUMNS_V5 = FEATURE_COLUMNS_V4 + GRAPH_COLUMNS

# V6 adds predictive-intelligence signals: graph embeddings + link prediction.
PRED_COLUMNS = [
    "node_embedding_norm",       # L2 norm of the CVE's graph embedding (0 if none)
    "predicted_link_count",      # predicted future relationships targeting the CVE
    "predicted_actor_exposure",  # max confidence a tracked actor will target the CVE
    "community_influence",       # relative size of the CVE's graph community
    "graph_similarity",          # GDS node-similarity score of the CVE
]
FEATURE_COLUMNS_V6 = FEATURE_COLUMNS_V5 + PRED_COLUMNS
~~~~

- **Default training version is v6 in code** — `ml/train.py` L68

~~~~text
    parser.add_argument("--version", choices=["v1", "v2", "v3", "v4", "v5", "v6"], default="v6")
~~~~


Feature counts per version (counted from `ml/feature_engineering.py` and matching `feature_columns` length in `ml/models/metrics_v*.json`): **V1 13, V2 17, V3 20, V4 23, V5 34, V6 39.**

### 4c. Recorded training metrics (from the committed metrics files)

All six versions record `"algorithm": "xgboost"` and `"n_samples": 1291`. The R² values below are held-out regression fit against the heuristic label. They are **not** accuracy at predicting exploitation (see the "high by construction" quote above).

- **V1 metrics block** — `ml/models/metrics_v1.json` L22-L26

~~~~text
  "metrics": {
    "r2": 0.9986,
    "mae": 0.1318,
    "rmse": 0.3393
  },
~~~~

- **V1 top feature** — `ml/models/metrics_v1.json` L27-L31

~~~~text
  "feature_importances": [
    {
      "feature": "cvss_score",
      "importance": 0.3771
    },
~~~~

- **V2 metrics block** — `ml/models/metrics_v2.json` L26-L30

~~~~text
  "metrics": {
    "r2": 0.9964,
    "mae": 0.2306,
    "rmse": 0.4366
  },
~~~~

- **V2 top feature** — `ml/models/metrics_v2.json` L31-L35

~~~~text
  "feature_importances": [
    {
      "feature": "kev_age_days",
      "importance": 0.5406
    },
~~~~

- **V3 metrics block** — `ml/models/metrics_v3.json` L29-L33

~~~~text
  "metrics": {
    "r2": 0.9975,
    "mae": 0.2316,
    "rmse": 0.4209
  },
~~~~

- **V3 top feature** — `ml/models/metrics_v3.json` L34-L38

~~~~text
  "feature_importances": [
    {
      "feature": "misp_actor_linked",
      "importance": 0.5772
    },
~~~~

- **V4 metrics block** — `ml/models/metrics_v4.json` L32-L36

~~~~text
  "metrics": {
    "r2": 0.9908,
    "mae": 0.2961,
    "rmse": 0.8242
  },
~~~~

- **V4 top feature** — `ml/models/metrics_v4.json` L37-L41

~~~~text
  "feature_importances": [
    {
      "feature": "misp_actor_linked",
      "importance": 0.1658
    },
~~~~

- **V5 metrics block** — `ml/models/metrics_v5.json` L43-L47

~~~~text
  "metrics": {
    "r2": 0.9878,
    "mae": 0.3637,
    "rmse": 1.0469
  },
~~~~

- **V5 top feature** — `ml/models/metrics_v5.json` L48-L52

~~~~text
  "feature_importances": [
    {
      "feature": "cve_degree",
      "importance": 0.3907
    },
~~~~

- **V6 metrics block** — `ml/models/metrics_v6.json` L48-L52

~~~~text
  "metrics": {
    "r2": 0.9792,
    "mae": 0.4339,
    "rmse": 1.4227
  },
~~~~

- **V6 top feature** — `ml/models/metrics_v6.json` L53-L57

~~~~text
  "feature_importances": [
    {
      "feature": "cve_degree",
      "importance": 0.6953
    },
~~~~

- **V1 level distribution (source of README's ~1,090 HIGH)** — `ml/models/metrics_v1.json` L88-L93

~~~~text
  "level_distribution": {
    "CRITICAL": 88,
    "HIGH": 1089,
    "MEDIUM": 114,
    "LOW": 0
  }
~~~~


### 4d. Threat Priority Engine v2 (per-CVE): exact weights and KEV override

- **README methodology** — `README.md` L306-L318

~~~~text
**Priority methodology (deterministic + explainable).** The five predictive
signals are a weighted blend (CVSS 0.20, correlation confidence 0.15, ML risk
0.15, **EPSS 0.30**, ATT&CK strength 0.20 → 0–100). **CISA KEV** is applied as a
real-world override on top — a KEV listing means *confirmed exploited in the
wild*, so the score is floored to ≥ 75 and boosted. EPSS carries the largest
predictive weight because it is the best estimate of exploit likelihood. Each
score stores its per-signal point breakdown and a plain-English explanation
(`/priority/{cve_id}/explanation`). Levels: CRITICAL ≥ 75, HIGH ≥ 50,
MEDIUM ≥ 25, LOW < 25.

This is the catalog→prioritization shift: ML risk flagged ~1,090 CVEs as HIGH,
but EPSS+KEV narrow *true* urgency to a few dozen — separating "severe" from
"actually likely to be exploited."
~~~~

- **Formula docstring (code)** — `backend/app/prioritization/engine.py` L3-L19

~~~~text
Methodology (deterministic + explainable)
-----------------------------------------
Each CVE's priority blends six normalized signals. The five model/intel signals
are a weighted sum (weights sum to 1.0); CISA KEV is applied as a real-world
override on top, because a KEV listing means the vulnerability is *confirmed
exploited in the wild* and CISA mandates remediation:

    base   = 100 * ( 0.20*cvss + 0.15*correlation + 0.15*ml
                     + 0.30*epss + 0.20*attack )
    final  = base, unless KEV → final = min(100, max(base, 75) + 15)

EPSS carries the largest weight among the predictive signals because it is the
best available estimate of real-world exploit likelihood. The per-component
point contributions are stored so any score can be explained exactly.

Levels: CRITICAL ≥ 75, HIGH ≥ 50, MEDIUM ≥ 25, LOW < 25 (consistent with the
ML risk levels, enabling an apples-to-apples old-vs-new comparison).
~~~~

- **Exact weights + KEV constants (code)** — `backend/app/prioritization/engine.py` L28-L39

~~~~text
METHOD = "priority-v2"

WEIGHTS = {
    "cvss": 0.20,
    "correlation": 0.15,
    "ml": 0.15,
    "epss": 0.30,
    "attack": 0.20,
}

KEV_FLOOR = 75.0
KEV_BOOST = 15.0
~~~~

- **KEV override implementation (code)** — `backend/app/prioritization/engine.py` L76-L82

~~~~text
    if kev:
        final = min(100.0, max(base, KEV_FLOOR) + KEV_BOOST)
        comp_kev = round(final - base, 2)
    else:
        final = base
        comp_kev = 0.0
    final = round(min(final, 100.0), 2)
~~~~


Arithmetic note (derived from the formula, not stated in the docs): because `final = min(100, max(base, 75) + 15)`, a KEV-listed CVE always ends at **>= 90**. The README's "floored to ≥ 75 and boosted" describes the same thing. Do not write "KEV floor = 75" as if 75 were the final value.

### 4e. SOC Priority (per Wazuh alert) — a DIFFERENT formula from 4d

- **SOC priority methodology** — `docs/wazuh_soc_architecture.md` L57-L73

~~~~text
## SOC Priority methodology

Wazuh severity (`rule_level`, 0-15) is preserved verbatim. The SOC priority is a
*separate* 0-100 score:

```
base = 100 * ( 0.25 * wazuh_severity     (rule_level / 15)
             + 0.20 * existing_risk       (max ML risk of related CVEs / 100)
             + 0.20 * epss                (max EPSS of related CVEs)
             + 0.15 * cve_breadth         (min(#related_cves, 5) / 5)
             + 0.10 * technique_breadth   (min(#techniques, 5) / 5)
             + 0.10 * actor_present )
```

CISA KEV override: if any related CVE is KEV-listed, `final = min(100, max(base,75)+15)`
— confirmed in-the-wild exploitation against a monitored asset is the strongest
escalation. Levels: CRITICAL ≥ 75, HIGH ≥ 50, MEDIUM ≥ 25, LOW < 25.
~~~~

- **SOC priority components (code)** — `backend/app/wazuh_enrichment/engine.py` L52-L67

~~~~text
    comp = {
        "wazuh_severity": round(0.25 * sev_n * 100, 2),
        "existing_risk": round(0.20 * risk_n * 100, 2),
        "epss": round(0.20 * epss_n * 100, 2),
        "cve_breadth": round(0.15 * cve_n * 100, 2),
        "technique_breadth": round(0.10 * tech_n * 100, 2),
        "actor_present": round(0.10 * actor * 100, 2),
    }
    base = sum(comp.values())
    if kev:
        final = min(100.0, max(base, KEV_FLOOR) + KEV_BOOST)
        comp["kev_override"] = round(final - base, 2)
    else:
        final = base
        comp["kev_override"] = 0.0
    final = round(min(final, 100.0), 2)
~~~~


**NOT FOUND IN DOCS (RISK):** validated accuracy, precision, recall or AUC against real exploitation; any claim that the model "predicts exploitation" (the docs explicitly deny this); supervised or ground-truth labels (listed under **Future**: "fully-supervised risk labels (KEV/EPSS ground truth)"); SHAP (code says "no SHAP required"); deep learning or neural nets (XGBoost or RandomForest only). Do not merge the CVE Priority Engine weights (0.20/0.15/0.15/0.30/0.20) with the alert SOC-priority weights (0.25/0.20/0.20/0.15/0.10/0.10). They are two separate engines.

---

## 5. INVESTIGATION — Neo4j graph, GDS analytics, blast radius, link prediction

### Supported facts

- **Neo4j in Docker + sync + investigation workflows** — `README.md` L374-L389

~~~~text
### Neo4j knowledge graph (Phase 11)

Neo4j runs as a Docker service (`docker compose up -d neo4j`; Browser at
http://localhost:7474, Bolt on 7687). Project the PostgreSQL data into the graph:

```powershell
python -m backend.app.graph.graph_sync            # full, idempotent sync
python -m backend.app.graph.graph_sync --since 2026-06-01   # incremental (alerts/risk)
```

The sync is MERGE-based and batched; PostgreSQL stays the system of record and
the graph is rebuildable at any time. Investigation workflows (alert → technique
→ CVE → actor → malware/campaign, actor ecosystems, CVE relationships, shortest
path) are exposed via `/graph/*` and the 5 graph dashboard pages. Credentials
come from `NEO4J_URI`/`NEO4J_USERNAME`/`NEO4J_PASSWORD`. See
[docs/graph_schema.md](docs/graph_schema.md) for the schema and diagrams.
~~~~

- **Graph schema intro** — `docs/graph_schema.md` L3-L5

~~~~text
A live Neo4j property graph projected from PostgreSQL (the system of record).
The graph is rebuildable at any time via the sync engine; PostgreSQL remains
authoritative.
~~~~

- **Node table + relationships** — `docs/graph_schema.md` L54-L68

~~~~text
| Node | Key (from PostgreSQL) | Properties |
|---|---|---|
| `:Technique` | `technique_id` | name |
| `:CVE` | `cve_id` | cvss_score, severity |
| `:ThreatActor` | `actor_id` | name |
| `:Malware` | `malware_id` | name |
| `:Campaign` | `campaign_id` | name |
| `:IOC` | `ioc_id` | type, value |
| `:Agent` | `agent_id` | name, ip, status |
| `:Alert` | `alert_id` | wazuh_alert_id, rule_level, description |
| `:RiskScore` | `key` (`cve:<id>` / `alert:<id>`) | score, level, kind |

Relationships: `OBSERVED_ON`, `USES_TECHNIQUE`, `CORRELATED_TO` (confidence),
`ATTRIBUTED_TO` (confidence), `USES`, `RUNS`, `USES_IOC`, `HAS_RISK`,
`PRIORITIZED_AS`. Each node label has a uniqueness constraint on its key.
~~~~

- **Investigation workflow diagram** — `docs/graph_schema.md` L70-L86

~~~~text
## Graph investigation workflow diagram

```
 ALERT INVESTIGATION        THREAT-ACTOR INVESTIGATION      VULNERABILITY INVESTIGATION
 ─────────────────────      ──────────────────────────      ───────────────────────────
   Alert                      ThreatActor                      CVE
    └▶ Technique               ├▶ Malware                       ├▶ Technique
        └▶ CVE                 ├▶ Campaign                      │   └▶ Alert (observed)
            └▶ ThreatActor     └▶ CVE                           └▶ ThreatActor
                ├▶ Malware          └▶ Alert (observed)
                └▶ Campaign
   GET /graph/alert/{id}      GET /graph/actor/{id}            GET /graph/cve/{id}
```

Each workflow is one API call returning a visualization-ready subgraph
(`{nodes, edges, summary}`). `GET /graph/path` finds the shortest path between
any two entities (e.g. an alert and a threat actor).
~~~~

- **Performance notes (scale, APT28 degree)** — `docs/graph_schema.md` L101-L110

~~~~text
## Performance notes

- Uniqueness constraints (one per label) back-index every MERGE key, so sync and
  lookups are O(log n) rather than scans.
- Sync uses batched `UNWIND $rows` writes (1,000 rows/tx) — the full projection
  (~5k nodes, ~4k relationships) syncs in a few seconds.
- Investigation queries are bounded (`LIMIT`/`cap`) because hub nodes are dense
  (e.g. APT28 has graph degree ~620); the dashboard further caps rendered nodes.
- The graph fits comfortably in memory at current scale; a single Neo4j
  community instance is sufficient for the foreseeable roadmap.
~~~~

- **GDS analytics intro** — `docs/graph_analytics.md` L3-L6

~~~~text
Turns the Neo4j knowledge graph into measurable intelligence (GDS centrality,
communities, attack paths) and feeds graph-derived features into **ML Risk
Scoring V5**. Everything is computed from the real graph; results are cached in
PostgreSQL (`graph_metrics`, `graph_insights`) for reuse by APIs and ML.
~~~~

- **Graph size + GDS version** — `docs/graph_analytics.md` L11-L16

~~~~text
   Neo4j graph (real data)              backend/app/graph/                PostgreSQL cache
 ┌──────────────────────────┐   ┌───────────────────────────────┐   ┌────────────────────┐
 │ 4,980 nodes / 4,116 rels  │   │ analytics.py  (GDS)            │   │ graph_metrics       │
 │  GDS plugin 2.13          │──▶│  project → degree/pagerank/    │──▶│  (per-entity        │
 │  bolt :7687               │   │  betweenness/louvain/wcc/sim   │   │   centrality,       │
 └──────────────────────────┘   ├───────────────────────────────┤   │   community)        │
~~~~

- **GDS algorithms table + last-run numbers** — `docs/graph_analytics.md` L28-L40

~~~~text
## GDS metrics computed (real)

| Algorithm | GDS proc | Stored in `graph_metrics` |
|---|---|---|
| Degree centrality | `gds.degree` | `degree_centrality` |
| PageRank | `gds.pageRank` | `pagerank` |
| Betweenness | `gds.betweenness` | `betweenness` |
| Louvain communities | `gds.louvain` | `community_id` |
| Weakly-connected components | `gds.wcc` | (isolated-node insights) |
| Node similarity | `gds.nodeSimilarity` | `node_similarity_score` |

Target entities: CVE, Technique, ThreatActor, Malware, Campaign, IOC. Last run:
**3,315 metrics**, **1,995 components** (1,991 isolated), largest component 2,975.
~~~~

- **Attack path diagram + worked example** — `docs/graph_analytics.md` L42-L52

~~~~text
## Attack path diagram

```
 GET /graph/attack-paths?alert_id=N
   Alert ─USES_TECHNIQUE▶ Technique ─CORRELATED_TO▶ CVE ─ATTRIBUTED_TO▶ ThreatActor
                                                                          ├─USES▶ Malware
                                                                          └─RUNS▶ Campaign
 e.g.  Alert#2 -> T1505.003 -> CVE-2026-46400 -> APT28 -> X-Agent
```
Per-alert paths are generated on demand from Neo4j; metadata for the top-priority
alerts is persisted as `attack_path` insights (last run: 50 alerts, 108 paths).
~~~~

- **GDS commands** — `README.md` L393-L401

~~~~text
Neo4j runs the **GDS** plugin (enabled in `docker-compose.yml`). Compute
centrality/communities, derive insights and attack paths, then retrain risk:

```powershell
python -m backend.app.graph.analytics       # GDS: degree/pagerank/betweenness/louvain/wcc/similarity
python -m backend.app.graph.intelligence    # severity-tagged insights -> graph_insights
python -m backend.app.graph.attack_paths    # attack-path metadata -> graph_insights
python -m ml.train --version v5             # ML Risk Scoring V5 (graph features); then: python -m ml.inference
```
~~~~

- **Neo4j service with GDS plugin (docker-compose)** — `docker-compose.yml` L22-L33

~~~~text
  neo4j:
    image: neo4j:5-community
    container_name: cti_neo4j
    restart: unless-stopped
    environment:
      NEO4J_AUTH: ${NEO4J_USERNAME:-neo4j}/${NEO4J_PASSWORD:-cti_graph_pass}
      NEO4J_server_memory_pagecache_size: 512M
      NEO4J_server_memory_heap_max__size: 1G
      # Graph Data Science plugin (Phase 12). Auto-downloaded on first start.
      NEO4J_PLUGINS: '["graph-data-science"]'
      NEO4J_dbms_security_procedures_unrestricted: gds.*
      NEO4J_dbms_security_procedures_allowlist: gds.*
~~~~

- **Blast radius diagram (depth <= 4)** — `docs/agentic_soc.md` L60-L69

~~~~text
## Blast-radius diagram (14.5)

```
        seed entity
            │  (bounded Neo4j traversal, depth ≤4, undirected)
   ┌────────┼─────────┬──────────┬───────────┬─────────────┐
 alerts    CVEs   techniques   actors    campaigns    communities (from cache)
```
Community seeds read members from cached `graph_metrics`. Output: per-category
counts + capped member lists + total affected.
~~~~

- **Blast radius docstring + bounded traversal (code)** — `backend/app/agents/blast_radius.py` L1-L21

~~~~text
"""Blast-radius analysis (Phase 14.5).

Graph-driven: from a seed entity, traverse the Neo4j knowledge graph to find all
reachable alerts, CVEs, techniques, threat actors, campaigns, and communities -
the potential impact surface. Falls back gracefully if Neo4j is unavailable.
"""

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

log = logging.getLogger("agents.blast_radius")

# Bounded traversal cypher per seed type -> reachable entities (undirected).
_CYPHER = {
    "alert": (
        "MATCH (s:Alert {alert_id:$id})-[*1..4]-(n) "
        "RETURN labels(n)[0] AS label, "
        "coalesce(n.cve_id,n.technique_id,n.name,toString(n.alert_id),n.key) AS id LIMIT 2000"
    ),
~~~~

- **Link prediction architecture (Phase 16)** — `docs/phases_15_17.md` L21-L35

~~~~text
## Predictive Intelligence architecture (Phase 16)

```
 Neo4j graph ──▶ GDS FastRP/Node2Vec (seeded) ──▶ embeddings written to nodes (stored)
                      │ load_embeddings()
                      ▼
   link_prediction: cosine similarity per pair-type, exclude existing edges, top-K
     actor↔cve · actor↔campaign · campaign↔technique · malware↔cve · technique↔alert
                      ▼
   predicted_relationships (confidence)  ──▶  prediction insights (graph_insights)
                      ▼
   ML Risk Scoring V6 features: node_embedding_norm, predicted_link_count,
     predicted_actor_exposure, community_influence, graph_similarity
```
APIs: `GET /predictions`, `/predictions/actors|cves|campaigns|paths`.
~~~~

- **Link prediction docstring (code)** — `backend/app/predictions/link_prediction.py` L1-L6

~~~~text
"""Link prediction over graph embeddings (Phase 16.2 / 16.3 / 16.5).

For each target relationship type, ranks candidate node pairs by embedding cosine
similarity, excludes pairs that already have an edge, and persists the top
predictions (with confidence) to predicted_relationships. Also emits prediction
insights into graph_insights. Deterministic given the seeded embeddings.
~~~~

- **Link prediction defaults: fastrp, top_k=10, min_conf=0.5 (code)** — `backend/app/predictions/link_prediction.py` L66

~~~~text
def run(db: Session, model: str = "fastrp", top_k: int = 10, min_conf: float = 0.5) -> dict:
~~~~

- **Embeddings: FastRP default (seeded) or Node2Vec (code)** — `backend/app/predictions/embeddings.py` L1-L6

~~~~text
"""Graph embeddings via Neo4j GDS (Phase 16.1).

Computes FastRP (default, deterministic with a seed) or Node2Vec node embeddings
and writes them to the `embedding` node property in Neo4j (so they are stored and
reusable). Returns the embeddings keyed by (label, entity_id) for link prediction.
"""
~~~~

- **Determinism control** — `docs/phases_15_17.md` L86-L87

~~~~text
- Deterministic: FastRP uses a fixed `randomSeed`; routing/scoring are rule-based.
- Predictions exclude already-existing edges (only *new* likely links surfaced).
~~~~


### Superseded older doc (do not quote as current)

- **Phase 7 doc says DESIGN ONLY (superseded by Phase 11/12)** — `docs/neo4j_design.md` L3-L5

~~~~text
**Status: DESIGN ONLY.** Nothing in this document is implemented. No Neo4j is
installed, no graph code exists, no containers are created, and the PostgreSQL
schema is unchanged. This is the blueprint for a future phase.
~~~~


**NOT FOUND IN DOCS (INVESTIGATION):** graph neural networks (embeddings are GDS FastRP or Node2Vec, and prediction is cosine similarity); link-prediction accuracy metrics; traversal deeper than 4 hops; a real-time or streaming graph; cloud-hosted Neo4j or Aura (the docs describe a single Docker community instance).

---

## 6. AI ANALYST — provider-agnostic LLM, default none

### Supported facts

- **AI analyst summary + default none** — `README.md` L408-L421

~~~~text
### AI Threat Analyst (Phase 13)

Ask natural-language investigation questions over the whole platform:

```powershell
# Provider is env-driven; AI_PROVIDER=none (default) needs no LLM keys.
curl -X POST localhost:8000/ai/query -H "Content-Type: application/json" `
  -d '{"question":"Why is CVE-2026-42271 high risk?"}'
```

Routing is deterministic, evidence comes from real platform data, and graph
access is restricted to vetted read-only templates (the LLM never executes
queries). Set `AI_PROVIDER=gemini|openai|ollama` (+ keys) to have an LLM narrate
the same evidence. See [docs/ai_analyst.md](docs/ai_analyst.md).
~~~~

- **Doc intro: grounded, no hallucinated intelligence** — `docs/ai_analyst.md` L3-L7

~~~~text
A Tier-3 SOC/CTI analyst that answers natural-language investigation questions by
gathering **real evidence** from the platform (Neo4j graph, graph analytics,
attack paths, Wazuh alerts, MISP, CVE/EPSS/KEV, ML risk) and narrating it. It is
provider-agnostic and grounded: with no LLM configured it returns deterministic,
evidence-only answers, so there is **no hallucinated intelligence**.
~~~~

- **LLM abstraction: none | gemini | openai | ollama; none is default; fallback** — `docs/ai_analyst.md` L34-L40

~~~~text
## LLM abstraction (no lock-in)

`AI_PROVIDER` ∈ `none | gemini | openai | ollama` selects the backend; each is
called over its REST API with `requests` (no heavy SDKs). `none` (default) uses
the deterministic generator. Keys/URLs come from the environment
(`GEMINI_API_KEY`, `OPENAI_API_KEY`/`OPENAI_BASE_URL`, `OLLAMA_URL`, `AI_MODEL`).
On any provider error the analyst falls back to the grounded summary.
~~~~

- **EXACT WORDING — Controlled Cypher** — `docs/ai_analyst.md` L55-L63

~~~~text
## Controlled Cypher (safety)

The LLM never writes or executes Cypher. Graph access happens only through:
1. existing **parameterized** graph services, and
2. a **vetted template registry** (`CYPHER_TEMPLATES`) executed via `run_template()`,
   which rejects unknown names and runs an `is_safe_cypher()` check that blocks any
   write token (`create/merge/delete/set/remove/drop/detach/call db./load csv`).

So arbitrary or mutating graph queries are impossible by construction.
~~~~

- **Security controls summary** — `docs/ai_analyst.md` L96-L102

~~~~text
## Security controls (summary)

- No arbitrary Cypher/SQL from the LLM; graph access via vetted read-only templates + write-token rejection.
- Entity extraction is regex + DB-validated (no free-text injection into queries).
- Answers grounded strictly in gathered evidence (no hallucinated CVEs/actors/scores).
- Provider credentials only from environment; default `none` needs no secrets.
- Provider failures degrade to the deterministic generator (no hard dependency).
~~~~

- **Router docstring: LLM never supplies or executes Cypher (code)** — `backend/app/ai/query_router.py` L1-L6

~~~~text
"""Query router + controlled Cypher (Phase 13.4 / 13.5).

Rule-based, deterministic intent classification + entity extraction decides which
data sources answer a question. Graph access only ever happens through a vetted,
parameterized template registry - the LLM never supplies or executes Cypher, so
arbitrary graph execution is impossible.
~~~~

- **Vetted template registry — exactly 2 templates (code)** — `backend/app/ai/query_router.py` L126-L161

~~~~text
# ── Controlled Cypher: vetted, read-only, parameterized templates only ──

CYPHER_TEMPLATES = {
    "actor_to_alerts": (
        "MATCH (al:Alert)-[:USES_TECHNIQUE]->(:Technique)-[:CORRELATED_TO]->"
        "(c:CVE)-[:ATTRIBUTED_TO]->(a:ThreatActor {actor_id:$actor_id}) "
        "RETURN DISTINCT al.alert_id AS alert_id, al.description AS description LIMIT $limit"
    ),
    "kev_actor_links": (
        "MATCH (c:CVE)-[:ATTRIBUTED_TO]->(a:ThreatActor) "
        "WHERE c.cve_id IN $cve_ids "
        "RETURN a.name AS actor, count(DISTINCT c) AS kev_cves "
        "ORDER BY kev_cves DESC LIMIT $limit"
    ),
}

_WRITE_TOKENS = ("create", "merge", "delete", "set ", "remove", "drop", "detach",
                 "call db.", "load csv")


def is_safe_cypher(cypher: str) -> bool:
    """Defense in depth: reject anything that could mutate the graph."""
    low = cypher.lower()
    return not any(tok in low for tok in _WRITE_TOKENS)


def run_template(name: str, params: dict) -> list[dict]:
    """Execute ONLY a registered, read-only template. Raises on anything else."""
    if name not in CYPHER_TEMPLATES:
        raise ValueError(f"Unknown Cypher template '{name}'")
    cypher = CYPHER_TEMPLATES[name]
    if not is_safe_cypher(cypher):
        raise ValueError(f"Template '{name}' failed the read-only safety check")
    from backend.app.graph.neo4j_client import get_client

    return get_client().run_read(cypher, params)
~~~~

- **Provider abstraction docstring (code)** — `backend/app/ai/providers.py` L1-L6

~~~~text
"""LLM provider abstraction (Phase 13.2).

No provider lock-in. All providers are called over their REST APIs using
`requests` (no heavy SDKs), selected by `AI_PROVIDER`. When the provider is
"none" (default) or unavailable, `get_provider()` returns None and the response
generator falls back to a deterministic, evidence-grounded summary.
~~~~

- **Default model ids per provider (code)** — `backend/app/ai/providers.py` L17-L21

~~~~text
DEFAULT_MODELS = {
    "gemini": "gemini-1.5-flash",
    "openai": "gpt-4o-mini",
    "ollama": "llama3",
}
~~~~

- **AI_PROVIDER=none returns no provider (code)** — `backend/app/ai/providers.py` L106-L111

~~~~text
def get_provider() -> LLMProvider | None:
    """Return the configured provider, or None to use the deterministic fallback."""
    s = get_settings()
    provider = (s.ai_provider or "none").lower()
    if provider == "none":
        return None
~~~~

- **Deterministic fallback path (code)** — `backend/app/ai/response_generator.py` L39-L49

~~~~text
def generate(question: str, evidence: dict, provider=None) -> tuple[str, str]:
    """Return (answer_text, generator_used)."""
    if provider is not None:
        try:
            text = provider.complete(SYSTEM_PROMPT, build_prompt(question, evidence))
            if text and text.strip():
                return text.strip(), provider.name
            log.warning("provider returned empty; using deterministic fallback")
        except Exception as exc:  # noqa: BLE001
            log.warning("provider failed (%s); using deterministic fallback", exc)
    return _deterministic(evidence), "deterministic"
~~~~

- **System prompt: use ONLY the evidence (code)** — `backend/app/ai/prompt_templates.py` L5-L13

~~~~text
SYSTEM_PROMPT = (
    "You are a Tier-3 SOC analyst and CTI researcher for a threat-intelligence "
    "platform. Answer the user's question using ONLY the structured EVIDENCE "
    "provided - never invent CVEs, actors, scores, or relationships. If the "
    "evidence is empty or insufficient, say so plainly. Be concise and "
    "actionable: lead with the answer, cite the supporting entities and graph "
    "relationships from the evidence, and end with a recommended next step. "
    "Do not output JSON; write a short analyst briefing."
)
~~~~

- **Config default (code)** — `backend/app/config.py` L58-L62

~~~~text
    # AI Threat Analyst (Phase 13). No provider lock-in; "none" -> deterministic
    # evidence-grounded responses (works with zero LLM credentials).
    ai_provider: str = "none"            # none | gemini | openai | ollama
    ai_model: str = ""                   # provider model id (sensible default per provider)
    ai_temperature: float = 0.1
~~~~

- **Env template default** — `.env.example` L60-L63

~~~~text
# ── AI Threat Analyst (Phase 13) ─────────────────────────
# Provider: none | gemini | openai | ollama. "none" => deterministic answers
# grounded in evidence (no LLM credentials required).
AI_PROVIDER=none
~~~~

- **Tests: unknown template / write Cypher rejected** — `tests/test_phase13.py` L139-L147

~~~~text
def test_only_registered_templates_run():
    with pytest.raises(ValueError):
        query_router.run_template("DROP_EVERYTHING", {})


def test_write_cypher_rejected():
    assert query_router.is_safe_cypher("MATCH (n) RETURN n") is True
    assert query_router.is_safe_cypher("MATCH (n) DETACH DELETE n") is False
    assert query_router.is_safe_cypher("MERGE (n:X) RETURN n") is False
~~~~


**What happens when `AI_PROVIDER=none`:** `get_provider()` returns `None`, and `response_generator.generate()` returns the deterministic evidence summary with generator `"deterministic"` (code quotes above). The same fallback runs when a provider errors or returns an empty answer.

**Exact "never executes" wording available (choose one):**
- README L418-L420 (the sentence wraps across lines; see the README quote above): "(the LLM never executes" on L419, continued by "queries)." at the start of L420.
- docs/ai_analyst.md L57: "The LLM never writes or executes Cypher."
- backend/app/ai/query_router.py L5: "the LLM never supplies or executes Cypher, so".

**NOT FOUND IN DOCS (AI ANALYST):** which LLM, if any, was used in demos; fine-tuning; RAG, vector databases or embeddings of documents; the LLM choosing tools or writing queries (explicitly denied); an "LLM narrates evidence only" sentence with those exact words. The closest exact phrases are "have an LLM narrate the same evidence" (README L420-421), "provider (Gemini/OpenAI/Ollama) narrates evidence" (docs/ai_analyst.md L25), and "Deterministic by default; no external LLM required (optional narration only)." (docs/agentic_soc.md L109). The Cypher template registry holds only **2** templates (`actor_to_alerts`, `kev_actor_links`). Do not imply a large template library.

---

## 7. AGENTIC ANALYST — planner + executor over 12 read-only tools

### Supported facts

- **README summary (12-tool read-only registry)** — `README.md` L423-L437

~~~~text
### Agentic SOC Analyst (Phase 14)

Run an autonomous investigation that plans, gathers evidence via vetted tools,
maps blast radius, and recommends remediations — all auditable and persisted:

```powershell
curl -X POST localhost:8000/agent/investigate/alert -H "Content-Type: application/json" `
  -d '{"alert_id": 2}'
# -> { plan, tool_calls, blast_radius, report{risk_assessment, recommendations, ...}, confidence }
```

The agent acts only through a 12-tool read-only registry over existing services;
every tool call is logged and every recommendation cites its evidence. History,
lineage, and stored reports are available via `/agent/history` and `/agent/report`.
See [docs/agentic_soc.md](docs/agentic_soc.md).
~~~~

- **Doc intro** — `docs/agentic_soc.md` L3-L6

~~~~text
Turns the AI Threat Analyst into an autonomous agent that **investigates,
correlates, prioritizes, explains, and recommends** by chaining existing
platform services as vetted tools. Every investigation is evidence-driven and
fully auditable (plan + tool-call log + evidence + report persisted).
~~~~

- **Agent architecture diagram** — `docs/agentic_soc.md` L10-L29

~~~~text
```
  User Request (type + target)
        ▼
   planner.plan() ───────────▶ Task Graph (ordered steps + rationale + $params)
        ▼
   executor.execute() ───────▶ resolve $params from running context
        │                       run vetted tool (tools.run_tool)  ──┐
        │                       log every call (auditable)          │ TOOL REGISTRY
        ▼                       collect evidence                    │ (12 read-only tools
   blast_radius.compute() ────▶ graph-driven impact surface        │  over existing services)
        ▼                                                          ─┘
   report_generator.build_report()
        │   risk explanation · remediation (evidence-cited) · attack paths · blast radius
        ▼
   memory.save()  ───────────▶ agent_investigations (plan, tool_calls, evidence, report, lineage)
        ▼
   AgentResult (structured, exportable JSON)
```

Files: `backend/app/agents/{agent,planner,executor,memory,tools,report_generator,blast_radius}.py`.
~~~~

- **EXACT TOOL LIST (12)** — `docs/agentic_soc.md` L31-L38

~~~~text
## Tools implemented (12, all read-only over existing services)

`graph_investigation`, `attack_path_investigation`, `alert_investigation`,
`threat_actor_investigation`, `campaign_investigation`, `technique_investigation`,
`risk_score_retrieval`, `graph_metrics_retrieval`, `wazuh_alert_retrieval`,
`misp_intel_retrieval`, `kev_retrieval`, `epss_retrieval`. The agent can act
**only** through this registry (`run_tool` rejects anything else); every call is
logged with status, summary, and duration.
~~~~

- **Planner workflow for an alert (8 tool steps)** — `docs/agentic_soc.md` L42-L53

~~~~text
```
 investigate alert #N  ──▶  1 wazuh_alert_retrieval
                            2 alert_investigation        (→ derives $cve_id)
                            3 attack_path_investigation
                            4 risk_score_retrieval($cve_id)
                            5 epss_retrieval($cve_id)
                            6 kev_retrieval($cve_id)
                            7 graph_metrics_retrieval(CVE,$cve_id)
                            8 misp_intel_retrieval($cve_id)
```
Steps with `$placeholders` are resolved by the executor from earlier outputs;
unresolved steps are skipped (logged), never fabricated.
~~~~

- **Investigation types** — `docs/agentic_soc.md` L55-L58

~~~~text
## Investigation types (14.4)

Alert, CVE, Threat-Actor, Campaign, Technique, Community — each an autonomous
agent that gathers evidence and produces a full report.
~~~~

- **Security controls** — `docs/agentic_soc.md` L102-L109

~~~~text
## Security controls

- Agent acts only through the vetted tool registry (no arbitrary code/queries);
  graph tools reuse the parameterized services and read-only Cypher templates.
- Tool failures degrade to skipped/error steps; the agent never crashes or invents data.
- Every recommendation and finding is traceable to a logged tool call + evidence source.
- Full audit trail persisted per investigation (plan, tool-call log, evidence, report).
- Deterministic by default; no external LLM required (optional narration only).
~~~~

- **Tool registry in code (matches the 12 names)** — `backend/app/agents/tools.py` L139-L163

~~~~text
TOOL_REGISTRY = {
    "graph_investigation": (graph_investigation, "Graph subgraph for an entity"),
    "attack_path_investigation": (attack_path_investigation, "Attack paths for an alert"),
    "alert_investigation": (alert_investigation, "Full alert evidence"),
    "threat_actor_investigation": (threat_actor_investigation, "Threat-actor ecosystem evidence"),
    "campaign_investigation": (campaign_investigation, "Campaign ecosystem evidence"),
    "technique_investigation": (technique_investigation, "Technique evidence"),
    "risk_score_retrieval": (risk_score_retrieval, "ML risk + priority for a CVE"),
    "graph_metrics_retrieval": (graph_metrics_retrieval, "GDS centrality for an entity"),
    "wazuh_alert_retrieval": (wazuh_alert_retrieval, "Raw Wazuh alert + enrichment"),
    "misp_intel_retrieval": (misp_intel_retrieval, "MISP actors linked to a CVE"),
    "kev_retrieval": (kev_retrieval, "CISA KEV status for a CVE"),
    "epss_retrieval": (epss_retrieval, "EPSS score for a CVE"),
}


def run_tool(name: str, db: Session, params: dict) -> dict:
    if name not in TOOL_REGISTRY:
        raise ValueError(f"Unknown agent tool '{name}'")
    fn, _desc = TOOL_REGISTRY[name]
    try:
        return fn(db, **params)
    except Exception as exc:  # noqa: BLE001 - tool failures degrade, never crash the agent
        log.warning("tool %s failed: %s", name, exc)
        return {"ok": False, "summary": f"{name} failed: {exc}", "data": {}}
~~~~

- **Tool registry docstring: read-only whitelist (code)** — `backend/app/agents/tools.py` L1-L5

~~~~text
"""Agent tool registry (Phase 14.2).

Every tool wraps an existing, vetted platform service or read-only DB query - the
agent can only act through this whitelist. Tools return {"ok", "summary", "data"}
and are invoked via `run_tool`, which the executor logs.
~~~~

- **Planner is a static per-type task graph (code)** — `backend/app/agents/planner.py` L1-L27

~~~~text
"""Investigation planner (Phase 14.3).

Builds an explainable, ordered task graph for each investigation type. Steps may
reference values discovered by earlier steps via "$placeholders" (e.g. the top
related CVE found while investigating an alert), which the executor resolves.
"""


def _step(n, tool, params, rationale):
    return {"step": n, "tool": tool, "params": params, "rationale": rationale}


def plan(investigation_type: str, target: dict) -> list[dict]:
    t = investigation_type

    if t == "alert":
        aid = target["alert_id"]
        steps = [
            ("wazuh_alert_retrieval", {"alert_id": aid}, "Retrieve the raw Wazuh alert and its enrichment"),
            ("alert_investigation", {"alert_id": aid}, "Correlate alert -> technique -> CVE -> actor"),
            ("attack_path_investigation", {"alert_id": aid}, "Enumerate attack paths from the alert"),
            ("risk_score_retrieval", {"cve_id": "$cve_id"}, "ML risk + priority for the top related CVE"),
            ("epss_retrieval", {"cve_id": "$cve_id"}, "EPSS exploit probability of the CVE"),
            ("kev_retrieval", {"cve_id": "$cve_id"}, "CISA KEV (active-exploitation) status"),
            ("graph_metrics_retrieval", {"entity_type": "CVE", "entity_id": "$cve_id"}, "Graph centrality of the CVE"),
            ("misp_intel_retrieval", {"cve_id": "$cve_id"}, "MISP threat-actor attribution"),
        ]
~~~~

- **Executor: resolve $params, log calls, degrade on failure (code)** — `backend/app/agents/executor.py` L1-L6

~~~~text
"""Plan executor (Phase 14.1).

Runs a planner task graph: resolves "$placeholder" params from a running context
built out of earlier tool outputs, invokes each vetted tool, logs every call
(auditable), and collects evidence. Tool failures degrade to skipped/error steps
without aborting the investigation.
~~~~

- **Agent pipeline (code)** — `backend/app/agents/agent.py` L1-L5

~~~~text
"""Agentic SOC investigation orchestrator (Phase 14.1 / 14.4).

Pipeline: plan -> execute tools (collect evidence + log) -> blast radius ->
report -> persist. Each agent type (alert/cve/actor/campaign/technique/community)
runs autonomously and produces an auditable, evidence-driven report.
~~~~

- **Roadmap Phase 14** — `README.md` L519

~~~~text
- **Phase 14 (done):** Agentic SOC Analyst — planner/executor over 12 vetted tools, autonomous investigations (alert/cve/actor/campaign/community), graph-driven blast radius, evidence-cited risk explanation + remediation, exportable reports with persisted lineage, 9 agent APIs, 5 agent dashboard pages; see [docs/agentic_soc.md](docs/agentic_soc.md)
~~~~


**Does planning work without an LLM?** Yes. The docs say "Deterministic by default; no external LLM required (optional narration only)." (docs/agentic_soc.md L109). In the code, `planner.plan()` returns hard-coded step lists per investigation type, and no file under `backend/app/agents/` imports the LLM provider. The only caller of `get_provider()` in the backend is `backend/app/ai/analyst.py` (checked with grep).

**NOT FOUND IN DOCS (AGENTIC):** LLM-driven planning or tool selection; any tool that writes, acts or contains threats (all 12 are read-only retrievals); multi-agent frameworks such as LangChain, LangGraph, CrewAI or AutoGen (none appear in the repo); autonomous remediation (response execution needs human approval, see section 9); any tool count other than 12.

---

## 8. RECOMMENDATION — how recommendations are generated

### Supported facts

- **Evidence-cited remediation rules** — `docs/agentic_soc.md` L71-L78

~~~~text
## Risk explanation & remediation (14.6 / 14.7)

The report's `risk_assessment` explains the level from Wazuh severity + EPSS +
KEV + ML risk + SOC priority + graph centrality. `recommendations` are generated
from that evidence (Patch immediately if KEV; prioritize if high EPSS; escalate
if CRITICAL/HIGH; hunt actor TTPs; tune detections; investigate related alerts)
and **each recommendation cites the evidence tool** it came from. No hallucinated
remediation.
~~~~

- **Report generator docstring (code)** — `backend/app/agents/report_generator.py` L1-L7

~~~~text
"""Investigation report generator (Phase 14.6 / 14.7 / 14.8).

Synthesizes the collected evidence + blast radius + tool log into a structured,
exportable report: executive summary, technical findings, threat intelligence,
attack-path analysis, risk assessment (explanation), blast radius, and
evidence-cited remediations. Every recommendation references supporting evidence
- no hallucinated remediation.
~~~~

- **Recommendation rules with exact triggers (code)** — `backend/app/agents/report_generator.py` L53-L108

~~~~text
def _recommendations(inv_type, evidence, blast) -> list:
    recs = []
    risk = _by_tool(evidence, "risk_score_retrieval")
    epss = _by_tool(evidence, "epss_retrieval")
    kev = _by_tool(evidence, "kev_retrieval")
    misp = _by_tool(evidence, "misp_intel_retrieval")
    alert_ev = _by_tool(evidence, "alert_investigation")
    actor_ev = _by_tool(evidence, "threat_actor_investigation")
    cve = risk.get("cve_id") or kev.get("cve_id") or epss.get("cve_id")

    if kev.get("in_kev"):
        recs.append({"action": "Patch immediately",
                     "detail": f"{cve} is in CISA KEV (actively exploited; due {kev.get('due_date') or 'n/a'}). "
                               "Apply the vendor fix per the CISA directive.",
                     "evidence": "kev_retrieval"})
    elif epss.get("epss_score", 0) and epss["epss_score"] >= 0.3:
        recs.append({"action": "Prioritize patching",
                     "detail": f"{cve} has high EPSS exploit probability ({epss['epss_score']:.3f}).",
                     "evidence": "epss_retrieval"})

    if (risk.get("priority_level") in ("CRITICAL", "HIGH")) or (risk.get("risk_level") in ("CRITICAL", "HIGH")):
        recs.append({"action": "Escalate for urgent remediation",
                     "detail": f"{cve or 'Target'} scored {risk.get('priority_level') or risk.get('risk_level')}.",
                     "evidence": "risk_score_retrieval"})

    actors = misp.get("threat_actors") or (alert_ev.get("findings", {}) if alert_ev else {}).get("threat_actors") or []
    if actors:
        recs.append({"action": "Review threat-actor activity / threat hunt",
                     "detail": f"Attributed actor(s): {', '.join(actors[:5])}. Hunt for their known TTPs.",
                     "evidence": "misp_intel_retrieval"})

    techniques = (alert_ev.get("findings", {}) if alert_ev else {}).get("techniques") or []
    if techniques:
        recs.append({"action": "Validate / tune detections",
                     "detail": f"Ensure coverage for ATT&CK technique(s): {', '.join(techniques[:5])}.",
                     "evidence": "alert_investigation"})

    affected_alerts = (blast or {}).get("counts", {}).get("affected_alerts", 0)
    if affected_alerts > 1:
        recs.append({"action": "Investigate related alerts",
                     "detail": f"{affected_alerts} alerts share entities in the blast radius; "
                               "review for a coordinated campaign.",
                     "evidence": "blast_radius"})

    if actor_ev.get("findings"):
        eco = actor_ev["findings"].get("ecosystem", {})
        if eco:
            recs.append({"action": "Increase monitoring",
                         "detail": f"Actor ecosystem spans {eco}. Raise monitoring on associated assets.",
                         "evidence": "threat_actor_investigation"})

    if not recs:
        recs.append({"action": "Continue monitoring",
                     "detail": "No urgent indicators in the gathered evidence; maintain standard monitoring.",
                     "evidence": "overview"})
    return recs
~~~~

- **Phase 19: recommendations turned into approvable actions** — `docs/response_approval.md` L3-L8

~~~~text
The final engineering phase. Turns evidence-based agent recommendations into
**approvable** response actions that execute **only through the existing
ShuffleProvider** after explicit analyst approval, with verification and a complete
audit trail. No action ever runs automatically. No new external products were
introduced — everything reuses PostgreSQL, the FastAPI backend, the Agentic SOC
Analyst, and the Phase-18 ticketing/SOAR framework.
~~~~

- **action_type mapping** — `docs/response_approval.md` L35-L36

~~~~text
`action_type` is mapped deterministically from the agent recommendation text
(patch / escalate / threat_hunt / tune_detection / investigate / monitor / review).
~~~~

- **action_type mapping (code)** — `backend/app/response_engine.py` L27-L41

~~~~text
def _action_type(action: str) -> str:
    a = (action or "").lower()
    if "patch" in a:
        return "patch"
    if "escalate" in a:
        return "escalate"
    if "hunt" in a or "actor" in a:
        return "threat_hunt"
    if "detection" in a:
        return "tune_detection"
    if "investigate" in a:
        return "investigate"
    if "monitor" in a:
        return "monitor"
    return "review"
~~~~

- **Idempotent generation from an investigation (code)** — `backend/app/response_engine.py` L61-L96

~~~~text
def generate_from_investigation(db: Session, investigation_id: int) -> list[dict]:
    from backend.app.models import AgentInvestigation, ResponseRecommendation

    inv = db.get(AgentInvestigation, investigation_id)
    if inv is None:
        raise ValueError(f"Investigation {investigation_id} not found")
    report = inv.report or {}
    level = (report.get("risk_assessment") or {}).get("level", "MEDIUM")

    existing = {
        (r.source_id, r.action_type, r.title)
        for r in db.execute(select(ResponseRecommendation)
                            .where(ResponseRecommendation.source_type == "investigation",
                                   ResponseRecommendation.source_id == str(inv.id))).scalars().all()
    }
    created = []
    for rec in report.get("recommendations", []):
        action_type = _action_type(rec.get("action", ""))
        title = rec.get("action", "Response action")
        key = (str(inv.id), action_type, title)
        if key in existing:
            continue
        row = ResponseRecommendation(
            source_type="investigation", source_id=str(inv.id), action_type=action_type,
            title=title, description=rec.get("detail", ""), severity=level,
            rationale=f"Derived from agent evidence: {rec.get('evidence', 'n/a')}",
            evidence={"evidence_tool": rec.get("evidence"), "target": inv.target,
                      "investigation_id": inv.id},
            confidence=inv.confidence or 0.0, status=PENDING, created_at=_now())
        db.add(row)
        db.flush()
        _audit(db, row.id, "generated", "system",
               {"source": f"investigation:{inv.id}", "action_type": action_type})
        created.append(row)
    db.commit()
    return [_serialize(r) for r in created]
~~~~

- **Generate command** — `README.md` L469-L470

~~~~text
# Generate evidence-based recommendations from recent agent investigations:
curl -X POST localhost:8000/response/generate -d '{"limit":10}' -H "Content-Type: application/json"
~~~~


Code detail: the "Prioritize patching" recommendation fires at EPSS **>= 0.3** (`report_generator.py` L68). The docs only say "prioritize if high EPSS".

**NOT FOUND IN DOCS (RECOMMENDATION):** LLM-generated recommendations (they come from fixed rules); containment actions such as isolating a host, blocking an IP or disabling an account. The action types are only patch, escalate, threat_hunt, tune_detection, investigate, monitor and review.

---

## 9. HUMAN APPROVAL — approval gate, state machine, HTTP 409

### Supported facts

- **Status line: nothing executes automatically; 409** — `README.md` L5

~~~~text
**Current status: Phase 19 — human-in-the-loop response (approval-gated).** The final engineering phase adds evidence-based **response recommendations** (derived from agent investigations) that an analyst must **approve** before they execute — only through the existing **ShuffleProvider** — followed by verification and a complete **audit trail**. Nothing executes automatically: attempting to execute an unapproved recommendation returns HTTP 409. Lightweight and reuse-only (2 tables, 1 migration, 1 module, 5 pages, existing SOAR framework). A 69-page dashboard adds 5 response pages. See [docs/response_approval.md](docs/response_approval.md). Every earlier phase (collectors → correlation → risk V6 → graph/GDS → AI/agentic analyst → orchestration) remains in place.
~~~~

- **Response lifecycle diagram + gate** — `docs/response_approval.md` L10-L26

~~~~text
## Response lifecycle

```
 agent investigation report.recommendations (evidence-cited)
        │  response_engine.generate_from_investigation()  (idempotent)
        ▼
   [ pending ] ──approve(analyst)──▶ [ approved ] ──execute(analyst)──▶ [ executed ]
        │                                │  via ticketing.execute_action()      │
        └──reject(analyst)──▶ [rejected] │  (ShuffleProvider webhook / mock)     │
                                         │                                       ▼
                                         └──────────────── verify(analyst) ─▶ [ verified ]
 every transition appends to response_audit (event, actor, timestamp, detail)
```

The approval gate is enforced in `execute()`: it raises `PermissionError`
(HTTP 409) unless `status == "approved"`. `verify()` likewise requires
`status == "executed"`.
~~~~

- **Guarantees** — `docs/response_approval.md` L57-L67

~~~~text
## Guarantees

- **No autonomous execution** — execution requires a prior recorded approval;
  attempting to execute a non-approved recommendation returns 409.
- **Auditable** — every transition (generated/approved/rejected/executed/verified)
  is logged with actor + timestamp in `response_audit`.
- **Reuses SOAR** — execution goes through the existing ShuffleProvider; Mock by
  default so nothing external is required for dev/tests.
- **Idempotent generation** — re-generating from the same investigation creates no
  duplicates.
- **Lightweight** — 2 tables, 1 migration, 1 backend module, 5 dashboard pages.
~~~~

- **Status constants (code)** — `backend/app/response_engine.py` L18-L20

~~~~text
# Recommendation status lifecycle.
PENDING, APPROVED, REJECTED, EXECUTED, VERIFIED, FAILED = (
    "pending", "approved", "rejected", "executed", "verified", "failed")
~~~~

- **State machine comment (code)** — `backend/app/models/response.py` L30-L31

~~~~text
    # pending -> approved | rejected ; approved -> executed ; executed -> verified | failed
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
~~~~

- **approve / reject / execute / verify (code)** — `backend/app/response_engine.py` L153-L208

~~~~text
def approve(db, rec_id: int, approver: str) -> dict:
    r = _load(db, rec_id)
    if r.status != PENDING:
        raise PermissionError(f"Cannot approve a '{r.status}' recommendation")
    r.status, r.approved_by, r.approved_at = APPROVED, approver, _now()
    _audit(db, r.id, "approved", approver, {})
    db.commit()
    return _serialize(r)


def reject(db, rec_id: int, approver: str, reason: str = "") -> dict:
    r = _load(db, rec_id)
    if r.status != PENDING:
        raise PermissionError(f"Cannot reject a '{r.status}' recommendation")
    r.status, r.approved_by, r.approved_at = REJECTED, approver, _now()
    _audit(db, r.id, "rejected", approver, {"reason": reason})
    db.commit()
    return _serialize(r)


def execute(db, rec_id: int, actor: str = "system") -> dict:
    """Execute an APPROVED action via ShuffleProvider. Refuses otherwise."""
    from backend.app.ticketing import execute_action

    r = _load(db, rec_id)
    if r.status != APPROVED:
        raise PermissionError(
            f"Refusing to execute: recommendation is '{r.status}', not 'approved'. "
            "Analyst approval is required before execution.")
    payload = {"action_type": r.action_type, "title": r.title, "description": r.description or "",
               "severity": r.severity, "source_type": r.source_type, "source_id": r.source_id,
               "recommendation_id": r.id}
    result = execute_action(payload)
    r.execution_result = result
    r.executed_at = _now()
    r.status = EXECUTED if result else FAILED
    _audit(db, r.id, "executed", actor, {"provider": result.get("provider"),
                                         "reference": result.get("ticket_id")})
    db.commit()
    return _serialize(r)


def verify(db, rec_id: int, actor: str = "system") -> dict:
    """Verify that the executed action was accepted by the SOAR provider."""
    r = _load(db, rec_id)
    if r.status != EXECUTED:
        raise PermissionError(f"Cannot verify a '{r.status}' recommendation (must be executed)")
    res = r.execution_result or {}
    ok = bool(res.get("status") in ("created", "triggered", "accepted") or res.get("ticket_id"))
    verification = {"verified": ok, "provider": res.get("provider"),
                    "reference": res.get("ticket_id"), "checked_at": _now().isoformat()}
    r.verified = ok
    r.status = VERIFIED if ok else FAILED
    _audit(db, r.id, "verified" if ok else "failed", actor, verification)
    db.commit()
    return _serialize(r)
~~~~

- **PermissionError -> HTTP 409, ValueError -> 404 (code)** — `backend/app/routers/response.py` L36-L42

~~~~text
def _guard(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
~~~~

- **Execute endpoint docstring (code)** — `backend/app/routers/response.py` L92-L95

~~~~text
@router.post("/recommendations/{rec_id}/execute")
def execute(rec_id: int, payload: ActorRequest, db: Session = Depends(get_db)):
    """Execute an APPROVED recommendation via Shuffle. 409 if not approved."""
    return _guard(engine.execute, db, rec_id, payload.actor)
~~~~

- **Test: execute without approval returns 409** — `tests/test_phase19.py` L139-L144

~~~~text
def test_api_execute_without_approval_409():
    pending = client.get("/response/recommendations?status=pending").json()
    if pending:
        rid = pending[0]["id"]
        resp = client.post(f"/response/recommendations/{rid}/execute", json={"actor": "x"})
        assert resp.status_code == 409  # approval gate enforced at the API
~~~~

- **Test: full flow audit sequence** — `tests/test_phase19.py` L102-L112

~~~~text
def test_full_approval_execution_flow_and_audit():
    with TestingSessionLocal() as db:
        rid = _first_pending(db)["id"]
        engine.approve(db, rid, "analyst.jane")
        ex = engine.execute(db, rid, "analyst.jane")
        assert ex["status"] == "executed"
        assert ex["execution_result"]["provider"] == "mock"  # SOAR mock
        vf = engine.verify(db, rid, "analyst.jane")
        assert vf["verified"] is True and vf["status"] == "verified"
        events = [a["event"] for a in engine.audit_trail(db, rid)]
    assert events == ["generated", "approved", "executed", "verified"]
~~~~

- **Endpoints (README)** — `README.md` L185

~~~~text
- `GET /response/recommendations`, `/response/stats`, `/response/audit`, `POST /response/generate`, `/response/recommendations/{id}/approve|reject|execute|verify` — approval-gated response actions
~~~~

- **Endpoints (doc)** — `docs/response_approval.md` L46-L50

~~~~text
## APIs

`GET /response/recommendations`, `/response/recommendations/{id}`,
`/response/recommendations/{id}/audit`, `/response/stats`, `/response/audit`;
`POST /response/generate`, `/response/recommendations/{id}/approve|reject|execute|verify`.
~~~~

- **Approval curl examples** — `README.md` L471-L475

~~~~text
# Approval gate: execute is refused (409) until an analyst approves:
curl -X POST localhost:8000/response/recommendations/1/approve -d '{"approver":"jane"}' -H "Content-Type: application/json"
curl -X POST localhost:8000/response/recommendations/1/execute -d '{"actor":"jane"}'  -H "Content-Type: application/json"
curl -X POST localhost:8000/response/recommendations/1/verify  -d '{"actor":"jane"}'  -H "Content-Type: application/json"
```
~~~~


Exact 409 behaviour (code): `execute()` raises `PermissionError("Refusing to execute: recommendation is '<status>', not 'approved'. Analyst approval is required before execution.")`, and the router maps `PermissionError` to **HTTP 409** with that message as `detail`. Approve and reject on a non-`pending` recommendation, and verify on a non-`executed` one, also return 409. An unknown id returns 404.

**NOT FOUND IN DOCS (HUMAN APPROVAL):** authentication, RBAC or approver identity checks. `approver` and `actor` are free-text request fields, and the backend has no auth layer (I grepped for OAuth, HTTPBearer, APIKeyHeader and roles and found none). Also absent: four-eyes or multi-approver rules, approval expiry, and approval SLAs. Do not claim "role-based approval" or "authenticated analysts".

---

## 10. RESPONSE — execution via ShuffleProvider, then verification

### Supported facts

- **Execution through existing ShuffleProvider (mock by default)** — `README.md` L477-L478

~~~~text
Approved actions execute through the existing `ShuffleProvider` (mock by default);
every transition is recorded in `response_audit`. See [docs/response_approval.md](docs/response_approval.md).
~~~~

- **Backend module + execute_action routing** — `docs/response_approval.md` L38-L44

~~~~text
## Backend module

`backend/app/response_engine.py` — `generate_from_investigation`, `generate_recent`,
`list_recommendations`, `approve`, `reject`, `execute`, `verify`, `audit_trail`,
`stats`. Execution reuses `backend.app.ticketing.execute_action()` (added to the
existing service), which routes to Shuffle (webhook/workflow) when configured and
the credential-free Mock otherwise.
~~~~

- **Reuses SOAR guarantee** — `docs/response_approval.md` L63-L64

~~~~text
- **Reuses SOAR** — execution goes through the existing ShuffleProvider; Mock by
  default so nothing external is required for dev/tests.
~~~~

- **execute_action (code)** — `backend/app/ticketing/service.py` L60-L72

~~~~text
def execute_action(action: dict) -> dict:
    """Execute an APPROVED response action via the SOAR provider (Phase 19).

    Reuses the existing provider framework (Shuffle webhook/workflow when
    configured, mock otherwise). This never runs automatically - callers must
    have recorded analyst approval first.
    """
    title = f"[RESPONSE:{action.get('action_type', 'action')}] {action.get('title', '')}"[:250]
    body = action.get("description", "")
    return _safe_create(title, body, action.get("severity", "HIGH"),
                        kind="response_action", action_type=action.get("action_type"),
                        recommendation_id=action.get("recommendation_id"),
                        source=f"{action.get('source_type')}:{action.get('source_id')}")
~~~~

- **Provider selection + fallback to mock (code)** — `backend/app/ticketing/service.py` L16-L36

~~~~text
def get_provider():
    s = get_settings()
    provider = (s.ticket_provider or "mock").lower()
    try:
        if provider == "jira" and s.jira_url and s.jira_token:
            return JiraProvider(s.jira_url, s.jira_user, s.jira_token, s.jira_project)
        if provider == "thehive" and s.thehive_url and s.thehive_api_key:
            return TheHiveProvider(s.thehive_url, s.thehive_api_key)
        if provider == "shuffle" and (s.shuffle_webhook_url or (s.shuffle_url and s.shuffle_workflow_id)):
            return ShuffleProvider(s.shuffle_webhook_url, s.shuffle_url, s.shuffle_api_key, s.shuffle_workflow_id)
    except Exception as exc:  # noqa: BLE001
        log.warning("ticket provider init failed (%s); using mock", exc)
    return MockProvider()


def _safe_create(title, body, severity, **extra) -> dict:
    try:
        return get_provider().create_ticket(title, body, severity, **extra)
    except Exception as exc:  # noqa: BLE001
        log.warning("ticket creation failed (%s); using mock", exc)
        return MockProvider().create_ticket(title, body, severity, **extra)
~~~~

- **ShuffleProvider: webhook preferred, else workflow execute API (code)** — `backend/app/ticketing/providers.py` L59-L83

~~~~text
class ShuffleProvider(TicketProvider):
    """Shuffle SOAR via webhook (preferred) or workflow execute API."""

    name = "shuffle"

    def __init__(self, webhook_url="", url="", api_key="", workflow_id=""):
        self.webhook_url = webhook_url.rstrip("/") if webhook_url else ""
        self.url = url.rstrip("/") if url else ""
        self.api_key, self.workflow_id = api_key, workflow_id

    def create_ticket(self, title, body, severity="HIGH", **extra) -> dict:
        payload = {"title": title, "body": body, "severity": severity, **extra}
        if self.webhook_url:
            r = requests.post(self.webhook_url, json=payload, timeout=TIMEOUT)
            r.raise_for_status()
            return {"provider": "shuffle", "status": "triggered", "via": "webhook",
                    "ticket_id": (r.json().get("execution_id") if r.headers.get("content-type", "").startswith("application/json") else "accepted")}
        if self.url and self.workflow_id:
            r = requests.post(f"{self.url}/api/v1/workflows/{self.workflow_id}/execute",
                              headers={"Authorization": f"Bearer {self.api_key}"},
                              json={"execution_argument": payload}, timeout=TIMEOUT)
            r.raise_for_status()
            return {"provider": "shuffle", "status": "triggered", "via": "api",
                    "ticket_id": r.json().get("execution_id")}
        raise RuntimeError("Shuffle provider not configured (set SHUFFLE_WEBHOOK_URL or SHUFFLE_URL)")
~~~~

- **SOAR diagram + Shuffle config** — `docs/orchestration.md` L49-L60

~~~~text
## SOAR integration diagram

```
 autonomous_triage ─▶ agent investigation ─▶ ticketing.export_investigation
                                                    │
        ┌───────────────────────────────────────────┤ provider = env TICKET_PROVIDER
        ▼                 ▼                 ▼         ▼
     MockProvider      JiraProvider    TheHiveProvider   ShuffleProvider
     (default)         REST issue      REST case         webhook or workflow API
```
Shuffle uses `SHUFFLE_WEBHOOK_URL` (preferred) or the workflow execute API. No
provider needs to be live — Mock is the default and all failures fall back to it.
~~~~

- **Default ticket provider = mock (code)** — `backend/app/config.py` L68-L79

~~~~text
    # Ticketing connectors (Phase 15.6). Default "mock" needs no credentials.
    ticket_provider: str = "mock"        # mock | jira | thehive | shuffle
    jira_url: str = ""
    jira_user: str = ""
    jira_token: str = ""
    jira_project: str = "SOC"
    thehive_url: str = ""
    thehive_api_key: str = ""
    shuffle_url: str = ""
    shuffle_api_key: str = ""
    shuffle_workflow_id: str = ""
    shuffle_webhook_url: str = ""
~~~~

- **Future roadmap: live Shuffle playbooks NOT yet done** — `README.md` L523

~~~~text
- **Future:** temporal coverage/risk trends, fully-supervised risk labels (KEV/EPSS ground truth), more feeds (OTX, AbuseIPDB), live Shuffle playbooks for approved actions
~~~~


What "verify" actually checks (code, `response_engine.py` L195-208): it passes when the stored execution result has status `created`, `triggered` or `accepted`, or has a `ticket_id`. **It confirms that the SOAR or mock provider accepted the action. It does not confirm that the remediation took effect on any asset.**

**NOT FOUND IN DOCS (RESPONSE):** live Shuffle playbooks actually running (listed as **Future**); endpoint or firewall enforcement; rollback; verification that remediation worked. The default everywhere is the **Mock** provider ("Mock by default so nothing external is required for dev/tests").

---

## 11. AUDIT — response_audit

### Supported facts

- **Audit in lifecycle diagram** — `docs/response_approval.md` L21

~~~~text
 every transition appends to response_audit (event, actor, timestamp, detail)
~~~~

- **Data model: 2 tables** — `docs/response_approval.md` L28-L33

~~~~text
## Data model (2 tables, 1 migration)

- **`response_recommendations`** — action_type, title, description, severity,
  rationale + evidence (JSON), confidence, status, approved_by/at, executed_at,
  verified, execution_result (SOAR response), source (investigation).
- **`response_audit`** — append-only (recommendation_id, event, actor, detail, ts).
~~~~

- **Auditable guarantee** — `docs/response_approval.md` L61-L62

~~~~text
- **Auditable** — every transition (generated/approved/rejected/executed/verified)
  is logged with actor + timestamp in `response_audit`.
~~~~

- **ResponseAudit model (code)** — `backend/app/models/response.py` L43-L54

~~~~text
class ResponseAudit(Base):
    __tablename__ = "response_audit"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    recommendation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("response_recommendations.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    event: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    actor: Mapped[str] = mapped_column(String(100), nullable=False, default="system")
    detail: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
~~~~

- **_audit helper (code)** — `backend/app/response_engine.py` L44-L47

~~~~text
def _audit(db: Session, rec_id: int, event: str, actor: str = "system", detail: dict | None = None):
    from backend.app.models import ResponseAudit
    db.add(ResponseAudit(recommendation_id=rec_id, event=event, actor=actor,
                         detail=detail or {}, created_at=_now()))
~~~~

- **Audit detail recorded on execute (code)** — `backend/app/response_engine.py` L189-L190

~~~~text
    _audit(db, r.id, "executed", actor, {"provider": result.get("provider"),
                                         "reference": result.get("ticket_id")})
~~~~

- **Other audit trails: agent investigations persisted** — `docs/agentic_soc.md` L108

~~~~text
- Full audit trail persisted per investigation (plan, tool-call log, evidence, report).
~~~~

- **Other audit trails: pipeline_runs** — `docs/orchestration.md` L62-L68

~~~~text
## Retry, recovery & idempotency (18.4)

- `executor.run_job` retries `JOB_MAX_RETRIES` times with linear backoff; every
  attempt's final outcome is a `pipeline_runs` row (running → completed/failed).
- **Idempotent:** correlation/risk/graph/analytics/embeddings/coverage all upsert;
  triage dedups investigations by target; reports append but triage-of-a-given-alert
  won't re-run. So retries and restarts never duplicate data.
~~~~


Recorded per audit row (code): `recommendation_id`, `event` (generated / approved / rejected / executed / verified / failed), `actor` (default `"system"`), `detail` (JSON: for example the source on generate, the `reason` on reject, the provider and reference on execute, the verification result on verify) and `created_at`.

**NOT FOUND IN DOCS (AUDIT):** tamper-evidence, hash chains, signing, or retention policy. "Append-only" is how the doc describes it. In code the audit table's foreign key is `ondelete="CASCADE"`, so deleting a recommendation would delete its audit rows. Do not call the audit trail "immutable" or "tamper-proof". Also absent: audit logging of AI-analyst Q&A in `response_audit` (agent investigations are persisted separately in `agent_investigations`).

---

## 12. "Core pipeline works without an LLM" — supporting sentences

No file contains the exact sentence "the core pipeline works without an LLM". The sentences below support the idea. Quote them, not the paraphrase.

- **Correlation: no LLMs** — `README.md` L229-L230

~~~~text
so every link is explainable. No LLMs or paid services are involved; the design
is built to be swapped for an ML/graph model later without a schema change.
~~~~

- **AI analyst default needs no LLM keys** — `README.md` L413

~~~~text
# Provider is env-driven; AI_PROVIDER=none (default) needs no LLM keys.
~~~~

- **Agentic analyst: no external LLM required** — `docs/agentic_soc.md` L109

~~~~text
- Deterministic by default; no external LLM required (optional narration only).
~~~~

- **AI analyst: deterministic with no LLM** — `docs/ai_analyst.md` L6-L7

~~~~text
provider-agnostic and grounded: with no LLM configured it returns deterministic,
evidence-only answers, so there is **no hallucinated intelligence**.
~~~~

- **Default none needs no secrets; failures degrade** — `docs/ai_analyst.md` L101-L102

~~~~text
- Provider credentials only from environment; default `none` needs no secrets.
- Provider failures degrade to the deterministic generator (no hard dependency).
~~~~

- **Config comment (code)** — `backend/app/config.py` L58-L59

~~~~text
    # AI Threat Analyst (Phase 13). No provider lock-in; "none" -> deterministic
    # evidence-grounded responses (works with zero LLM credentials).
~~~~

- **Env template** — `.env.example` L61-L62

~~~~text
# Provider: none | gemini | openai | ollama. "none" => deterministic answers
# grounded in evidence (no LLM credentials required).
~~~~

- **Phases 15-17 are deterministic/rule-based** — `docs/phases_15_17.md` L3-L4

~~~~text
All three layers are deterministic, explainable, auditable, and built on real
platform data (Wazuh, Neo4j/GDS, MISP, CVE/EPSS/KEV, ML risk). New tables:
~~~~


Safe website wording: "Every stage runs deterministically with no LLM. An LLM (Gemini, OpenAI or Ollama) is optional and only narrates evidence that has already been gathered. The default is `AI_PROVIDER=none`."

---

## 13. Status, phase, deployment mode, counts

### Status / phase

- **Current status** — `README.md` L5

~~~~text
**Current status: Phase 19 — human-in-the-loop response (approval-gated).** The final engineering phase adds evidence-based **response recommendations** (derived from agent investigations) that an analyst must **approve** before they execute — only through the existing **ShuffleProvider** — followed by verification and a complete **audit trail**. Nothing executes automatically: attempting to execute an unapproved recommendation returns HTTP 409. Lightweight and reuse-only (2 tables, 1 migration, 1 module, 5 pages, existing SOAR framework). A 69-page dashboard adds 5 response pages. See [docs/response_approval.md](docs/response_approval.md). Every earlier phase (collectors → correlation → risk V6 → graph/GDS → AI/agentic analyst → orchestration) remains in place.
~~~~

- **Roadmap (Phases 1-19 + Future)** — `README.md` L502-L525

~~~~text
## Roadmap

- **Phase 1 (done):** project foundation, environment, API skeleton, PostgreSQL
- **Phase 2.1 (done):** Technique ORM model, table creation, first database-backed endpoint
- **Phase 2.2 (done):** Pydantic schemas, dependency-injected routes, MITRE ATT&CK STIX collector + ingestion
- **Phase 3 (done):** CVE model + schemas, NVD collector (incremental, paginated), CVE endpoints with filtering/search/stats
- **Phase 4 (done):** rule-based ATT&CK↔CVE correlation engine (confidence scoring, evidence), correlation endpoints + stats
- **Phase 5 (done):** ML threat risk scoring (XGBoost, weak supervision), risk-score endpoints + stats, feature importance & explainability
- **Phase 6 (done):** Streamlit threat-intelligence dashboard
- **Phase 7 (designed, not built):** Neo4j knowledge graph — see [docs/neo4j_design.md](docs/neo4j_design.md)
- **Phase 8 (done):** EPSS + CISA KEV integration, Priority Engine v2, SOC enrichment layer (Wazuh-ready), 4 new dashboard pages
- **Phase 8.x (done):** Alembic migration system (schema now migration-owned; see [docs/migrations.md](docs/migrations.md)); ML Risk Scoring **V2** with EPSS/KEV features
- **Phase 9 (done):** MISP integration (events, IOCs, actors, malware, campaigns), enrichment engine, ML Risk Scoring **V3** with MISP actor-attribution features, 6 new dashboard pages
- **Phase 10 (done):** Wazuh SOC integration — agents/alerts ingestion, alert enrichment engine, SOC Priority Engine (separate from Wazuh severity), ML Risk Scoring **V4** with live Wazuh telemetry, 7 new SOC dashboard pages; see [docs/wazuh_soc_architecture.md](docs/wazuh_soc_architecture.md)
- **Phase 11 (done):** Neo4j knowledge graph — Docker deployment, PostgreSQL→Neo4j sync engine, graph analytics + investigation workflows, 8 graph APIs, 5 graph dashboard pages; see [docs/graph_schema.md](docs/graph_schema.md)
- **Phase 12 (done):** Neo4j GDS analytics (centrality/communities/similarity), graph intelligence + attack-path engines, ML Risk Scoring **V5** with graph-topology features, 9 graph-analytics APIs, 6 dashboard pages; see [docs/graph_analytics.md](docs/graph_analytics.md)
- **Phase 13 (done):** AI Threat Analyst — provider-agnostic LLM abstraction (Gemini/OpenAI/Ollama), rule-based query routing, vetted-template Cypher safety, multi-source evidence engine, explainable grounded answers, multi-turn memory, 7 AI APIs, 5 AI dashboard pages; see [docs/ai_analyst.md](docs/ai_analyst.md)
- **Phase 14 (done):** Agentic SOC Analyst — planner/executor over 12 vetted tools, autonomous investigations (alert/cve/actor/campaign/community), graph-driven blast radius, evidence-cited risk explanation + remediation, exportable reports with persisted lineage, 9 agent APIs, 5 agent dashboard pages; see [docs/agentic_soc.md](docs/agentic_soc.md)
- **Phases 15–17 (done):** autonomous triage + SOC/CTI reporting + ticketing connectors; GDS graph embeddings + link prediction + **ML Risk Scoring V6**; ATT&CK detection-gap analysis + prioritized backlog; 3 tables, 15 APIs, 14 dashboard pages; see [docs/phases_15_17.md](docs/phases_15_17.md)
- **Phase 18 (done):** APScheduler orchestration — 18 scheduled jobs, dependency-ordered pipeline, execution history + retry/backoff + idempotency, autonomous investigation rules, ticketing/SOAR abstraction (Mock/Jira/TheHive/Shuffle-webhook), monitoring; 1 table, 7 APIs, 6 dashboard pages; see [docs/orchestration.md](docs/orchestration.md)
- **Phase 19 (done):** human-in-the-loop response — evidence-based recommendations, mandatory analyst approval gate, execution via existing ShuffleProvider, verification, complete audit trail; 2 tables, 1 module, 9 APIs, 5 dashboard pages; see [docs/response_approval.md](docs/response_approval.md)
- **Future:** temporal coverage/risk trends, fully-supervised risk labels (KEV/EPSS ground truth), more feeds (OTX, AbuseIPDB), live Shuffle playbooks for approved actions
- **Phase 3:** enrichment pipeline, Streamlit dashboard
- **Phase 4:** ML scoring, MISP / Neo4j / LLM integrations
~~~~

- **Phase 19 called 'the final engineering phase'** — `docs/response_approval.md` L3

~~~~text
The final engineering phase. Turns evidence-based agent recommendations into
~~~~


### Deployment mode (local, Docker for data stores)

- **Prerequisites** — `README.md` L74-L78

~~~~text
## Prerequisites

- Python 3.11+ (3.14 tested)
- Docker Desktop with Docker Compose v2+
- Git
~~~~

- **Services: PostgreSQL in Docker, API via uvicorn on localhost** — `README.md` L126-L132

~~~~text
## Starting Services

| Service | Command | URL |
|---|---|---|
| PostgreSQL | `docker compose up -d` | `localhost:5432` |
| FastAPI (dev) | `.\scripts\start_api.ps1` or `uvicorn backend.app.main:app --reload` | http://127.0.0.1:8000 |
| API docs | starts with the API | http://127.0.0.1:8000/docs |
~~~~

- **Tech stack table** — `README.md` L9-L17

~~~~text
## Tech Stack

| Layer | Technology |
|---|---|
| API | FastAPI + Uvicorn |
| Database | PostgreSQL 16 (Docker) |
| ORM / Migrations | SQLAlchemy 2.x / Alembic (schema owned by migrations) |
| Dashboard (later phase) | Streamlit |
| Data processing | Pandas |
~~~~

- **docker-compose: only postgres + neo4j services** — `docker-compose.yml` L1-L4

~~~~text
services:
  postgres:
    image: postgres:16-alpine
    container_name: cti_postgres
~~~~

- **Neo4j Docker service** — `README.md` L376-L377

~~~~text
Neo4j runs as a Docker service (`docker compose up -d neo4j`; Browser at
http://localhost:7474, Bolt on 7687). Project the PostgreSQL data into the graph:
~~~~

- **Orchestration deployment (opt-in)** — `docs/orchestration.md` L85-L90

~~~~text
## Deployment

Set `ORCHESTRATION_ENABLED=true` (+ `.env` credentials for live collectors/SOAR) to
start the in-process APScheduler on API boot. For dev/tests it stays off so nothing
auto-runs. Cron/systemd can alternatively invoke `python -m` collectors + the
pipeline API. Everything is observable via `/pipeline/*` and the 6 dashboard pages.
~~~~

- **Dashboard run + API URL** — `README.md` L486-L492

~~~~text
```powershell
# With the API running (uvicorn ...):
streamlit run dashboard/app.py
```

It targets `http://127.0.0.1:8000` by default; set `CTI_API_URL` to point
elsewhere. Charts are rendered with Plotly and results are cached for fast loads.
~~~~


Summary: local development setup. PostgreSQL 16 and Neo4j 5 community (with GDS) run in Docker Compose. The FastAPI API runs with uvicorn on `127.0.0.1:8000`, and the Streamlit dashboard runs locally. A Windows quick-start script is provided. **No cloud deployment or Kubernetes appears anywhere in the repo.**

### Counts (each with its quote)

- **12 tools** — `README.md` L434

~~~~text
The agent acts only through a 12-tool read-only registry over existing services;
~~~~

- **18 scheduled jobs (README)** — `README.md` L461-L462

~~~~text
Set `ORCHESTRATION_ENABLED=true` to start the APScheduler cron pipeline on API
boot (18 production schedules). Jobs are idempotent, retried with backoff, and
~~~~

- **18 jobs (doc)** — `docs/orchestration.md` L47

~~~~text
(15 spec schedules + `graph_intelligence` and `attack_paths` = 18 jobs total.)
~~~~

- **JOB_REGISTRY — 18 entries (code)** — `backend/app/orchestration/jobs.py` L132-L152

~~~~text
# job_name -> (callable, job_type, description, cron)
JOB_REGISTRY = {
    "wazuh_sync": (lambda: _run_collector("collectors.wazuh"), "collector", "Wazuh agents+alerts", {"minute": "*/15"}),
    "misp_sync": (lambda: _run_collector("collectors.misp"), "collector", "MISP intel", {"minute": "*/30"}),
    "epss_sync": (lambda: _run_collector("collectors.epss"), "collector", "EPSS scores", {"hour": 1, "minute": 0}),
    "kev_sync": (lambda: _run_collector("collectors.cisa_kev"), "collector", "CISA KEV", {"hour": 1, "minute": 15}),
    "nvd_sync": (lambda: _run_collector("collectors.nvd_cve"), "collector", "NVD CVEs", {"hour": 2, "minute": 0}),
    "mitre_sync": (lambda: _run_collector("collectors.mitre_attack"), "collector", "MITRE ATT&CK", {"day_of_week": "sun", "hour": 3}),
    "correlation": (_correlation, "analytics", "ATT&CK<->CVE correlation", {"hour": 3, "minute": 15}),
    "graph_sync": (_graph_sync, "graph", "PostgreSQL->Neo4j sync", {"hour": 3, "minute": 30}),
    "graph_analytics": (_graph_analytics, "graph", "GDS centrality/communities", {"hour": 4, "minute": 0}),
    "graph_intelligence": (_graph_intelligence, "graph", "Graph insights", {"hour": 4, "minute": 15}),
    "embeddings": (_embeddings, "graph", "FastRP embeddings", {"hour": 4, "minute": 30}),
    "link_prediction": (_link_prediction, "ml", "Link prediction", {"hour": 5, "minute": 0}),
    "coverage": (_coverage, "analytics", "ATT&CK coverage", {"hour": 5, "minute": 30}),
    "attack_paths": (_attack_paths, "graph", "Attack-path metadata", {"hour": 5, "minute": 45}),
    "risk_scoring": (_risk_scoring, "ml", "ML Risk Scoring V6", {"hour": 6, "minute": 0}),
    "autonomous_triage": (_autonomous_triage, "soc", "Autonomous investigation rules", {"hour": 6, "minute": 30}),
    "daily_briefing": (_daily_briefing, "reporting", "SOC daily briefing", {"hour": 8, "minute": 0}),
    "weekly_cti": (_weekly_cti, "reporting", "Executive CTI report", {"day_of_week": "mon", "hour": 9}),
}
~~~~

- **69-page dashboard (README)** — `README.md` L482-L484

~~~~text
A 69-page Streamlit dashboard — the 64 earlier pages plus five response pages
(**Response Recommendations, Approval Queue, Action Execution Center, Response
Audit Trail, SOAR Response Center**) — that reads only from the REST API:
~~~~

- **PAGES list — 69 entries (code)** — `dashboard/app.py` L129-L199

~~~~text
PAGES = [
    "Executive Overview",
    "Threat Intelligence Overview",
    "Risk Analysis",
    "ATT&CK Analysis",
    "CVE Analysis",
    "Correlation Explorer",
    "EPSS Analysis",
    "KEV Analysis",
    "Threat Prioritization",
    "SOC Readiness",
    "MISP Intelligence Overview",
    "Threat Actors",
    "Malware Analysis",
    "IOC Explorer",
    "Campaign Explorer",
    "Threat Intelligence Relationships",
    "SOC Overview",
    "Live Alerts",
    "Threat-Enriched Alerts",
    "Threat Actor Activity",
    "Malware Activity",
    "Campaign Activity",
    "Priority Queue",
    "Knowledge Graph Overview",
    "Threat Actor Graph",
    "Campaign Graph",
    "Alert Investigation Graph",
    "CVE Relationship Graph",
    "Graph Intelligence Center",
    "Attack Path Explorer",
    "Threat Actor Influence",
    "Campaign Communities",
    "High-Risk CVEs",
    "Graph-Based Risk Analysis",
    "AI Threat Analyst",
    "Investigation Assistant",
    "Attack Path Investigator",
    "Threat Actor Investigator",
    "AI Risk Advisor",
    "Agentic SOC Analyst",
    "Autonomous Investigations",
    "Blast Radius Explorer",
    "Risk Explanation Center",
    "Investigation Reports",
    "SOC Briefings",
    "CTI Reports",
    "Investigation History",
    "Autonomous Triage Center",
    "Predictive Intelligence Center",
    "Predicted Threat Actors",
    "Predicted CVEs",
    "Emerging Campaigns",
    "Graph Embedding Explorer",
    "ATT&CK Coverage Center",
    "Detection Gap Explorer",
    "Coverage Heatmaps",
    "Coverage Trends",
    "Detection Engineering Advisor",
    "Pipeline Operations Center",
    "Scheduler Dashboard",
    "Pipeline History",
    "Job Monitoring",
    "Autonomous Operations Center",
    "SOAR Integration Center",
    "Response Recommendations",
    "Approval Queue",
    "Action Execution Center",
    "Response Audit Trail",
    "SOAR Response Center",
]
~~~~

- **Per-phase API/page/table counts (roadmap)** — `README.md` L516-L522

~~~~text
- **Phase 11 (done):** Neo4j knowledge graph — Docker deployment, PostgreSQL→Neo4j sync engine, graph analytics + investigation workflows, 8 graph APIs, 5 graph dashboard pages; see [docs/graph_schema.md](docs/graph_schema.md)
- **Phase 12 (done):** Neo4j GDS analytics (centrality/communities/similarity), graph intelligence + attack-path engines, ML Risk Scoring **V5** with graph-topology features, 9 graph-analytics APIs, 6 dashboard pages; see [docs/graph_analytics.md](docs/graph_analytics.md)
- **Phase 13 (done):** AI Threat Analyst — provider-agnostic LLM abstraction (Gemini/OpenAI/Ollama), rule-based query routing, vetted-template Cypher safety, multi-source evidence engine, explainable grounded answers, multi-turn memory, 7 AI APIs, 5 AI dashboard pages; see [docs/ai_analyst.md](docs/ai_analyst.md)
- **Phase 14 (done):** Agentic SOC Analyst — planner/executor over 12 vetted tools, autonomous investigations (alert/cve/actor/campaign/community), graph-driven blast radius, evidence-cited risk explanation + remediation, exportable reports with persisted lineage, 9 agent APIs, 5 agent dashboard pages; see [docs/agentic_soc.md](docs/agentic_soc.md)
- **Phases 15–17 (done):** autonomous triage + SOC/CTI reporting + ticketing connectors; GDS graph embeddings + link prediction + **ML Risk Scoring V6**; ATT&CK detection-gap analysis + prioritized backlog; 3 tables, 15 APIs, 14 dashboard pages; see [docs/phases_15_17.md](docs/phases_15_17.md)
- **Phase 18 (done):** APScheduler orchestration — 18 scheduled jobs, dependency-ordered pipeline, execution history + retry/backoff + idempotency, autonomous investigation rules, ticketing/SOAR abstraction (Mock/Jira/TheHive/Shuffle-webhook), monitoring; 1 table, 7 APIs, 6 dashboard pages; see [docs/orchestration.md](docs/orchestration.md)
- **Phase 19 (done):** human-in-the-loop response — evidence-based recommendations, mandatory analyst approval gate, execution via existing ShuffleProvider, verification, complete audit trail; 2 tables, 1 module, 9 APIs, 5 dashboard pages; see [docs/response_approval.md](docs/response_approval.md)
~~~~

- **Phase 19 lightweight counts** — `docs/response_approval.md` L67

~~~~text
- **Lightweight** — 2 tables, 1 migration, 1 backend module, 5 dashboard pages.
~~~~

- **Phases 15-17 new tables** — `docs/phases_15_17.md` L4-L5

~~~~text
platform data (Wazuh, Neo4j/GDS, MISP, CVE/EPSS/KEV, ML risk). New tables:
`scheduled_reports`, `predicted_relationships`, `coverage_scores`.
~~~~

- **Graph scale** — `docs/graph_analytics.md` L13

~~~~text
 │ 4,980 nodes / 4,116 rels  │   │ analytics.py  (GDS)            │   │ graph_metrics       │
~~~~

- **MISP counts come from fixture** — `README.md` L7

~~~~text
> **MISP note:** the production connector uses PyMISP against a live MISP instance via `MISP_URL`/`MISP_API_KEY`. With no instance available, an offline **sample fixture** (`collectors/fixtures/sample_misp_events.json`) drives the same parser/pipeline so the full flow can be exercised; the MISP counts below come from that fixture.
~~~~

- **EPSS/KEV collector scale** — `README.md` L301-L302

~~~~text
python -m collectors.epss        # FIRST EPSS scores (daily CSV, ~2,580 matched)
python -m collectors.cisa_kev    # CISA KEV catalog (~1,619 entries)
~~~~

- **Autonomous investigation rules** — `docs/orchestration.md` L72-L78

~~~~text
## Autonomous investigation rules (18.5)

| Condition | Action |
|---|---|
| Wazuh level ≥ 10, new KEV, EPSS ≥ 0.80, predicted conf > 0.80, new actors/campaigns, critical gaps | **AUTO** investigate (agent) |
| Wazuh level 7–9, EPSS 0.50–0.79 | **QUEUE** (stored in `investigation_queue` report) |
| Wazuh level ≤ 6, EPSS < 0.50 | **IGNORE** (counted) |
~~~~


**Total API endpoint count:** no doc states one. My own count from the code is 115 `@router` route decorators across 19 router modules, plus the root `GET /`. If the site shows a number, label it as counted from code, or leave it out.

**Test count:** no doc states one. My count is 203 `def test_` functions across 18 files in `tests/`. Label it as counted if used.

---

## 14. Discrepancies between files (note before publishing any number)

| Topic | Value A (source) | Value B (source) | Recommendation |
|---|---|---|---|
| Dashboard pages | "Streamlit dashboard (6 pages)" (README.md L53, project-structure tree, stale from Phase 6) | "A 69-page Streamlit dashboard" (README.md L482); 69 entries in `PAGES` (dashboard/app.py L129-199) | Use **69** |
| Phase 19 API count | "9 APIs" (README.md L522) | 10 route decorators in `backend/app/routers/response.py`; docs/response_approval.md L48-50 lists 10 paths | Avoid a number, or say "10 endpoints (from code)" |
| Phases 15-17 API count | "15 APIs" (README.md L520) | 16 route decorators (reports 6 + predictions 5 + coverage 5) | Avoid the number |
| Alert investigation steps | "agent.investigate_alert (Phase 14, 9-step)" (docs/phases_15_17.md L10) | 8 tool steps in the planner diagram (docs/agentic_soc.md L43-50) and `planner.py` L18-27 | Say "8 tool steps (then blast radius + report)", or avoid the number |
| V4 feature count | "V4 features (34)  +  GRAPH_COLUMNS (11)" (docs/graph_analytics.md L65) | V4 = 23 and V5 = 34 in code / metrics_v4.json (23) / metrics_v5.json (34) | Use code values: V4 23, V5 34, V6 39 |
| Default training version | "train V2 (EPSS + KEV enriched) - the default" (ml/train.py L3 docstring); README says it "defaults to V3" (L342) and "defaults to V4" (L368) | `default="v6"` (ml/train.py L68) | Say "V6 is the current default" |
| Neo4j status | "Status: DESIGN ONLY. Nothing in this document is implemented." (docs/neo4j_design.md L3) and README L57 "(not implemented)" | Implemented in Phase 11/12 (docs/graph_schema.md, docs/graph_analytics.md, docker-compose.yml) | Treat neo4j_design.md as a historical design doc |
| Wazuh status | "Status: FOUNDATION ONLY. No live Wazuh instance is deployed" (docs/wazuh_integration.md L3) | Phase 10 connector + enrichment (docs/wazuh_soc_architecture.md) | Treat wazuh_integration.md as historical |
| README tech stack / roadmap tail | Tech stack table lists only FastAPI, PostgreSQL, SQLAlchemy, Streamlit, Pandas (L11-17); roadmap ends with stale "Phase 3/Phase 4" lines (L524-525) | Neo4j, GDS, XGBoost, APScheduler, etc. used elsewhere | Build the stack list from the phase sections, not the table |
| ML metrics committed | "models/ ... persisted model + metrics (gitignored)" (README.md L51) | `ml/models/metrics*.json` are committed in the repo | Minor; metrics JSON can be cited |
| V6 top-feature note | "cve_degree (graph_similarity + community_influence added)" (docs/phases_15_17.md L41) | metrics_v6.json: cve_degree 0.6953, graph_similarity 0.0656 (#4), community_influence 0.0021 | Don't say community_influence is a major driver |

---

## 15. Code-level observations (true in code but NOT stated in the docs; use with a "from code" label or skip)

- The rule base has 19 rules, each for a distinct technique. The shipped rules never produce multi-rule noisy-OR or LOW confidence (see section 3).
- A KEV-listed CVE's priority is always >= 90 (see section 4d).
- In `build_features_v5`, `connected_entities` is filled with the same value as `cve_degree` (`ml/feature_engineering.py` L490-492). The V5 "top two features" (`cve_degree` 0.39, `connected_entities` 0.29) are therefore the same signal counted twice. **Do not present the two as independent drivers.**
- Only 2 vetted Cypher templates exist (`CYPHER_TEMPLATES`). Other graph access goes through parameterized service functions.
- Verification confirms that the provider accepted the action, not that remediation took effect (section 10).
- The FastAPI backend has no authentication or authorization layer (section 9).
- The response audit FK uses `ondelete="CASCADE"` (section 11).

---

## 16. Sigma LLM project (Domain-Tuned LLM for Sigma Detection Rules, QLoRA)

**No such repository exists on GitHub user PushkarSingh-26.** On 2026-09-11 the user had 18 public repos: Churn_Analysis (fork), Coding-Assistant (fork), cyber-threat-intelligence-platform, End-to-end-Medical-Chatbot-Generative-AI (fork), nextus-automation (fork), Profile_pushkar, Rag-resume-chatbot, SneakerHub-Amplify (fork), spring-petclinic (fork), stock-market-pred-using-LSTM-NLP, stockpredyfinance, test, thapar, thapar_new, todo, Vectorless-RAG-Locally-, vite-amplified-main, YFinance-Stockbot (fork). No name or description contains sigma, qlora or lora. A GitHub search (`user:PushkarSingh-26` with `in:name,description,readme`) returned 0 hits for "sigma", "qlora" and "lora". "llm" matched only Rag-resume-chatbot and this CTI platform, and "detection" matched only this CTI platform. The CTI platform repo itself never mentions Sigma, QLoRA or fine-tuning. **Nothing about the Sigma or QLoRA project can be verified from GitHub.** `content/sources/sigma-llm/` was not created.

---

## 17. Files downloaded (all under `C:\Portfolio\content\sources\aegisai\`)

README.md; .env.example; docker-compose.yml; docs/{agentic_soc, ai_analyst, graph_analytics, graph_schema, migrations, neo4j_design, orchestration, phases_15_17, response_approval, wazuh_integration, wazuh_soc_architecture}.md; collectors/wazuh.py; collectors/fixtures/{sample_wazuh.json, sample_misp_events.json}; backend/app/{main.py, config.py, response_engine.py}; backend/app/correlation/{rules.py, engine.py}; backend/app/prioritization/engine.py; backend/app/models/{priority, response, wazuh, agent}.py; backend/app/routers/{priority, response, agent, ai}.py; backend/app/agents/{__init__, agent, blast_radius, executor, memory, planner, report_generator, tools}.py; backend/app/ai/{__init__, analyst, investigation_engine, prompt_templates, providers, query_router, response_generator}.py; backend/app/ticketing/{__init__, providers, service}.py; backend/app/graph/{analytics, attack_paths, services}.py; backend/app/predictions/{embeddings, link_prediction}.py; backend/app/orchestration/{executor, jobs, rules, scheduler}.py; backend/app/reporting/triage.py; backend/app/soc/enrichment.py; backend/app/wazuh_enrichment/engine.py; ml/{risk_model, feature_engineering, train, inference, explainability}.py; ml/models/metrics{,_v1.._v6}.json; dashboard/app.py (89 KB); alembic/versions/0f8ef0cf8739_response_recommendations.py; tests/{test_correlations, test_phase13, test_phase14, test_phase18, test_phase19, test_risk_scores}.py.

Nothing was skipped for size. The largest file is dashboard/app.py at 89,004 bytes. The repo has no `backend/app/response/` directory. The response code is `backend/app/response_engine.py` plus `backend/app/ticketing/`.
