# Phase 13 — AI Threat Analyst

A Tier-3 SOC/CTI analyst that answers natural-language investigation questions by
gathering **real evidence** from the platform (Neo4j graph, graph analytics,
attack paths, Wazuh alerts, MISP, CVE/EPSS/KEV, ML risk) and narrating it. It is
provider-agnostic and grounded: with no LLM configured it returns deterministic,
evidence-only answers, so there is **no hallucinated intelligence**.

## AI analyst architecture

```
  question ─▶ analyst.ask() ──────────────────────────────────────────────┐
                 │ session memory (last entities, for follow-ups)          │
                 ▼                                                          │
        query_router.route()                                               │
          • intent classify (rule-based, deterministic)                    │
          • entity extract (CVE/technique/alert regex; actor/campaign DB)  │
          • follow-up resolution from context                              │
                 ▼                                                          │
        investigation_engine.gather_evidence()  ── reads REAL sources ─────┤
          PostgreSQL · Neo4j services · graph_metrics · attack_paths       │
          risk_scores · epss · kev · correlations · wazuh enrichment       │
                 ▼                                                          │
        response_generator.generate(evidence, provider)                    │
          • provider (Gemini/OpenAI/Ollama) narrates evidence, OR          │
          • deterministic grounded summary (no LLM)                        │
                 ▼                                                          ▼
        structured AIResponse  (answer + evidence + supporting entities +
        graph relationships + risk justification + confidence + sources)
```

Files: `backend/app/ai/{providers,query_router,investigation_engine,prompt_templates,response_generator,analyst}.py`.

## LLM abstraction (no lock-in)

`AI_PROVIDER` ∈ `none | gemini | openai | ollama` selects the backend; each is
called over its REST API with `requests` (no heavy SDKs). `none` (default) uses
the deterministic generator. Keys/URLs come from the environment
(`GEMINI_API_KEY`, `OPENAI_API_KEY`/`OPENAI_BASE_URL`, `OLLAMA_URL`, `AI_MODEL`).
On any provider error the analyst falls back to the grounded summary.

## Query routing

```
 question ──▶ extract entities ──▶ classify intent ──▶ data sources
   CVE-id?  T####?  alert N?         (ordered rules)      (per-intent)
   actor/campaign name (DB match)
```
Intents: `cve_risk, actor_investigation, attack_paths_actor, recent_alert_actors,
campaigns_wazuh, dangerous_cves, top_techniques, kev_actors, triage_alerts,
top_attack_paths, alert_investigation, campaign_investigation,
technique_investigation, overview`. Each maps to a fixed set of data sources used
(reported in every answer for explainability).

## Controlled Cypher (safety)

The LLM never writes or executes Cypher. Graph access happens only through:
1. existing **parameterized** graph services, and
2. a **vetted template registry** (`CYPHER_TEMPLATES`) executed via `run_template()`,
   which rejects unknown names and runs an `is_safe_cypher()` check that blocks any
   write token (`create/merge/delete/set/remove/drop/detach/call db./load csv`).

So arbitrary or mutating graph queries are impossible by construction.

## Investigation workflows (13.6)

Alert, Threat-Actor, Campaign, CVE, Technique, and Attack-Path investigations each
gather evidence from multiple sources before answering. Example evidence chains:

```
 CVE investigation:     CVE ─▶ CVSS/EPSS/KEV ─▶ ML risk ─▶ graph PageRank ─▶ techniques ─▶ actors
 Actor investigation:   Actor ─▶ graph centrality ─▶ malware/campaigns ─▶ CVEs ─▶ reachable alerts
 Alert investigation:   Alert ─▶ enrichment ─▶ attack paths ─▶ techniques ─▶ actors ─▶ priority
```

## Evidence generation & explainability (13.7)

Every answer includes: `answer`, `risk_justification`, `supporting_entities`,
`graph_relationships`, `findings` (structured), `confidence` (0–1, scaled by
entity resolution + evidence volume), `data_sources`, and `generator`
(`deterministic` or the provider name). Nothing outside the gathered evidence is
ever asserted.

## Memory & multi-turn (13.10)

`analyst.ask(question, db, session_id)` keeps per-session memory of the last
resolved entities, so follow-ups like *"show me more about that actor"* resolve
the pronoun against the prior turn. `/ai/chat` exposes this; `/ai/query` is
single-shot.

## APIs

`POST /ai/query`, `POST /ai/chat`, `POST /ai/investigate/{alert,cve,actor,campaign,path}`
— all return the structured `AIResponse`.

## Security controls (summary)

- No arbitrary Cypher/SQL from the LLM; graph access via vetted read-only templates + write-token rejection.
- Entity extraction is regex + DB-validated (no free-text injection into queries).
- Answers grounded strictly in gathered evidence (no hallucinated CVEs/actors/scores).
- Provider credentials only from environment; default `none` needs no secrets.
- Provider failures degrade to the deterministic generator (no hard dependency).
