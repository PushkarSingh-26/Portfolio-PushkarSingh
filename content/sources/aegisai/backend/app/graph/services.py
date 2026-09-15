"""Graph analytics + investigation workflows over the Neo4j knowledge graph.

Each subgraph function returns a visualization-ready payload:
    {"nodes": [{"id","label","name","props"}...], "edges": [{"source","target","type"}...],
     "summary": {...}}
so the dashboard can render an interactive network directly.
"""

from backend.app.graph.neo4j_client import get_client

DEFAULT_CAP = 300


def _node(node_id: str, label: str, name: str, **props) -> dict:
    return {"id": f"{label}:{node_id}", "label": label, "name": name or node_id, "props": props}


def _edge(src_label, src_id, tgt_label, tgt_id, rel) -> dict:
    return {"source": f"{src_label}:{src_id}", "target": f"{tgt_label}:{tgt_id}", "type": rel}


# ── Stats ───────────────────────────────────────────────────

def graph_stats() -> dict:
    client = get_client()
    nodes = client.run_read(
        "MATCH (n) RETURN labels(n)[0] AS label, count(*) AS c ORDER BY c DESC"
    )
    rels = client.run_read(
        "MATCH ()-[r]->() RETURN type(r) AS rel, count(*) AS c ORDER BY c DESC"
    )
    node_counts = {r["label"]: r["c"] for r in nodes}
    rel_counts = {r["rel"]: r["c"] for r in rels}
    return {
        "node_counts": node_counts,
        "relationship_counts": rel_counts,
        "total_nodes": sum(node_counts.values()),
        "total_relationships": sum(rel_counts.values()),
    }


def top_entities(label: str | None = None, limit: int = 15) -> list[dict]:
    """Most-connected nodes by degree (optionally restricted to a label)."""
    client = get_client()
    label_filter = f":{label}" if label else ""
    cypher = (
        f"MATCH (n{label_filter}) "
        "WITH n, count{ (n)--() } AS degree "
        "WHERE degree > 0 "
        "RETURN labels(n)[0] AS label, "
        "coalesce(n.name, n.cve_id, n.technique_id, n.agent_id, n.key) AS name, "
        "degree ORDER BY degree DESC LIMIT $limit"
    )
    return client.run_read(cypher, {"limit": limit})


def degree_stats() -> dict:
    client = get_client()
    rows = client.run_read(
        "MATCH (n) WITH n, count{ (n)--() } AS d "
        "RETURN labels(n)[0] AS label, avg(d) AS avg_degree, max(d) AS max_degree "
        "ORDER BY avg_degree DESC"
    )
    return {r["label"]: {"avg_degree": round(r["avg_degree"], 2), "max_degree": r["max_degree"]}
            for r in rows}


# ── Investigation subgraphs ─────────────────────────────────

def alert_investigation(alert_id: int, cap: int = DEFAULT_CAP) -> dict:
    """Alert -> Technique -> CVE -> ThreatActor -> Malware/Campaign."""
    client = get_client()
    rows = client.run_read(
        "MATCH (al:Alert {alert_id:$id})-[:USES_TECHNIQUE]->(t:Technique) "
        "OPTIONAL MATCH (t)-[:CORRELATED_TO]->(c:CVE) "
        "OPTIONAL MATCH (c)-[:ATTRIBUTED_TO]->(a:ThreatActor) "
        "OPTIONAL MATCH (a)-[:USES]->(m:Malware) "
        "OPTIONAL MATCH (a)-[:RUNS]->(ca:Campaign) "
        "RETURN al.alert_id AS alert, al.description AS adesc, t.technique_id AS technique, "
        "c.cve_id AS cve, a.actor_id AS actor_id, a.name AS actor, "
        "m.malware_id AS malware_id, m.name AS malware, "
        "ca.campaign_id AS campaign_id, ca.name AS campaign LIMIT $cap",
        {"id": alert_id, "cap": cap},
    )
    if not rows:
        return {"nodes": [], "edges": [], "summary": {}}

    nodes, edges, seen = {}, set(), set()

    def add_node(n):
        nodes[n["id"]] = n

    alert = rows[0]
    add_node(_node(str(alert_id), "Alert", alert["adesc"] or f"alert {alert_id}"))
    techs, cves, actors, malware, campaigns = set(), set(), set(), set(), set()
    for r in rows:
        if r["technique"]:
            techs.add(r["technique"])
            add_node(_node(r["technique"], "Technique", r["technique"]))
            edges.add(("Alert", alert_id, "Technique", r["technique"], "USES_TECHNIQUE"))
        if r["cve"]:
            cves.add(r["cve"])
            add_node(_node(r["cve"], "CVE", r["cve"]))
            edges.add(("Technique", r["technique"], "CVE", r["cve"], "CORRELATED_TO"))
        if r["actor"]:
            actors.add(r["actor"])
            add_node(_node(str(r["actor_id"]), "ThreatActor", r["actor"]))
            edges.add(("CVE", r["cve"], "ThreatActor", r["actor_id"], "ATTRIBUTED_TO"))
        if r["malware"]:
            malware.add(r["malware"])
            add_node(_node(str(r["malware_id"]), "Malware", r["malware"]))
            edges.add(("ThreatActor", r["actor_id"], "Malware", r["malware_id"], "USES"))
        if r["campaign"]:
            campaigns.add(r["campaign"])
            add_node(_node(str(r["campaign_id"]), "Campaign", r["campaign"]))
            edges.add(("ThreatActor", r["actor_id"], "Campaign", r["campaign_id"], "RUNS"))

    return {
        "nodes": list(nodes.values()),
        "edges": [_edge(*e) for e in edges],
        "summary": {"techniques": len(techs), "cves": len(cves), "threat_actors": len(actors),
                    "malware": len(malware), "campaigns": len(campaigns)},
    }


def actor_investigation(actor_id: int, cap: int = DEFAULT_CAP) -> dict:
    """ThreatActor -> Malware/Campaign and ThreatActor <- CVE <- Technique <- Alert."""
    client = get_client()
    rows = client.run_read(
        "MATCH (a:ThreatActor {actor_id:$id}) "
        "OPTIONAL MATCH (a)-[:USES]->(m:Malware) "
        "OPTIONAL MATCH (a)-[:RUNS]->(ca:Campaign) "
        "OPTIONAL MATCH (c:CVE)-[:ATTRIBUTED_TO]->(a) "
        "OPTIONAL MATCH (al:Alert)-[:USES_TECHNIQUE]->(:Technique)-[:CORRELATED_TO]->(c) "
        "RETURN a.actor_id AS actor_id, a.name AS actor, m.malware_id AS malware_id, m.name AS malware, "
        "ca.campaign_id AS campaign_id, ca.name AS campaign, c.cve_id AS cve, "
        "al.alert_id AS alert_id, al.description AS adesc LIMIT $cap",
        {"id": actor_id, "cap": cap},
    )
    if not rows:
        return {"nodes": [], "edges": [], "summary": {}}
    nodes, edges = {}, set()
    a0 = rows[0]
    nodes[f"ThreatActor:{actor_id}"] = _node(str(actor_id), "ThreatActor", a0["actor"])
    cves, malware, campaigns, alerts = set(), set(), set(), set()
    for r in rows:
        if r["malware"]:
            malware.add(r["malware"])
            nodes[f"Malware:{r['malware_id']}"] = _node(str(r["malware_id"]), "Malware", r["malware"])
            edges.add(("ThreatActor", actor_id, "Malware", r["malware_id"], "USES"))
        if r["campaign"]:
            campaigns.add(r["campaign"])
            nodes[f"Campaign:{r['campaign_id']}"] = _node(str(r["campaign_id"]), "Campaign", r["campaign"])
            edges.add(("ThreatActor", actor_id, "Campaign", r["campaign_id"], "RUNS"))
        if r["cve"]:
            cves.add(r["cve"])
            nodes[f"CVE:{r['cve']}"] = _node(r["cve"], "CVE", r["cve"])
            edges.add(("CVE", r["cve"], "ThreatActor", actor_id, "ATTRIBUTED_TO"))
        if r["alert_id"]:
            alerts.add(r["alert_id"])
            nodes[f"Alert:{r['alert_id']}"] = _node(str(r["alert_id"]), "Alert", r["adesc"] or f"alert {r['alert_id']}")
    return {"nodes": list(nodes.values()), "edges": [_edge(*e) for e in edges],
            "summary": {"cves": len(cves), "malware": len(malware),
                        "campaigns": len(campaigns), "alerts": len(alerts)}}


def cve_investigation(cve_id: str, cap: int = DEFAULT_CAP) -> dict:
    """CVE -> Techniques -> Alerts and CVE -> ThreatActors, plus RiskScore."""
    client = get_client()
    rows = client.run_read(
        "MATCH (c:CVE {cve_id:$id}) "
        "OPTIONAL MATCH (t:Technique)-[:CORRELATED_TO]->(c) "
        "OPTIONAL MATCH (al:Alert)-[:USES_TECHNIQUE]->(t) "
        "OPTIONAL MATCH (c)-[:ATTRIBUTED_TO]->(a:ThreatActor) "
        "RETURN c.cve_id AS cve, t.technique_id AS technique, al.alert_id AS alert_id, "
        "al.description AS adesc, a.actor_id AS actor_id, a.name AS actor LIMIT $cap",
        {"id": cve_id.upper(), "cap": cap},
    )
    if not rows:
        return {"nodes": [], "edges": [], "summary": {}}
    nodes, edges = {}, set()
    nodes[f"CVE:{cve_id.upper()}"] = _node(cve_id.upper(), "CVE", cve_id.upper())
    techs, alerts, actors = set(), set(), set()
    for r in rows:
        if r["technique"]:
            techs.add(r["technique"])
            nodes[f"Technique:{r['technique']}"] = _node(r["technique"], "Technique", r["technique"])
            edges.add(("Technique", r["technique"], "CVE", r["cve"], "CORRELATED_TO"))
        if r["alert_id"]:
            alerts.add(r["alert_id"])
            nodes[f"Alert:{r['alert_id']}"] = _node(str(r["alert_id"]), "Alert", r["adesc"] or f"alert {r['alert_id']}")
            edges.add(("Alert", r["alert_id"], "Technique", r["technique"], "USES_TECHNIQUE"))
        if r["actor"]:
            actors.add(r["actor"])
            nodes[f"ThreatActor:{r['actor_id']}"] = _node(str(r["actor_id"]), "ThreatActor", r["actor"])
            edges.add(("CVE", r["cve"], "ThreatActor", r["actor_id"], "ATTRIBUTED_TO"))
    return {"nodes": list(nodes.values()), "edges": [_edge(*e) for e in edges],
            "summary": {"techniques": len(techs), "alerts": len(alerts), "threat_actors": len(actors)}}


def campaign_investigation(campaign_id: int, cap: int = DEFAULT_CAP) -> dict:
    client = get_client()
    rows = client.run_read(
        "MATCH (ca:Campaign {campaign_id:$id}) "
        "OPTIONAL MATCH (a:ThreatActor)-[:RUNS]->(ca) "
        "OPTIONAL MATCH (ca)-[:USES_IOC]->(i:IOC) "
        "OPTIONAL MATCH (a)-[:USES]->(m:Malware) "
        "RETURN ca.campaign_id AS cid, ca.name AS campaign, a.actor_id AS actor_id, a.name AS actor, "
        "i.ioc_id AS ioc_id, i.value AS ioc, m.malware_id AS malware_id, m.name AS malware LIMIT $cap",
        {"id": campaign_id, "cap": cap},
    )
    if not rows:
        return {"nodes": [], "edges": [], "summary": {}}
    nodes, edges = {}, set()
    nodes[f"Campaign:{campaign_id}"] = _node(str(campaign_id), "Campaign", rows[0]["campaign"])
    actors, iocs, malware = set(), set(), set()
    for r in rows:
        if r["actor"]:
            actors.add(r["actor"])
            nodes[f"ThreatActor:{r['actor_id']}"] = _node(str(r["actor_id"]), "ThreatActor", r["actor"])
            edges.add(("ThreatActor", r["actor_id"], "Campaign", campaign_id, "RUNS"))
        if r["ioc"]:
            iocs.add(r["ioc"])
            nodes[f"IOC:{r['ioc_id']}"] = _node(str(r["ioc_id"]), "IOC", r["ioc"])
            edges.add(("Campaign", campaign_id, "IOC", r["ioc_id"], "USES_IOC"))
        if r["malware"]:
            malware.add(r["malware"])
            nodes[f"Malware:{r['malware_id']}"] = _node(str(r["malware_id"]), "Malware", r["malware"])
            edges.add(("ThreatActor", r["actor_id"], "Malware", r["malware_id"], "USES"))
    return {"nodes": list(nodes.values()), "edges": [_edge(*e) for e in edges],
            "summary": {"threat_actors": len(actors), "iocs": len(iocs), "malware": len(malware)}}


def malware_investigation(malware_id: int, cap: int = DEFAULT_CAP) -> dict:
    client = get_client()
    rows = client.run_read(
        "MATCH (m:Malware {malware_id:$id}) "
        "OPTIONAL MATCH (a:ThreatActor)-[:USES]->(m) "
        "OPTIONAL MATCH (a)-[:RUNS]->(ca:Campaign) "
        "RETURN m.malware_id AS mid, m.name AS malware, a.actor_id AS actor_id, a.name AS actor, "
        "ca.campaign_id AS campaign_id, ca.name AS campaign LIMIT $cap",
        {"id": malware_id, "cap": cap},
    )
    if not rows:
        return {"nodes": [], "edges": [], "summary": {}}
    nodes, edges = {}, set()
    nodes[f"Malware:{malware_id}"] = _node(str(malware_id), "Malware", rows[0]["malware"])
    actors, campaigns = set(), set()
    for r in rows:
        if r["actor"]:
            actors.add(r["actor"])
            nodes[f"ThreatActor:{r['actor_id']}"] = _node(str(r["actor_id"]), "ThreatActor", r["actor"])
            edges.add(("ThreatActor", r["actor_id"], "Malware", malware_id, "USES"))
        if r["campaign"]:
            campaigns.add(r["campaign"])
            nodes[f"Campaign:{r['campaign_id']}"] = _node(str(r["campaign_id"]), "Campaign", r["campaign"])
            edges.add(("ThreatActor", r["actor_id"], "Campaign", r["campaign_id"], "RUNS"))
    return {"nodes": list(nodes.values()), "edges": [_edge(*e) for e in edges],
            "summary": {"threat_actors": len(actors), "campaigns": len(campaigns)}}


_LABEL_KEY = {
    "technique": ("Technique", "technique_id"), "cve": ("CVE", "cve_id"),
    "actor": ("ThreatActor", "actor_id"), "malware": ("Malware", "malware_id"),
    "campaign": ("Campaign", "campaign_id"), "agent": ("Agent", "agent_id"),
    "alert": ("Alert", "alert_id"),
}


def shortest_path(from_type: str, from_key, to_type: str, to_key, max_hops: int = 6) -> dict:
    """Shortest path between any two entities (by type + key)."""
    if from_type not in _LABEL_KEY or to_type not in _LABEL_KEY:
        raise ValueError(f"Unknown entity type. Allowed: {sorted(_LABEL_KEY)}")
    client = get_client()
    fl, fk = _LABEL_KEY[from_type]
    tl, tk = _LABEL_KEY[to_type]

    def _coerce(label, value):
        return int(value) if label in ("ThreatActor", "Malware", "Campaign", "Alert") and str(value).isdigit() else value

    cypher = (
        f"MATCH (a:{fl} {{{fk}:$from}}), (b:{tl} {{{tk}:$to}}), "
        f"p = shortestPath((a)-[*..{max_hops}]-(b)) "
        "RETURN [n IN nodes(p) | {label: labels(n)[0], "
        "name: coalesce(n.name, n.cve_id, n.technique_id, n.agent_id, n.key, toString(n.alert_id))}] AS nodes, "
        "[r IN relationships(p) | type(r)] AS rels, length(p) AS hops"
    )
    res = client.run_read(cypher, {"from": _coerce(fl, from_key), "to": _coerce(tl, to_key)})
    if not res:
        return {"found": False, "hops": None, "path": []}
    row = res[0]
    return {"found": True, "hops": row["hops"], "nodes": row["nodes"], "relationships": row["rels"]}
