"""AI Threat Analyst orchestrator (Phase 13.1 / 13.10).

Pipeline: route question -> gather real evidence -> generate grounded answer.
Maintains lightweight per-session memory so follow-up questions ("show me more
about that actor") resolve against the prior turn's entities.
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.app.ai import investigation_engine, query_router, response_generator
from backend.app.ai.providers import get_provider

# In-process conversation memory: session_id -> {history, last_entities}.
_SESSIONS: dict[str, dict] = {}
_MAX_HISTORY = 20


def _session(session_id: str | None) -> dict:
    if not session_id:
        return {"history": [], "last_entities": {}}
    return _SESSIONS.setdefault(session_id, {"history": [], "last_entities": {}})


def _respond(question, intent, entities, db, *, resolved=False, session=None,
             session_id=None) -> dict:
    evidence = investigation_engine.gather_evidence(intent, entities, db)
    answer, generator = response_generator.generate(question, evidence, get_provider())
    response = {
        "question": question,
        "answer": answer,
        "intent": intent,
        "entities": entities,
        "findings": evidence.get("findings", {}),
        "supporting_entities": evidence.get("supporting_entities", []),
        "graph_relationships": evidence.get("graph_relationships", []),
        "risk_justification": evidence.get("risk_justification", ""),
        "confidence": evidence.get("confidence", 0.0),
        "data_sources": evidence.get("data_sources", []),
        "generator": generator,
        "resolved_from_context": resolved,
    }
    if session is not None:
        session["history"].append({"q": question, "intent": intent})
        del session["history"][:-_MAX_HISTORY]
        if entities:
            session["last_entities"] = entities
        response["session_id"] = session_id
    return response


def ask(question: str, db: Session, session_id: str | None = None) -> dict:
    """Answer a natural-language question (with optional multi-turn memory)."""
    session = _session(session_id) if session_id else None
    context = {"last_entities": session["last_entities"]} if session else None
    route = query_router.route(question, db, context)
    return _respond(question, route.intent, route.entities, db,
                    resolved=route.resolved_from_context, session=session,
                    session_id=session_id)


# ── Explicit workflow entrypoints (bypass classification) ───

def investigate_alert(alert_id: int, db: Session) -> dict:
    return _respond(f"Investigate alert {alert_id}", "alert_investigation",
                    {"alert_id": alert_id}, db)


def investigate_cve(cve_id: str, db: Session) -> dict:
    return _respond(f"Why is {cve_id} high risk?", "cve_risk",
                    {"cve_id": cve_id.upper()}, db)


def investigate_actor(actor_id: int, db: Session, name: str | None = None) -> dict:
    return _respond(f"Investigate threat actor {name or actor_id}", "actor_investigation",
                    {"actor_id": actor_id, "actor_name": name}, db)


def investigate_campaign(campaign_id: int, db: Session, name: str | None = None) -> dict:
    return _respond(f"Investigate campaign {name or campaign_id}", "campaign_investigation",
                    {"campaign_id": campaign_id, "campaign_name": name}, db)


def investigate_path(alert_id: int, db: Session) -> dict:
    return _respond(f"Show attack paths for alert {alert_id}", "alert_investigation",
                    {"alert_id": alert_id}, db)


def clear_session(session_id: str) -> None:
    _SESSIONS.pop(session_id, None)
