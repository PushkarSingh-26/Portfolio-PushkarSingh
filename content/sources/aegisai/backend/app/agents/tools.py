"""Agent tool registry (Phase 14.2).

Every tool wraps an existing, vetted platform service or read-only DB query - the
agent can only act through this whitelist. Tools return {"ok", "summary", "data"}
and are invoked via `run_tool`, which the executor logs.
"""

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

log = logging.getLogger("agents.tools")


def _ok(summary: str, data) -> dict:
    return {"ok": True, "summary": summary, "data": data}


# ── Tool implementations (db, **params) ─────────────────────

def graph_investigation(db: Session, entity_type: str, entity_id) -> dict:
    from backend.app.graph import services
    fn = {
        "alert": services.alert_investigation, "cve": services.cve_investigation,
        "actor": services.actor_investigation, "campaign": services.campaign_investigation,
        "malware": services.malware_investigation,
    }.get(entity_type)
    if not fn:
        return {"ok": False, "summary": f"no graph tool for {entity_type}", "data": {}}
    sub = fn(int(entity_id) if str(entity_id).isdigit() else entity_id)
    return _ok(f"graph subgraph for {entity_type} {entity_id}: {sub.get('summary', {})}", sub)


def attack_path_investigation(db: Session, alert_id: int) -> dict:
    from backend.app.graph import attack_paths
    paths = attack_paths.alert_attack_paths(int(alert_id), limit=25)
    return _ok(f"{len(paths)} attack path(s) for alert {alert_id}", paths)


def alert_investigation(db: Session, alert_id: int) -> dict:
    from backend.app.ai import investigation_engine
    ev = investigation_engine.gather_evidence("alert_investigation", {"alert_id": int(alert_id)}, db)
    return _ok(f"alert {alert_id} evidence", ev)


def threat_actor_investigation(db: Session, actor_id: int, name: str | None = None) -> dict:
    from backend.app.ai import investigation_engine
    ev = investigation_engine.gather_evidence(
        "actor_investigation", {"actor_id": int(actor_id), "actor_name": name}, db)
    return _ok(f"actor {name or actor_id} evidence", ev)


def campaign_investigation(db: Session, campaign_id: int, name: str | None = None) -> dict:
    from backend.app.ai import investigation_engine
    ev = investigation_engine.gather_evidence(
        "campaign_investigation", {"campaign_id": int(campaign_id), "campaign_name": name}, db)
    return _ok(f"campaign {name or campaign_id} evidence", ev)


def technique_investigation(db: Session, technique_id: str) -> dict:
    from backend.app.ai import investigation_engine
    ev = investigation_engine.gather_evidence(
        "technique_investigation", {"technique_id": technique_id.upper()}, db)
    return _ok(f"technique {technique_id} evidence", ev)


def risk_score_retrieval(db: Session, cve_id: str) -> dict:
    from backend.app.models import PriorityScore, RiskScore
    cid = cve_id.upper()
    rs = db.execute(select(RiskScore).where(RiskScore.cve_id == cid)).scalar_one_or_none()
    ps = db.execute(select(PriorityScore).where(PriorityScore.cve_id == cid)).scalar_one_or_none()
    data = {"cve_id": cid,
            "risk_score": getattr(rs, "risk_score", None), "risk_level": getattr(rs, "risk_level", None),
            "model_version": getattr(rs, "model_version", None),
            "priority_score": getattr(ps, "priority_score", None),
            "priority_level": getattr(ps, "priority_level", None)}
    return _ok(f"risk for {cid}: ML {data['risk_score']} / priority {data['priority_score']}", data)


def graph_metrics_retrieval(db: Session, entity_type: str, entity_id) -> dict:
    from backend.app.models import GraphMetric
    gm = db.execute(select(GraphMetric).where(
        GraphMetric.entity_type == entity_type, GraphMetric.entity_id == str(entity_id))
    ).scalar_one_or_none()
    data = {} if gm is None else {
        "pagerank": gm.pagerank, "degree_centrality": gm.degree_centrality,
        "betweenness": gm.betweenness, "community_id": gm.community_id}
    return _ok(f"graph metrics for {entity_type} {entity_id}", data)


def wazuh_alert_retrieval(db: Session, alert_id: int) -> dict:
    from backend.app.models import WazuhAlert, WazuhAlertEnrichment
    a = db.get(WazuhAlert, int(alert_id))
    if a is None:
        return {"ok": False, "summary": f"alert {alert_id} not found", "data": {}}
    enr = db.execute(select(WazuhAlertEnrichment).where(
        WazuhAlertEnrichment.alert_id == int(alert_id))).scalar_one_or_none()
    ev = getattr(enr, "evidence", None) or {}
    related_cves = [c.get("cve_id") for c in ev.get("cves", []) if c.get("cve_id")]
    data = {"alert_id": a.id, "rule_level": a.rule_level, "description": a.description,
            "agent_id": a.agent_id, "mitre_techniques": a.mitre_techniques,
            "cve_id": getattr(enr, "cve_id", None),
            "related_cves": related_cves,
            "priority_score": getattr(enr, "priority_score", None),
            "priority_level": getattr(enr, "priority_level", None),
            "kev_present": getattr(enr, "kev_present", None),
            "evidence": ev}
    return _ok(f"wazuh alert {alert_id} (level {a.rule_level})", data)


def misp_intel_retrieval(db: Session, cve_id: str) -> dict:
    from backend.app.models import CTIRelationship
    cid = cve_id.upper()
    actors = set()
    for st, sk, tt, tk in db.execute(select(
        CTIRelationship.source_type, CTIRelationship.source_key,
        CTIRelationship.target_type, CTIRelationship.target_key)).all():
        if {st, tt} == {"actor", "cve"} and cid in (sk, tk):
            actors.add(sk if st == "actor" else tk)
    return _ok(f"{len(actors)} actor(s) linked to {cid}", {"cve_id": cid, "threat_actors": sorted(actors)})


def kev_retrieval(db: Session, cve_id: str) -> dict:
    from backend.app.models import KEVEntry
    k = db.execute(select(KEVEntry).where(KEVEntry.cve_id == cve_id.upper())).scalar_one_or_none()
    data = {} if k is None else {"in_kev": True, "date_added": k.date_added,
                                 "due_date": k.due_date, "known_ransomware": k.known_ransomware}
    return _ok(f"{cve_id} {'is' if k else 'is not'} in CISA KEV", data or {"in_kev": False})


def epss_retrieval(db: Session, cve_id: str) -> dict:
    from backend.app.models import EPSSScore
    e = db.execute(select(EPSSScore).where(EPSSScore.cve_id == cve_id.upper())).scalar_one_or_none()
    data = {} if e is None else {"epss_score": e.epss_score, "percentile": e.percentile}
    return _ok(f"EPSS for {cve_id}: {getattr(e, 'epss_score', 'n/a')}", data)


TOOL_REGISTRY = {
    "graph_investigation": (graph_investigation, "Graph subgraph for an entity"),
    "attack_path_investigation": (attack_path_investigation, "Attack paths for an alert"),
    "alert_investigation": (alert_investigation, "Full alert evidence"),
    "threat_actor_investigation": (threat_actor_investigation, "Threat-actor ecosystem evidence"),
    "campaign_investigation": (campaign_investigation, "Campaign ecosystem evidence"),
    "technique_investigation": (technique_investigation, "Technique evidence"),
    "risk_score_retrieval": (risk_score_retrieval, "ML risk + priority for a CVE"),
    "graph_metrics_retrieval": (graph_metrics_retrieval, "GDS centrality for an entity"),
    "wazuh_alert_retrieval": (wazuh_alert_retrieval, "Raw Wazuh alert + enrichment"),
    "misp_intel_retrieval": (misp_intel_retrieval, "MISP actors linked to a CVE"),
    "kev_retrieval": (kev_retrieval, "CISA KEV status for a CVE"),
    "epss_retrieval": (epss_retrieval, "EPSS score for a CVE"),
}


def run_tool(name: str, db: Session, params: dict) -> dict:
    if name not in TOOL_REGISTRY:
        raise ValueError(f"Unknown agent tool '{name}'")
    fn, _desc = TOOL_REGISTRY[name]
    try:
        return fn(db, **params)
    except Exception as exc:  # noqa: BLE001 - tool failures degrade, never crash the agent
        log.warning("tool %s failed: %s", name, exc)
        return {"ok": False, "summary": f"{name} failed: {exc}", "data": {}}
