"""Investigation memory (Phase 14.11).

Persists each investigation (plan, tool-call log, trimmed evidence, full report)
and supports history, lineage (continue), and comparison. Heavy raw evidence is
trimmed to summaries on save - the full structured findings live in the report.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session


def _trim_evidence(evidence: dict) -> dict:
    out = {}
    for key, val in evidence.items():
        if isinstance(val, dict):
            out[key] = {"ok": val.get("ok"), "summary": val.get("summary", "")}
    return out


def save(db: Session, *, investigation_type: str, target: str, plan: list,
         tool_calls: list, evidence: dict, report: dict, confidence: float,
         parent_id: int | None = None):
    from backend.app.models import AgentInvestigation

    inv = AgentInvestigation(
        investigation_type=investigation_type, target=target, status="completed",
        confidence=confidence, plan=plan, tool_calls=tool_calls,
        evidence=_trim_evidence(evidence), report=report, parent_id=parent_id,
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv


def get(db: Session, investigation_id: int):
    from backend.app.models import AgentInvestigation
    return db.get(AgentInvestigation, investigation_id)


def history(db: Session, limit: int = 50, investigation_type: str | None = None) -> list:
    from backend.app.models import AgentInvestigation
    q = select(AgentInvestigation).order_by(AgentInvestigation.id.desc())
    if investigation_type:
        q = q.where(AgentInvestigation.investigation_type == investigation_type)
    return db.execute(q.limit(limit)).scalars().all()


def lineage(db: Session, investigation_id: int) -> list:
    """Walk the parent chain from this investigation back to its root."""
    from backend.app.models import AgentInvestigation
    chain, current = [], db.get(AgentInvestigation, investigation_id)
    seen = set()
    while current is not None and current.id not in seen:
        seen.add(current.id)
        chain.append(current)
        current = db.get(AgentInvestigation, current.parent_id) if current.parent_id else None
    return chain


def compare(db: Session, id_a: int, id_b: int) -> dict:
    a, b = get(db, id_a), get(db, id_b)
    if a is None or b is None:
        return {"error": "one or both investigations not found"}

    def _summ(inv):
        r = inv.report or {}
        return {"id": inv.id, "type": inv.investigation_type, "target": inv.target,
                "confidence": inv.confidence, "risk_level": (r.get("risk_assessment") or {}).get("level"),
                "recommendations": len(r.get("recommendations", [])),
                "blast_total": (r.get("blast_radius") or {}).get("total_affected", 0)}
    return {"a": _summ(a), "b": _summ(b)}
