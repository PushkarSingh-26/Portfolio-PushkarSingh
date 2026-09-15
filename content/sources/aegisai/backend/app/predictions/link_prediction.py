"""Link prediction over graph embeddings (Phase 16.2 / 16.3 / 16.5).

For each target relationship type, ranks candidate node pairs by embedding cosine
similarity, excludes pairs that already have an edge, and persists the top
predictions (with confidence) to predicted_relationships. Also emits prediction
insights into graph_insights. Deterministic given the seeded embeddings.
"""

import logging
from datetime import datetime, timezone

import numpy as np
from sqlalchemy.orm import Session

from backend.app.predictions import embeddings as emb

log = logging.getLogger("predictions.link")

LABEL_TYPE = {"ThreatActor": "actor", "CVE": "cve", "Campaign": "campaign",
              "Technique": "technique", "Malware": "malware", "Alert": "alert"}
_KEY_EXPR = {
    "ThreatActor": "toString({v}.actor_id)", "CVE": "{v}.cve_id",
    "Campaign": "toString({v}.campaign_id)", "Technique": "{v}.technique_id",
    "Malware": "toString({v}.malware_id)", "Alert": "toString({v}.alert_id)",
}
# (name, source_label, target_label)
PAIR_SPECS = [
    ("actor_cve", "ThreatActor", "CVE"),
    ("actor_campaign", "ThreatActor", "Campaign"),
    ("campaign_technique", "Campaign", "Technique"),
    ("malware_cve", "Malware", "CVE"),
    ("technique_alert", "Technique", "Alert"),
]


def _existing_pairs(client, sl: str, tl: str) -> set:
    cypher = (f"MATCH (a:{sl})--(b:{tl}) "
              f"RETURN {_KEY_EXPR[sl].format(v='a')} AS s, {_KEY_EXPR[tl].format(v='b')} AS t")
    return {(r["s"], r["t"]) for r in client.run_read(cypher) if r["s"] and r["t"]}


def _predict_pairs(emb_map, sl, tl, existing, top_k, min_conf):
    src = [(eid, vec) for (lab, eid), vec in emb_map.items() if lab == sl]
    tgt = [(eid, vec) for (lab, eid), vec in emb_map.items() if lab == tl]
    if not src or not tgt:
        return []
    S = np.array([v for _, v in src], dtype=float)
    T = np.array([v for _, v in tgt], dtype=float)
    S /= (np.linalg.norm(S, axis=1, keepdims=True) + 1e-9)
    T /= (np.linalg.norm(T, axis=1, keepdims=True) + 1e-9)
    sims = S @ T.T  # cosine similarity matrix
    preds = []
    for i, (sid, _) in enumerate(src):
        row = sims[i]
        for j in np.argsort(row)[::-1][: top_k * 3]:
            sid_, tid_ = sid, tgt[j][0]
            conf = float(row[j])
            if conf < min_conf or (sid_, tid_) in existing:
                continue
            preds.append((sid_, tid_, round(conf, 4)))
            if len([p for p in preds if p[0] == sid]) >= top_k:
                break
    return preds


def run(db: Session, model: str = "fastrp", top_k: int = 10, min_conf: float = 0.5) -> dict:
    from backend.app.graph.neo4j_client import get_client
    from backend.app.models import PredictedRelationship

    client = get_client()
    emb_map = emb.load_embeddings(set(LABEL_TYPE))
    if not emb_map:
        raise RuntimeError("No embeddings found - run compute_embeddings() first")

    # Idempotent refresh for this model.
    db.query(PredictedRelationship).filter(PredictedRelationship.model == model).delete(
        synchronize_session=False)
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    by_type, total = {}, 0
    for name, sl, tl in PAIR_SPECS:
        existing = _existing_pairs(client, sl, tl)
        preds = _predict_pairs(emb_map, sl, tl, existing, top_k, min_conf)
        for sid, tid, conf in preds:
            db.add(PredictedRelationship(
                source_type=LABEL_TYPE[sl], source_id=sid, target_type=LABEL_TYPE[tl],
                target_id=tid, confidence=conf, model=model, created_at=now))
        by_type[name] = len(preds)
        total += len(preds)
    db.commit()

    _generate_insights(db, model)
    return {"model": model, "predictions": total, "by_type": by_type}


def _generate_insights(db: Session, model: str) -> None:
    from collections import defaultdict
    from backend.app.models import GraphInsight, PredictedRelationship, ThreatActor

    db.query(GraphInsight).filter(GraphInsight.insight_type.like("prediction_%")).delete(
        synchronize_session=False)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    names = {str(a.id): a.actor_name for a in db.query(ThreatActor).all()}

    actor_cve = defaultdict(list)
    cve_pred = defaultdict(list)
    campaign_tech = defaultdict(list)
    for p in db.query(PredictedRelationship).filter(PredictedRelationship.model == model).all():
        if p.target_type == "cve":  # predicted to be targeted by an actor or malware
            cve_pred[p.target_id].append((p.source_type, p.source_id, p.confidence))
            if p.source_type == "actor":
                actor_cve[p.source_id].append((p.target_id, p.confidence))
        elif p.source_type == "campaign" and p.target_type == "technique":
            campaign_tech[p.source_id].append((p.target_id, p.confidence))

    insights = []
    for aid, links in sorted(actor_cve.items(), key=lambda kv: len(kv[1]), reverse=True)[:5]:
        insights.append(GraphInsight(
            insight_type="prediction_emerging_actor", entity_type="ThreatActor", entity_id=aid,
            insight=f"Actor '{names.get(aid, aid)}' is predicted to be linked to {len(links)} "
                    f"additional CVE(s) (max confidence {max(c for _, c in links):.2f}).",
            severity="HIGH", created_at=now))
    for cid, links in sorted(cve_pred.items(), key=lambda kv: max(c for *_, c in kv[1]), reverse=True)[:10]:
        srcs = ", ".join(sorted({f"{t}:{i}" for t, i, _ in links}))
        insights.append(GraphInsight(
            insight_type="prediction_high_risk_cve", entity_type="CVE", entity_id=cid,
            insight=f"{cid} is predicted to be targeted by {srcs} "
                    f"(confidence {max(c for *_, c in links):.2f}).",
            severity="HIGH", created_at=now))
    for cpid, links in sorted(campaign_tech.items(), key=lambda kv: len(kv[1]), reverse=True)[:5]:
        insights.append(GraphInsight(
            insight_type="prediction_emerging_campaign", entity_type="Campaign", entity_id=cpid,
            insight=f"Campaign {cpid} is predicted to adopt {len(links)} additional technique(s).",
            severity="MEDIUM", created_at=now))
    db.add_all(insights)
    db.commit()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [predict] %(message)s")
    from backend.app.database import SessionLocal
    emb.compute_embeddings("fastrp")
    with SessionLocal() as db:
        stats = run(db)
    log.info("Link prediction done: %s", stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
