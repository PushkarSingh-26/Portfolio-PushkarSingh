# Cyber Threat Intelligence Platform

A platform for collecting, enriching, analyzing, and serving cyber threat intelligence.

**Current status: Phase 19 — human-in-the-loop response (approval-gated).** The final engineering phase adds evidence-based **response recommendations** (derived from agent investigations) that an analyst must **approve** before they execute — only through the existing **ShuffleProvider** — followed by verification and a complete **audit trail**. Nothing executes automatically: attempting to execute an unapproved recommendation returns HTTP 409. Lightweight and reuse-only (2 tables, 1 migration, 1 module, 5 pages, existing SOAR framework). A 69-page dashboard adds 5 response pages. See [docs/response_approval.md](docs/response_approval.md). Every earlier phase (collectors → correlation → risk V6 → graph/GDS → AI/agentic analyst → orchestration) remains in place.

> **MISP note:** the production connector uses PyMISP against a live MISP instance via `MISP_URL`/`MISP_API_KEY`. With no instance available, an offline **sample fixture** (`collectors/fixtures/sample_misp_events.json`) drives the same parser/pipeline so the full flow can be exercised; the MISP counts below come from that fixture.

## Tech Stack

| Layer | Technology |
|---|---|
| API | FastAPI + Uvicorn |
| Database | PostgreSQL 16 (Docker) |
| ORM / Migrations | SQLAlchemy 2.x / Alembic (schema owned by migrations) |
| Dashboard (later phase) | Streamlit |
| Data processing | Pandas |

## Project Structure

```
cyber-threat-intelligence-platform/
├── backend/
│   └── app/
│       ├── main.py          # FastAPI application entry point
│       ├── config.py        # Settings loaded from .env
│       ├── database.py      # SQLAlchemy engine, sessions, Base
│       ├── models/          # ORM models (Technique, CVE, CorrelationResult, RiskScore, EPSSScore, KEVEntry, PriorityScore)
│       ├── schemas/         # Pydantic schemas for every resource
│       ├── correlation/     # Rule base + correlation engine
│       ├── prioritization/  # Priority Engine v2 (signal blend + explanation)
│       ├── enrichment/      # CTI enrichment engine (MISP entity relationships)
│       ├── soc/             # SOC enrichment service (Wazuh-readiness foundation)
│       └── routers/         # API routers (… epss, kev, priority, soc, misp)
├── collectors/
│   ├── mitre_attack.py      # MITRE ATT&CK STIX collector
│   ├── nvd_cve.py           # NVD CVE collector
│   ├── correlate.py         # ATT&CK <-> CVE correlation runner
│   ├── epss.py              # FIRST EPSS collector
│   ├── cisa_kev.py          # CISA KEV catalog collector
│   ├── prioritize.py        # Priority Engine v2 runner
│   ├── misp.py              # MISP connector (PyMISP + offline sample loader)
│   ├── wazuh.py             # Wazuh connector (Manager API + indexer + sample loader)
│   └── (graph sync: python -m backend.app.graph.graph_sync)
│   └── fixtures/            # sample_misp_events.json (offline verification)
├── ml/                      # Risk-scoring ML pipeline
│   ├── feature_engineering.py   # features + weak-supervision labels
│   ├── risk_model.py            # model factory (XGBoost/RF), persistence
│   ├── train.py / inference.py  # train model / score CVEs
│   ├── evaluation.py / explainability.py
│   └── models/                  # persisted model + metrics (gitignored)
├── dashboard/
│   └── app.py               # Streamlit dashboard (6 pages)
├── alembic/                 # Alembic migration environment + versions/
├── alembic.ini              # Alembic config (DB URL comes from app settings)
├── docs/
│   ├── neo4j_design.md      # Phase 7 knowledge-graph design (not implemented)
│   ├── wazuh_integration.md # Phase 8.4 Wazuh readiness design
│   └── migrations.md        # Alembic migration workflow
├── database/
│   ├── init/                # SQL run on first PostgreSQL startup
│   └── migrations/          # Alembic migrations (Phase 2)
├── dashboard/               # Streamlit dashboard (later phase)
├── ml/                      # ML components (later phase)
├── tests/                   # Test suite
├── docs/                    # Documentation
├── scripts/                 # Setup & startup scripts
├── docker-compose.yml       # PostgreSQL service
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variable template
└── README.md
```

## Prerequisites

- Python 3.11+ (3.14 tested)
- Docker Desktop with Docker Compose v2+
- Git

## Setup

### Quick start (Windows)

```powershell
.\scripts\setup_dev.ps1
```

### Manual setup

1. **Clone and enter the project**

   ```powershell
   git clone <repo-url>
   cd cyber-threat-intelligence-platform
   ```

2. **Create and activate a virtual environment**

   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1        # Windows
   # source venv/bin/activate         # Linux/macOS
   ```

3. **Install dependencies**

   ```powershell
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   ```powershell
   Copy-Item .env.example .env
   ```

   Edit `.env` and set a real `POSTGRES_PASSWORD` (and keep `DATABASE_URL` in sync). Never commit `.env`.

5. **Start PostgreSQL**

   ```powershell
   docker compose up -d
   docker compose ps          # wait until cti_postgres is "healthy"
   ```

## Starting Services

| Service | Command | URL |
|---|---|---|
| PostgreSQL | `docker compose up -d` | `localhost:5432` |
| FastAPI (dev) | `.\scripts\start_api.ps1` or `uvicorn backend.app.main:app --reload` | http://127.0.0.1:8000 |
| API docs | starts with the API | http://127.0.0.1:8000/docs |

### API endpoints

- `GET /health` — API liveness
- `GET /health/db` — database connectivity
- `GET /techniques` — list techniques; supports `?skip=`, `?limit=` (max 500), and `?search=` (case-insensitive name filter)
- `GET /techniques/{id}` — one technique by MITRE ID (`T1059`, `T1059.001`) or numeric primary key
- `GET /cves` — list CVEs (newest first); supports `?skip=`, `?limit=` (max 500), `?severity=` (LOW/MEDIUM/HIGH/CRITICAL), `?min_score=` (0–10 CVSS), and `?search=` (matches CVE ID or description)
- `GET /cves/{cve_id}` — one CVE by NVD ID (`CVE-2024-3094`) or numeric primary key
- `GET /stats/cves` — aggregate stats: total, counts by severity, average CVSS, latest published date
- `GET /correlations` — list technique↔CVE correlations (highest confidence first); supports `?skip=`, `?limit=`, `?min_confidence=` (0–1), `?confidence_level=` (LOW/MEDIUM/HIGH), `?severity=`, `?technique_id=`, `?cve_id=`, `?search=`
- `GET /correlations/{technique_id}` — all CVEs correlated to an ATT&CK technique
- `GET /correlations/cve/{cve_id}` — all ATT&CK techniques correlated to a CVE
- `GET /stats/correlations` — totals by confidence, by tactic, most-associated techniques, most-correlated CVEs, count of critical CVEs with mappings
- `GET /stats/techniques` — ATT&CK totals (parent vs sub-techniques)
- `GET /risk-scores` — list risk scores (highest first); supports `?skip=`, `?limit=`, `?risk_level=`, `?min_score=`, `?search=`
- `GET /risk-scores/top` — top-N highest-risk CVEs (optional `?risk_level=`)
- `GET /risk-scores/{cve_id}` — risk score for one CVE
- `GET /stats/risk-scores` — totals by level, average/max/min, score distribution, model version
- `GET /epss`, `/epss/top`, `/epss/{cve_id}`, `/stats/epss` — FIRST EPSS exploit-probability scores
- `GET /kev`, `/kev/in-catalog`, `/kev/{cve_id}`, `/stats/kev` — CISA Known Exploited Vulnerabilities catalog
- `GET /priority`, `/priority/top`, `/priority/{cve_id}`, `/priority/{cve_id}/explanation`, `/stats/priority` — Threat Priority Engine v2 (with per-signal breakdown)
- `GET /soc/enrich/{cve_id}`, `POST /soc/enrich`, `GET /soc/demo-alert` — SOC enrichment (Wazuh-readiness foundation)
- `GET /misp/events`, `/misp/events/{id}` — MISP events (with IOCs)
- `GET /iocs`, `/iocs/{id}` — indicators of compromise (filter by type/category/to_ids/search)
- `GET /actors`, `/actors/{id}` — threat actors (detail includes derived techniques, CVEs, malware)
- `GET /malware`, `/malware/{id}` — malware families (detail includes techniques)
- `GET /campaigns`, `/campaigns/{id}` — campaigns
- `GET /stats/misp` — MISP totals, IOC-type breakdown, threat-level breakdown, top actors/malware by relationships
- `GET /wazuh/agents`, `/wazuh/agents/{id}` — Wazuh agents (filter status, search)
- `GET /wazuh/alerts`, `/wazuh/alerts/{id}` — Wazuh alerts (filter level/agent/technique/search)
- `GET /wazuh/enriched-alerts`, `/wazuh/enriched-alerts/{id}` — alerts with full CTI enrichment + SOC priority (filter priority/KEV/actor)
- `GET /wazuh/stats` — SOC totals: alerts by severity & SOC priority, top techniques/actors/malware, KEV-linked alerts
- `GET /graph/stats` — knowledge-graph node/relationship counts + degree statistics
- `GET /graph/top-entities` — most-connected nodes (optional `?label=`)
- `GET /graph/alert/{id}`, `/graph/cve/{id}`, `/graph/actor/{id}`, `/graph/campaign/{id}`, `/graph/malware/{id}` — investigation subgraphs
- `GET /graph/path` — shortest path between any two entities (`from_type/from_key/to_type/to_key`)
- `GET /graph/metrics`, `/graph/pagerank`, `/graph/high-risk-entities` — GDS centrality metrics (filter/order/paginate)
- `GET /graph/top-threat-actors`, `/graph/top-cves`, `/graph/top-techniques` — most-influential entities by graph centrality
- `GET /graph/communities` — Louvain communities with composition
- `GET /graph/insights` — graph intelligence findings (filter by type/severity)
- `GET /graph/attack-paths` — attack paths for an alert (`?alert_id=`) or stored path insights
- `POST /ai/query` — natural-language investigation (structured, evidence-grounded answer)
- `POST /ai/chat` — multi-turn investigation with per-session memory
- `POST /ai/investigate/{alert,cve,actor,campaign,path}` — workflow investigations
- `POST /agent/investigate` + `/agent/investigate/{alert,cve,actor,campaign}` — autonomous investigations (plan → tools → blast radius → report)
- `POST /agent/blast-radius` — graph-driven impact surface for an entity
- `POST /agent/report`, `GET /agent/history`, `GET /agent/tasks` — stored reports, lineage, task graphs + tool registry
- `GET /reports`, `/reports/{id}`, `/reports/history`, `POST /reports/daily|weekly|generate` — SOC briefings, CTI reports, autonomous triage
- `GET /predictions`, `/predictions/actors|cves|campaigns|paths` — graph-embedding link predictions
- `GET /coverage`, `/coverage/techniques|tactics|gaps|recommendations` — ATT&CK detection coverage + gaps
- `GET /pipeline/jobs|history|status|health`, `POST /pipeline/run`, `/pipeline/run/{job}`, `/pipeline/retry/{job}` — orchestration + scheduling
- `GET /response/recommendations`, `/response/stats`, `/response/audit`, `POST /response/generate`, `/response/recommendations/{id}/approve|reject|execute|verify` — approval-gated response actions

### Ingesting MITRE ATT&CK data

Download the official Enterprise ATT&CK STIX bundle and upsert all active
techniques into PostgreSQL (idempotent — safe to re-run for updates):

```powershell
python -m collectors.mitre_attack
# or from a previously downloaded bundle:
python -m collectors.mitre_attack --file enterprise-attack.json
```

### Ingesting CVE data (NVD)

Download CVE records from the NVD 2.0 API and upsert them into PostgreSQL.
Re-runs are incremental: the collector asks NVD only for records modified since
the newest `last_modified_date` already stored.

```powershell
python -m collectors.nvd_cve                  # incremental (or last 30 days on first run)
python -m collectors.nvd_cve --days 7 --full  # fixed 7-day window, ignore stored state
```

NVD throttles unauthenticated clients to ~5 requests / 30s. Set `NVD_API_KEY`
in `.env` (request one at https://nvd.nist.gov/developers/request-an-api-key)
to raise the limit to ~50 and ingest much faster.

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

### Stopping services

```powershell
docker compose down            # stop PostgreSQL (data persists in the volume)
docker compose down -v         # stop AND delete all database data
```

## Development Workflow

1. Activate the venv: `.\venv\Scripts\Activate.ps1`
2. Ensure PostgreSQL is up: `docker compose up -d`
3. Run the API with auto-reload: `uvicorn backend.app.main:app --reload`
4. Make changes — the server reloads automatically.
5. Run tests: `pip install -r requirements-dev.txt` then `pytest tests/ -v`
6. Branch, commit, open a PR against `main`.

### Database migrations (Phase 2+)

Alembic is installed and `database/migrations/` is reserved for it. When models land in `backend/app/models/`, initialize with:

```powershell
alembic init database/migrations
```

### ML threat risk scoring (Phase 5)

After correlations exist, train the model and score CVEs:

```powershell
python -m ml.train        # build features, train XGBoost, persist model + metrics
python -m ml.inference    # score all correlated CVEs into the risk_scores table
python -m ml.evaluation   # held-out metrics + score/level distribution
python -m ml.explainability   # global feature importance + an example explanation
```

**Methodology — weak supervision (documented assumption).** The platform has no
observed ground truth for "risk" (no exploitation outcomes, no analyst labels).
Supervised learning on real labels is therefore not possible today. Instead we
derive a transparent **heuristic label** (a weighted blend of CVSS, correlation
confidence, ATT&CK breadth, technique centrality, and recency) and train a model
(XGBoost preferred, RandomForest fallback) to learn it. This produces a smooth,
explainable 0–100 score and — importantly — a serving pipeline whose labels can
later be replaced by real signals (**CISA KEV** known-exploited, **FIRST EPSS**
exploit probability) without changing the model or the API.

**Limitation.** Because the label is a function of the same features, held-out
regression metrics are high by construction (they confirm the model faithfully
learns the target, *not* that it predicts real-world exploitation). Treat the
score as a transparent prioritization aid, not a validated probability. Risk
levels: CRITICAL ≥ 75, HIGH ≥ 50, MEDIUM ≥ 25, LOW < 25.

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

### Real-world threat prioritization (Phase 8)

Layer EPSS exploit probabilities and the CISA KEV catalog on top, then compute
the v2 priority. All collectors are idempotent and daily-refresh friendly:

```powershell
python -m collectors.epss        # FIRST EPSS scores (daily CSV, ~2,580 matched)
python -m collectors.cisa_kev    # CISA KEV catalog (~1,619 entries)
python -m collectors.prioritize  # Priority Engine v2 over all scored CVEs
```

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

### MISP threat intelligence (Phase 9)

Ingest MISP events, IOCs, and galaxy entities (actors/malware/campaigns), then
derive the enrichment graph. Production uses PyMISP against a live instance;
the offline fixture drives the identical parser for verification:

```powershell
# Live (requires MISP_URL + MISP_API_KEY in .env):
python -m collectors.misp                 # full sync
python -m collectors.misp --since 2026-01-01   # incremental

# Offline / no MISP instance:
python -m collectors.misp --sample collectors/fixtures/sample_misp_events.json
```

Ingestion writes entities + event-membership edges, then runs the enrichment
engine ([backend/app/enrichment/engine.py](backend/app/enrichment/engine.py)),
which derives confidence-scored, **explainable** relationships: actor→technique
and malware→technique (event co-occurrence), actor→CVE (transitive
actor→technique→correlation→CVE), actor→malware, and IOC→actor/malware. Every
edge stores the evidence behind it.

**Risk Scoring V3.** `python -m ml.train` now defaults to V3, adding MISP
actor-attribution features (`misp_actor_linked`, `misp_actor_count`,
`misp_max_actor_conf`) and a label bump for actor-attributed CVEs. Impact: the
top risk feature shifts from `cvss_score` (V1) → `kev_age_days` (V2) →
`misp_actor_linked` (V3) — the model increasingly leans on real-world
exploitation evidence over static severity. Train older versions with
`--version v1|v2|v3` for comparison.

### Ingesting Wazuh SOC data (Phase 10)

Pull agents (Manager API) and alerts (OpenSearch indexer), then enrich + score:

```powershell
# Live (requires WAZUH_API_URL/USERNAME/PASSWORD + INDEXER_URL/USERNAME/PASSWORD in .env):
python -m collectors.wazuh                 # full sync (agents + alerts)
python -m collectors.wazuh --since 2026-06-01   # incremental alerts

# Offline / no Wazuh credentials:
python -m collectors.wazuh --sample collectors/fixtures/sample_wazuh.json
```

Each alert is enriched (technique → CVEs → EPSS/KEV → actor → malware/campaign)
with stored evidence, then assigned a **SOC priority** (0–100) that is *separate*
from Wazuh severity. See [docs/wazuh_soc_architecture.md](docs/wazuh_soc_architecture.md)
for the architecture and enrichment-flow diagrams.

**Risk Scoring V4.** `python -m ml.train` defaults to V4, adding live Wazuh
telemetry features (`wazuh_observed`, `wazuh_alert_count`, `wazuh_max_level`):
CVEs whose techniques are firing as alerts in the monitored estate are
escalated. The Wazuh features rank among the top signals, confirming SOC
telemetry improves risk scoring.

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

### Graph analytics & ML Risk Scoring V5 (Phase 12)

Neo4j runs the **GDS** plugin (enabled in `docker-compose.yml`). Compute
centrality/communities, derive insights and attack paths, then retrain risk:

```powershell
python -m backend.app.graph.analytics       # GDS: degree/pagerank/betweenness/louvain/wcc/similarity
python -m backend.app.graph.intelligence    # severity-tagged insights -> graph_insights
python -m backend.app.graph.attack_paths    # attack-path metadata -> graph_insights
python -m ml.train --version v5             # ML Risk Scoring V5 (graph features); then: python -m ml.inference
```

GDS metrics are cached in `graph_metrics` and insights in `graph_insights`, so the
`/graph/*` analytics APIs and ML V5 read from PostgreSQL (no live Neo4j needed at
inference). V5 adds 11 graph features; `cve_degree` and `connected_entities` become
the top risk drivers. See [docs/graph_analytics.md](docs/graph_analytics.md).

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

### Autonomous triage, predictions & coverage (Phases 15–17)

```powershell
python -m backend.app.predictions.link_prediction   # GDS embeddings + link prediction
python -m ml.train --version v6 ; python -m ml.inference   # ML Risk Scoring V6
python -m backend.app.coverage.engine               # ATT&CK detection-gap analysis
python -m backend.app.reporting.triage              # autonomous triage of critical alerts
# briefings: POST /reports/daily  |  /reports/weekly   (ticketing via TICKET_PROVIDER, default mock)
```

See [docs/phases_15_17.md](docs/phases_15_17.md) for architecture + end-to-end SOC workflow.

### Autonomous orchestration (Phase 18)

```powershell
# Run the full internal pipeline on demand (collectors excluded by default):
curl -X POST localhost:8000/pipeline/run
# Run / retry one job; inspect schedule, history, health:
curl -X POST localhost:8000/pipeline/run/coverage
curl localhost:8000/pipeline/jobs ; curl localhost:8000/pipeline/health
```

Set `ORCHESTRATION_ENABLED=true` to start the APScheduler cron pipeline on API
boot (18 production schedules). Jobs are idempotent, retried with backoff, and
recorded to `pipeline_runs`. Ticketing/SOAR via `TICKET_PROVIDER` (default mock).
See [docs/orchestration.md](docs/orchestration.md).

### Human-in-the-loop response (Phase 19)

```powershell
# Generate evidence-based recommendations from recent agent investigations:
curl -X POST localhost:8000/response/generate -d '{"limit":10}' -H "Content-Type: application/json"
# Approval gate: execute is refused (409) until an analyst approves:
curl -X POST localhost:8000/response/recommendations/1/approve -d '{"approver":"jane"}' -H "Content-Type: application/json"
curl -X POST localhost:8000/response/recommendations/1/execute -d '{"actor":"jane"}'  -H "Content-Type: application/json"
curl -X POST localhost:8000/response/recommendations/1/verify  -d '{"actor":"jane"}'  -H "Content-Type: application/json"
```

Approved actions execute through the existing `ShuffleProvider` (mock by default);
every transition is recorded in `response_audit`. See [docs/response_approval.md](docs/response_approval.md).

## Dashboard (Phase 6, extended through Phase 19)

A 69-page Streamlit dashboard — the 64 earlier pages plus five response pages
(**Response Recommendations, Approval Queue, Action Execution Center, Response
Audit Trail, SOAR Response Center**) — that reads only from the REST API:

```powershell
# With the API running (uvicorn ...):
streamlit run dashboard/app.py
```

It targets `http://127.0.0.1:8000` by default; set `CTI_API_URL` to point
elsewhere. Charts are rendered with Plotly and results are cached for fast loads.

## Troubleshooting

**Port 5432 already in use / password authentication fails from the host.**
If a native PostgreSQL service is installed on your machine (check with `Get-Service postgresql*`), it owns port 5432 and host connections will hit it instead of the Docker container. Fix: in `.env`, set `POSTGRES_PORT=5433` and change the port in `DATABASE_URL` to `5433`, then run `docker compose up -d --force-recreate`. (This is already configured in this workspace's `.env`.)

**Docker commands fail with "cannot connect to the Docker API".**
Docker Desktop is not running — start it and wait for the engine to report ready (`docker info`).

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
