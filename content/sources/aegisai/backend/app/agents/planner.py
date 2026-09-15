"""Investigation planner (Phase 14.3).

Builds an explainable, ordered task graph for each investigation type. Steps may
reference values discovered by earlier steps via "$placeholders" (e.g. the top
related CVE found while investigating an alert), which the executor resolves.
"""


def _step(n, tool, params, rationale):
    return {"step": n, "tool": tool, "params": params, "rationale": rationale}


def plan(investigation_type: str, target: dict) -> list[dict]:
    t = investigation_type

    if t == "alert":
        aid = target["alert_id"]
        steps = [
            ("wazuh_alert_retrieval", {"alert_id": aid}, "Retrieve the raw Wazuh alert and its enrichment"),
            ("alert_investigation", {"alert_id": aid}, "Correlate alert -> technique -> CVE -> actor"),
            ("attack_path_investigation", {"alert_id": aid}, "Enumerate attack paths from the alert"),
            ("risk_score_retrieval", {"cve_id": "$cve_id"}, "ML risk + priority for the top related CVE"),
            ("epss_retrieval", {"cve_id": "$cve_id"}, "EPSS exploit probability of the CVE"),
            ("kev_retrieval", {"cve_id": "$cve_id"}, "CISA KEV (active-exploitation) status"),
            ("graph_metrics_retrieval", {"entity_type": "CVE", "entity_id": "$cve_id"}, "Graph centrality of the CVE"),
            ("misp_intel_retrieval", {"cve_id": "$cve_id"}, "MISP threat-actor attribution"),
        ]
    elif t == "cve":
        cid = target["cve_id"]
        steps = [
            ("risk_score_retrieval", {"cve_id": cid}, "ML risk + priority score"),
            ("epss_retrieval", {"cve_id": cid}, "EPSS exploit probability"),
            ("kev_retrieval", {"cve_id": cid}, "CISA KEV status"),
            ("graph_metrics_retrieval", {"entity_type": "CVE", "entity_id": cid}, "Graph centrality"),
            ("misp_intel_retrieval", {"cve_id": cid}, "Threat-actor attribution"),
            ("graph_investigation", {"entity_type": "cve", "entity_id": cid}, "CVE relationship subgraph"),
        ]
    elif t == "actor":
        aid = target["actor_id"]
        name = target.get("name")
        steps = [
            ("threat_actor_investigation", {"actor_id": aid, "name": name}, "Actor ecosystem + reachable alerts"),
            ("graph_metrics_retrieval", {"entity_type": "ThreatActor", "entity_id": aid}, "Actor graph influence"),
            ("graph_investigation", {"entity_type": "actor", "entity_id": aid}, "Actor relationship subgraph"),
        ]
    elif t == "campaign":
        cid = target["campaign_id"]
        steps = [
            ("campaign_investigation", {"campaign_id": cid, "name": target.get("name")}, "Campaign ecosystem"),
            ("graph_investigation", {"entity_type": "campaign", "entity_id": cid}, "Campaign relationship subgraph"),
        ]
    elif t == "technique":
        tid = target["technique_id"]
        steps = [
            ("technique_investigation", {"technique_id": tid}, "Technique correlations + alert frequency"),
            ("graph_metrics_retrieval", {"entity_type": "Technique", "entity_id": tid}, "Technique graph centrality"),
        ]
    elif t == "community":
        steps = []  # community investigations are driven entirely by blast radius
    else:
        raise ValueError(f"Unknown investigation type '{investigation_type}'")

    return [_step(i, tool, params, rationale) for i, (tool, params, rationale) in enumerate(steps, 1)]
