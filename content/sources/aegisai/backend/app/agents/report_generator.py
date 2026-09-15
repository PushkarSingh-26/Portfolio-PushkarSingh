"""Investigation report generator (Phase 14.6 / 14.7 / 14.8).

Synthesizes the collected evidence + blast radius + tool log into a structured,
exportable report: executive summary, technical findings, threat intelligence,
attack-path analysis, risk assessment (explanation), blast radius, and
evidence-cited remediations. Every recommendation references supporting evidence
- no hallucinated remediation.
"""


def _by_tool(evidence: dict, tool: str) -> dict:
    for key, val in evidence.items():
        if key.endswith(tool):
            return val.get("data", {}) if isinstance(val, dict) else {}
    return {}


def _collect_confidences(evidence: dict) -> list:
    out = []
    for val in evidence.values():
        data = val.get("data", {}) if isinstance(val, dict) else {}
        if isinstance(data, dict) and isinstance(data.get("confidence"), (int, float)):
            out.append(data["confidence"])
    return out


def _risk_assessment(inv_type, evidence) -> dict:
    risk = _by_tool(evidence, "risk_score_retrieval")
    epss = _by_tool(evidence, "epss_retrieval")
    kev = _by_tool(evidence, "kev_retrieval")
    gm = _by_tool(evidence, "graph_metrics_retrieval")
    alert = _by_tool(evidence, "wazuh_alert_retrieval")
    reasons = []
    if alert.get("rule_level") is not None:
        reasons.append(f"Wazuh severity level {alert['rule_level']}")
    if kev.get("in_kev"):
        reasons.append(f"CISA KEV listed (actively exploited; due {kev.get('due_date') or 'n/a'})")
    if epss.get("epss_score") is not None:
        reasons.append(f"EPSS {epss['epss_score']:.3f} exploit probability")
    if risk.get("risk_score") is not None:
        reasons.append(f"ML risk {risk['risk_score']:.0f}/{risk.get('risk_level')}")
    if risk.get("priority_score") is not None:
        reasons.append(f"SOC priority {risk['priority_score']:.0f}/{risk.get('priority_level')}")
    if gm.get("pagerank"):
        reasons.append(f"graph PageRank {gm['pagerank']:.3f} (degree {gm.get('degree_centrality', 0):.0f})")
    level = (risk.get("priority_level") or risk.get("risk_level")
             or (alert.get("priority_level")) or "UNKNOWN")
    return {"level": level, "factors": reasons,
            "explanation": ("Risk driven by: " + "; ".join(reasons) + ".") if reasons
            else "Insufficient scoring evidence."}


def _recommendations(inv_type, evidence, blast) -> list:
    recs = []
    risk = _by_tool(evidence, "risk_score_retrieval")
    epss = _by_tool(evidence, "epss_retrieval")
    kev = _by_tool(evidence, "kev_retrieval")
    misp = _by_tool(evidence, "misp_intel_retrieval")
    alert_ev = _by_tool(evidence, "alert_investigation")
    actor_ev = _by_tool(evidence, "threat_actor_investigation")
    cve = risk.get("cve_id") or kev.get("cve_id") or epss.get("cve_id")

    if kev.get("in_kev"):
        recs.append({"action": "Patch immediately",
                     "detail": f"{cve} is in CISA KEV (actively exploited; due {kev.get('due_date') or 'n/a'}). "
                               "Apply the vendor fix per the CISA directive.",
                     "evidence": "kev_retrieval"})
    elif epss.get("epss_score", 0) and epss["epss_score"] >= 0.3:
        recs.append({"action": "Prioritize patching",
                     "detail": f"{cve} has high EPSS exploit probability ({epss['epss_score']:.3f}).",
                     "evidence": "epss_retrieval"})

    if (risk.get("priority_level") in ("CRITICAL", "HIGH")) or (risk.get("risk_level") in ("CRITICAL", "HIGH")):
        recs.append({"action": "Escalate for urgent remediation",
                     "detail": f"{cve or 'Target'} scored {risk.get('priority_level') or risk.get('risk_level')}.",
                     "evidence": "risk_score_retrieval"})

    actors = misp.get("threat_actors") or (alert_ev.get("findings", {}) if alert_ev else {}).get("threat_actors") or []
    if actors:
        recs.append({"action": "Review threat-actor activity / threat hunt",
                     "detail": f"Attributed actor(s): {', '.join(actors[:5])}. Hunt for their known TTPs.",
                     "evidence": "misp_intel_retrieval"})

    techniques = (alert_ev.get("findings", {}) if alert_ev else {}).get("techniques") or []
    if techniques:
        recs.append({"action": "Validate / tune detections",
                     "detail": f"Ensure coverage for ATT&CK technique(s): {', '.join(techniques[:5])}.",
                     "evidence": "alert_investigation"})

    affected_alerts = (blast or {}).get("counts", {}).get("affected_alerts", 0)
    if affected_alerts > 1:
        recs.append({"action": "Investigate related alerts",
                     "detail": f"{affected_alerts} alerts share entities in the blast radius; "
                               "review for a coordinated campaign.",
                     "evidence": "blast_radius"})

    if actor_ev.get("findings"):
        eco = actor_ev["findings"].get("ecosystem", {})
        if eco:
            recs.append({"action": "Increase monitoring",
                         "detail": f"Actor ecosystem spans {eco}. Raise monitoring on associated assets.",
                         "evidence": "threat_actor_investigation"})

    if not recs:
        recs.append({"action": "Continue monitoring",
                     "detail": "No urgent indicators in the gathered evidence; maintain standard monitoring.",
                     "evidence": "overview"})
    return recs


def build_report(inv_type: str, target: dict, evidence: dict, blast: dict,
                 tool_calls: list) -> dict:
    # Threat intelligence digest
    misp = _by_tool(evidence, "misp_intel_retrieval")
    alert_ev = _by_tool(evidence, "alert_investigation")
    actor_ev = _by_tool(evidence, "threat_actor_investigation")
    paths = _by_tool(evidence, "attack_path_investigation")

    findings = {}
    for key, val in evidence.items():
        if isinstance(val, dict):
            findings[key] = val.get("summary", "")

    risk = _risk_assessment(inv_type, evidence)
    recs = _recommendations(inv_type, evidence, blast)

    # Confidence: blend of evidence confidences and tool-call success rate.
    confs = _collect_confidences(evidence)
    ran = [c for c in tool_calls if c["status"] in ("ok", "error")]
    success_ratio = (sum(1 for c in ran if c["status"] == "ok") / len(ran)) if ran else 0.0
    avg_conf = (sum(confs) / len(confs)) if confs else None
    confidence = round((0.5 * avg_conf + 0.5 * success_ratio) if avg_conf is not None
                       else (success_ratio or 0.5), 2)

    sources = sorted({s for val in evidence.values()
                      if isinstance(val, dict)
                      for s in (val.get("data", {}).get("data_sources", []) if isinstance(val.get("data"), dict) else [])}
                     | {c["tool"] for c in tool_calls if c["status"] == "ok"})

    attack_paths = paths if isinstance(paths, list) else []
    actors = misp.get("threat_actors") or (alert_ev.get("findings", {}) if alert_ev else {}).get("threat_actors") or []

    exec_summary = (
        f"Autonomous {inv_type} investigation of {target}. "
        f"Risk level: {risk['level']}. "
        f"{len(attack_paths)} attack path(s); "
        f"{(blast or {}).get('total_affected', 0)} entities in blast radius; "
        f"{len(actors)} attributed actor(s); {len(recs)} recommendation(s). "
        f"Confidence {confidence}."
    )

    return {
        "executive_summary": exec_summary,
        "technical_findings": findings,
        "threat_intelligence": {"threat_actors": actors,
                                "actor_ecosystem": actor_ev.get("findings", {}).get("ecosystem", {})
                                if actor_ev.get("findings") else {}},
        "attack_path_analysis": {"count": len(attack_paths),
                                 "paths": [p.get("path") for p in attack_paths[:15]]},
        "risk_assessment": risk,
        "blast_radius": blast or {},
        "recommendations": recs,
        "confidence_score": confidence,
        "evidence_sources": sources,
    }
