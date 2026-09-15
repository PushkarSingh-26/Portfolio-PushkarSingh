# Phase 7 — Neo4j Knowledge Graph: Architecture & Implementation Plan

**Status: DESIGN ONLY.** Nothing in this document is implemented. No Neo4j is
installed, no graph code exists, no containers are created, and the PostgreSQL
schema is unchanged. This is the blueprint for a future phase.

## 1. Why a graph, and why now

The platform's core entities — ATT&CK techniques, CVEs, tactics, and the
correlations between them — form a naturally connected network. PostgreSQL
serves point lookups and aggregate stats well, but **multi-hop questions** are
where it strains:

- "Which techniques are reachable from a given CVE through shared tactics?"
- "What are the shortest attack paths from an Initial Access CVE to an Impact
  technique?"
- "Which techniques are central (high betweenness) across all correlated CVEs?"
- "Find clusters of CVEs that exploit overlapping technique sets."

These are recursive/path/centrality queries that become expensive multi-join
recursive CTEs in SQL but are first-class in Cypher. A graph database
complements (does not replace) PostgreSQL.

## 2. Graph schema

### 2.1 Node types

| Label | Source table | Key property | Other properties |
|---|---|---|---|
| `:Technique` | `techniques` | `technique_id` (e.g. `T1059`) | `name`, `is_subtechnique` |
| `:Tactic` | derived (`correlation_results.tactic`, later ATT&CK tactics) | `name` (e.g. `Execution`) | `short_id` |
| `:CVE` | `cves` | `cve_id` | `cvss_score`, `severity`, `published_date`, `description_length` |
| `:RiskScore` (optional) | `risk_scores` | — | `risk_score`, `risk_level`, `model_version` — may instead be **properties on `:CVE`** |
| `:Platform` / `:Product` (future) | NVD CPE data | `name` | — |
| `:CWE` (future) | NVD `weaknesses` | `cwe_id` | `name` |

`RiskScore` is best folded into `:CVE` as properties (1:1) rather than its own
node; it is listed for completeness.

### 2.2 Relationship types

| Relationship | From → To | Properties | Meaning |
|---|---|---|---|
| `(:CVE)-[:CORRELATES_TO]->(:Technique)` | CVE → Technique | `confidence_score`, `confidence_level`, `method`, `matched_keywords` | The core correlation edge (from `correlation_results`) |
| `(:Technique)-[:BELONGS_TO]->(:Tactic)` | Technique → Tactic | — | ATT&CK tactic membership |
| `(:Technique)-[:SUBTECHNIQUE_OF]->(:Technique)` | Sub → Parent | — | `T1059.001 → T1059` |
| `(:CVE)-[:EXPLOITS]->(:Product)` (future) | CVE → Product | `version_range` | Affected products via CPE |
| `(:CVE)-[:HAS_WEAKNESS]->(:CWE)` (future) | CVE → CWE | — | Weakness classification |
| `(:CWE)-[:MAPS_TO]->(:Technique)` (future) | CWE → Technique | `source` | Authoritative CWE→CAPEC→ATT&CK mapping |

### 2.3 Constraints & indexes (Cypher, for the future phase)

```cypher
CREATE CONSTRAINT technique_id IF NOT EXISTS
  FOR (t:Technique) REQUIRE t.technique_id IS UNIQUE;
CREATE CONSTRAINT cve_id IF NOT EXISTS
  FOR (c:CVE) REQUIRE c.cve_id IS UNIQUE;
CREATE CONSTRAINT tactic_name IF NOT EXISTS
  FOR (x:Tactic) REQUIRE x.name IS UNIQUE;
CREATE INDEX cve_severity IF NOT EXISTS FOR (c:CVE) ON (c.severity);
CREATE INDEX cve_risk IF NOT EXISTS FOR (c:CVE) ON (c.risk_level);
```

## 3. Data ingestion strategy

PostgreSQL remains the **system of record**; Neo4j is a **derived projection**
rebuilt/refreshed from it. Three options, in order of recommended adoption:

1. **Batch ETL (start here).** A `graph_sync.py` job reads the four tables and
   `MERGE`s nodes/relationships in idempotent batches (e.g. `UNWIND $rows`).
   Run it after each collector/correlation/inference cycle. Simple, reproducible,
   no dual-write risk.
2. **Incremental sync.** Use `generated_at` / `created_at` watermarks to sync
   only rows changed since the last run — the same incremental pattern the NVD
   collector already uses.
3. **CDC (later, if needed).** Logical replication / Debezium → Kafka → Neo4j
   for near-real-time graphs. Only justified at much larger scale.

Idempotent upsert pattern:

```cypher
UNWIND $rows AS row
MATCH (c:CVE {cve_id: row.cve_id})
MATCH (t:Technique {technique_id: row.technique_id})
MERGE (c)-[r:CORRELATES_TO]->(t)
SET r.confidence_score = row.confidence_score,
    r.confidence_level = row.confidence_level,
    r.method = row.method;
```

## 4. Query strategy

Representative Cypher for questions SQL handles poorly:

```cypher
// Attack paths: Initial-Access CVE → ... → Impact technique (≤4 hops)
MATCH path = (c:CVE)-[:CORRELATES_TO]->(:Technique)
             -[:BELONGS_TO]->(:Tactic {name:'Initial Access'})
MATCH (c)-[:CORRELATES_TO]->(imp:Technique)-[:BELONGS_TO]->(:Tactic {name:'Impact'})
RETURN c.cve_id, collect(DISTINCT imp.technique_id) AS impact_techniques
ORDER BY size(impact_techniques) DESC LIMIT 20;

// Co-occurring techniques (often exploited by the same CVEs)
MATCH (t1:Technique)<-[:CORRELATES_TO]-(:CVE)-[:CORRELATES_TO]->(t2:Technique)
WHERE t1.technique_id < t2.technique_id
RETURN t1.technique_id, t2.technique_id, count(*) AS shared_cves
ORDER BY shared_cves DESC LIMIT 25;
```

The API would gain read-only endpoints such as `GET /graph/attack-paths/{cve_id}`
and `GET /graph/related-techniques/{technique_id}`, backed by the Neo4j Python
driver — mirroring the existing router/DI conventions, with Neo4j sessions
injected the same way `get_db` injects SQLAlchemy sessions.

## 5. Performance considerations

- **Constraints first.** Unique constraints on `technique_id`/`cve_id` create
  backing indexes that make `MERGE` and lookups O(log n) instead of scans.
- **Batch with `UNWIND`.** Per-row transactions are the #1 ETL bottleneck; batch
  500–1,000 rows per transaction.
- **Bound traversals.** Always cap variable-length paths (`[:REL*1..4]`) — the
  technique/CVE graph is dense around popular techniques (e.g. T1203) and
  unbounded paths explode.
- **Projection for analytics.** Run GDS centrality/community algorithms on an
  in-memory **named graph projection**, not the stored graph.
- **Scale.** Current data (≈700 techniques + 2,600 CVEs + ≈1,500 edges) fits in
  memory comfortably; a single Neo4j instance is ample for the foreseeable
  roadmap.

## 6. Migration roadmap from PostgreSQL

1. **Phase 7a — Stand up Neo4j** alongside PostgreSQL (`docker-compose` service),
   apply constraints. PostgreSQL untouched.
2. **Phase 7b — Batch ETL** (`graph_sync.py`) projecting the four tables; validate
   node/edge counts against SQL aggregates.
3. **Phase 7c — Read-only graph endpoints** for paths/related/centrality; the
   dashboard gains a "Graph Explorer" page.
4. **Phase 7d — Incremental sync** on watermarks; schedule after each ingest.
5. **Phase 7e — GDS analytics** (centrality, community detection) surfaced via API.

PostgreSQL stays authoritative throughout; Neo4j is always rebuildable from it,
so there is no risky one-way migration.

## 7. Future graph analytics opportunities

- **Centrality** (PageRank / betweenness) to rank the most pivotal techniques —
  a graph-native signal that could feed back into the **risk model** as a new
  feature (replacing the current `technique_popularity` proxy).
- **Community detection** (Louvain) to discover threat clusters / campaign-like
  groupings of CVEs and techniques.
- **Similarity** (node2vec / Jaccard on shared techniques) for "CVEs similar to
  this one" recommendations.
- **Path analysis** to model and visualize end-to-end attack chains across
  tactics — the foundation for an attack-path explorer.
- **Temporal graphs** to track how technique↔CVE structure evolves as new CVEs
  land, surfacing emerging exploitation trends.
