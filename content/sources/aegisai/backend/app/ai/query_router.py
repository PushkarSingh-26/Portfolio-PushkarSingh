"""Query router + controlled Cypher (Phase 13.4 / 13.5).

Rule-based, deterministic intent classification + entity extraction decides which
data sources answer a question. Graph access only ever happens through a vetted,
parameterized template registry - the LLM never supplies or executes Cypher, so
arbitrary graph execution is impossible.
"""

import re
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

CVE_RE = re.compile(r"CVE-\d{4}-\d{3,7}", re.IGNORECASE)
TECH_RE = re.compile(r"\bT\d{4}(?:\.\d{3})?\b", re.IGNORECASE)
ALERT_RE = re.compile(r"(?:alert|#)\s*#?(\d+)", re.IGNORECASE)

# Pronouns that trigger context resolution for follow-up questions.
_PRONOUNS = ("that", "this", "it", "them", "those", "the actor", "the alert", "the cve")

# Each intent -> the data sources it draws on (for explainability).
INTENT_SOURCES = {
    "cve_risk": ["risk_scores", "epss", "kev", "correlations", "graph_metrics", "neo4j"],
    "actor_investigation": ["neo4j", "graph_metrics", "cti_relationships", "wazuh"],
    "attack_paths_actor": ["neo4j", "attack_paths"],
    "recent_alert_actors": ["wazuh", "cti_relationships"],
    "campaigns_wazuh": ["wazuh", "cti_relationships", "neo4j"],
    "dangerous_cves": ["priority", "risk_scores", "epss", "kev"],
    "top_techniques": ["wazuh", "graph_metrics"],
    "kev_actors": ["kev", "cti_relationships"],
    "triage_alerts": ["wazuh", "priority"],
    "top_attack_paths": ["attack_paths", "graph_insights"],
    "alert_investigation": ["wazuh", "neo4j", "attack_paths", "risk_scores"],
    "campaign_investigation": ["neo4j", "cti_relationships"],
    "technique_investigation": ["graph_metrics", "correlations", "wazuh"],
    "overview": ["graph_metrics", "wazuh", "risk_scores"],
}


@dataclass
class RouteResult:
    intent: str
    entities: dict = field(default_factory=dict)
    data_sources: list = field(default_factory=list)
    resolved_from_context: bool = False


def _extract_entities(question: str, db: Session) -> dict:
    ents: dict = {}
    if m := CVE_RE.search(question):
        ents["cve_id"] = m.group(0).upper()
    if m := TECH_RE.search(question):
        ents["technique_id"] = m.group(0).upper()
    if m := ALERT_RE.search(question):
        ents["alert_id"] = int(m.group(1))

    # Resolve actor / campaign names by matching against the DB (no free text).
    from backend.app.models import Campaign, ThreatActor

    lower = question.lower()
    for a in db.execute(select(ThreatActor.id, ThreatActor.actor_name)).all():
        if a.actor_name and a.actor_name.lower() in lower:
            ents["actor_id"], ents["actor_name"] = a.id, a.actor_name
            break
    for c in db.execute(select(Campaign.id, Campaign.campaign_name)).all():
        if c.campaign_name and c.campaign_name.lower() in lower:
            ents["campaign_id"], ents["campaign_name"] = c.id, c.campaign_name
            break
    return ents


def _classify(question: str, ents: dict) -> str:
    q = question.lower()
    has_path = "attack path" in q or "attack-path" in q or "path" in q

    if ents.get("cve_id"):
        return "cve_risk"
    if has_path and ents.get("actor_id"):
        return "attack_paths_actor"
    if has_path and ("highest" in q or "riskiest" in q or "top" in q or "most" in q):
        return "top_attack_paths"
    if ents.get("alert_id"):
        return "alert_investigation"
    if ents.get("technique_id"):
        return "technique_investigation"
    if ents.get("campaign_id") and not ents.get("actor_id"):
        return "campaign_investigation"
    if ents.get("actor_id"):
        return "attack_paths_actor" if has_path else "actor_investigation"

    if "kev" in q and "actor" in q:
        return "kev_actors"
    if ("recent" in q or "my" in q) and "alert" in q and "actor" in q:
        return "recent_alert_actors"
    if "campaign" in q and ("wazuh" in q or "current" in q or "activity" in q or "alert" in q):
        return "campaigns_wazuh"
    if ("dangerous" in q or "riskiest" in q or "most risky" in q or "highest risk" in q) and "cve" in q:
        return "dangerous_cves"
    if "technique" in q and ("most" in q or "frequent" in q or "observed" in q or "common" in q):
        return "top_techniques"
    if has_path:
        return "top_attack_paths"
    if "investigate first" in q or "triage" in q or ("which alert" in q and "first" in q):
        return "triage_alerts"
    if "alert" in q and ("first" in q or "priorit" in q):
        return "triage_alerts"
    if "actor" in q:
        return "recent_alert_actors"
    return "overview"


def route(question: str, db: Session, context: dict | None = None) -> RouteResult:
    ents = _extract_entities(question, db)
    resolved = False
    # Follow-up resolution: borrow last entities when a pronoun stands in.
    if context and not ents and any(p in question.lower() for p in _PRONOUNS):
        ents = dict(context.get("last_entities") or {})
        resolved = bool(ents)
    intent = _classify(question, ents)
    return RouteResult(intent=intent, entities=ents,
                       data_sources=INTENT_SOURCES.get(intent, []),
                       resolved_from_context=resolved)


# ── Controlled Cypher: vetted, read-only, parameterized templates only ──

CYPHER_TEMPLATES = {
    "actor_to_alerts": (
        "MATCH (al:Alert)-[:USES_TECHNIQUE]->(:Technique)-[:CORRELATED_TO]->"
        "(c:CVE)-[:ATTRIBUTED_TO]->(a:ThreatActor {actor_id:$actor_id}) "
        "RETURN DISTINCT al.alert_id AS alert_id, al.description AS description LIMIT $limit"
    ),
    "kev_actor_links": (
        "MATCH (c:CVE)-[:ATTRIBUTED_TO]->(a:ThreatActor) "
        "WHERE c.cve_id IN $cve_ids "
        "RETURN a.name AS actor, count(DISTINCT c) AS kev_cves "
        "ORDER BY kev_cves DESC LIMIT $limit"
    ),
}

_WRITE_TOKENS = ("create", "merge", "delete", "set ", "remove", "drop", "detach",
                 "call db.", "load csv")


def is_safe_cypher(cypher: str) -> bool:
    """Defense in depth: reject anything that could mutate the graph."""
    low = cypher.lower()
    return not any(tok in low for tok in _WRITE_TOKENS)


def run_template(name: str, params: dict) -> list[dict]:
    """Execute ONLY a registered, read-only template. Raises on anything else."""
    if name not in CYPHER_TEMPLATES:
        raise ValueError(f"Unknown Cypher template '{name}'")
    cypher = CYPHER_TEMPLATES[name]
    if not is_safe_cypher(cypher):
        raise ValueError(f"Template '{name}' failed the read-only safety check")
    from backend.app.graph.neo4j_client import get_client

    return get_client().run_read(cypher, params)
