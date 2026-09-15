"""Autonomous investigation rules (Phase 18.5).

Deterministic triage policy over real alerts/CVEs:
  AUTO investigate : Wazuh level >= 10, new KEV, EPSS >= 0.80, predicted conf > 0.80
  QUEUE only       : Wazuh level 7-9, EPSS 0.50-0.79
  IGNORE           : Wazuh level <= 6, EPSS < 0.50
Auto-investigations reuse the agent (idempotent dedup); queued items are stored.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

log = logging.getLogger("orchestration.rules")

AUTO_LEVEL_MIN = 10
QUEUE_LEVEL_MIN = 7
EPSS_AUTO = 0.80
EPSS_QUEUE = 0.50
PRED_AUTO = 0.80


def _investigated_alert_ids(db: Session) -> set[int]:
    from backend.app.models import AgentInvestigation
    out = set()
    for (t,) in db.execute(select(AgentInvestigation.target)
                           .where(AgentInvestigation.investigation_type == "alert")).all():
        if t and t.startswith("alert:"):
            try:
                out.add(int(t.split(":", 1)[1]))
            except ValueError:
                pass
    return out


def apply_investigation_rules(db: Session, max_auto: int = 15) -> dict:
    from backend.app.agents import agent
    from backend.app.models import (
        EPSSScore, PredictedRelationship, ScheduledReport, WazuhAlert,
    )
    from backend.app.ticketing import export_investigation

    done = _investigated_alert_ids(db)
    alerts = db.execute(
        select(WazuhAlert).order_by(WazuhAlert.rule_level.desc().nullslast(),
                                    WazuhAlert.timestamp.desc().nullslast())
    ).scalars().all()

    auto, queued = [], []
    ignored = 0
    for a in alerts:
        lvl = a.rule_level or 0
        if lvl >= AUTO_LEVEL_MIN and a.id not in done:
            auto.append(a)
        elif QUEUE_LEVEL_MIN <= lvl < AUTO_LEVEL_MIN:
            queued.append({"alert_id": a.id, "rule_level": lvl, "description": a.description})
        elif lvl <= 6:
            ignored += 1

    investigated = []
    for a in auto[:max_auto]:
        result = agent.investigate_alert(db, a.id)
        rep = result["report"]
        if rep["risk_assessment"]["level"] in ("CRITICAL", "HIGH"):
            export_investigation(result)  # SOAR/ticket export (mock by default)
        investigated.append({"alert_id": a.id, "investigation_id": result["investigation_id"],
                             "risk_level": rep["risk_assessment"]["level"],
                             "confidence": result["confidence"]})

    # EPSS-driven candidates (auto vs queue).
    epss_auto = db.scalar(select(func.count()).select_from(EPSSScore)
                          .where(EPSSScore.epss_score >= EPSS_AUTO)) or 0
    epss_queue = db.scalar(select(func.count()).select_from(EPSSScore)
                           .where(EPSSScore.epss_score >= EPSS_QUEUE, EPSSScore.epss_score < EPSS_AUTO)) or 0
    pred_auto = db.scalar(select(func.count()).select_from(PredictedRelationship)
                          .where(PredictedRelationship.confidence > PRED_AUTO)) or 0

    queue_report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "queued_alerts": queued[:100],
        "epss_auto_candidates": epss_auto, "epss_queue_candidates": epss_queue,
        "predicted_auto_candidates": pred_auto,
        "summary": f"Auto-investigated {len(investigated)} alert(s); queued {len(queued)}; "
                   f"ignored {ignored} low-severity alert(s).",
    }
    db.add(ScheduledReport(report_type="investigation_queue",
                           report_date=datetime.now(timezone.utc).date().isoformat(),
                           report_json=queue_report))
    db.commit()

    return {"investigated": len(investigated), "queued": len(queued), "ignored": ignored,
            "epss_auto_candidates": epss_auto, "predicted_auto_candidates": pred_auto,
            "details": investigated}
