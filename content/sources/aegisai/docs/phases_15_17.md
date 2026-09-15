# Phases 15–17 — Autonomous Triage, Predictive Intelligence (V6), Detection Gap Analysis

All three layers are deterministic, explainable, auditable, and built on real
platform data (Wazuh, Neo4j/GDS, MISP, CVE/EPSS/KEV, ML risk). New tables:
`scheduled_reports`, `predicted_relationships`, `coverage_scores`.

## Autonomous Triage architecture (Phase 15)

```
 detect_candidates(db)            agent.investigate_alert (Phase 14, 9-step)
   critical alerts (new)  ──┐         plan → tools → blast radius → report
   high-risk CVEs          ─┼──▶ run_triage ──▶ per-alert investigations ──▶ scheduled_reports
   recent KEV              ─┘                                                 (autonomous_triage)
 briefings.daily_briefing ──▶ critical alerts · top actors · emerging risks · attack paths ·
                              high-risk communities · detection gaps  ──▶ scheduled_reports(daily)
 briefings.weekly_cti     ──▶ landscape · actor/campaign activity · CVE/risk/community trends ──▶ (weekly)
 tickets.create_ticket    ──▶ Jira | TheHive | Shuffle | mock (no creds → mock)
```
APIs: `GET /reports`, `/reports/{id}`, `/reports/history`, `POST /reports/daily|weekly|generate`.

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

### Model evolution (top risk feature by version)

| V1 | V2 | V3 | V4 | V5 | V6 |
|----|----|----|----|----|----|
| cvss_score | kev_age_days | misp_actor_linked | misp_actor_linked | cve_degree | cve_degree (graph_similarity + community_influence added) |

V6 layers predictive-intelligence features on the graph-topology model; risk is
driven by graph centrality + similarity + predicted exposure, not static CVSS.

## Detection Gap Analysis architecture (Phase 17)

```
 observed techniques (Wazuh enrichment + alert mitre)   full ATT&CK technique set
                         └──────────────┬───────────────────────┘
                                        ▼
   coverage engine: coverage % overall / by tactic / by risk band
     per-technique risk = KEV-linked + critical-linked + graph centrality
                                        ▼
   coverage_scores (per technique)  +  detection-gap detection:
     high-risk-no-alerts · KEV-not-observed · high-centrality-no-coverage
                                        ▼
   prioritized detection backlog  ──▶ graph_insights(coverage_gap)
```
APIs: `GET /coverage`, `/coverage/techniques|tactics|gaps|recommendations`.

## End-to-end SOC workflow

```
 collectors ─▶ correlate ─▶ EPSS/KEV ─▶ risk(ML) ─▶ Neo4j sync ─▶ GDS analytics ─▶ embeddings/links
      │                                                                    │
      ▼                                                                    ▼
 Wazuh alerts ─▶ enrichment + SOC priority ─▶ autonomous triage (agent) ─▶ reports/tickets
      │                                                                    │
      ▼                                                                    ▼
 coverage/gap analysis ─────────────────▶ detection backlog        AI / Agentic analyst (Q&A + investigate)
```

## Run order (after collectors + correlation + risk + graph sync + GDS analytics)

```powershell
python -m backend.app.predictions.link_prediction   # embeddings + predictions (+insights)
python -m ml.train --version v6 ; python -m ml.inference   # V6 risk with predictive features
python -m backend.app.coverage.engine               # ATT&CK coverage + gaps
python -m backend.app.reporting.triage              # autonomous triage of critical alerts
# daily/weekly briefings via POST /reports/daily | /reports/weekly
```

## Security / integrity controls

- Deterministic: FastRP uses a fixed `randomSeed`; routing/scoring are rule-based.
- Predictions exclude already-existing edges (only *new* likely links surfaced).
- Ticketing defaults to a mock provider (no credentials); real providers via env only.
- Every report/prediction/coverage row is persisted and auditable; no fabricated data.
- Backward compatible: V1–V5 models remain trainable/archived; all prior APIs unchanged.
