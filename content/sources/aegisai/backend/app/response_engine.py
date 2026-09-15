"""Human-in-the-loop response engine (Phase 19).

Turns evidence-based agent recommendations into approvable response actions,
enforces an approval gate, executes ONLY approved actions through the existing
ShuffleProvider (reused), verifies execution, and records a complete audit trail.
Nothing executes automatically - every transition requires an explicit call and
is logged in response_audit.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

log = logging.getLogger("response.engine")

# Recommendation status lifecycle.
PENDING, APPROVED, REJECTED, EXECUTED, VERIFIED, FAILED = (
    "pending", "approved", "rejected", "executed", "verified", "failed")


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _action_type(action: str) -> str:
    a = (action or "").lower()
    if "patch" in a:
        return "patch"
    if "escalate" in a:
        return "escalate"
    if "hunt" in a or "actor" in a:
        return "threat_hunt"
    if "detection" in a:
        return "tune_detection"
    if "investigate" in a:
        return "investigate"
    if "monitor" in a:
        return "monitor"
    return "review"


def _audit(db: Session, rec_id: int, event: str, actor: str = "system", detail: dict | None = None):
    from backend.app.models import ResponseAudit
    db.add(ResponseAudit(recommendation_id=rec_id, event=event, actor=actor,
                         detail=detail or {}, created_at=_now()))


def _serialize(r) -> dict:
    return {"id": r.id, "source_type": r.source_type, "source_id": r.source_id,
            "action_type": r.action_type, "title": r.title, "description": r.description,
            "severity": r.severity, "rationale": r.rationale, "evidence": r.evidence,
            "confidence": r.confidence, "status": r.status, "approved_by": r.approved_by,
            "approved_at": r.approved_at, "executed_at": r.executed_at, "verified": r.verified,
            "execution_result": r.execution_result, "created_at": r.created_at}


# ── generation ──────────────────────────────────────────────

def generate_from_investigation(db: Session, investigation_id: int) -> list[dict]:
    from backend.app.models import AgentInvestigation, ResponseRecommendation

    inv = db.get(AgentInvestigation, investigation_id)
    if inv is None:
        raise ValueError(f"Investigation {investigation_id} not found")
    report = inv.report or {}
    level = (report.get("risk_assessment") or {}).get("level", "MEDIUM")

    existing = {
        (r.source_id, r.action_type, r.title)
        for r in db.execute(select(ResponseRecommendation)
                            .where(ResponseRecommendation.source_type == "investigation",
                                   ResponseRecommendation.source_id == str(inv.id))).scalars().all()
    }
    created = []
    for rec in report.get("recommendations", []):
        action_type = _action_type(rec.get("action", ""))
        title = rec.get("action", "Response action")
        key = (str(inv.id), action_type, title)
        if key in existing:
            continue
        row = ResponseRecommendation(
            source_type="investigation", source_id=str(inv.id), action_type=action_type,
            title=title, description=rec.get("detail", ""), severity=level,
            rationale=f"Derived from agent evidence: {rec.get('evidence', 'n/a')}",
            evidence={"evidence_tool": rec.get("evidence"), "target": inv.target,
                      "investigation_id": inv.id},
            confidence=inv.confidence or 0.0, status=PENDING, created_at=_now())
        db.add(row)
        db.flush()
        _audit(db, row.id, "generated", "system",
               {"source": f"investigation:{inv.id}", "action_type": action_type})
        created.append(row)
    db.commit()
    return [_serialize(r) for r in created]


def generate_recent(db: Session, limit: int = 10) -> dict:
    from backend.app.models import AgentInvestigation
    ids = [i.id for i in db.execute(
        select(AgentInvestigation).order_by(AgentInvestigation.id.desc()).limit(limit)
    ).scalars().all()]
    total = 0
    for iid in ids:
        total += len(generate_from_investigation(db, iid))
    return {"investigations_scanned": len(ids), "recommendations_created": total}


# ── query ───────────────────────────────────────────────────

def list_recommendations(db, status=None, severity=None, limit=100) -> list[dict]:
    from backend.app.models import ResponseRecommendation
    q = select(ResponseRecommendation).order_by(ResponseRecommendation.id.desc())
    if status:
        q = q.where(ResponseRecommendation.status == status)
    if severity:
        q = q.where(ResponseRecommendation.severity == severity.upper())
    return [_serialize(r) for r in db.execute(q.limit(limit)).scalars().all()]


def get(db, rec_id: int) -> dict | None:
    from backend.app.models import ResponseRecommendation
    r = db.get(ResponseRecommendation, rec_id)
    return _serialize(r) if r else None


def audit_trail(db, rec_id: int) -> list[dict]:
    from backend.app.models import ResponseAudit
    rows = db.execute(select(ResponseAudit).where(ResponseAudit.recommendation_id == rec_id)
                      .order_by(ResponseAudit.id)).scalars().all()
    return [{"id": a.id, "event": a.event, "actor": a.actor, "detail": a.detail,
             "created_at": a.created_at} for a in rows]


def recent_audit(db, limit: int = 100) -> list[dict]:
    from backend.app.models import ResponseAudit
    rows = db.execute(select(ResponseAudit).order_by(ResponseAudit.id.desc()).limit(limit)).scalars().all()
    return [{"id": a.id, "recommendation_id": a.recommendation_id, "event": a.event,
             "actor": a.actor, "detail": a.detail, "created_at": a.created_at} for a in rows]


# ── approval workflow (each transition is explicit + audited) ──

def _load(db, rec_id):
    from backend.app.models import ResponseRecommendation
    r = db.get(ResponseRecommendation, rec_id)
    if r is None:
        raise ValueError(f"Recommendation {rec_id} not found")
    return r


def approve(db, rec_id: int, approver: str) -> dict:
    r = _load(db, rec_id)
    if r.status != PENDING:
        raise PermissionError(f"Cannot approve a '{r.status}' recommendation")
    r.status, r.approved_by, r.approved_at = APPROVED, approver, _now()
    _audit(db, r.id, "approved", approver, {})
    db.commit()
    return _serialize(r)


def reject(db, rec_id: int, approver: str, reason: str = "") -> dict:
    r = _load(db, rec_id)
    if r.status != PENDING:
        raise PermissionError(f"Cannot reject a '{r.status}' recommendation")
    r.status, r.approved_by, r.approved_at = REJECTED, approver, _now()
    _audit(db, r.id, "rejected", approver, {"reason": reason})
    db.commit()
    return _serialize(r)


def execute(db, rec_id: int, actor: str = "system") -> dict:
    """Execute an APPROVED action via ShuffleProvider. Refuses otherwise."""
    from backend.app.ticketing import execute_action

    r = _load(db, rec_id)
    if r.status != APPROVED:
        raise PermissionError(
            f"Refusing to execute: recommendation is '{r.status}', not 'approved'. "
            "Analyst approval is required before execution.")
    payload = {"action_type": r.action_type, "title": r.title, "description": r.description or "",
               "severity": r.severity, "source_type": r.source_type, "source_id": r.source_id,
               "recommendation_id": r.id}
    result = execute_action(payload)
    r.execution_result = result
    r.executed_at = _now()
    r.status = EXECUTED if result else FAILED
    _audit(db, r.id, "executed", actor, {"provider": result.get("provider"),
                                         "reference": result.get("ticket_id")})
    db.commit()
    return _serialize(r)


def verify(db, rec_id: int, actor: str = "system") -> dict:
    """Verify that the executed action was accepted by the SOAR provider."""
    r = _load(db, rec_id)
    if r.status != EXECUTED:
        raise PermissionError(f"Cannot verify a '{r.status}' recommendation (must be executed)")
    res = r.execution_result or {}
    ok = bool(res.get("status") in ("created", "triggered", "accepted") or res.get("ticket_id"))
    verification = {"verified": ok, "provider": res.get("provider"),
                    "reference": res.get("ticket_id"), "checked_at": _now().isoformat()}
    r.verified = ok
    r.status = VERIFIED if ok else FAILED
    _audit(db, r.id, "verified" if ok else "failed", actor, verification)
    db.commit()
    return _serialize(r)


def stats(db) -> dict:
    from sqlalchemy import func
    from backend.app.models import ResponseRecommendation
    rows = db.execute(select(ResponseRecommendation.status, func.count())
                      .group_by(ResponseRecommendation.status)).all()
    return {"by_status": {s: c for s, c in rows},
            "total": sum(c for _, c in rows)}
