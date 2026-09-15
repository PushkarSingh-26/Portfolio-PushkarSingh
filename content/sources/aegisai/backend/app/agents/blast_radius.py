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
    "actor": (
        "MATCH (s:ThreatActor {actor_id:$id})-[*1..4]-(n) "
        "RETURN labels(n)[0] AS label, "
        "coalesce(n.cve_id,n.technique_id,n.name,toString(n.alert_id),n.key) AS id LIMIT 3000"
    ),
    "cve": (
        "MATCH (s:CVE {cve_id:$id})-[*1..4]-(n) "
        "RETURN labels(n)[0] AS label, "
        "coalesce(n.cve_id,n.technique_id,n.name,toString(n.alert_id),n.key) AS id LIMIT 2000"
    ),
    "campaign": (
        "MATCH (s:Campaign {campaign_id:$id})-[*1..4]-(n) "
        "RETURN labels(n)[0] AS label, "
        "coalesce(n.cve_id,n.technique_id,n.name,toString(n.alert_id),n.key) AS id LIMIT 3000"
    ),
}

_LABEL_BUCKET = {
    "Alert": "affected_alerts", "CVE": "affected_cves", "Technique": "affected_techniques",
    "ThreatActor": "affected_actors", "Campaign": "affected_campaigns",
}


def compute(seed_type: str, seed_id, db: Session) -> dict:
    """Return the blast radius for a seed entity."""
    buckets = {v: set() for v in _LABEL_BUCKET.values()}
    buckets["affected_communities"] = set()

    if seed_type == "community":
        # Community blast radius is read from cached graph_metrics.
        from backend.app.models import GraphMetric
        members = db.execute(
            select(GraphMetric.entity_type, GraphMetric.entity_id)
            .where(GraphMetric.community_id == int(seed_id))
        ).all()
        for etype, eid in members:
            bucket = _LABEL_BUCKET.get(etype)
            if bucket:
                buckets[bucket].add(eid)
        buckets["affected_communities"].add(str(seed_id))
        return _finalize(seed_type, seed_id, buckets)

    cypher = _CYPHER.get(seed_type)
    if cypher:
        try:
            from backend.app.graph.neo4j_client import get_client
            coerced = int(seed_id) if seed_type in ("alert", "actor", "campaign") and str(seed_id).isdigit() else seed_id
            rows = get_client().run_read(cypher, {"id": coerced})
            for r in rows:
                bucket = _LABEL_BUCKET.get(r["label"])
                if bucket and r["id"] is not None:
                    buckets[bucket].add(str(r["id"]))
        except Exception as exc:  # noqa: BLE001
            log.warning("blast-radius graph traversal failed: %s", exc)

    # Affected communities = communities of the affected CVEs (from cache).
    _attach_communities(db, buckets)
    return _finalize(seed_type, seed_id, buckets)


def _attach_communities(db: Session, buckets: dict) -> None:
    from backend.app.models import GraphMetric
    cves = buckets.get("affected_cves", set())
    if not cves:
        return
    rows = db.execute(
        select(GraphMetric.community_id).where(
            GraphMetric.entity_type == "CVE", GraphMetric.entity_id.in_(list(cves)),
            GraphMetric.community_id.isnot(None))
    ).all()
    for (cid,) in rows:
        buckets["affected_communities"].add(str(cid))


def _finalize(seed_type, seed_id, buckets: dict) -> dict:
    counts = {k: len(v) for k, v in buckets.items()}
    return {
        "seed": {"type": seed_type, "id": str(seed_id)},
        "counts": counts,
        "total_affected": sum(counts.values()),
        "affected": {k: sorted(v)[:100] for k, v in buckets.items()},
    }
