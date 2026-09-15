"""Investigation engine (Phase 13.6 / 13.7).

Gathers real evidence from every relevant source for a routed intent, before any
narration. Returns a structured Evidence dict (findings, supporting entities,
graph relationships, risk justification, data sources, confidence) so answers
are fully grounded - no hallucinated intelligence.
"""

import logging
from collections import defaultdict

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.ai import query_router

log = logging.getLogger("ai.engine")


def _safe(fn, default):
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001 - graph backend optional/degradable
        log.warning("evidence source failed: %s", exc)
        return default


def _confidence(entity_ok: bool, n_evidence: int) -> float:
    score = 0.35 + (0.3 if entity_ok else 0.0) + min(0.35, 0.07 * n_evidence)
    return round(min(score, 0.97), 2)


# ── per-intent evidence gatherers ───────────────────────────

def _cve_risk(db, ents):
    from backend.app.models import (
        CVE, CorrelationResult, CTIRelationship, EPSSScore, GraphMetric,
        KEVEntry, PriorityScore, RiskScore,
    )
    cid = ents.get("cve_id")
    cve = db.execute(select(CVE).where(CVE.cve_id == cid)).scalar_one_or_none()
    if cve is None:
        return {"findings": {"error": f"{cid} not in catalog"}, "supporting_entities": [],
                "graph_relationships": [], "risk_justification": f"{cid} is not tracked.",
                "confidence": 0.2}
    risk = db.execute(select(RiskScore).where(RiskScore.cve_id == cid)).scalar_one_or_none()
    epss = db.execute(select(EPSSScore).where(EPSSScore.cve_id == cid)).scalar_one_or_none()
    kev = db.execute(select(KEVEntry).where(KEVEntry.cve_id == cid)).scalar_one_or_none()
    prio = db.execute(select(PriorityScore).where(PriorityScore.cve_id == cid)).scalar_one_or_none()
    gm = db.execute(select(GraphMetric).where(GraphMetric.entity_type == "CVE",
                    GraphMetric.entity_id == cid)).scalar_one_or_none()
    techs = [t for (t,) in db.execute(select(CorrelationResult.technique_id)
             .where(CorrelationResult.cve_id == cid)).all()]
    actors = [k for (st, sk, tt, tk) in db.execute(
        select(CTIRelationship.source_type, CTIRelationship.source_key,
               CTIRelationship.target_type, CTIRelationship.target_key)).all()
        for k in [sk if st == "actor" else tk]
        if {st, tt} == {"actor", "cve"} and (sk == cid or tk == cid)]

    findings = {
        "cve_id": cid, "cvss_score": cve.cvss_score, "severity": cve.severity,
        "ml_risk_score": getattr(risk, "risk_score", None),
        "ml_risk_level": getattr(risk, "risk_level", None),
        "epss_score": getattr(epss, "epss_score", None),
        "in_kev": kev is not None,
        "priority_score": getattr(prio, "priority_score", None),
        "graph_pagerank": getattr(gm, "pagerank", None),
        "graph_degree": getattr(gm, "degree_centrality", None),
        "techniques": techs, "threat_actors": sorted(set(actors)),
    }
    reasons = []
    if cve.cvss_score:
        reasons.append(f"CVSS {cve.cvss_score} ({cve.severity})")
    if epss:
        reasons.append(f"EPSS {epss.epss_score:.3f} exploit probability")
    if kev:
        reasons.append("listed in CISA KEV (actively exploited)")
    if risk:
        reasons.append(f"ML risk {risk.risk_score:.0f}/{risk.risk_level}")
    if gm and gm.pagerank:
        reasons.append(f"graph PageRank {gm.pagerank:.3f} ({gm.degree_centrality:.0f} connections)")
    if actors:
        reasons.append(f"attributed to {', '.join(sorted(set(actors)))}")
    se = [{"type": "Technique", "id": t} for t in techs] + \
         [{"type": "ThreatActor", "name": a} for a in sorted(set(actors))]
    rels = [f"CVE {cid} -CORRELATED_TO- {t}" for t in techs] + \
           [f"{a} -ATTRIBUTED_TO- CVE {cid}" for a in sorted(set(actors))]
    return {"findings": findings, "supporting_entities": se, "graph_relationships": rels,
            "risk_justification": f"{cid} is high risk because: " + "; ".join(reasons) + ".",
            "confidence": _confidence(True, len(reasons))}


def _actor_investigation(db, ents):
    from backend.app.graph import services
    from backend.app.models import GraphMetric
    aid = ents.get("actor_id")
    sub = _safe(lambda: services.actor_investigation(aid), {"nodes": [], "edges": [], "summary": {}})
    gm = db.execute(select(GraphMetric).where(GraphMetric.entity_type == "ThreatActor",
                    GraphMetric.entity_id == str(aid))).scalar_one_or_none()
    findings = {"actor": ents.get("actor_name"), "ecosystem": sub.get("summary", {}),
                "graph_pagerank": getattr(gm, "pagerank", None),
                "graph_degree": getattr(gm, "degree_centrality", None),
                "betweenness": getattr(gm, "betweenness", None)}
    se = [{"type": n["label"], "name": n["name"]} for n in sub.get("nodes", [])[:25]]
    rels = [f"{e['source']} -{e['type']}- {e['target']}" for e in sub.get("edges", [])[:25]]
    infl = (f"PageRank {gm.pagerank:.3f}, degree {gm.degree_centrality:.0f}"
            if gm else "no graph centrality computed")
    return {"findings": findings, "supporting_entities": se, "graph_relationships": rels,
            "risk_justification": f"Actor '{ents.get('actor_name')}' influence: {infl}. "
            f"Ecosystem: {sub.get('summary', {})}.",
            "confidence": _confidence(bool(aid), len(se))}


def _attack_paths_actor(db, ents):
    aid = ents.get("actor_id")
    alerts = _safe(lambda: query_router.run_template("actor_to_alerts", {"actor_id": aid, "limit": 25}), [])
    actor_inv = _actor_investigation(db, ents)
    findings = dict(actor_inv["findings"])
    findings["reachable_alerts"] = [{"alert_id": a["alert_id"], "description": a["description"]} for a in alerts]
    rels = actor_inv["graph_relationships"] + \
           [f"Alert#{a['alert_id']} ->...-> {ents.get('actor_name')}" for a in alerts]
    return {"findings": findings,
            "supporting_entities": actor_inv["supporting_entities"] +
            [{"type": "Alert", "id": a["alert_id"]} for a in alerts],
            "graph_relationships": rels,
            "risk_justification": f"{len(alerts)} live alert(s) trace to actor "
            f"'{ents.get('actor_name')}' via technique->CVE->actor attack paths.",
            "confidence": _confidence(bool(aid), len(alerts) + 1)}


def _recent_alert_actors(db, ents):
    from backend.app.models import WazuhAlert, WazuhAlertEnrichment
    rows = db.execute(
        select(WazuhAlertEnrichment, WazuhAlert)
        .join(WazuhAlert, WazuhAlert.id == WazuhAlertEnrichment.alert_id)
        .order_by(WazuhAlert.timestamp.desc().nullslast()).limit(100)
    ).all()
    actor_counts = defaultdict(int)
    alerts_seen = 0
    for enr, _alert in rows:
        alerts_seen += 1
        for a in (enr.evidence or {}).get("threat_actors", []):
            actor_counts[a] += 1
    ranked = sorted(actor_counts.items(), key=lambda kv: kv[1], reverse=True)
    findings = {"alerts_examined": alerts_seen,
                "actors": [{"actor": a, "alerts": c} for a, c in ranked]}
    se = [{"type": "ThreatActor", "name": a} for a, _ in ranked]
    return {"findings": findings, "supporting_entities": se,
            "graph_relationships": [f"{a} associated with {c} recent alert(s)" for a, c in ranked],
            "risk_justification": f"{len(ranked)} actor(s) associated with the last "
            f"{alerts_seen} enriched alerts.",
            "confidence": _confidence(True, len(ranked))}


def _campaigns_wazuh(db, ents):
    from backend.app.models import WazuhAlertEnrichment
    rows = db.query(WazuhAlertEnrichment).all()
    camp = defaultdict(int)
    for enr in rows:
        for c in (enr.evidence or {}).get("campaigns", []):
            camp[c] += 1
    ranked = sorted(camp.items(), key=lambda kv: kv[1], reverse=True)
    findings = {"campaigns": [{"campaign": c, "alerts": n} for c, n in ranked]}
    return {"findings": findings,
            "supporting_entities": [{"type": "Campaign", "name": c} for c, _ in ranked],
            "graph_relationships": [f"Campaign {c} linked to {n} alert(s)" for c, n in ranked],
            "risk_justification": (f"{len(ranked)} campaign(s) linked to current Wazuh activity."
                                   if ranked else "No campaigns are currently linked to Wazuh alerts."),
            "confidence": _confidence(True, len(ranked) or 1)}


def _dangerous_cves(db, ents):
    from backend.app.models import CVE, PriorityScore
    rows = db.execute(
        select(PriorityScore, CVE.severity).join(CVE, CVE.cve_id == PriorityScore.cve_id)
        .order_by(PriorityScore.priority_score.desc()).limit(15)
    ).all()
    findings = {"cves": [{"cve_id": p.cve_id, "priority_score": p.priority_score,
                          "priority_level": p.priority_level, "kev": p.kev_flag,
                          "epss": p.epss_score, "severity": sev} for p, sev in rows]}
    se = [{"type": "CVE", "id": p.cve_id} for p, _ in rows]
    return {"findings": findings, "supporting_entities": se,
            "graph_relationships": [],
            "risk_justification": "Top CVEs by combined priority (CVSS+EPSS+KEV+ML+graph).",
            "confidence": _confidence(True, len(rows))}


def _top_techniques(db, ents):
    from backend.app.models import GraphMetric, WazuhAlertEnrichment
    counts = defaultdict(int)
    for (tid,) in db.execute(select(WazuhAlertEnrichment.technique_id)
                             .where(WazuhAlertEnrichment.technique_id.isnot(None))).all():
        counts[tid] += 1
    ranked = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:15]
    deg = {m.entity_id: m.degree_centrality for m in db.execute(
        select(GraphMetric).where(GraphMetric.entity_type == "Technique")).scalars().all()}
    findings = {"techniques": [{"technique_id": t, "alerts": c,
                                "graph_degree": deg.get(t)} for t, c in ranked]}
    return {"findings": findings,
            "supporting_entities": [{"type": "Technique", "id": t} for t, _ in ranked],
            "graph_relationships": [f"{t} observed in {c} alert(s)" for t, c in ranked],
            "risk_justification": "Most frequently observed ATT&CK techniques across Wazuh alerts.",
            "confidence": _confidence(True, len(ranked))}


def _kev_actors(db, ents):
    from backend.app.models import KEVEntry
    kev_ids = [row[0] for row in db.execute(select(KEVEntry.cve_id)).all()]
    rows = _safe(lambda: query_router.run_template(
        "kev_actor_links", {"cve_ids": kev_ids, "limit": 25}), [])
    findings = {"kev_count": len(kev_ids),
                "actors": [{"actor": r["actor"], "kev_cves": r["kev_cves"]} for r in rows]}
    return {"findings": findings,
            "supporting_entities": [{"type": "ThreatActor", "name": r["actor"]} for r in rows],
            "graph_relationships": [f"{r['actor']} -ATTRIBUTED_TO- {r['kev_cves']} KEV CVE(s)" for r in rows],
            "risk_justification": f"{len(rows)} actor(s) attributed to KEV (actively-exploited) CVEs.",
            "confidence": _confidence(True, len(rows) + 1)}


def _triage_alerts(db, ents):
    from backend.app.models import WazuhAlert, WazuhAlertEnrichment
    rows = db.execute(
        select(WazuhAlertEnrichment, WazuhAlert.description)
        .join(WazuhAlert, WazuhAlert.id == WazuhAlertEnrichment.alert_id)
        .order_by(WazuhAlertEnrichment.priority_score.desc()).limit(15)
    ).all()
    findings = {"alerts": [{"alert_id": e.alert_id, "priority_score": e.priority_score,
                            "priority_level": e.priority_level, "kev": e.kev_present,
                            "description": d} for e, d in rows]}
    return {"findings": findings,
            "supporting_entities": [{"type": "Alert", "id": e.alert_id} for e, _ in rows],
            "graph_relationships": [],
            "risk_justification": "Alerts ranked by SOC priority (highest first).",
            "confidence": _confidence(True, len(rows))}


def _top_attack_paths(db, ents):
    from backend.app.models import GraphInsight
    rows = db.execute(select(GraphInsight).where(GraphInsight.insight_type == "attack_path")
                      .order_by(GraphInsight.id).limit(20)).scalars().all()
    findings = {"attack_paths": [{"alert_id": r.entity_id, "severity": r.severity,
                                  "insight": r.insight} for r in rows]}
    return {"findings": findings,
            "supporting_entities": [{"type": "Alert", "id": r.entity_id} for r in rows],
            "graph_relationships": [r.insight for r in rows[:10]],
            "risk_justification": f"{len(rows)} stored attack path(s), highest-priority first.",
            "confidence": _confidence(True, len(rows))}


def _alert_investigation(db, ents):
    from backend.app.graph import attack_paths, services
    from backend.app.models import WazuhAlertEnrichment
    aid = ents.get("alert_id")
    enr = db.execute(select(WazuhAlertEnrichment).where(WazuhAlertEnrichment.alert_id == aid)
                     ).scalar_one_or_none()
    sub = _safe(lambda: services.alert_investigation(aid), {"nodes": [], "edges": [], "summary": {}})
    paths = _safe(lambda: attack_paths.alert_attack_paths(aid, limit=10), [])
    ev = (enr.evidence or {}) if enr else {}
    findings = {"alert_id": aid,
                "priority_score": getattr(enr, "priority_score", None),
                "priority_level": getattr(enr, "priority_level", None),
                "kev_present": getattr(enr, "kev_present", None),
                "graph_summary": sub.get("summary", {}),
                "attack_paths": [p["path"] for p in paths],
                "techniques": ev.get("techniques", []),
                "threat_actors": ev.get("threat_actors", [])}
    se = [{"type": "Technique", "id": t} for t in ev.get("techniques", [])] + \
         [{"type": "ThreatActor", "name": a} for a in ev.get("threat_actors", [])]
    return {"findings": findings, "supporting_entities": se,
            "graph_relationships": [p["path"] for p in paths],
            "risk_justification": (enr.evidence or {}).get("rationale", "") if enr
            else f"No enrichment found for alert {aid}.",
            "confidence": _confidence(enr is not None, len(paths) + len(se))}


def _campaign_investigation(db, ents):
    from backend.app.graph import services
    cid = ents.get("campaign_id")
    sub = _safe(lambda: services.campaign_investigation(cid), {"nodes": [], "edges": [], "summary": {}})
    return {"findings": {"campaign": ents.get("campaign_name"), "ecosystem": sub.get("summary", {})},
            "supporting_entities": [{"type": n["label"], "name": n["name"]} for n in sub.get("nodes", [])[:25]],
            "graph_relationships": [f"{e['source']} -{e['type']}- {e['target']}" for e in sub.get("edges", [])[:25]],
            "risk_justification": f"Campaign '{ents.get('campaign_name')}' ecosystem: {sub.get('summary', {})}.",
            "confidence": _confidence(bool(cid), len(sub.get("nodes", [])))}


def _technique_investigation(db, ents):
    from backend.app.models import CorrelationResult, GraphMetric, WazuhAlertEnrichment
    tid = ents.get("technique_id")
    n_cves = db.scalar(select(func.count()).select_from(CorrelationResult)
                       .where(CorrelationResult.technique_id == tid)) or 0
    n_alerts = db.scalar(select(func.count()).select_from(WazuhAlertEnrichment)
                         .where(WazuhAlertEnrichment.technique_id == tid)) or 0
    gm = db.execute(select(GraphMetric).where(GraphMetric.entity_type == "Technique",
                    GraphMetric.entity_id == tid)).scalar_one_or_none()
    findings = {"technique_id": tid, "correlated_cves": n_cves, "related_alerts": n_alerts,
                "graph_degree": getattr(gm, "degree_centrality", None)}
    return {"findings": findings, "supporting_entities": [{"type": "Technique", "id": tid}],
            "graph_relationships": [f"{tid} -CORRELATED_TO- {n_cves} CVE(s)",
                                    f"{tid} observed in {n_alerts} alert(s)"],
            "risk_justification": f"{tid} correlates to {n_cves} CVEs and appears in {n_alerts} alerts.",
            "confidence": _confidence(bool(tid), 2)}


def _overview(db, ents):
    from backend.app.models import CVE, GraphMetric, ThreatActor, WazuhAlert
    findings = {
        "cves": db.scalar(select(func.count()).select_from(CVE)) or 0,
        "actors": db.scalar(select(func.count()).select_from(ThreatActor)) or 0,
        "alerts": db.scalar(select(func.count()).select_from(WazuhAlert)) or 0,
        "graph_metrics": db.scalar(select(func.count()).select_from(GraphMetric)) or 0,
    }
    return {"findings": findings, "supporting_entities": [], "graph_relationships": [],
            "risk_justification": "Platform overview. Ask about a CVE, actor, alert, "
            "campaign, technique, or attack paths for a focused investigation.",
            "confidence": 0.5}


_HANDLERS = {
    "cve_risk": _cve_risk, "actor_investigation": _actor_investigation,
    "attack_paths_actor": _attack_paths_actor, "recent_alert_actors": _recent_alert_actors,
    "campaigns_wazuh": _campaigns_wazuh, "dangerous_cves": _dangerous_cves,
    "top_techniques": _top_techniques, "kev_actors": _kev_actors,
    "triage_alerts": _triage_alerts, "top_attack_paths": _top_attack_paths,
    "alert_investigation": _alert_investigation, "campaign_investigation": _campaign_investigation,
    "technique_investigation": _technique_investigation, "overview": _overview,
}


def gather_evidence(intent: str, entities: dict, db: Session) -> dict:
    handler = _HANDLERS.get(intent, _overview)
    evidence = handler(db, entities)
    evidence["intent"] = intent
    evidence["data_sources"] = query_router.INTENT_SOURCES.get(intent, [])
    return evidence
