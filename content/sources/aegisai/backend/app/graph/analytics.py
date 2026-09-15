"""Neo4j GDS graph analytics (Phase 12).

Projects the live graph and computes degree centrality, PageRank, betweenness,
Louvain communities, weakly-connected components, and node similarity, then
persists per-entity results into PostgreSQL `graph_metrics` for reuse by the
intelligence engine, ML V5, and the APIs. Uses real GDS over the real graph.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.app.graph.neo4j_client import get_client

log = logging.getLogger("graph.analytics")

GRAPH_NAME = "cti_analytics"
TARGET_LABELS = {"CVE", "Technique", "ThreatActor", "Malware", "Campaign", "IOC"}

# Canonical per-label entity_id (matches identifiers used elsewhere).
_KEY = (
    "coalesce(n.technique_id, n.cve_id, n.agent_id, n.key, "
    "toString(n.actor_id), toString(n.malware_id), toString(n.campaign_id), "
    "toString(n.ioc_id), toString(n.alert_id))"
)


def gds_available() -> bool:
    try:
        get_client().run_read("RETURN gds.version() AS v")
        return True
    except Exception:
        return False


def _project(client) -> None:
    client.run_write(
        "CALL gds.graph.drop($g, false) YIELD graphName RETURN graphName", {"g": GRAPH_NAME}
    )
    client.run_write(
        "CALL gds.graph.project($g, '*', "
        "{REL: {type: '*', orientation: 'UNDIRECTED'}}) "
        "YIELD graphName RETURN graphName",
        {"g": GRAPH_NAME},
    )


def _stream_score(client, proc: str, yield_field: str = "score") -> list[dict]:
    cypher = (
        f"CALL {proc}($g) YIELD nodeId, {yield_field} "
        "WITH gds.util.asNode(nodeId) AS n, " + yield_field + " AS val "
        f"RETURN labels(n)[0] AS label, {_KEY} AS entity_id, val"
    )
    return client.run_read(cypher, {"g": GRAPH_NAME})


def compute_metrics(client) -> tuple[dict, dict]:
    """Run all GDS algorithms. Returns (metrics_by_entity, component_info)."""
    _project(client)
    metrics: dict[tuple[str, str], dict] = {}

    def _slot(label, eid):
        return metrics.setdefault(
            (label, eid),
            {"degree_centrality": 0.0, "pagerank": 0.0, "betweenness": 0.0,
             "community_id": None, "node_similarity_score": 0.0},
        )

    for row in _stream_score(client, "gds.degree.stream"):
        _slot(row["label"], row["entity_id"])["degree_centrality"] = row["val"]
    for row in _stream_score(client, "gds.pageRank.stream"):
        _slot(row["label"], row["entity_id"])["pagerank"] = round(row["val"], 6)
    for row in _stream_score(client, "gds.betweenness.stream"):
        _slot(row["label"], row["entity_id"])["betweenness"] = round(row["val"], 4)
    for row in _stream_score(client, "gds.louvain.stream", "communityId"):
        _slot(row["label"], row["entity_id"])["community_id"] = int(row["val"])

    # Weakly-connected components -> component sizes (for isolated-node insights).
    comp_rows = _stream_score(client, "gds.wcc.stream", "componentId")
    component_sizes: dict[int, int] = {}
    for row in comp_rows:
        cid = int(row["val"])
        component_sizes[cid] = component_sizes.get(cid, 0) + 1

    # Node similarity: keep each node's strongest Jaccard similarity.
    sim_rows = client.run_read(
        "CALL gds.nodeSimilarity.stream($g) YIELD node1, similarity "
        "WITH gds.util.asNode(node1) AS n, max(similarity) AS s "
        f"RETURN labels(n)[0] AS label, {_KEY.replace('n.', 'n.')} AS entity_id, s AS val",
        {"g": GRAPH_NAME},
    )
    for row in sim_rows:
        key = (row["label"], row["entity_id"])
        if key in metrics:
            metrics[key]["node_similarity_score"] = round(row["val"], 4)

    client.run_write("CALL gds.graph.drop($g, false) YIELD graphName RETURN graphName",
                     {"g": GRAPH_NAME})

    component_info = {
        "num_components": len(component_sizes),
        "isolated_nodes": sum(1 for s in component_sizes.values() if s == 1),
        "largest_component": max(component_sizes.values()) if component_sizes else 0,
    }
    return metrics, component_info


def run_analytics(db: Session) -> dict:
    """Compute GDS metrics and upsert graph_metrics (target labels only)."""
    from backend.app.models import GraphMetric

    client = get_client()
    if not gds_available():
        raise RuntimeError("Neo4j GDS plugin is not available")

    metrics, component_info = compute_metrics(client)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    existing = {(m.entity_type, m.entity_id): m for m in db.query(GraphMetric).all()}

    inserted = updated = 0
    for (label, eid), vals in metrics.items():
        if label not in TARGET_LABELS or eid is None:
            continue
        cur = existing.get((label, eid))
        if cur is None:
            db.add(GraphMetric(entity_type=label, entity_id=eid, calculated_at=now, **vals))
            inserted += 1
        else:
            for k, v in vals.items():
                setattr(cur, k, v)
            cur.calculated_at = now
            updated += 1

    db.commit()
    persisted = inserted + updated
    return {
        "persisted_metrics": persisted, "inserted": inserted, "updated": updated,
        "components": component_info,
    }


def main() -> int:
    import logging as _l

    _l.basicConfig(level=_l.INFO, format="%(asctime)s %(levelname)s [analytics] %(message)s")
    from backend.app.database import SessionLocal

    log.info("Computing GDS graph metrics ...")
    with SessionLocal() as db:
        stats = run_analytics(db)
    log.info("Done: %s", stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
