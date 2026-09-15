from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import CVE, PriorityScore
from backend.app.schemas import PriorityBreakdown, PriorityRead, PriorityStats

router = APIRouter()

VALID_LEVELS = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}

_ENRICHED = (
    PriorityScore,
    CVE.severity.label("severity"),
    CVE.cvss_score.label("cvss_score"),
)


def _base_query():
    return select(*_ENRICHED).join(CVE, CVE.cve_id == PriorityScore.cve_id)


def _to_read(row) -> PriorityRead:
    p = row[0]
    return PriorityRead(
        id=p.id,
        cve_id=p.cve_id,
        priority_score=p.priority_score,
        priority_level=p.priority_level,
        ml_risk_score=p.ml_risk_score,
        epss_score=p.epss_score,
        kev_flag=p.kev_flag,
        explanation=p.explanation,
        generated_at=p.generated_at,
        severity=row.severity,
        cvss_score=row.cvss_score,
    )


def _validate_level(level: str) -> str:
    upper = level.upper()
    if upper not in VALID_LEVELS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid priority_level '{level}'. Expected one of {sorted(VALID_LEVELS)}.",
        )
    return upper


@router.get("/priority", response_model=list[PriorityRead], tags=["priority"])
def list_priority(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    priority_level: str | None = Query(None, description="LOW, MEDIUM, HIGH, CRITICAL"),
    min_score: float | None = Query(None, ge=0.0, le=100.0),
    kev_only: bool = Query(False, description="Only CVEs in the CISA KEV catalog"),
    search: str | None = Query(None, description="Substring match on CVE ID"),
    db: Session = Depends(get_db),
):
    query = _base_query()
    if priority_level:
        query = query.where(PriorityScore.priority_level == _validate_level(priority_level))
    if min_score is not None:
        query = query.where(PriorityScore.priority_score >= min_score)
    if kev_only:
        query = query.where(PriorityScore.kev_flag.is_(True))
    if search:
        query = query.where(PriorityScore.cve_id.ilike(f"%{search}%"))

    query = query.order_by(PriorityScore.priority_score.desc())
    rows = db.execute(query.offset(skip).limit(limit)).all()
    return [_to_read(r) for r in rows]


@router.get("/priority/top", response_model=list[PriorityRead], tags=["priority"])
def top_priority(
    limit: int = Query(10, ge=1, le=100),
    kev_only: bool = Query(False),
    db: Session = Depends(get_db),
):
    """Highest-priority vulnerabilities to patch first."""
    query = _base_query()
    if kev_only:
        query = query.where(PriorityScore.kev_flag.is_(True))
    query = query.order_by(PriorityScore.priority_score.desc()).limit(limit)
    return [_to_read(r) for r in db.execute(query).all()]


@router.get("/stats/priority", response_model=PriorityStats, tags=["priority"])
def priority_stats(db: Session = Depends(get_db)):
    total = db.scalar(select(func.count()).select_from(PriorityScore)) or 0

    level_rows = db.execute(
        select(PriorityScore.priority_level, func.count())
        .group_by(PriorityScore.priority_level)
    ).all()
    by_level = {level: count for level, count in level_rows}

    avg = db.scalar(select(func.avg(PriorityScore.priority_score)))
    max_score = db.scalar(select(func.max(PriorityScore.priority_score)))
    kev_count = db.scalar(
        select(func.count()).select_from(PriorityScore).where(PriorityScore.kev_flag.is_(True))
    ) or 0
    epss_covered = db.scalar(
        select(func.count()).select_from(PriorityScore).where(PriorityScore.epss_score.isnot(None))
    ) or 0
    avg_ml = db.scalar(select(func.avg(PriorityScore.ml_risk_score)))

    # Escalated by KEV = KEV-listed and now a higher band than its raw priority would be.
    escalated = db.scalar(
        select(func.count()).select_from(PriorityScore).where(
            PriorityScore.kev_flag.is_(True), PriorityScore.comp_kev > 0
        )
    ) or 0

    distribution = {"0-20": 0, "20-40": 0, "40-60": 0, "60-80": 0, "80-100": 0}
    for s in db.execute(select(PriorityScore.priority_score)).scalars():
        if s < 20:
            distribution["0-20"] += 1
        elif s < 40:
            distribution["20-40"] += 1
        elif s < 60:
            distribution["40-60"] += 1
        elif s < 80:
            distribution["60-80"] += 1
        else:
            distribution["80-100"] += 1

    return PriorityStats(
        total=total,
        by_level=by_level,
        average_score=round(avg, 2) if avg is not None else None,
        max_score=round(max_score, 2) if max_score is not None else None,
        kev_count=kev_count,
        epss_covered=epss_covered,
        distribution=distribution,
        average_ml_risk=round(avg_ml, 2) if avg_ml is not None else None,
        escalated_by_kev=escalated,
    )


@router.get(
    "/priority/{cve_id}/explanation",
    response_model=PriorityBreakdown,
    tags=["priority"],
)
def priority_explanation(cve_id: str, db: Session = Depends(get_db)):
    """Explainable per-component breakdown of one CVE's priority."""
    p = db.execute(
        select(PriorityScore).where(PriorityScore.cve_id == cve_id.upper())
    ).scalar_one_or_none()
    if p is None:
        raise HTTPException(status_code=404, detail=f"No priority score for CVE '{cve_id}'")
    return PriorityBreakdown(
        cve_id=p.cve_id,
        priority_score=p.priority_score,
        priority_level=p.priority_level,
        components={
            "cvss": p.comp_cvss,
            "correlation": p.comp_correlation,
            "ml": p.comp_ml,
            "epss": p.comp_epss,
            "attack": p.comp_attack,
            "kev": p.comp_kev,
        },
        explanation=p.explanation,
        ml_risk_score=p.ml_risk_score,
        epss_score=p.epss_score,
        kev_flag=p.kev_flag,
    )


@router.get("/priority/{cve_id}", response_model=PriorityRead, tags=["priority"])
def get_priority(cve_id: str, db: Session = Depends(get_db)):
    """Priority score for one CVE by its NVD identifier."""
    row = db.execute(
        _base_query().where(PriorityScore.cve_id == cve_id.upper())
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail=f"No priority score for CVE '{cve_id}'")
    return _to_read(row)
