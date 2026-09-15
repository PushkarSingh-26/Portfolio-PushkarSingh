# Phase 12 — Graph Analytics & ML Risk Scoring V5

Turns the Neo4j knowledge graph into measurable intelligence (GDS centrality,
communities, attack paths) and feeds graph-derived features into **ML Risk
Scoring V5**. Everything is computed from the real graph; results are cached in
PostgreSQL (`graph_metrics`, `graph_insights`) for reuse by APIs and ML.

## Graph intelligence architecture

```
   Neo4j graph (real data)              backend/app/graph/                PostgreSQL cache
 ┌──────────────────────────┐   ┌───────────────────────────────┐   ┌────────────────────┐
 │ 4,980 nodes / 4,116 rels  │   │ analytics.py  (GDS)            │   │ graph_metrics       │
 │  GDS plugin 2.13          │──▶│  project → degree/pagerank/    │──▶│  (per-entity        │
 │  bolt :7687               │   │  betweenness/louvain/wcc/sim   │   │   centrality,       │
 └──────────────────────────┘   ├───────────────────────────────┤   │   community)        │
                                 │ intelligence.py  → insights    │──▶│ graph_insights      │
                                 │ attack_paths.py  → path meta   │──▶│  (findings + paths) │
                                 └───────────────┬───────────────┘   └─────────┬──────────┘
                                                 │ services / routers/graph.py  │ read
                                                 ▼                              ▼
                                       GET /graph/* APIs            ml/ build_features_v5 → V5 model
```

Run order (after a graph sync): `python -m backend.app.graph.analytics` →
`python -m backend.app.graph.intelligence` → `python -m backend.app.graph.attack_paths`.

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

## Graph analytics workflow diagram

```
 graph_sync ─▶ analytics (GDS) ─▶ graph_metrics ─┬─▶ intelligence ─▶ graph_insights
                                                  ├─▶ attack_paths ─▶ graph_insights
                                                  └─▶ build_features_v5 ─▶ ML Risk V5 ─▶ risk_scores
```

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

## Performance notes

- GDS runs on an in-memory projection (`gds.graph.project`, UNDIRECTED) dropped
  after each run; full analytics over ~5k nodes / ~4k edges completes in seconds.
- Metrics/insights are cached in PostgreSQL, so the `/graph/metrics`,
  `/graph/insights`, `/graph/top-*` APIs and ML V5 read without touching Neo4j.
- Attack-path queries are bounded (`LIMIT`); hub nodes are dense (APT28 betweenness
  ≈ 2.0M), so analytics-on-write + cache-on-read keeps request latency low.
