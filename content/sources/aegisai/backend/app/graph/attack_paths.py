"""Attack-path engine (Phase 12).

Generates explainable attack paths over the Neo4j graph:

    Alert -> Technique -> CVE -> ThreatActor [-> Campaign | -> Malware]

and persists path metadata (per high-priority alert) into `graph_insights`.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.graph.neo4j_client import get_client

log = logging.getLogger("graph.attack_paths")


def alert_attack_paths(alert_id: int, limit: int = 25) -> list[dict]:
    """Concrete Alert→Technique→CVE→ThreatActor(→Malware/Campaign) paths."""
    client = get_client()
    rows = client.run_read(
        "MATCH (al:Alert {alert_id:$id})-[:USES_TECHNIQUE]->(t:Technique)"
        "-[:CORRELATED_TO]->(c:CVE)-[:ATTRIBUTED_TO]->(a:ThreatActor) "
        "OPTIONAL MATCH (a)-[:USES]->(m:Malware) "
        "OPTIONAL MATCH (a)-[:RUNS]->(ca:Campaign) "
        "RETURN t.technique_id AS technique, c.cve_id AS cve, a.name AS actor, "
        "collect(DISTINCT m.name) AS malware, collect(DISTINCT ca.name) AS campaigns "
        "LIMIT $limit",
        {"id": alert_id, "limit": limit},
    )
    paths = []
    for r in rows:
        chain = [f"Alert#{alert_id}", r["technique"], r["cve"], r["actor"]]
        tail = [x for x in r["malware"] if x] + [x for x in r["campaigns"] if x]
        suffix = f" -> {', '.join(tail)}" if tail else ""
        paths.append({
            "alert_id": alert_id, "technique": r["technique"], "cve": r["cve"],
            "threat_actor": r["actor"], "malware": [x for x in r["malware"] if x],
            "campaigns": [x for x in r["campaigns"] if x],
            "path": " -> ".join(chain) + suffix, "length": len(chain),
        })
    return paths


def analyze_and_store(db: Session, top_alerts: int = 50) -> dict:
    """Compute attack paths for the highest-priority alerts; persist metadata."""
    from backend.app.models import GraphInsight, WazuhAlertEnrichment

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    db.query(GraphInsight).filter(GraphInsight.insight_type == "attack_path").delete(
        synchronize_session=False
    )

    top = db.execute(
        select(WazuhAlertEnrichment.alert_id, WazuhAlertEnrichment.priority_level)
        .order_by(WazuhAlertEnrichment.priority_score.desc()).limit(top_alerts)
    ).all()

    stored = 0
    total_paths = 0
    for alert_id, level in top:
        paths = alert_attack_paths(alert_id, limit=10)
        if not paths:
            continue
        total_paths += len(paths)
        actors = sorted({p["threat_actor"] for p in paths if p["threat_actor"]})
        sample = paths[0]["path"]
        db.add(GraphInsight(
            insight_type="attack_path", entity_type="Alert", entity_id=str(alert_id),
            insight=f"Alert #{alert_id}: {len(paths)} attack path(s) to actor(s) "
                    f"{', '.join(actors)}. e.g. {sample}",
            severity=level if level in ("CRITICAL", "HIGH") else "MEDIUM",
            created_at=now,
        ))
        stored += 1

    db.commit()
    return {"alerts_with_paths": stored, "total_paths": total_paths}


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [paths] %(message)s")
    from backend.app.database import SessionLocal

    with SessionLocal() as db:
        stats = analyze_and_store(db)
    log.info("Done: %s", stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
