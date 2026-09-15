"""Human-in-the-loop response API (Phase 19).

Analysts review, approve/reject, and only then execute (via Shuffle) response
recommendations. Every step is audited. No endpoint executes anything without a
recorded prior approval.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app import response_engine as engine
from backend.app.database import get_db

router = APIRouter(prefix="/response", tags=["response"])


class GenerateRequest(BaseModel):
    investigation_id: int | None = None
    limit: int = 10


class ApproveRequest(BaseModel):
    approver: str


class RejectRequest(BaseModel):
    approver: str
    reason: str = ""


class ActorRequest(BaseModel):
    actor: str = "analyst"


def _guard(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.get("/recommendations")
def list_recommendations(status: str | None = Query(None), severity: str | None = Query(None),
                         limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db)):
    return engine.list_recommendations(db, status=status, severity=severity, limit=limit)


@router.get("/stats")
def response_stats(db: Session = Depends(get_db)):
    return engine.stats(db)


@router.get("/audit")
def recent_audit(limit: int = Query(100, ge=1, le=1000), db: Session = Depends(get_db)):
    return engine.recent_audit(db, limit=limit)


@router.post("/generate")
def generate(payload: GenerateRequest, db: Session = Depends(get_db)):
    if payload.investigation_id is not None:
        created = _guard(engine.generate_from_investigation, db, payload.investigation_id)
        return {"recommendations_created": len(created), "recommendations": created}
    return engine.generate_recent(db, limit=payload.limit)


@router.get("/recommendations/{rec_id}")
def get_recommendation(rec_id: int, db: Session = Depends(get_db)):
    r = engine.get(db, rec_id)
    if r is None:
        raise HTTPException(status_code=404, detail=f"Recommendation {rec_id} not found")
    return r


@router.get("/recommendations/{rec_id}/audit")
def recommendation_audit(rec_id: int, db: Session = Depends(get_db)):
    return engine.audit_trail(db, rec_id)


@router.post("/recommendations/{rec_id}/approve")
def approve(rec_id: int, payload: ApproveRequest, db: Session = Depends(get_db)):
    return _guard(engine.approve, db, rec_id, payload.approver)


@router.post("/recommendations/{rec_id}/reject")
def reject(rec_id: int, payload: RejectRequest, db: Session = Depends(get_db)):
    return _guard(engine.reject, db, rec_id, payload.approver, payload.reason)


@router.post("/recommendations/{rec_id}/execute")
def execute(rec_id: int, payload: ActorRequest, db: Session = Depends(get_db)):
    """Execute an APPROVED recommendation via Shuffle. 409 if not approved."""
    return _guard(engine.execute, db, rec_id, payload.actor)


@router.post("/recommendations/{rec_id}/verify")
def verify(rec_id: int, payload: ActorRequest, db: Session = Depends(get_db)):
    return _guard(engine.verify, db, rec_id, payload.actor)
