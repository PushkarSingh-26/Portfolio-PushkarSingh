# Phase 11 — Neo4j Knowledge Graph

A live Neo4j property graph projected from PostgreSQL (the system of record).
The graph is rebuildable at any time via the sync engine; PostgreSQL remains
authoritative.

## Neo4j architecture

```
            PostgreSQL (system of record)                     Neo4j (projection)
 ┌───────────────────────────────────────────┐      ┌──────────────────────────────┐
 │ techniques · cves · correlation_results     │      │ cti_neo4j (Docker)           │
 │ risk_scores · epss · kev · threat_actors    │      │   bolt  :7687                │
 │ malware · campaigns · ioc_indicators        │─────▶│   http  :7474 (Browser)      │
 │ cti_relationships · wazuh_agents/alerts/...  │      │   constraints: 1 per label   │
 └───────────────────────────────────────────┘      └───────────────┬──────────────┘
                  │  backend/app/graph/graph_sync.py                  │
                  │  • ensure_constraints()                            │ Cypher (Bolt)
                  │  • sync_nodes()  (MERGE, batched UNWIND)           ▼
                  │  • sync_relationships()                ┌──────────────────────────┐
                  └───────────────────────────────────────│ services.py  (analytics +  │
   credentials via ENV: NEO4J_URI / USERNAME / PASSWORD   │ investigation workflows)   │
                                                          │ routers/graph.py  (REST)   │
                                                          └──────────────────────────┘
```

Run the sync: `python -m backend.app.graph.graph_sync` (full) or `--since <ts>`
(incremental for alerts/risk). It is idempotent (MERGE on PostgreSQL ids).

## Knowledge-graph ER diagram (schema)

```
                         ┌────────────┐  OBSERVED_ON   ┌────────────┐
                         │   Alert    │───────────────▶│   Agent    │
                         └─────┬──────┘                └────────────┘
              USES_TECHNIQUE   │      PRIORITIZED_AS ┌────────────┐
                         ┌─────▼──────┐──────────────▶│ RiskScore  │◀── HAS_RISK ──┐
                         │ Technique  │               └────────────┘               │
                         └─────┬──────┘                                            │
              CORRELATED_TO    │                                                   │
                         ┌─────▼──────┐  ATTRIBUTED_TO  ┌────────────┐             │
                         │    CVE     │────────────────▶│ThreatActor │             │
                         └─────┬──────┘                 └─────┬──────┘             │
                               └───────────── HAS_RISK ───────┼────────────────────┘
                                                  USES  ┌─────▼──────┐  RUNS  ┌────────────┐
                                                        │  Malware   │        │  Campaign  │
                                                        └────────────┘        └─────┬──────┘
                                                              ▲ (ThreatActor)─USES   │ USES_IOC
                                                                                ┌────▼─────┐
                                                                                │   IOC    │
                                                                                └──────────┘
```

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

## API summary

| Endpoint | Purpose |
|---|---|
| `GET /graph/stats` | node/relationship counts + degree statistics |
| `GET /graph/top-entities?label=&limit=` | most-connected nodes (by degree) |
| `GET /graph/alert/{id}` | alert investigation subgraph |
| `GET /graph/cve/{id}` | CVE relationship subgraph |
| `GET /graph/actor/{id}` | threat-actor ecosystem subgraph |
| `GET /graph/campaign/{id}` | campaign ecosystem subgraph |
| `GET /graph/malware/{id}` | malware subgraph |
| `GET /graph/path?from_type&from_key&to_type&to_key` | shortest path between entities |

## Performance notes

- Uniqueness constraints (one per label) back-index every MERGE key, so sync and
  lookups are O(log n) rather than scans.
- Sync uses batched `UNWIND $rows` writes (1,000 rows/tx) — the full projection
  (~5k nodes, ~4k relationships) syncs in a few seconds.
- Investigation queries are bounded (`LIMIT`/`cap`) because hub nodes are dense
  (e.g. APT28 has graph degree ~620); the dashboard further caps rendered nodes.
- The graph fits comfortably in memory at current scale; a single Neo4j
  community instance is sufficient for the foreseeable roadmap.
