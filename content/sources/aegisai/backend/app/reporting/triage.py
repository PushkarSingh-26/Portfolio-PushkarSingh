"""Autonomous triage engine (Phase 15.1 / 15.2).

Detects critical findings (critical alerts, new KEV, high-risk CVEs, influential
actors) and auto-runs full agent investigations on the top critical alerts. The
agent already performs the 9-step evidence-driven workflow; triage orchestrates
selection, dedup, and execution history.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

log = logging.getLogger("reporting.triage")


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _already_investigated_alerts(db: Session) -> set[int]:
    from backend.app.models import AgentInvestigation
    ids = set()
    for (target,) in db.execute(
        select(AgentInvestigation.target).where(AgentInvestigation.investigation_type == "alert")
    ).all():
        if target and target.startswith("alert:"):
            try:
                ids.add(int(target.split(":", 1)[1]))
            except ValueError:
                pass
    return ids


def detect_candidates(db: Session) -> dict:
    """Return critical findings worth investigating (evidence-driven selection)."""
    from backend.app.models import (
        CVE, KEVEntry, PriorityScore, WazuhAlert, WazuhAlertEnrichment,
    )

    done = _already_investigated_alerts(db)
    crit_alerts = db.execute(
        select(WazuhAlertEnrichment.alert_id, WazuhAlertEnrichment.priority_score,
               WazuhAlert.description)
        .join(WazuhAlert, WazuhAlert.id == WazuhAlertEnrichment.alert_id)
        .where(WazuhAlertEnrichment.priority_level == "CRITICAL")
        .order_by(WazuhAlertEnrichment.priority_score.desc())
    ).all()
    new_crit = [{"alert_id": a, "priority_score": p, "description": d}
                for a, p, d in crit_alerts if a not in done]

    high_cves = db.execute(
        select(PriorityScore.cve_id, PriorityScore.priority_score)
        .where(PriorityScore.priority_level == "CRITICAL")
        .order_by(PriorityScore.priority_score.desc()).limit(10)
    ).all()
    kev_recent = db.execute(
        select(KEVEntry.cve_id, KEVEntry.date_added)
        .order_by(KEVEntry.date_added.desc()).limit(10)
    ).all()

    return {
        "critical_alerts": new_crit,
        "high_risk_cves": [{"cve_id": c, "priority_score": p} for c, p in high_cves],
        "recent_kev": [{"cve_id": c, "date_added": d} for c, d in kev_recent],
    }


def run_triage(db: Session, max_alerts: int = 10) -> dict:
    """Auto-investigate the top new critical alerts; persist a triage report."""
    from backend.app.agents import agent
    from backend.app.models import ScheduledReport

    candidates = detect_candidates(db)
    investigated = []
    for cand in candidates["critical_alerts"][:max_alerts]:
        result = agent.investigate_alert(db, cand["alert_id"])
        rep = result["report"]
        investigated.append({
            "alert_id": cand["alert_id"],
            "investigation_id": result["investigation_id"],
            "risk_level": rep["risk_assessment"]["level"],
            "blast_radius": (rep.get("blast_radius") or {}).get("total_affected", 0),
            "recommendations": len(rep.get("recommendations", [])),
            "confidence": result["confidence"],
        })

    report_json = {
        "triggered_at": datetime.now(timezone.utc).isoformat(),
        "candidates": {k: len(v) for k, v in candidates.items()},
        "investigations": investigated,
        "summary": f"Auto-investigated {len(investigated)} critical alert(s); "
                   f"{len(candidates['critical_alerts'])} pending critical alert(s) detected.",
    }
    sr = ScheduledReport(report_type="autonomous_triage", report_date=_today(),
                         report_json=report_json)
    db.add(sr)
    db.commit()
    db.refresh(sr)
    return {"report_id": sr.id, "investigated": len(investigated),
            "candidates": report_json["candidates"], "investigations": investigated}


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [triage] %(message)s")
    from backend.app.database import SessionLocal
    with SessionLocal() as db:
        stats = run_triage(db)
    log.info("Triage done: %s", stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
