"""Priority scoring math and pipeline.

Methodology (deterministic + explainable)
-----------------------------------------
Each CVE's priority blends six normalized signals. The five model/intel signals
are a weighted sum (weights sum to 1.0); CISA KEV is applied as a real-world
override on top, because a KEV listing means the vulnerability is *confirmed
exploited in the wild* and CISA mandates remediation:

    base   = 100 * ( 0.20*cvss + 0.15*correlation + 0.15*ml
                     + 0.30*epss + 0.20*attack )
    final  = base, unless KEV → final = min(100, max(base, 75) + 15)

EPSS carries the largest weight among the predictive signals because it is the
best available estimate of real-world exploit likelihood. The per-component
point contributions are stored so any score can be explained exactly.

Levels: CRITICAL ≥ 75, HIGH ≥ 50, MEDIUM ≥ 25, LOW < 25 (consistent with the
ML risk levels, enabling an apples-to-apples old-vs-new comparison).
"""

from collections import defaultdict
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

METHOD = "priority-v2"

WEIGHTS = {
    "cvss": 0.20,
    "correlation": 0.15,
    "ml": 0.15,
    "epss": 0.30,
    "attack": 0.20,
}

KEV_FLOOR = 75.0
KEV_BOOST = 15.0

_SEVERITY_CVSS_PROXY = {"LOW": 2.0, "MEDIUM": 5.0, "HIGH": 7.5, "CRITICAL": 9.5}


def priority_level(score: float) -> str:
    if score >= 75:
        return "CRITICAL"
    if score >= 50:
        return "HIGH"
    if score >= 25:
        return "MEDIUM"
    return "LOW"


def compute_priority(signals: dict) -> dict:
    """Pure scoring function. `signals` carries raw inputs; returns the score,
    level, per-component points, and a human explanation."""
    cvss = signals.get("cvss")
    if cvss is None:
        cvss = _SEVERITY_CVSS_PROXY.get((signals.get("severity") or "").upper(), 5.0)
    cvss_n = max(0.0, min(cvss / 10.0, 1.0))
    corr_n = max(0.0, min(signals.get("max_confidence", 0.0), 1.0))
    ml_n = max(0.0, min(signals.get("ml_risk", 0.0) / 100.0, 1.0))
    epss_n = max(0.0, min(signals.get("epss", 0.0), 1.0))
    attack_n = min(signals.get("num_mappings", 0), 5) / 5.0
    kev = bool(signals.get("kev", False))

    comp = {
        "cvss": round(WEIGHTS["cvss"] * cvss_n * 100, 2),
        "correlation": round(WEIGHTS["correlation"] * corr_n * 100, 2),
        "ml": round(WEIGHTS["ml"] * ml_n * 100, 2),
        "epss": round(WEIGHTS["epss"] * epss_n * 100, 2),
        "attack": round(WEIGHTS["attack"] * attack_n * 100, 2),
    }
    base = sum(comp.values())

    if kev:
        final = min(100.0, max(base, KEV_FLOOR) + KEV_BOOST)
        comp_kev = round(final - base, 2)
    else:
        final = base
        comp_kev = 0.0
    final = round(min(final, 100.0), 2)

    # Build an explanation ordered by impact.
    reasons = []
    if kev:
        reasons.append("listed in CISA KEV (confirmed exploited in the wild)")
    if epss_n >= 0.5:
        reasons.append(f"high EPSS exploit probability ({epss_n:.2f})")
    elif epss_n > 0:
        reasons.append(f"EPSS {epss_n:.2f}")
    if cvss_n >= 0.9:
        reasons.append(f"critical CVSS ({cvss:.1f})")
    elif cvss_n >= 0.7:
        reasons.append(f"high CVSS ({cvss:.1f})")
    if signals.get("num_mappings", 0):
        reasons.append(f"{signals['num_mappings']} ATT&CK technique mapping(s)")
    if corr_n >= 0.7:
        reasons.append(f"high correlation confidence ({corr_n:.2f})")
    explanation = (
        f"Priority {final:.0f} ({priority_level(final)}): " + "; ".join(reasons)
        if reasons
        else f"Priority {final:.0f} ({priority_level(final)})."
    )

    return {
        "priority_score": final,
        "priority_level": priority_level(final),
        "components": {**comp, "kev": comp_kev},
        "explanation": explanation,
        "ml_risk_score": signals.get("ml_risk"),
        "epss_score": signals.get("epss"),
        "kev_flag": kev,
    }


def gather_signals(db: Session) -> dict[str, dict]:
    """Assemble per-CVE input signals from all source tables."""
    from backend.app.models import (
        CVE,
        CorrelationResult,
        EPSSScore,
        KEVEntry,
        RiskScore,
    )

    # Scope: CVEs that have a risk score (i.e. the correlated set).
    risk = {r.cve_id: r.risk_score for r in db.query(RiskScore).all()}
    signals: dict[str, dict] = {
        cve_id: {"ml_risk": score} for cve_id, score in risk.items()
    }
    if not signals:
        return signals

    for cve_id, cvss, severity in db.execute(
        select(CVE.cve_id, CVE.cvss_score, CVE.severity)
    ).all():
        if cve_id in signals:
            signals[cve_id]["cvss"] = cvss
            signals[cve_id]["severity"] = severity

    corr = defaultdict(list)
    for cve_id, conf in db.execute(
        select(CorrelationResult.cve_id, CorrelationResult.confidence_score)
    ).all():
        corr[cve_id].append(conf)
    for cve_id, confs in corr.items():
        if cve_id in signals:
            signals[cve_id]["max_confidence"] = max(confs)
            signals[cve_id]["num_mappings"] = len(confs)

    for cve_id, epss in db.execute(
        select(EPSSScore.cve_id, EPSSScore.epss_score)
    ).all():
        if cve_id in signals:
            signals[cve_id]["epss"] = epss

    kev_ids = {row[0] for row in db.execute(select(KEVEntry.cve_id)).all()}
    for cve_id in signals:
        signals[cve_id]["kev"] = cve_id in kev_ids

    return signals


def run_prioritization(db: Session) -> dict:
    """Compute and upsert priority scores for all scored CVEs."""
    from backend.app.models import PriorityScore

    signals = gather_signals(db)
    if not signals:
        return {"prioritized": 0, "inserted": 0, "updated": 0}

    existing = {p.cve_id: p for p in db.query(PriorityScore).all()}
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    inserted = updated = 0
    by_level: dict[str, int] = defaultdict(int)
    kev_count = epss_count = escalated_by_kev = 0

    from ml.risk_model import risk_level as ml_level

    for cve_id, sig in signals.items():
        result = compute_priority(sig)
        by_level[result["priority_level"]] += 1
        if result["kev_flag"]:
            kev_count += 1
            # Escalation vs the ML-only view (old scoring).
            if ml_level(sig.get("ml_risk", 0)) != result["priority_level"]:
                escalated_by_kev += 1
        if sig.get("epss"):
            epss_count += 1

        comp = result["components"]
        current = existing.get(cve_id)
        if current is None:
            db.add(
                PriorityScore(
                    cve_id=cve_id,
                    priority_score=result["priority_score"],
                    priority_level=result["priority_level"],
                    ml_risk_score=result["ml_risk_score"],
                    epss_score=result["epss_score"],
                    kev_flag=result["kev_flag"],
                    comp_cvss=comp["cvss"],
                    comp_correlation=comp["correlation"],
                    comp_ml=comp["ml"],
                    comp_epss=comp["epss"],
                    comp_attack=comp["attack"],
                    comp_kev=comp["kev"],
                    explanation=result["explanation"],
                    method=METHOD,
                    generated_at=now,
                )
            )
            inserted += 1
        else:
            current.priority_score = result["priority_score"]
            current.priority_level = result["priority_level"]
            current.ml_risk_score = result["ml_risk_score"]
            current.epss_score = result["epss_score"]
            current.kev_flag = result["kev_flag"]
            current.comp_cvss = comp["cvss"]
            current.comp_correlation = comp["correlation"]
            current.comp_ml = comp["ml"]
            current.comp_epss = comp["epss"]
            current.comp_attack = comp["attack"]
            current.comp_kev = comp["kev"]
            current.explanation = result["explanation"]
            current.method = METHOD
            current.generated_at = now
            updated += 1

    db.commit()
    return {
        "prioritized": len(signals),
        "inserted": inserted,
        "updated": updated,
        "by_level": dict(by_level),
        "kev_count": kev_count,
        "epss_count": epss_count,
        "escalated_by_kev": escalated_by_kev,
    }


def main() -> int:
    from backend.app.database import SessionLocal

    print("Running Threat Prioritization Engine v2 ...")
    with SessionLocal() as db:
        stats = run_prioritization(db)
    if not stats.get("prioritized"):
        print("No scored CVEs to prioritize. Run the risk model first.")
        return 1
    print(
        f"Done. Prioritized {stats['prioritized']} CVEs "
        f"(inserted {stats['inserted']}, updated {stats['updated']}).\n"
        f"By level: {stats['by_level']}\n"
        f"KEV-listed: {stats['kev_count']}, with EPSS: {stats['epss_count']}, "
        f"escalated by KEV vs ML-only: {stats['escalated_by_kev']}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
